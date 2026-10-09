#!/usr/bin/env python3
"""GPU-product throughput benchmark harness (campaigns/2026-09-29-gpu-benchmark). Telemetry only:
nothing this script prints is a result.

    python -u bench_driver.py arm --name NAME --run-root DIR [--stop-after 21]
    python -u bench_driver.py pod --bench-root DIR --plan-json JSON

The frozen chang0926 bundle (42abed4b) is imported from the extracted tree on PYTHONPATH; this file
is shipped in its own ConfigMap and never patches that tree.

arm   Trains ONE config of the bundle's campaign index (BNJ_CAMPAIGN_DIR/index.json + configs/, read by
      name, sha256-checked against the index row) the way run_study.train does (run_study.py:94-150),
      with one difference: ablation.run_training(..., remote=False, ...), so W&B is never imported or
      initialised (ablation.py:746-756 is the only W&B init and is guarded by `remote`; every later
      W&B use is guarded by `wandb_run`). Mirrored from run_study.train: TF32 disabled and asserted,
      a GPU asserted, run_engram.validate_cfg, the run.lock flock, BNHGQ2_CODE_SHA256 =
      run_study.manifest(), source_manifest.json, cost_contract.json and the static-infeasible
      refusal, run_engram.load_cache (every array hash, the split check) on
      BNJ_DATA_ROOT/n<n_part>/data, the same model_builder and epoch_observer, exit 3 on
      ablation.Diverged. Not mirrored, on purpose: run_engram.validate_tracking_destination (refuses
      WANDB_MODE != online, run_engram.py:141-142) and wandb_util.run_stage. After the stop it calls
      run_study.verify_selected (reload the selected checkpoint, stored-EBOPs check, validation replay
      within atol 1e-7) and prints its CHECKPOINT_VERIFICATION_PASS / _SKIPPED line; a failed check is
      recorded (CHECKPOINT_VERIFICATION_FAIL, exit 6), not raised.
pod   Runs the phases of one benchmark Job in order, each with K arms launched 15 s apart as separate
      processes (as run_pack.py does) under its own run root <bench-root>/<phase>/runs/<name>, logs in
      <bench-root>/<phase>/logs/<name>.log. No arm is ever retried: an OOM, a crash, a divergence or a
      stall is recorded in <phase>/phase_result.json and the next phase starts once every arm of this
      phase has exited. A sampler thread writes <bench-root>/samples.csv every BENCH_SAMPLE_SECONDS
      (default 60): nvidia-smi name / memory.total / memory.used / utilization.gpu (plus SM clock,
      power, temperature), per-process used_memory, cgroup cpu usage_usec and memory.current, per-arm
      RSS, epochs done and the CPUs its threads may use, each row tagged with the phase and K.

CPU per arm (STUDY Amendment 1, A2): every phase's K arms run on exactly 2 x K CPUs, the first 2K of
the pod's allowed set (os.sched_getaffinity, else /proc/self/status Cpus_allowed_list; on a node with
the kubelet's static CPU manager that set is the pod's own). The pod passes the list with --cpus and
each arm pins itself before it imports anything (threads created later inherit the mask), checks the
mask the kernel reports and prints ARM_CPUS; a mismatch exits 14 before any work. The thread env is
pilot-b's, unchanged. PHASE_START prints the allowed and pinned sets; PHASE_DONE prints the steady
cgroup cores / K from the sampler (STUDY rule 5: above 2.0 x 1.05 = 2.1 is above budget).

Outcomes are decided by exit code first (the arm's own classification): 0 ok, 3 diverged, 7 oom (the
arm caught tf.errors.ResourceExhaustedError; OOM-looking log text alone is telemetry, never an OOM),
6 verify_fail, 11/12/13/14 named, a signal host_oom_kill (SIGKILL while the cgroup's oom_kill counter
rose) or killed, anything else crash; an arm the watchdog stopped is stalled.
Exit codes (arm): 0 done, 3 diverged, 6 checkpoint verification failed, 7 GPU out of memory,
11 run directory not empty, 12 wandb imported, 13 manifest sha mismatch (pod runs only),
14 CPU pinning not applied as requested.
Exit codes (pod): 0 all phases ran (whatever the arms did), 2 bad plan, 11 bench root not empty.

Test flags (CPU gate and unit tests only; refused inside a Kubernetes pod): --test-cpu skips the GPU
assert only (TF32 is still disabled and asserted) and lets an arm run where the platform cannot pin
(macOS); --test-rows T,V slices the arrays AFTER run_engram.load_cache (the loader requires the full
620,000-row split, run_engram.py:216-219); --test-inject-oom PHASE:NAME makes that arm raise
tf.errors.ResourceExhaustedError before training; --test-allowed-cpus LIST replaces the pod's allowed
CPU set (plumbing test on a platform without sched_getaffinity); --test-arm-stub makes every arm pin,
print ARM_CPUS and exit 0 without importing the bundle (the Linux pinning test).
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import traceback

# Import the bundle from PYTHONPATH, never this script's directory (fingerprint_check.py does the same).
HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != HERE]

EXPECTED_MANIFEST_SHA = os.environ.get(
    'BENCH_EXPECT_MANIFEST_SHA', '041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42')
EXIT_DIVERGED = 3          # run_study.EXIT_DIVERGED
EXIT_VERIFY_FAIL = 6
EXIT_OOM = 7
EXIT_ROOT_NOT_EMPTY = 11
EXIT_WANDB_IMPORTED = 12
EXIT_MANIFEST = 13
EXIT_CPU_PIN = 14
EXIT_BAD_PLAN = 2
NAMED_EXITS = {EXIT_ROOT_NOT_EMPTY: 'root_not_empty', EXIT_WANDB_IMPORTED: 'wandb_imported',
               EXIT_MANIFEST: 'manifest_mismatch', EXIT_CPU_PIN: 'cpu_pin_failed'}
CPU_PER_ARM = 2            # STUDY: 2 CPU per arm (Chang RUN.md l. 817-819); Amendment 1 enforces it per phase

# Benchmark classes, in the order names are taken (brief 2026-09-29): E = arm A then arm B (same
# architecture and compute; B differs only in train.ebops.pid.target_ebops 250k), A07 = arm C then
# A07-350 (same A07 architecture; A07-350 differs only in target_ebops 350k).
CLASS_NAMES = {
    'E': [f'chang0926-a-n64-s{s}' for s in range(1, 9)] + [f'chang0926-b-n64-s{s}' for s in range(1, 9)],
    'A07': [f'chang0926-c-n64-s{s}' for s in range(1, 9)] + [f'chang0926-a07-350-n64-s{s}' for s in range(1, 9)],
}
# A failed arm whose log matches this is an out-of-memory outcome. The Delta A07 canary died in an
# allocation before its first epoch line ("RESOURCE_EXHAUSTED: failed to allocate memory").
OOM_RE = re.compile(r'RESOURCE_EXHAUSTED|ResourceExhaustedError|CUDA_ERROR_OUT_OF_MEMORY|out of memory|'
                    r'failed to allocate memory|OOM when allocating', re.IGNORECASE)
NAN_RE = re.compile(r'ARM_DIVERGED|Nonfinite')
STAGGER = float(os.environ.get('BENCH_STAGGER_SECONDS', '15'))
POLL = float(os.environ.get('BENCH_POLL_SECONDS', '5'))
# run_pack's 1,800 s would kill a healthy arm at large K: the first heartbeat after launch needs the
# build, calibration, the initial full-split trace, epoch 1 and its trace, all shared K ways.
STALL_SECONDS = float(os.environ.get('BENCH_STALL_SECONDS', '3600'))
SAMPLE_SECONDS = float(os.environ.get('BENCH_SAMPLE_SECONDS', '60'))
GRACE_SECONDS = 120


def utc(ts=None):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ts))


def say(*parts):
    print(*parts, flush=True)


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(tmp, path)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def refuse_test_flags_in_cluster(args):
    test = (args.test_cpu or args.test_rows or args.test_inject_oom or args.test_arm_stub
            or getattr(args, 'test_allowed_cpus', ''))
    if test and os.environ.get('KUBERNETES_SERVICE_HOST'):
        say('BENCH_TEST_FLAGS_REFUSED: test flags are for the local CPU gate, never a pod')
        raise SystemExit(EXIT_BAD_PLAN)


# ------------------------------------------------------------------------------------------ CPU pinning


def parse_cpu_list(text):
    """'0-3,8,10-11' -> [0, 1, 2, 3, 8, 10, 11] (the kernel's Cpus_allowed_list / cpuset format)."""
    cpus = set()
    for part in str(text).strip().split(','):
        part = part.strip()
        if part:
            lo, _, hi = part.partition('-')
            cpus.update(range(int(lo), int(hi or lo) + 1))
    return sorted(cpus)


def format_cpu_list(cpus):
    """[0, 1, 2, 3, 8, 10, 11] -> '0-3,8,10-11'."""
    cpus, out, i = sorted(set(cpus)), [], 0
    while i < len(cpus):
        j = i
        while j + 1 < len(cpus) and cpus[j + 1] == cpus[j] + 1:
            j += 1
        out.append(str(cpus[i]) if i == j else f'{cpus[i]}-{cpus[j]}')
        i = j + 1
    return ','.join(out)


def allowed_cpus(status=Path('/proc/self/status')):
    """The CPUs this process may run on: os.sched_getaffinity(0), else /proc/self/status Cpus_allowed_list.
    On a node with the kubelet's static CPU manager this is the pod's own exclusive set, not 0..N-1.
    None where neither exists (macOS: the CPU gate only)."""
    if hasattr(os, 'sched_getaffinity'):
        return sorted(os.sched_getaffinity(0))
    try:
        for line in Path(status).read_text().splitlines():
            if line.startswith('Cpus_allowed_list:'):
                return parse_cpu_list(line.split(':', 1)[1])
    except OSError:
        pass
    return None


def phase_cpus(allowed, k):
    """STUDY Amendment 1 (A2): the first 2 x K CPUs of the pod's allowed set (all of it if shorter)."""
    return list(allowed[:CPU_PER_ARM * k]) if allowed else None


def physical_cores(cpus, sysfs=Path('/sys/devices/system/cpu')):
    """Distinct (package, core) pairs among `cpus`: 2K CPUs may be 2K cores or K cores with SMT siblings."""
    cores = set()
    for c in cpus or []:
        try:
            cores.add(((sysfs / f'cpu{c}' / 'topology' / 'physical_package_id').read_text().strip(),
                       (sysfs / f'cpu{c}' / 'topology' / 'core_id').read_text().strip()))
        except OSError:
            return None
    return len(cores) if cores else None


def pin_self(cpus, test_cpu=False):
    """Pin this arm to `cpus` before anything is imported; threads created later (TF, OpenBLAS) inherit
    the mask. Prints ARM_CPUS with the mask the kernel reports. Returns True if the arm may proceed."""
    wanted = sorted(cpus)
    if not hasattr(os, 'sched_setaffinity'):
        say('ARM_CPUS unavailable requested', format_cpu_list(wanted),
            '(no sched_setaffinity on this platform; allowed under --test-cpu only)')
        return bool(test_cpu)
    try:
        os.sched_setaffinity(0, wanted)
    except OSError as exc:
        say('ARM_CPUS MISMATCH requested', format_cpu_list(wanted), 'error', repr(exc)[:200])
        return False
    seen = sorted(os.sched_getaffinity(0))
    ok = seen == wanted
    say('ARM_CPUS', f'n={len(seen)}', 'requested', format_cpu_list(wanted), 'seen', format_cpu_list(seen),
        'OK' if ok else 'MISMATCH')
    return ok


def proc_cpus(pid, proc=Path('/proc')):
    """Union of Cpus_allowed_list over every thread of `pid`, and the thread count (None, None off Linux)."""
    try:
        tasks = list((proc / str(pid) / 'task').iterdir())
    except OSError:
        return None, None
    cpus, threads = set(), 0
    for task in tasks:
        try:
            for line in (task / 'status').read_text().splitlines():
                if line.startswith('Cpus_allowed_list:'):
                    cpus.update(parse_cpu_list(line.split(':', 1)[1]))
                    threads += 1
                    break
        except (OSError, ValueError):
            continue
    return (format_cpu_list(cpus) if cpus else None), threads


def cgroup_oom_kills(root):
    """cgroup v2 memory.events oom_kill: the kernel OOM killer's count for this container."""
    def parse(text):
        return int(next(line.split()[1] for line in text.splitlines() if line.startswith('oom_kill ')))
    return read_first([Path(root) / 'memory.events'], parse)


# ------------------------------------------------------------------------------------------ arm


def campaign_row(campaign, name):
    rows = json.loads((campaign / 'index.json').read_text())['runs']
    match = [r for r in rows if r['name'] == name]
    if len(match) != 1:
        raise SystemExit(f'{name}: {len(match)} rows in {campaign}/index.json')
    row = match[0]
    path = campaign / 'configs' / row['file']
    digest = file_sha256(path)
    if digest != row['config_sha256']:
        raise SystemExit(f'{path}: sha256 {digest} != index config_sha256 {row["config_sha256"]}')
    cfg = json.loads(path.read_text())
    assert cfg['name'] == row['name'], (cfg['name'], row['name'])
    return row, cfg


def arm_main(args):
    refuse_test_flags_in_cluster(args)
    # STUDY Amendment 1 (A2): pin before any import, so every thread TF or OpenBLAS creates inherits the mask
    if args.cpus and not pin_self(parse_cpu_list(args.cpus), args.test_cpu):
        return EXIT_CPU_PIN
    if args.test_arm_stub:   # the Linux pinning test: no bundle import, no training
        say('ARM_STUB_DONE', args.name, 'utc', utc())
        return 0
    import run_engram
    import run_study
    tree = Path(run_study.__file__).resolve().parent
    assert Path(run_engram.__file__).resolve().parent == tree, (run_engram.__file__, run_study.__file__)
    ablation, engram = run_engram.runtime()
    assert Path(ablation.__file__).resolve().parent == tree / 'bnhgq2', ablation.__file__
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)            # as run_study.py:98-99
    assert not tf.config.experimental.tensor_float_32_execution_enabled()
    gpus = tf.config.list_physical_devices('GPU')
    if not args.test_cpu:
        assert gpus, 'Training requires GPU'                                   # as run_study.py:100
    say('BENCH_ARM', args.name, 'tree', tree, 'devices', [g.name for g in gpus] or 'CPU-only',
        'tf32_enabled', tf.config.experimental.tensor_float_32_execution_enabled(),
        'test_cpu', bool(args.test_cpu), 'utc', utc())
    campaign = Path(os.environ['BNJ_CAMPAIGN_DIR'])   # the bundle's campaigns/chang0926 (index.json, configs/)
    data_root = Path(os.environ['BNJ_DATA_ROOT'])
    row, cfg = campaign_row(campaign, args.name)
    run_engram.validate_cfg(cfg)                                               # as run_study.py:103
    out = Path(args.run_root) / 'runs' / row['name']
    if out.exists() and any(out.iterdir()):
        # run_training would resume from latest.json or return at once (ablation.py:706, 757)
        say('ARM_ROOT_NOT_EMPTY', out, '(a benchmark arm starts fresh; move the directory aside)')
        return EXIT_ROOT_NOT_EMPTY
    out.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))   # as run_study.py:114
    code = 0
    with (out / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source = run_study.manifest()
        os.environ['BNHGQ2_CODE_SHA256'] = source['sha256']                   # as run_study.py:117-118
        ok = source['sha256'] == EXPECTED_MANIFEST_SHA
        say('ARM_MANIFEST_SHA', source['sha256'], 'expected', EXPECTED_MANIFEST_SHA, 'OK' if ok else 'MISMATCH')
        if not ok and not args.test_cpu:
            return EXIT_MANIFEST
        run_engram.write_json(out / 'source_manifest.json', source)
        limits = run_study.contract(cfg, engram)
        run_engram.write_json(out / 'cost_contract.json', limits)
        if limits['static_infeasible_reasons']:
            raise RuntimeError('Static-infeasible arm must be excluded from GPU packs')
        arrays, info = run_engram.load_cache(data_root / f"n{cfg['arch']['n_part']}" / 'data', cfg)
        # the digests load_cache itself computed (STUDY: the anchor cache is held fixed across products)
        say('BENCH_CACHE', json.dumps(info['engram_array_sha256'], sort_keys=True))
        if args.test_rows:
            n_train, n_val = (int(v) for v in args.test_rows.split(','))
            arrays = (arrays[0][:n_train], arrays[1][:n_train], arrays[2][:n_val], arrays[3][:n_val])
            say('BENCH_TEST_ROWS', n_train, n_val, '(CPU gate only; sliced after run_engram.load_cache)')
        start = time.monotonic()
        try:
            if args.test_inject_oom:
                raise tf.errors.ResourceExhaustedError(
                    None, None, 'RESOURCE_EXHAUSTED: injected by --test-inject-oom (CPU gate only)')
            state = ablation.run_training(cfg, arrays, info, out, remote=False, stop_after=args.stop_after,
                                          model_builder=run_engram.builder_for(info),
                                          epoch_observer=engram.diagnostic_observer())
            if (out / 'COMPLETE.json').exists():                               # as run_study.py:148-149
                (out / 'COMPLETE.json').replace(out / 'TRAINING_COMPLETE.json')
            try:
                run_study.verify_selected(cfg, row, out, state, arrays, info, source, start)
            except AssertionError as exc:
                say('CHECKPOINT_VERIFICATION_FAIL', json.dumps({'run': cfg['name'], 'error': repr(exc)[:2000]}))
                code = EXIT_VERIFY_FAIL
        except ablation.Diverged:
            say('ARM_OUTCOME', args.name, 'diverged')
            return EXIT_DIVERGED
        except tf.errors.ResourceExhaustedError as exc:
            say('ARM_OOM', args.name, str(exc).splitlines()[0][:500] if str(exc) else repr(exc))
            return EXIT_OOM
    imported = 'wandb' in sys.modules
    say('WANDB_IMPORTED', imported)
    if imported:
        return EXIT_WANDB_IMPORTED
    say('ARM_DONE', args.name, 'exit', code, 'wall_seconds', f'{time.monotonic() - start:.1f}', 'utc', utc())
    return code


# ------------------------------------------------------------------------------------------ sampler

CSV_FIELDS = ['utc', 'unix_s', 'phase', 'k', 'kind', 'gpu_name', 'gpu_mem_total_mib', 'gpu_mem_used_mib',
              'gpu_util_pct', 'gpu_sm_clock_mhz', 'gpu_power_w', 'gpu_temp_c', 'cgroup_cpu_usage_usec',
              'cgroup_mem_current_bytes', 'cgroup_mem_max_bytes', 'live_arms', 'epochs_done_min',
              'epochs_done_max', 'pid', 'arm', 'proc_gpu_mem_mib', 'proc_rss_mib', 'proc_epochs_done',
              'proc_cpus_allowed', 'proc_threads']


def steady_cores(rows, k, stop):
    """Mean cgroup CPU cores over consecutive sample pairs that are both steady (K arms live, all past epoch 1,
    none at the last), the window of bench_summary.samples_for. rows: (unix_s, usage_usec, live_arms,
    epochs_done_min, epochs_done_max). Returns (mean cores, number of pairs)."""
    def is_steady(r):
        return r[2] == k and r[3] is not None and r[3] >= 1 and r[4] is not None and r[4] < stop
    cores = [(b[1] - a[1]) / ((b[0] - a[0]) * 1e6) for a, b in zip(rows, rows[1:])
             if is_steady(a) and is_steady(b) and None not in (a[1], b[1]) and b[0] > a[0]]
    return (sum(cores) / len(cores) if cores else None), len(cores)


def run_quiet(cmd, timeout=30):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def query_gpu():
    text = run_quiet(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,clocks.sm,'
                      'power.draw,temperature.gpu', '--format=csv,noheader,nounits'])
    rows = []
    for line in (text or '').strip().splitlines():
        parts = [p.strip() for p in line.split(',')]
        if len(parts) == 7:
            rows.append(dict(zip(['gpu_name', 'gpu_mem_total_mib', 'gpu_mem_used_mib', 'gpu_util_pct',
                                  'gpu_sm_clock_mhz', 'gpu_power_w', 'gpu_temp_c'], parts)))
    return rows


