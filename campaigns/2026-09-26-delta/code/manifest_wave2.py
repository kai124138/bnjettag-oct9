#!/usr/bin/env python3
"""Pack the Delta wave-2 runs and emit Indexed-Job manifest templates plus the memory canary. Never submits.

    python3 manifest_wave2.py [--gpu-product NVIDIA-L40S] [--k-result k_result.json]

Template: the anchor's regime-B pilot-b-k3-job.json (bundle 42abed4b), reshaped.
Outputs in manifests/:
  delta_w2_t0_packs.json     + delta-w2-t0-job.json      replicas (rep-A, rep-A07-350, rep-C) and the
                                                         teachers P-T1/P-T2: the t = 0 pods (STUDY launch gate 10)
  delta_w2_cells_packs.json  + delta-w2-cells-job.json   cells and placebos, released at the replica
                                                         epoch-500 gate; floor family first, then the
                                                         long-horizon cells, then placebos and singles
  delta_canary_packs.json    + delta-canary-job.json     ONE pod on the selected product (A10 for
                                                         the historical default): E at K=4, E at K=5, A07 at K=3,
                                                         110 epochs each (the RSS gate window 5-105 completes),
                                                         batch 2,790 (from the configs), nvidia-smi and POD_MEM
                                                         logged; canary_k.py writes k_result.json (GPU peak and
                                                         RSS slope per arm, K per class)
Packs are dict-form (run_pack.py after patch 0038): run names, run_root, per-pack data_root.

Gate 15 (PREFLIGHT, REGRESSION_TICKET 2026-09-28): EVERY Delta pod (t0, cells, canary) runs
campaigns/delta0926/fingerprint_check.py after CACHE_READY and before the first run_pack.py. It builds
rep-A s1 as the runner does on the anchor cache, traces initial_ebops and exits 9 unless it is
11,559,681 (8 if no GPU is visible); it logs the driver, GPU, TF build and `pip freeze` first. The
canary runs under /data/delta-20260927/canary-v2 (the c6017 run dirs hold DIVERGED.json, which is
never resumed) and excludes hcc-nrp-shor-c6017.unl.edu until the discriminator clears it.

Packable row: status ready_on_base / runnable_on_series (classify_series.py), its (entry, arm) gate
GATE_PASS (gate_results.json), floor traced, cache built (the anchor's gated 90/10 cache), no teacher
dependency (those go to after_teacher). A pack never mixes horizon, data_root, architecture class or
phase; replicas never share a pod with cells or placebos.

K per (architecture class, GPU class) (memory_measurements.json; wave-2 STUDY launch gate 7, [DK11]):
from k_result.json when the canary covered that class on a product of the GPU class; else the
CPU-side estimate floor(0.90 * card_MiB / per_process_MiB) from a measured per-process footprint
(E on A10: RUN.md 4,354 of 23,028 MiB); else the STUDY's planning K. Anything short of the canary
makes the manifest a PLANNING manifest (annotation), and the canary runs first. Pod cap 10.

Host memory and the RSS gate (anchor 42abed4b `ablation.rss_gate_from_env`: PASS iff
baseline + slope x train.epochs <= BNJ_RSS_GATE_LIMIT_MB, fitted over process epochs 5-104, exit 5).
Rule, per pack (a pack never mixes horizons): BNJ_RSS_GATE_LIMIT_MB = 2,100 + 5 x H (MiB), the
wave-2 STUDY's PACK-MEM line (Budget: host memory per arm >= baseline 2.1 GB + slope x H at the
gate-14 limit of 5 MB/epoch; `budget.py` PACK-MEM), i.e. 4,600 / 7,100 / 9,600 / 12,100 at H 500 /
1,000 / 1,500 / 2,000. With the measured start-of-run RSS of 2,106-2,160 MB (anchor PREFLIGHT) the
gate then fails an arm whose slope exceeds about 4.9 MB/epoch at any horizon, which is gate 14's
bound; a single 6,144 limit would admit 8 MB/epoch at H 500 and fail 2 MB/epoch at H 2,000.
Pod memory per arm = max(6 Gi, ceil(limit / 1,024) Gi) = 6 / 7 / 10 / 12 Gi, so the cgroup holds
whatever the gate admits; a Job's pods are sized for its largest pack (K x per-arm Gi).
The header exports the pod's own pack limit from pack_meta; run_pack passes it to every child.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
TEMPLATE = LAB / 'campaigns/2026-09-26-training-batch/manifests/pilot-b-k3-job.json'
MEASURE = HERE / 'memory_measurements.json'
CPU_PER_ARM, MEM_GI_FLOOR = 2, 6
RSS_BASE_MIB, RSS_SLOPE_MIB = 2100, 5     # wave-2 STUDY Budget PACK-MEM; gate 14 (5 MB/epoch)
RSS_WINDOW = '5:105'
CANARY_EPOCHS = 110                       # > 105: the RSS gate window completes in every canary arm
S_RUN_EPOCH = 22.75                       # STUDY Budget: 136.5 / 6 pod-seconds per run-epoch, a projection
A07_R = (1, 2)                            # STUDY Budget: A07 = r x 22.75, r in {1, 2}, illustrations
CANARY_DIR = 'canary-v2'                  # v1 (c6017, all rep-A arms NaN at epoch 0) stays under canary/
FINGERPRINT_CACHE = '/data/chang-n64-20260926'   # gate 15 reference cache (the anchor's), never a pack data_root
CANARY_EXCLUDE = ('hcc-nrp-shor-c6017.unl.edu',)  # REGRESSION_TICKET 2026-09-28; until the discriminator reads


def gate15_lines(run=None):
    """PREFLIGHT gate 15: the GPU integer fingerprint before any arm (exit 9 mismatch, 8 no GPU)."""
    extra = f' --run {run}' if run else ''
    return [
        f'test -f {FINGERPRINT_CACHE}/n64/data/READY.json || {{ echo "GATE15_CACHE_NOT_READY {FINGERPRINT_CACHE}"; exit 9; }}',
        f'python -u {CAMPAIGN_DIR}/fingerprint_check.py --env-report --data-root {FINGERPRINT_CACHE}{extra} '
        '|| { rc=$?; echo "GATE15_FAIL exit $rc"; exit $rc; }',
        'echo GATE15_PASS',
    ]


def rss_limit_mib(h):
    return RSS_BASE_MIB + RSS_SLOPE_MIB * int(h)


def arm_gi(h):
    return max(MEM_GI_FLOOR, math.ceil(rss_limit_mib(h) / 1024))
POD_CAP = 10          # Delta pods (Kai; wave-2 STUDY launch gate 12, [DK11])
N_DEFAULT = 4         # n_350 = n_5M = 4, the wave-2 STUDY budget default (l. 244-246); replica seeds above n stop at the gate
RUN_ROOT = '/data/delta-20260927'
CAMPAIGN_DIR = '/work/code/campaigns/delta0926'
ARCH_KEYS = ('n_part', 'n_feat', 'd_model', 'n_heads', 'n_layers', 'ffn_dim', 'pos_enc', 'attn_kind', 'linformer_k',
             'body', 'deepsets_dims', 'head_dims', 'pre_block_act')
QUANT_KEYS = ('weight', 'act_granularity')
PACKABLE = ('ready_on_base', 'runnable_on_series')


def arch_sig(cfg):
    return json.dumps({'arch': {k: cfg['arch'].get(k) for k in ARCH_KEYS},
                       'quant': {k: cfg['quant'].get(k) for k in QUANT_KEYS}}, sort_keys=True)


def header(stage, packs_file, tags, *, canary=False):
    lines = [
        'set -euo pipefail',
        'export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2',
        'export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1',
        'mkdir -p /work/code',
        "echo '__BUNDLE_SHA256__  /cmcode/hgq2.tar.gz' | sha256sum -c -",
        'tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1',
        'export PYTHONPATH=/work/code',
        '# roots come from the dict-form packs file (run_pack.py, Delta patch 0038); never from the environment',
        'unset BNJ_DATA_ROOT BNJ_RUN_ROOT',
        f'export BNJ_CAMPAIGN_DIR={CAMPAIGN_DIR} BNJ_STAGE={stage} BNJ_RSS_GATE_WINDOW={RSS_WINDOW}',
        'export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0',
        'unset WANDB_PROJECT   # every config says train.wandb_project BNJetTag-Delta; run_engram checks env == config',
        f'export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_MODE={"disabled" if canary else "online"} WANDB_TAGS={tags}',
        'export WANDB_DIR=/work WANDB_CACHE_DIR=/work/wandb-cache WANDB_DATA_DIR=/work/wandb-data WANDB_DISABLE_CODE=true WANDB_QUIET=true',
        'pip install -q --no-cache-dir -r /work/code/requirements-training.txt',
        'NVLIBS=$(python -c "import glob; print(\':\'.join(sorted(glob.glob(\'/usr/local/lib/python*/site-packages/nvidia/*/lib\'))))")',
        'export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        'cd /work/code',
        'MSHA=$(python -c "import run_study; print(run_study.manifest()[\'sha256\'])")',
        'test "$MSHA" = "__MANIFEST_SHA256__" || { echo "MANIFEST_SHA_MISMATCH $MSHA"; exit 1; }',
        'echo "MANIFEST_SHA_OK $MSHA"',
        'export BNHGQ2_CODE_SHA256="$MSHA"',
        'python -c "import tensorflow as tf; assert tf.config.list_physical_devices(\'GPU\'); print(\'GPU_GATE_PASS\')"',
        'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true',
        'df -h /data',
    ]
    ready = ('python - <<\'PY\'\nimport json, os, pathlib, sys\n'
             f'p = json.load(open(os.path.join(os.environ["BNJ_CAMPAIGN_DIR"], "{packs_file}")))\n'
             'idx = range(len(p["packs"])) if "{canary}" == "1" else [int(os.environ["JOB_COMPLETION_INDEX"])]\n'
             'bad = [(m["data_root"], n) for i in idx for m in [p["pack_meta"][i]] for n in m["n_parts"]\n'
             '       if not pathlib.Path(m["data_root"], f"n{n}", "data", "READY.json").is_file()]\n'
             'print("CACHE_NOT_READY" if bad else "CACHE_READY", bad or ""); sys.exit(1 if bad else 0)\nPY')
    lines.append(ready.replace('{canary}', '1' if canary else '0'))
    lines += gate15_lines()
    if not canary:   # the RSS gate limit of THIS pod's pack (packs never mix horizons)
        lines.append('export BNJ_RSS_GATE_LIMIT_MB=$(python -c "import json, os; '
                     f'p = json.load(open(os.path.join(os.environ[\'BNJ_CAMPAIGN_DIR\'], \'{packs_file}\'))); '
                     'print(p[\'pack_meta\'][int(os.environ[\'JOB_COMPLETION_INDEX\'])][\'rss_gate_limit_mb\'])")')
        lines.append('echo "RSS_GATE_LIMIT_MB $BNJ_RSS_GATE_LIMIT_MB window $BNJ_RSS_GATE_WINDOW"')
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', type=Path, default=HERE / 'configs' / 'index.json')
    ap.add_argument('--out', type=Path, default=HERE / 'manifests')
    ap.add_argument('--gate', type=Path, default=HERE / 'gate_results.json')
    ap.add_argument('--gpu-class', default='24GB', help='memory_measurements.json gpu_classes key')
    ap.add_argument('--gpu-product', help='one exact product for a new GPU-policy benchmark; use a separate --out directory')
    ap.add_argument('--k-result', type=Path, default=HERE / 'k_result.json',
                    help='canary output (canary_k.py); absent = PLANNING manifest')
    args = ap.parse_args(argv)
    index = json.loads(args.index.read_text())
    if not index.get('series_classification'):
        raise SystemExit('index.json is not classified; run classify_series.py on the applied tree first')
    if index.get('stand_in_base'):
        raise SystemExit('stand-in index: never packed')
    gate = {(r['id'], r['base_arm']): r for r in json.loads(args.gate.read_text())['results']}
    meas = json.loads(MEASURE.read_text())
    if args.gpu_product:
        matches = [name for name, row in meas['gpu_classes'].items()
                   if args.gpu_product in row['products']]
        if len(matches) != 1:
            raise SystemExit(f'gpu product {args.gpu_product!r} must appear in exactly one gpu_classes entry')
        args.gpu_class = matches[0]
        products = [args.gpu_product]
    else:
        products = meas['gpu_classes'][args.gpu_class]['products']
    kres = json.loads(args.k_result.read_text()) if args.k_result.exists() else None
    slug = re.sub(r'[^a-z0-9]+', '-', args.gpu_product.lower()).strip('-') if args.gpu_product else ''
    canary_dir = f'canary-gpu-{slug}' if slug else CANARY_DIR
    # A new product needs a separate K/throughput/utilization certification beyond the baseline
    # E-k4/E-k5/A07-k3 canary. A planning manifest must not be treated as production-ready.
    product_certified = bool(args.gpu_product and kres and kres.get('gpu_policy_certified')
                             and kres.get('gpu_product') == args.gpu_product)
    template = json.loads(TEMPLATE.read_text())
    root = args.index.parent
    cfg_of = {r['name']: json.loads((root / r['file']).read_text()) for r in index['runs'] if r.get('file')}

    # architecture classes: E = arm A's, A07 = arm C's (arch + weight scheme), else X-<hash>
    by_arm = {}
    for r in index['runs']:
        if r.get('kind') == 'drift_replica' and r['base_arm'] in ('A', 'C') and r.get('file'):
            by_arm.setdefault(r['base_arm'], arch_sig(cfg_of[r['name']]))
    known = {by_arm['A']: 'E', by_arm['C']: 'A07'}

    def arch_class(r):
        s = arch_sig(cfg_of[r['name']])
        if s in known:
            return known[s], None
        base_class = 'E' if r['base_arm'] in ('A', 'B', 'D', 'F', 'R') else 'A07'
        return 'X-' + hashlib.sha256(s.encode()).hexdigest()[:6], base_class

    def k_for(cls, base_class):
        """(K, source, planning?) for this class on the GPU class."""
        c = cls if base_class is None else base_class
        if kres:
            ok = [(ph['k_accepted'], name) for name, ph in kres['phases'].items()
                  if ph['class'] == c and ph.get('k_accepted')
                  and set(p.replace(' ', '-') for p in ph.get('gpu_product') or []) & set(products)]
            if ok:
                k, name = max(ok)
                return k, f'canary k_result.json (phase {name})', base_class is not None
        est = [m for m in meas['measurements'] if m['class'] == c and m['gpu_product'] in products]
        if est:
            m = est[0]
            k = math.floor(meas['rule_fraction'] * m['card_mib'] / m['per_process_mib'])
            return k, (f'estimate floor({meas["rule_fraction"]} x {m["card_mib"]} / {m["per_process_mib"]}) '
                       f'on {m["gpu_product"]} ({m["source"].split(",")[0]})'), True
        plan = meas['planning_k'].get(c, {}).get(args.gpu_class)
        if plan is None:
            raise SystemExit(f'no K for class {c} on {args.gpu_class}: run the canary')
        return plan, f'planning ({meas["planning_k"][c]["source"]})', True

    rows = [r for r in index['runs'] if r['wave'] in ('W2', 'prereq')]
    unpacked, after_teacher, packable = [], {}, []
    for r in rows:
        g = gate.get((r['id'], r['base_arm']))
        why = (None if r.get('file') and r['status'] in PACKABLE else f"status {r['status']}"
               + (f" [{(r.get('series_refusal') or {}).get('key')}]" if r.get('series_refusal') else ''))
        if why is None and r.get('depends_on'):
            after_teacher.setdefault(r['depends_on'], []).append(r['name'])
            continue
        if why is None and (g is None or g['outcome'] != 'GATE_PASS'):
            why = f"gate {g['outcome'] if g else 'not gated'}"
        if why is None and 'floor_untraced' in r['flags']:
            why = 'floor_untraced'
        if why is None and 'cache_not_built' in r['flags']:
            why = f"cache_not_built ({r['data_root']})"
        if why:
            unpacked.append({'name': r.get('name'), 'run_id': r['run_id'], 'id': r['id'], 'why': why})
            continue
        packable.append(r)

    def phase_of(r):
        return 't0' if r['kind'] in ('drift_replica', 'prerequisite_teacher') else 'cells'

    def order_key(r):
        floor_family = r['base_arm'] == 'A07-350'
        long_h = r['horizon'] > 500
        placebo = r['kind'] == 'placebo'
        return (0 if r['kind'] == 'drift_replica' else 1 if r['kind'] == 'prerequisite_teacher'
                else 2 if floor_family else 3 if long_h else 4 if placebo else 5)

    outputs, k_table, planning = {}, {}, bool(args.gpu_product and not product_certified)
    for phase in ('t0', 'cells'):
        prow = sorted((r for r in packable if phase_of(r) == phase), key=lambda r: (order_key(r), index['runs'].index(r)))
        groups = {}
        for r in prow:
            cls, base_class = arch_class(r)
            key = (order_key(r), r['kind'] == 'drift_replica', r['horizon'], r['data_root'], cls,
                   r['id'] if r['kind'] in ('drift_replica', 'prerequisite_teacher') else None)   # one family per t0 pack
            groups.setdefault(key, {'rows': [], 'cls': cls, 'base_class': base_class})['rows'].append(r)
        packs, meta = [], []
        for key, grp in groups.items():
            k, source, plan = k_for(grp['cls'], grp['base_class'])
            planning |= plan or kres is None
            k_table[grp['cls']] = {'k': k, 'source': source, 'base_class': grp['base_class']}
            rs = grp['rows']
            for i in range(0, len(rs), k):
                chunk = rs[i:i + k]
                packs.append([r['name'] for r in chunk])
                flags = sorted({f for r in chunk for f in r['flags'] if f in ('study_frozen_list', 'placebo',
                                                                             'teacher_definition_provisional')})
                meta.append({'data_root': chunk[0]['data_root'], 'n_parts': sorted({r['n_part'] for r in chunk}),
                             'horizon': key[2], 'arch_class': grp['cls'], 'k': k, 'k_source': source,
                             'rss_gate_limit_mb': rss_limit_mib(key[2]), 'mem_gi_per_arm': arm_gi(key[2]),
                             'arms': len(chunk), 'kinds': sorted({r['kind'] for r in chunk}),
                             'entries': sorted({r['id'] for r in chunk}), 'flags': flags,
                             **({'k_class_unmeasured': f"planning K of base class {grp['base_class']}"}
                                if grp['base_class'] else {})})
        outputs[phase] = (packs, meta)

    # placebo never in its replica's pod: replicas are in t0, placebos in cells (asserted)
    t0_names = {n for p in outputs['t0'][0] for n in p}
    assert not any(n in t0_names for p in outputs['cells'][0] for n in p)
    names = [n for ph in outputs.values() for p in ph[0] for n in p]
    assert len(names) == len(set(names)), 'a run is packed twice'

    # t0 pods still alive when the cells are released (epoch-500 gate): a replica pack with H > 500
    # holding a seed <= n keeps running, so the cells Job gets the rest of the 10-pod cap
    seed_of = {r['name']: r['seed'] for r in index['runs'] if r.get('name')}
    live_t0 = sum(1 for p, m in zip(*outputs['t0']) if m['horizon'] > 500 and any(seed_of[n] <= N_DEFAULT for n in p))
    args.out.mkdir(parents=True, exist_ok=True)
    for stale in ('atlas_w2_packs.json', 'wave2-screen-job.json'):
        (args.out / stale).unlink(missing_ok=True)
    common = {'format': 'run_pack.py dict form (Delta patch 0038)', 'index_sha256': hashlib.sha256(args.index.read_bytes()).hexdigest(),
              'gpu_class': args.gpu_class, 'gpu_products': products, 'planning': planning,
              'k_table': k_table, 'pod_cap': POD_CAP}
    for phase, (packs, meta) in outputs.items():
        f = f'delta_w2_{phase}_packs.json'
        body = {**common, 'phase': phase, 'run_root': f'{RUN_ROOT}/w2', 'data_root': index['anchor_cache']['data_root'],
                'packs': packs, 'pack_meta': meta}
        if phase == 'cells':
            body.update(unpacked=unpacked, after_teacher=after_teacher,
                        release='at the replica epoch-500 gate (wave-2 STUDY launch gate 10), not at t = 0')
        (args.out / f).write_text(json.dumps(body, indent=1) + '\n')
        cap = POD_CAP if phase == 't0' else POD_CAP - live_t0
        (args.out / f'delta-w2-{phase}-job.json').write_text(json.dumps(
            job(template, f'kai-delta0926-w2-{phase}' + (f'-{slug}' if slug else ''), f, packs, meta, products, planning, stage='production',
                tags=f'delta0926,wave2,{phase},validation-only', cap=cap, live_t0=live_t0 if phase == 'cells' else 0),
            indent=2) + '\n')

    # memory canary (wave-2 STUDY gates 7 and 14): one pod on an A10, three sequential phases
    reps = {arm: sorted((x for x in index['runs'] if x.get('kind') == 'drift_replica' and x['base_arm'] == arm and x['wave'] == 'W2'
                         and x.get('file')), key=lambda r: r['seed']) for arm in ('A', 'C')}
    plac = sorted((x for x in index['runs'] if x['id'] == 'P-350' and x.get('file')), key=lambda r: r['seed'])
    # every phase holds one horizon (its RSS limit); names are disjoint across phases (one W&B id each):
    # E-k4 rep-A s1-4 (H 1,000); E-k5 P-350 s1-4 + rep-A s5 (both arm A's config, H 500); A07-k3 rep-C s1-3 (H 2,000)
    phases = [('E-k4', 'E', 4, reps['A'][:4], 'canary'),
              ('E-k5', 'E', 5, plac[:4] + [r for r in reps['A'] if r['seed'] == 5], 'canary'),
              ('A07-k3', 'A07', 3, reps['C'][:3], 'canary')]
    can_packs, can_meta = [], []
    for ph, cls, k, rs, stage in phases:
        h = rs[0]['horizon']
        assert all(r['horizon'] == h for r in rs)
        can_packs.append([r['name'] for r in rs])
        can_meta.append({'phase': ph, 'class': cls, 'k_tested': k, 'stage': stage, 'run_root': f'{RUN_ROOT}/{canary_dir}/{ph}',
                         'data_root': index['anchor_cache']['data_root'], 'n_parts': [64], 'arms': len(rs),
                         'config_horizon': h, 'rss_gate_limit_mb': rss_limit_mib(h), 'mem_gi_per_arm': arm_gi(h),
                         'epochs': CANARY_EPOCHS,
                         'gpu_hours_projection': ([round(CANARY_EPOCHS * k * S_RUN_EPOCH * r / 3600, 2) for r in A07_R]
                                                  if cls == 'A07' else round(CANARY_EPOCHS * k * S_RUN_EPOCH / 3600, 2))})
    gh = [sum(m['gpu_hours_projection'] if m['class'] == 'E' else m['gpu_hours_projection'][i] for m in can_meta)
          for i in range(len(A07_R))]
    (args.out / 'delta_canary_packs.json').write_text(json.dumps(
        {**common, 'phase': 'canary', 'run_root': f'{RUN_ROOT}/{canary_dir}', 'data_root': index['anchor_cache']['data_root'],
         'packs': can_packs, 'pack_meta': can_meta, 'stop_after_epochs': CANARY_EPOCHS,
         'gpu_hours_projection_total': {'r=1': round(gh[0], 2), 'r=2': round(gh[1], 2),
                                        'basis': 'epochs x K x 22.75 pod-s per run-epoch (STUDY Budget, a projection; '
                                                 'A07 x r, r in {1, 2}); excludes pip install, calibration and the epoch-0 trace'},
         'note': 'drift-replica configs at their own train.epochs (the RSS gate projects to it); own run_root per phase; '
                 'never resumed by production (production run_root /data/delta-20260927/w2)'}, indent=1) + '\n')
    (args.out / 'delta-canary-job.json').write_text(json.dumps(
        canary_job(template, can_meta, product=args.gpu_product or 'NVIDIA-A10',
                   canary_dir=canary_dir, name='kai-delta0926-canary' + (f'-{slug}' if slug else '')),
        indent=2) + '\n')

    print(f'gpu_class={args.gpu_class} products={products} planning={planning} k_result={"yes" if kres else "no"}')
    for cls, v in sorted(k_table.items()):
        print(f'  K[{cls}] = {v["k"]}  ({v["source"]})' + (f'  base class {v["base_class"]}' if v['base_class'] else ''))
    for phase, (packs, meta) in outputs.items():
        by = {}
        for m in meta:
            by.setdefault((m['horizon'], m['arch_class']), []).append(m['arms'])
        cap = POD_CAP if phase == 't0' else POD_CAP - live_t0
        print(f'{phase}: packs={len(packs)} arms={sum(m["arms"] for m in meta)}  parallelism={min(len(packs), cap)}'
              + (f' (cap {POD_CAP} minus {live_t0} t0 pods still running past the epoch-500 gate)' if phase == 'cells' else ''))
        for (h, c), arms in sorted(by.items(), key=lambda kv: str(kv[0])):
            print(f'    H={h} class={c}: {len(arms)} pods {arms}')
    print(f'after_teacher: ' + ', '.join(f'{k}: {len(v)} runs' for k, v in after_teacher.items()))
    ex = {}
    for u in unpacked:
        ex.setdefault(u['why'], set()).add(u['id'])
    for why, ids in sorted(ex.items()):
        print(f'  unpacked [{why}]: {len(ids)} entries {",".join(sorted(ids))}')
    print(f'canary: 1 pod on {args.gpu_product or "NVIDIA-A10 (historical default)"}, ' + ', '.join(f"{m['phase']} ({m['arms']} arms, RSS limit {m['rss_gate_limit_mb']} MiB)" for m in can_meta)
          + f', {CANARY_EPOCHS} epochs each; projected GPU-hours {gh[0]:.1f} (A07 r=1) to {gh[1]:.1f} (r=2)')


def base_job(template, name, k, products, annotations, mem_gi=None):
    job = copy.deepcopy(template)
    labels = {'user': 'kai', 'campaign': 'delta-20260927', 'app': name, 'bnjettag.io/arms-per-pod': str(k)}
    job['metadata'] = {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': annotations}
    spec = job['spec']
    spec['template']['metadata'] = {'labels': copy.deepcopy(labels)}
    pod = spec['template']['spec']
    terms = pod['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]
    for expr in terms['matchExpressions']:
        if expr['key'] == 'nvidia.com/gpu.product':
            expr['values'] = list(products)
    pod['affinity']['nodeAffinity'].pop('preferredDuringSchedulingIgnoredDuringExecution', None)
    for vol in pod['volumes']:
        if vol.get('configMap'):
            vol['configMap']['name'] = '__CONFIGMAP_NAME__'
    c = pod['containers'][0]
    resource_by_product = {
        'NVIDIA-A100-SXM4-80GB': 'nvidia.com/a100',
        'NVIDIA-A100-80GB-PCIe': 'nvidia.com/a100',
        'NVIDIA-A100-PCIE-40GB': 'nvidia.com/a100',
        'NVIDIA-RTX-A6000': 'nvidia.com/rtxa6000',
        'NVIDIA-A40': 'nvidia.com/a40',
    }
    keys = {resource_by_product.get(product, 'nvidia.com/gpu') for product in products}
    if len(keys) != 1:
        raise ValueError(f'GPU products require different Kubernetes resources: {products}')
    gpu_key = keys.pop()
    # gate 15 logs the node (downward API); the value is a hostname, not a secret
    c['env'] = [e for e in c.get('env', []) if e['name'] != 'NODE_NAME'] + [
        {'name': 'NODE_NAME', 'valueFrom': {'fieldRef': {'fieldPath': 'spec.nodeName'}}}]
    for kind in ('requests', 'limits'):
        for key in tuple(c['resources'][kind]):
            if key.startswith('nvidia.com/'):
                del c['resources'][kind][key]
        c['resources'][kind][gpu_key] = '1'
        c['resources'][kind].update(cpu=str(CPU_PER_ARM * k), memory=f'{mem_gi or MEM_GI_FLOOR * k}Gi')
    return job


def job(template, name, packs_file, packs, meta, products, planning, *, stage, tags, cap=POD_CAP, live_t0=0):
    kmax = max((m['k'] for m in meta), default=1)
    ann = {'bnjettag.io/placeholders': '__CONFIGMAP_NAME__ (kai-delta0926-code-<sha10>), __BUNDLE_SHA256__, '
                                       '__MANIFEST_SHA256__ (cluster-ops, from the Delta freeze)',
           'bnjettag.io/packs': f'{CAMPAIGN_DIR}/{packs_file}',
           'bnjettag.io/status': ('PLANNING: K not from the memory canary; run delta-canary-job.json first, '
                                  'copy k_result.json to code/, regenerate' if planning else 'K from the memory canary')
                                 + '; TEMPLATE, not for kubectl apply before the wave-2 STUDY PASS and PREFLIGHT',
           'bnjettag.io/active-deadline': 'unset on purpose (resumable arms; anchor STUDY Resume)'}
    mem = max((m['k'] * m['mem_gi_per_arm'] for m in meta), default=MEM_GI_FLOOR)
    ann['bnjettag.io/per-arm-memory'] = ('per pack: max(6 Gi, ceil((2,100 + 5 x H) / 1,024)) Gi = 6 / 7 / 10 / 12 Gi at '
                                         'H 500 / 1,000 / 1,500 / 2,000; pods sized for the largest pack of this Job '
                                         f'({mem}Gi); STUDY Budget PACK-MEM')
    ann['bnjettag.io/rss-gate'] = ('BNJ_RSS_GATE_LIMIT_MB = 2,100 + 5 x H MiB of the pod\'s pack (pack_meta), window 5:105; '
                                   'PASS iff baseline + slope x train.epochs <= limit, else exit 5 (not retried)')
    j = base_job(template, name, kmax, products, ann, mem_gi=mem)
    spec = j['spec']
    spec.update(completions=len(packs), parallelism=min(len(packs), cap))
    if live_t0:
        j['metadata']['annotations']['bnjettag.io/parallelism'] = (
            f'{cap} = the 10-pod Delta cap minus {live_t0} t0 replica pods that run past the epoch-500 gate '
            f'(n = {N_DEFAULT}); recompute if the seed rule changes n or the t0 pods have finished')
    lines = header(stage, packs_file, tags)
    lines.append(f'python -u /work/code/run_pack.py {packs_file}')
    spec['template']['spec']['containers'][0]['args'] = ['\n'.join(lines) + '\n']
    return j


def canary_job(template, can_meta, product='NVIDIA-A10', canary_dir=CANARY_DIR, name='kai-delta0926-canary'):
    kmax = max(m['k_tested'] for m in can_meta)
    mem = max(m['k_tested'] * m['mem_gi_per_arm'] for m in can_meta)
    ann = {'bnjettag.io/placeholders': '__CONFIGMAP_NAME__, __BUNDLE_SHA256__, __MANIFEST_SHA256__ (cluster-ops)',
           'bnjettag.io/packs': f'{CAMPAIGN_DIR}/delta_canary_packs.json',
           'bnjettag.io/status': (f'memory canary (wave-2 STUDY launch gates 7 and 14): one pod on {product}; phases '
                                  + ', '.join(f"{m['phase']} ({m['arms']} arms)" for m in can_meta)
                                  + f', {CANARY_EPOCHS} epochs each, sequential; output {RUN_ROOT}/{canary_dir}/k_result.json; '
                                  'TEMPLATE until PREFLIGHT'),
           'bnjettag.io/rss-gate': 'per phase BNJ_RSS_GATE_LIMIT_MB = 2,100 + 5 x H of the replica configs, window 5:105',
           'bnjettag.io/per-arm-memory': f'{mem}Gi = the largest phase (K x per-arm Gi)'}
    ann['bnjettag.io/gate15'] = ('fingerprint_check.py (rep-A s1 initial_ebops == 11,559,681) before any ARM_STARTED; '
                                 'exit 9 mismatch, 8 no GPU; excludes ' + ', '.join(CANARY_EXCLUDE) + ' (REGRESSION_TICKET 2026-09-28)')
    j = base_job(template, name, kmax, [product], ann, mem_gi=mem)
    for term in j['spec']['template']['spec']['affinity']['nodeAffinity'][
            'requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms']:
        for expr in term['matchExpressions']:
            if expr['key'] == 'kubernetes.io/hostname' and expr['operator'] == 'NotIn':
                expr['values'] = sorted(set(expr['values']) | set(CANARY_EXCLUDE))
    spec = j['spec']
    spec.update(completions=1, parallelism=1, activeDeadlineSeconds=16 * 3600)
    spec['backoffLimitPerIndex'] = 1   # pod blips only; arm OOMs are not retried (BNJ_ARM_RETRIES=0)
    can = f'{RUN_ROOT}/{canary_dir}'
    lines = header('canary', 'delta_canary_packs.json', 'delta0926,wave2,memory-canary,validation-only', canary=True)
    lines += [
        f'CAN={can}; mkdir -p $CAN; echo start > $CAN/phase',
        'FAIL=0',
        'export BNJ_ARM_RETRIES=0 BNJ_POD_STALL_RETRIES=0   # an OOM or a stall is the measurement: never retried',
        '( set +e; while true; do P=$(cat $CAN/phase); T=$(date +%s);'
        ' nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits | sed "s/^/$T,$P,gpu,/" >> $CAN/gpu_samples.csv;'
        ' nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits | sed "s/^/$T,$P,app,/" >> $CAN/gpu_samples.csv;'
        ' sleep 10; done ) & SAMPLER=$!',
    ]
    for i, m in enumerate(can_meta):
        ph = m['phase']
        lines.append(f'echo {ph} > $CAN/phase; mkdir -p $CAN/{ph}; '
                     f'BNJ_STAGE={m["stage"]} BNJ_RSS_GATE_LIMIT_MB={m["rss_gate_limit_mb"]} JOB_COMPLETION_INDEX={i} '
                     f'python -u /work/code/run_pack.py delta_canary_packs.json {CANARY_EPOCHS} 2>&1 | tee $CAN/{ph}/pack.log '
                     f'|| {{ echo PHASE_EXIT_NONZERO {ph}; FAIL=1; }}   # pack.log keeps ARM_STARTED pids and POD_MEM lines')
    lines += [
        'echo done > $CAN/phase; sleep 20; kill $SAMPLER || true',
        f'python -u {CAMPAIGN_DIR}/canary_k.py --samples $CAN/gpu_samples.csv --packs {CAMPAIGN_DIR}/delta_canary_packs.json '
        '--run-root $CAN --out $CAN/k_result.json || echo CANARY_K_INCOMPLETE',
        'cat $CAN/k_result.json',
        'test "$FAIL" = 0 || { echo CANARY_PHASES_FAILED; exit 7; }',
    ]
    spec['template']['spec']['containers'][0]['args'] = ['\n'.join(lines) + '\n']
    return j


if __name__ == '__main__':
    main()
