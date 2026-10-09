#!/usr/bin/env python3
"""Summarise the GPU-product benchmark from its saved logs and samples. Telemetry, never a result.

    python3 bench_summary.py bench --root DIR [--plan ../manifests/bench_plan.json] [--out summary.json]
        DIR/<slug>-<shape>/ as copied from the PVC (/data/chang-n64-20260926/gpu-bench/<slug>-<shape>/, one per Job):
        plan.json, samples.csv, p*/phase_result.json, p*/logs/<name>.log, pod-*.log, and, saved by cluster-ops at
        the end, pod.json (`kubectl get pod -o json`) and job.json (`kubectl get job -o json`). --plan lists every
        Job, so a Job with no data is reported (STUDY [D6] "not practical" for that pod shape, or not run).
    python3 bench_summary.py a10 --pack LABEL=GLOB --pod-log LABEL=FILE [...] [--offset 10m] [--out summary.json]
        The A10 regime-B pilot logs as a labelled MIXED-PACK cross-check (run_study.train, W&B on, several
        architectures per pod). Since STUDY Amendment 1 (A1) the A10 baseline is the A10 harness Jobs; this mode is
        the cross-check only. --offset 10m reads the window 10m+2 .. 10m+21 instead of 2 .. 21 (STUDY falsifier (i));
        the A10 K=3 logs resume at 25, and later attempts replace re-run epochs.
    python3 bench_summary.py probe --job job.json --pods pods.json [--window-min 30] [--pod-logs DIR]
        STUDY [D4]: G_obs = probe pods Running within the window after Job creation, Q_p = their median wait.

Per product x class x K (one benchmark phase), stop_after 21, traces at one-based epochs 1, 10, 20 (read from each
epoch line: `EBOPs=untraced` or a number):
  s [D1]            per arm (9 x median untraced + median traced) / 10 over epochs 2-21; the SLOWEST arm of the
                    phase (STUDY [D1]: a pack ends with it)
  R [D1]            K x 3600 / s, only if all K arms completed stop_after epochs (else None: the others ran at K-1,
                    or the phase was cut short)
  pooled (brief)    the same formula on medians pooled over the K arms, and its K x 3600 / s
  total elapsed per run-epoch, peak GPU memory (pod, per process) against 0.90 x memory.total, GPU utilization
  (all samples; steady window = K arms live, all past epoch 1, none at the last), cgroup CPU cores and cores / K in
  the steady window against the 2 x K pinned CPUs, host RSS peaks, the driver's outcome per arm (non-ok arms listed),
  NaN, checkpoint verification, fingerprint, node and node CPU, cache digests, queue (Job creation -> Running from
  job.json; pod creation -> PodScheduled; pod creation -> Running; Running = Ready, else the container's startedAt).
Exclusion rules (STUDY, pre-registered; 5 and 6 by Amendment 1): 1 OOM (the driver's exit-7 classification only), a
non-finite loss or a peak above 90 % excludes that K for the class; 2 a fingerprint mismatch on any pod of the product
excludes the product; 3 no pod Running 6 h after apply = not practical for that Job shape; 5 a phase whose steady
cgroup cores / K exceed 2.0 x 1.05 = 2.1 is above the CPU budget and kept out of T; 6 a CHECKPOINT_VERIFICATION FAIL
on any arm of the product excludes the product. A phase under 40 % mean GPU utilization is a finding, not an exclusion.
Fixer v2 (PREFLIGHT critical v2): rule 5's thread-mask check reads only sampler rows of arms past epoch 1 (B1); a phase
without phase_result.json runs the pin checks from the arm logs' ARM_CPUS lines, else it keeps no R (C1); an arm
stopped during verify_selected is verify_interrupted, not a FAIL, and only an A10 Job's first complete attempt counts
(B3); the counted A10 s at E K=4 / A07 K=2 is checked one-sided against Delta's pure-pack A10 canary (B6).
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
from pathlib import Path
import re
import statistics
from datetime import datetime, timezone

EPOCH_RE = re.compile(r'^\[epoch (\d+)/(\d+)\] EBOPs=(untraced|\d+)\b.*?\bseconds=([\d.]+)')
TRACE_S_RE = re.compile(r'\bebops_trace_seconds=([\d.]+)')
RSS_RE = re.compile(r'\bhost_rss_mb=(\d+)')
TRAIN_RE = re.compile(r'^\[train\] (\S+) params=(\d+) resume_epoch=(\d+) initial_ebops=(\d+)')
ATTEMPT_RE = re.compile(r'^==== (?:BENCH_)?ARM_ATTEMPT \d+ (\S+)')
ARM_CPUS_RE = re.compile(r'^ARM_CPUS (?:n=(\d+) requested (\S+) seen (\S+) (OK|MISMATCH)|(unavailable|MISMATCH) requested (\S+))')
OOM_RE = re.compile(r'RESOURCE_EXHAUSTED|ResourceExhaustedError|CUDA_ERROR_OUT_OF_MEMORY|out of memory|'
                    r'failed to allocate memory|OOM when allocating', re.IGNORECASE)
SMI_RE = re.compile(r'^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\.\d+, ([^,]+), (\d+) %, (\d+) MiB, (\d+) MiB')
POD_STAMP_RE = re.compile(r'^(?:BENCH_POD|PROBE_POD) .* (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$')
# the A10 pilot arms, classed by parameter count as printed by the build ([train] line)
PARAMS_CLASS = {31735: 'E', 33271: 'E+PE (F)', 19447: 'E1 (one head)', 61951: 'A07', 12788: "C' (A07, old quantizers)"}
# anchor cache (training-batch PREFLIGHT.md l. 518, cache job DATA_INFO): held fixed across products (STUDY)
ANCHOR_CACHE = {'x_train': '420ac79dcece207aca849f6ca56e6426586023c9e02f38e5d3ac596fa74d79bc',
                'x_val': '7b56c1b25bc0d9231767f891ec52455ecb7c5656735fcf9d404104fd2c264d31',
                'y_train': 'a5269398e2c6e5f1fc0db98e1a99a8befea619bf0c55531293d02a286c0dd378',
                'y_val': '63049d9bdcfdc83af97c58bc6579e1def1ec2d9e7a6c30007793badd75217709'}
CPU_PER_ARM = 2
CPU_BUDGET_PER_ARM = CPU_PER_ARM * 1.05   # STUDY rule 5 (Amendment 1, A2): above 2.1 cores per arm = above budget
UTIL_FLOOR_PCT = 40.0                      # policy item 4; STUDY Amendment 1 (B5): below it is a finding only
BASELINE = 'NVIDIA-A10'                    # STUDY Amendment 1 (A1): the headline comparator, in this benchmark
# STUDY Amendment 1, critical v2 B6 (fixer v2): [D1] s of the slowest arm of Delta's pure-pack A10 canaries per class x K
# (code/evidence/a10_delta_canary_crosscheck.json; 114.455 prints as 114.45 at two decimals). The counted A10 benchmark
# s more than 10 % above it flags the baseline, and the headline comparison goes to Kai with both readings.
DELTA_CANARY_S = {('E', 4): 114.455, ('A07', 2): 90.73}
BASELINE_CHECK_FACTOR = 1.10


def median(values):
    return statistics.median(values) if values else None


def steady(untraced_median, traced_median):
    """(9 u + t) / 10: nine untraced epochs and one traced epoch per trace cycle of ten."""
    if untraced_median is None or traced_median is None:
        return None
    return (9 * untraced_median + traced_median) / 10


def parse_ts(text):
    text = text.rstrip('Z').replace('/', '-')
    return datetime.fromisoformat(text.replace(' ', 'T')).replace(tzinfo=timezone.utc).timestamp()


def cpu_list(text):
    """'0-3,8' -> {0, 1, 2, 3, 8}."""
    out = set()
    for part in str(text or '').split(','):
        part = part.strip()
        if part:
            lo, _, hi = part.partition('-')
            out.update(range(int(lo), int(hi or lo) + 1))
    return out


def parse_arm_log(path):
    """Attempt blocks of one arm log: header time, [train] line, epoch rows, flags."""
    blocks, block = [], None
    for line in Path(path).read_text(errors='replace').splitlines():
        m = ATTEMPT_RE.match(line)
        if m or block is None:
            block = {'attempt_utc': m.group(1) if m else None, 'name': None, 'params': None, 'resume_epoch': None,
                     'epochs': {}, 'oom': [], 'arm_oom': False, 'diverged': False, 'verification': 'none',
                     'verification_error': None, 'cache': None, 'arm_cpus': None, 'lines': 0}
            blocks.append(block)
            if m:
                continue
        block['lines'] += 1
        m = TRAIN_RE.match(line)
        if m:
            block.update(name=m.group(1), params=int(m.group(2)), resume_epoch=int(m.group(3)))
            continue
        m = EPOCH_RE.match(line)
        if m:
            t, r = TRACE_S_RE.search(line), RSS_RE.search(line)
            block['epochs'][int(m.group(1))] = {'traced': m.group(3) != 'untraced', 'seconds': float(m.group(4)),
                                                'trace_seconds': float(t.group(1)) if t else None,
                                                'host_rss_mb': int(r.group(1)) if r else None,
                                                'loss_finite': 'loss=nan' not in line and 'loss=inf' not in line}
            continue
        if line.startswith('BENCH_CACHE '):
            block['cache'] = json.loads(line.split(' ', 1)[1])
        m = ARM_CPUS_RE.match(line)
        if m:
            block['arm_cpus'] = ({'n': int(m.group(1)), 'requested': m.group(2), 'seen': m.group(3), 'status': m.group(4)}
                                 if m.group(1) else {'n': None, 'requested': m.group(6), 'seen': None, 'status': m.group(5)})
        if line.startswith('ARM_OOM '):   # the arm's own catch of ResourceExhaustedError (bench_driver, exit 7)
            block['arm_oom'] = True
        if OOM_RE.search(line):
            block['oom'].append(line.strip()[:200])
        if 'ARM_DIVERGED' in line:
            block['diverged'] = True
        for tag in ('PASS', 'SKIPPED', 'FAIL'):
            if f'CHECKPOINT_VERIFICATION_{tag}' in line:
                block['verification'] = tag
                if tag == 'FAIL':   # the assertion text carries the replay deltas (np.testing.assert_allclose)
                    block['verification_error'] = line.split(' ', 1)[1][:2000] if ' ' in line else line
    return [b for b in blocks if b['lines'] or b['attempt_utc']]


def fresh_block(path):
    """The attempt that started at epoch 0 (the A10 K=3 logs also hold a resume from epoch 25)."""
    blocks = [b for b in parse_arm_log(path) if b['resume_epoch'] == 0]
    return blocks[0] if blocks else None


def merged_block(path):
    """Every attempt of one arm, a later attempt replacing the epochs it re-ran (offset windows)."""
    blocks = [b for b in parse_arm_log(path) if b['resume_epoch'] is not None]
    if not blocks:
        return None
    out = {**blocks[0], 'epochs': {}, 'source': {}, 'oom': [], 'diverged': False}
    for i, b in enumerate(blocks):
        for e, r in b['epochs'].items():
            out['epochs'][e] = r
            out['source'][e] = i
        out['oom'] += b['oom']
        out['diverged'] = out['diverged'] or b['diverged']
        out['verification'] = b['verification'] if b['verification'] != 'none' else out['verification']
    return out


def arm_metrics(block, stop, offset=0):
    lo, hi = offset + 1, offset + stop
    ep = {e: r for e, r in block['epochs'].items() if lo <= e <= hi}
    traced = sorted(e for e, r in ep.items() if r['traced'])
    expected = ([1] if offset == 0 else []) + [offset + 10, offset + 20]
    untraced = [r['seconds'] for e, r in ep.items() if e >= offset + 2 and not r['traced']]
    traced_s = [r['seconds'] for e, r in ep.items() if e in (offset + 10, offset + 20) and r['traced']]
    sources = {block.get('source', {}).get(e, 0) for e in ep}
    return {'name': block['name'], 'params': block['params'], 'epochs_done': len(ep), 'window': [lo, hi],
            'steady_s': steady(median(untraced), median(traced_s)),
            'traced_epochs': traced, 'traced_as_expected': traced == [e for e in expected if e <= hi][:len(traced)],
            'untraced_s': untraced, 'traced_s': traced_s,
            'epoch1_s': ep[lo]['seconds'] if lo in ep else None,
            'trace_s': [r['trace_seconds'] for e, r in ep.items() if e in (offset + 10, offset + 20) and r['traced']
                        and r['trace_seconds'] is not None],
            'host_rss_peak_mb': max((r['host_rss_mb'] for r in ep.values() if r['host_rss_mb'] is not None), default=None),
            # An OOM-looking line alone is not an OOM: TF's allocator can log a failed growth attempt and retry smaller
            # while the arm carries on. In bench mode the sole source is the driver's exit-7 classification
            # (phase_result.json, else the arm's own ARM_OOM line); this text heuristic serves the A10 pilot logs only.
            'oom_lines_seen': len(block['oom']),
            'oom': bool(block['oom']) and len(ep) < stop,
            'arm_oom': block.get('arm_oom', False),
            'nan': block['diverged'] or not all(r['loss_finite'] for r in ep.values()),
            'verification': block['verification'], 'verification_error': block.get('verification_error'),
            'cache': block.get('cache'), 'arm_cpus': block.get('arm_cpus'),
            'window_crosses_resume': len(sources) > 1}


def pool(arms, k, stop):
    """One phase (or one class of a mixed pack). R needs all K arms to have completed `stop` epochs in the window:
    the plan's stop_after, not the longest arm (PREFLIGHT critical v1 B2: a phase stopped early for every arm, by the
    deadline or a SIGTERM, has no R)."""
    untraced = [s for a in arms for s in a['untraced_s']]
    traced = [s for a in arms for s in a['traced_s']]
    u, t = median(untraced), median(traced)
    s = steady(u, t)
    per_arm = [median(a['untraced_s']) for a in arms if a['untraced_s']]
    slowest = max((a['steady_s'] for a in arms if a['steady_s'] is not None), default=None)
    completed = sum(a['epochs_done'] == stop for a in arms)
    # K x 3600 / s holds only if all K arms ran every epoch: after an arm dies the others run at K-1
    whole = s is not None and len(arms) == k and completed == k
    return {'k': k, 'stop_after': stop, 'arms_parsed': len(arms), 'arms_completed': completed,
            'all_arms_completed': whole,
            # STUDY [D1]: s per arm, the slowest arm of the phase (a pack ends with it); R = K x 3600 / s
            's_d1': slowest, 'R_d1': k * 3600 / slowest if whole and slowest else None,
            'steady_s_slowest_arm': slowest,
            # the brief's pooled form, beside it
            'untraced_median_s': u, 'traced_median_s': t, 'n_untraced': len(untraced), 'n_traced': len(traced),
            'steady_s_per_epoch': s, 'run_epochs_per_gpu_hour': k * 3600 / s if whole else None,
            'gpu_hours_per_1000_run_epochs': 1000 * s / (k * 3600) if whole else None,
            'per_arm_untraced_median_range_s': [min(per_arm), max(per_arm)] if per_arm else None,
            'epoch1_median_s': median([a['epoch1_s'] for a in arms if a['epoch1_s'] is not None]),
            'trace_seconds_median': median([x for a in arms for x in a['trace_s']]),
            'completed_run_epochs': sum(a['epochs_done'] for a in arms),
            'host_rss_peak_mb': max((a['host_rss_peak_mb'] for a in arms if a['host_rss_peak_mb'] is not None), default=None),
            'oom': any(a['oom'] for a in arms), 'oom_lines_seen': sum(a['oom_lines_seen'] for a in arms),
            'nan': any(a['nan'] for a in arms),
            'traced_epochs_as_expected': all(a['traced_as_expected'] for a in arms),
            'window_crosses_resume': any(a['window_crosses_resume'] for a in arms),
            'verification': {v: sum(a['verification'] == v for a in arms) for v in ('PASS', 'SKIPPED', 'FAIL', 'none')}}


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def samples_for(rows, phase, k, stop, pinned=None):
    """Sampler rows of one phase. `pinned`: the phase's pinned CPU list from phase_result.json ('0-3')."""
    gpu = [r for r in rows if r['phase'] == phase and r['kind'] == 'gpu']
    proc = [r for r in rows if r['phase'] == phase and r['kind'] == 'proc' and r['arm'] != 'other']
    util = [f(r['gpu_util_pct']) for r in gpu if f(r['gpu_util_pct']) is not None]
    steady_rows = [r for r in gpu if f(r['live_arms']) == k and f(r['epochs_done_min']) is not None
                   and f(r['epochs_done_min']) >= 1 and f(r['epochs_done_max']) < stop]
    s_util = [f(r['gpu_util_pct']) for r in steady_rows if f(r['gpu_util_pct']) is not None]
    used = [f(r['gpu_mem_used_mib']) for r in gpu if f(r['gpu_mem_used_mib']) is not None]
    total = next((f(r['gpu_mem_total_mib']) for r in gpu if f(r['gpu_mem_total_mib'])), None)
    cores, s_cores = [], []
    for a, b in zip(gpu, gpu[1:]):
        ua, ub, ta, tb = f(a['cgroup_cpu_usage_usec']), f(b['cgroup_cpu_usage_usec']), f(a['unix_s']), f(b['unix_s'])
        if None not in (ua, ub, ta, tb) and tb > ta:
            c = (ub - ua) / ((tb - ta) * 1e6)
            cores.append(c)
            if a in steady_rows and b in steady_rows:
                s_cores.append(c)
    mem = [f(r['cgroup_mem_current_bytes']) for r in gpu if f(r['cgroup_mem_current_bytes']) is not None]
    per_proc = [f(r['proc_gpu_mem_mib']) for r in proc if f(r['proc_gpu_mem_mib']) is not None]
    rss = [f(r['proc_rss_mib']) for r in proc if f(r['proc_rss_mib']) is not None]
    # every thread of every arm stayed on the pinned CPUs (sampler: union of the threads' Cpus_allowed_list). Only rows
    # of arms past epoch 1 count: a row sampled between Popen and the arm's own pin shows the whole allowed set, a
    # start-up race and not a pin failure (PREFLIGHT critical v2 B1)
    thread_cpus = [cpu_list(r.get('proc_cpus_allowed')) for r in proc
                   if r.get('proc_cpus_allowed') and (f(r.get('proc_epochs_done')) or 0) >= 1]
    union = set().union(*thread_cpus) if thread_cpus else set()
    steady_cores = statistics.fmean(s_cores) if s_cores else None
    return {'n_samples': len(gpu), 'n_steady_samples': len(steady_rows),
            'gpu_util_mean_all': statistics.fmean(util) if util else None,
            'gpu_util_mean_steady': statistics.fmean(s_util) if s_util else None,
            'gpu_util_median_steady': median(s_util),
            'gpu_mem_peak_mib': max(used) if used else None, 'gpu_mem_total_mib': total,
            'gpu_mem_peak_fraction': (max(used) / total) if used and total else None,
            'gpu_mem_over_90pct': (max(used) / total > 0.90) if used and total else None,
            'proc_gpu_mem_peak_mib': max(per_proc) if per_proc else None,
            'cpu_cores_mean_all': statistics.fmean(cores) if cores else None,
            'cpu_cores_mean_steady': steady_cores,
            # STUDY Amendment 1 (A2): cores / K against 2 per arm; the pinned set is 2K CPUs, the pod request 2 x K_max
            'cpu_cores_per_arm_steady': steady_cores / k if steady_cores is not None else None,
            'cpu_pinned_cores_expected': CPU_PER_ARM * k,
            'thread_cpus_union': ','.join(str(c) for c in sorted(union)) if union else None,
            'thread_mask_rows': len(thread_cpus),
            'threads_within_pinned': (union <= cpu_list(pinned)) if union and pinned else None,
            'cgroup_mem_peak_mib': max(mem) / 2 ** 20 if mem else None,
            'proc_rss_peak_mib': max(rss) if rss else None}


