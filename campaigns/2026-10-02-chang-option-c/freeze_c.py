#!/usr/bin/env python3
"""Freeze the option-(c) tree and prepare (never submit) its Jobs and immutable handoffs.

python3 campaigns/2026-10-02-chang-option-c/freeze_c.py              # scientific gate pending (default)
python3 campaigns/2026-10-02-chang-option-c/freeze_c.py --only pilotc1 \
    --gate-cleared '<reviewed gate record>' --approval-ref '<exact Kai authorization>'   # at action time only

Writes, under this directory only:
  manifests/chang1002c-code.tar.gz, configmap.json, bundle-manifest.json
  manifests/cpugate-job.json      CPU: full pytest suite + chang1002c cpu_gate.py + A/B/D/R-F pairing
  manifests/pilotc{1,2,3}-job.json GPU A10, the eight registered pilot arms in three pods, epoch-500 pause
  manifests/readoutc-job.json      CPU: epoch-500 certification, [A26] entropy, controller/at-target report
  manifests/brief-<job>.json       factual handoff briefs (scientific gate pending)
  handoffs/rh-*                    tools/run_handoff.py prepare output (offline)
  PREPARED.json                    names, hashes and handoff IDs
Never calls kubectl. Historical files are read, never written.
"""
import base64
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CODE = HERE / 'code' / 'tree'
CAMP_REL = 'campaigns/chang1002c'
CAMP = CODE / CAMP_REL
OUT = HERE / 'manifests'
HIST = REPO / 'campaigns' / '2026-09-26-training-batch' / 'manifests' / 'freeze.py'
EXPORT_INFO = REPO / 'campaigns/2026-10-01-recovery/captures/pvc-20261001T0555Z/chang-n64-20260926/n64/data/data_info.json'
DATA_ROOT = '/data/chang-n64-20260926'                 # the existing gated N64 cache, unchanged
DATA_INFO_PATH = DATA_ROOT + '/n64/data/data_info.json'
RUN_ROOT = DATA_ROOT + '/pilot-c-20261002'              # new: never the pilot or pilot-b roots
GATE_ROOT = DATA_ROOT + '/option-c-20261002'
STAGE = 'pilot-c'
CAMPAIGN_DIR = '/work/code/' + CAMP_REL
IMAGE = 'docker.io/library/python@sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7'
PYTEST = 'pytest==8.4.2'                                # test runner only; not a training pin
KEY = 'hgq2.tar.gz'
SKIP = ('__pycache__', '.pytest_cache', '.DS_Store')
LABELS = {'user': 'kai', 'campaign': 'chang-n64-20261002-c'}
TAGS = 'chang1002c,option-c,pilot,pilot-c,regime-b,validation-only'
GPU_PRODUCT = ['NVIDIA-A10']                           # see PREFLIGHT "GPU product": open decision
PER_ARM_MEMORY_GI, PER_ARM_CPU = 8, 2
RSS_GATE_LIMIT_MB, RSS_GATE_WINDOW = str(8 * 1024), '5:105'
STOP_AFTER = 500
MONITOR_EVERY_S = 1800
APPROVAL = ('PENDING launch authorization; design decision local/2026-10-01-execution/'
            'chang-option-c-decision.json')


sys.dont_write_bytecode = True   # importing the historical freeze.py must not write into its campaign


def load_hist():
    spec = importlib.util.spec_from_file_location('chang0926_freeze', HIST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)        # module level only defines constants; main() is not run
    return module


H = load_hist()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def build_tarball():
    entries = sorted((p.relative_to(CODE).as_posix(), p) for p in CODE.rglob('*')
                     if not any(part in SKIP for part in p.relative_to(CODE).parts))
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for rel, path in entries:
            info = tarfile.TarInfo('code/' + rel)
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, '', ''
            if path.is_dir():
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                archive.addfile(info)
            else:
                data = path.read_bytes()
                info.size, info.mode = len(data), 0o755 if path.stat().st_mode & 0o111 else 0o644
                archive.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0, compresslevel=9) as gz:
        gz.write(raw.getvalue())
    return out.getvalue(), [(rel, p) for rel, p in entries if p.is_file()]


