"""Run every N8 and N64 confirmation to completion on one shared GPU."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

CONFIGS = Path("/configs")
ROOT = Path("/data/confirmation-20260923/architecture")
CHUNK_EPOCHS = int(os.environ.get("CHUNK_EPOCHS", "20"))
STALL_SECONDS = int(os.environ.get("STALL_SECONDS", "7200"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "3"))
children = []


def stop(signum, frame):
    for entry in children:
        child = entry[0]
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    raise SystemExit(128 + signum)


def completed_epochs(output: Path) -> int:
    if not (output / "latest.json").exists():
        return 0
    generation = json.loads((output / "latest.json").read_text())["checkpoint"]
    state = json.loads((output / "checkpoints" / generation / "state.json").read_text())
    return int(state["completed_epochs"])


def descendant_rss_mib():
    result = subprocess.run(["ps", "-e", "-o", "ppid=,rss="], text=True,
                            capture_output=True, check=False)
    direct = {entry[0].pid for entry in children if entry[0].poll() is None}
    total = 0
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and int(fields[0]) in direct:
            total += int(fields[1])
    return round(total / 1024, 1)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
rows = json.loads((CONFIGS / "index-one-gpu.json").read_text())["runs"]
log_dir = ROOT / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
round_number = 0

while True:
    pending = []
    for row in rows:
        output = Path(row["output_root"]) / row["name"]
        cfg = json.loads((CONFIGS / row["file"]).read_text())
        current = completed_epochs(output)
        total = int(cfg["train"]["epochs"])
        if current < total:
            pending.append((row, output, current, min(current + CHUNK_EPOCHS, total)))
    if not pending:
        print("ALL_RUNS_COMPLETE", flush=True)
        break
    # Always advance the least-complete runs first. This alternates work fairly
    # across all runs while limiting host memory to three TensorFlow processes.
    pending.sort(key=lambda item: (item[2], item[0]["name"]))
    pending = pending[:MAX_CONCURRENT]

    round_number += 1
    print("ROUND_START", round_number,
          json.dumps({row["name"]: [start, target] for row, _, start, target in pending}, sort_keys=True),
          flush=True)
    children = []
    for row, output, start, target in pending:
        command = [
            sys.executable, "-u", "/work/code/run_engram.py", "train",
            "--config", str(CONFIGS / row["file"]),
            "--data-cache", row["data_cache"],
            "--out", str(output), "--track", "--stop-after", str(target),
        ]
        log_path = log_dir / f"{row['name']}-{os.environ.get('HOSTNAME', 'pod')}.log"
        handle = log_path.open("a", buffering=1)
        handle.write(f"\n[one-gpu round {round_number}] resume={start} stop_after={target}\n")
        child = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        children.append((child, row["name"], handle, time.time(), output, target))
        print("ARM_STARTED", row["name"], "pid", child.pid, "target", target, flush=True)
        time.sleep(10)

    failed = False
    last_sample = 0.0
    while children:
        for entry in children[:]:
            child, name, handle, started_wall, output, target = entry
            if child.poll() is not None:
                actual = completed_epochs(output)
                okay = child.returncode == 0 and actual >= target
                failed |= not okay
                print("ARM_EXIT", name, child.returncode, "epoch", actual, "target", target, flush=True)
                handle.close()
                children.remove(entry)
                continue
            latest = output / "latest.json"
            last_progress = max(started_wall, latest.stat().st_mtime if latest.exists() else started_wall)
            if time.time() - last_progress > STALL_SECONDS:
                print("ARM_STALLED_NO_CHECKPOINT", STALL_SECONDS, name, flush=True)
                os.killpg(child.pid, signal.SIGTERM)
        if children and time.monotonic() - last_sample >= 60:
            query = subprocess.run([
                "nvidia-smi",
                "--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total,power.draw,power.limit",
                "--format=csv,noheader,nounits",
            ], text=True, capture_output=True, check=False)
            print("RESOURCE_SAMPLE", query.stdout.strip(),
                  "child_rss_mib", descendant_rss_mib(), "active", len(children), flush=True)
            last_sample = time.monotonic()
        time.sleep(5)
    if failed:
        raise SystemExit(1)
    print("ROUND_COMPLETE", round_number, flush=True)
