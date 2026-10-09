#!/usr/bin/env python3
"""Prepare, preflight, or submit the four explicitly registered N=8 pilot jobs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE.parents[3] / "results" / "ebops-n8-20260910" / "launch"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "preflight", "train", "status"))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cost-first", action="store_true")
    mode.add_argument("--long-budget", action="store_true")
    args = parser.parse_args()
    if args.cost_first and args.out_dir == DEFAULT_OUT:
        args.out_dir = DEFAULT_OUT.parent.parent / "ebops-n8-costfirst-20260910" / "launch"
    if args.long_budget and args.out_dir == DEFAULT_OUT:
        args.out_dir = DEFAULT_OUT.parent.parent / "ebops-n8-long-20260911" / "launch"
    out = args.out_dir.resolve()
    kubectl = ["kubectl", "--context", "nautilus", "-n", "cms-ml"]
    if args.stage == "prepare":
        subprocess.run([sys.executable, str(HERE / "gen_ebops_n8_jobs.py"), "--out-dir", str(out)] + (["--long-budget"] if args.long_budget else ["--cost-first"] if args.cost_first else []), check=True)
        return
    manifest = json.loads((out / "launch_manifest.json").read_text())
    if args.stage == "preflight":
        subprocess.run(kubectl + ["apply", "--server-side", "-f", str(out / "configmap.json")], check=True)
        subprocess.run(kubectl + ["apply", "-f", str(out / "preflight.yaml")], check=True)
    elif args.stage == "train":
        job = manifest["preflight_job"]
        state = json.loads(subprocess.check_output(kubectl + ["get", "job", job, "-o", "json"]))
        assert state.get("status", {}).get("succeeded", 0) >= 1, "CPU preflight must finish successfully first"
        logs = subprocess.check_output(kubectl + ["logs", f"job/{job}"], text=True)
        assert "PREFLIGHT_ALL_PASS" in logs and "EBOPS_TARGET_ALL_PASS" in logs
        if manifest.get("cost_first"):
            assert "EBOPS_COSTFIRST_ALL_PASS" in logs
        if manifest.get("long_budget"):
            assert "EBOPS_LONG_ALL_PASS" in logs
        (out / "preflight.log").write_text(logs)
        subprocess.run(kubectl + ["apply", "-f", str(out / "training-jobs.yaml")], check=True)
    else:
        subprocess.run(kubectl + ["get", "jobs,pods", "-l", "app=kai-ebops-n8", "-o", "wide"], check=True)


if __name__ == "__main__":
    main()
