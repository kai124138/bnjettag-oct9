"""Run several independent models on one GPU, preserving per-model checkpoints."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
children = []


def stop(signum, frame):
    for child, *_ in children:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    raise SystemExit(128 + signum)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
packs = json.loads((HERE / sys.argv[1]).read_text())
indices = packs[int(os.environ['JOB_COMPLETION_INDEX'])]
rows = json.loads((HERE / 'index.json').read_text())['runs']
stop_after = sys.argv[2] if len(sys.argv) > 2 else None
for index in indices:
    command = [sys.executable, '-u', str(HERE / 'run_study.py'), 'train', '--index', str(index)]
    if stop_after:
        command += ['--stop-after', stop_after]
    name = rows[index]['name']
    log = Path('/data/constituent-study-20260922/fp32/logs')
    log.mkdir(parents=True, exist_ok=True)
    handle = (log / f'{name}-{os.environ.get("HOSTNAME", "pod")}.log').open('a', buffering=1)
    child = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
    children.append((child, name, handle, time.monotonic()))
    print('ARM_STARTED', index, name, 'pid', child.pid, flush=True)
    # Avoid overlapping the largest calibration allocations during startup.
    time.sleep(15)
failed = False
last_gpu = 0
while children:
    for entry in children[:]:
        child, name, handle, started = entry
        if child.poll() is not None:
            failed |= child.returncode != 0
            print('ARM_EXIT', name, child.returncode, flush=True)
            handle.close()
            children.remove(entry)
            continue
        latest = Path('/data/constituent-study-20260922/fp32/runs') / name / 'latest.json'
        age = time.time() - latest.stat().st_mtime if latest.exists() else time.monotonic() - started
        if age > 1800:
            print('ARM_STALLED_NO_CHECKPOINT_30MIN', name, flush=True)
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=120)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
    if time.monotonic() - last_gpu > 60:
        subprocess.run(['nvidia-smi', '--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total',
                        '--format=csv,noheader'], check=False)
        last_gpu = time.monotonic()
    time.sleep(5)
raise SystemExit(1 if failed else 0)