def manifest_sha():
    """run_study.manifest() construction over this tree and the pinned training versions."""
    pins = {}
    for line in (CODE / 'requirements-training.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split('==')
            pins[name.split('[')[0].strip()] = version.strip()
    versions = {k: pins[k] for k in ('tensorflow', 'keras', 'hgq2', 'quantizers', 'numpy', 'scikit-learn')}
    paths = sorted(CODE.glob('*.py')) + sorted((CODE / 'bnhgq2').glob('*.py'))
    result = {'files': {str(p.relative_to(CODE)): sha(p.read_bytes()) for p in paths}, 'versions': versions}
    return sha(json.dumps(result, sort_keys=True).encode())


def check_campaign():
    index = json.loads((CAMP / 'index.json').read_text())
    rows = index['runs']
    assert index['count'] == len(rows) == 58 and index['production_count'] == 56
    for row in rows:
        assert sha((CAMP / 'configs' / row['file']).read_bytes()) == row['config_sha256'], row['file']
        cfg = json.loads((CAMP / 'configs' / row['file']).read_text())
        eb = cfg['train']['ebops']
        assert eb['pid_input'] == 'traced_only' and eb['pid_traced_integral'] == 'per_epoch', row['file']
        assert cfg['train']['ebops_trace_every'] == 10 and cfg['experiment']['group'] == LABELS['campaign']
    pods = json.loads((CAMP / 'pilot_c_packs.json').read_text())
    assert [len(p) for p in pods] == [4, 2, 2]
    for number, pod in enumerate(pods, 1):
        assert json.loads((CAMP / f'pilot_c{number}_packs.json').read_text()) == [pod]
    return {r['index']: r['name'] for r in rows}, pods


def header(bundle, msha, cpu):
    lines = [
        'set -euo pipefail',
        'export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2',
        'export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1',
        'mkdir -p /work/code',
        f"echo '{bundle}  /cmcode/{KEY}' | sha256sum -c -",
        f'tar -xzf /cmcode/{KEY} -C /work/code --strip-components=1',
        'export PYTHONPATH=/work/code',
        f'export BNJ_DATA_ROOT={DATA_ROOT} BNJ_RUN_ROOT={RUN_ROOT} BNJ_CAMPAIGN_DIR={CAMPAIGN_DIR}',
        f'export BNJ_STAGE={STAGE}',
    ]
    if cpu:
        lines += ['export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled',
                  'pip install -q --no-cache-dir -r /work/code/requirements-cpu.txt']
    else:
        lines += [
            'export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0',
            'unset WANDB_PROJECT',
            'export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_MODE=online',
            f'export WANDB_TAGS={TAGS}',
            f'export BNJ_RSS_GATE_LIMIT_MB={RSS_GATE_LIMIT_MB} BNJ_RSS_GATE_WINDOW={RSS_GATE_WINDOW}',
            'export WANDB_DIR=/work WANDB_CACHE_DIR=/work/wandb-cache WANDB_DATA_DIR=/work/wandb-data '
            'WANDB_DISABLE_CODE=true WANDB_QUIET=true',
            'pip install -q --no-cache-dir -r /work/code/requirements-training.txt',
            'NVLIBS=$(python -c "import glob; print(\':\'.join(sorted(glob.glob(\'/usr/local/lib/python*/'
            'site-packages/nvidia/*/lib\'))))")',
            'export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        ]
    lines += [
        'cd /work/code',
        'MSHA=$(python -c "import run_study; print(run_study.manifest()[\'sha256\'])")',
        f'test "$MSHA" = "{msha}" || {{ echo "MANIFEST_SHA_MISMATCH $MSHA"; exit 1; }}',
        'echo "MANIFEST_SHA_OK $MSHA"',
        'export BNHGQ2_CODE_SHA256="$MSHA"',
    ]
    return '\n'.join(lines) + '\n'


def monitor_loop(names):
    """Notify-only, standard library: every MONITOR_EVERY_S the canary/controller/at-target
    reader runs on each arm's telemetry and prints its lines into the pod log. Never kills."""
    body = ' '.join(names)
    return (f'( while sleep {MONITOR_EVERY_S}; do for n in {body}; do '
            f't={RUN_ROOT}/runs/$n/pid_telemetry.jsonl; test -s "$t" || continue; '
            f'python -u {CAMPAIGN_DIR}/monitor_c.py --config {CAMPAIGN_DIR}/configs/$n.json --telemetry "$t" '
            '| sed "s/^/MONITOR /" || echo "MONITOR_ERROR $n"; done; done ) &\nMON=$!\n')


def pilot_tail(packs_file, names):
    fp_run = 'chang1002c-a-n64-s1'
    return '\n'.join([
        'python -c "import tensorflow as tf; assert tf.config.list_physical_devices(\'GPU\'); print(\'GPU_GATE_PASS\')"',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true',
        'df -h /data',
        f"echo '{H.FP_SHA}  {H.FP_MOUNT}/fingerprint_check.py' | sha256sum -c -",
        'FP=0',
        f'python -u {H.FP_MOUNT}/fingerprint_check.py --run {fp_run} --expect {H.FP_EXPECT} --data-root {DATA_ROOT} '
        f'--campaign-dir {CAMPAIGN_DIR} --env-report || FP=$?',
        'if [ "$FP" != 0 ]; then echo "FINGERPRINT_GATE_FAIL exit=$FP node=${NODE_NAME:-na}; no arm started"; exit "$FP"; fi',
        # GPU memory telemetry for the 90 % rule, one-minute samples into the pod log
        '( while sleep 60; do echo "GPU_SAMPLE $(date -u +%FT%TZ) $(nvidia-smi --query-gpu=utilization.gpu,'
        'memory.used,memory.total --format=csv,noheader,nounits | tr -d \' \')"; done ) &',
        'SMI=$!',
        monitor_loop(names).rstrip('\n'),
        f'PACKS={packs_file}',
        'RP=0; E0=0',
        f'python -u /work/code/run_pack.py "$PACKS" {STOP_AFTER} || RP=$?',
        'kill "$SMI" "$MON" 2>/dev/null || true',
        H.EPOCH0_CHECK,
        f'if [ "$E0" = {H.EXIT_EPOCH0_ALL_DIVERGED} ]; then echo "POD_EPOCH0_ALL_DIVERGED node=${{NODE_NAME:-na}} '
        f'run_pack_exit=$RP"; exit {H.EXIT_EPOCH0_ALL_DIVERGED}; fi',
        'if [ "$E0" != 0 ]; then echo "PACK_EPOCH0_CHECK_ERROR $E0"; fi',
        f'for n in {" ".join(names)}; do t={RUN_ROOT}/runs/$n/pid_telemetry.jsonl; '
        f'test -s "$t" && python -u {CAMPAIGN_DIR}/monitor_c.py --config {CAMPAIGN_DIR}/configs/$n.json '
        '--telemetry "$t" | sed "s/^/FINAL /" || echo "FINAL_MONITOR_MISSING $n"; done',
        'exit "$RP"',
    ]) + '\n'


def readout_tail(names_by_index, indices, bundle):
    snap = f'snapshots/epoch-{STOP_AFTER:04d}'
    out = f'{RUN_ROOT}/readout-epoch-{STOP_AFTER:04d}-{bundle[:6]}-r1'
    pairs = ' '.join(f'{i}:{names_by_index[i]}' for i in indices)
    return '\n'.join([
        f'OUT={out}',
        'test ! -e "$OUT" || { echo "READOUT_OUTPUT_EXISTS $OUT"; exit 1; }',
        'ONLY=""; IDX=""; NSNAP=0; MISSING=""',
        f'for pair in {pairs}; do',
        '  i=${pair%%:*}; n=${pair#*:}; d=' + f'{RUN_ROOT}/runs/$n',
        f'  if test -f "$d/{snap}/state.json"; then ONLY="$ONLY${{ONLY:+,}}$n"; IDX="$IDX $i"; NSNAP=$((NSNAP + 1))',
        '  elif test -f "$d/DIVERGED.json"; then ONLY="$ONLY${ONLY:+,}$n"; IDX="$IDX $i"',
        '  else why=NO_TERMINAL_MARKER; test -f "$d/RSS_GATE_FAIL.json" && why=RSS_GATE_FAIL; '
        'echo "READOUT_MISSING $n $why"; MISSING="$MISSING $n"; fi',
        'done',
        'test "$NSNAP" -gt 0 || { echo "READOUT_NOTHING_PRESENT"; exit 1; }',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        'mkdir "$OUT"',
        'echo "READOUT_ARMS only=$ONLY indices=$IDX missing=${MISSING:- none}"',
        'CERT=0; A26=0; MONC=0',
        f'python -u {CAMPAIGN_DIR}/certify_ebops.py --run-root {RUN_ROOT}/runs --cache {DATA_ROOT}/n64/data '
        f'--out "$OUT/certify-snapshot-{STOP_AFTER:04d}.json" --snapshot {STOP_AFTER} --only "$ONLY" || CERT=$?',
        f'python -u /work/code/analysis/attn_entropy.py --indices $IDX --epoch {STOP_AFTER} '
        f'--out "$OUT/a26-entropy-epoch-{STOP_AFTER:04d}.json" || A26=$?',
        # controller audit, cadence-adjusted canary and at-target accuracy/attention per arm
        'for n in $(echo "$ONLY" | tr , " "); do',
        f'  t={RUN_ROOT}/runs/$n/{snap}/pid_telemetry.jsonl',
        f'  if test -s "$t"; then python -u {CAMPAIGN_DIR}/monitor_c.py --config {CAMPAIGN_DIR}/configs/$n.json '
        '--telemetry "$t" --json "$OUT/controller-$n.json" || MONC=1; else echo "TELEMETRY_MISSING $n"; MONC=1; fi',
        'done',
        'sha256sum "$OUT"/*.json',
        'echo "READOUT_JOB_DONE certify_exit=$CERT a26_exit=$A26 controller_exit=$MONC missing=${MISSING:- none}"',
        'test "$CERT" = 0 && test "$A26" = 0 && test "$MONC" = 0 && test -z "$MISSING"',
    ]) + '\n'


def cpugate_tail(bundle):
    out = f'{GATE_ROOT}/cpu-gate-{bundle[:6]}-r1'
    return '\n'.join([
        f'OUT={out}',
        'test ! -e "$OUT" || { echo "CPU_GATE_OUTPUT_EXISTS $OUT"; exit 1; }',
        f'mkdir -p {GATE_ROOT} && mkdir "$OUT"',
        f'pip install -q --no-cache-dir {PYTEST}',
        'pip freeze > "$OUT/pip-freeze.txt"',
        'PT=0; GATE=0; PAIR=0',
        'python -m pytest -q -p no:cacheprovider tests analysis > "$OUT/pytest.log" 2>&1 || PT=$?',
        'tail -n 40 "$OUT/pytest.log"',
        f'python -u {CAMPAIGN_DIR}/cpu_gate.py --out "$OUT/cpu_gate.json" > "$OUT/cpu_gate.log" 2>&1 || GATE=$?',
        'grep -E "PID_TRACED_ONLY_OK|CONFIG_PREFLIGHT_PASS|PREFLIGHT_ALL_PASS|Error|assert" "$OUT/cpu_gate.log" | tail -n 140 || true',
        f'python -u {CAMPAIGN_DIR}/check_pairing.py --arms a,b,d,r --seeds 1,2,3,4,5,6,7,8 --out "$OUT/pairing.json" '
        '|| PAIR=$?',
        'sha256sum "$OUT"/*',
        'echo "CPU_GATE_DONE pytest_exit=$PT cpu_gate_exit=$GATE pairing_exit=$PAIR"',
        'test "$PT" = 0 && test "$GATE" = 0 && test "$PAIR" = 0',
    ]) + '\n'


MOUNTS = [{'mountPath': '/cmcode', 'name': 'code', 'readOnly': True},
          {'mountPath': '/work', 'name': 'work'},
          {'mountPath': '/data', 'name': 'persistent'}]


def volumes(cm, work, fingerprint=False):
    out = [{'name': 'code', 'configMap': {'name': cm, 'defaultMode': 420}},
           {'name': 'work', 'emptyDir': {'sizeLimit': work}},
           {'name': 'persistent', 'persistentVolumeClaim': {'claimName': 'kai-data'}}]
    if fingerprint:
        out.append({'name': 'fingerprint', 'configMap': {'name': H.fp_configmap_name(), 'defaultMode': 420}})
    return out


def res(**kw):
    return {'requests': dict(kw), 'limits': dict(kw)}


def affinity(extra=()):
    return {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{
        'matchExpressions': list(extra) + [{'key': 'kubernetes.io/hostname', 'operator': 'NotIn',
                                            'values': H.PILOT_B_BAD_NODES}]}]}}}


