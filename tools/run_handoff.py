#!/usr/bin/env python3
"""Immutable, content-addressed handoff for existing JSON Jobs and frozen ConfigMaps.

Standard library only. prepare/validate/launch (without --submit) are offline.
install is used by the generated init container, before the original containers run.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from datetime import datetime, timezone

PREFIX = 'bnjettag.io/'
MAX_PAYLOAD = 950_000
MAX_EXPANDED = 64 * 1024 * 1024
BLOCKED = {'.git', '.ssh', '.aws', '.kube', '.gnupg', '.netrc', '.npmrc',
           'credentials', 'credentials.json', 'wandb-api-key.txt', 'id_rsa',
           'id_ed25519', '__pycache__', '.venv', 'node_modules'}
TEXT_EXT = {'.py', '.json', '.md', '.txt', '.sh', '.awk', '.yaml', '.yml',
            '.toml', '.cfg', '.ini', '.csv', '.lock', '.patch', '.diff'}
SECRET = re.compile(rb'-----BEGIN (?:[A-Z ]*PRIVATE KEY)-----|\bAKIA[A-Z0-9]{16}\b|'
                    rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{24,})\b|'
                    rb'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def read_json(path):
    return json.loads(Path(path).read_bytes())


def safe_name(name):
    p = PurePosixPath(name)
    need(name and not p.is_absolute() and '..' not in p.parts and '\\' not in name
         and ':' not in name and str(p) == name, 'unsafe or noncanonical path')
    need(not any(x.lower() in BLOCKED or x.lower().startswith('.env')
                 or x.lower().endswith(('.pem', '.key', '.p12', '.pfx'))
                 or re.search(r'(?:api[-_]?key|credential|secret)', x, re.I)
                 for x in p.parts), 'excluded credential path')
    return p


def scan_text(data):
    need(not SECRET.search(data), 'credential-like content rejected (value not displayed)')
    need(not re.search(rb'''(?im)^\s*(?:[A-Z_]*(?:PASSWORD|API_KEY|ACCESS_TOKEN|REFRESH_TOKEN|PRIVATE_KEY|CLIENT_SECRET))\s*=\s*["'][^"'\r\n]+["']''', data),
         'literal credential assignment rejected (value not displayed)')
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('non-text file in code snapshot') from None


def no_inline_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if re.fullmatch(r'(?:password|api[-_]?key|access[-_]?token|refresh[-_]?token|client[-_]?secret|private[-_]?key|credential)', key, re.I):
                need(item in (None, ''), 'inline credential field excluded (value not displayed)')
            no_inline_secrets(item)
    elif isinstance(value, list):
        for item in value:
            no_inline_secrets(item)


def payload_files(payload):
    need(len(payload) <= MAX_PAYLOAD, 'payload exceeds supported ConfigMap size')
    files, seen, total = {}, set(), 0
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        for entry in archive:
            p = safe_name(entry.name)
            need(p.parts[0] == 'code', 'snapshot must be rooted at code/')
            need(entry.name not in seen, 'duplicate archive path')
            seen.add(entry.name)
            need(entry.isfile() or entry.isdir(), 'links/devices are excluded')
            if entry.isdir():
                continue
            need(p.suffix.lower() in TEXT_EXT, 'unsupported file type in code snapshot')
            total += entry.size
            need(total <= MAX_EXPANDED, 'expanded snapshot exceeds limit')
            data = archive.extractfile(entry).read()
            scan_text(data)
            if p.suffix.lower() == '.json':
                no_inline_secrets(json.loads(data))
            files[entry.name] = data
    need(files, 'empty code snapshot')
    return files


def check_brief(brief, files):
    for key in ('purpose', 'changes', 'approval_ref'):
        need(isinstance(brief.get(key), str) and brief[key].strip(), 'missing brief field: ' + key)
    for key in ('runs', 'expected_metrics', 'stop_rules', 'outputs'):
        need(isinstance(brief.get(key), list) and brief[key], 'missing brief list: ' + key)
    need(brief.get('scientific_gate', {}).get('status') in ('pending', 'cleared'), 'missing scientific gate')
    need(isinstance(brief['scientific_gate'].get('reference'), str)
         and brief['scientific_gate']['reference'].strip(), 'missing scientific gate reference')
    names = set()
    for run in brief['runs']:
        need(isinstance(run.get('name'), str) and run['name'].strip() and run['name'] not in names, 'duplicate/missing run name')
        names.add(run['name'])
        p = str(safe_name(run.get('config_path', '')))
        need(p in files and p.endswith('.json'), 'selected config missing from exact payload')
        need(isinstance(json.loads(files[p]), dict), 'config must be resolved JSON object')
    for metric in brief['expected_metrics']:
        need(all(isinstance(metric.get(k), str) and metric[k].strip()
                 for k in ('name', 'split', 'expectation')), 'metric requires name/split/expectation')
    for rule in brief['stop_rules']:
        need(all(isinstance(rule.get(k), str) and rule[k].strip()
                 for k in ('condition', 'action', 'approval_ref')), 'stop rule missing approval or definition')
        need(rule['action'] in ('notify-only', 'existing-runner-guard'), 'monitor may not mutate jobs')
    for out in brief['outputs']:
        need(isinstance(out, str) and (out.startswith('/data/') or out.startswith('wandb://')),
             'output must identify PVC or W&B location')
    scan_text(encoded(brief))
    no_inline_secrets(brief)


def check_job(job, source):
    need(job.get('kind') == 'Job' and job.get('apiVersion') == 'batch/v1', 'only batch/v1 JSON Jobs supported')
    meta = job['metadata']
    need(meta.get('namespace') == 'cms-ml' and meta.get('labels', {}).get('user') == 'kai', 'expected cms-ml/user=kai')
    need(meta.get('name') and meta['labels'].get('campaign'), 'job needs explicit name and campaign')
    spec = job['spec']['template']['spec']
    need(not spec.get('initContainers'), 'existing init containers require manual integration')
    need(spec.get('automountServiceAccountToken') is False, 'handoff requires existing token automount=false')
    volumes = spec.get('volumes', [])
    need(len({v['name'] for v in volumes}) == len(volumes), 'duplicate volume names')
    pvc = [v['name'] for v in volumes if v.get('persistentVolumeClaim', {}).get('claimName') == 'kai-data']
    cm = [v['name'] for v in volumes if v.get('configMap', {}).get('name') == source['metadata']['name']]
    need(len(pvc) == len(cm) == 1, 'expected exactly one kai-data and matching code ConfigMap mount')
    need(pvc[0] != cm[0], 'code and data volumes must be distinct')
    for volume in volumes:
        if volume['name'] == cm[0]:
            need('items' not in volume['configMap'], 'code key remapping is unsupported')
        if volume['name'] == pvc[0]:
            need(not volume['persistentVolumeClaim'].get('readOnly'), 'data PVC must be writable')
    for container in spec['containers']:
        mounts = container.get('volumeMounts', [])
        data_mounts = [m for m in mounts if m['name'] == pvc[0]]
        code_mounts = [m for m in mounts if m['name'] == cm[0]]
        need(len(data_mounts) == len(code_mounts) == 1, 'expected one actual data and code mount per container')
        need(data_mounts[0]['mountPath'] == '/data' and not data_mounts[0].get('readOnly'), 'expected writable /data mount')
        need(code_mounts[0]['mountPath'] == '/cmcode' and code_mounts[0].get('readOnly') is True,
             'expected read-only frozen code mount at /cmcode')
        for mount in mounts:
            p = PurePosixPath(mount['mountPath'])
            need(p.is_absolute() and '..' not in p.parts and str(p) == mount['mountPath'], 'noncanonical mount path')
            for protected, expected in [('/data', data_mounts[0]), ('/cmcode', code_mounts[0])]:
                target = PurePosixPath(protected)
                if p.is_relative_to(target) or target.is_relative_to(p):
                    need(mount is expected, 'overlapping code/data mount is unsupported')
                    need('subPath' not in mount and 'subPathExpr' not in mount, 'code/data subPath is unsupported')
        for env in container.get('env', []):
            if re.search(r'KEY|TOKEN|PASSWORD|SECRET|CREDENTIAL', env.get('name', ''), re.I):
                need('value' not in env, 'inline credential environment value excluded; use secretKeyRef')
    scan_text(encoded(job))
    return pvc[0], cm[0]


def build_record(job, source, brief, data_info, data_path):
    need(source.get('kind') == 'ConfigMap' and source.get('immutable') is True, 'source ConfigMap must be immutable')
    need(source['metadata'].get('namespace') == 'cms-ml', 'source namespace mismatch')
    need(set(source.get('binaryData', {})) == {'hgq2.tar.gz'} and not source.get('data'), 'unsupported source payload keys')
    payload = base64.b64decode(source['binaryData']['hgq2.tar.gz'], validate=True)
    files = payload_files(payload)
    need(source['metadata'].get('annotations', {}).get(PREFIX + 'bundle-sha256') == sha(payload), 'bundle hash mismatch')
    check_job(job, source)
    check_brief(brief, files)
    safe_name(data_path.lstrip('/'))
    need(data_path.startswith('/data/') and data_path.endswith('/data_info.json'), 'data identity must be /data/.../data_info.json')
    info = json.loads(data_info)
    hashes = info.get('array_sha256')
    need(isinstance(hashes, dict) and hashes and all(re.fullmatch('[0-9a-f]{64}', x) for x in hashes.values()),
         'data_info needs array_sha256 content hashes')
    scan_text(data_info)
    no_inline_secrets(info)
    return {'schema': 1, 'brief': brief, 'job': job, 'source_configmap': source,
            'payload_sha256': sha(payload), 'files': {p: sha(b) for p, b in sorted(files.items())},
            'resolved_configs': {r['name']: json.loads(files[r['config_path']]) for r in brief['runs']},
            'data_path': data_path, 'data_info_text': data_info.decode(), 'data_info_sha256': sha(data_info),
            'publisher_sha256': sha(Path(__file__).read_bytes())}


def identity(record):
    return 'rh-' + sha(encoded(record))[:24]


def manifests(record):
    rid = identity(record)
    cmname = 'kai-' + rid
    need(record['publisher_sha256'] == sha(Path(__file__).read_bytes()), 'publisher version mismatch')
    job = copy.deepcopy(record['job'])
    pvc, code = check_job(job, record['source_configmap'])
    annotations = {PREFIX + 'handoff-sha256': sha(encoded(record)), PREFIX + 'handoff-configmap': cmname,
                   PREFIX + 'handoff-path': '/data/run-handoffs/' + rid}
    for meta in (job['metadata'], job['spec']['template'].setdefault('metadata', {})):
        meta.setdefault('labels', {})[PREFIX + 'run-id'] = rid
        meta.setdefault('annotations', {}).update(annotations)
    spec = job['spec']['template']['spec']
    need(not any(v['name'] == 'run-handoff' for v in spec['volumes']), 'handoff volume collision')
    spec['volumes'].append({'name': 'run-handoff', 'configMap': {'name': cmname}})
    spec['initContainers'] = [{'name': 'record-run-handoff', 'image': spec['containers'][0]['image'],
        'command': ['python', '/handoff/run_handoff.py', 'install', '--record', '/handoff/record.json'],
        'resources': {'requests': {'cpu': '100m', 'memory': '128Mi'}, 'limits': {'cpu': '1', 'memory': '256Mi'}},
        'volumeMounts': [{'name': 'run-handoff', 'mountPath': '/handoff', 'readOnly': True},
                         {'name': pvc, 'mountPath': '/data'}]}]
    # The immutable source ConfigMap bytes are included in record.json; no extra credentials or API calls.
    cm = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
          'metadata': {'name': cmname, 'namespace': 'cms-ml', 'labels': {
              'user': 'kai', 'campaign': job['metadata']['labels']['campaign'], PREFIX + 'run-id': rid}},
          'data': {'record.json': encoded(record).decode(), 'run_handoff.py': Path(__file__).read_text()}}
    need(len(encoded(cm)) < 1_000_000, 'handoff ConfigMap exceeds size limit; do not split silently')
    return job, cm


def validate_record(record):
    rebuilt = build_record(record['job'], record['source_configmap'], record['brief'],
                           record['data_info_text'].encode(), record['data_path'])
    need(rebuilt == record, 'record metadata or checksum mismatch')
    return manifests(record)


def prepare(args):
    record = build_record(read_json(args.job), read_json(args.configmap), read_json(args.brief),
                          Path(args.data_info).read_bytes(), args.data_path)
    job, cm = manifests(record)
    dest = Path(args.out) / identity(record)
    expected = {'record.json': encoded(record), 'job.json': encoded(job),
                'handoff-configmap.json': encoded(cm), 'source-configmap.json': encoded(record['source_configmap'])}
    if dest.exists():
        for name, data in expected.items():
            need((dest / name).read_bytes() == data, 'existing run ID contents conflict')
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix='.handoff-', dir=dest.parent))
        try:
            for name, data in expected.items():
                (temp / name).write_bytes(data)
            temp.rename(dest)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
    print(dest)
    return dest


def validate_dir(directory):
    directory = Path(directory)
    record = read_json(directory / 'record.json')
    job, cm = validate_record(record)
    for filename, expected in [('job.json', job), ('handoff-configmap.json', cm),
                               ('source-configmap.json', record['source_configmap'])]:
        need(read_json(directory / filename) == expected, 'modified generated file: ' + filename)
    need(directory.name == identity(record), 'run directory name mismatch')
    return record


def install(args):
    record = read_json(args.record)
    validate_record(record)
    data = Path(record['data_path']).read_bytes()
    need(sha(data) == record['data_info_sha256'], 'live PVC data identity differs from handoff')
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    dest = root / identity(record)
    payload = base64.b64decode(record['source_configmap']['binaryData']['hgq2.tar.gz'])
    expected = {'record.json': encoded(record), 'source.tar.gz': payload,
                'job-original.json': encoded(record['job']), 'data_info.json': data,
                'run_handoff.py': Path(__file__).read_bytes()}
    if dest.exists():
        for name, content in expected.items():
            need((dest / name).read_bytes() == content, 'immutable PVC record conflict')
    else:
        temp = Path(tempfile.mkdtemp(prefix='.handoff-', dir=root))
        try:
            for name, content in expected.items():
                (temp / name).write_bytes(content)
            temp.rename(dest)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
    print('HANDOFF_VERIFIED', identity(record), sha(encoded(record)))


def event(directory, status, details):
    """Append-only event plus atomically replaced derived status, outside immutable record files."""
    directory = Path(directory)
    events = directory / 'events'
    events.mkdir(exist_ok=True)
    value = {'time': datetime.now(timezone.utc).isoformat(), 'status': status, 'details': details}
    with (events / (uuid.uuid4().hex + '.json')).open('xb') as f:
        f.write(encoded(value))
        f.flush()
        os.fsync(f.fileno())
    temp = directory / ('.status-' + uuid.uuid4().hex)
    temp.write_bytes(encoded(value))
    os.replace(temp, directory / 'status.json')


def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(expected) == len(actual) and all(subset(x, y) for x, y in zip(expected, actual))
    return expected == actual


def launch(args):
    directory = Path(args.directory).resolve()
    record = validate_dir(directory)
    # Dry run is strictly offline and never invokes kubectl or a browser.
    if not args.submit:
        print('OFFLINE_VALIDATED', identity(record), 'no cluster calls; submit also requires cleared gate and nrp_doctor lint')
        return
    need(record['brief']['scientific_gate']['status'] == 'cleared', 'scientific gate pending; ask Kai')
    need(args.approval_ref == record['brief']['approval_ref'], 'explicit matching --approval-ref required')
    root = Path(__file__).resolve().parents[1]
    doctor = root / 'nrp-lab/nrp_doctor.py'
    need(doctor.is_file(), 'existing nrp_doctor lint required')
    lint = subprocess.run([sys.executable, str(doctor), 'lint', str(directory / 'job.json')], cwd=root)
    need(lint.returncode in (0, 1), 'nrp_doctor lint blocked launch')
    lock = directory / '.submit.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    base = [args.kubectl, '--request-timeout=30s', '-n', 'cms-ml']
    try:
        objects = {name: read_json(directory / name) for name in
                   ('source-configmap.json', 'handoff-configmap.json', 'job.json')}
        def lookup(obj):
            get = subprocess.run(base + ['get', obj['kind'], obj['metadata']['name'], '--ignore-not-found', '-o', 'json'],
                                 capture_output=True, text=True)
            need(get.returncode == 0, 'cluster lookup failed; no automatic retry')
            if get.stdout.strip():
                need(subset(obj, json.loads(get.stdout)), 'existing cluster object conflicts; manual review required')
                return True
            return False
        # Inspect the Job first. TTL/deletion must never turn a replay into fresh training.
        existing_job = lookup(objects['job.json'])
        existing_handoff = lookup(objects['handoff-configmap.json'])
        if existing_job:
            need(existing_handoff and lookup(objects['source-configmap.json']),
                 'existing Job lost provenance objects; manual review required')
            event(directory, 'submitted-or-already-present', {'run_id': identity(record), 'job': record['job']['metadata']['name']})
            return
        prior_events = (directory / 'events').exists() and any((directory / 'events').iterdir())
        need(not existing_handoff and not prior_events and not (directory / 'status.json').exists(),
             'run already submitted or submission is ambiguous; use a separately approved new attempt/Job identity')
        existing_source = lookup(objects['source-configmap.json'])
        # Durable local intent precedes every create. The immutable handoff CM independently
        # acts as a remote attempt marker and has no Job owner reference/TTL.
        event(directory, 'submission-intent', {'run_id': identity(record), 'job': record['job']['metadata']['name']})
        if not existing_source:
            subprocess.run(base + ['create', '-f', str(directory / 'source-configmap.json')], check=True)
        for filename in ('handoff-configmap.json', 'job.json'):
            subprocess.run(base + ['create', '-f', str(directory / filename)], check=True)
        event(directory, 'submitted-or-already-present', {'run_id': identity(record), 'job': record['job']['metadata']['name']})
    finally:
        lock.unlink()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('job', 'configmap', 'brief', 'data-info', 'data-path', 'out'):
        prep.add_argument('--' + name, required=True)
    check = sub.add_parser('validate')
    check.add_argument('directory')
    send = sub.add_parser('launch')
    send.add_argument('directory')
    send.add_argument('--submit', action='store_true')
    send.add_argument('--approval-ref')
    send.add_argument('--kubectl', default='kubectl')
    ins = sub.add_parser('install')
    ins.add_argument('--record', required=True)
    ins.add_argument('--root', default='/data/run-handoffs')
    view = sub.add_parser('inspect')
    view.add_argument('directory')
    view.add_argument('--expected-sha', required=True, help='full SHA-256 from Job annotation')
    view.add_argument('--run-id', required=True, help='run ID from Job label')
    args = p.parse_args()
    try:
        if args.command == 'prepare': prepare(args)
        elif args.command == 'validate':
            record = validate_dir(args.directory)
            print('VALID', identity(record))
        elif args.command == 'install': install(args)
        elif args.command == 'inspect':
            directory = Path(args.directory)
            raw = (directory / 'record.json').read_bytes()
            need(sha(raw) == args.expected_sha, 'Job annotation/record hash mismatch')
            record = json.loads(raw)
            need(identity(record) == args.run_id, 'Job run ID mismatch')
            validate_record(record)
            need(sha((directory / 'source.tar.gz').read_bytes()) == record['payload_sha256'], 'saved source hash mismatch')
            print(json.dumps(record['brief'], indent=2))
        else: launch(args)
    except (ValueError, KeyError, OSError, TypeError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print('HANDOFF_BLOCKED:', str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
