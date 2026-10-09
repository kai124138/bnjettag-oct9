#!/usr/bin/env python3
"""Fill the gate-15 canary re-run and build the two node discriminator Jobs (REGRESSION_TICKET 2026-09-28).

    python3 campaigns/2026-09-27-delta-screen/manifests/build_gate15_manifests.py

Reads bundle/bundle-manifest.json (the current freeze) and the generated canary template
campaigns/2026-09-26-delta/code/manifests/delta-canary-job.json (manifest_wave2.py, gate 15 in the header,
run root canary-v2, c6017 excluded). Writes beside this file, never applies:
  delta-canary-v2-job.json            kai-delta0926-canary-v2: the canary template with the freeze's ConfigMap / bundle / manifest sha
  discrim-c6017-job.json              kai-delta0926-discrim-c6017: pinned to hcc-nrp-shor-c6017.unl.edu
  discrim-other-job.json              kai-delta0926-discrim-other: A10, NotIn c6017, prefers c5825
The discriminators train nothing: env report, then fingerprint_check.py for rep-A s1 and s2, twice each,
as four separate processes; every reading is taken, then exit 9 if any mismatched.
delta-canary-job.json (the c6017 run, bundle e6fc6cd9) is the record of what ran and is not touched.
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
BUNDLE = HERE.parent / 'bundle' / 'bundle-manifest.json'
TEMPLATE = LAB / 'campaigns/2026-09-26-delta/code/manifests/delta-canary-job.json'
BAD = 'hcc-nrp-shor-c6017.unl.edu'
PREFER = 'hcc-nrp-shor-c5825.unl.edu'   # the anchor pilot's healthy node (training-batch RUN.md l. 35)
CAMPAIGN_DIR = '/work/code/campaigns/delta0926'
CACHE = '/data/chang-n64-20260926'
RUNS = ('delta0926-w2-rep-a-t350000-s1', 'delta0926-w2-rep-a-t350000-s2')


def fill(obj, subs):
    text = json.dumps(obj)
    for k, v in subs.items():
        text = text.replace(k, v)
    return json.loads(text)


def discriminator(base, name, where, subs):
    j = copy.deepcopy(base)
    labels = {'user': 'kai', 'campaign': 'delta-20260927', 'app': name, 'bnjettag.io/arms-per-pod': '1'}
    j['metadata'] = {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': {
        'bnjettag.io/status': f'gate-15 node discriminator ({where}); no training; ~0.2 GPU-h; REGRESSION_TICKET.md §3 item 1',
        'bnjettag.io/single-arm-justified': 'diagnostic pod: init + initial EBOPs trace only (4 processes), no training arm',
        'bnjettag.io/bundle': f"{subs['__CONFIGMAP_NAME__']} {subs['__BUNDLE_SHA256__']}",
        'bnjettag.io/cluster-ops-read': "kubectl get pod -l app=%s -o jsonpath='{.items[*].status.containerStatuses[*].imageID} "
                                        "{.items[*].spec.nodeName}' (imageID is not readable in the pod)" % name}}
    spec = j['spec']
    for k in ('completionMode', 'backoffLimitPerIndex', 'podReplacementPolicy'):
        spec.pop(k, None)
    spec.update(completions=1, parallelism=1, backoffLimit=0, activeDeadlineSeconds=3600)
    spec['template']['metadata'] = {'labels': copy.deepcopy(labels)}
    pod = spec['template']['spec']
    na = pod['affinity']['nodeAffinity']
    exprs = na['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]['matchExpressions']
    host = [e for e in exprs if e['key'] == 'kubernetes.io/hostname' and e['operator'] == 'NotIn'][0]
    na.pop('preferredDuringSchedulingIgnoredDuringExecution', None)
    if where == 'c6017':
        host['values'] = sorted(v for v in host['values'] if v != BAD)
        exprs.append({'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': [BAD]})
    else:
        host['values'] = sorted(set(host['values']) | {BAD})
        na['preferredDuringSchedulingIgnoredDuringExecution'] = [
            {'weight': 100, 'preference': {'matchExpressions': [
                {'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': [PREFER]}]}}]
    c = pod['containers'][0]
    c['env'] = [e for e in c.get('env', []) if not e['name'].startswith('WANDB')]   # nothing tracks: no secret mounted
    for kind in ('requests', 'limits'):
        c['resources'][kind].update(cpu='4', memory='12Gi')
    lines = [
        'set -euo pipefail',
        'export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2',
        'export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1',
        'echo "DISCRIM_NODE $NODE_NAME"',
        'mkdir -p /work/code',
        f"echo '{subs['__BUNDLE_SHA256__']}  /cmcode/hgq2.tar.gz' | sha256sum -c -",
        'tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1',
        'export PYTHONPATH=/work/code',
        'unset BNJ_DATA_ROOT BNJ_RUN_ROOT WANDB_API_KEY',
        f'export BNJ_CAMPAIGN_DIR={CAMPAIGN_DIR}',
        'export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0',
        'pip install -q --no-cache-dir -r /work/code/requirements-training.txt',
        'NVLIBS=$(python -c "import glob; print(\':\'.join(sorted(glob.glob(\'/usr/local/lib/python*/site-packages/nvidia/*/lib\'))))")',
        'export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        'cd /work/code',
        'MSHA=$(python -c "import run_study; print(run_study.manifest()[\'sha256\'])")',
        f'test "$MSHA" = "{subs["__MANIFEST_SHA256__"]}" || {{ echo "MANIFEST_SHA_MISMATCH $MSHA"; exit 1; }}',
        'echo "MANIFEST_SHA_OK $MSHA"',
        f'test -f {CACHE}/n64/data/READY.json || {{ echo "GATE15_CACHE_NOT_READY {CACHE}"; exit 9; }}',
        f'OUT=/data/delta-20260927/discriminator/{name}-$(date -u +%Y%m%dT%H%M%SZ); mkdir -p $OUT',
        'RC=0',
    ]
    first = True
    for rep in (1, 2):
        for run in RUNS:
            tag = f'{run.rsplit("-", 1)[1]}-r{rep}'
            env = ' --env-report' if first else ''
            first = False
            lines.append(f'rc=0; python -u {CAMPAIGN_DIR}/fingerprint_check.py{env} --run {run} --data-root {CACHE} 2>&1 '
                         f'| tee $OUT/{tag}.log || rc=$?; echo "DISCRIM_RESULT {tag} exit $rc"; '
                         'test "$rc" = 0 || RC=9')
    lines += ['grep -h "^FINGERPRINT " $OUT/*.log || true', 'test "$RC" = 0 && echo DISCRIM_ALL_MATCH || echo DISCRIM_MISMATCH',
              'exit $RC']
    c['args'] = ['\n'.join(lines) + '\n']
    return j


def main():
    man = json.loads(BUNDLE.read_text())
    subs = {'__CONFIGMAP_NAME__': man['configmap'], '__BUNDLE_SHA256__': man['bundle_sha256'],
            '__MANIFEST_SHA256__': man['manifest_sha256']}
    assert 'fingerprint_check.py' in ''.join(man['files']), 'the freeze does not ship fingerprint_check.py'
    template = json.loads(TEMPLATE.read_text())
    canary = fill(template, subs)
    assert not any(k in json.dumps(canary) for k in subs)
    canary['metadata']['annotations']['bnjettag.io/placeholders'] = (
        f"{subs['__CONFIGMAP_NAME__']}, {subs['__BUNDLE_SHA256__']}, {subs['__MANIFEST_SHA256__']} (filled)")
    # own Job name: the c6017 Job (kai-delta0926-canary) is the v1 record
    canary['metadata']['name'] = 'kai-delta0926-canary-v2'
    for labels in (canary['metadata']['labels'], canary['spec']['template']['metadata']['labels']):
        labels['app'] = 'kai-delta0926-canary-v2'
    canary['metadata']['annotations']['bnjettag.io/status'] = canary['metadata']['annotations']['bnjettag.io/status'].replace(
        'canary/k_result.json', 'canary-v2/k_result.json')
    out = {'delta-canary-v2-job.json': canary,
           'discrim-c6017-job.json': discriminator(canary, 'kai-delta0926-discrim-c6017', 'c6017', subs),
           'discrim-other-job.json': discriminator(canary, 'kai-delta0926-discrim-other', 'other', subs)}
    for fname, job in out.items():
        (HERE / fname).write_text(json.dumps(job, indent=2) + '\n')
        print('WROTE', fname, job['metadata']['name'])
    print('BUNDLE', subs['__BUNDLE_SHA256__'], 'CONFIGMAP', subs['__CONFIGMAP_NAME__'], 'MANIFEST', subs['__MANIFEST_SHA256__'])


if __name__ == '__main__':
    main()
