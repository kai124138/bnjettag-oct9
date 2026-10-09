#!/usr/bin/env python3
"""Local substitute for kubectl, for tests and the recovery demo only. Never contacts a cluster.

State lives in $LOCAL_KUBE_DIR. `create -f job.json` runs the Job's first container on this
machine from the code ConfigMap it mounts (the frozen bundle, not a working copy), with /cmcode
and /data mapped to local directories, and writes Job and Pod objects shaped like Kubernetes
records. The pod failure policy and per-index retry limit are applied as Kubernetes would.
Records it writes are constructed, not captured: each carries bnjettag.io/substitute=true.
Init containers are not run.
"""
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

STATE = Path(os.environ['LOCAL_KUBE_DIR'])


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def path(kind, name):
    return STATE / 'objects' / kind / f'{name}.json'


def load(kind, name):
    p = path(kind, name)
    return json.loads(p.read_text()) if p.exists() else None


def save(obj):
    p = path(obj['kind'], obj['metadata']['name'])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True))


def all_of(kind):
    d = STATE / 'objects' / kind
    return [json.loads(p.read_text()) for p in sorted(d.glob('*.json'))] if d.exists() else []


def policy_action(job, exit_code):
    for rule in (job['spec'].get('podFailurePolicy') or {}).get('rules', []):
        oc = rule.get('onExitCodes')
        if oc and oc.get('operator') == 'In' and exit_code in oc.get('values', []):
            return rule['action']
    return 'Count'


def run_job(job):
    spec = job['spec']
    tspec = spec['template']['spec']
    ctr = tspec['containers'][0]
    cm_name = next(v['configMap']['name'] for v in tspec['volumes']
                   if v.get('configMap') and v['name'] != 'run-handoff')
    cm = load('ConfigMap', cm_name)
    name = job['metadata']['name']
    run = STATE / 'runs' / name
    (run / 'cmcode').mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(cm['binaryData']['hgq2.tar.gz']))) as t:
        t.extractall(run / 'cmcode', filter='data')
    data = STATE / 'data'
    data.mkdir(exist_ok=True)
    argv = [sys.executable if a == 'python' else
            a.replace('/cmcode', str(run / 'cmcode')).replace('/data', str(data))
            for a in ctr['command']]
    retries = spec.get('backoffLimitPerIndex', 0)
    status = {'startTime': now(), 'failed': 0, 'succeeded': 0, 'conditions': []}
    attempt = 0
    while True:
        pod_name = f'{name}-0-{attempt}'
        started = now()
        r = subprocess.run(argv, capture_output=True, text=True, cwd=run,
                           env=dict(os.environ, DATA_ROOT=str(data), JOB_NAME=name),
                           timeout=tspec.get('activeDeadlineSeconds') or 600)
        log = STATE / 'logs' / f'{pod_name}.log'
        log.parent.mkdir(exist_ok=True)
        log.write_text(r.stdout + r.stderr)
        phase = 'Succeeded' if r.returncode == 0 else 'Failed'
        save({'apiVersion': 'v1', 'kind': 'Pod',
              'metadata': {'name': pod_name, 'namespace': 'cms-ml',
                           'labels': {'batch.kubernetes.io/job-name': name, 'job-name': name,
                                      'batch.kubernetes.io/job-completion-index': '0'},
                           'annotations': {'bnjettag.io/substitute': 'true'}},
              'spec': {'containers': [{'name': ctr['name'], 'resources': ctr.get('resources', {})}]},
              'status': {'phase': phase, 'startTime': started, 'conditions': [],
                         'containerStatuses': [{'name': ctr['name'], 'restartCount': 0, 'state': {
                             'terminated': {'exitCode': r.returncode, 'startedAt': started,
                                            'finishedAt': now(),
                                            'reason': 'Completed' if r.returncode == 0 else 'Error'}}}]}})
        if r.returncode == 0:
            status.update(succeeded=1, completedIndexes='0', completionTime=now())
            status['conditions'] = [{'type': 'Complete', 'status': 'True', 'reason': 'CompletionsReached'}]
            break
        status['failed'] += 1
        action = policy_action(job, r.returncode)
        if action in ('FailIndex', 'FailJob') or attempt >= retries:
            status.update(failedIndexes='0')
            status['conditions'] = [{'type': 'Failed', 'status': 'True', 'reason': 'FailedIndexes'
                                     if action != 'FailJob' else 'PodFailurePolicy'}]
            break
        attempt += 1
    job['status'] = status
    job['metadata'].setdefault('annotations', {})['bnjettag.io/substitute'] = 'true'
    save(job)


def selector_match(obj, sel):
    labels = obj['metadata'].get('labels', {})
    if ' in (' in sel:
        key, vals = sel.split(' in (')
        return labels.get(key.strip()) in [v.strip() for v in vals.rstrip(')').split(',')]
    key, val = sel.split('=', 1)
    return labels.get(key) == val


def main(argv):
    args = [a for a in argv if not a.startswith('--request-timeout')]
    if '-n' in args:
        i = args.index('-n')
        del args[i:i + 2]
    with open(STATE / 'calls.log', 'a') as f:
        f.write(json.dumps(args) + '\n')
    if args[0] == 'create' and args[1] == '-f':
        obj = json.loads(Path(args[2]).read_text())
        if load(obj['kind'], obj['metadata']['name']):
            print(f'Error from server (AlreadyExists): {obj["metadata"]["name"]}', file=sys.stderr)
            return 1
        save(obj)
        if obj['kind'] == 'Job':
            run_job(obj)
        return 0
    if args[0] == 'get' and '-l' in args:
        kinds = {'jobs': 'Job', 'pods': 'Pod'}[args[1]]
        sel = args[args.index('-l') + 1]
        print(json.dumps({'apiVersion': 'v1', 'kind': 'List',
                          'items': [o for o in all_of(kinds) if selector_match(o, sel)]}))
        return 0
    if args[0] == 'get':
        obj = load(args[1], args[2])
        if obj:
            print(json.dumps(obj))
        return 0
    if args[0] == 'logs':
        p = STATE / 'logs' / f'{args[1]}.log'
        if not p.exists():
            return 1
        print(p.read_text(), end='')
        return 0
    print(f'local_kubectl: unsupported {args}', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
