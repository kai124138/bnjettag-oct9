#!/usr/bin/env python3
"""Pt-weighting study (N=8 headline): immutable code ConfigMap, CPU preflight, one GPU
utilization benchmark and the packed production Jobs. Writes files only; no cluster mutation.

Arms base / ptw5 / ptwnc (configs/gen_ptw.py) x seeds 1-8 = 24 trainings. A ~19k-parameter
model at batch 256 is kernel-launch-bound (one process holds a GPU at ~30%), so each GPU pod
runs K trainings concurrently: all three arms of K/3 seeds, i.e. every seed-paired comparison
shares one GPU/node. Batch size and recipe are unchanged. Every training gets a distinct
WANDB_RUN_NAME and out_dir leaf (ptw-n8-0925-<arm>-s<seed>) because _variant() is `w1a8` for
every arm and default names / model-<leaf> artifacts would collide.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import yaml

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[2] / "hgq2"
sys.path.insert(0, str(CODE / "configs"))
from gen_ptw import ARMS, GROUP, PREFIX, check_matched, make  # noqa: E402

# W&B project for the jobs (2026-09-26, user correction): the env var WANDB_PROJECT outranks the
# configs' train.wandb_project (wandb_util.resolve_project), so configs/ConfigMap stay unchanged.
# Pack p1 was submitted earlier with BNJetTagAug and runs there; see the launch record.
PROJECT = "BNJetTag-Weights"

ENTITY = "kayamaguchi-uc-san-diego"
SEEDS = list(range(1, 9))
SHORT = "ptw-n8-0925"
GPU_POOL = ["NVIDIA-GeForce-RTX-4090", "NVIDIA-L40S", "NVIDIA-L40",
            "NVIDIA-A100-SXM4-80GB", "NVIDIA-A100-80GB-PCIe", "NVIDIA-A100-PCIE-40GB"]
BAD_NODES = ["nautilus-ext-gpu01.fullerton.edu", "ren-gp-argo-01.madren.org",
             "k8s-chase-ci-07.calit2.optiputer.net", "k8s-chase-ci-10.calit2.optiputer.net",
             "k8s-haosu-22.sdsc.optiputer.net", "ry-gpu-08.sdsc.optiputer.net"]
GPU_DEPS = ('"tensorflow[and-cuda]==2.21.0" "keras==3.15.0" "hgq2==0.1.9" "quantizers==1.2.2" '
            '"scikit-learn==1.9.0" "h5py==3.14.0" "wandb==0.28.0" "hls4ml==1.3.0" "numpy==2.5.0" "matplotlib==3.11.0"')  # matplotlib: pt_weights plots
CPU_DEPS = GPU_DEPS.replace("tensorflow[and-cuda]", "tensorflow")
ZENODO = "https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_train.tar.gz?download=1"


def leaf(arm, seed):
    return f"{SHORT}-{arm}-s{seed}"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def package_code():
    paths = list((CODE / "bnhgq2").rglob("*.py"))
    paths += list((CODE / "hls_templates").glob("*.h"))
    paths += [CODE / "run_stage.py", CODE / "preflight_final.sh"]
    paths += list((CODE / "configs").glob(f"{PREFIX}-*.json"))
    paths += [CODE / "configs" / n for n in ("gen_ptw.py", "r14-l1x3-n8-w1a8.json")]
    raw, records = io.BytesIO(), {}
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for p in sorted(set(paths)):
            if "__pycache__" in p.parts:
                continue
            data = p.read_bytes()
            rel = str(p.relative_to(CODE))
            records[rel] = hashlib.sha256(data).hexdigest()
            info = tarfile.TarInfo("hgq2/" + rel)
            info.size, info.mode = len(data), 0o644
            tar.addfile(info, io.BytesIO(data))
    payload = gzip.compress(raw.getvalue(), mtime=0)
    assert len(payload) < 900_000, "ConfigMap payload is too large"
    assert "bnhgq2/pt_weights.py" in records and "bnhgq2/train.py" in records
    digest = hashlib.sha256(payload).hexdigest()
    return payload, digest, f"kai-ptw-n8-code-{digest[:10]}", records


def code_setup(digest, records):
    """Unpack + verify the exact archive and the two load-bearing files."""
    cfgs = " ".join(f'"$CODE/configs/{make(a)["name"]}.json"' for a in ARMS)
    return f'''mkdir -p /work/code /work/data /work/outputs
CODE=/work/code
echo "{digest}  /cmcode/hgq2.tar.gz" | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1
echo "{records['bnhgq2/train.py']}  $CODE/bnhgq2/train.py" | sha256sum -c -
echo "{records['bnhgq2/pt_weights.py']}  $CODE/bnhgq2/pt_weights.py" | sha256sum -c -
for f in {cfgs}; do test -f "$f" || {{ echo "[fatal] missing $f"; exit 1; }}; done
echo "[gate] archive {digest[:12]} + train.py + pt_weights.py + 3 arm configs verified"
export PYTHONPATH="$CODE" BNHGQ2_CODE_SHA256={digest}
'''


FETCH = f'''echo "[data] $(date -u +%FT%TZ) fetch HLS4ML LHC Jet 150p TRAIN split from Zenodo"
python -u -c 'import urllib.request; urllib.request.urlretrieve("{ZENODO}", "/work/data/train.tar.gz")'
sz=$(stat -c %s /work/data/train.tar.gz); echo "[data] tarball bytes: $sz"
[ "$sz" -gt 2500000000 ] || {{ echo "[fatal] train tarball too small ($sz)"; exit 1; }}
tar -xzf /work/data/train.tar.gz -C /work/data && rm -f /work/data/train.tar.gz
DATA=$(dirname "$(find /work/data -name 'jetImage_*.h5' -print -quit)")
[ -n "$DATA" ] || {{ echo "[fatal] no jetImage_*.h5 after extract"; exit 1; }}
echo "[data] DATA=$DATA ($(ls "$DATA" | wc -l) files) $(date -u +%FT%TZ)"
export BNHGQ2_TRAIN_DATA="$DATA" BNHGQ2_OUT_ROOT=/work/outputs BNHGQ2_STORE=/work/outputs/_store
'''

# 5 s GPU samples (epoch s, gpu, util %, mem MiB, cgroup RAM bytes, cgroup cpu usec) to a file,
# plus a 5-minute rolling mean in the pod log every 5 minutes.
GPU_LOGGER = '''UTIL=/work/outputs/gpu_util.csv
( set +e +o pipefail; while true; do
    q=$(nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    m=$(cat /sys/fs/cgroup/memory.current 2>/dev/null || echo NA)
    c=$(awk '/usage_usec/{print $2}' /sys/fs/cgroup/cpu.stat 2>/dev/null || echo NA)
    echo "$(date +%s), $q, $m, $c" >> "$UTIL"; sleep 5
  done ) &
( set +e +o pipefail; while sleep 300; do
    echo "[gpu-util] $(date -u +%FT%TZ) $(tail -n 60 "$UTIL" | awk -F', ' '{s+=$3; n++; if($5!="NA") m=$5} END{if(n) printf "last5min_mean=%.1f%% n=%d ram=%.1fGiB", s/n, n, m/1073741824}')"
  done ) &
'''


def train_cmd(arm, seed, timeout=None):
    lf = leaf(arm, seed)
    cfg = make(arm)["name"]
    t = f"timeout {timeout} " if timeout else ""
    return (f'mkdir -p /work/outputs/{lf}\n'
            f'( set -o pipefail; WANDB_RUN_NAME={lf} WANDB_TAGS=ptw,l1x3,n8,w1a8,{arm},s{seed} '
            f'{t}python -u "$CODE/run_stage.py" train --config "$CODE/configs/{cfg}.json" '
            f'--seed {seed} --out-dir /work/outputs/{lf} 2>&1 | tee /work/outputs/{lf}/train.log '
            f'| sed -u "s/^/[{lf}] /" ) &\n'
            f'pids+=($!); leaves+=({lf})\n')


# Best-effort: attach per-run pt_weights files, train.log and the pod GPU-utilization log to
# each finished W&B training run (found by display name in the group). Never fails the pod.
AUX_UPLOAD = f'''python - <<'PYEOF' || echo "[aux] upload skipped"
import glob, os, wandb
api = wandb.Api()
for d in sorted(glob.glob("/work/outputs/{SHORT}-*")):
    name = os.path.basename(d)
    try:
        runs = list(api.runs("{ENTITY}/{PROJECT}", filters={{"display_name": name, "group": "{GROUP}"}}))
        for r in runs:
            for f in ["pt_weights.json", "train.log"] + [os.path.basename(p) for p in glob.glob(d + "/*.png")]:
                if os.path.exists(os.path.join(d, f)):
                    r.upload_file(os.path.join(d, f), root=d)
            r.upload_file("/work/outputs/gpu_util.csv", root="/work/outputs")
        print(f"[aux] {{name}}: uploaded to {{len(runs)}} run(s)", flush=True)
    except Exception as e:
        print(f"[aux] {{name}}: upload warn {{e}}", flush=True)
PYEOF
'''


def gpu_script(digest, records, runs, bench=False, bench_seconds=600):
    s = ["set -eo pipefail",
         "export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_FORCE_GPU_ALLOW_GROWTH=true",
         "export TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=2 OMP_NUM_THREADS=2",
         code_setup(digest, records), GPU_LOGGER,
         f"echo \"[setup] $(date -u +%FT%TZ) pinned deps\"",
         f"pip install -q --no-cache-dir {GPU_DEPS}",
         'NVLIBS=$(python -c "import glob; print(\':\'.join(sorted(glob.glob(\'/usr/local/lib/python*/site-packages/nvidia/*/lib\'))))")',
         'export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
         "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || { echo '[fatal] no GPU'; exit 1; }",
         "python -c \"import tensorflow as tf; g=tf.config.list_physical_devices('GPU'); assert g, 'NO GPU'; print('[gpu] TF sees', g)\""]
    if bench:
        s.append("export WANDB_MODE=disabled  # benchmark: no W&B secret mounted, no runs created")
    else:
        s.append(f"export WANDB_PROJECT={PROJECT} WANDB_ENTITY={ENTITY} WANDB_GROUP={GROUP} WANDB_MODE=online")
        s.append("python -c \"import wandb; wandb.Api().viewer; print('[wandb] authentication OK')\"")
    s.append(FETCH)
    s.append('cd "$CODE"\npids=(); leaves=()')
    for arm, seed in runs:
        s.append(train_cmd(arm, seed, timeout=(bench_seconds + 1800) if bench else None))
    s.append(f'echo "[pack] $(date -u +%FT%TZ) started {len(runs)} trainings: ${{leaves[*]}}"')
    if bench:
        s.append(f'''# Measure only once every process has built/calibrated its model (fit about to start).
for i in $(seq 1 360); do
  ready=$( (grep -l "binary gate OK" /work/outputs/{SHORT}-*/train.log 2>/dev/null || true) | wc -l)
  [ "$ready" -ge {len(runs)} ] && break; sleep 5
done
T0=$(date +%s); echo "[bench] all {len(runs)} processes at fit start: T0=$T0 ($(date -u +%FT%TZ))"
nvidia-smi dmon -s um -d 5 > /work/outputs/dmon.log 2>&1 &
sleep {bench_seconds}
T1=$(date +%s)
python - "$T0" "$T1" <<'PYEOF'
import sys, numpy as np
t0, t1 = int(sys.argv[1]), int(sys.argv[2])
rows = [l.strip().split(", ") for l in open("/work/outputs/gpu_util.csv") if l.strip()]
win = [r for r in rows if len(r) >= 6 and t0 <= int(r[0]) <= t1 and r[2].strip().isdigit()]
u = np.array([float(r[2]) for r in win])
ram = max(float(r[4]) for r in win if r[4] != "NA") / 2**30
cpu = (float(win[-1][5]) - float(win[0][5])) / 1e6 / (int(win[-1][0]) - int(win[0][0]))
print(f"[bench] gpu={{win[0][1]}} window={{t1-t0}}s samples={{len(u)}} util_mean={{u.mean():.1f}}% "
      f"median={{np.median(u):.1f}}% p10={{np.percentile(u,10):.1f}}% min={{u.min():.0f}}% max={{u.max():.0f}}% "
      f"gpu_mem_max={{max(float(r[3]) for r in win):.0f}}MiB ram_peak={{ram:.2f}}GiB cpu_cores_used={{cpu:.2f}}")
print("BENCH_UTIL_MEAN=%.1f" % u.mean())
PYEOF
echo "[bench] dmon (sm%/mem% per 5 s):"; cat /work/outputs/dmon.log
echo "[bench] Keras epoch lines per process:"
for f in /work/outputs/{SHORT}-*/train.log; do echo "== $f"; grep -E "^Epoch |ms/step" "$f" || true; grep -E "pt_weights ON|params=" "$f" || true; done
kill "${{pids[@]}}" 2>/dev/null || true
echo "[bench] done $(date -u +%FT%TZ)"
''')
    else:
        s.append('''fail=0
for i in "${!pids[@]}"; do
  if wait "${pids[$i]}"; then echo "[pack] ${leaves[$i]} OK $(date -u +%FT%TZ)"
  else rc=$?; echo "[pack] ${leaves[$i]} FAILED rc=$rc $(date -u +%FT%TZ)"; fail=1; fi
done''')
        s.append(AUX_UPLOAD)
        s.append('echo "[gpu-util] whole-pod mean over all samples:"; awk -F", " \'{s+=$3;n++} END{if(n) printf "%.1f%% n=%d\\n", s/n, n}\' "$UTIL"')
        s.append('[ "$fail" = 0 ] || exit 1\necho "[done] $(date -u +%FT%TZ)"')
    return "\n".join(s) + "\n"


def job(name, script, cm, labels, *, gpu=True, cpu="14", mem="36Gi", eph="32Gi",
        deadline=None, secret=True):
    affinity = {"nodeAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": {"nodeSelectorTerms": [
        {"matchExpressions": [
            {"key": "kubernetes.io/hostname", "operator": "NotIn", "values": BAD_NODES},
            {"key": "kubernetes.io/arch", "operator": "In", "values": ["amd64"]}]
            + ([{"key": "nvidia.com/gpu.product", "operator": "In", "values": GPU_POOL}] if gpu else [])}]}}}
    if gpu:
        affinity["nodeAffinity"]["preferredDuringSchedulingIgnoredDuringExecution"] = [
            {"weight": 100, "preference": {"matchExpressions": [
                {"key": "nvidia.com/gpu.product", "operator": "In", "values": GPU_POOL[:3]}]}}]
    res = {"cpu": cpu, "memory": mem, "ephemeral-storage": eph}
    if gpu:
        res["nvidia.com/gpu"] = "1"
    container = {"name": "train" if gpu else "preflight", "image": "python:3.12",
                 "command": ["bash", "-c"], "args": [script],
                 "resources": {"requests": dict(res), "limits": dict(res)},
                 "volumeMounts": [{"name": "cmcode", "mountPath": "/cmcode"},
                                  {"name": "work", "mountPath": "/work"}]}
    if secret:
        container["env"] = [{"name": "WANDB_API_KEY", "valueFrom": {"secretKeyRef": {
            "name": "kai-wandb", "key": "WANDB_API_KEY"}}}]
    spec = {"backoffLimit": 0, "template": {"metadata": {"labels": dict(labels)}, "spec": {
        "restartPolicy": "Never", "affinity": affinity, "containers": [container],
        "volumes": [{"name": "cmcode", "configMap": {"name": cm}},
                    {"name": "work", "emptyDir": {"sizeLimit": "28Gi"}}]}}}
    if deadline:
        spec["activeDeadlineSeconds"] = deadline
    return {"apiVersion": "batch/v1", "kind": "Job",
            "metadata": {"name": name, "namespace": "cms-ml", "labels": dict(labels)}, "spec": spec}


def preflight_script(digest, records):
    smokes = "\n".join(
        f'python -u "$CODE/run_stage.py" train --config "$CODE/configs/{make(a)["name"]}.json" '
        f'--seed 1 --smoke --out-dir /work/outputs/smoke-{a} 2>&1 | tee /work/outputs/smoke-{a}.log'
        for a in ARMS)
    return f'''set -euo pipefail
export KERAS_BACKEND=tensorflow CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled MPLBACKEND=Agg
{code_setup(digest, records)}
export BNF_CODE=/work/code BNF_CONFIG_GLOB='{PREFIX}-*.json' BNF_SKIP_INSTALL=1
pip install -q --no-cache-dir {CPU_DEPS}
bash "$CODE/preflight_final.sh"
{FETCH}
cd "$CODE"
{smokes}
python - <<'PYEOF'
import json, os
ok = True
for arm in {list(ARMS)!r}:
    d = f"/work/outputs/smoke-{{arm}}"
    meta = json.load(open(os.path.join(d, "train_meta.json")))
    log = open(f"/work/outputs/smoke-{{arm}}.log").read()
    on = arm != "base"
    has = ("pt_weights" in meta, os.path.exists(os.path.join(d, "pt_weights.json")), "pt_weights ON" in log)
    pngs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    good = all(has) if on else not any(has)
    if on:
        cap = meta["pt_weights"]["cap"]
        good = good and len(pngs) == 2 and cap == (5.0 if arm == "ptw5" else None)
        print(f"  {{arm}}: cap={{cap}} eff_frac={{ {{k: round(v['eff_frac'], 3) for k, v in meta['pt_weights']['summary'].items()}} }} pngs={{pngs}}")
    print(f"  {{arm}}: n_files={{meta['n_files']}} n_train={{meta['n_train']}} epochs_run={{meta['epochs_run']}} jit={{meta['jit_compile']}} params={{meta['params']}} -> {{'OK' if good else 'FAIL'}}")
    ok = ok and good and meta["jit_compile"] is False
print("PTW_SMOKE_PASS" if ok else "PTW_SMOKE_FAIL")
raise SystemExit(0 if ok else 1)
PYEOF
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--k", type=int, default=6, help="trainings per GPU pod (multiple of 3)")
    ap.add_argument("--cpu-per-proc", type=float, default=2.0)
    ap.add_argument("--mem-gi", type=int, default=36, help="pod memory limit (Gi)")
    ap.add_argument("--deadline", type=int, default=172800)
    args = ap.parse_args()
    assert args.k % 3 == 0 and len(SEEDS) * 3 % args.k == 0
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        cfg = make(arm)
        check_matched(cfg)
        assert json.loads((CODE / "configs" / f"{cfg['name']}.json").read_text()) == cfg, \
            "Regenerate configs first (configs/gen_ptw.py)"
    payload, digest, cm, records = package_code()
    for rel in ("bnhgq2/train.py", "bnhgq2/pt_weights.py"):
        assert records[rel] == sha(CODE / rel)
    (out / "hgq2.tar.gz").write_bytes(payload)
    (out / "configmap.json").write_text(json.dumps({
        "apiVersion": "v1", "kind": "ConfigMap", "immutable": True,
        "metadata": {"name": cm, "namespace": "cms-ml", "labels": {"app": "kai-ptw-n8"}},
        "binaryData": {"hgq2.tar.gz": base64.b64encode(payload).decode()}}, indent=2) + "\n")

    per_pod_seeds = args.k // 3
    packs = [[(arm, s) for s in SEEDS[i:i + per_pod_seeds] for arm in ARMS]
             for i in range(0, len(SEEDS), per_pod_seeds)]
    cpu = str(int(round(args.cpu_per_proc * args.k + 2)))
    mem = f"{args.mem_gi}Gi"
    jobs = []
    for p, runs in enumerate(packs, 1):
        name = f"kai-{SHORT}-k{args.k}-p{p}"
        labels = {"app": "kai-ptw-n8", "pack": f"p{p}"}
        j = job(name, gpu_script(digest, records, runs), cm, labels, cpu=cpu, mem=mem,
                deadline=args.deadline)
        (out / f"{name}.yaml").write_text(yaml.safe_dump(j, sort_keys=False))
        jobs.append(j)
    (out / "training-jobs.yaml").write_text(yaml.safe_dump_all(jobs, sort_keys=False))

    bench_name = f"kai-{SHORT}-bench-k{args.k}-{digest[:6]}"
    bench = job(bench_name, gpu_script(digest, records, packs[0], bench=True), cm,
                {"app": "kai-ptw-n8-bench"}, cpu=cpu, mem=mem, deadline=5400, secret=False)
    (out / "benchmark.yaml").write_text(yaml.safe_dump(bench, sort_keys=False))

    pre_name = f"kai-{SHORT}-preflight-{digest[:8]}"
    pre = job(pre_name, preflight_script(digest, records), cm, {"app": "kai-ptw-n8-preflight"},
              gpu=False, cpu="4", mem="12Gi", eph="32Gi", deadline=3600, secret=False)
    (out / "preflight.yaml").write_text(yaml.safe_dump(pre, sort_keys=False))

    manifest = {"project": PROJECT, "entity": ENTITY, "group": GROUP,
                "wandb_group_url": f"https://wandb.ai/{ENTITY}/{PROJECT}/groups/{GROUP}",
                "configmap": cm, "code_sha256": digest, "files": records,
                "train_py_sha256": records["bnhgq2/train.py"],
                "pt_weights_py_sha256": records["bnhgq2/pt_weights.py"],
                "configs": {a: make(a)["name"] for a in ARMS},
                "arms": {a: (make(a)["train"].get("pt_weights")) for a in ARMS},
                "seeds": SEEDS, "k_per_pod": args.k, "cpu_per_pod": cpu, "mem_per_pod": mem,
                "gpu_pool": GPU_POOL, "deadline_s": args.deadline, "backoffLimit": 0,
                "packs": {j["metadata"]["name"]: [leaf(a, s) for a, s in r] for j, r in zip(jobs, packs)},
                "preflight_job": pre_name, "benchmark_job": bench_name,
                "resume": "none on the train.py path: a killed pod loses all K of its seeds",
                "epochs": make("base")["train"]["epochs"],
                "es_patience": make("base")["train"]["es_patience"]}
    (out / "launch_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ("configmap", "code_sha256", "train_py_sha256",
                                                "pt_weights_py_sha256", "preflight_job",
                                                "benchmark_job", "packs")}, indent=2))


if __name__ == "__main__":
    main()
