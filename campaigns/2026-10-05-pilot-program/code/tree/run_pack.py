"""Run several independent models on one GPU, preserving per-model checkpoints.

[A12] failed-arm isolation (2026-09-27; incident: cluster-inventory.md, 2026-09-26):
- an arm with DIVERGED.json or VERIFIED_COMPLETE.json is skipped at start;
- a child exit 3 is a recorded divergence: the arm stops, the others keep running, and the
  pod does not fail because of it;
- any other non-zero exit (crash, stall kill) tails the child's log into this pod's stdout
  and relaunches THAT arm only, from its own checkpoint, up to BNJ_ARM_RETRIES times;
- the pod exits 1 only if an arm still fails after its retries, and only after every other
  arm has finished.
Stall incident 2026-09-28 (review/INCIDENT_stall_20260928.md; the pod's memory cgroup filled and
four arms stalled in one sweep):
- each attempt's heartbeat clock starts at its own launch: age = now - max(latest.json and
  activation_widths.jsonl mtimes, the attempt's wall-clock start), so a relaunched arm no
  longer inherits the stale files of the attempt it replaces;
- a pod-wide stall (at least BNJ_POD_STALL_FRACTION, default 0.5, of the live arms and at least
  two of them past BNJ_STALL_SECONDS in the same sweep) is logged as POD_STALL; those arms are
  stopped together and NOT charged to their per-arm retry budget. They are relaunched under a
  separate budget (BNJ_POD_STALL_RETRIES, default 2) and only while the cgroup has at least that
  arm's last RSS free (POD_RELAUNCH_WAIT otherwise);
- every poll prints POD_MEM: cgroup memory.current / memory.max / free (MiB), memory.pressure
  full avg10, and each live arm's RSS (sum over its process group), from /sys/fs/cgroup and /proc
  (absent files print "na").
Exit 5 from an arm is a memory-gate failure (ablation RSS gate): not retried, counted as failed.
Roots: BNJ_RUN_ROOT (runs/, logs/), default the 2026-09-22 screen root; BNJ_CAMPAIGN_DIR
(index.json, packs), default this directory.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('BNJ_RUN_ROOT', '/data/constituent-study-20260922/fp32'))
CAMPAIGN = Path(os.environ.get('BNJ_CAMPAIGN_DIR', str(HERE)))
RETRIES = int(os.environ.get('BNJ_ARM_RETRIES', '2'))
STALL_SECONDS = int(os.environ.get('BNJ_STALL_SECONDS', '1800'))
TAIL_LINES = int(os.environ.get('BNJ_TAIL_LINES', '80'))
STAGGER = float(os.environ.get('BNJ_STAGGER_SECONDS', '15'))
RETRY_DELAY = float(os.environ.get('BNJ_RETRY_DELAY_SECONDS', '30'))
POD_STALL_FRACTION = float(os.environ.get('BNJ_POD_STALL_FRACTION', '0.5'))
POD_STALL_RETRIES = int(os.environ.get('BNJ_POD_STALL_RETRIES', '2'))
CGROUP = Path(os.environ.get('BNJ_CGROUP_DIR', '/sys/fs/cgroup'))
PROC = Path(os.environ.get('BNJ_PROC_DIR', '/proc'))
EXIT_DIVERGED = 3
EXIT_MEMORY_GATE = 5
children = []


def stop(signum, frame):
    for entry in children:
        if entry['child'].poll() is None:
            os.killpg(entry['child'].pid, signal.SIGTERM)
    raise SystemExit(128 + signum)


def tail(path, lines=TAIL_LINES):
    try:
        text = Path(path).read_text(errors='replace').splitlines()[-lines:]
    except OSError as error:
        text = [f'<log unreadable: {error}>']
    for line in text:
        print('ARM_LOG', line, flush=True)


def launch(index, name, stop_after, attempt):
    command = [sys.executable, '-u', str(HERE / 'run_study.py'), 'train', '--index', str(index)]
    if stop_after:
        command += ['--stop-after', stop_after]
    log = ROOT / 'logs'
    log.mkdir(parents=True, exist_ok=True)
    path = log / f'{name}-{os.environ.get("HOSTNAME", "pod")}.log'
    handle = path.open('a', buffering=1)
    handle.write(f'==== ARM_ATTEMPT {attempt} {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\n')
    child = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
    print('ARM_STARTED', index, name, 'pid', child.pid, 'attempt', attempt, flush=True)
    return {'child': child, 'index': index, 'name': name, 'handle': handle, 'log': path,
            'started': time.monotonic(), 'started_wall': time.time(), 'attempt': attempt,
            'pod_stalls': 0, 'rss_mib': None}


def heartbeat_age(entry):
    """Seconds since this attempt last showed progress. The attempt's own launch time is a
    floor, so a relaunch never inherits the previous attempt's stale file mtimes."""
    run = ROOT / 'runs' / entry['name']
    stamps = [p.stat().st_mtime for p in (run / 'latest.json', run / 'activation_widths.jsonl') if p.exists()]
    return time.time() - max(stamps + [entry['started_wall']])


def read_int(path):
    try:
        text = path.read_text().strip()
    except OSError:
        return None
    return None if text == 'max' else int(text)


def cgroup_memory():
    """(current MiB, max MiB, free MiB, pressure 'full avg10'); None where unreadable."""
    current, limit = read_int(CGROUP / 'memory.current'), read_int(CGROUP / 'memory.max')
    full = None
    try:
        for line in (CGROUP / 'memory.pressure').read_text().splitlines():
            if line.startswith('full'):
                full = float(line.split()[1].split('=')[1])
    except (OSError, IndexError, ValueError):
        pass
    mib = (lambda v: None if v is None else v / 2 ** 20)
    free = None if current is None or limit is None else (limit - current) / 2 ** 20
    return mib(current), mib(limit), free, full


