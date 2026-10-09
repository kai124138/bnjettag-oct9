"""[A12] pack runner isolation with fake arms (no TF): a divergence (exit 3) and a crash do
not stop the other arms; the crash is retried alone with its log tailed; markers skip."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

FAKE = r'''
import sys, os, json
from pathlib import Path
idx = int(sys.argv[sys.argv.index('--index') + 1])
root = Path(os.environ['BNJ_RUN_ROOT'])
name = json.loads((Path(__file__).parent / 'index.json').read_text())['runs'][idx]['name']
run = root / 'runs' / name; run.mkdir(parents=True, exist_ok=True)
count = run / 'attempts'; n = int(count.read_text()) if count.exists() else 0; count.write_text(str(n + 1))
print('child', name, 'attempt', n, flush=True)
if name == 'ok': sys.exit(0)
if name == 'div': (run / 'DIVERGED.json').write_text('{}'); sys.exit(3)
if name == 'flaky': print('Traceback: boom', flush=True); sys.exit(0 if n >= 1 else 1)
if name == 'dead': print('Traceback: always', flush=True); sys.exit(1)
if name == 'memgate': print('RSS_GATE_FAIL', flush=True); sys.exit(5)
if name.startswith('stale'):
    import time; time.sleep(1.5); sys.exit(0)
if name.startswith('hang'):
    import time
    if n == 0: time.sleep(60)
    sys.exit(0)
'''


def setup(tmp, names, **extra):
    shutil.copy(HERE / 'run_pack.py', tmp / 'run_pack.py')
    (tmp / 'run_study.py').write_text(FAKE)
    (tmp / 'index.json').write_text(json.dumps({'runs': [{'name': n} for n in names]}))
    (tmp / 'packs.json').write_text(json.dumps([list(range(len(names)))]))
    # BNJ_CAMPAIGN_DIR: the fixture dir, never an inherited campaign (CPU-gate regression
    # 2026-10-05, campaigns/2026-10-02-chang-option-c/REGRESSION_TICKET.md)
    env = dict(os.environ, JOB_COMPLETION_INDEX='0', BNJ_RUN_ROOT=str(tmp / 'root'), BNJ_CAMPAIGN_DIR=str(tmp),
               BNJ_STAGGER_SECONDS='0', BNJ_RETRY_DELAY_SECONDS='0', BNJ_POLL_SECONDS='0.2',
               BNJ_ARM_RETRIES='2', BNJ_CGROUP_DIR=str(tmp / 'cgroup'), BNJ_PROC_DIR=str(tmp / 'proc'))
    env.update(extra)
    return env


def run(tmp, env):
    return subprocess.run([sys.executable, str(tmp / 'run_pack.py'), 'packs.json'], env=env, cwd=tmp,
                          capture_output=True, text=True, timeout=120)


def test_isolation_and_retry(tmp_path):
    env = setup(tmp_path, ['ok', 'div', 'flaky'])
    r = run(tmp_path, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'ARM_EXIT div 3' in r.stdout and 'ARM_EXIT ok 0' in r.stdout
    assert 'ARM_LOG Traceback: boom' in r.stdout            # crashed child's log tailed
    assert 'ARM_STARTED 2 flaky' in r.stdout and 'attempt 1' in r.stdout
    assert (tmp_path / 'root' / 'runs' / 'flaky' / 'attempts').read_text() == '2'
    assert (tmp_path / 'root' / 'runs' / 'ok' / 'attempts').read_text() == '1'
    # second pod start: the diverged arm is skipped, never replayed
    r2 = run(tmp_path, env)
    assert 'ARM_SKIPPED 1 div DIVERGED.json' in r2.stdout
    assert (tmp_path / 'root' / 'runs' / 'div' / 'attempts').read_text() == '1'


def test_unrecorded_failure_fails_pod_after_others(tmp_path):
    env = setup(tmp_path, ['dead', 'ok'])
    r = run(tmp_path, env)
    assert r.returncode == 1
    assert 'ARM_FAILED_AFTER_RETRIES dead' in r.stdout and 'ARM_EXIT ok 0' in r.stdout
    assert (tmp_path / 'root' / 'runs' / 'dead' / 'attempts').read_text() == '3'


def test_relaunch_starts_a_fresh_heartbeat_clock(tmp_path):
    """Incident 2026-09-28: a new attempt must not inherit a previous attempt's stale files."""
    env = setup(tmp_path, ['stale'], BNJ_STALL_SECONDS='3')
    run_dir = tmp_path / 'root' / 'runs' / 'stale'
    run_dir.mkdir(parents=True)
    for f in ('latest.json', 'activation_widths.jsonl'):
        (run_dir / f).write_text('{}')
        os.utime(run_dir / f, (1, 1))            # decades old
    r = run(tmp_path, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'ARM_STALLED_NO_PROGRESS' not in r.stdout and 'POD_STALL' not in r.stdout
    assert 'ARM_EXIT stale 0 attempt 0' in r.stdout


def test_pod_wide_stall_is_not_charged_to_retry_budgets(tmp_path):
    """Two of two live arms stall in one sweep: POD_STALL, both relaunched with the same attempt
    number and no per-arm retry spent (BNJ_ARM_RETRIES=0 would otherwise fail both)."""
    env = setup(tmp_path, ['hang-a', 'hang-b'], BNJ_STALL_SECONDS='2', BNJ_ARM_RETRIES='0')
    r = run(tmp_path, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'POD_STALL 2 of 2 live arms' in r.stdout
    assert 'ARM_STALLED_NO_PROGRESS' not in r.stdout
    assert r.stdout.count('POD_STALL_RELAUNCH_QUEUED') == 2 and '(not charged)' in r.stdout
    assert 'ARM_FAILED' not in r.stdout
    for n in ('hang-a', 'hang-b'):
        assert (tmp_path / 'root' / 'runs' / n / 'attempts').read_text() == '2'
        assert r.stdout.count(f'ARM_EXIT {n} 0 attempt 0') == 1


def test_single_arm_stall_is_charged(tmp_path):
    """One stalled arm among live ones is an arm problem: charged, as before."""
    env = setup(tmp_path, ['hang-a', 'stale-b', 'stale-c'], BNJ_STALL_SECONDS='2', BNJ_ARM_RETRIES='1')
    r = run(tmp_path, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'ARM_STALLED_NO_PROGRESS hang-a' in r.stdout and 'POD_STALL ' not in r.stdout
    assert 'ARM_STARTED 0 hang-a pid' in r.stdout and 'attempt 1' in r.stdout


def test_memory_gate_exit_is_not_retried(tmp_path):
    env = setup(tmp_path, ['memgate', 'ok'])
    r = run(tmp_path, env)
    assert r.returncode == 1
    assert 'ARM_MEMORY_GATE_FAILED memgate' in r.stdout
    assert (tmp_path / 'root' / 'runs' / 'memgate' / 'attempts').read_text() == '1'


def test_pod_mem_line_reads_cgroup_and_process_groups(tmp_path, monkeypatch):
    """POD_MEM: cgroup v2 files and per-process-group VmRSS (fake /sys/fs/cgroup and /proc)."""
    import importlib.util
    cg, proc = tmp_path / 'cgroup', tmp_path / 'proc'
    cg.mkdir()
    (cg / 'memory.current').write_text(str(30 * 2 ** 30) + '\n')
    (cg / 'memory.max').write_text(str(36 * 2 ** 30) + '\n')
    (cg / 'memory.pressure').write_text('some avg10=1.00 avg60=0.50 avg300=0.10 total=1\n'
                                        'full avg10=53.24 avg60=10.00 avg300=1.00 total=2\n')
    for pid, pgid, kb in ((101, 101, 2048000), (102, 101, 1024), (201, 201, 4096000)):
        (proc / str(pid)).mkdir(parents=True)
        (proc / str(pid) / 'stat').write_text(f'{pid} (python (x)) S 1 {pgid} {pgid} 0 -1\n')
        (proc / str(pid) / 'status').write_text(f'Name:\tpython\nVmRSS:\t{kb} kB\n')
    monkeypatch.setenv('BNJ_CGROUP_DIR', str(cg))
    monkeypatch.setenv('BNJ_PROC_DIR', str(proc))
    spec = importlib.util.spec_from_file_location('run_pack_under_test', HERE / 'run_pack.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    current, limit, free, full = mod.cgroup_memory()
    assert (current, limit, free, full) == (30 * 1024, 36 * 1024, 6 * 1024, 53.24)
    rss = mod.group_rss_mib()
    assert rss == {101: (2048000 + 1024) / 1024, 201: 4096000 / 1024}