def cpu_job(name, app, cm, script, annotations):
    labels = {**LABELS, 'app': app}
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': annotations},
            'spec': {'backoffLimit': 0, 'activeDeadlineSeconds': 14400, 'ttlSecondsAfterFinished': 604800,
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'affinity': affinity(), 'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'main', 'image': IMAGE, 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [script],
                                         'resources': res(cpu='8', memory='24Gi', **{'ephemeral-storage': '12Gi'}),
                                         'volumeMounts': MOUNTS}],
                         'volumes': volumes(cm, '12Gi')}}}}


def pilot_job(name, number, cm, script, pod_names):
    arms = len(pod_names)
    labels = {**LABELS, 'app': f'kai-chang1002c-pilotc{number}', 'bnjettag.io/arms-per-pod': str(arms)}
    gpu = {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': GPU_PRODUCT}
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': {
                'bnjettag.io/pack': f'pilot_c{number}_packs.json {",".join(pod_names)}',
                'bnjettag.io/controller': 'option (c): train.ebops.pid_input traced_only, pid_traced_integral per_epoch',
                'bnjettag.io/gpu-fingerprint': f'{H.fp_configmap_name()} sha256 {H.FP_SHA[:16]}: '
                                               f'chang1002c-a-n64-s1 initial_ebops == {H.FP_EXPECT} before any arm',
                'bnjettag.io/regime': 'B: [D20] trace every 10 epochs; PID steps only on traces',
                'bnjettag.io/active-deadline': 'unset on purpose (STUDY Resume); pauses at epoch 500',
                'bnjettag.io/per-arm-memory': f'{PER_ARM_MEMORY_GI}Gi host RAM, {PER_ARM_CPU} CPU per arm',
                'bnjettag.io/rss-gate': f'projection <= {RSS_GATE_LIMIT_MB} MiB, fit over process epochs {RSS_GATE_WINDOW}'}},
            'spec': {'completionMode': 'Indexed', 'completions': 1, 'parallelism': 1,
                     'backoffLimitPerIndex': 2, 'podReplacementPolicy': 'Failed', 'ttlSecondsAfterFinished': 604800,
                     'podFailurePolicy': {'rules': [
                         {'action': 'Ignore', 'onPodConditions': [{'type': 'DisruptionTarget'}]},
                         {'action': 'FailJob', 'onExitCodes': {'containerName': 'train', 'operator': 'In',
                                                               'values': [H.EXIT_EPOCH0_ALL_DIVERGED]}}]},
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'affinity': affinity([gpu]), 'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'train', 'image': IMAGE, 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [script],
                                         'env': [{'name': 'WANDB_API_KEY', 'valueFrom': {'secretKeyRef': {
                                             'name': 'kai-wandb', 'key': 'WANDB_API_KEY'}}},
                                                 {'name': 'NODE_NAME', 'valueFrom': {'fieldRef': {
                                                     'fieldPath': 'spec.nodeName'}}}],
                                         'resources': res(cpu=str(PER_ARM_CPU * arms),
                                                          memory=f'{PER_ARM_MEMORY_GI * arms}Gi',
                                                          **{'ephemeral-storage': '24Gi', 'nvidia.com/gpu': '1'}),
                                         'volumeMounts': MOUNTS + [{'mountPath': H.FP_MOUNT, 'name': 'fingerprint',
                                                                    'readOnly': True}]}],
                         'volumes': volumes(cm, '24Gi', fingerprint=True)}}}}