def group_rss_mib():
    """RSS (MiB) summed per process group: each arm is its own session/group (start_new_session)."""
    totals = {}
    try:
        entries = list(PROC.iterdir())
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


def fmt(value):
    return 'na' if value is None else f'{value:.0f}' if isinstance(value, float) and value > 100 else f'{value}'


def log_memory(live):
    current, limit, free, full = cgroup_memory()
    rss = group_rss_mib()
    parts = []
    for entry in live:
        value = rss.get(entry['child'].pid)
        if value is not None:
            entry['rss_mib'] = value
        parts.append(f"{entry['name']}={fmt(value)}")
    print('POD_MEM', time.strftime('%H:%M:%SZ', time.gmtime()), 'current_mib', fmt(current), 'max_mib', fmt(limit),
          'free_mib', fmt(free), 'pressure_full_avg10', fmt(full), 'rss_mib', ' '.join(parts), flush=True)
    return free


def terminate(entries):
    """SIGTERM every entry's group at once, then one shared 120 s grace, then SIGKILL."""
    for entry in entries:
        try:
            os.killpg(entry['child'].pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 120
    for entry in entries:
        try:
            entry['child'].wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            try:
                os.killpg(entry['child'].pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    packs = json.loads((CAMPAIGN / sys.argv[1]).read_text())
    indices = packs[int(os.environ['JOB_COMPLETION_INDEX'])]
    rows = json.loads((CAMPAIGN / 'index.json').read_text())['runs']
    stop_after = sys.argv[2] if len(sys.argv) > 2 else None
    for index in indices:
        name = rows[index]['name']
        run = ROOT / 'runs' / name
        marker = next((m for m in ('DIVERGED.json', 'VERIFIED_COMPLETE.json') if (run / m).exists()), None)
        if marker:
            print('ARM_SKIPPED', index, name, marker, flush=True)
            continue
        children.append(launch(index, name, stop_after, 0))
        # Avoid overlapping the largest calibration allocations during startup.
        time.sleep(STAGGER)
    failed, diverged = [], []
    pending = []      # pod-stall relaunches waiting for free cgroup memory
    last_gpu = 0
    while children or pending:
        free = log_memory(children)
        live = [e for e in children if e['child'].poll() is None]
        stalled = [e for e in live if heartbeat_age(e) > STALL_SECONDS]
        if len(stalled) >= 2 and len(stalled) >= POD_STALL_FRACTION * len(live):
            print('POD_STALL', len(stalled), 'of', len(live), 'live arms:',
                  ' '.join(f"{e['name']}={int(heartbeat_age(e))}s" for e in stalled),
                  'free_mib', fmt(free), flush=True)
            for entry in stalled:
                entry['pod_stall'] = True
            terminate(stalled)
        elif stalled:
            for entry in stalled:
                print('ARM_STALLED_NO_PROGRESS', entry['name'], int(heartbeat_age(entry)), 's', flush=True)
            terminate(stalled)
        for entry in children[:]:
            child, name = entry['child'], entry['name']
            code = child.poll()
            if code is None:
                continue
            entry['handle'].close()
            children.remove(entry)
            print('ARM_EXIT', name, code, 'attempt', entry['attempt'], flush=True)
            if code == 0:
                continue
            if code == EXIT_DIVERGED:
                diverged.append(name)
                tail(entry['log'], 20)
                continue
            tail(entry['log'])
            if code == EXIT_MEMORY_GATE:
                print('ARM_MEMORY_GATE_FAILED', name, flush=True)
                failed.append(name)
                continue
            if entry.get('pod_stall'):
                if entry['pod_stalls'] < POD_STALL_RETRIES:
                    print('POD_STALL_RELAUNCH_QUEUED', name, 'pod_stalls', entry['pod_stalls'] + 1,
                          'attempt', entry['attempt'], '(not charged)', flush=True)
                    pending.append(entry)
                else:
                    print('ARM_FAILED_AFTER_POD_STALLS', name, flush=True)
                    failed.append(name)
                continue
            if entry['attempt'] < RETRIES:
                time.sleep(RETRY_DELAY)
                children.append(launch(entry['index'], name, stop_after, entry['attempt'] + 1))
            else:
                print('ARM_FAILED_AFTER_RETRIES', name, flush=True)
                failed.append(name)
        for entry in pending[:]:
            need = entry['rss_mib']
            _, _, free_now, _ = cgroup_memory()
            if free_now is not None and need is not None and free_now < need:
                print('POD_RELAUNCH_WAIT', entry['name'], 'free_mib', fmt(free_now), 'need_mib', fmt(need), flush=True)
                continue
            pending.remove(entry)
            time.sleep(RETRY_DELAY)
            new = launch(entry['index'], entry['name'], stop_after, entry['attempt'])
            new['pod_stalls'] = entry['pod_stalls'] + 1
            children.append(new)
        if time.monotonic() - last_gpu > 60:
            try:
                subprocess.run(['nvidia-smi', '--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total',
                                '--format=csv,noheader'], check=False)
            except FileNotFoundError:
                pass
            last_gpu = time.monotonic()
        time.sleep(float(os.environ.get('BNJ_POLL_SECONDS', '5')))
    print('PACK_DONE', 'diverged', diverged, 'failed', failed, flush=True)
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