def pin_from_arm_logs(arms, k):
    """PREFLIGHT critical v2 C1: without phase_result.json (a deletion or the deadline during the last arm's
    verify_selected) the rule-5 pin checks run from the arm logs. The pin counts as applied and confirmed only if all K
    arms printed `ARM_CPUS ... OK` with one common list of 2K CPUs; that list is returned, else None (the phase keeps
    no R)."""
    pins = [a.get('arm_cpus') or {} for a in arms]
    lists = {p.get('requested') for p in pins}
    if len(arms) != k or any(p.get('status') != 'OK' for p in pins) or len(lists) != 1:
        return None
    pinned = lists.pop()
    return pinned if len(cpu_list(pinned)) == CPU_PER_ARM * k else None


def pod_log_order(path):
    """Chronological order of a Job directory's pod logs: the BENCH_POD / PROBE_POD stamp, else the file mtime
    (PREFLIGHT critical v1 C6: not the file name)."""
    try:
        for line in Path(path).read_text(errors='replace').splitlines():
            m = POD_STAMP_RE.match(line)
            if m:
                return parse_ts(m.group(1)), str(path)
    except OSError:
        pass
    return os.path.getmtime(path), str(path)


def running_time(pod):
    """Ready=True, else the earliest containerStatuses[].state.{running,terminated}.startedAt: a finished pod carries
    Ready False (reason PodCompleted) and keeps its container's startedAt (PREFLIGHT critical v1 B1)."""
    conds = pod.get('status', {}).get('conditions', [])
    ready = next((c['lastTransitionTime'] for c in conds if c['type'] == 'Ready' and c['status'] == 'True'), None)
    if ready:
        return parse_ts(ready), 'Ready'
    started = [s.get('state', {}).get(k, {}).get('startedAt') for s in pod.get('status', {}).get('containerStatuses', [])
               for k in ('running', 'terminated')]
    started = sorted(parse_ts(x) for x in started if x)
    return (started[0], 'containerStatuses.startedAt') if started else (None, None)


