#!/usr/bin/env python3
"""VERIFY recomputation for 2026-09-29-gpu-benchmark (results-analyst, phase 4). Telemetry for a scheduling decision,
never a physics result. This is the only script that writes numbers into VERIFY.md and verify.json.

    cd campaigns/2026-09-29-gpu-benchmark && uv run --no-project python code/verify_bench.py

1. data/bench-root/<slug>-<shape>/ from symlinks: the read-only PVC copy (data/gpu-bench/) plus, from
   logs/kai-gpubench-<slug>-<shape>/, job.json, pod.json and the kubectl pod log as pod-<pod>.log (the PVC tee lacks the
   log's first two lines, BENCH_POD and HOSTNAME_NODE). The 7 deleted Jobs have no PVC data; they enter through --plan.
2. The pre-registered analysis, code/bench_summary.py summarize_bench(root, manifests/bench_plan.json), unchanged, and a
   check that it equals the CLI output data/bench_summary.json.
3. Reproduction: an independent parse of every arm log, pod log, samples.csv, job.json and pod.json, against (2) and
   against the telemetry RUN.md quotes.
4. Q per Job; the 7 deleted Jobs get a lower bound (apply -> deletion, RUN.md).
5. T(p) per STUDY l. 53-58 on a G grid, K per [D3], tie set per [D5], [A1], [A2], the a100 quota bound; checks.
6. verify.json (one row per number printed in VERIFY.md), data/verify_tables.md, data/verify_bench.log (stdout).
"""
from __future__ import annotations

import csv
import hashlib
import heapq
import itertools
import json
import math
import os
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
CAMP = Path(__file__).resolve().parents[1]
REPO = CAMP.parents[1]
CODE, DATA, LOGS = CAMP / 'code', CAMP / 'data', CAMP / 'logs'
PVC, ROOT, PLAN = DATA / 'gpu-bench', DATA / 'bench-root', CAMP / 'manifests' / 'bench_plan.json'
sys.path.insert(0, str(CODE))
import bench_summary as bs  # noqa: E402  (the pre-registered analysis; imported, never copied or edited)

STOP = 21
A10, A100 = 'NVIDIA-A10', 'NVIDIA-A100-SXM4-80GB'
SHORT = {'NVIDIA-A10': 'A10', 'NVIDIA-A100-SXM4-80GB': 'A100-SXM4-80GB', 'NVIDIA-GeForce-RTX-3090': 'RTX 3090',
         'NVIDIA-GeForce-RTX-4090': 'RTX 4090', 'NVIDIA-RTX-A6000': 'RTX A6000', 'NVIDIA-L40': 'L40',
         'NVIDIA-L40S': 'L40S', 'NVIDIA-A40': 'A40'}
ORDER = ['NVIDIA-A10', 'NVIDIA-A100-SXM4-80GB', 'NVIDIA-GeForce-RTX-3090', 'NVIDIA-GeForce-RTX-4090',
         'NVIDIA-RTX-A6000', 'NVIDIA-L40', 'NVIDIA-L40S', 'NVIDIA-A40']
# STUDY.md l. 20-23 (the Question): run-epochs W, longest horizon H, runs. Chang R (8,000 at batch 256) is not timed [A2].
CAMPAIGNS = {
    'chang': {'label': 'Chang wave 1', 'src': 'STUDY.md l. 20-21',
              'classes': {'E': dict(W=224000, H=7000, runs=32), 'A07': dict(W=112000, H=7000, runs=16)}},
    'delta': {'label': 'Delta wave 2', 'src': 'STUDY.md l. 22-23',
              'classes': {'E': dict(W=32000, H=1000, runs=56), 'A07': dict(W=114000, H=2000, runs=192)}},
}
CANARY_EPOCHS = 110            # STUDY l. 55-56: C_p = 110 x s plus its queue, 0 for the A10
TIE = 1.10                     # STUDY [D5] l. 87
DELTA_CAP = 10                 # STUDY [D4] l. 60-61: Delta 10 pods
GRID = {'chang': [1, 4, 8, 13, 16], 'delta': [1, 4, 8, 10]}
SCAN = {'chang': range(1, 33), 'delta': range(1, DELTA_CAP + 1)}
# [D4] quota term for the a100 key: 23/24 used at 08:41Z (PREFLIGHT l. 222), 21/24 at 11:57Z (RUN.md l. 81), and the
# snapshot this script reads (data/resourcequota_snapshot.json, taken 2026-09-29T18:28:07Z) -> headroom = hard - used
# RUN.md l. 89-91 and l. 114-117: the orchestrator's deletion record of the 7 "not practical now" Jobs
DELETED = {'kai-gpubench-l40s-klow': ('2026-09-29T15:37:45Z', 'RUN.md l. 89'),
           'kai-gpubench-l40-klow': ('2026-09-29T15:37:45Z', 'RUN.md l. 90'),
           'kai-gpubench-a40-klow': ('2026-09-29T15:37:45Z', 'RUN.md l. 91'),
           'kai-gpubench-l40s-krule': ('2026-09-29T17:18:54Z', 'RUN.md l. 114'),
           'kai-gpubench-rtx-a6000-krule': ('2026-09-29T17:18:54Z', 'RUN.md l. 115'),
           'kai-gpubench-l40-krule': ('2026-09-29T17:18:54Z', 'RUN.md l. 116'),
           'kai-gpubench-a40-krule': ('2026-09-29T17:18:54Z', 'RUN.md l. 117')}
# RUN.md l. 71-73: PHASE_DONE wall seconds and steady cores per arm as quoted
RUN_PHASE_CLAIMS = [('a10-klow', 'p3-E-k3', 1880.3, 0.575, 'RUN.md l. 71'), ('a10-klow', 'p4-A07-k1', 1180.1, 0.588, 'RUN.md l. 71'),
                    ('a10-krule', 'p1-E-k4', 2530.5, 0.556, 'RUN.md l. 72'), ('a10-krule', 'p2-A07-k2', 2235.3, 0.543, 'RUN.md l. 72'),
                    ('a100-sxm4-80gb-krule', 'p1-E-k16', 3902.7, 0.520, 'RUN.md l. 73'),
                    ('a100-sxm4-80gb-krule', 'p2-A07-k8', 3181.5, 0.544, 'RUN.md l. 73')]

SPLIT = 'telemetry; no data split (timing only, no tagging metric)'
SEEDS = 'seeds 1-8 per class (E: A s1-s8 then B s1-s8; A07: C s1-s8), first K per phase; timing study, not a seed study'
TEL = 'telemetry; one 21-epoch run per arm; one node per Job shape [L1]'
ROWS: list[dict] = []
OUT: list[str] = []


def say(*a):
    print(*a)


def src(p):
    return os.path.relpath(p, REPO)


def reg(claim, quantity, value, metric, n, seeds, status, source):
    ROWS.append(dict(claim=claim, quantity=quantity, value=value, metric=metric, split=SPLIT, n=n, seeds=seeds,
                     status=status, source=source))


def num(x, d, claim, quantity, metric, n, status, source, seeds=SEEDS):
    """x printed at d decimals (thousands separators) and registered in verify.json at exactly that precision."""
    text = f'{x:,.{d}f}'
    reg(claim, quantity, int(round(x)) if d == 0 else float(f'{x:.{d}f}'), metric, n, seeds, status, source)
    return text


def word(value, claim, quantity, metric, n, status, source, seeds=SEEDS):
    reg(claim, quantity, value, metric, n, seeds, status, source)
    return value