def query_compute_apps():
    text = run_quiet(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'])
    apps = {}
    for line in (text or '').strip().splitlines():
        parts = [p.strip() for p in line.split(',')]
        if len(parts) == 2 and parts[0].isdigit():
            apps[int(parts[0])] = parts[1]
    return apps


def read_first(paths, parse):
    for path in paths:
        try:
            return parse(Path(path).read_text())
        except (OSError, ValueError, IndexError):
            continue
    return None


def cgroup_cpu_usec(root):
    def v2(text):
        return int(next(line.split()[1] for line in text.splitlines() if line.startswith('usage_usec')))
    value = read_first([root / 'cpu.stat'], v2)
    if value is None:   # cgroup v1: nanoseconds
        value = read_first([root / 'cpuacct' / 'cpuacct.usage', root / 'cpu,cpuacct' / 'cpuacct.usage'],
                           lambda t: int(t.strip()) // 1000)
    return value


def cgroup_mem(root):
    current = read_first([root / 'memory.current', root / 'memory' / 'memory.usage_in_bytes'], lambda t: int(t.strip()))
    limit = read_first([root / 'memory.max', root / 'memory' / 'memory.limit_in_bytes'],
                       lambda t: None if t.strip() == 'max' else int(t.strip()))
    return current, limit


def group_rss_mib(proc=Path('/proc')):
    """RSS (MiB) summed per process group, as run_pack.group_rss_mib: each arm is its own session."""
    totals = {}
    try:
        entries = list(proc.iterdir())
    except OSError:
        return totals
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / 'stat').read_text()
            pgid = int(stat[stat.rindex(')') + 2:].split()[2])
            for line in (entry / 'status').read_text().splitlines():
                if line.startswith('VmRSS:'):
                    totals[pgid] = totals.get(pgid, 0) + int(line.split()[1]) / 1024
                    break
        except (OSError, ValueError, IndexError):
            continue
    return totals


def epochs_done(run_dir):
    try:
        with (Path(run_dir) / 'activation_widths.jsonl').open('rb') as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


class Sampler(threading.Thread):
    def __init__(self, path, interval):
        super().__init__(daemon=True)
        self.path, self.interval = Path(path), interval
        self.lock = threading.Lock()
        self.halt = threading.Event()
        self.phase, self.k, self.root, self.entries = 'setup', 0, None, []
        self.cgroup = Path(os.environ.get('BENCH_CGROUP_DIR', '/sys/fs/cgroup'))
        self.count = 0
        self.cpu_rows = {}   # phase -> [(unix_s, usage_usec, live_arms, epochs_done_min, epochs_done_max)]
        new = not self.path.exists()
        self.handle = self.path.open('a', newline='', buffering=1)
        self.writer = csv.DictWriter(self.handle, fieldnames=CSV_FIELDS)
        if new:
            self.writer.writeheader()

    def set_phase(self, phase, k, root, entries):
        with self.lock:
            self.phase, self.k, self.root, self.entries = phase, k, root, entries

    def sample(self):
        with self.lock:
            phase, k, root, entries = self.phase, self.k, self.root, list(self.entries)
        now = time.time()
        base = {'utc': utc(now), 'unix_s': f'{now:.1f}', 'phase': phase, 'k': k}
        live = [e for e in entries if e['child'].poll() is None]
        done = {e['name']: epochs_done(root / 'runs' / e['name']) for e in entries} if root else {}
        live_done = [done[e['name']] for e in live]
        cpu = cgroup_cpu_usec(self.cgroup)
        mem_current, mem_max = cgroup_mem(self.cgroup)
        gpus = query_gpu() or [{}]
        rows = []
        for gpu in gpus:
            rows.append({**base, 'kind': 'gpu', **gpu, 'cgroup_cpu_usage_usec': cpu,
                         'cgroup_mem_current_bytes': mem_current, 'cgroup_mem_max_bytes': mem_max,
                         'live_arms': len(live), 'epochs_done_min': min(live_done) if live_done else '',
                         'epochs_done_max': max(live_done) if live_done else ''})
        with self.lock:
            self.cpu_rows.setdefault(phase, []).append(
                (now, cpu, len(live), min(live_done) if live_done else None, max(live_done) if live_done else None))
        apps = query_compute_apps()
        rss = group_rss_mib()
        pids = set()
        for entry in live:
            pid = entry['child'].pid
            pids.add(pid)
            cpus, threads = proc_cpus(pid)
            rows.append({**base, 'kind': 'proc', 'pid': pid, 'arm': entry['name'],
                         'proc_gpu_mem_mib': apps.get(pid, ''),
                         'proc_rss_mib': f'{rss[pid]:.0f}' if pid in rss else '',
                         'proc_epochs_done': done.get(entry['name'], ''),
                         'proc_cpus_allowed': cpus, 'proc_threads': threads})
        for pid, used in apps.items():
            if pid not in pids:
                rows.append({**base, 'kind': 'proc', 'pid': pid, 'arm': 'other', 'proc_gpu_mem_mib': used})
        for row in rows:
            self.writer.writerow({k: ('' if v is None else v) for k, v in row.items()})
        self.handle.flush()
        self.count += 1

    def run(self):
        while True:
            try:
                self.sample()
            except Exception as exc:   # telemetry must never stop the benchmark
                say('SAMPLER_ERROR', repr(exc)[:300])
            if self.halt.wait(self.interval):
                break

    def stop(self):
        self.halt.set()
        self.join(timeout=self.interval + 60)
        try:
            self.sample()   # one last row after the last phase
        except Exception as exc:
            say('SAMPLER_ERROR', repr(exc)[:300])
        self.handle.close()

    def phase_cores(self, phase, k, stop):
        with self.lock:
            rows = list(self.cpu_rows.get(phase, []))
        return steady_cores(rows, k, stop)


# ------------------------------------------------------------------------------------------ pod

children = []


def terminate(entries):
    """SIGTERM every entry's process group, one shared grace, then SIGKILL (run_pack.terminate)."""
    for entry in entries:
        try:
            os.killpg(entry['child'].pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + GRACE_SECONDS
    for entry in entries:
        try:
            entry['child'].wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            try:
                os.killpg(entry['child'].pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def on_signal(signum, frame):
    say('BENCH_SIGNAL', signum, 'stopping', len(children), 'arm(s)', utc())
    terminate([e for e in children if e['child'].poll() is None])
    raise SystemExit(128 + signum)


def validate_plan(plan, campaign):
    names = {r['name'] for r in json.loads((campaign / 'index.json').read_text())['runs']}
    problems = []
    if not isinstance(plan.get('stop_after'), int) or plan['stop_after'] < 1:
        problems.append('stop_after must be a positive int')
    seen = set()
    for ph in plan.get('phases', []):
        pid, cls, k, arm_names = ph.get('phase'), ph.get('class'), ph.get('k'), ph.get('names', [])
        if not pid or pid in seen or not re.fullmatch(r'p\d+-[A-Za-z0-9]+-k\d+', pid):
            problems.append(f'bad or repeated phase id {pid!r}')
        seen.add(pid)
        if cls not in CLASS_NAMES:
            problems.append(f'{pid}: unknown class {cls!r}')
            continue
        if not isinstance(k, int) or k < 1 or len(arm_names) != k or len(set(arm_names)) != k:
            problems.append(f'{pid}: k={k!r} with {len(arm_names)} names ({len(set(arm_names))} distinct)')
        if arm_names != CLASS_NAMES[cls][:len(arm_names)]:
            problems.append(f'{pid}: names are not the first {len(arm_names)} of class {cls}')
        problems += [f'{pid}: {n} not in the campaign index' for n in arm_names if n not in names]
    if not plan.get('phases'):
        problems.append('no phases')
    return problems


def launch(name, phase, root, stop_after, args, cpus=None):
    log = root / 'logs' / f'{name}.log'
    handle = log.open('a', buffering=1)
    handle.write(f'==== BENCH_ARM_ATTEMPT 0 {utc()} phase {phase}\n')
    command = [sys.executable, '-u', str(Path(__file__).resolve()), 'arm', '--name', name,
               '--run-root', str(root), '--stop-after', str(stop_after)]
    if cpus:
        command += ['--cpus', format_cpu_list(cpus)]   # the arm pins itself before any import
    if args.test_cpu:
        command.append('--test-cpu')
    if args.test_rows:
        command += ['--test-rows', args.test_rows]
    if args.test_inject_oom == f'{phase}:{name}':
        command.append('--test-inject-oom')
    if args.test_arm_stub:
        command.append('--test-arm-stub')
    child = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
    say('ARM_STARTED', phase, name, 'pid', child.pid, 'cpus', format_cpu_list(cpus) if cpus else 'unpinned', utc())
    return {'child': child, 'name': name, 'log': log, 'handle': handle, 'run': root / 'runs' / name,
            'started_wall': time.time(), 'stalled': False}


def heartbeat_age(entry):
    stamps = [entry['started_wall']]
    for path in (entry['run'] / 'activation_widths.jsonl', entry['run'] / 'latest.json', entry['log']):
        try:
            stamps.append(path.stat().st_mtime)
        except OSError:
            pass
    return time.time() - max(stamps)


def signal_name(number):
    try:
        return signal.Signals(number).name
    except ValueError:
        return str(number)


def classify(entry, code, oom_kill_rose=False):
    """The exit code decides (PREFLIGHT critical v1 B2): an OOM is exit 7 only, the arm's own catch of
    tf.errors.ResourceExhaustedError. OOM-looking lines are kept as telemetry (oom_lines) and never turn a
    verify_fail (6) or a crash into an OOM. A signal is host_oom_kill when it is SIGKILL and the cgroup's
    oom_kill counter rose during the phase, else killed."""
    text = entry['log'].read_text(errors='replace') if entry['log'].exists() else ''
    oom_lines = [line for line in text.splitlines() if OOM_RE.search(line)]
    verify = ('PASS' if 'CHECKPOINT_VERIFICATION_PASS' in text else 'SKIPPED'
              if 'CHECKPOINT_VERIFICATION_SKIPPED' in text else 'FAIL'
              if 'CHECKPOINT_VERIFICATION_FAIL' in text else 'none')
    verify_error = next((line.split(' ', 1)[1][:2000] for line in text.splitlines()
                         if line.startswith('CHECKPOINT_VERIFICATION_FAIL ')), None)
    if entry['stalled']:
        outcome = 'stalled'
    elif code == 0:
        outcome = 'ok'
    elif code == EXIT_DIVERGED:
        outcome = 'diverged'
    elif code == EXIT_OOM:
        outcome = 'oom'
    elif code == EXIT_VERIFY_FAIL:
        outcome = 'verify_fail'
    elif code in NAMED_EXITS:
        outcome = NAMED_EXITS[code]
    elif code < 0:
        outcome = 'host_oom_kill' if code == -signal.SIGKILL and oom_kill_rose else 'killed'
    else:
        outcome = 'crash'
    return {'name': entry['name'], 'pid': entry['child'].pid, 'exit_code': code, 'outcome': outcome,
            'signal': signal_name(-code) if code < 0 else None,
            'epochs_done': epochs_done(entry['run']), 'verification': verify, 'verification_error': verify_error,
            'oom_lines': oom_lines[:5], 'nan': bool(NAN_RE.search(text)),
            'started_utc': utc(entry['started_wall']), 'ended_utc': utc(entry.get('ended_wall'))}


def pod_allowed_cpus(args):
    """The pod's allowed CPU set; --test-allowed-cpus replaces it in the plumbing test (refused in a pod)."""
    return parse_cpu_list(args.test_allowed_cpus) if args.test_allowed_cpus else allowed_cpus()


def run_phase(ph, bench_root, stop_after, sampler, args):
    root = bench_root / ph['phase']
    if root.exists() and any(root.iterdir()):
        say('PHASE_ROOT_NOT_EMPTY', root, '(skipped; a benchmark phase starts fresh)')
        return {'phase': ph['phase'], 'skipped': 'root_not_empty'}
    (root / 'logs').mkdir(parents=True, exist_ok=True)
    (root / 'runs').mkdir(parents=True, exist_ok=True)
    # STUDY Amendment 1 (A2): this phase's arms get exactly 2 x K CPUs, the first 2K of the allowed set
    allowed = pod_allowed_cpus(args)
    cpus = phase_cpus(allowed, ph['k'])
    pin = ('unavailable' if cpus is None else 'short' if len(cpus) < CPU_PER_ARM * ph['k'] else 'pinned')
    cpu_record = {'cpu_pin': pin, 'cpus_allowed_n': len(allowed) if allowed else None,
                  'cpus_allowed': format_cpu_list(allowed) if allowed else None,
                  'cpus_pinned_n': len(cpus) if cpus else None, 'cpus_pinned': format_cpu_list(cpus) if cpus else None,
                  'pinned_physical_cores': physical_cores(cpus) if cpus else None}
    oom_kills_start = cgroup_oom_kills(sampler.cgroup)
    entries = []
    sampler.set_phase(ph['phase'], ph['k'], root, entries)
    t0 = time.time()
    say('PHASE_START', ph['phase'], 'class', ph['class'], 'k', ph['k'], 'names', ','.join(ph['names']), utc(t0))
    say('PHASE_CPUS', ph['phase'], 'pin', pin, 'pinned', cpu_record['cpus_pinned'], 'n', cpu_record['cpus_pinned_n'],
        'physical_cores', cpu_record['pinned_physical_cores'], 'allowed_n', cpu_record['cpus_allowed_n'],
        'allowed', cpu_record['cpus_allowed'])
    for i, name in enumerate(ph['names']):
        if i:
            time.sleep(STAGGER)   # run_pack: avoid overlapping the largest calibration allocations
        entry = launch(name, ph['phase'], root, stop_after, args, cpus)
        entries.append(entry)
        children.append(entry)
        sampler.set_phase(ph['phase'], ph['k'], root, entries)
    results = {}
    while len(results) < len(entries):
        for entry in entries:
            if entry['name'] in results:
                continue
            code = entry['child'].poll()
            if code is None and heartbeat_age(entry) > STALL_SECONDS:
                say('ARM_STALLED', ph['phase'], entry['name'], f'{heartbeat_age(entry):.0f}s', 'terminating (not retried)')
                entry['stalled'] = True
                terminate([entry])
                code = entry['child'].poll()
            if code is None:
                continue
            entry['ended_wall'] = time.time()
            entry['handle'].close()
            children.remove(entry)
            kills = cgroup_oom_kills(sampler.cgroup)
            rose = None not in (kills, oom_kills_start) and kills > oom_kills_start
            results[entry['name']] = classify(entry, code, rose)
            r = results[entry['name']]
            say('ARM_EXIT', ph['phase'], entry['name'], code, 'outcome', r['outcome'], 'epochs', r['epochs_done'],
                'verification', r['verification'], utc())
            if r['outcome'] == 'oom':
                say('ARM_OOM_RECORDED', ph['phase'], entry['name'], '(no retry; the phase continues)')
        time.sleep(POLL)
    t1 = time.time()
    sampler.set_phase('idle', 0, None, [])
    arms = [results[e['name']] for e in entries]
    cores, pairs = sampler.phase_cores(ph['phase'], ph['k'], stop_after)
    record = {'phase': ph['phase'], 'class': ph['class'], 'k': ph['k'], 'names': ph['names'],
              'stop_after': stop_after, 'start_utc': utc(t0), 'end_utc': utc(t1), 'wall_seconds': round(t1 - t0, 1),
              **cpu_record, 'steady_cpu_cores': cores, 'steady_cpu_pairs': pairs,
              'steady_cpu_cores_per_arm': cores / ph['k'] if cores is not None else None,
              'cgroup_oom_kill_start': oom_kills_start, 'cgroup_oom_kill_end': cgroup_oom_kills(sampler.cgroup),
              'arms': arms, 'outcomes': {o: sum(a['outcome'] == o for a in arms) for o in sorted({a['outcome'] for a in arms})}}
    write_json(root / 'phase_result.json', record)
    say('PHASE_DONE', ph['phase'], 'wall_seconds', record['wall_seconds'], 'outcomes', json.dumps(record['outcomes']),
        'steady_cores', f'{cores:.3f}' if cores is not None else 'na', 'per_arm',
        f"{record['steady_cpu_cores_per_arm']:.3f}" if cores is not None else 'na', 'pairs', pairs,
        'pinned', record['cpus_pinned'], utc(t1))
    return record


def pod_main(args):
    refuse_test_flags_in_cluster(args)
    plan = json.loads(args.plan_json)
    campaign = Path(os.environ['BNJ_CAMPAIGN_DIR'])
    problems = validate_plan(plan, campaign)
    if problems:
        for p in problems:
            say('BENCH_PLAN_ERROR', p)
        return EXIT_BAD_PLAN
    bench_root = Path(args.bench_root)
    bench_root.mkdir(parents=True, exist_ok=True)
    busy = [p.name for p in bench_root.glob('p[0-9]*') if p.is_dir() and any(p.iterdir())]
    if busy or (bench_root / 'samples.csv').exists():
        say('BENCH_ROOT_NOT_EMPTY', bench_root, busy, '(move it aside, never delete, before a re-run)')
        return EXIT_ROOT_NOT_EMPTY
    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    say('BENCH_PLAN_OK', plan.get('product'), plan.get('slug'), 'stop_after', plan['stop_after'],
        'phases', ' '.join(f"{p['phase']}" for p in plan['phases']), 'driver_sha256', file_sha256(__file__),
        'stall_s', STALL_SECONDS, 'sample_s', SAMPLE_SECONDS, 'stagger_s', STAGGER)
    allowed = pod_allowed_cpus(args)
    say('POD_CPUS allowed_n', len(allowed) if allowed else 'na', 'allowed', format_cpu_list(allowed) if allowed else 'na',
        'pod_cpu_request', plan.get('pod_cpu_request', 'na'),
        '(allowed_n == request: the static CPU manager gave the pod its own CPUs; larger: a shared pool)')
    write_json(bench_root / 'plan.json', plan)
    sampler = Sampler(bench_root / 'samples.csv', SAMPLE_SECONDS)
    sampler.start()
    records = []
    try:
        for ph in plan['phases']:
            records.append(run_phase(ph, bench_root, plan['stop_after'], sampler, args))
    finally:
        sampler.stop()
    write_json(bench_root / 'bench_result.json', {'plan': plan, 'phases': records, 'samples': sampler.count,
                                                  'driver_sha256': file_sha256(__file__), 'end_utc': utc()})
    say('BENCH_DONE', plan.get('slug'), 'phases', len(records), 'samples', sampler.count, utc())
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('arm')
    a.add_argument('--name', required=True)
    a.add_argument('--run-root', required=True)
    a.add_argument('--stop-after', type=int, default=21)
    a.add_argument('--cpus', default='', help='CPU list the arm pins itself to before any import (set by pod mode)')
    a.add_argument('--test-inject-oom', action='store_true')
    p = sub.add_parser('pod')
    p.add_argument('--bench-root', required=True)
    p.add_argument('--plan-json', required=True)
    p.add_argument('--test-inject-oom', default='', help='PHASE:NAME (CPU gate only)')
    p.add_argument('--test-allowed-cpus', default='', help='replaces the allowed CPU set (plumbing test only)')
    for s in (a, p):
        s.add_argument('--test-cpu', action='store_true')
        s.add_argument('--test-rows', default='')
        s.add_argument('--test-arm-stub', action='store_true', help='arms pin, print ARM_CPUS, exit 0 (pinning test)')
    args = ap.parse_args(argv)
    try:
        return arm_main(args) if args.mode == 'arm' else pod_main(args)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
