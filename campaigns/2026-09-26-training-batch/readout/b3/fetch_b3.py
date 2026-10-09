"""Fetch the inputs of the b3 (K=3 pod) epoch-500 rule readout. Read-only everywhere.

Pilot telemetry, validation only, never quoted. Writes, beside this file:
  wandb-history-b3.csv   W&B history of the three K=3 runs (every step, selected keys)
  pvc-extract-b3.json    the needed keys of each snapshots/epoch-0500/state.json and of four
                         activation_widths.jsonl records, each with its PVC path, line and sha256

Run from the campaign directory:
  uv run --with wandb python readout/b3/fetch_b3.py
W&B credentials come from ~/.netrc (read by wandb itself; never printed). The PVC is read through
`kubectl -n cms-ml exec <pod> -- cat|sed -n|sha256sum`, nothing else.
"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POD = "kai-chang0926-pilotb5-42abed-0-qqjmt"
NS = "cms-ml"
ROOT = "/data/chang-n64-20260926/pilot-b/runs"
PROJECT = "kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe"
GROUP = "chang-n64-20260926-pilot-b"
RUNS = {  # name -> W&B run id (arm logs, `View run at .../runs/<id>`)
    "chang0926-a07-350-n64-s1": "2b483f74139a",
    "chang0926-c-n64-s1": "d5ba2fb6f134",
    "chang0926-f-n64-s1": "097faea3088c",
}
WB_KEYS = ["_step", "epoch", "ebops_traced", "ebops", "ebops_in_training", "ebops_in_training_over_traced",
           "pid_ebops", "beta", "training_target_ebops", "target_ebops", "budget_met", "ebops_budget_met",
           "ebops_above_floor", "nondegenerate", "feasible_degenerate", "val_categorical_accuracy",
           "val_macro_auc"]
STATE_KEYS = ["config_sha256", "data_sha256", "code_sha256", "completed_epochs", "initial_ebops",
              "best_feasible", "best_feasible_auc", "lowest", "best_auc", "pid", "nondegenerate_rule",
              "feasible_degenerate_epochs", "first_feasible_degenerate", "recovery_frozen"]
# activation_widths.jsonl keeps exactly the committed epochs (restore_checkpoint truncates it,
# code/tree/bnhgq2/ablation.py:317-320), so line n holds zero-based epoch n - 1.
JSONL_LINES = [("chang0926-a07-350-n64-s1", 330), ("chang0926-a07-350-n64-s1", 500),
               ("chang0926-c-n64-s1", 20), ("chang0926-f-n64-s1", 290)]
RECORD_KEYS = ["epoch", "ebops", "ebops_in_training", "ebops_in_training_over_traced", "ebops_above_floor",
               "ebops_traced", "beta", "val_categorical_accuracy", "val_macro_auc", "nondegenerate",
               "ebops_budget_met", "per_layer"]


def _flatten(x):
    if isinstance(x, list):
        for y in x:
            yield from _flatten(y)
    else:
        yield float(x)


def kexec(*args):
    cmd = ["kubectl", "-n", NS, "exec", POD, "--", *args]
    return subprocess.run(cmd, check=True, capture_output=True).stdout, " ".join(cmd)


def fetch_wandb():
    import wandb
    api = wandb.Api(timeout=120)
    path = HERE / "wandb-history-b3.csv"
    with path.open("w", newline="") as fh:
        out = csv.writer(fh)
        out.writerow(["run", "run_id"] + WB_KEYS)
        for name, rid in RUNS.items():
            run = api.run(f"{PROJECT}/{rid}")
            assert run.name == name and run.group == GROUP, (run.name, run.group)
            rows = sorted(run.scan_history(page_size=1000), key=lambda r: r["_step"])
            assert [r["_step"] for r in rows] == list(range(1, 501)), name
            for r in rows:
                out.writerow([name, rid] + [repr(r[k]) if isinstance(r.get(k), float) else r.get(k)
                                            for k in WB_KEYS])
            print("WANDB", name, rid, run.state, len(rows), file=sys.stderr)
    return path


def fetch_pvc():
    extract = {"pod": POD, "namespace": NS, "state": {}, "records": []}
    for name in RUNS:
        path = f"{ROOT}/{name}/snapshots/epoch-0500/state.json"
        raw, cmd = kexec("cat", path)
        remote, _ = kexec("sha256sum", path)
        sha = hashlib.sha256(raw).hexdigest()
        assert remote.split()[0].decode() == sha, (path, remote)
        state = json.loads(raw)
        extract["state"][name] = {"path": path, "command": cmd, "sha256": sha, "bytes": len(raw),
                                  **{k: state.get(k) for k in STATE_KEYS}}
    for name, line in JSONL_LINES:
        path = f"{ROOT}/{name}/activation_widths.jsonl"
        raw, cmd = kexec("sed", "-n", f"{line}{{p;q}}", path)
        rec = json.loads(raw)
        assert rec["epoch"] == line - 1, (name, line, rec["epoch"])
        widths = {}
        for q, w in rec["widths"].items():
            if "ebops_bits" not in w:
                continue
            flat = list(_flatten(w["ebops_bits"]))
            entry = {"overflow_mode": w.get("overflow_mode"), "channels": len(flat),
                     "zero_bit": sum(1 for b in flat if b == 0), "live": sum(1 for b in flat if b > 0),
                     "one_bit": sum(1 for b in flat if b == 1), "channel_bits": sum(flat)}
            if len(flat) <= 64:
                # one line per quantizer: the per-channel EBOPs-billed widths (HGQ2 `bits`)
                entry["ebops_bits"] = json.dumps(flat)
            widths[q] = entry
        extract["records"].append({"run": name, "path": path, "line": line, "command": cmd,
                                   "sha256_line": hashlib.sha256(raw.rstrip(b"\n")).hexdigest(),
                                   **{k: rec.get(k) for k in RECORD_KEYS}, "widths_ebops_bits": widths})
    out = HERE / "pvc-extract-b3.json"
    # indent=1 keeps one scalar per line so the READOUT can cite file:line; the per-channel
    # ebops_bits lists are stored as one-line strings.
    text = json.dumps(extract, indent=1)
    out.write_text(text + "\n")
    print("PVC", out, file=sys.stderr)
    return out


if __name__ == "__main__":
    fetch_wandb()
    fetch_pvc()