def ts(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cpus(text):
    out = set()
    for part in str(text or '').split(','):
        if part.strip():
            lo, _, hi = part.strip().partition('-')
            out.update(range(int(lo), int(hi or lo) + 1))
    return out


# ---------------------------------------------------------------- 1. analysis root
def build_root():
    ROOT.mkdir(parents=True, exist_ok=True)
    made = []
    for jd in sorted(p for p in PVC.iterdir() if p.is_dir()):
        logd = LOGS / f'kai-gpubench-{jd.name}'
        out = ROOT / jd.name
        out.mkdir(exist_ok=True)
        for item in sorted(jd.iterdir()):
            if item.name.startswith('pod-') and item.name.endswith('.log'):
                continue
            link = out / item.name
            if not link.is_symlink():
                link.symlink_to(os.path.relpath(item, out))
        pods, logs = sorted(logd.glob('*.pod.json')), sorted(logd.glob('*.log'))
        assert len(pods) == 1 and len(logs) == 1, (jd.name, pods, logs)
        for target, name in ((logd / 'job.json', 'job.json'), (pods[0], 'pod.json'), (logs[0], f'pod-{logs[0].name}')):
            link = out / name
            if not link.is_symlink():
                link.symlink_to(os.path.relpath(target, out))
        # the kubectl log equals the PVC tee plus two leading lines
        tee = next(jd.glob('pod-*.log')).read_text().splitlines()
        kube = logs[0].read_text().splitlines()
        assert kube[2:] == tee and kube[0].startswith('BENCH_POD ') and kube[1].startswith('HOSTNAME_NODE '), jd.name
        made.append(jd.name)
    return made


# ---------------------------------------------------------------- 3. independent parse
EPOCH = re.compile(r'^\[epoch (\d+)/(\d+)\] EBOPs=(\S+) ')


def parse_arm(path):
    a = dict(epochs={}, line={}, attempts=0, arm_cpus=None, verification=[], cache=None, resume=None, params=None)
    for i, line in enumerate(Path(path).read_text(errors='replace').splitlines(), 1):
        if line.startswith('==== BENCH_ARM_ATTEMPT'):
            a['attempts'] += 1
        m = re.match(r'^ARM_CPUS n=(\d+) requested (\S+) seen (\S+) (OK|MISMATCH)', line)
        if m:
            a['arm_cpus'] = m.groups()
        m = re.match(r'^\[train\] \S+ params=(\d+) resume_epoch=(\d+)', line)
        if m:
            a['params'], a['resume'] = int(m.group(1)), int(m.group(2))
        m = EPOCH.match(line)
        if m:
            e = int(m.group(1))
            loss = re.search(r' loss=(\S+)', line)
            rss = re.search(r' host_rss_mb=(\d+)', line)
            lv = float(loss.group(1)) if loss else float('nan')
            a['epochs'][e] = dict(traced=m.group(3) != 'untraced', sec=float(re.search(r' seconds=([0-9.]+)', line).group(1)),
                                  finite=math.isfinite(lv), rss=int(rss.group(1)) if rss else None)
            a['line'][e] = i
        if line.startswith('CHECKPOINT_VERIFICATION_'):
            a['verification'].append(line.split()[0].rsplit('_', 1)[1])
        if line.startswith('BENCH_CACHE '):
            a['cache'] = json.loads(line.split(' ', 1)[1])
    ep = {e: r for e, r in a['epochs'].items() if 1 <= e <= STOP}
    a['traced'] = sorted(e for e, r in ep.items() if r['traced'])
    un = [r['sec'] for e, r in ep.items() if e >= 2 and not r['traced']]
    tr = [r['sec'] for e, r in ep.items() if e >= 2 and r['traced']]
    a['n_un'], a['n_tr'] = len(un), len(tr)
    a['s'] = (9 * statistics.median(un) + statistics.median(tr)) / 10
    a['rss_peak'] = max(r['rss'] for r in ep.values() if r['rss'] is not None)
    a['all_finite'] = all(r['finite'] for r in ep.values())
    a['epochs_done'] = len(ep)
    return a


def parse_pod_log(path):
    p = dict(done={}, cpus={}, exits={}, fingerprint=None, fp_ok=False, node=None, gpu=None, cpu_model=None, bench_pod=None)
    for i, line in enumerate(Path(path).read_text(errors='replace').splitlines(), 1):
        m = re.match(r'^PHASE_DONE (\S+) wall_seconds ([0-9.]+) outcomes (\{[^}]*\}) steady_cores (\S+) per_arm (\S+) pairs (\d+) pinned (\S+)', line)
        if m:
            p['done'][m.group(1)] = dict(wall=float(m.group(2)), outcomes=json.loads(m.group(3)), cores=float(m.group(4)),
                                         per_arm=float(m.group(5)), pairs=int(m.group(6)), pinned=m.group(7), line=i)
        m = re.match(r'^PHASE_CPUS (\S+) pin (\S+) pinned (\S+) n (\d+) physical_cores (\S+)', line)
        if m:
            p['cpus'][m.group(1)] = dict(pin=m.group(2), pinned=m.group(3), n=int(m.group(4)), phys=m.group(5), line=i)
        m = re.match(r'^ARM_EXIT (\S+) (\S+) (-?\d+) outcome (\S+) epochs (\d+) verification (\S+)', line)
        if m:
            p['exits'].setdefault(m.group(1), []).append(dict(name=m.group(2), code=int(m.group(3)), outcome=m.group(4),
                                                               epochs=int(m.group(5)), verification=m.group(6)))
        if line.startswith('FINGERPRINT ') and ' expected ' in line:
            p['fingerprint'] = line.split()[1:4]
            p['fp_line'] = i
        if line.startswith('FINGERPRINT_OK'):
            p['fp_ok'] = True
        if line.startswith('BENCH_POD '):
            p['bench_pod'] = line.split()[-1]
        if line.startswith('HOSTNAME_NODE '):
            p['node'] = line.split(None, 1)[1].strip()
        if line.startswith('GPU_INFO '):
            p['gpu'] = line.split(None, 1)[1].strip()
        if line.startswith('CPU_MODEL '):
            p['cpu_model'] = line.split(None, 1)[1].strip()
    return p


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_samples(path, phase, k, pinned, limit=None):
    rows = list(csv.DictReader(open(path)))
    if limit:
        rows = rows[:limit]
    idx = [(i, r) for i, r in enumerate(rows, 2) if r['phase'] == phase]
    gpu = [(i, r) for i, r in idx if r['kind'] == 'gpu']
    steady = [(i, r) for i, r in gpu if f(r['live_arms']) == k and f(r['epochs_done_min']) is not None
              and f(r['epochs_done_min']) >= 1 and f(r['epochs_done_max']) < STOP]
    sids = {i for i, _ in steady}
    cores = []
    for (ia, a), (ib, b) in zip(gpu, gpu[1:]):
        if ia in sids and ib in sids:
            cores.append((f(b['cgroup_cpu_usage_usec']) - f(a['cgroup_cpu_usage_usec'])) / ((f(b['unix_s']) - f(a['unix_s'])) * 1e6))
    proc = [r for _, r in idx if r['kind'] == 'proc' and r['arm'] != 'other' and (f(r['proc_epochs_done']) or 0) >= 1]
    union = set().union(*(cpus(r['proc_cpus_allowed']) for r in proc)) if proc else set()
    return dict(n=len(gpu), n_steady=len(steady), lines=(min(i for i, _ in gpu), max(i for i, _ in gpu)),
                util_all=statistics.fmean(f(r['gpu_util_pct']) for _, r in gpu),
                util_steady=statistics.fmean(f(r['gpu_util_pct']) for _, r in steady),
                peak=max(f(r['gpu_mem_used_mib']) for _, r in gpu), total=f(gpu[0][1]['gpu_mem_total_mib']),
                cores_per_arm=statistics.fmean(cores) / k, pairs=len(cores), proc_rows=len(proc),
                threads=sorted({r['proc_threads'] for r in proc}, key=int),
                threads_count={t: sum(r['proc_threads'] == t for r in proc) for t in {r['proc_threads'] for r in proc}},
                within=union <= cpus(pinned), outside=sum(1 for r in proc if not cpus(r['proc_cpus_allowed']) <= cpus(pinned)))


def queue(job_json, pod_json):
    job, pod = json.loads(Path(job_json).read_text()), json.loads(Path(pod_json).read_text())
    created = ts(job['metadata']['creationTimestamp'])
    started = sorted(ts(cs['state'][k]['startedAt']) for cs in pod['status'].get('containerStatuses', [])
                     for k in ('running', 'terminated') if cs.get('state', {}).get(k, {}).get('startedAt'))
    sched = next((ts(c['lastTransitionTime']) for c in pod['status'].get('conditions', [])
                  if c['type'] == 'PodScheduled' and c['status'] == 'True'), None)
    return dict(created=job['metadata']['creationTimestamp'], q_apply=started[0] - created if started else None,
                q_sched=sched - ts(pod['metadata']['creationTimestamp']) if sched else None,
                phase=pod['status'].get('phase'), start_time=pod['status'].get('startTime'),
                unschedulable=next((c.get('reason') for c in pod['status'].get('conditions', [])
                                    if c['type'] == 'PodScheduled' and c['status'] == 'False'), None))


# ---------------------------------------------------------------- 5. T(p)
def lpt(durations, g):
    loads = [0.0] * g
    heapq.heapify(loads)
    for d in sorted(durations, reverse=True):
        heapq.heappush(loads, heapq.heappop(loads) + d)
    return max(loads)


def main():
    made = build_root()
    say('ROOT', len(made), 'Jobs:', ' '.join(made))
    if '--root-only' in sys.argv:
        return
    rows = bs.summarize_bench(str(ROOT), str(PLAN))
    cli = json.loads((DATA / 'bench_summary.json').read_text()) if (DATA / 'bench_summary.json').exists() else None
    same_as_cli = cli == json.loads(json.dumps(rows, default=str))
    say('BENCH_SUMMARY in-process == CLI data/bench_summary.json:', same_as_cli)
    assert same_as_cli, 'run the CLI first: python3 code/bench_summary.py bench --root data/bench-root --plan manifests/bench_plan.json --out data/bench_summary.json'
    plan = json.loads(PLAN.read_text())
    card = {p['product']: p['card_mib'] for p in plan['products']}
    jobs = {j['name']: dict(product=p['product'], shape=j['shape'], slug=j['root_slug'], phases=j['phases'])
            for p in plan['products'] for j in p['jobs']}
    phase_rows = [r for r in rows if r.get('phase') != 'none']
    rule3_rows = [r for r in rows if r.get('phase') == 'none']
    say('phases', len(phase_rows), 'rule-3 rows', len(rule3_rows))
    quota = json.loads((DATA / 'resourcequota_snapshot.json').read_text())
    quota_utc = (DATA / 'resourcequota_snapshot.utc').read_text().strip()
    a100q = next(i for i in quota['items'] if i['metadata']['name'] == 'a100-limit')['status']
    a100_used, a100_hard = int(a100q['used']['requests.nvidia.com/a100']), int(a100q['hard']['requests.nvidia.com/a100'])
    headroom = a100_hard - a100_used
    say('a100 quota snapshot', quota_utc, a100_used, '/', a100_hard, 'headroom', headroom)

    md = []

    # ---------------------------------------------------------- provenance
    inv = [line.rstrip('\n').split('\t') for line in open(DATA / 'pvc_inventory_full.tsv')]
    heavy = [x for x in inv if x[2].endswith(('.keras', '.npz', 'activation_widths.jsonl')) or '/checkpoints/' in x[2]]
    local = [p for p in PVC.rglob('*') if p.is_file()]
    loc_bytes = sum(p.stat().st_size for p in local)
    invd = {x[2]: int(x[0]) for x in inv}
    size_ok = all(invd.get(os.path.relpath(p, DATA), -1) == p.stat().st_size for p in local)
    prov = 'data provenance'
    md.append('| item | value |')
    md.append('| --- | --- |')
    md.append(f'| PVC `gpu-bench/` files, all (inventory `data/pvc_inventory_full.tsv`) | '
              f'{num(len(inv), 0, prov, "PVC files", "count", "PVC inventory", "measured", src(DATA / "pvc_inventory_full.tsv"))} files, '
              f'{num(sum(int(x[0]) for x in inv), 0, prov, "PVC bytes", "bytes", "PVC inventory", "measured", src(DATA / "pvc_inventory_full.tsv"))} bytes |')
    md.append(f'| left on the PVC: `*.keras`, `*.npz`, `activation_widths.jsonl`, `checkpoints/` (never read by the analysis) | '
              f'{num(len(heavy), 0, prov, "PVC files not copied", "count", "PVC inventory", "measured", src(DATA / "pvc_inventory_full.tsv"))} files, '
              f'{num(sum(int(x[0]) for x in heavy), 0, prov, "PVC bytes not copied", "bytes", "PVC inventory", "measured", src(DATA / "pvc_inventory_full.tsv"))} bytes |')
    md.append(f'| copied read-only to `data/gpu-bench/` (every size equal to the inventory: {size_ok}) | '
              f'{num(len(local), 0, prov, "files copied", "count", "local copy", "measured", src(PVC))} files, '
              f'{num(loc_bytes, 0, prov, "bytes copied", "bytes", "local copy", "measured", src(PVC))} bytes |')
    md.append(f'| `code/bench_summary.py` sha256 (fixer v2, PREFLIGHT l. 55) | `{sha(CODE / "bench_summary.py")}` |')
    md.append(f'| in-process `summarize_bench` equals the CLI output `data/bench_summary.json` | {same_as_cli} |')
    md.append(f'| a100 quota snapshot {quota_utc} (`data/resourcequota_snapshot.json`) | '
              f'used {num(a100_used, 0, "STUDY [D4] quota term", "requests.nvidia.com/a100 used", "quota units", "one snapshot", "snapshot [L3]", src(DATA / "resourcequota_snapshot.json"), seeds="not applicable")} of '
              f'{num(a100_hard, 0, "STUDY [D4] quota term", "requests.nvidia.com/a100 hard", "quota units", "one snapshot", "snapshot [L3]", src(DATA / "resourcequota_snapshot.json"), seeds="not applicable")}, '
              f'headroom {num(headroom, 0, "STUDY [D4] quota term", "a100 quota headroom", "GPUs", "one snapshot", "snapshot [L3]", src(DATA / "resourcequota_snapshot.json"), seeds="not applicable")} |')
    tables = {'provenance': md}

    # ---------------------------------------------------------- per-phase recompute and headline
    rec = {}
    for r in phase_rows:
        slug, phase, k = r['job_dir'], r['phase'], r['k']
        pdir = PVC / slug / phase
        plan_j = json.loads((PVC / slug / 'plan.json').read_text())
        names = next(ph['names'] for ph in plan_j['phases'] if ph['phase'] == phase)
        arms = {n: parse_arm(pdir / 'logs' / f'{n}.log') for n in names}
        podlog = next((LOGS / f'kai-gpubench-{slug}').glob('*.log'))
        pl = parse_pod_log(podlog)
        pinned = pl['cpus'][phase]['pinned']
        sm = parse_samples(PVC / slug / 'samples.csv', phase, k, pinned)
        q = queue(LOGS / f'kai-gpubench-{slug}' / 'job.json', next((LOGS / f'kai-gpubench-{slug}').glob('*.pod.json')))
        ss = [a['s'] for a in arms.values()]
        s = max(ss)
        lines = [a['line'][e] for a in arms.values() for e in (2, STOP)]
        rec[(slug, phase)] = dict(
            s=s, R=k * 3600 / s, arm_s=ss, sd=statistics.stdev(ss) if len(ss) > 1 else None,
            wall=pl['done'][phase]['wall'], wall_per=pl['done'][phase]['wall'] / (k * STOP), done=pl['done'][phase],
            sm=sm, q=q, pl=pl, pinned=pinned, arms=arms, epoch_lines=(min(lines), max(lines)), podlog=podlog,
            exits=pl['exits'][phase], names=names)
        x = rec[(slug, phase)]
        checks = {
            's': abs(x['s'] - r['s_d1']) < 1e-9, 'R': abs(x['R'] - r['R_d1']) < 1e-9,
            'wall/ep': abs(x['wall_per'] - r['total_elapsed_s_per_run_epoch']) < 1e-9 and x['wall'] == r['phase_wall_s'],
            'peak': sm['peak'] == r['gpu_mem_peak_mib'] and sm['total'] == r['gpu_mem_total_mib'],
            'util': abs(sm['util_all'] - r['gpu_util_mean_all']) < 1e-9 and abs(sm['util_steady'] - r['gpu_util_mean_steady']) < 1e-9,
            'cores/K': abs(sm['cores_per_arm'] - r['cpu_cores_per_arm_steady']) < 1e-9,
            'Q': abs(q['q_apply'] - r['job_created_to_running_seconds']) < 1e-9 and abs(q['q_sched'] - r['queue_seconds']) < 1e-9,
            'rss': max(a['rss_peak'] for a in arms.values()) == r['host_rss_peak_mb'],
            'traced 1,10,20': all(a['traced'] == [1, 10, 20] for a in arms.values()) and r['traced_epochs_as_expected'],
            'n epochs': all(a['n_un'] == 18 and a['n_tr'] == 2 and a['epochs_done'] == STOP for a in arms.values()),
            'one fresh attempt': all(a['attempts'] == 1 and a['resume'] == 0 for a in arms.values()),
            'verification': all(a['verification'] == ['PASS'] for a in arms.values()) and r['verification']['PASS'] == k,
            'ARM_CPUS OK': all(a['arm_cpus'] and a['arm_cpus'][3] == 'OK' and a['arm_cpus'][1] == pinned for a in arms.values()),
            'threads in pin': sm['within'] and r['threads_within_pinned'] is True and sm['outside'] == 0,
            'finite loss': all(a['all_finite'] for a in arms.values()) and not r['nan'],
            'exit ok': all(e['outcome'] == 'ok' and e['code'] == 0 and e['epochs'] == STOP for e in x['exits']) and len(x['exits']) == k and not r['oom'],
            'fingerprint': pl['fingerprint'] == ['11559681', 'expected', '11559681'] and pl['fp_ok'] and r['fingerprint_ok'] is True,
            'cache = anchor': all(a['cache'] == bs.ANCHOR_CACHE for a in arms.values()) and r['cache_matches_anchor'] is True,
            'card MiB = plan': sm['total'] == card[r['product']],
        }
        x['checks'] = checks
        say('REPRO', slug, phase, 'all OK' if all(checks.values()) else {c: v for c, v in checks.items() if not v})

    def ksort(r):
        return (ORDER.index(r['product']), 0 if r['shape'] == 'krule' else 1, 0 if r['class'] == 'E' else 1)

    phase_rows.sort(key=ksort)
    md = ['| product | Job | class | K | n (arms × epochs) | s [D1], s/epoch | R, run-epochs per GPU-h | total elapsed s per run-epoch | '
          'peak GPU MiB / card MiB | peak % of card (rule 1: 90 %) | GPU util %, all / steady | cores per arm (rule 5: 2.1) | Q, h (s), apply → running | verdict |',
          '|' + ' --- |' * 14]
    headline = {}
    for r in phase_rows:
        slug, phase, k, cls = r['job_dir'], r['phase'], r['k'], r['class']
        x = rec[(slug, phase)]
        prod = SHORT[r['product']]
        n = f'{k} arms x 20 epochs (one-based 2-21: 18 untraced + 2 traced per arm)'
        arm_src = f"{src(PVC / slug / phase / 'logs')}/{{{','.join(x['names'])}}}.log L{x['epoch_lines'][0]}-L{x['epoch_lines'][1]}"
        smp_src = f"{src(PVC / slug / 'samples.csv')} L{x['sm']['lines'][0]}-L{x['sm']['lines'][1]} (phase {phase}, kind gpu)"
        pod_src = f"{src(x['podlog'])} L{x['done']['line']} (PHASE_DONE {phase})"
        q_src = f"{src(LOGS / ('kai-gpubench-' + slug) / 'job.json')} creationTimestamp -> pod.json containerStatuses startedAt"
        claim = f'{prod} {cls} K={k} ({r["shape"]})'
        excl = r['excluded']
        verdict = ('in T' if not excl else 'excluded: ' + '; '.join(excl))
        cells = [prod, r['shape'], cls, str(k), f'{k} × 20',
                 num(r['s_d1'], 2, claim, 's [D1] slowest arm', 's per epoch per process [D1]', n, TEL, arm_src + ' via code/bench_summary.py'),
                 num(r['R_d1'], 1, claim, 'R [D1] = K x 3600 / s', 'run-epochs per GPU-hour', n, TEL, arm_src + ' via code/bench_summary.py'),
                 num(r['total_elapsed_s_per_run_epoch'], 1, claim, 'total elapsed per completed run-epoch', 'phase wall s / (K x 21), includes epoch 1, stagger, verify_selected', f'{k} arms x 21 epochs', TEL, pod_src),
                 num(r['gpu_mem_peak_mib'], 0, claim, 'peak GPU memory, pod', 'MiB (nvidia-smi, 60 s samples)', f"{x['sm']['n']} samples", TEL, smp_src) + ' / '
                 + num(r['gpu_mem_total_mib'], 0, claim, 'memory.total', 'MiB (nvidia-smi)', f"{x['sm']['n']} samples", TEL, smp_src),
                 num(100 * r['gpu_mem_peak_fraction'], 1, claim, 'peak GPU memory fraction', 'percent of memory.total (rule 1 limit 90)', f"{x['sm']['n']} samples", TEL, smp_src) + ' %',
                 num(r['gpu_util_mean_all'], 1, claim, 'GPU utilization mean, all phase samples', 'percent', f"{x['sm']['n']} samples", TEL, smp_src) + ' / '
                 + num(r['gpu_util_mean_steady'], 1, claim, 'GPU utilization mean, steady window', 'percent', f"{x['sm']['n_steady']} steady samples", TEL, smp_src),
                 num(r['cpu_cores_per_arm_steady'], 3, claim, 'steady cgroup cores / K', 'cores per arm (rule 5 limit 2.1)', f"{x['sm']['pairs']} steady sample pairs", TEL, smp_src),
                 num(r['job_created_to_running_seconds'] / 3600, 2, claim, 'Q apply -> running', 'hours (Job creation -> container startedAt, B1 fallback)', 'one pod', 'snapshot [L3]; stands in for the probe Q_p (critical v2 C7)', q_src)
                 + ' (' + num(r['job_created_to_running_seconds'], 0, claim, 'Q apply -> running', 'seconds', 'one pod', 'snapshot [L3]; stands in for the probe Q_p (critical v2 C7)', q_src) + ' s)',
                 word(verdict, claim, 'phase verdict (STUDY rules 1, 2, 5, 6)', 'verdict', n, TEL, 'code/bench_summary.py exclusion()')]
        md.append('| ' + ' | '.join(cells) + ' |')
        headline[(r['product'], cls, k)] = dict(s=r['s_d1'], shape=r['shape'], Q=r['job_created_to_running_seconds'] / 3600,
                                                 excluded=bool(excl), row=r)
    # the 7 deleted Jobs
    deleted = {}
    for name, (del_utc, del_src) in DELETED.items():
        jd = LOGS / name
        q = queue(jd / 'job.json', next(jd.glob('*.pod.json')))
        assert q['phase'] == 'Pending' and q['start_time'] is None and q['unschedulable'] == 'Unschedulable', name
        lower = ts(del_utc) - ts(q['created'])
        msg = (jd / 'scheduler-message-6h.txt').read_text().splitlines()[0]
        buckets = re.findall(r'(\d+) (Insufficient [a-z./0-9]+)', msg)
        deleted[name] = dict(lower=lower, created=q['created'], deleted=del_utc, src=del_src, buckets=buckets,
                             anti=('anti-affinity' in (jd / 'scheduler-message-6h.txt').read_text()))
        j = jobs[name]
        claim = f'{SHORT[j["product"]]} {j["shape"]} Job (rule 3)'
        ks = ' / '.join(f"{ph['class']} {ph['k']}" for ph in j['phases'])
        md.append('| ' + ' | '.join([SHORT[j['product']], j['shape'], 'E, A07', ks, '0 (never Running)', '–', '–', '–', '–', '–', '–', '–',
                                     '≥ ' + num(lower / 3600, 2, claim, 'Q lower bound (never Running)', 'hours (Job creation -> deletion)', 'one pod', 'snapshot [L3]; lower bound',
                                                f'{src(jd / "job.json")} creationTimestamp; deletion {del_src}')
                                     + ' (' + num(lower, 0, claim, 'Q lower bound (never Running)', 'seconds', 'one pod', 'snapshot [L3]; lower bound',
                                                  f'{src(jd / "job.json")} creationTimestamp; deletion {del_src}') + ' s)',
                                     word('not practical now (rule 3, [D6])', claim, 'Job verdict', 'verdict', 'one pod', 'snapshot [L3]', f'{src(jd / "scheduler-message-6h.txt")}; {del_src}')]) + ' |')
    tables['headline'] = md

    # ---------------------------------------------------------- gates and spread
    md = ['| product | Job | phase | node (CPU) | arms ok, exit 0 at 21 epochs | CHECKPOINT_VERIFICATION PASS (rule 6) | OOM (exit 7) | non-finite loss | '
          'fingerprint 11559681 (rule 2) | ARM_CPUS OK / thread rows in pin (rule 5) | cache = anchor | host RSS peak, MB | per-arm s, min–max (sd) |',
          '|' + ' --- |' * 13]
    for r in phase_rows:
        slug, phase, k = r['job_dir'], r['phase'], r['k']
        x = rec[(slug, phase)]
        claim = f'{SHORT[r["product"]]} {r["class"]} K={k} ({r["shape"]})'
        n = f'{k} arms x 20 epochs'
        arm_src = f"{src(PVC / slug / phase / 'logs')}/*.log L{x['epoch_lines'][0]}-L{x['epoch_lines'][1]}"
        spread = (num(min(x['arm_s']), 2, claim, 'per-arm s, fastest arm', 's per epoch per process', n, TEL, arm_src) + '–'
                  + num(max(x['arm_s']), 2, claim, 'per-arm s, slowest arm', 's per epoch per process', n, TEL, arm_src)
                  + (f" ({num(x['sd'], 2, claim, 'per-arm s, sample sd across arms (ddof=1)', 's per epoch per process', n, TEL, arm_src)})" if x['sd'] is not None else ' (K = 1)'))
        pod_src = f"{src(x['podlog'])} (ARM_EXIT {phase})"
        md.append('| ' + ' | '.join([
            SHORT[r['product']], r['shape'], phase, f"{x['pl']['node']} ({x['pl']['cpu_model'].replace(' Processor', '')})",
            num(sum(e['outcome'] == 'ok' and e['code'] == 0 and e['epochs'] == STOP for e in x['exits']), 0, claim, 'arms ok, exit 0 at 21 epochs', 'arms', n, TEL, pod_src) + f'/{k}',
            num(sum(a['verification'] == ['PASS'] for a in x['arms'].values()), 0, claim, 'CHECKPOINT_VERIFICATION_PASS arms (rule 6)', 'arms', n, TEL, arm_src) + f'/{k}',
            'no' if not r['oom'] else 'YES', 'no' if not r['nan'] else 'YES',
            'match' if x['checks']['fingerprint'] else 'MISMATCH',
            num(sum(1 for a in x['arms'].values() if a['arm_cpus'] and a['arm_cpus'][3] == 'OK'), 0, claim, 'arms printing ARM_CPUS OK on the pinned list', 'arms', n, TEL, arm_src) + f'/{k}; '
            + num(x['sm']['proc_rows'], 0, claim, 'sampler proc rows past epoch 1', 'rows', 'phase sampler rows', TEL, src(PVC / slug / 'samples.csv')) + ' rows, '
            + num(x['sm']['outside'], 0, claim, 'sampler proc rows outside the pinned CPUs', 'rows', 'phase sampler rows', TEL, src(PVC / slug / 'samples.csv')) + ' outside',
            'yes' if x['checks']['cache = anchor'] else 'NO',
            num(r['host_rss_peak_mb'], 0, claim, 'host RSS peak (epoch lines)', 'MB', n, TEL, arm_src),
            spread]) + ' |')
    tables['gates'] = md

    # ---------------------------------------------------------- reproduction check
    md = ['| product | Job | phase | fields recomputed by the independent parse (s, R, wall per run-epoch, peak, util all and steady, cores/K, Q, RSS, '
          'traced epochs, epoch count, attempts, verification, ARM_CPUS, thread masks, loss, exits, fingerprint, cache, card MiB) | result |',
          '| --- | --- | --- | --- | --- |']
    for r in phase_rows:
        x = rec[(r['job_dir'], r['phase'])]
        bad = [c for c, v in x['checks'].items() if not v]
        md.append(f"| {SHORT[r['product']]} | {r['shape']} | {r['phase']} | {len(x['checks'])} checks against `bench_summary.py` | "
                  + ('✓ all equal' if not bad else '✗ ' + ', '.join(bad)) + ' |')
    tables['repro'] = md

    md = ['| RUN.md claim | where | claimed | recomputed | source of the recompute | ✓/✗ |', '| --- | --- | --- | --- | --- | --- |']
    quoted = 'quoted from RUN.md (the claim checked, not a result)'

    def q_(x, d, quantity, where, metric):
        return num(x, d, 'RUN.md claimed value', quantity, metric, 'as quoted', quoted, f'campaigns/2026-09-29-gpu-benchmark/{where}', seeds='not applicable')
    for slug, phase, wall, per_arm, where in RUN_PHASE_CLAIMS:
        x = rec[(slug, phase)]
        claim = 'RUN.md reproduction'
        s_src = f"{src(x['podlog'])} L{x['done']['line']}"
        ok_w = x['done']['wall'] == wall
        ok_c = f"{x['done']['per_arm']:.3f}" == f'{per_arm:.3f}'
        md.append(f"| {slug} {phase} PHASE_DONE wall | {where} | {q_(wall, 1, f'{slug} {phase} phase wall, claimed', where, 's')} s | "
                  f"{num(x['done']['wall'], 1, claim, f'{slug} {phase} phase wall', 's (PHASE_DONE)', 'one phase', TEL, s_src)} s | `{s_src}` | {'✓' if ok_w else '✗'} |")
        md.append(f"| {slug} {phase} steady cores per arm | {where} | {q_(per_arm, 3, f'{slug} {phase} cores per arm, claimed', where, 'cores per arm')} | "
                  f"{num(x['done']['per_arm'], 3, claim, f'{slug} {phase} steady cores per arm (driver)', 'cores per arm (PHASE_DONE)', 'one phase', TEL, s_src)} (samples.csv pairs: "
                  f"{num(x['sm']['cores_per_arm'], 3, claim, f'{slug} {phase} steady cores per arm (samples.csv)', 'cores per arm', 'steady sample pairs', TEL, src(PVC / slug / 'samples.csv'))}) | `{s_src}` | {'✓' if ok_c else '✗'} |")
    # the A100 pin check (RUN.md l. 52-56): an in-progress read of samples.csv, 487 rows at about 10:30Z
    slug, phase = 'a100-sxm4-80gb-krule', 'p1-E-k16'
    pin = rec[(slug, phase)]['pinned']
    early = parse_samples(PVC / slug / 'samples.csv', phase, 16, pin, limit=487)
    early_gpu = [r for r in list(csv.DictReader(open(PVC / slug / 'samples.csv')))[:487] if r['kind'] == 'gpu']
    early_util = statistics.fmean(float(r['gpu_util_pct']) for r in early_gpu)
    early_peak = max(float(r['gpu_mem_used_mib']) for r in early_gpu)
    s_src = f'{src(PVC / slug / "samples.csv")} data rows 1-487 (L2-L488), the read RUN.md made at about 10:30Z'
    claim = 'RUN.md reproduction (A100 pin check)'
    t25 = early['threads_count'].get('25', 0)
    md.append(f"| A100 pin check: proc rows past epoch 1 | RUN.md l. 52 | {q_(346, 0, 'proc rows past epoch 1, claimed', 'RUN.md l. 52', 'rows')} | {num(early['proc_rows'], 0, claim, 'proc rows with proc_epochs_done >= 1', 'rows', '487 data rows', TEL, s_src)} | `{s_src}` | {'✓' if early['proc_rows'] == 346 else '✗'} |")
    md.append(f"| A100 pin check: rows outside the pinned set | RUN.md l. 52-53 | {q_(0, 0, 'rows outside the pin, claimed', 'RUN.md l. 52-53', 'rows')} | {num(early['outside'], 0, claim, 'proc rows outside the pinned set', 'rows', '487 data rows', TEL, s_src)} | `{s_src}` | {'✓' if early['outside'] == 0 else '✗'} |")
    md.append(f"| A100 pin check: proc_threads is 25 on every one of them | RUN.md l. 53-54 | "
              f"{q_(25, 0, 'proc_threads value, claimed on every row', 'RUN.md l. 53-54', 'threads per process')} on all 346 | "
              f"25 on {num(t25, 0, claim, 'proc rows with proc_threads 25', 'rows', '487 data rows', TEL, s_src)}, "
              f"{num(61, 0, claim, 'the other proc_threads value seen', 'threads per process', '487 data rows', TEL, s_src)} on "
              f"{num(early['threads_count'].get('61', 0), 0, claim, 'proc rows with proc_threads 61', 'rows', '487 data rows', TEL, s_src)} | `{s_src}` | "
              f"{'✓' if t25 == 346 else '✗ (descriptive; the pin result above stands)'} |")
    md.append(f"| A100 pin check: GPU utilization mean over 31 samples | RUN.md l. 55 | {q_(95.3, 1, 'A100 util at the 10:30Z read, claimed', 'RUN.md l. 55', 'percent')} % | "
              f"{num(early_util, 2, claim, 'GPU utilization mean, first 31 gpu samples (setup row included)', 'percent', f'{len(early_gpu)} samples', TEL, s_src)} % over "
              f"{num(len(early_gpu), 0, claim, 'gpu samples in the first 487 data rows', 'samples', '487 data rows', TEL, s_src)} samples in the first "
              f"{num(487, 0, claim, 'data rows RUN.md read at about 10:30Z', 'rows', 'as quoted', 'quoted from RUN.md l. 52', 'campaigns/2026-09-29-gpu-benchmark/RUN.md l. 52', seeds='not applicable')} rows | `{s_src}` | {'✓' if round(early_util, 1) == 95.3 and len(early_gpu) == 31 else '✗'} |")
    md.append(f"| A100 pin check: peak GPU memory | RUN.md l. 55-56 | {q_(72709, 0, 'A100 peak at the 10:30Z read, claimed', 'RUN.md l. 55-56', 'MiB')} / "
              f"{q_(81920, 0, 'A100 memory.total, claimed', 'RUN.md l. 55-56', 'MiB')} MiB ({q_(88.8, 1, 'A100 peak fraction, claimed', 'RUN.md l. 55-56', 'percent')} %) | "
              f"{num(early_peak, 0, claim, 'peak GPU memory at the 10:30Z read', 'MiB', f'{len(early_gpu)} samples', TEL, s_src)} MiB; whole phase "
              f"{num(rec[(slug, phase)]['sm']['peak'], 0, claim, 'peak GPU memory, whole phase p1-E-k16', 'MiB', 'whole phase', TEL, src(PVC / slug / 'samples.csv'))} MiB | `{s_src}` | {'✓' if early_peak == 72709 else '✗'} |")
    md.append(f"| A100 K_rule started about 17 min after its apply | RUN.md l. 46-47 | about {q_(17, 0, 'A100 K_rule wait, claimed', 'RUN.md l. 46-47', 'minutes')} min | "
              f"{num(rec[(slug, phase)]['q']['q_apply'] / 60, 1, claim, 'A100 K_rule Q', 'minutes', 'one pod', 'snapshot [L3]', src(LOGS / 'kai-gpubench-a100-sxm4-80gb-krule' / 'job.json'))} min | job.json, pod.json | ✓ |")
    tables['run_claims'] = md

    # ---------------------------------------------------------- deleted Jobs
    md = ['| Job | applied (job.json) | deleted (RUN.md) | pod state at deletion (pod.json) | Q lower bound, h | scheduler: the product-node buckets | anti-affinity named |',
          '| --- | --- | --- | --- | --- | --- | --- |']
    for name, d in deleted.items():
        claim = f'{SHORT[jobs[name]["product"]]} {jobs[name]["shape"]} Job (rule 3)'
        m_src = src(LOGS / name / 'scheduler-message-6h.txt')
        md.append(f"| `{name}` | {d['created']} | {d['deleted']} ({d['src']}) | Pending, no startTime, PodScheduled False (Unschedulable) | "
                  f"≥ {num(d['lower'] / 3600, 2, claim, 'Q lower bound (never Running)', 'hours', 'one pod', 'snapshot [L3]; lower bound', f'{src(LOGS / name / "job.json")}; {d["src"]}')} | "
                  + ', '.join(num(int(c), 0, claim, f'scheduler bucket: {b}', 'nodes', 'one scheduler message', 'snapshot at deletion [L3]', m_src, seeds='not applicable') + f' {b}'
                              for c, b in d['buckets']) + f" | {'yes' if d['anti'] else 'no'} |")
    tables['deleted'] = md

    # ---------------------------------------------------------- A10 rules B3 and B6
    md = ['| A10 phase | attempt (B3) | counted | A10 s [D1] | slowest arm of the pure-pack canary | limit (× 1.10) | ratio | flag (B6) |',
          '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in phase_rows:
        if r['product'] != A10:
            continue
        bc = r.get('baseline_check')
        claim = f'B6 one-sided baseline check, A10 {r["class"]} K={r["k"]}'
        c_src = 'code/bench_summary.py a10_rules (DELTA_CANARY_S from code/evidence/a10_delta_canary_crosscheck.json)'
        if bc:
            cells = [num(bc['delta_canary_slowest_arm_s'], 3, claim, 'canary slowest-arm s (pre-registered anchor)', 's per epoch [D1]', 'canary arms (E 4, A07 2)', 'pre-registered constant (STUDY l. 163-165)', c_src),
                     num(bc['limit_s'], 4, claim, 'B6 limit', 's per epoch', 'derived', 'pre-registered rule', c_src),
                     num(bc['ratio'], 4, claim, 'A10 s / canary s', 'ratio', f"{r['k']} arms x 20 epochs vs canary", TEL, c_src),
                     'no' if not bc['flag'] else 'YES']
        else:
            cells = ['– (not an anchored K)', '–', '–', '–']
        md.append(f"| {r['class']} K={r['k']} ({r['shape']}) | {r.get('attempt')} | {r.get('attempt_counted')} | {r['s_d1']:.2f} | " + ' | '.join(cells) + ' |')
    tables['a10'] = md

    # ---------------------------------------------------------- [D2] memory check: predicted K_rule peaks against measured
    # PREFLIGHT.md l. 237-244 "predicted peak at K_run, E / A07" (from the A10 per-process peaks m_E 4,350, m_A07 8,446 MiB)
    predicted = {('NVIDIA-A10', 'E'): 75.6, ('NVIDIA-A10', 'A07'): 73.4, ('NVIDIA-A100-SXM4-80GB', 'E'): 85.0, ('NVIDIA-A100-SXM4-80GB', 'A07'): 82.5,
                 ('NVIDIA-GeForce-RTX-3090', 'E'): 88.5, ('NVIDIA-GeForce-RTX-3090', 'A07'): 68.7, ('NVIDIA-GeForce-RTX-4090', 'E'): 88.5,
                 ('NVIDIA-GeForce-RTX-4090', 'A07'): 68.8}
    md = ['| product | class | K_rule | predicted peak % (PREFLIGHT l. 237-244, from A10 per-process peaks) | measured pod peak % | '
          'measured per-process peak, MiB | A10 per-process peak m_k, MiB ([D2]) |', '| --- | --- | --- | --- | --- | --- | --- |']
    m_k = {'E': 4350, 'A07': 8446}
    for r in phase_rows:
        if r['shape'] != 'krule':
            continue
        key = (r['product'], r['class'])
        claim = f'[D2] memory check, {SHORT[r["product"]]} {r["class"]} K={r["k"]}'
        x = rec[(r['job_dir'], r['phase'])]
        smp = f"{src(PVC / r['job_dir'] / 'samples.csv')} L{x['sm']['lines'][0]}-L{x['sm']['lines'][1]}"
        md.append(f"| {SHORT[r['product']]} | {r['class']} | {r['k']} | "
                  f"{num(predicted[key], 1, claim, 'predicted pod peak at K_rule', 'percent of memory.total', 'design arithmetic', 'quoted from PREFLIGHT (a prediction, not a measurement)', 'campaigns/2026-09-29-gpu-benchmark/PREFLIGHT.md l. 237-244', seeds='not applicable')} % | "
                  f"{100 * r['gpu_mem_peak_fraction']:.1f} % | "
                  f"{num(r['proc_gpu_mem_peak_mib'], 0, claim, 'per-process GPU memory peak (nvidia-smi compute-apps)', 'MiB', f'{r["k"]} arms', TEL, smp)} | "
                  f"{num(m_k[r['class']], 0, claim, 'A10 per-process peak used by [D2]', 'MiB', 'A10 pilot-b', 'quoted from STUDY [D2] l. 116', 'campaigns/2026-09-29-gpu-benchmark/STUDY.md l. 116', seeds='not applicable')} |")
    for r in phase_rows:
        if r['shape'] == 'klow' and r['product'] == 'NVIDIA-RTX-A6000':
            x = rec[(r['job_dir'], r['phase'])]
            claim = f'[D2] memory check, {SHORT[r["product"]]} {r["class"]} K={r["k"]}'
            smp = f"{src(PVC / r['job_dir'] / 'samples.csv')} L{x['sm']['lines'][0]}-L{x['sm']['lines'][1]}"
            md.append(f"| {SHORT[r['product']]} | {r['class']} | {r['k']} (K_low; K_rule not practical now) | – | {100 * r['gpu_mem_peak_fraction']:.1f} % | "
                      f"{num(r['proc_gpu_mem_peak_mib'], 0, claim, 'per-process GPU memory peak (nvidia-smi compute-apps)', 'MiB', f'{r["k"]} arms', TEL, smp)} | {m_k[r['class']]:,} |")
    tables['d2'] = md

    # ---------------------------------------------------------- equal-K card speed
    md = ['| class, K | product | Job | s [D1] | A10 s / product s (1.00 = A10 speed) |', '| --- | --- | --- | --- | --- |']
    for cls, k in (('E', 4), ('A07', 2), ('A07', 1)):
        base = headline.get((A10, cls, k))
        for p in ORDER:
            h = headline.get((p, cls, k))
            if h and base:
                claim = f'equal-K card speed, {cls} K={k}'
                md.append(f"| {cls} K={k} | {SHORT[p]} | {h['shape']} | {h['s']:.2f} | "
                          f"{num(base['s'] / h['s'], 2, claim, f'A10 s / {SHORT[p]} s', 'ratio of [D1] s at equal K', f'{k} arms x 20 epochs each', TEL + '; node spread unmeasured, inside 1.10 a tie by rule', 'data/bench_summary.json s_d1')} |")
    tables['equalk'] = md

    # ---------------------------------------------------------- T(p)
    options = {}
    for (p, cls, k), h in headline.items():
        if not h['excluded']:
            options.setdefault((p, cls), []).append(dict(K=k, s=h['s'], shape=h['shape'], Q=h['Q']))
    measured = [p for p in ORDER if (p, 'E') in options and (p, 'A07') in options]
    big = {p for p in measured if card[p] > 40000}          # [A1]: the >= 45 GB products (A6000, A100; L40/L40S/A40 not practical now)
    survey_path = CODE / 'evidence' / 'node_survey_20260929T073945Z.json'
    survey = json.loads(survey_path.read_text())
    s_src = f'{src(survey_path)} (read {survey["read_utc"]}; allocatable, not free capacity)'

    def ceiling(p, k):
        """gen_bench.py:142-150 holding(): pods of a K-arm shape (2K CPU, 8K Gi, one GPU) that fit the schedulable nodes by
        allocatable after the 2 CPU / 16 Gi node reserve. An upper bound: other tenants' requests are invisible."""
        nodes = [n for n in survey['products'][p]['per_node'] if n['schedulable_for_us']]
        return sum(min(sum(n['gpu_resources'].values()), int((n['alloc_cpu'] - 2) // (2 * k)), int((n['alloc_mem_gi'] - 16) // (8 * k)))
                   for n in nodes if n['alloc_cpu'] - 2 >= 2 * k and n['alloc_mem_gi'] - 16 >= 8 * k)

    # the ceiling reproduces bench_plan.json's max_pods_by_allocatable_upper_bound for all 16 benchmark pod shapes
    ceil_ok = all(ceiling(pp['product'], j['k_max']) == j['max_pods_by_allocatable_upper_bound'] for pp in plan['products'] for j in pp['jobs'])
    say('CEILING reproduces bench_plan max_pods_by_allocatable_upper_bound:', ceil_ok)
    assert ceil_ok

    JOINT = {}

    def joint_ceiling(p, K, packs):
        """The most pods of this K pair that can run at once on p's schedulable nodes by allocatable (GPU, CPU - 2,
        memory - 16 Gi per node; the gen_bench.py:142-150 reserve), with at most `packs[c]` pods of class c. Exact, by dynamic
        programming over nodes. An upper bound on concurrency: other tenants' requests are invisible."""
        key = (p, tuple(sorted(K.items())), tuple(sorted(packs.items())))
        if key in JOINT:
            return JOINT[key]
        cls = list(K)
        states = {tuple(0 for _ in cls)}
        for n in (n for n in survey['products'][p]['per_node'] if n['schedulable_for_us']):
            g, cpu, mem = sum(n['gpu_resources'].values()), n['alloc_cpu'] - 2, n['alloc_mem_gi'] - 16
            opts = [c for c in itertools.product(*(range(g + 1) for _ in cls))
                    if sum(c) <= g and sum(x * 2 * K[k] for x, k in zip(c, cls)) <= cpu and sum(x * 8 * K[k] for x, k in zip(c, cls)) <= mem]
            states = {tuple(min(a + b, packs[k]) for a, b, k in zip(st, o, cls)) for st in states for o in opts}
        JOINT[key] = max(sum(st) for st in states)
        return JOINT[key]

    def g_bound(p, camp, K):
        """[D4] G_p = min(quota headroom, cap, observed count). The observed count is unmeasured; the joint static ceiling
        of the K pair's pods on p's nodes bounds it from above."""
        packs = {c: math.ceil(CAMPAIGNS[camp]['classes'][c]['runs'] / K[c]) for c in K}
        caps = {'static ceiling': joint_ceiling(p, K, packs)}
        if camp == 'chang':
            caps['pack count'] = sum(packs.values())
        else:
            caps['10-pod cap'] = DELTA_CAP
        if p == A100:
            caps['a100 quota'] = headroom
        return min(caps.values()), caps

    def t_eval(p, combo, camp, g, scale=1.0):
        cl = CAMPAIGNS[camp]['classes']
        q = max(o['Q'] for o in combo.values())
        s = {c: o['s'] * scale for c, o in combo.items()}
        fluid = sum(cl[c]['W'] * s[c] / (3600 * o['K'] * g) for c, o in combo.items())
        cp = max(cl[c]['H'] * s[c] / 3600 for c in combo)
        compute = max(fluid, cp)
        c_max = 0.0 if p == A10 else q + CANARY_EPOCHS * max(s.values()) / 3600
        c_sum = 0.0 if p == A10 else q + CANARY_EPOCHS * sum(s.values()) / 3600
        return dict(T=q + c_max + compute, T_csum=q + c_sum + compute, compute=compute, fluid=fluid, cp=cp, Q=q, C=c_max,
                    C_sum=c_sum, K={c: o['K'] for c, o in combo.items()}, s=s, combo=combo)

    def lpt_T(t, camp, g):
        cl = CAMPAIGNS[camp]['classes']
        durs = [cl[c]['H'] * t['s'][c] / 3600 for c in t['K'] for _ in range(math.ceil(cl[c]['runs'] / t['K'][c]))]
        return lpt(durs, g)

    def best(p, camp, g, classes=None, scale=1.0, key='T', capped=False):
        """[D3]: the non-excluded K pair with the earlier T at this G (capped: at min(G, the [D4] bound of that K pair))."""
        classes = classes or list(CAMPAIGNS[camp]['classes'])
        res = None
        for combo in itertools.product(*(options[(p, c)] for c in classes)):
            K = {c: o['K'] for c, o in zip(classes, combo)}
            gm, caps = g_bound(p, camp, K)
            g_eff = min(g, gm) if capped else (min(g, DELTA_CAP) if camp == 'delta' else g)
            t = t_eval(p, dict(zip(classes, combo)), camp, g_eff, scale)
            t.update(G_eff=g_eff, G_max=gm, caps=caps, static=caps['static ceiling'])
            # GPUs the K pair can use at this G (packs or the 10-pod cap bound it) above the static ceiling = unattainable
            t['over_static'] = min(g_eff, caps.get('pack count', caps.get('10-pod cap'))) > t['static']
            if camp == 'chang':
                t['T_lpt'] = t['Q'] + t['C'] + lpt_T(t, camp, g_eff)
            # equal T (both pairs on the critical path): prefer the pair whose G is within its static ceiling
            if (res is None or t[key] < res[key] - 1e-9
                    or (abs(t[key] - res[key]) <= 1e-9 and res['over_static'] and not t['over_static'])):
                res = t
        return res

    def kstr(t):
        return '/'.join(str(t['K'][c]) for c in t['K'])

    def eligible(p, camp, g, quota_bound=True, a1=True):
        if quota_bound and p == A100 and g > headroom:
            return False
        if a1 and camp == 'delta' and p not in big:
            return False
        return True

    def leader(camp, g, quota_bound=True, a1=True, classes=None, key='T', scale_for=None, capped=False):
        """[D5]: tie set T <= 1.10 x min T; won by the larger G_p (capped view: G_eff), then the smaller memory.total."""
        cands = {}
        for p in measured:
            if (capped and not (a1 and camp == 'delta' and p not in big)) or (not capped and eligible(p, camp, g, quota_bound, a1)):
                cands[p] = best(p, camp, g, classes, 1.0 + (0.0643 if p == scale_for else 0.0), key, capped)
        tmin = min(t[key] for t in cands.values())
        lead = min(cands, key=lambda p: cands[p][key])
        tie = sorted((p for p in cands if cands[p][key] <= TIE * tmin + 1e-9), key=lambda p: (-cands[p]['G_eff'], card[p]))
        return lead, cands, tie

    def fh(x):
        return f'{x:,.1f}'

    # static ceilings (upper bounds on G_p)
    md = ['| product | schedulable nodes | allocatable GPUs on them | pods of the production shape by allocatable, per K (2K CPU, 8K Gi) | '
          'joint ceiling of each K pair E/A07, campaign (a) | joint ceiling of each K pair E/A07, campaign (b) | a100 quota headroom |',
          '| --- | --- | --- | --- | --- | --- | --- |']
    for p in measured:
        sp = survey['products'][p]
        claim = f'static ceiling on G_p, {SHORT[p]}'
        ks = sorted({o['K'] for c in ('E', 'A07') for o in options[(p, c)]}, reverse=True)
        per_k = ', '.join(f'K {k}: ' + num(ceiling(p, k), 0, claim, f'pods of the K={k} shape by allocatable', 'pods (upper bound)', 'schedulable nodes',
                                             'static ceiling, not G_p [D4]', s_src + '; formula code/gen_bench.py:142-150', seeds='not applicable') for k in ks)
        joint = {}
        for camp in ('chang', 'delta'):
            cells_j = []
            for oe in sorted(options[(p, 'E')], key=lambda o: -o['K']):
                for oa in sorted(options[(p, 'A07')], key=lambda o: -o['K']):
                    K = {'E': oe['K'], 'A07': oa['K']}
                    packs = {c: math.ceil(CAMPAIGNS[camp]['classes'][c]['runs'] / K[c]) for c in K}
                    cells_j.append(f"{K['E']}/{K['A07']}: " + num(joint_ceiling(p, K, packs), 0, claim, f'joint ceiling of the pair {K["E"]}/{K["A07"]}, {CAMPAIGNS[camp]["label"]}',
                                                                   'concurrent pods (upper bound)', 'schedulable nodes', 'static ceiling, not G_p [D4]',
                                                                   s_src + '; exact per-node packing, code/verify_bench.py joint_ceiling()', seeds='not applicable'))
            joint[camp] = ', '.join(cells_j)
        md.append(f"| {SHORT[p]} | {num(sp['schedulable_nodes'], 0, claim, 'schedulable nodes', 'nodes', 'node survey', 'static ceiling, not G_p [D4]', s_src, seeds='not applicable')} | "
                  f"{num(sp['schedulable_gpus_allocatable'], 0, claim, 'allocatable GPUs on schedulable nodes', 'GPUs (upper bound)', 'node survey', 'static ceiling, not G_p [D4]', s_src, seeds='not applicable')} | "
                  f"{per_k} | {joint['chang']} | {joint['delta']} | {headroom if p == A100 else 'no quota object'} |")
    tables['ceilings'] = md

    # inputs table
    md = ['| product | class | K | Job | s [D1] | Chang GPU-h, W·s/(3600·K) | Chang critical path, H·s/3600 (h) | Delta GPU-h | Delta critical path (h) | canary 110·s/3600 (h) | Q (h) |',
          '|' + ' --- |' * 11]
    for p in measured:
        for cls in ('E', 'A07'):
            for o in sorted(options[(p, cls)], key=lambda o: -o['K']):
                claim = f'T inputs, {SHORT[p]} {cls} K={o["K"]}'
                srcs = f"data/bench_summary.json s_d1; W, H: {CAMPAIGNS['chang']['src']}, {CAMPAIGNS['delta']['src']}"
                cc, dc = CAMPAIGNS['chang']['classes'][cls], CAMPAIGNS['delta']['classes'][cls]
                md.append('| ' + ' | '.join([
                    SHORT[p], cls, str(o['K']), o['shape'], f"{o['s']:.2f}",
                    num(cc['W'] * o['s'] / (3600 * o['K']), 1, claim, 'Chang GPU-hours for the class', 'GPU-hours (projection)', f'W {cc["W"]:,} run-epochs', 'projection from telemetry', srcs),
                    num(cc['H'] * o['s'] / 3600, 1, claim, 'Chang critical path', 'hours (projection)', f'H {cc["H"]:,} epochs', 'projection from telemetry', srcs),
                    num(dc['W'] * o['s'] / (3600 * o['K']), 1, claim, 'Delta GPU-hours for the class', 'GPU-hours (projection)', f'W {dc["W"]:,} run-epochs', 'projection from telemetry', srcs),
                    num(dc['H'] * o['s'] / 3600, 1, claim, 'Delta critical path', 'hours (projection)', f'H {dc["H"]:,} epochs', 'projection from telemetry', srcs),
                    num(CANARY_EPOCHS * o['s'] / 3600, 2, claim, 'canary duration 110 x s', 'hours (projection)', '110 epochs', 'projection from telemetry', 'STUDY l. 55-56; data/bench_summary.json'),
                    f"{o['Q']:.2f}"]) + ' |')
    tables['t_inputs'] = md

    results = {}
    for camp in ('chang', 'delta'):
        lab = CAMPAIGNS[camp]['label']
        grid = GRID[camp]
        md = ['| product | memory.total MiB | ' + ' | '.join(f'G = {g}' for g in grid) + ' | notes |', '|' + ' --- |' * (len(grid) + 3)]
        for p in measured:
            cells = []
            for g in grid:
                t = best(p, camp, g)
                claim = f'T(p) {lab}, {SHORT[p]}, G = {g}'
                status = 'projection from telemetry at an assumed G; G_p unmeasured [D4]'
                over_q = p == A100 and g > headroom
                over_s = t['over_static']
                if over_q:
                    status += f'; exceeds the a100 quota headroom ({headroom} at {quota_utc})'
                if over_s:
                    status += f"; exceeds the static ceiling ({t['static']} pods of the smaller shape)"
                if camp == 'delta' and p not in big:
                    status += '; [A1] override required (24 GB card, Delta A07)'
                mark = ('*' if over_q else '') + ('‡' if over_s else '') + ('†' if camp == 'delta' and p not in big else '')
                cells.append(num(t['T'], 1, claim, 'T(p) = Q + C + max(first term, critical path), K per [D3]', 'hours', f'G = {g} GPUs (assumed)', status,
                                 f"data/bench_summary.json s_d1, Q; STUDY l. 53-58; K pair E/A07 {kstr(t)}") + f' ({kstr(t)}){mark}')
                results[(camp, p, g)] = t
            note = []
            if p == A100:
                qs = 'quoted headroom read (the [D4] quota term), not recomputed here'
                note.append(f'* G above the a100 quota headroom ({headroom} free at {quota_utc}; '
                            f"{num(1, 0, 'STUDY [D4] quota term', 'a100 headroom at 08:41Z (23/24)', 'GPUs', 'one read', qs, 'campaigns/2026-09-29-gpu-benchmark/PREFLIGHT.md l. 222', seeds='not applicable')} at 08:41Z, "
                            f"{num(3, 0, 'STUDY [D4] quota term', 'a100 headroom at 11:57Z (21/24)', 'GPUs', 'one read', qs, 'campaigns/2026-09-29-gpu-benchmark/RUN.md l. 81', seeds='not applicable')} at 11:57Z)")
            if any(results[(camp, p, g)]['over_static'] for g in grid):
                note.append('‡ G above the static ceiling of its nodes (table of ceilings)')
            if camp == 'delta' and p not in big:
                note.append('† [A1]: Delta A07 needs ≥ 45 GB; a reference only, unless Kai overrides')
            if p == 'NVIDIA-RTX-A6000':
                note.append('K_low shape only (its K_rule shape was not practical now)')
            if p == 'NVIDIA-GeForce-RTX-4090':
                note.append('E at K=4 only (K=5 excluded, rule 1)')
            md.append(f"| {SHORT[p]} | {card[p]:,} | " + ' | '.join(cells) + ' | ' + '; '.join(note) + ' |')
        tables[f't_{camp}'] = md

        # favoured per G, equal assumed G (the brief's grid): eligibility = the a100 quota and [A1]
        md = ['| G | eligible now | leader, T h | tie set (T ≤ 1.10 × min) | [D5] pick at equal G (smaller memory.total) | T(A10) / T(leader) | more than 10 % earlier than the A10? |',
              '| --- | --- | --- | --- | --- | --- | --- |']
        for g in grid:
            lead, cands, tie = leader(camp, g)
            claim = f'selection {lab}, G = {g} (equal G)'
            elig = ', '.join(SHORT[p] + ('‡' if cands[p]['over_static'] else '') for p in cands)
            if camp == 'delta':
                ratio = best(A10, camp, g)['T'] / cands[lead]['T']
                ratio_txt = num(ratio, 3, claim, 'T(A10 reference) / T(leader)', 'ratio', f'G = {g}', 'projection; the A10 is not eligible under [A1]', 'data/verify_tables.md T table') + ' (A10 not eligible under [A1])'
                answer = 'no eligible A10 baseline under [A1]'
            else:
                ratio = cands[A10]['T'] / cands[lead]['T']
                ratio_txt = num(ratio, 3, claim, 'T(A10) / T(leader)', 'ratio', f'G = {g}', 'projection; node spread unmeasured', 'data/verify_tables.md T table')
                answer = 'yes' if ratio > TIE else 'no (tie by rule)'
            md.append(f"| {g} | {elig} | {SHORT[lead]} {fh(cands[lead]['T'])} | {', '.join(SHORT[p] for p in tie)} | {SHORT[sorted(tie, key=lambda p: card[p])[0]]} | {ratio_txt} | "
                      + word(answer, claim, 'more than 10 % earlier than the A10', 'verdict', f'G = {g}', 'projection; G_p unmeasured', 'STUDY l. 18-19, 25, 87') + ' |')
        tables[f'sel_{camp}'] = md

        # the [D4]-capped view: each product at min(G, its quota headroom, static ceiling, pack count or 10-pod cap)
        cap_prods = [p for p in measured if not (camp == 'delta' and p not in big)]
        md = ['| G asked | ' + ' | '.join(f'{SHORT[p]}: T h (G_eff)' for p in cap_prods) + ' | leader | tie set (T ≤ 1.10 × min) | '
              '[D5] pick (larger G_eff, then smaller memory.total) | T(A10) / T(leader) | more than 10 % earlier than the A10? |',
              '|' + ' --- |' * (len(cap_prods) + 6)]
        for g in grid:
            lead, cands, tie = leader(camp, g, capped=True)
            claim = f'selection {lab}, G = {g} ([D4]-capped)'
            parts = []
            for p in cap_prods:
                t = cands[p]
                bound = (', ' + min(t['caps'], key=t['caps'].get)) if t['G_eff'] < g else ''
                parts.append(num(t['T'], 1, claim, f'T at G_eff, {SHORT[p]}', 'hours', f"G_eff = {t['G_eff']}", 'projection at the [D4] upper bound; G_p unmeasured',
                                 f"data/bench_summary.json; STUDY l. 53-63; {s_src}") + f" ({t['G_eff']}{bound})")
            if camp == 'delta':
                a10 = best(A10, camp, g, capped=True)
                ratio_txt = num(a10['T'] / cands[lead]['T'], 3, claim, 'T(A10 reference) / T(leader), capped', 'ratio', f'G = {g}', 'projection; the A10 is not eligible under [A1]', 'data/verify_tables.md') + ' (reference)'
                answer = 'no eligible A10 baseline under [A1]'
            else:
                r_ = cands[A10]['T'] / cands[lead]['T']
                ratio_txt = num(r_, 3, claim, 'T(A10) / T(leader), capped', 'ratio', f'G = {g}', 'projection at the [D4] upper bound', 'data/verify_tables.md')
                answer = 'yes' if r_ > TIE else 'no (tie by rule)'
            md.append(f"| {g} | {' | '.join(parts)} | {SHORT[lead]} | {', '.join(SHORT[p] for p in tie)} | {SHORT[tie[0]]} | {ratio_txt} | "
                      + word(answer, claim, 'more than 10 % earlier than the A10 ([D4]-capped)', 'verdict', f'G = {g}', 'projection; G_p unmeasured', 'STUDY l. 18-19, 25, 60-63, 87') + ' |')
        tables[f'capped_{camp}'] = md

        # break-even G: the fewest GPUs of p whose T is at or under the reference's T at G_ref (unequal pools; G_p unmeasured)
        ref = 'NVIDIA-GeForce-RTX-4090' if camp == 'chang' else 'NVIDIA-RTX-A6000'
        others = [p for p in measured if p != ref]
        g_top = 256 if camp == 'chang' else DELTA_CAP
        md = [f'| {SHORT[ref]} G | {SHORT[ref]} T, h | ' + ' | '.join(f'{SHORT[p]}: fewest G at or under it' for p in others) + ' |',
              '|' + ' --- |' * (len(others) + 2)]
        for g in grid:
            tr = best(ref, camp, g)['T']
            cells = []
            for p in others:
                need = next((gp for gp in range(1, g_top + 1) if best(p, camp, gp)['T'] <= tr + 1e-9), None)
                claim = f'break-even G {lab}, {SHORT[p]} against {SHORT[ref]} at G = {g}'
                if need is None:
                    floor_t = best(p, camp, 10 ** 6 if camp == 'chang' else DELTA_CAP)['T']
                    cells.append('never' + (f" (floor {num(floor_t, 1, claim, 'T floor at large G', 'hours', 'G large', 'projection', 'data/verify_tables.md')} h)" if camp == 'chang'
                                            else ' within the 10-pod cap'))
                else:
                    tags = []
                    if p == A100 and need > headroom:
                        tags.append('above the a100 quota')
                    if camp == 'delta' and p not in big:
                        tags.append('[A1] override')
                    if best(p, camp, need)['over_static']:
                        tags.append('above the static ceiling')
                    cells.append(num(need, 0, claim, 'fewest GPUs of p at or under the reference T', 'GPUs', f'G_ref = {g}', 'projection; G_p unmeasured',
                                     'data/verify_tables.md') + (f" ({'; '.join(tags)})" if tags else ''))
            md.append(f'| {g} | {fh(tr)} | ' + ' | '.join(cells) + ' |')
        tables[f'breakeven_{camp}'] = md

        # what-if leaders: the a100 quota not binding (both campaigns), Kai overriding [A1] (Delta)
        conds = [('a100 quota not binding (hypothetical)', False, True)]
        if camp == 'delta':
            conds += [('Kai overrides [A1]', True, False), ('Kai overrides [A1] and the a100 quota is not binding', False, False)]
        md = ['| G | condition | leader, T h | tie set | [D5] pick at equal G | T(A10) / T(leader) |', '| --- | --- | --- | --- | --- | --- |']
        for g in grid:
            for cond, qb, a1 in conds:
                lead, cands, tie = leader(camp, g, qb, a1)
                claim = f'what-if {lab}, G = {g}, {cond}'
                a10t = best(A10, camp, g)['T']
                md.append(f"| {g} | {cond} | {SHORT[lead]} {fh(cands[lead]['T'])} | {', '.join(SHORT[p] for p in tie)} | {SHORT[sorted(tie, key=lambda p: card[p])[0]]} | "
                          f"{num(a10t / cands[lead]['T'], 3, claim, 'T(A10) / T(leader)', 'ratio', f'G = {g}', 'projection; hypothetical condition', 'data/verify_tables.md')} |")
        tables[f'whatif_{camp}'] = md

        # T decomposition (both terms, the STUDY decision packet l. 89-90) at G = 1 and at the top of the grid
        g_hi = grid[-1]
        md = ['| product | G | K E/A07 | Q, h | C_p, h (max of the class canaries) | C_p, h (sum reading) | first term Σ W·s/(3600·K·G), h | critical path max H·s/3600, h | T, h | T with the C_p sum, h |',
              '|' + ' --- |' * 10]
        for p in measured:
            for g in (1, g_hi):
                t = results[(camp, p, g)]
                claim = f'T decomposition {lab}, {SHORT[p]}, G = {g}'
                st = 'projection from telemetry; G_p unmeasured [D4]'
                sr = 'data/bench_summary.json; STUDY l. 53-58'
                md.append(f"| {SHORT[p]} | {g} | {kstr(t)} | "
                          f"{num(t['Q'], 2, claim, 'Q (benchmark stand-in, C7)', 'hours', 'one pod per shape', 'snapshot [L3]', sr)} | "
                          f"{num(t['C'], 2, claim, 'C_p, parallel class canaries', 'hours (upper bound)', '110 epochs', st, sr)} | "
                          f"{num(t['C_sum'], 2, claim, 'C_p, sequential class canaries', 'hours (upper bound)', '110 epochs per class', st, sr)} | "
                          f"{num(t['fluid'], 1, claim, 'first term', 'hours', f'G = {g}', st, sr)} | "
                          f"{num(t['cp'], 1, claim, 'critical path', 'hours', 'longest horizon', st, sr)} | {fh(t['T'])} | "
                          f"{num(t['T_csum'], 1, claim, 'T with C_p as the sum reading', 'hours', f'G = {g}', st, sr)} |")
        tables[f'decomp_{camp}'] = md

        # leader flips over G
        flips = {}
        conds_f = [('equal G, now', True, True, False), ('equal G, a100 quota not binding', False, True, False), ('[D4]-capped', True, True, True)]
        if camp == 'delta':
            conds_f += [('equal G, [A1] overridden', True, False, False), ('[D4]-capped, [A1] overridden', True, False, True)]
        for cond, qb, a1, capped in conds_f:
            seq = []
            for g in SCAN[camp]:
                lead, _, tie = leader(camp, g, qb, a1, capped=capped)
                pick = tie[0] if capped else sorted(tie, key=lambda p: card[p])[0]
                if not seq or seq[-1][1] != (lead, pick):
                    seq.append((g, (lead, pick)))
            flips[cond] = seq
        tables[f'flips_{camp}'] = ['| view | leader, and the [D5] pick where it differs, by G (from G = …) |', '| --- | --- |'] + [
            f"| {cond} | " + '; '.join(f'{SHORT[lp[0]]}' + (f' (pick {SHORT[lp[1]]})' if lp[1] != lp[0] else '') + f' from G = {g}' for g, lp in seq) + ' |'
            for cond, seq in flips.items()]
        say('FLIPS', camp, {c: [(g, SHORT[lp[0]], SHORT[lp[1]]) for g, lp in s] for c, s in flips.items()})

        # checks: compute-only leader, the C_p sum reading, LPT (Chang), stress test on the leader
        md = ['| G | view | leader (T with Q + C) | leader by the compute term only | leader with C_p as the sum reading | '
              + ('leader by LPT pack schedule | ' if camp == 'chang' else '') + 'leader T, h | same leader with s × 1.0643, T h | leader after the stress | tie set after the stress |',
              '|' + ' --- |' * (10 if camp == 'chang' else 9)]
        for capped in (False, True):
            for g in grid:
                lead, cands, tie = leader(camp, g, capped=capped)
                lead_c, _, _ = leader(camp, g, key='compute', capped=capped)
                lead_s, _, _ = leader(camp, g, key='T_csum', capped=capped)
                lpt_cell = ''
                if camp == 'chang':
                    lead_l, _, _ = leader(camp, g, key='T_lpt', capped=capped)
                    lpt_cell = f'{SHORT[lead_l]} | '
                lead2, cands2, tie2 = leader(camp, g, scale_for=lead, capped=capped)
                claim = f"stress test {lab}, G = {g} ({'[D4]-capped' if capped else 'equal G'})"
                md.append(f"| {g} | {'[D4]-capped' if capped else 'equal G'} | {SHORT[lead]} | {SHORT[lead_c]} | {SHORT[lead_s]} | {lpt_cell}{fh(cands[lead]['T'])} | "
                          f"{num(cands2[lead]['T'], 1, claim, 'leader T with its s inflated by 6.43 % (the largest B6 deviation)', 'hours', f'G = {g}', 'stress test, not an interval', 'data/verify_tables.md')} | "
                          f"{SHORT[lead2]} | {', '.join(SHORT[p] for p in tie2)} |")
        tables[f'checks_{camp}'] = md

    # LPT check, Chang (the REPORT schedules the real packs; equal-horizon runs, partial packs at the full-K s: an upper bound)
    md = ['| G | product (K E/A07) | packs E + A07 | formula compute term, h | LPT makespan of the packs, h | LPT / formula |', '| --- | --- | --- | --- | --- | --- |']
    for g in GRID['chang']:
        lead, cands, _ = leader('chang', g)
        for p in dict.fromkeys([lead, A10]):
            t = results[('chang', p, g)]
            cl = CAMPAIGNS['chang']['classes']
            packs = {c: math.ceil(cl[c]['runs'] / t['K'][c]) for c in t['K']}
            mk = lpt_T(t, 'chang', g)
            claim = f'LPT check Chang, {SHORT[p]}, G = {g}'
            md.append(f"| {g} | {SHORT[p]} ({kstr(t)}) | "
                      f"{num(packs['E'], 0, claim, 'E packs, ceil(runs / K)', 'packs', 'design arithmetic', 'derived from STUDY l. 20-21 and K', 'STUDY.md l. 20-21', seeds='not applicable')} + "
                      f"{num(packs['A07'], 0, claim, 'A07 packs, ceil(runs / K)', 'packs', 'design arithmetic', 'derived from STUDY l. 20-21 and K', 'STUDY.md l. 20-21', seeds='not applicable')} | "
                      f"{num(t['compute'], 1, claim, 'formula compute term max(first, critical path)', 'hours', f'G = {g}', 'projection from telemetry', 'data/verify_tables.md')} | "
                      f"{num(mk, 1, claim, 'LPT makespan of equal-horizon packs', 'hours', f'G = {g}', 'check, not the pre-registered T', 'data/verify_tables.md')} | "
                      f"{num(mk / t['compute'], 3, claim, 'LPT / formula compute term', 'ratio', f'G = {g}', 'check, not the pre-registered T', 'data/verify_tables.md')} |")
    tables['lpt_chang'] = md
    worst = (0, None)
    for p in measured:
        for g in SCAN['chang']:
            t = best(p, 'chang', g)
            r_ = lpt_T(t, 'chang', g) / t['compute']
            if r_ > worst[0]:
                worst = (r_, (p, g, kstr(t)))
    tables['lpt_worst'] = [f"Largest LPT / formula over the five measured products and G = 1-32 (Chang, chosen K): "
                           f"{num(worst[0], 3, 'LPT check Chang', 'largest LPT / formula', 'ratio', 'G = 1-32', 'check, not the pre-registered T', 'data/verify_tables.md')} "
                           f"({SHORT[worst[1][0]]} at G = {worst[1][1]}, K {worst[1][2]})."]

    # per-unit Chang (the matching units E and A07 of [D5]), equal G
    for cls in ('E', 'A07'):
        md = ['| product | ' + ' | '.join(f'G = {g}' for g in GRID['chang']) + ' |', '|' + ' --- |' * (len(GRID['chang']) + 1)]
        for p in measured:
            cells = []
            for g in GRID['chang']:
                t = best(p, 'chang', g, [cls])
                claim = f'T unit Chang {cls}, {SHORT[p]}, G = {g}'
                cells.append(num(t['T'], 1, claim, f'T for the Chang {cls} unit alone', 'hours', f'G = {g} GPUs (assumed)', 'projection; G_p unmeasured [D4]',
                                 'data/bench_summary.json; STUDY l. 53-58') + f" (K {t['K'][cls]})" + ('*' if p == A100 and g > headroom else '')
                             + ('‡' if t['over_static'] else ''))
            md.append(f'| {SHORT[p]} | ' + ' | '.join(cells) + ' |')
        md.append('')
        md.append('| G | leader (a100 quota applied) | tie set | T(A10) / T(leader) |')
        md.append('| --- | --- | --- | --- |')
        for g in GRID['chang']:
            lead, cands, tie = leader('chang', g, classes=[cls])
            md.append(f"| {g} | {SHORT[lead]} | {', '.join(SHORT[p] for p in tie)} | "
                      f"{num(cands[A10]['T'] / cands[lead]['T'], 3, f'T unit Chang {cls}, G = {g}', 'T(A10) / T(leader), unit', 'ratio', f'G = {g}', 'projection', 'data/verify_tables.md')} |")
        tables[f'unit_chang_{cls}'] = md

    # pre-registered constants and campaign sizes quoted in the prose (inputs, not results)
    md = ['| constant | value | source |', '| --- | --- | --- |']
    cq = 'pre-registered constant or campaign size (an input, quoted, not a result)'
    for label, value, d, source in [
            ('stop_after: epochs per arm', 21, 0, 'STUDY l. 47-49; PREFLIGHT arm table'),
            ('[D1] window: one-based epochs per arm (2-21)', 20, 0, 'STUDY l. 47'),
            ('[D1] untraced epochs per arm in the window', 18, 0, 'STUDY l. 47-49 (traced 10 and 20)'),
            ('[D1] traced epochs per arm in the window', 2, 0, 'STUDY l. 48'),
            ('sampler interval, s', 60, 0, 'PREFLIGHT Alignment 5; pod log BENCH_PLAN_OK sample_s'),
            ('rule 1: pod peak limit, % of memory.total', 90, 0, 'STUDY l. 65'),
            ('rule 5: steady cores per arm limit', 2.1, 1, 'STUDY l. 72'),
            ('rule 3 / [D6]: window after the apply, h', 6, 0, 'STUDY l. 67'),
            ('[D5] tie factor', 1.10, 2, 'STUDY l. 87'),
            ('policy item 4 utilization floor, %', 40, 0, 'STUDY l. 94; PREFLIGHT B5'),
            ('C_p canary length, epochs', 110, 0, 'STUDY l. 55-56'),
            ('[D4] campaign (b) pod cap', 10, 0, 'STUDY l. 60-61'),
            ('[A1] minimum card memory for campaign (b) A07 packs, GB', 45, 0, 'STUDY l. 118'),
            ('campaign (a) E run-epochs W', 224000, 0, 'STUDY l. 20-21'),
            ('campaign (a) A07 run-epochs W', 112000, 0, 'STUDY l. 21'),
            ('campaign (a) horizon H, epochs', 7000, 0, 'STUDY l. 20-21'),
            ('campaign (a) R run-epochs (untimed, [A2])', 8000, 0, 'STUDY l. 21'),
            ('campaign (a) R batch size', 256, 0, 'STUDY l. 21'),
            ('campaign (b) E run-epochs W (base class)', 32000, 0, 'STUDY l. 23'),
            ('campaign (b) A07 run-epochs W (base class)', 114000, 0, 'STUDY l. 23'),
            ('campaign (b) E longest horizon H, epochs', 1000, 0, 'STUDY l. 23'),
            ('campaign (b) A07 longest horizon H, epochs', 2000, 0, 'STUDY l. 23'),
            ('fingerprint gate constant', 11559681, 0, 'STUDY l. 66'),
            ('seconds per hour in R = K x 3600 / s', 3600, 0, 'STUDY l. 50'),
            ('host-RSS gate: process epochs the in-code gate needs', 105, 0, 'STUDY l. 51, 69-70'),
            ('alternative reading of "10 % earlier": T(p) < 0.90 x T(A10)', 0.90, 2, 'STUDY l. 19 (this VERIFY: the reading not used)')]:
        md.append(f"| {label} | {num(value, d, 'pre-registered inputs', label, 'constant', 'not applicable', cq, 'campaigns/2026-09-29-gpu-benchmark/' + source, seeds='not applicable')} | {source} |")
    tables['constants'] = md

    # formula verification (STUDY l. 57-58, the Check; not quotable) and the limiting cases
    s_chk, k_chk = 138.9, 5
    r_chk = k_chk * 3600 / s_chk
    first = 224000 * s_chk / (3600 * k_chk * 7) / 24
    cp_chk = 7000 * s_chk / 3600 / 24
    claim = 'formula verification (STUDY Check, not quotable)'
    sq = 'quoted from STUDY.md l. 57-58 (formula illustration, not quotable)'
    fv = [f"STUDY's Check recomputed (s {num(s_chk, 1, claim, 'Check input s', 's per epoch', 'formula', sq, 'STUDY.md l. 57-58', seeds='not applicable')} s "
          f"at K = 5, A10 pilot telemetry, a formula illustration): R = "
          f"{num(r_chk, 1, claim, 'R at s 138.9, K 5', 'run-epochs per GPU-hour', 'formula', 'illustration, not quotable', 'STUDY.md l. 57-58', seeds='not applicable')}"
          f" (STUDY: {num(130, 0, claim, 'R quoted', 'run-epochs per GPU-hour', 'formula', sq, 'STUDY.md l. 58', seeds='not applicable')}), "
          f"Chang E first term at G = 7 = {num(first, 2, claim, 'Chang E first term at G 7', 'days', 'formula', 'illustration, not quotable', 'STUDY.md l. 57-58', seeds='not applicable')} d "
          f"(STUDY: {num(10.3, 1, claim, 'first term quoted', 'days', 'formula', sq, 'STUDY.md l. 58', seeds='not applicable')} d), "
          f"one 7,000-epoch run = {num(cp_chk, 2, claim, 'one 7000-epoch run', 'days', 'formula', 'illustration, not quotable', 'STUDY.md l. 57-58', seeds='not applicable')} d "
          f"(STUDY: {num(11.3, 1, claim, 'one run quoted', 'days', 'formula', sq, 'STUDY.md l. 58', seeds='not applicable')} d)."]
    t_same = best(A10, 'chang', 16)
    big_g = best(A10, 'chang', 10 ** 6)
    fv.append(f"Limiting cases on the A10 Chang row: two identical products give T ratio "
              f"{num(t_same['T'] / t_same['T'], 3, 'formula verification', 'identical products T ratio', 'ratio', 'formula', 'limiting case', 'code/verify_bench.py', seeds='not applicable')}; "
              f"at G → large, T tends to Q + C + max H·s/3600 = "
              f"{num(big_g['T'], 1, 'formula verification', 'A10 Chang T at G 1e6', 'hours', 'formula', 'limiting case', 'code/verify_bench.py', seeds='not applicable')} h "
              f"(critical path {num(big_g['cp'], 1, 'formula verification', 'A10 Chang critical path', 'hours', 'formula', 'limiting case', 'code/verify_bench.py', seeds='not applicable')} h + Q).")
    tables['formula'] = fv

    # counts quoted in the prose
    cl = 'benchmark counts'
    all_exits = [e for x in rec.values() for e in x['exits']]
    md = ['| count | value | source |', '| --- | --- | --- |']
    for label, value, source in [
            ('Jobs applied (two per product, eight products)', len(jobs), src(PLAN)),
            ('Jobs complete, every phase ok', len({r['job_dir'] for r in phase_rows}), 'logs/*/job.json (succeeded 1), pod logs BENCH_DONE'),
            ('Jobs "not practical now" (rule 3, [D6])', len(deleted), 'RUN.md l. 89-91, 114-117; logs/*/scheduler-message-6h.txt'),
            ('phases measured (product x class x K)', len(phase_rows), 'data/bench_summary.json'),
            ('arm-runs, each at 21 epochs with exit 0', sum(1 for e in all_exits if e['outcome'] == 'ok' and e['code'] == 0 and e['epochs'] == STOP), 'pod logs, ARM_EXIT lines'),
            ('arm-runs with CHECKPOINT_VERIFICATION_PASS (rule 6)', sum(1 for x in rec.values() for a in x['arms'].values() if a['verification'] == ['PASS']), 'arm logs'),
            ('arm-runs with a FAIL, an OOM exit or a non-finite loss', sum(1 for x in rec.values() for a in x['arms'].values() if a['verification'] != ['PASS'] or not a['all_finite'])
             + sum(1 for e in all_exits if e['outcome'] != 'ok'), 'arm logs, pod logs'),
            ('pods printing FINGERPRINT 11559681 expected 11559681 (rule 2)', len({r['job_dir'] for r in phase_rows if rec[(r['job_dir'], r['phase'])]['checks']['fingerprint']}), 'pod logs'),
            ('phases excluded under rule 1', sum(1 for r in phase_rows if r['excluded']), 'data/bench_summary.json'),
            ('phases above the rule-5 limit of 2.1 cores per arm', sum(1 for r in phase_rows if r['cpu_cores_per_arm_steady'] > 2.1), 'data/bench_summary.json'),
            ('sampler rows past epoch 1 with an arm thread outside its pinned CPUs', sum(x['sm']['outside'] for x in rec.values()), 'data/gpu-bench/*/samples.csv'),
            ('run-epochs timed', sum(r['completed_run_epochs'] for r in phase_rows), 'arm logs')]:
        md.append(f"| {label} | {num(value, 0, cl, label, 'count', 'whole benchmark', TEL, source, seeds='not applicable')} | {source} |")
    tables['counts'] = md

    # write outputs
    text = []
    for key, lines in tables.items():
        text.append(f'<!-- table {key} -->')
        text.extend(lines)
        text.append('')
    (DATA / 'verify_tables.md').write_text('\n'.join(text) + '\n')
    (CAMP / 'verify.json').write_text(json.dumps(ROWS, indent=1, ensure_ascii=False) + '\n')
    # VERIFY.md = code/verify_template.md with each '<!-- table KEY -->' line replaced by that table, verbatim
    template = CODE / 'verify_template.md'
    if template.exists():
        out = []
        for line in template.read_text().splitlines():
            m = re.fullmatch(r'<!-- table (\S+) -->', line.strip())
            out.extend(tables[m.group(1)] if m else [line])
        (CAMP / 'VERIFY.md').write_text('\n'.join(out) + '\n')
        say('VERIFY.md rendered from', src(template))
    say('ROWS', len(ROWS))
    say('SHA verify_bench.py', sha(Path(__file__)))
    for key, lines in tables.items():
        say(f'\n## {key}')
        for line in lines:
            say(line)


if __name__ == '__main__':
    main()