def pod_facts(pod_logs, pod_json):
    facts = {'node': None, 'gpu_info': None, 'fingerprint': None, 'fingerprint_ok': None, 'fingerprints': [],
             'pip_freeze_sha256': None, 'queue_seconds': None, 'pod_created_to_running_seconds': None,
             'job_created_to_running_seconds': None, 'running_source': None, 'driver': None,
             'cpu_model': None, 'cpu_counts': None, 'lscpu': [], 'host_mem': None, 'pod_cpus': None, 'pod_logs': [],
             'bench_product': None}
    for path in sorted(pod_logs, key=pod_log_order):
        log = {'log': Path(path).name, 'fingerprint': None, 'fingerprint_ok': None}
        for line in Path(path).read_text(errors='replace').splitlines():
            if line.startswith('HOSTNAME_NODE ') and not facts['node']:
                facts['node'] = line.split(None, 1)[1].strip()
            elif line.startswith('BENCH_POD ') and ' product ' in line and not facts['bench_product']:
                facts['bench_product'] = line.split(' product ', 1)[1].split()[0]
            elif line.startswith('GPU_INFO '):
                facts['gpu_info'] = line.split(None, 1)[1].strip()
            elif line.startswith('FINGERPRINT ') and ' expected ' in line:
                log['fingerprint'] = line.strip()
            elif line.startswith('FINGERPRINT_OK'):
                log['fingerprint_ok'] = True
            elif line.startswith('GPU_FINGERPRINT_MISMATCH') or line.startswith('FINGERPRINT_GATE_FAIL'):
                log['fingerprint_ok'] = False
            elif line.startswith('PIP_FREEZE_SHA256 '):
                facts['pip_freeze_sha256'] = line.split()[1]
            elif line.startswith('Driver Version') and not facts['driver']:
                facts['driver'] = line.split(':', 1)[1].strip()
            elif line.startswith('CPU_MODEL '):
                facts['cpu_model'] = line.split(None, 1)[1].strip()
            elif line.startswith('CPU_COUNTS '):
                facts['cpu_counts'] = line.split(None, 1)[1].strip()
            elif line.startswith('LSCPU ') and line.strip() not in facts['lscpu']:
                facts['lscpu'].append(line.strip())
            elif line.startswith('HOST_MEM '):
                facts['host_mem'] = line.split(None, 1)[1].strip()
            elif line.startswith('POD_CPUS '):
                facts['pod_cpus'] = line.split(None, 1)[1].strip()
        facts['pod_logs'].append(log)
    facts['fingerprints'] = [g['fingerprint'] for g in facts['pod_logs'] if g['fingerprint']]
    facts['fingerprint'] = facts['fingerprints'][-1] if facts['fingerprints'] else None
    oks = [g['fingerprint_ok'] for g in facts['pod_logs'] if g['fingerprint_ok'] is not None]
    # rule 2 excludes the product on ANY mismatch, whatever the order of the pods (not the last log's value)
    facts['fingerprint_ok'] = (False if False in oks else True) if oks else None
    if pod_json and Path(pod_json).exists():
        pod = json.loads(Path(pod_json).read_text())
        created = parse_ts(pod['metadata']['creationTimestamp'])
        conds = pod.get('status', {}).get('conditions', [])
        scheduled = next((c['lastTransitionTime'] for c in conds if c['type'] == 'PodScheduled' and c['status'] == 'True'), None)
        t_run, source = running_time(pod)
        facts['queue_seconds'] = parse_ts(scheduled) - created if scheduled else None
        facts['pod_created_to_running_seconds'] = t_run - created if t_run else None
        facts['running_source'] = source
        facts['node'] = facts['node'] or pod.get('spec', {}).get('nodeName')
        job_json = Path(pod_json).with_name('job.json')
        if job_json.exists() and t_run:   # STUDY: queue Q from apply (Job creation) to Running
            facts['job_created_to_running_seconds'] = t_run - parse_ts(
                json.loads(job_json.read_text())['metadata']['creationTimestamp'])
    return facts