GATE_REF = ('campaigns/2026-10-02-chang-option-c/PREFLIGHT.md; amendment design PASS only '
            '(campaigns/2026-10-01-chang-traced-pid/REVIEW_DRAFT.md); K1 triggered, production blocked')
COMMON_LIMITS = ['Historical 42abed runs, snapshots and readouts are evidence only; no historical checkpoint may '
                 'initialize or resume these runs (config and code SHA guards).',
                 'Pilot validation values select no arm, alter no primary rule and support no performance claim.',
                 'The epoch-500 pause does not observe the first LR restart after epoch 500.']


GATE = {'status': 'pending', 'reference': GATE_REF, 'approval_ref': APPROVAL}


def brief(purpose, changes, runs, metrics, stops, outputs):
    return {'purpose': purpose, 'changes': changes, 'approval_ref': GATE['approval_ref'],
            'scientific_gate': {'status': GATE['status'], 'reference': GATE['reference']},
            'production_gate': {'status': 'pending', 'reference': 'K1 triggered; option (c) selected 2026-10-01T06:00:02Z'},
            'runs': [{'name': n, 'config_path': f'code/{CAMP_REL}/configs/{n}.json'} for n in runs],
            'expected_metrics': metrics, 'stop_rules': stops, 'outputs': outputs, 'limitations': COMMON_LIMITS,
            'decision_ref': 'local/2026-10-01-execution/chang-option-c-decision.json',
            'amendment_ref': 'campaigns/2026-10-01-chang-traced-pid/AMENDMENT_DRAFT.md'}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='', help='comma list of cpugate,pilotc1,pilotc2,pilotc3,readoutc (default all)')
    ap.add_argument('--gate-cleared', metavar='REFERENCE',
                    help='only after Kai clears the gate: reviewed document that records it')
    ap.add_argument('--approval-ref', help='exact dated Kai launch authorization (required with --gate-cleared)')
    args = ap.parse_args()
    if args.gate_cleared:
        assert args.approval_ref and not args.approval_ref.startswith('PENDING'), 'explicit approval reference required'
        GATE.update(status='cleared', reference=args.gate_cleared, approval_ref=args.approval_ref)
    only = set(filter(None, args.only.split(',')))
    names, pods = check_campaign()
    msha = manifest_sha()
    payload, files = build_tarball()
    bundle = sha(payload)
    assert len(base64.b64encode(payload)) < 1_000_000, len(payload)
    assert bundle != H.BUNDLE_42
    cm = 'kai-chang1002c-code-' + bundle[:10]
    OUT.mkdir(exist_ok=True)
    (OUT / 'chang1002c-code.tar.gz').write_bytes(payload)
    configmap = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
                 'metadata': {'name': cm, 'namespace': 'cms-ml', 'labels': LABELS,
                              'annotations': {'bnjettag.io/bundle-sha256': bundle, 'bnjettag.io/manifest-sha256': msha,
                                              'bnjettag.io/base': f'42abed4b + 0032 + 0033 (build_tree.py)'}},
                 'binaryData': {KEY: base64.b64encode(payload).decode()}}
    (OUT / 'configmap.json').write_bytes(enc(configmap))
    b6 = bundle[:6]
    jobs = {}
    all_names = [names[i] for i in range(58)]
    gate = cpu_job(f'kai-chang1002c-cpugate-{b6}', 'kai-chang1002c-cpugate', cm,
                   header(bundle, msha, cpu=True) + cpugate_tail(bundle),
                   {'bnjettag.io/purpose': 'option-(c) CPU gate: pytest suite, cpu_gate.py on 58 configs, A/B/D/R-F pairing'})
    jobs['cpugate'] = (gate, brief(
        'CPU gate for the option-(c) revision before any pilot: full unit suite including the tiny synthetic '
        'run_training fixtures, per-config build/reload/floor/trace-cadence gate and shared-kernel pairing.',
        'New frozen tree 42abed4b + staged 0032 + amendment 0033; 58 regenerated chang1002c configs. No training data, '
        'no GPU, no checkpoint read. Adds pytest (test runner only).',
        all_names,
        [{'name': 'pytest suite', 'split': 'synthetic fixtures only', 'expectation': 'all pass; skips listed'},
         {'name': 'cpu_gate.py', 'split': 'synthetic inputs, n=4096 rows', 'expectation': 'PREFLIGHT_ALL_PASS, 58 PID_TRACED_ONLY_OK, floors equal static_floors.json'},
         {'name': 'A/B/D/R vs F pairing', 'split': 'synthetic sample, 8 seeds', 'expectation': 'PAIRED except pos_table, else registered Welch fallback'}],
        [{'condition': 'any gate exit nonzero or 4 h deadline', 'action': 'existing-runner-guard',
          'approval_ref': 'Job script exit status; activeDeadlineSeconds 14400'}],
        [f'{GATE_ROOT}/cpu-gate-{b6}-r1']))
    for number, pod in enumerate(pods, 1):
        pod_names = [names[i] for i in pod]
        job = pilot_job(f'kai-chang1002c-pilotc{number}-{b6}', number, cm,
                        header(bundle, msha, cpu=False) + pilot_tail(f'pilot_c{number}_packs.json', pod_names), pod_names)
        script = job['spec']['template']['spec']['containers'][0]['args'][0]
        assert script.index('fingerprint_check.py --run') < script.index('run_pack.py')
        jobs[f'pilotc{number}'] = (job, brief(
            'Replacement option-(c) pilot from initialization to the epoch-500 pause: does the traced-only PID consume '
            'only traces and hold between them, and what are budget, accuracy and attention state at the target.',
            'Relative to pilot-b (42abed4b, A10 K5/K3): PID input traced-only with per_epoch integral (0032/0033), '
            'new names/group/run root/stage pilot-c, repacked to 3 pods for the 90 % GPU-memory rule, durable '
            'pid_telemetry.jsonl and notify-only monitor lines. Same data, split, gains, targets, schedules, seeds.',
            pod_names,
            [{'name': 'canary (cadence-adjusted)', 'split': 'training epochs 1-11 (one-based)',
              'expectation': 'finite loss; A/D loss(10) < loss(1); traced(10) < traced(1); at one-based 11 a step with span 9 '
                             'on the epoch-10 trace and a beta change by the HGQ2 formula (CANARY_* lines)'},
             {'name': 'controller audit', 'split': 'every epoch 1-500', 'expectation': 'CONTROLLER_AUDIT PASS: '
                             'inputs equal traces (rel 1e-6), held epochs keep beta/integral'},
             {'name': 'at-target state', 'split': 'validation n=62000, traced epochs', 'expectation':
              'reported, not predicted: budget met, feasible, degenerate-under-budget, Q/K 0-bit attention, beta at bounds'}],
            [{'condition': 'divergence, nonfinite metrics, RSS projection gate, epoch-0 all-diverged, fingerprint mismatch',
              'action': 'existing-runner-guard', 'approval_ref': 'run_pack/ablation guards in the frozen bundle; STUDY Resume'},
             {'condition': 'CANARY_* FAIL or CONTROLLER_AUDIT FAIL in a MONITOR line',
              'action': 'notify-only', 'approval_ref': 'amendment canary/controller gate; operator stops at a checkpoint only with Kai'},
             {'condition': 'NOTIFY_DEGENERATE_UNDER_BUDGET or NOTIFY_ATTENTION_QK_ZERO_BIT',
              'action': 'notify-only', 'approval_ref': 'b5 readout VERIFY.md (diagnostic); no registered stop rule exists'},
             {'condition': 'GPU_SAMPLE memory above 90 % of the card', 'action': 'notify-only',
              'approval_ref': 'docs/infrastructure/gpu-selection-policy.md'}],
            [f'{RUN_ROOT}/runs/{n}' for n in pod_names] + [f'{RUN_ROOT}/logs',
             f'wandb://kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe/{LABELS["campaign"]}-pilot-c']))
    indices = [i for pod in pods for i in pod]
    readout = cpu_job(f'kai-chang1002c-readoutc-{b6}', 'kai-chang1002c-readout', cm,
                      header(bundle, msha, cpu=True) + readout_tail(names, indices, bundle),
                      {'bnjettag.io/readout': f'epoch-{STOP_AFTER} snapshots under {RUN_ROOT}: certify_ebops.py, '
                                              'analysis/attn_entropy.py, monitor_c.py',
                       'bnjettag.io/runs': ','.join(names[i] for i in indices)})
    jobs['readoutc'] = (readout, brief(
        'Registered epoch-500 readout of the option-(c) pilot plus the controller audit and at-target accuracy/attention report.',
        'Same registered certification and [A26] entropy scripts as readout-b; adds monitor_c.py on each frozen '
        'snapshots/epoch-0500/pid_telemetry.jsonl. CPU only, TF32 off, no training, new output directory.',
        [names[i] for i in indices],
        [{'name': 'traced EBOP certification', 'split': 'training n=558000', 'expectation': 'registered relative 1e-6 on feasible selections'},
         {'name': '[A26] attention entropy and Q/K/V 0-bit', 'split': 'validation n=62000', 'expectation': 'reported per head'},
         {'name': 'controller audit and at-target report', 'split': 'telemetry epochs 1-500', 'expectation': 'audit PASS; report only'}],
        [{'condition': 'any script exit nonzero, missing arm or 4 h deadline', 'action': 'existing-runner-guard',
          'approval_ref': 'Job script exit status; registered readout bound'}],
        [f'{RUN_ROOT}/readout-epoch-{STOP_AFTER:04d}-{b6}-r1']))
    prepared = {}
    for key, (job, br) in jobs.items():
        if only and key not in only:
            continue
        (OUT / f'{key}-job.json').write_bytes(enc(job))
        (OUT / f'brief-{key}.json').write_bytes(enc(br))
        result = subprocess.run([sys.executable, str(REPO / 'tools/run_handoff.py'), 'prepare',
                                 '--job', str(OUT / f'{key}-job.json'), '--configmap', str(OUT / 'configmap.json'),
                                 '--brief', str(OUT / f'brief-{key}.json'), '--data-info', str(EXPORT_INFO),
                                 '--data-path', DATA_INFO_PATH, '--out', str(HERE / 'handoffs')],
                                capture_output=True, text=True)
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        assert result.returncode == 0, key
        handoff = Path(result.stdout.strip())
        prepared[key] = {'job': job['metadata']['name'], 'handoff': str(handoff.relative_to(HERE)),
                         'record_sha256': sha((handoff / 'record.json').read_bytes()),
                         'job_json_sha256': sha((handoff / 'job.json').read_bytes())}
    (OUT / 'bundle-manifest.json').write_bytes(enc({
        'bundle_sha256': bundle, 'manifest_sha256': msha, 'configmap': cm, 'bytes': len(payload),
        'base': '42abed4b + patches/0032 (f475c69e) + patches/0033', 'run_root': RUN_ROOT, 'stage': STAGE,
        'data_root': DATA_ROOT, 'files': {rel: sha(p.read_bytes()) for rel, p in files}}))
    if GATE['status'] == 'cleared':
        (HERE / 'PREPARED-cleared.json').write_bytes(enc({'gate': GATE, 'jobs': prepared}))
        return
    (HERE / 'PREPARED.json').write_bytes(enc({'status': 'offline_prepared_not_submitted', 'bundle_sha256': bundle,
                                              'manifest_sha256': msha, 'configmap': cm, 'image': IMAGE,
                                              'gpu_product': GPU_PRODUCT, 'jobs': prepared}))
    print('BUNDLE_SHA256', bundle)
    print('MANIFEST_SHA256', msha)
    print('CONFIGMAP', cm, 'bytes', len(payload), 'files', len(files))
    for key, value in prepared.items():
        print('PREPARED', key, value['job'], value['handoff'])


if __name__ == '__main__':
    main()
