"""Parse pilot b5 per-epoch series. Primary source: recovered PVC logs (complete, 500 epochs);
cross-check: local timestamped captures in ../logs. Writes pilotb5-curves.csv."""
import re, glob, csv, os, json, sys
from collections import defaultdict
H = os.path.dirname(os.path.abspath(__file__))
PVC = H + "/../../2026-10-01-recovery/captures/pvc-20261001T0555Z/chang-n64-20260926/pilot-b/logs"
LOC = H + "/../logs"
ARMS = ["a-n64-s1", "a-n64-s2", "d-n64-s1", "e1-n64-s1", "cprime-n64-s1"]
ep_re = re.compile(r"^\[epoch (\d+)/7000\] (.*)$")
def parse(path):
    out = {}
    for line in open(path, errors="replace"):
        m = ep_re.match(line.strip())
        if not m: continue
        kv = dict(t.split("=", 1) for t in m.group(2).split() if "=" in t)
        out[int(m.group(1))] = kv
    return out
def num(x):
    try: return float(x)
    except: return None
def build():
    rows, conflicts = [], []
    for arm in ARMS:
        src = parse(glob.glob(f"{PVC}/chang0926-{arm}-kai-chang0926-pilotb5-42abed-0.log")[0])
        others = {}
        for f in sorted(glob.glob(f"{LOC}/chang0926-{arm}-kai-chang0926-pilotb5-*Z.log")):
            for e, kv in parse(f).items():
                for k in ("val_accuracy", "val_AUC", "EBOPs", "beta", "degenerate"):
                    if k in kv and e in src and src[e].get(k) != kv[k]:
                        conflicts.append((arm, e, k, src[e].get(k), kv[k], os.path.basename(f)))
                others.setdefault(e, kv)
        missing = [e for e in others if e not in src]
        for e in sorted(src):
            kv = src[e]; traced = kv.get("EBOPs") not in (None, "untraced")
            ab = num(kv.get("above_floor"))
            eb = num(kv["EBOPs"]) if traced else None
            rows.append(dict(arm=arm, epoch=e, ebops_traced=eb if eb is not None else "",
              in_training_ebops=kv.get("in_training_ebops", ""), target=kv.get("target"),
              above_floor=kv.get("above_floor", ""),
              floor=(int(eb - ab) if (traced and ab is not None) else ""),
              feasible=kv.get("feasible", ""), degenerate=kv.get("degenerate", ""),
              beta=kv.get("beta"), val_auc=kv.get("val_AUC"), val_accuracy=kv.get("val_accuracy")))
        print(arm, "epochs", len(src), "max", max(src), "local-only epochs", missing, file=sys.stderr)
    return rows, conflicts
if __name__ == "__main__":
    rows, conflicts = build()
    with open(H + "/pilotb5-curves.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("rows", len(rows), "conflicts", len(conflicts))
    for c in conflicts[:20]: print(c)