def exclusion(row):
    """STUDY rules 1, 2, 5 and 6 for one phase row (rule 3 is a Job without data). Rules 2 and 6 are product-wide:
    summarize_bench copies them onto every row of the product."""
    why = []
    if row.get('fingerprint_ok') is False:
        why.append('rule 2: fingerprint mismatch (product)')
    if row.get('oom'):
        why.append('rule 1: OOM')
    if row.get('nan'):
        why.append('rule 1: non-finite loss')
    if row.get('gpu_mem_over_90pct'):
        why.append('rule 1: pod peak above 90 % of memory.total')
    per_arm = row.get('cpu_cores_per_arm_steady')
    if per_arm is not None and per_arm > CPU_BUDGET_PER_ARM:
        why.append(f'rule 5: above the CPU budget (steady cores / K {per_arm:.2f} > {CPU_BUDGET_PER_ARM:.2f}); out of T')
    if row.get('cpu_pin') not in (None, 'pinned'):
        why.append(f"rule 5: CPU pin {row.get('cpu_pin')} (not 2 x K CPUs); out of T")
    if row.get('threads_within_pinned') is False:
        why.append('rule 5: an arm thread ran outside the pinned CPUs; out of T')
    if row.get('arm_cpus_unconfirmed'):
        why.append(f"rule 5: {len(row['arm_cpus_unconfirmed'])} arm(s) did not confirm the pin (ARM_CPUS not OK); out of T")
    if (row.get('verification') or {}).get('FAIL'):
        why.append('rule 6: checkpoint verification FAIL (product)')
    return why


