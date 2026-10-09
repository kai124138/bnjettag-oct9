#!/usr/bin/env python3
"""Static checks on the generated benchmark manifests (PREFLIGHT evidence; stdlib only; never touches the cluster).

    python3 plan_check.py --tree EXTRACTED_42abed4b [--survey evidence/node_survey_<UTC>.json]

Per Job manifest (manifests/kai-gpubench-*.json):
  BENCH_PLAN validates with bench_driver.validate_plan against the bundle's campaigns/chang0926/index.json; every named
  config's sha256 equals its index row; bash -n on the pod script; WANDB_MODE disabled and no secret env; the Job
  deadline equals the 21,600 s [D6] window plus the pod deadline; requests == limits == 2 CPU / 8 Gi x the Job's
  largest K; the product pin and resource key match bench_plan.json; the four hostname exclusions, and the two Chang
  pilot-b nodes on the A10 Jobs only (PREFLIGHT critical v2 C5); the pinned-pod
  anti-affinity; the driver sha in the script equals code/bench_driver.py and the ConfigMap's; the A10 Jobs carry the
  yield-to-anchor rule. Per product: two Jobs, phase ids p1-p4 once each (STUDY Amendment 1).
Then GENERATOR_IDEMPOTENT: gen_bench.py re-run with the same survey rewrites every file byte-identical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MAN = HERE.parent / 'manifests'
EXCLUDED = {'hcc-nrp-shor-c6017.unl.edu', 'k8s-chase-ci-07.calit2.optiputer.net', 'nautilus-ext-gpu01.fullerton.edu',
            'ren-gp-argo-01.madren.org'}
PILOT_NODES = {'gpu-17.nrp.mghpcc.org', 'hcc-nrp-shor-c5805.unl.edu'}   # excluded on the A10 Jobs only (critical v2 C5)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', type=Path, required=True, help='an extraction of chang0926-code.tar.gz (42abed4b)')
    ap.add_argument('--survey', type=Path, default=None)
    args = ap.parse_args()
    sys.path.insert(0, str(HERE))
    import bench_driver as bd   # noqa: E402
    camp = args.tree / 'campaigns' / 'chang0926'
    index = {r['name']: r for r in json.loads((camp / 'index.json').read_text())['runs']}
    plan = json.loads((MAN / 'bench_plan.json').read_text())
    driver_sha = sha(HERE / 'bench_driver.py')
    cm = json.loads((MAN / f'configmap-bench-driver-{driver_sha[:8]}.json').read_text())
    assert cm['metadata']['annotations']['bnjettag.io/bench-driver-sha256'] == driver_sha
    assert hashlib.sha256(cm['data']['bench_driver.py'].encode()).hexdigest() == driver_sha
    print('# driver', driver_sha, 'ConfigMap', cm['metadata']['name'], 'payload sha256 equal')
    jobs = {j['name']: (p, j) for p in plan['products'] for j in p['jobs']}
    files = sorted(MAN.glob('kai-gpubench-*.json'))
    assert {f.stem for f in files} == set(jobs), (sorted(f.stem for f in files), sorted(jobs))
    failures = 0
    for f in files:
        m = json.loads(f.read_text())
        p, j = jobs[f.stem]
        spec = m['spec']['template']['spec']
        c = spec['containers'][0]
        env = {e['name']: e.get('value') for e in c['env']}
        bench_plan = json.loads(env['BENCH_PLAN'])
        problems = bd.validate_plan(bench_plan, camp)
        names = [n for ph in bench_plan['phases'] for n in ph['names']]
        config_ok = all(sha(camp / 'configs' / index[n]['file']) == index[n]['config_sha256'] for n in names)
        bash_n = subprocess.run(['bash', '-n'], input=c['args'][0], text=True, capture_output=True).returncode
        secret = any('secretKeyRef' in json.dumps(e) for e in c['env'])
        k_max = max(ph['k'] for ph in bench_plan['phases'])
        res = c['resources']
        expr = spec['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0][
            'matchExpressions']
        anti = spec['affinity'].get('podAntiAffinity', {}).get('requiredDuringSchedulingIgnoredDuringExecution', [])
        hosts = set(next(e['values'] for e in expr if e['key'] == 'kubernetes.io/hostname'))
        checks = {
            'plan_valid': not problems,
            'config_sha_ok': config_ok,
            'bash_n': bash_n == 0,
            'wandb_disabled': env.get('WANDB_MODE') == 'disabled' and not secret,
            'deadlines': m['spec']['activeDeadlineSeconds'] == 21600 + spec['activeDeadlineSeconds']
                         and spec['activeDeadlineSeconds'] == j['pod_active_deadline_seconds'],
            'shape': res['requests'] == res['limits'] and res['requests']['cpu'] == str(2 * k_max)
                     and res['requests']['memory'] == f'{8 * k_max}Gi' and res['requests'].get(p['resource_key']) == '1'
                     and k_max == j['k_max'],
            'product_pin': {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': [p['product']]} in expr,
            'exclusions': hosts >= EXCLUDED,
            'pilot_nodes': (hosts & PILOT_NODES) == (PILOT_NODES if p['product'] == 'NVIDIA-A10' else set()),
            'anti_affinity': anti == [{'labelSelector': {'matchLabels': {'bnjettag.io/gpu-bench-pinned': 'true'}},
                                       'topologyKey': 'kubernetes.io/hostname'}]
                             and m['spec']['template']['metadata']['labels'].get('bnjettag.io/gpu-bench-pinned') == 'true',
            'driver_sha': f"echo '{driver_sha}  /cmbench/bench_driver.py'" in c['args'][0]
                          and any(v.get('configMap', {}).get('name') == cm['metadata']['name'] for v in spec['volumes']),
            'yield_rule': ('bnjettag.io/yield-to-anchor' in m['metadata']['annotations']) == (p['product'] == 'NVIDIA-A10'),
            'no_restart': m['spec']['backoffLimit'] == 0 and 'podFailurePolicy' not in m['spec'],
        }
        bad = [k for k, v in checks.items() if not v]
        failures += bool(bad)
        print(f"{f.name} {'PLAN_OK' if not bad else 'PLAN_FAIL ' + ','.join(bad)} phases "
              f"{' '.join(ph['phase'] for ph in bench_plan['phases'])} pod {res['requests']['cpu']} CPU "
              f"{res['requests']['memory']} arms {len(names)} job_deadline {m['spec']['activeDeadlineSeconds']} "
              f"pod_deadline {spec['activeDeadlineSeconds']}" + (f" problems {problems}" if problems else ''))
    for p in plan['products']:
        ids = sorted(ph['phase'].split('-')[0] for j in p['jobs'] for ph in j['phases'])
        ok = len(p['jobs']) == 2 and ids == ['p1', 'p2', 'p3', 'p4']
        failures += not ok
        print(f"# {p['product']}: {len(p['jobs'])} Jobs, phase ids {' '.join(ids)} {'OK' if ok else 'FAIL'}")
    before = {f.name: sha(f) for f in MAN.glob('*.json')}
    cmd = [sys.executable, str(HERE / 'gen_bench.py')] + (['--survey', str(args.survey)] if args.survey else [])
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    after = {f.name: sha(f) for f in MAN.glob('*.json')}
    idem = before == after
    failures += not idem
    print('GENERATOR_IDEMPOTENT' if idem else f'GENERATOR_NOT_IDEMPOTENT {sorted(k for k in after if before.get(k) != after[k])}')
    print('PLAN_CHECK_ALL_OK' if not failures else f'PLAN_CHECK_FAILURES {failures}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
