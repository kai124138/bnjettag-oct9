#!/usr/bin/env python3
"""Generate the GPU-product benchmark Jobs and the driver ConfigMap. Writes files; never applies anything.

    python3 gen_bench.py [--survey evidence/node_survey_<UTC>.json] [--k-low-rule study-d2]
    python3 gen_bench.py --probe PRODUCT:K:N [--out-dir DIR]     # STUDY [D4] G_p probe Job only

Outputs in ../manifests/:
  kai-gpubench-<slug>-krule.json      per product, the K_rule Job: phase E at K_run, then A07 at K_run
  kai-gpubench-<slug>-klow.json       per product, the K_low Job: phase E at K_low, then A07 at K_low
  configmap-bench-driver-<sha8>.json  immutable ConfigMap kai-gpubench-driver-<sha10> holding bench_driver.py
  bench_plan.json                     the K table: every input, every cap, every Job, its phases and deadlines
Each Job is non-indexed, backoffLimit 0, no retries.

Frozen inputs (brief 2026-09-29; none is edited here): bundle 42abed4b in ConfigMap
kai-chang0926-code-42abed4b5d, manifest sha 041f981a, fingerprint ConfigMap kai-chang0926-fp-e9511d1aeb,
anchor cache /data/chang-n64-20260926/n64/data, batch 2,790 (the configs), TF32 off, trace every 10
epochs (the configs), and the pilot-b pod header (training-batch manifests/pilot-b-k5-job.json), minus
W&B. Card memory, resource key, taints and allocatable come from the node survey (node_survey.py),
never from this file.

Products (STUDY Amendment 1, A1): the seven candidates and the NVIDIA-A10 baseline, all in this harness. The A10 Jobs
also exclude the Chang pilot-b nodes, PILOT_NODES (PREFLIGHT critical v2 C5).
K per product and class:
  K_rule = floor(0.90 x card MiB / per-process MiB); per-process = the A10 figures under TF
           allow_growth (E 4,350 MiB, A07 8,446 MiB; training-batch RUN.md "Takeover check").
  K_run  = min(K_rule, node cap, name pool 16); node cap = the largest K some schedulable node of the
           product can hold at 2 CPU and 8 Gi per arm after a reserve of 2 CPU and 16 Gi for the node's
           own daemons (allocatable is capacity, not free capacity).
  K_low  = STUDY.md [D2] (default --k-low-rule study-d2; orchestrator decision 2026-09-29, the STUDY governs): the
           class's A10 K (E 4, A07 2), or K_run - 1 where K_run <= that (so the A10 itself: E 3, A07 1).
           --k-low-rule half = max(1, K_run // 2), the brief's first reading, kept for comparison only.
Job shapes (STUDY Amendment 1, A2 and B6): two Jobs per product. The pod requests 2 CPU and 8 Gi x the
largest K of its own two phases, and the driver pins every phase's arms to exactly 2 x K CPUs. A required
pod anti-affinity keeps two pinned benchmark pods off one node, where both would pin the same first CPUs.
Phase ids are unique per product: p1 (E) and p2 (A07) in the K_rule Job, p3 (E) and p4 (A07) in the K_low Job.
Deadlines: the pod's activeDeadlineSeconds bounds the run from pod start; the Job's (which counts from Job
creation, so Pending time too) is the STUDY [D6] 6-h not-practical window plus that bound, a backstop only.
stop_after 21 (traced epochs 1, 10, 20). Names: the first K of the class list (E: A s1-s8 then B s1-s8; A07:
C s1-s8 then A07-350 s1-s8), distinct within a phase.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
CAMP = HERE.parent
REPO = HERE.parents[2]
TB = REPO / 'campaigns' / '2026-09-26-training-batch'
OUT = CAMP / 'manifests'

BUNDLE_TAR = TB / 'manifests' / 'chang0926-code.tar.gz'
BUNDLE_SHA = '42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0'
MANIFEST_SHA = '041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42'
CODE_CM = 'kai-chang0926-code-42abed4b5d'
FP_PAYLOAD = TB / 'manifests' / 'configmap-fp-e9511d1a.json'
FP_CM, FP_SHA = 'kai-chang0926-fp-e9511d1aeb', 'e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1'
FP_RUN, FP_EXPECT = 'chang0926-a-n64-s1', 11559681
DRIVER = HERE / 'bench_driver.py'
DATA_ROOT = '/data/chang-n64-20260926'
BENCH_BASE = DATA_ROOT + '/gpu-bench'
CAMPAIGN_DIR = '/work/code/campaigns/chang0926'
STOP_AFTER = 21
# host_rss_mb= is printed only when the gate env is set (ablation.py:645-647); the window ends at
# process epoch 105 > 21, so the gate never evaluates and never exits 5 here.
RSS_LIMIT_MB, RSS_WINDOW = 8192, '5:105'

BASELINE = 'NVIDIA-A10'   # STUDY Amendment 1 (A1): the headline comparator, measured in this harness
PRODUCTS = ['NVIDIA-L40', 'NVIDIA-L40S', 'NVIDIA-GeForce-RTX-4090', 'NVIDIA-GeForce-RTX-3090',
            'NVIDIA-RTX-A6000', 'NVIDIA-A40', 'NVIDIA-A100-SXM4-80GB', BASELINE]
PER_PROCESS_MIB = {'E': 4350, 'A07': 8446}
PER_PROCESS_SOURCE = ('A10, TF_FORCE_GPU_ALLOW_GROWTH, nvidia-smi --query-compute-apps: E 4,350 MiB (K=5 pod, c5805), '
                      'A07 8,446 MiB (K=3 pods, gpu-16 and gpu-17); campaigns/2026-09-26-training-batch/RUN.md '
                      '"Takeover check, 2026-09-29T02:47-03:10Z"')
RULE_FRACTION = 0.90
CPU_PER_ARM, MEM_GI_PER_ARM = 2, 8
NODE_RESERVE_CPU, NODE_RESERVE_MEM_GI = 2, 16
CLASS_NAMES = {
    'E': [f'chang0926-a-n64-s{s}' for s in range(1, 9)] + [f'chang0926-b-n64-s{s}' for s in range(1, 9)],
    'A07': [f'chang0926-c-n64-s{s}' for s in range(1, 9)] + [f'chang0926-a07-350-n64-s{s}' for s in range(1, 9)],
}
# activeDeadlineSeconds only bounds a hung pod. A10 aggregate cost per run-epoch (RUN.md "Takeover check":
# E 138.8 s/epoch at K=5 -> 27.8 s; A07 130.7 s/epoch at K=3 with one F arm of 80.9 s/epoch ->
# (130.7 - 130.7/80.9 x 27.8) / 2 = 42.9 s), rounded up; x2.5 margin for a product or node slower than the A10.
A10_S_PER_RUN_EPOCH = {'E': 28.0, 'A07': 44.0}
# Expected runtime, second bound (STUDY Compute budget): every process at the upper end of the A10's per-process
# s, 105-140 s (pilot-b K=5 slowest arm [D1] 140.4 s, code/evidence/a10_baseline_summary.json).
A10_PER_PROCESS_S = 140.0
DEADLINE_MARGIN, HEADER_S, PHASE_OVERHEAD_S, STAGGER_S = 2.5, 1800, 900, 15
D6_WINDOW_S = 6 * 3600   # STUDY [D6] / exclusion rule 3: not Running 6 h after apply = not practical
PROBE_JOB_DEADLINE_S, PROBE_POD_DEADLINE_S, PROBE_WINDOW_MIN = 3600, 1800, 30   # STUDY [D4]
STALL_S, SAMPLE_S = 3600, 60
NRP_WINDOW_H = 3.0   # NRP's rolling GPU-utilization window (nrp-nautilus-setup.md, "GPU utilization floor")
LABELS = {'user': 'kai', 'campaign': 'gpu-bench-20260929'}
PIN_LABEL = 'bnjettag.io/gpu-bench-pinned'   # the pods whose phases pin CPUs; the anti-affinity keeps them apart
A10_K = {'E': 4, 'A07': 2}   # STUDY.md [D2] (designed, 2026-09-29): the class's compliant A10 K
K_LOW_RULES = {'half': 'K_low = max(1, K_run // 2) (brief 2026-09-29)',
               'study-d2': 'K_low = A10 K of the class (E 4, A07 2), or K_run - 1 where K_run <= it (STUDY.md [D2])'}
# (shape, K key, first phase number): STUDY Amendment 1 (A2): one Job per (product, pod shape)
JOB_SHAPES = (('krule', 'k_run', 1), ('klow', 'k_low', 3))
YIELD_RULE = ("Kai's priority rule, pilots first (STUDY Amendment 1, A1): apply only while no Chang pilot-b pod is "
              "Pending; if a Chang pilot-b pod is Pending while this Job has a pod, delete this Job. Check: kubectl -n "
              "cms-ml get pods -l campaign=chang-n64-20260926 --field-selector=status.phase=Pending -o "
              "custom-columns=NAME:.metadata.name,APP:.metadata.labels.app (any APP kai-chang0926-pilot-b*). "
              "cluster-ops; RUN.md operating note")
# The Chang pilot-b nodes (pilotb3 on gpu-17, pilotb5 on c5805; read-only reads 08:41Z, 09:03Z and 09:47Z 2026-09-29),
# excluded from the A10 Jobs only (PREFLIGHT critical v2 C5); no other product has a pilot on its nodes
PILOT_NODES = ('gpu-17.nrp.mghpcc.org', 'hcc-nrp-shor-c5805.unl.edu')


def k_low_of(cls, k_run, rule):
    if rule == 'half':
        return max(1, k_run // 2)
    return A10_K[cls] if k_run > A10_K[cls] else max(1, k_run - 1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def known_bad_nodes():
    spec = importlib.util.spec_from_file_location('nrp_doctor', REPO / 'nrp-lab' / 'nrp_doctor.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.KNOWN_BAD_NODES)


def slug_of(product):
    return re.sub(r'[^a-z0-9]+', '-', product.lower().removeprefix('nvidia-')).strip('-')


def node_cap(nodes):
    """Largest K some node can hold at CPU_PER_ARM / MEM_GI_PER_ARM per arm after the node reserve."""
    return max(min(int((n['alloc_cpu'] - NODE_RESERVE_CPU) // CPU_PER_ARM),
                   int((n['alloc_mem_gi'] - NODE_RESERVE_MEM_GI) // MEM_GI_PER_ARM)) for n in nodes)


def holding(nodes, k):
    """Schedulable nodes whose allocatable can hold a K-arm pod, and an upper bound on how many such
    pods fit on them by allocatable (other tenants' requests are invisible to us)."""
    ok = [n for n in nodes if n['alloc_cpu'] - NODE_RESERVE_CPU >= CPU_PER_ARM * k
          and n['alloc_mem_gi'] - NODE_RESERVE_MEM_GI >= MEM_GI_PER_ARM * k]
    pods = sum(min(sum(n['gpu_resources'].values()),
                   int((n['alloc_cpu'] - NODE_RESERVE_CPU) // (CPU_PER_ARM * k)),
                   int((n['alloc_mem_gi'] - NODE_RESERVE_MEM_GI) // (MEM_GI_PER_ARM * k))) for n in ok)
    return [n['node'] for n in ok], pods


def pod_deadline(phases):
    """The pod's bound from pod start: header + per phase (K x 21 x A10 cost x 2.5 + stagger + overhead), up to 600 s."""
    raw = HEADER_S + sum(p['k'] * STOP_AFTER * A10_S_PER_RUN_EPOCH[p['class']] * DEADLINE_MARGIN
                         + STAGGER_S * p['k'] + PHASE_OVERHEAD_S for p in phases)
    return int(-(-raw // 600) * 600)


def expected_compute(phases):
    """Compute seconds of one Job between the two A10 bounds (STUDY Compute budget); arithmetic, not a measurement.
    aggregate: the product no faster than an A10 per GPU (K x 21 x E 28 / A07 44 s); per-process: every process at
    the A10's 140 s per epoch whatever K (21 x 140 s per phase). Header and per-phase start-up not included."""
    agg = sum(p['k'] * STOP_AFTER * A10_S_PER_RUN_EPOCH[p['class']] for p in phases)
    per_process = sum(STOP_AFTER * A10_PER_PROCESS_S for _ in phases)
    return {'a10_aggregate_bound_s': agg, 'a10_per_process_bound_s': per_process,
            'upper_h': round(max(agg, per_process) / 3600, 2),
            'upper_with_header_allowance_h': round((max(agg, per_process) + HEADER_S) / 3600, 2)}


def plan_job(p, shape, nodes):
    key, first = {s: (k, f) for s, k, f in JOB_SHAPES}[shape]
    phases = []
    for i, cls in enumerate(('E', 'A07')):
        k = p['classes'][cls][key]
        phases.append({'phase': f'p{first + i}-{cls}-k{k}', 'class': cls, 'k': k, 'names': CLASS_NAMES[cls][:k]})
    k_max = max(ph['k'] for ph in phases)
    held, pods = holding(nodes, k_max)
    deadline = pod_deadline(phases)
    root_slug = f"{p['slug']}-{shape}"
    runtime = expected_compute(phases)
    return {'shape': shape, 'name': f'kai-gpubench-{root_slug}', 'root_slug': root_slug,
            'run_root': f'{BENCH_BASE}/{root_slug}', 'phases': phases, 'k_max': k_max,
            'pod_request': {'cpu': CPU_PER_ARM * k_max, 'memory_gi': MEM_GI_PER_ARM * k_max},
            'nodes_that_can_hold_pod': held, 'max_pods_by_allocatable_upper_bound': pods,
            'run_epochs': sum(ph['k'] for ph in phases) * STOP_AFTER,
            'pod_active_deadline_seconds': deadline, 'job_active_deadline_seconds': D6_WINDOW_S + deadline,
            'expected_compute': runtime,
            'longer_than_nrp_window_at_upper_bound': runtime['upper_with_header_allowance_h'] > NRP_WINDOW_H}


def plan_product(product, s, k_low_rule='study-d2'):
    keys, cards = s['resource_keys'], s['card_mib_labels']
    assert len(keys) == 1, (product, keys)
    assert len(cards) == 1, (product, cards)
    nodes = [n for n in s['per_node'] if n['schedulable_for_us']]
    assert nodes, f'{product}: no schedulable node'
    card, cap = cards[0], node_cap(nodes)
    classes = {}
    for cls in ('E', 'A07'):
        k_rule = int(RULE_FRACTION * card // PER_PROCESS_MIB[cls])
        k_run = min(k_rule, cap, len(CLASS_NAMES[cls]))
        assert k_run >= 1, (product, cls, k_rule, cap)
        binding = [f'node cap {cap} (2 CPU + 8 Gi per arm, node reserve 2 CPU / 16 Gi; largest schedulable node '
                   f'{max(n["alloc_cpu"] for n in nodes):g} CPU / {max(n["alloc_mem_gi"] for n in nodes):g} Gi)'] \
            if cap < k_rule else []
        binding += [f'name pool {len(CLASS_NAMES[cls])}'] if len(CLASS_NAMES[cls]) < min(k_rule, cap) else []
        classes[cls] = {'per_process_mib': PER_PROCESS_MIB[cls], 'k_rule': k_rule, 'k_run': k_run,
                        'k_low': k_low_of(cls, k_run, k_low_rule), 'binding_caps': binding,
                        'predicted_peak_fraction_at_k_run': round(k_run * PER_PROCESS_MIB[cls] / card, 3)}
    p = {'product': product, 'slug': slug_of(product), 'role': 'baseline' if product == BASELINE else 'candidate',
         'resource_key': keys[0], 'card_mib': card, 'k_low_rule': K_LOW_RULES[k_low_rule],
         'nodes': s['nodes'], 'schedulable_nodes': len(nodes),
         'schedulable_gpus_allocatable': s['schedulable_gpus_allocatable'], 'node_cap': cap, 'classes': classes}
    p['jobs'] = [plan_job(p, shape, nodes) for shape, _, _ in JOB_SHAPES]
    p['run_epochs'] = sum(j['run_epochs'] for j in p['jobs'])
    return p


def driver_configmap(text, digest):
    return {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
            'metadata': {'name': 'kai-gpubench-driver-' + digest[:10], 'namespace': 'cms-ml', 'labels': LABELS,
                         'annotations': {'bnjettag.io/bench-driver-sha256': digest,
                                         'bnjettag.io/source': 'campaigns/2026-09-29-gpu-benchmark/code/bench_driver.py'}},
            'data': {'bench_driver.py': text}}


def setup_lines():
    """Pod header shared by the benchmark and the probe: bundle sha, pins, manifest sha, GPU gate, cache READY,
    GPU_INFO, the node CPU and RAM (STUDY Amendment 1, B4), pip-freeze hash and the unchanged fingerprint gate
    (a mismatch starts nothing). $BR must be set."""
    return [
        'export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2',
        'export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1',
        'mkdir -p /work/code',
        f"echo '{BUNDLE_SHA}  /cmcode/hgq2.tar.gz' | sha256sum -c -",
        'tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1',
        'export PYTHONPATH=/work/code',
        f'export BNJ_DATA_ROOT={DATA_ROOT} BNJ_RUN_ROOT="$BR" BNJ_CAMPAIGN_DIR={CAMPAIGN_DIR}',
        # W&B off: no secret is mounted, no stage, and the driver calls run_training(remote=False).
        'unset BNJ_STAGE WANDB_PROJECT WANDB_ENTITY WANDB_API_KEY WANDB_TAGS',
        'export WANDB_MODE=disabled',
        'export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0',
        f'export BNJ_RSS_GATE_LIMIT_MB={RSS_LIMIT_MB} BNJ_RSS_GATE_WINDOW={RSS_WINDOW}',
        'pip install -q --no-cache-dir -r /work/code/requirements-training.txt',
        'NVLIBS=$(python -c "import glob; print(\':\'.join(sorted(glob.glob(\'/usr/local/lib/python*/site-packages/nvidia/*/lib\'))))")',
        'export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        'cd /work/code',
        'MSHA=$(python -c "import run_study; print(run_study.manifest()[\'sha256\'])")',
        f'test "$MSHA" = "{MANIFEST_SHA}" || {{ echo "MANIFEST_SHA_MISMATCH $MSHA"; exit 1; }}',
        'echo "MANIFEST_SHA_OK $MSHA"',
        'export BNHGQ2_CODE_SHA256="$MSHA"',
        'python -c "import tensorflow as tf; assert tf.config.list_physical_devices(\'GPU\'); print(\'GPU_GATE_PASS\')"',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        'echo CACHE_READY',
        'echo "GPU_INFO $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || echo na)"',
        # The node's CPU and RAM (policy item 1 "Record ... CPU and host RAM"; STUDY Amendment 1, B4)
        "echo \"CPU_MODEL $(grep -m1 '^model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')\"",
        "echo \"CPU_COUNTS node_logical $(grep -c '^processor' /proc/cpuinfo) allowed $(nproc) "
        "cpus_allowed_list $(grep Cpus_allowed_list /proc/self/status | cut -f2) "
        "cgroup_cpu_max $(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo na)\"",
        "(lscpu 2>/dev/null || true) | grep -E '^(Model name|Socket|Core|Thread|CPU\\(s\\)|On-line|CPU max MHz|CPU MHz|NUMA node\\(s\\))' "
        "| sed 's/^/LSCPU /' || true",
        "echo \"HOST_MEM $(grep MemTotal /proc/meminfo | tr -s ' ') cgroup_memory_max $(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo na)\"",
        'df -h /data',
        'echo "PIP_FREEZE_SHA256 $(python -m pip freeze --all | sha256sum | cut -d\' \' -f1)"',
        # The existing GPU fingerprint gate (Delta gate 15), unchanged: a mismatch starts no arm.
        f"echo '{FP_SHA}  /cmfp/fingerprint_check.py' | sha256sum -c -",
        'FP=0',
        f'python -u /cmfp/fingerprint_check.py --run {FP_RUN} --expect {FP_EXPECT} --data-root {DATA_ROOT} '
        f'--campaign-dir {CAMPAIGN_DIR} --env-report || FP=$?',
        'if [ "$FP" != 0 ]; then echo "FINGERPRINT_GATE_FAIL exit=$FP node=${NODE_NAME:-na}; no arm started"; exit "$FP"; fi',
    ]


def script(p, j, driver_sha):
    return '\n'.join([
        'set -euo pipefail',
        f"BR={j['run_root']}",
        f'echo "BENCH_POD ${{POD_NAME:-na}} product {p["product"]} slug {j["root_slug"]} shape {j["shape"]} '
        f'$(date -u +%Y-%m-%dT%H:%M:%SZ)"',
        'echo "HOSTNAME_NODE ${NODE_NAME:-na}"',
        # A benchmark never resumes (ablation.run_training would resume from latest.json): refuse a used
        # root before any work. A manual re-run moves the Job's directory aside first, never deletes it.
        'if [ -e "$BR/samples.csv" ] || compgen -G "$BR/p[0-9]*" > /dev/null; then '
        'echo "BENCH_ROOT_NOT_EMPTY $BR: move it aside (never delete), then re-apply"; exit 11; fi',
        'mkdir -p "$BR"',
        'exec > >(tee -a "$BR/pod-${POD_NAME:-pod}.log") 2>&1',
        *setup_lines(),
        f"echo '{driver_sha}  /cmbench/bench_driver.py' | sha256sum -c -",
        # exec: the driver becomes PID 1, so a deletion or the deadline delivers SIGTERM to its handler, which
        # stops the arms within the 180 s grace (bash as PID 1 would ignore SIGTERM).
        'exec python -u /cmbench/bench_driver.py pod --bench-root "$BR" --plan-json "$BENCH_PLAN"',
    ]) + '\n'


def job(p, j, driver_cm, driver_sha, excluded, survey_ref):
    name = j['name']
    sibling = next(o['name'] for o in p['jobs'] if o['shape'] != j['shape'])
    labels = {**LABELS, 'app': name, 'bnjettag.io/arms-per-pod': str(j['k_max']), 'bnjettag.io/job-shape': j['shape'],
              'bnjettag.io/gpu-product-slug': p['slug'], PIN_LABEL: 'true'}
    plan = {'product': p['product'], 'slug': j['root_slug'], 'product_slug': p['slug'], 'shape': j['shape'],
            'card_mib': p['card_mib'], 'stop_after': STOP_AFTER, 'pod_cpu_request': j['pod_request']['cpu'],
            'phases': j['phases']}
    caps = '; '.join(f"{cls}: K_rule {c['k_rule']}, K_run {c['k_run']}, K_low {c['k_low']}"
                     + (f" (capped by {' and '.join(c['binding_caps'])})" if c['binding_caps'] else ' (no cap binds)')
                     for cls, c in p['classes'].items())
    rt = j['expected_compute']
    annotations = {
        'bnjettag.io/telemetry-only': 'GPU-product throughput benchmark, campaigns/2026-09-29-gpu-benchmark; nothing it writes is a result',
        'bnjettag.io/gpu-product': f"{p['product']} via {p['resource_key']} ({p['card_mib']} MiB, node label nvidia.com/gpu.memory)",
        'bnjettag.io/job-shape': (f"{j['shape']}: the {'K_rule' if j['shape'] == 'krule' else 'K_low'} Job of {p['product']} "
                                  f"(pod {j['pod_request']['cpu']} CPU / {j['pod_request']['memory_gi']}Gi); sibling Job "
                                  f"{sibling}; STUDY Amendment 1 (A2, B6)"),
        'bnjettag.io/phases': ' '.join(ph['phase'] for ph in j['phases']) + f'; stop_after {STOP_AFTER} (traced epochs 1, 10, 20)',
        'bnjettag.io/k-rule': (f'K_rule = floor({RULE_FRACTION} x {p["card_mib"]} / per-process MiB), per-process E '
                               f'{PER_PROCESS_MIB["E"]} / A07 {PER_PROCESS_MIB["A07"]} ({PER_PROCESS_SOURCE}); '
                               + p['k_low_rule']),
        'bnjettag.io/k-caps': caps,
        'bnjettag.io/per-arm-resources': (f"{CPU_PER_ARM} CPU and {MEM_GI_PER_ARM}Gi per arm: the pod requests them for "
                                          f"its largest K ({j['k_max']}), and every phase's K arms are pinned to exactly "
                                          f"{CPU_PER_ARM} x K CPUs, the first {CPU_PER_ARM}K of the pod's allowed set "
                                          '(bench_driver --cpus; thread env as pilot-b). STUDY rule 5: a phase whose steady '
                                          'cgroup cores / K exceed 2.1 is above budget and kept out of T'),
        'bnjettag.io/cpu-pin-anti-affinity': ('required pod anti-affinity on ' + PIN_LABEL + ' per node: two pinned '
                                              'benchmark pods on one node would pin the same first CPUs of a shared pool'),
        'bnjettag.io/wandb': 'disabled: no secret mounted, WANDB_MODE=disabled, bench_driver calls ablation.run_training(remote=False)',
        'bnjettag.io/gpu-fingerprint': (f'{FP_CM} sha256 {FP_SHA[:16]}: {FP_RUN} initial_ebops == {FP_EXPECT} before '
                                        'any arm, else exit 9 (Delta REGRESSION_TICKET); a mismatch on a new product is a finding'),
        'bnjettag.io/bundle-sha256': f'{BUNDLE_SHA} ({CODE_CM}, manifest {MANIFEST_SHA[:8]}), unchanged',
        'bnjettag.io/bench-driver': f'{driver_cm} sha256 {driver_sha}',
        'bnjettag.io/run-root': f"{j['run_root']}/<phase>/runs/<name>; samples.csv every {SAMPLE_S} s",
        'bnjettag.io/retries': 'backoffLimit 0 and no podFailurePolicy: never re-run automatically (a preempted pod fails the Job)',
        'bnjettag.io/active-deadline': (f"pod {j['pod_active_deadline_seconds']} s from pod start = {HEADER_S} s header + per "
                                        f"phase (K x {STOP_AFTER} x A10 s/run-epoch E {A10_S_PER_RUN_EPOCH['E']:g} / A07 "
                                        f"{A10_S_PER_RUN_EPOCH['A07']:g} x {DEADLINE_MARGIN} + {STAGGER_S} s x K + "
                                        f"{PHASE_OVERHEAD_S} s), rounded up to 600 s; Job {j['job_active_deadline_seconds']} s "
                                        f"from creation (Pending counts) = the {D6_WINDOW_S} s [D6] window + the pod bound, a backstop"),
        'bnjettag.io/expected-runtime': (f"compute {rt['a10_aggregate_bound_s'] / 3600:.2f} h at the A10 aggregate cost "
                                         f"(E {A10_S_PER_RUN_EPOCH['E']:g} / A07 {A10_S_PER_RUN_EPOCH['A07']:g} s per run-epoch), "
                                         f"{rt['a10_per_process_bound_s'] / 3600:.2f} h at the A10 per-process {A10_PER_PROCESS_S:g} s "
                                         f"per epoch; {rt['upper_with_header_allowance_h']:.2f} h at the larger bound with the "
                                         f"{HEADER_S} s header allowance; arithmetic, not a measurement. STUDY Amendment 1 "
                                         '(B5): a phase under 40 % mean GPU utilization is a finding, not an exclusion'),
        'bnjettag.io/not-practical-after': ('6 h after kubectl apply of this Job with no Running pod: delete this Job only (its '
                                            'sibling is judged on its own shape) and keep the PodScheduled message (STUDY [D6], '
                                            'rule 3, Amendment 1 B6); cluster-ops'),
        'bnjettag.io/narrow-pool': ('one product on purpose: the controlled timing comparison the setup doc (Pool policy) '
                                    'allows; decisions.md 2026-09-29; ends when the benchmark Jobs are deleted'),
        'bnjettag.io/node-survey': (f"{survey_ref}: {p['schedulable_nodes']} schedulable of {p['nodes']} nodes; "
                                    f"{len(j['nodes_that_can_hold_pod'])} can hold this pod by allocatable"),
    }
    hostnames = excluded
    if p['product'] == BASELINE:
        annotations['bnjettag.io/baseline'] = ('the A10 comparator of the headline question, measured in this harness '
                                               '(STUDY Amendment 1, A1); pilot-b telemetry is a labelled cross-check only')
        annotations['bnjettag.io/yield-to-anchor'] = YIELD_RULE
        annotations['bnjettag.io/pilot-nodes-excluded'] = (
            ' and '.join(PILOT_NODES) + ', the Chang pilot-b nodes, are excluded from the A10 Jobs only (PREFLIGHT critical '
            "v2 C5): no pinned benchmark arm runs on the anchor's nodes, and falsifier (i)'s later pilot windows stay "
            'free of benchmark load')
        hostnames = sorted(set(excluded) | set(PILOT_NODES))
    env = [{'name': 'NODE_NAME', 'valueFrom': {'fieldRef': {'fieldPath': 'spec.nodeName'}}},
           {'name': 'POD_NAME', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}}},
           {'name': 'WANDB_MODE', 'value': 'disabled'},
           {'name': 'BENCH_PLAN', 'value': json.dumps(plan, separators=(',', ':'))},
           {'name': 'BENCH_SAMPLE_SECONDS', 'value': str(SAMPLE_S)},
           {'name': 'BENCH_STALL_SECONDS', 'value': str(STALL_S)},
           {'name': 'BENCH_STAGGER_SECONDS', 'value': str(STAGGER_S)}]
    res = {'cpu': str(j['pod_request']['cpu']), 'memory': f"{j['pod_request']['memory_gi']}Gi",
           'ephemeral-storage': '24Gi', p['resource_key']: '1'}
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': annotations},
            'spec': {'backoffLimit': 0, 'activeDeadlineSeconds': j['job_active_deadline_seconds'],
                     'ttlSecondsAfterFinished': 604800,
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'activeDeadlineSeconds': j['pod_active_deadline_seconds'],
                         'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {
                             'nodeSelectorTerms': [{'matchExpressions': [
                                 {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': [p['product']]},
                                 {'key': 'kubernetes.io/hostname', 'operator': 'NotIn', 'values': hostnames}]}]}},
                             'podAntiAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': [{
                                 'labelSelector': {'matchLabels': {PIN_LABEL: 'true'}},
                                 'topologyKey': 'kubernetes.io/hostname'}]}},
                         'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'bench', 'image': 'python:3.12', 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [script(p, j, driver_sha)], 'env': env,
                                         'resources': {'requests': dict(res), 'limits': dict(res)},
                                         'volumeMounts': [{'mountPath': '/cmcode', 'name': 'code', 'readOnly': True},
                                                          {'mountPath': '/work', 'name': 'work'},
                                                          {'mountPath': '/data', 'name': 'persistent'},
                                                          {'mountPath': '/cmfp', 'name': 'fingerprint', 'readOnly': True},
                                                          {'mountPath': '/cmbench', 'name': 'bench', 'readOnly': True}]}],
                         'volumes': [{'name': 'code', 'configMap': {'name': CODE_CM, 'defaultMode': 420}},
                                     {'name': 'work', 'emptyDir': {'sizeLimit': '24Gi'}},
                                     {'name': 'persistent', 'persistentVolumeClaim': {'claimName': 'kai-data'}},
                                     {'name': 'fingerprint', 'configMap': {'name': FP_CM, 'defaultMode': 420}},
                                     {'name': 'bench', 'configMap': {'name': driver_cm, 'defaultMode': 420}}]}}}}