def findings(row):
    """Recorded, never an exclusion (STUDY Amendment 1, B5; C2)."""
    out = []
    util = row.get('gpu_util_mean_steady')
    if util is not None and util < UTIL_FLOOR_PCT:
        out.append(f'GPU utilization mean {util:.1f} % < {UTIL_FLOOR_PCT:g} % in the steady window (a finding, not an exclusion)')
    if row.get('cpu_cores_per_arm_steady') is None and row.get('phase') != 'none':
        out.append('CPU budget unverified: no steady sample pair')
    if row.get('verify_interrupted_arms'):
        out.append(f"{len(row['verify_interrupted_arms'])} arm(s) verify_interrupted: stopped during verify_selected "
                   '(STUDY Amendment 1, critical v2 B3: not a rule-6 FAIL)')
    return out


def a10_rules(rows):
    """STUDY Amendment 1, critical v2 B3 and B6 (fixer v2), on the A10 benchmark rows; appends to `excluded` and `findings`.
    B3: an A10 Job runs at most twice (one re-run, into a fresh directory). Its attempts are ordered by the pod's
    BENCH_POD stamp; the first complete attempt (every phase with all K arms at stop_after) counts, and every row of any
    other attempt is listed, never pooled, and kept out of T. A class with no counted A10 phase that has R and no
    exclusion reads "A10 baseline not measured"; the [L2] pilot telemetry is never promoted to the baseline.
    B6 (one-sided): at E K=4 and A07 K=2 a counted A10 [D1] s more than 10 % above the slowest arm of Delta's pure-pack
    A10 canary flags the baseline, and the headline comparison goes to Kai with both readings."""
    a10 = [r for r in rows if r.get('product') == BASELINE and r.get('phase') != 'none']
    jobs = {}
    for r in a10:
        jobs.setdefault(r.get('shape'), {}).setdefault(r['job_dir'], []).append(r)
    for shape, dirs in jobs.items():
        order = sorted(dirs, key=lambda d: (dirs[d][0].get('attempt_started_unix') or float('inf'), d))
        complete = [d for d in order if all(r.get('all_arms_completed') for r in dirs[d])]
        for i, d in enumerate(order, 1):
            for r in dirs[d]:
                r['attempt'] = f'{i} of {len(order)}'
                r['attempt_counted'] = bool(complete) and d == complete[0]
                if not r['attempt_counted']:
                    r['excluded'].append(f'B3: A10 {shape} attempt {i} of {len(order)} is not the first complete attempt '
                                         '(listed, never pooled); out of T')
                if len(order) > 2:
                    r['findings'].append(f'B3: {len(order)} attempts of the A10 {shape} Job; at most one re-run is allowed')
    missing = []
    for (cls, k), delta_s in DELTA_CANARY_S.items():
        limit = BASELINE_CHECK_FACTOR * delta_s
        checked = [r for r in a10 if r['class'] == cls and r['k'] == k and r['attempt_counted'] and r['s_d1'] is not None]
        for r in checked:
            flag = r['s_d1'] > limit
            r['baseline_check'] = {'delta_canary_slowest_arm_s': delta_s, 'limit_s': round(limit, 4),
                                   'a10_s_d1': r['s_d1'], 'ratio': round(r['s_d1'] / delta_s, 4), 'flag': flag}
            if flag:
                r['findings'].append(f"B6: A10 s {r['s_d1']:.2f} is more than 10 % above Delta's pure-pack A10 canary "
                                     f'({delta_s} s, {cls} K={k}): the baseline is flagged, and the headline comparison '
                                     'goes to Kai with both readings')
        if not checked:
            missing.append(f'B6: check not run at {cls} K={k} (no counted A10 phase with s)')
    for cls in ('E', 'A07'):
        if not any(r['class'] == cls and r['attempt_counted'] and r['R_d1'] is not None and not r['excluded'] for r in a10):
            missing.append(f'B3: A10 baseline not measured for class {cls} (no counted A10 phase with R and no '
                           'exclusion); the [L2] telemetry is never promoted to the baseline')
    if missing:
        rows.append({'product': BASELINE, 'slug': 'a10', 'class': 'A10 baseline (STUDY Amendment 1, critical v2 B3 and B6)',
                     'phase': 'none', 'excluded': [], 'findings': missing})
    return rows


