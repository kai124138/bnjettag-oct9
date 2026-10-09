#!/usr/bin/env python3
"""Per-product GPU node survey for the benchmark generator (read-only; never schedules anything).

    python3 node_survey.py [--nodes-json FILE] [--out-dir evidence]

Reads the live node LIST (`kubectl get nodes -o json`; a single-node get is forbidden in cms-ml) or a
saved copy, and for every candidate product records: node count, the nvidia.com/* resource key the
nodes actually offer (allocatable, nonzero), the `nvidia.com/gpu.memory` label (card MiB), and per
node the allocatable CPU / memory / GPUs, taints, readiness, the driver label, and whether a pod of
ours can land there at all. "Schedulable for us": Ready, not cordoned, no NoSchedule/NoExecute taint
(our pods tolerate none; PreferNoSchedule is soft), and not excluded by hostname (c6017, the
pilot-b list, nrp_doctor.KNOWN_BAD_NODES). Allocatable is capacity, not free capacity: other
tenants' requests are not visible to us (cluster-scope pod list is forbidden).

Writes <out-dir>/node_survey_<UTC>.json and prints a table. Cluster facts with a date, not results.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRODUCTS = ['NVIDIA-L40', 'NVIDIA-L40S', 'NVIDIA-GeForce-RTX-4090', 'NVIDIA-GeForce-RTX-3090',
            'NVIDIA-RTX-A6000', 'NVIDIA-A40', 'NVIDIA-A100-SXM4-80GB']
REFERENCE = ['NVIDIA-A10']   # the baseline; benchmarked in the same harness since STUDY Amendment 1 (A1)
C6017 = 'hcc-nrp-shor-c6017.unl.edu'   # Delta REGRESSION_TICKET 2026-09-28
PILOT_B_BAD = ['k8s-chase-ci-07.calit2.optiputer.net', 'nautilus-ext-gpu01.fullerton.edu',
               'ren-gp-argo-01.madren.org']   # training-batch manifests/freeze.py BAD_NODES


def known_bad_nodes():
    spec = importlib.util.spec_from_file_location('nrp_doctor', REPO / 'nrp-lab' / 'nrp_doctor.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.KNOWN_BAD_NODES)


def excluded_nodes():
    out = {C6017: 'Delta REGRESSION_TICKET 2026-09-28 (epoch-0 NaN, fingerprint off)'}
    out.update({n: 'training-batch pilot-b exclusion list (freeze.py BAD_NODES)' for n in PILOT_B_BAD})
    out.update({n: f'nrp_doctor KNOWN_BAD_NODES: {why}' for n, why in known_bad_nodes().items()})
    return dict(sorted(out.items()))


def cpu(v):
    s = str(v)
    return int(s[:-1]) / 1000 if s.endswith('m') else float(s)


def mem_gi(v):
    s = str(v)
    for unit, f in (('Ki', 1 / 1024 ** 2), ('Mi', 1 / 1024), ('Gi', 1.0), ('Ti', 1024.0)):
        if s.endswith(unit):
            return float(s[:-2]) * f
    return float(s) / 1024 ** 3


def survey(nodes, excluded):
    products = {}
    for n in nodes:
        labels = n['metadata'].get('labels', {})
        product = labels.get('nvidia.com/gpu.product')
        if product not in PRODUCTS + REFERENCE:
            continue
        alloc = n.get('status', {}).get('allocatable', {})
        keys = {k: int(v) for k, v in alloc.items()
                if k.startswith('nvidia.com/') and k != 'nvidia.com/gpu.shared' and str(v) not in ('0', '')}
        taints = [{'key': t['key'], 'value': t.get('value', ''), 'effect': t['effect']}
                  for t in n.get('spec', {}).get('taints', []) or []]
        ready = next((c['status'] for c in n.get('status', {}).get('conditions', []) if c['type'] == 'Ready'), 'Unknown')
        name = n['metadata']['name']
        hard = [t for t in taints if t['effect'] in ('NoSchedule', 'NoExecute')]
        reasons = []
        if ready != 'True':
            reasons.append(f'Ready={ready}')
        if n.get('spec', {}).get('unschedulable'):
            reasons.append('cordoned')
        if hard:
            reasons.append('taint ' + ', '.join(f"{t['key']}={t['value']}:{t['effect']}" for t in hard))
        if name in excluded:
            reasons.append('excluded: ' + excluded[name])
        if not keys:
            reasons.append('no nvidia.com/* allocatable')
        products.setdefault(product, []).append({
            'node': name, 'ready': ready, 'unschedulable': bool(n.get('spec', {}).get('unschedulable')),
            'taints': taints, 'gpu_resources': keys, 'gpu_memory_label_mib': labels.get('nvidia.com/gpu.memory'),
            'driver_label': labels.get('nvidia.com/cuda.driver-version.full'),
            'alloc_cpu': cpu(alloc.get('cpu', '0')), 'alloc_mem_gi': round(mem_gi(alloc.get('memory', '0')), 1),
            'schedulable_for_us': not reasons, 'not_schedulable_because': reasons})
    result = {}
    for product in PRODUCTS + REFERENCE:
        rows = sorted(products.get(product, []), key=lambda r: r['node'])
        keys = sorted({k for r in rows for k in r['gpu_resources']})
        mib = sorted({int(r['gpu_memory_label_mib']) for r in rows if r['gpu_memory_label_mib']})
        ok = [r for r in rows if r['schedulable_for_us']]
        result[product] = {
            'role': 'baseline (benchmarked in the same harness, STUDY Amendment 1)' if product in REFERENCE else 'candidate',
            'nodes': len(rows), 'resource_keys': keys, 'card_mib_labels': mib,
            'schedulable_nodes': len(ok), 'schedulable_gpus_allocatable': sum(sum(r['gpu_resources'].values()) for r in ok),
            'schedulable_alloc_cpu': sorted({r['alloc_cpu'] for r in ok}),
            'schedulable_alloc_mem_gi': sorted({r['alloc_mem_gi'] for r in ok}),
            'per_node': rows}
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nodes-json', type=Path)
    ap.add_argument('--out-dir', type=Path, default=HERE / 'evidence')
    args = ap.parse_args()
    read_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    if args.nodes_json:
        nodes = json.loads(args.nodes_json.read_text())['items']
        source = f'{args.nodes_json} (saved kubectl get nodes -o json; file mtime ' \
                 f'{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(args.nodes_json.stat().st_mtime))})'
    else:
        out = subprocess.run(['kubectl', 'get', 'nodes', '-o', 'json', '--request-timeout=120s'],
                             capture_output=True, text=True, check=True)
        nodes = json.loads(out.stdout)['items']
        source = f'live kubectl get nodes -o json at {read_utc}'
    excluded = excluded_nodes()
    result = {'read_utc': read_utc, 'source': source, 'cluster_nodes': len(nodes), 'excluded_hostnames': excluded,
              'schedulable_rule': 'Ready=True, not cordoned, no NoSchedule/NoExecute taint, hostname not excluded',
              'products': survey(nodes, excluded)}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = args.out_dir / f"node_survey_{read_utc.replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(result, indent=1) + '\n')
    print(f'NODE_SURVEY {path} source: {source}; {len(nodes)} nodes')
    for product, s in result['products'].items():
        print(f"{product:26s} nodes {s['nodes']:3d} key {','.join(s['resource_keys']) or '-':20s} "
              f"card_mib {s['card_mib_labels']} schedulable {s['schedulable_nodes']} nodes / "
              f"{s['schedulable_gpus_allocatable']} GPUs  cpu {s['schedulable_alloc_cpu']} mem_gi {s['schedulable_alloc_mem_gi']}")
        for r in s['per_node']:
            flag = 'OK ' if r['schedulable_for_us'] else 'no '
            print(f"    {flag}{r['node'][:44]:44s} cpu {r['alloc_cpu']:6.1f} mem {r['alloc_mem_gi']:7.1f}Gi "
                  f"gpus {r['gpu_resources']} {'; '.join(r['not_schedulable_because'])}")


if __name__ == '__main__':
    main()