def probe_script(p, k):
    pr = f"{BENCH_BASE}/probe-{p['slug']}-k{k}"
    return '\n'.join([
        'set -euo pipefail',
        f'BR={pr}',
        f'echo "PROBE_POD ${{POD_NAME:-na}} product {p["product"]} K {k} $(date -u +%Y-%m-%dT%H:%M:%SZ)"',
        'echo "HOSTNAME_NODE ${NODE_NAME:-na}"',
        'mkdir -p "$BR"',
        'exec > >(tee -a "$BR/${POD_NAME:-pod}.log") 2>&1',
        *setup_lines(),
        'echo "PROBE_DONE ${POD_NAME:-na} node ${NODE_NAME:-na} $(date -u +%Y-%m-%dT%H:%M:%SZ)"',
    ]) + '\n'


def probe_job(p, k, n, excluded, survey_ref):
    """STUDY [D4]: n production-shaped pods (K arms: 2K CPU, 8K Gi, one GPU of the product) that run only the pod
    header and the fingerprint gate, then exit. G_obs = pods Running within 30 min of apply; Q_p = their median wait
    (bench_summary.py probe). Indexed so one failed pod (e.g. exit 9) does not stop the others."""
    name = f"kai-gpuprobe-{p['slug']}-k{k}"
    labels = {**LABELS, 'app': name, 'bnjettag.io/arms-per-pod': str(k), 'bnjettag.io/probe': 'true'}
    annotations = {
        'bnjettag.io/telemetry-only': 'STUDY [D4] schedulability probe, campaigns/2026-09-29-gpu-benchmark; no training',
        'bnjettag.io/probe': (f"{n} pods of the K={k} production shape ({CPU_PER_ARM * k} CPU, {MEM_GI_PER_ARM * k}Gi, 1 "
                              f"{p['resource_key']}); header + fingerprint gate only; G_obs = pods Running within "
                              f"{PROBE_WINDOW_MIN} min of apply, Q_p = their median wait"),
        'bnjettag.io/gpu-product': f"{p['product']} via {p['resource_key']}",
        'bnjettag.io/gpu-fingerprint': f'{FP_CM} sha256 {FP_SHA[:16]}: {FP_RUN} initial_ebops == {FP_EXPECT}, else exit 9',
        'bnjettag.io/wandb': 'none: no training',
        'bnjettag.io/retries': 'backoffLimitPerIndex 0: a probe pod is never retried; a preempted one is replaced',
        'bnjettag.io/narrow-pool': 'one product on purpose (decisions.md 2026-09-29); ends when the probe Job is deleted',
        'bnjettag.io/node-survey': survey_ref}
    if k == 1:
        annotations['bnjettag.io/single-arm-justified'] = 'probe of the K=1 production pod shape; runs only the fingerprint check'
    res = {'cpu': str(CPU_PER_ARM * k), 'memory': f'{MEM_GI_PER_ARM * k}Gi', 'ephemeral-storage': '24Gi',
           p['resource_key']: '1'}
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': annotations},
            'spec': {'completionMode': 'Indexed', 'completions': n, 'parallelism': n,
                     'backoffLimitPerIndex': 0, 'maxFailedIndexes': n,
                     'podFailurePolicy': {'rules': [{'action': 'Ignore', 'onPodConditions': [{'type': 'DisruptionTarget'}]}]},
                     'activeDeadlineSeconds': PROBE_JOB_DEADLINE_S, 'ttlSecondsAfterFinished': 604800,
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'activeDeadlineSeconds': PROBE_POD_DEADLINE_S,
                         'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {
                             'nodeSelectorTerms': [{'matchExpressions': [
                                 {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': [p['product']]},
                                 {'key': 'kubernetes.io/hostname', 'operator': 'NotIn', 'values': excluded}]}]}}},
                         'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 60,
                         'containers': [{'name': 'probe', 'image': 'python:3.12', 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [probe_script(p, k)],
                                         'env': [{'name': 'NODE_NAME', 'valueFrom': {'fieldRef': {'fieldPath': 'spec.nodeName'}}},
                                                 {'name': 'POD_NAME', 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}}},
                                                 {'name': 'WANDB_MODE', 'value': 'disabled'}],
                                         'resources': {'requests': dict(res), 'limits': dict(res)},
                                         'volumeMounts': [{'mountPath': '/cmcode', 'name': 'code', 'readOnly': True},
                                                          {'mountPath': '/work', 'name': 'work'},
                                                          {'mountPath': '/data', 'name': 'persistent'},
                                                          {'mountPath': '/cmfp', 'name': 'fingerprint', 'readOnly': True}]}],
                         'volumes': [{'name': 'code', 'configMap': {'name': CODE_CM, 'defaultMode': 420}},
                                     {'name': 'work', 'emptyDir': {'sizeLimit': '24Gi'}},
                                     {'name': 'persistent', 'persistentVolumeClaim': {'claimName': 'kai-data'}},
                                     {'name': 'fingerprint', 'configMap': {'name': FP_CM, 'defaultMode': 420}}]}}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--survey', type=Path, default=None)
    ap.add_argument('--k-low-rule', choices=sorted(K_LOW_RULES), default='study-d2')
    ap.add_argument('--probe', metavar='PRODUCT:K:N', help='write only the STUDY [D4] probe Job for PRODUCT at K, N pods')
    ap.add_argument('--out-dir', type=Path, default=None, help='--probe output directory (default ../manifests)')
    args = ap.parse_args()
    survey_path = args.survey or sorted((HERE / 'evidence').glob('node_survey_*.json'))[-1]
    survey = json.loads(survey_path.read_text())
    # frozen inputs, checked, never rewritten
    assert sha(BUNDLE_TAR.read_bytes()) == BUNDLE_SHA, 'bundle tarball is not 42abed4b'
    fp = json.loads(FP_PAYLOAD.read_text())
    assert fp['metadata']['name'] == FP_CM and sha(fp['data']['fingerprint_check.py'].encode()) == FP_SHA
    text = DRIVER.read_text()
    driver_sha = sha(text.encode())
    cm = driver_configmap(text, driver_sha)
    excluded = sorted(set(survey['excluded_hostnames']) | known_bad_nodes())
    survey_ref = f"{survey_path.name} (read {survey['read_utc']})"
    if args.probe:
        product, k, n = args.probe.rsplit(':', 2)
        p = plan_product(product, survey['products'][product], args.k_low_rule)
        out = args.out_dir or OUT
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"kai-gpuprobe-{p['slug']}-k{int(k)}.json"
        path.write_text(json.dumps(probe_job(p, int(k), int(n), excluded, survey_ref), indent=2) + '\n')
        print('PROBE_JOB', path, 'pods', n, 'shape', f'{CPU_PER_ARM * int(k)} CPU {MEM_GI_PER_ARM * int(k)}Gi 1 {p["resource_key"]}')
        return
    OUT.mkdir(exist_ok=True)
    (OUT / f'configmap-bench-driver-{driver_sha[:8]}.json').write_text(json.dumps(cm, indent=2) + '\n')
    plans = []
    for product in PRODUCTS:
        p = plan_product(product, survey['products'][product], args.k_low_rule)
        c = p['classes']
        print(f"{p['product']:25s} {p['resource_key']:20s} card {p['card_mib']:6d} MiB  "
              f"E rule {c['E']['k_rule']:2d} run {c['E']['k_run']:2d} low {c['E']['k_low']:2d}  "
              f"A07 rule {c['A07']['k_rule']:2d} run {c['A07']['k_run']:2d} low {c['A07']['k_low']:2d}  "
              f"schedulable {p['schedulable_nodes']}/{p['nodes']}  role {p['role']}")
        for cls, cc in c.items():
            if cc['binding_caps']:
                print(f"    CAP {cls}: K_rule {cc['k_rule']} -> {cc['k_run']}: {'; '.join(cc['binding_caps'])}")
        for j in p['jobs']:
            path = OUT / f"{j['name']}.json"
            path.write_text(json.dumps(job(p, j, cm['metadata']['name'], driver_sha, excluded, survey_ref), indent=2) + '\n')
            print(f"    {j['shape']:5s} {' '.join(ph['phase'] for ph in j['phases']):22s} "
                  f"pod {j['pod_request']['cpu']:2d} CPU {j['pod_request']['memory_gi']:3d}Gi  "
                  f"can hold {len(j['nodes_that_can_hold_pod']):2d}  deadline pod {j['pod_active_deadline_seconds']} s / "
                  f"Job {j['job_active_deadline_seconds']} s  run-epochs {j['run_epochs']}  "
                  f"compute h agg {j['expected_compute']['a10_aggregate_bound_s'] / 3600:.2f} "
                  f"per-process {j['expected_compute']['a10_per_process_bound_s'] / 3600:.2f}  -> {path.name}")
        plans.append(p)
    (OUT / 'bench_plan.json').write_text(json.dumps({
        'survey': survey_ref, 'k_low_rule': K_LOW_RULES[args.k_low_rule], 'rule_fraction': RULE_FRACTION, 'per_process_mib': PER_PROCESS_MIB,
        'per_process_source': PER_PROCESS_SOURCE, 'cpu_per_arm': CPU_PER_ARM, 'mem_gi_per_arm': MEM_GI_PER_ARM,
        'cpu_pinning': 'each phase: the first 2 x K CPUs of the pod allowed set (STUDY Amendment 1, A2)',
        'cpu_budget_rule': 'steady cgroup cores / K > 2.0 x 1.05 = 2.1: above budget, kept out of T (STUDY rule 5)',
        'node_reserve': {'cpu': NODE_RESERVE_CPU, 'mem_gi': NODE_RESERVE_MEM_GI}, 'stop_after': STOP_AFTER,
        'class_names': CLASS_NAMES, 'excluded_hostnames': excluded, 'driver_configmap': cm['metadata']['name'],
        'driver_sha256': driver_sha, 'jobs': sum(len(p['jobs']) for p in plans), 'products': plans}, indent=1) + '\n')
    print('JOBS', sum(len(p['jobs']) for p in plans), 'PRODUCTS', len(plans))
    print('DRIVER_CONFIGMAP', cm['metadata']['name'], 'sha256', driver_sha)
    print('EXCLUDED', ' '.join(excluded))
    print('EXCLUDED_A10_ONLY', ' '.join(PILOT_NODES), '(the Chang pilot-b nodes; PREFLIGHT critical v2 C5)')
    print('SURVEY', survey_ref)


if __name__ == '__main__':
    main()