def summarize_bench(root, plan_path=None):
    rows_out, seen = [], set()
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        pod_logs = sorted(d.glob('pod-*.log'))
        facts = pod_facts(pod_logs, d / 'pod.json')
        if not (d / 'plan.json').exists():
            if pod_logs or (d / 'pod.json').exists():   # e.g. the fingerprint gate stopped the pod before any phase
                rows_out.append({'product': facts['bench_product'], 'slug': d.name, 'job_dir': d.name, 'class': None,
                                 'phase': 'none', **facts, 'excluded': exclusion(facts) or ['no phase ran (see the pod log)']})
                seen.add(d.name)
            continue
        plan = json.loads((d / 'plan.json').read_text())
        seen.add(plan['slug'])
        stop = plan['stop_after']
        samples = list(csv.DictReader((d / 'samples.csv').open())) if (d / 'samples.csv').exists() else []
        # the attempt's start (its pod log's BENCH_POD stamp): orders an A10 Job's attempts (STUDY Amendment 1, critical v2 B3)
        started = min((pod_log_order(p)[0] for p in pod_logs), default=None)
        for ph in plan['phases']:
            pdir = d / ph['phase']
            result = json.loads((pdir / 'phase_result.json').read_text()) if (pdir / 'phase_result.json').exists() else {}
            arms = []
            for name in ph['names']:
                log = pdir / 'logs' / f'{name}.log'
                block = fresh_block(log) if log.exists() else None
                if block:
                    arms.append(arm_metrics(block, stop))
            if result:
                pinned, cpu_pin, pin_source = result.get('cpus_pinned'), result.get('cpu_pin'), 'phase_result.json'
            else:   # C1 (critical v2): the pin checks run from the arm logs, or the phase keeps no R (below)
                pinned = pin_from_arm_logs(arms, ph['k'])
                cpu_pin, pin_source = ('pinned', 'arm logs (ARM_CPUS; no phase_result.json)') if pinned else (None, None)
            row = {'product': plan['product'], 'slug': plan.get('product_slug', plan['slug']), 'job_dir': d.name,
                   'shape': plan.get('shape'), 'class': ph['class'], 'phase': ph['phase'],
                   **pool(arms, ph['k'], stop), **samples_for(samples, ph['phase'], ph['k'], stop, pinned),
                   **facts, 'phase_wall_s': result.get('wall_seconds'), 'outcomes': result.get('outcomes'),
                   'cpu_pin': cpu_pin, 'cpu_pin_source': pin_source, 'cpus_pinned': pinned,
                   'cpus_pinned_n': result.get('cpus_pinned_n', len(cpu_list(pinned)) if pinned else None),
                   'cpus_allowed_n': result.get('cpus_allowed_n'),
                   'pinned_physical_cores': result.get('pinned_physical_cores'),
                   'pod_cpu_request': plan.get('pod_cpu_request'), 'attempt_started_unix': started}
            done = row['completed_run_epochs']
            row['total_elapsed_s_per_run_epoch'] = row['phase_wall_s'] / done if row['phase_wall_s'] and done else None
            # OOM: the driver's exit-7 classification only (phase_result), else the arm's own ARM_OOM line
            row['oom'] = (bool((result.get('outcomes') or {}).get('oom')) if result
                          else any(a['arm_oom'] for a in arms))
            row['nan'] = row['nan'] or bool((result.get('outcomes') or {}).get('diverged'))
            # every arm that did not end ok, with its outcome (crash, stall, verify_fail, killed, ...)
            row['non_ok_arms'] = [{k2: a.get(k2) for k2 in ('name', 'outcome', 'exit_code', 'signal', 'epochs_done',
                                                             'verification', 'verification_error')}
                                  for a in result.get('arms', []) if a.get('outcome') != 'ok']
            # every arm of a pinned phase must print ARM_CPUS ... OK (the kernel's mask equals the requested 2K CPUs)
            row['arm_cpus_unconfirmed'] = ([a['name'] for a in arms if (a.get('arm_cpus') or {}).get('status') != 'OK']
                                           if cpu_pin == 'pinned' else [])
            # STUDY Amendment 1, critical v2 B3 (fixer v2): an arm with all stop_after epochs, no CHECKPOINT_VERIFICATION line and
            # no ok outcome was stopped during verify_selected: verify_interrupted, never a rule-6 FAIL
            ended = {a.get('name'): a.get('outcome') for a in result.get('arms', [])}
            row['verify_interrupted_arms'] = [a['name'] for a in arms if a['verification'] == 'none'
                                              and a['epochs_done'] == stop and ended.get(a['name']) != 'ok']
            if not result:
                row['non_ok_arms'].append({'name': None, 'outcome': 'no phase_result.json (phase cut short)'})
            withheld = None
            if not result and not pinned and row['R_d1'] is not None:
                withheld = ('C1 (critical v2): no phase_result.json, and the pin checks could not run from the arm '
                            'logs (every arm ARM_CPUS OK with one list of 2K CPUs)')
                row['R_d1'] = row['run_epochs_per_gpu_hour'] = row['gpu_hours_per_1000_run_epochs'] = None
            if row['R_d1'] is None:
                row['no_R_reason'] = ('s undefined (no traced or no untraced epoch in 2-21); ' if row['s_d1'] is None else '') + (
                    f"{row['arms_completed']} of {ph['k']} arms completed {stop} epochs"
                    + (f"; non-ok: {', '.join(str(a['outcome']) for a in row['non_ok_arms'])}" if row['non_ok_arms'] else '')
                    + (f'; {withheld}' if withheld else ''))
            caches = {json.dumps(a['cache'], sort_keys=True) for a in arms if a['cache']}
            row['cache_digest_sets'] = len(caches)
            row['cache_matches_anchor'] = (caches == {json.dumps(ANCHOR_CACHE, sort_keys=True)}) if caches else None
            row['arms'] = [{k2: v for k2, v in a.items() if k2 not in ('untraced_s', 'traced_s', 'trace_s')} for a in arms]
            rows_out.append(row)
    # product-wide rules 2 and 6 across both Job directories of a product (and C3: does a mismatch repeat?)
    by_product = {}
    for r in rows_out:
        by_product.setdefault(r.get('product') or r.get('slug'), []).append(r)
    for product, rows in by_product.items():
        logs = {(r.get('job_dir'), g['log']): g for r in rows for g in r.get('pod_logs', [])}
        mismatched = [g for g in logs.values() if g['fingerprint_ok'] is False]
        values = [g['fingerprint'] for g in mismatched if g['fingerprint']]
        product_fp = {'product_pod_logs': len(logs), 'product_fingerprint_mismatch_pods': len(mismatched),
                      'product_fingerprint_values': sorted({g['fingerprint'] for g in logs.values() if g['fingerprint']}),
                      # same wrong value on every mismatching pod: architecture-deterministic; scattered: a node fault
                      'product_fingerprint_mismatch_repeats': (len(set(values)) == 1) if len(values) >= 2 else None}
        product_fail = any((r.get('verification') or {}).get('FAIL') for r in rows)
        for r in rows:
            r.update(product_fp)
            if mismatched:
                r['fingerprint_ok'] = False
            r['excluded'] = exclusion(r)
            if product_fail and 'rule 6: checkpoint verification FAIL (product)' not in r['excluded']:
                r['excluded'].append('rule 6: checkpoint verification FAIL (product)')
            if r.get('phase') == 'none' and not r['excluded']:
                r['excluded'] = ['no phase ran (see the pod log)']
            r['findings'] = findings(r)
    if plan_path:
        for p in json.loads(Path(plan_path).read_text())['products']:
            for j in p.get('jobs', [{'root_slug': p['slug'], 'shape': None, 'name': None}]):
                if j['root_slug'] not in seen:
                    rows_out.append({'product': p['product'], 'slug': p['slug'], 'job_dir': j['root_slug'],
                                     'shape': j['shape'], 'class': None, 'phase': 'none',
                                     'excluded': [f"rule 3 / [D6]: no data for Job {j['name']} (this pod shape not "
                                                  'Running 6 h after apply, or not run)'], 'findings': []})
    return a10_rules(rows_out)


def smi_samples(pod_log):
    out = []
    for line in Path(pod_log).read_text(errors='replace').splitlines():
        m = SMI_RE.match(line)
        if m:
            out.append({'t': parse_ts(m.group(1)), 'name': m.group(2), 'util': float(m.group(3)),
                        'used': float(m.group(4)), 'total': float(m.group(5))})
    return out


def summarize_a10(packs, pod_logs, stop=21, offset=0):
    rows_out = []
    for label, pattern in packs:
        paths = sorted(glob.glob(pattern))
        blocks = [b for b in ((fresh_block(p) if offset == 0 else merged_block(p)) for p in paths) if b]
        k = len(blocks)
        arms = [arm_metrics(b, stop, offset) for b in blocks]
        logs = [p for lab, p in pod_logs if lab == label]
        facts = pod_facts(logs, None)
        lo = hi = None
        if offset == 0:
            # approximate all-arms-in-epochs-1..21 window: last attempt start + the shortest sum of seconds
            starts = [parse_ts(b['attempt_utc']) for b in blocks if b['attempt_utc']]
            spans = [sum(r['seconds'] for e, r in b['epochs'].items() if 1 <= e <= stop) for b in blocks]
            if starts and spans:
                lo, hi = max(starts), max(starts) + min(spans)
        smi = [s for p in logs for s in smi_samples(p) if lo is not None and lo <= s['t'] <= hi]
        classes = {}
        for a in arms:
            classes.setdefault(PARAMS_CLASS.get(a['params'], f"params {a['params']}"), []).append(a)
        mix = ', '.join(f'{c} x{len(v)}' for c, v in classes.items())
        gpu = {'n_samples': len(smi),
               'gpu_util_mean_all': statistics.fmean(s['util'] for s in smi) if smi else None,
               'gpu_mem_peak_mib': max((s['used'] for s in smi), default=None),
               'gpu_mem_total_mib': smi[0]['total'] if smi else None,
               'gpu_mem_peak_fraction': (max(s['used'] for s in smi) / smi[0]['total']) if smi else None,
               'smi_window_utc': [datetime.fromtimestamp(x, timezone.utc).isoformat() if x else None for x in (lo, hi)]}
        for cls, members in classes.items():
            row = {'product': 'NVIDIA-A10', 'slug': f'a10-pilot-b-{label}', 'class': cls,
                   'phase': f'{label} (mixed pack)' + (f' epochs {offset + 2}-{offset + stop}' if offset else ''),
                   **pool(members, k, stop), 'pack_k': k, 'pack_mix': mix, **gpu, **facts,
                   'note': ('CROSS-CHECK ONLY (STUDY Amendment 1, A1): MIXED PACK, run_study.train with W&B on, run_pack; '
                            'K counts every arm in the pod. Not the benchmark harness; the A10 baseline is the A10 harness Jobs.')}
            # K x 3600 / s assumes K arms of this class; in a mixed pack only this class's own share is defined
            row['class_run_epochs_per_gpu_hour'] = (len(members) * 3600 / row['s_d1'] if row['s_d1'] else None)
            row['R_d1'] = row['run_epochs_per_gpu_hour'] = row['gpu_hours_per_1000_run_epochs'] = None
            row['arms'] = [{k2: v for k2, v in a.items() if k2 not in ('untraced_s', 'traced_s', 'trace_s')} for a in members]
            rows_out.append(row)
        own = [a['steady_s'] for a in arms]
        rows_out.append({'product': 'NVIDIA-A10', 'slug': f'a10-pilot-b-{label}', 'class': 'ALL (mixed pack)',
                         'phase': f'{label} (mixed pack)' + (f' epochs {offset + 2}-{offset + stop}' if offset else ''),
                         'k': k, 'pack_k': k, 'pack_mix': mix,
                         'pack_run_epochs_per_gpu_hour': sum(3600 / s for s in own if s),
                         # a pack total covers only arms with data in the window (an offset window can miss some)
                         'pack_arms_with_window_data': sum(1 for s in own if s),
                         'per_arm_steady_s': {a['name']: a['steady_s'] for a in arms}, **gpu, **facts,
                         'window_crosses_resume': any(a['window_crosses_resume'] for a in arms),
                         'host_rss_peak_mb': max((a['host_rss_peak_mb'] for a in arms if a['host_rss_peak_mb']), default=None),
                         'oom': any(a['oom'] for a in arms), 'oom_lines_seen': sum(a['oom_lines_seen'] for a in arms),
                         'nan': any(a['nan'] for a in arms)})
    return rows_out


def summarize_probe(job_json, pods_json, window_min=30, pod_logs_dir=None):
    """STUDY [D4]: G_obs = probe pods Running within `window_min` of Job creation; Q_p = their median wait."""
    job = json.loads(Path(job_json).read_text())
    created = parse_ts(job['metadata']['creationTimestamp'])
    pods = json.loads(Path(pods_json).read_text())['items']
    rows = []
    for p in pods:
        conds = p.get('status', {}).get('conditions', [])
        scheduled = next((c['lastTransitionTime'] for c in conds if c['type'] == 'PodScheduled' and c['status'] == 'True'), None)
        t_run, _ = running_time(p)
        fp = None
        if pod_logs_dir:
            log = Path(pod_logs_dir) / f"{p['metadata']['name']}.log"
            if log.exists():
                fp = next((line.strip() for line in log.read_text(errors='replace').splitlines()
                           if line.startswith('FINGERPRINT ') and ' expected ' in line), None)
        rows.append({'pod': p['metadata']['name'], 'node': p.get('spec', {}).get('nodeName'),
                     'scheduled_after_s': parse_ts(scheduled) - created if scheduled else None,
                     'running_after_s': t_run - created if t_run else None, 'fingerprint': fp,
                     'phase': p.get('status', {}).get('phase')})
    inside = [r['running_after_s'] for r in rows if r['running_after_s'] is not None and r['running_after_s'] <= 60 * window_min]
    return {'job': job['metadata']['name'], 'job_created_utc': job['metadata']['creationTimestamp'], 'pods': len(rows),
            'window_min': window_min, 'G_obs': len(inside), 'Q_p_median_s': median(inside), 'per_pod': rows}


def table(rows):
    cols = [('product', 'product'), ('shape', 'Job'), ('class', 'class'), ('k', 'K'), ('s_d1', 's [D1]'), ('R_d1', 'R [D1]'),
            ('steady_s_per_epoch', 's pooled'), ('run_epochs_per_gpu_hour', 'R pooled'),
            ('class_run_epochs_per_gpu_hour', 'class R'), ('pack_run_epochs_per_gpu_hour', 'pack R'),
            ('total_elapsed_s_per_run_epoch', 'wall s/ep'), ('gpu_mem_peak_fraction', 'mem frac'),
            ('gpu_util_mean_all', 'util all'), ('gpu_util_mean_steady', 'util st'), ('cpu_cores_mean_steady', 'cores'),
            ('cpu_cores_per_arm_steady', 'cores/K'), ('cpus_pinned', 'pinned'),
            ('host_rss_peak_mb', 'rss MB'), ('oom', 'OOM'), ('nan', 'NaN'), ('job_created_to_running_seconds', 'Q apply'),
            ('queue_seconds', 'Q sched'), ('excluded', 'excluded')]

    def fmt(v):
        if v is None:
            return '-'
        if isinstance(v, list):
            return '; '.join(str(x) for x in v) if v else 'no'
        if isinstance(v, float):
            return f'{v:.3f}' if v < 10 else f'{v:.1f}'
        return str(v)
    lines = ['| ' + ' | '.join(h for _, h in cols) + ' |', '|' + '---|' * len(cols)]
    for r in rows:
        lines.append('| ' + ' | '.join(fmt(r.get(c)) for c, _ in cols) + ' |')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)
    b = sub.add_parser('bench')
    b.add_argument('--root', required=True)
    b.add_argument('--plan', help='manifests/bench_plan.json: report Jobs without data')
    a = sub.add_parser('a10')
    a.add_argument('--pack', action='append', default=[], help='LABEL=GLOB of per-arm logs')
    a.add_argument('--pod-log', action='append', default=[], help='LABEL=FILE')
    a.add_argument('--offset', type=int, default=0, help='a multiple of 10: window offset+2 .. offset+21')
    pr = sub.add_parser('probe')
    pr.add_argument('--job', required=True)
    pr.add_argument('--pods', required=True)
    pr.add_argument('--window-min', type=float, default=30)
    pr.add_argument('--pod-logs')
    for s in (a, b, pr):
        s.add_argument('--out', type=Path)
    args = ap.parse_args()
    if args.mode == 'probe':
        result = summarize_probe(args.job, args.pods, args.window_min, args.pod_logs)
        if args.out:
            args.out.write_text(json.dumps(result, indent=1) + '\n')
        print(f"PROBE {result['job']}: G_obs {result['G_obs']} of {result['pods']} pods Running within "
              f"{result['window_min']:g} min; Q_p median {result['Q_p_median_s']} s")
        return
    if args.mode == 'bench':
        rows = summarize_bench(args.root, args.plan)
    else:
        if args.offset % 10:
            raise SystemExit('--offset must be a multiple of 10 (the trace cadence)')
        rows = summarize_a10([tuple(x.split('=', 1)) for x in args.pack], [tuple(x.split('=', 1)) for x in args.pod_log],
                             offset=args.offset)
    if args.out:
        args.out.write_text(json.dumps(rows, indent=1, default=str) + '\n')
    print(table(rows))
    for r in rows:
        print(f"# {r.get('product')} {r.get('shape') or ''} {r.get('class')} {r.get('phase')}: node {r.get('node')} "
              f"cpu {r.get('cpu_model')} fingerprint {r.get('fingerprint')} verification {r.get('verification')} "
              f"traced_as_expected {r.get('traced_epochs_as_expected')} n_untraced {r.get('n_untraced')} "
              f"n_traced {r.get('n_traced')} samples {r.get('n_samples')} cache_matches_anchor {r.get('cache_matches_anchor')} "
              f"crosses_resume {r.get('window_crosses_resume')} non_ok {r.get('non_ok_arms')} findings {r.get('findings')}"
              + (f" no_R: {r['no_R_reason']}" if r.get('no_R_reason') else '')
              + (f" attempt {r['attempt']} counted {r.get('attempt_counted')}" if r.get('attempt') else '')
              + (f" mix [{r['pack_mix']}]" if r.get('pack_mix') else ''))


if __name__ == '__main__':
    main()
