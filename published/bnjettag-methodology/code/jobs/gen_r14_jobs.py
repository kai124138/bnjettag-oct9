#!/usr/bin/env python3
"""Round-14 job YAMLs — L1-realistic (N, 3) inputs, constituent-count sweep.

One NRP Job per (config, seed) from the r14 configs written by
`code/hgq2/configs/gen_r14.py`. Structure is the round-13 YAML verbatim except:

  * round label / ConfigMap `kai-bn14-code`;
  * the stale-ConfigMap gate requires the r14 config AND `feature_indices` in
    `bnhgq2/data.py` — a pre-r14 tree would silently train on all 16 features
    (the confound this round exists to remove);
  * W&B project **BNJetTagAug** (new inputs => new project, per Kai 2026-08-01),
    runs grouped per constituent count (`WANDB_GROUP=r14-n<N>`) and tagged;
  * `activeDeadlineSeconds: 21600` (6 h) — the r8 recipe is 101 epochs, not r13's 1500.

Run set (R14 design, decisions.md 2026-08-01), 3 seeds per arm:
  stage1  N in {8,16,32,64} x {fp32, w8a8, w1a8}  = 36 jobs  (baselines + thesis)
  stage2  N in {8,16,32,64} x {w1a6, w1a4}        = 24 jobs  (activation ladder)

NOTHING here launches anything; this only writes files.
Usage (from code/jobs/training/variants/):  python gen_r14_jobs.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "hgq2", "configs"))

N_SWEEP = [8, 16, 32, 64]
SEEDS = [1, 2, 3]
STAGES = {
    "stage1": [(f"r14-l1x3-n{n}-{v}", s)
               for n in N_SWEEP for v in ("fp32", "w8a8", "w1a8") for s in SEEDS],
    "stage2": [(f"r14-l1x3-n{n}-{v}", s)
               for n in N_SWEEP for v in ("w1a6", "w1a4") for s in SEEDS],
}

TEMPLATE = """apiVersion: batch/v1
kind: Job
metadata:
  name: {job}
  labels:
    app: bnjet-r14
    bn14: "{leaf}"
    bn14stage: "{stage}"
spec:
  # backoffLimit 2: an UnexpectedAdmissionError (node GPU device-plugin race, zero side
  # effects) must not kill the Job. Duplicate-W&B-run risk from a mid-train retry is
  # accepted (the ROC fetcher prefers the finished run if duplicates appear).
  backoffLimit: 2
  # 6 h: the r8 recipe (101 epochs, batch 256) at N=64 sequence length with margin.
  activeDeadlineSeconds: 21600
  template:
    metadata:
      labels:
        app: bnjet-r14
        bn14: "{leaf}"
        bn14stage: "{stage}"
    spec:
      restartPolicy: Never
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: NotIn
                values: [k8s-chase-ci-07.calit2.optiputer.net, k8s-chase-ci-10.calit2.optiputer.net, k8s-haosu-22.sdsc.optiputer.net, ry-gpu-08.sdsc.optiputer.net, suncave-1, suncave-2, suncave-3, suncave-4, suncave-5, suncave-6, suncave-7, suncave-8, suncave-9, suncave-10, suncave-11, suncave-12, suncave-13, suncave-14, suncave-15, suncave-16, suncave-17, suncave-18, suncave-19, suncave-20]
              - key: kubernetes.io/arch
                operator: In
                values: [amd64]
              - key: nvidia.com/gpu.product
                operator: In
                values:
                - NVIDIA-H200-NVL
                - NVIDIA-H100-80GB-HBM3
                - NVIDIA-RTX-PRO-6000-Blackwell-Max-Q-Workstation-Edition
                - NVIDIA-A100-SXM4-80GB
                - NVIDIA-A100-80GB-PCIe
                - NVIDIA-A100-PCIE-40GB
                - NVIDIA-GeForce-RTX-4090
                - NVIDIA-L40S
                - NVIDIA-L40
                - NVIDIA-RTX-A6000
                - NVIDIA-A10
                - NVIDIA-L4
                - NVIDIA-GeForce-RTX-2080-Ti
                - Tesla-V100-SXM2-32GB
                - Tesla-V100-PCIE-32GB
                - NVIDIA-A40
                - NVIDIA-RTX-A5000
                - NVIDIA-GeForce-RTX-3090
          preferredDuringSchedulingIgnoredDuringExecution:
          # PREFER the abundant mid-tier — plentiful and more than enough for a
          # d_model-32 model. De-prefer A100s, flagship = last resort.
          - weight: 100
            preference:
              matchExpressions:
              - key: nvidia.com/gpu.product
                operator: In
                values: [NVIDIA-A10, NVIDIA-L4, NVIDIA-GeForce-RTX-2080-Ti, Tesla-V100-SXM2-32GB, Tesla-V100-PCIE-32GB, NVIDIA-A40, NVIDIA-RTX-A5000, NVIDIA-GeForce-RTX-3090]
          - weight: 60
            preference:
              matchExpressions:
              - key: nvidia.com/gpu.product
                operator: In
                values: [NVIDIA-GeForce-RTX-4090, NVIDIA-L40S, NVIDIA-L40, NVIDIA-RTX-A6000]
          - weight: 20
            preference:
              matchExpressions:
              - key: nvidia.com/gpu.product
                operator: In
                values: [NVIDIA-A100-SXM4-80GB, NVIDIA-A100-80GB-PCIe, NVIDIA-A100-PCIE-40GB]
          - weight: 10
            preference:
              matchExpressions:
              - key: nvidia.com/gpu.product
                operator: In
                values: [NVIDIA-H200-NVL, NVIDIA-H100-80GB-HBM3, NVIDIA-RTX-PRO-6000-Blackwell-Max-Q-Workstation-Edition]
      containers:
      - name: train
        image: python:3.12
        command: ["bash", "-c"]
        args:
        - |
          set -eo pipefail
          export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_FORCE_GPU_ALLOW_GROWTH=true
          mkdir -p /work/code /work/data /work/outputs
          CODE=/work/code
          OUT=/work/outputs/{leaf}
          mkdir -p "$OUT"
          echo "[code] $(date) unpack code from ConfigMap kai-bn14-code (PVC-free)"
          tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1
          md5sum /cmcode/hgq2.tar.gz | awk '{{print "[code] configmap tar md5:", $1}}'
          # ---- STALE-CONFIGMAP GATE: round 14 REQUIRES the L1-realistic feature-subset
          # plumbing. A pre-r14 bnhgq2 would run this config on ALL 16 features — the
          # exact confound this round removes — or crash late. Fail fast instead. ----
          [ -f "$CODE/configs/{config}.json" ] || {{
            echo "[fatal] unpacked code lacks configs/{config}.json -> ConfigMap kai-bn14-code is STALE."
            echo "[fatal] rebuild it (make_code_configmap_r14.sh) and re-apply."
            exit 1
          }}
          grep -q "def feature_indices" "$CODE/bnhgq2/data.py" || {{
            echo "[fatal] bnhgq2/data.py has no feature_indices (L1 feature subset) -> STALE ConfigMap."
            exit 1
          }}
          grep -q "wandb_util" "$CODE/bnhgq2/train.py" || {{
            echo "[fatal] bnhgq2/train.py predates the W&B artifact layout -> STALE ConfigMap."
            exit 1
          }}
          echo "[gate] configs/{config}.json + feature_indices + wandb_util present (ConfigMap kai-bn14-code is fresh)"
          export PYTHONPATH="$CODE:$PYTHONPATH"
          echo "[setup] $(date) pinned deps (mirror .venv-hgq2)"
          pip install -q --no-cache-dir "tensorflow[and-cuda]==2.21.0" "keras==3.15.0" "hgq2==0.1.9" "quantizers==1.2.2" "scikit-learn==1.9.0" "h5py==3.14.0" "wandb==0.28.0" "hls4ml==1.3.0" "numpy==2.5.0"
          # TF 2.21 pip wheel's RPATH discovery of the nvidia-*-cu12 wheel libs is broken;
          # explicit LD_LIBRARY_PATH over the wheel lib dirs fixes it (verified 2026-07-07).
          NVLIBS=$(python -c "import glob; print(':'.join(sorted(glob.glob('/usr/local/lib/python*/site-packages/nvidia/*/lib'))))")
          export LD_LIBRARY_PATH="$NVLIBS${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"
          echo "[gpu] $(date) nvidia-smi + TF backend assertion"
          nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || {{ echo "[fatal] no nvidia-smi / GPU"; exit 1; }}
          python -c "import os; os.environ.setdefault('KERAS_BACKEND','tensorflow'); import tensorflow as tf; g=tf.config.list_physical_devices('GPU'); assert g, 'NO GPU visible to TensorFlow'; print('[gpu] TF sees', g)"
          echo "[data] $(date) fetch HLS4ML LHC Jet 150p TRAIN split from Zenodo (~3 GB, PVC-free)"
          python -u -c 'import urllib.request; urllib.request.urlretrieve("https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_train.tar.gz?download=1", "/work/data/train.tar.gz")'
          sz=$(stat -c %s /work/data/train.tar.gz); echo "[data] tarball bytes: $sz"
          [ "$sz" -gt 2500000000 ] || {{ echo "[fatal] train tarball too small ($sz < 2.5GB; real size 2,725,115,104 B measured 2026-07-07)"; exit 1; }}
          tar -xzf /work/data/train.tar.gz -C /work/data && rm -f /work/data/train.tar.gz
          DATA=$(dirname "$(find /work/data -name 'jetImage_*.h5' -print -quit)")
          [ -n "$DATA" ] || {{ echo "[fatal] no jetImage_*.h5 after extract"; exit 1; }}
          echo "[data] DATA=$DATA ($(ls "$DATA" | wc -l) files)"
          export BNHGQ2_TRAIN_DATA="$DATA"
          export BNHGQ2_OUT_ROOT=/work/outputs
          export BNHGQ2_STORE=/work/outputs/_store
          # ---- W&B (layout 2026-08-01): NEW project BNJetTagAug — new inputs, new
          # project so r14 numbers can never be conflated with the 16-feature tables.
          # Grouped per constituent count for the sweep comparison. ----
          export WANDB_PROJECT=BNJetTagAug
          export WANDB_ENTITY=kayamaguchi-uc-san-diego
          export WANDB_RUN_NAME={leaf}
          export WANDB_GROUP=r14-n{npart}
          export WANDB_TAGS=r14,l1x3,{stage},n{npart},{variant}
          # ---- ROUND 14 ({stage}): L1-realistic inputs (pt, etarel, phirel) x N sweep.
          # Recipe = r8-small verbatim; the ONLY change vs r7/r8 is the input set. ----
          echo "[train] $(date) {leaf}  config={config}.json seed={seed}"
          cd "$CODE"
          python -u "$CODE/run_stage.py" train \\
            --config "$CODE/configs/{config}.json" --seed {seed} --out-dir "$OUT" \\
            2>&1 | tee "$OUT/train.log"
          echo "[done] $(date) {leaf}"
        env:
        - name: WANDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: kai-wandb
              key: WANDB_API_KEY
        resources:
          # RIGHT-SIZED (decisions.md 2026-07-13): deployable-scale jobs are data-bound,
          # not FLOP-bound. requests==limits.
          limits:
            nvidia.com/gpu: "1"
            cpu: "2"
            memory: 8Gi
            ephemeral-storage: 16Gi
          requests:
            nvidia.com/gpu: "1"
            cpu: "2"
            memory: 8Gi
            ephemeral-storage: 16Gi
        volumeMounts:
        - name: cmcode
          mountPath: /cmcode
        - name: work
          mountPath: /work
      volumes:
      - name: cmcode
        configMap:
          name: kai-bn14-code
      - name: work
        emptyDir:
          sizeLimit: 16Gi
"""


def leaf_of(config: str, seed: int) -> str:
    return f"{config}-s{seed}"


def job_of(config: str, seed: int) -> str:
    # k8s names: lowercase alnum + '-', <= 63 chars.
    return f"kai-bn14-{config.removeprefix('r14-')}-s{seed}"


def emit() -> None:
    by_stage: dict[str, list[str]] = {}
    for stage, runs in STAGES.items():
        names = []
        for config, seed in runs:
            if not os.path.exists(os.path.join(CONFIGS, f"{config}.json")):
                sys.exit(f"[fatal] missing config {config}.json — run gen_r14.py first")
            job = job_of(config, seed)
            if len(job) > 63:
                sys.exit(f"[fatal] job name too long ({len(job)}): {job}")
            npart = config.split("-n")[1].split("-")[0]
            variant = config.rsplit("-", 1)[1]
            text = TEMPLATE.format(job=job, leaf=leaf_of(config, seed),
                                   config=config, seed=seed, stage=stage,
                                   npart=npart, variant=variant)
            with open(os.path.join(HERE, f"{job}.yaml"), "w") as f:
                f.write(text)
            names.append(job)
            print(f"wrote {job}.yaml  [{stage}]")
        by_stage[stage] = names

    lists = "\n".join(f'{s}=({" ".join(j)})' for s, j in by_stage.items())
    sh = os.path.join(HERE, "launch_r14.sh")
    with open(sh, "w") as f:
        f.write(f"""#!/usr/bin/env bash
# Round 14 — L1-realistic (N,3) inputs, constituent-count sweep (decisions.md 2026-08-01).
#
#   stage1  N in {{8,16,32,64}} x fp32/w8a8/w1a8 x s1-3  (36 jobs: baselines + thesis)
#   stage2  N in {{8,16,32,64}} x w1a6/w1a4     x s1-3  (24 jobs: activation ladder)
#
# PREREQS: ConfigMap kai-bn14-code built from code/hgq2 INCLUDING the r14 configs and
# the feature-subset plumbing (make_code_configmap_r14.sh; jobs hard-fail on a stale
# one). Staged in waves of 6.
#
# Usage: ./launch_r14.sh stage1 | stage2 | delete
set -euo pipefail
CTX="nautilus"; NS="cms-ml"; HERE="$(cd "$(dirname "$0")" && pwd)"
{lists}
ALL=("${{stage1[@]}}" "${{stage2[@]}}")
CMD="${{1:-}}"
if [ "$CMD" = "delete" ]; then
  for j in "${{ALL[@]}}"; do kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found; done
  exit 0
fi
case "$CMD" in
  stage1)  JOBS=("${{stage1[@]}}") ;;
  stage2)  JOBS=("${{stage2[@]}}") ;;
  *) echo "usage: $0 stage1|stage2|delete"; exit 2 ;;
esac
wait_for_wave() {{
  local jobs=("$@")
  while true; do
    local pending=0
    for j in "${{jobs[@]}}"; do
      local done_n
      done_n=$(kubectl --context "$CTX" -n "$NS" get job "$j" \\
        -o jsonpath='{{.status.succeeded}}{{.status.failed}}' 2>/dev/null || true)
      [ -n "$done_n" ] || pending=$((pending+1))
    done
    [ "$pending" -eq 0 ] && break
    echo "  ... $pending/${{#jobs[@]}} still running"; sleep 120
  done
}}
wave=()
for j in "${{JOBS[@]}}"; do
  kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found >/dev/null 2>&1 || true
  kubectl --context "$CTX" -n "$NS" apply -f "$HERE/$j.yaml"
  wave+=("$j")
  if [ "${{#wave[@]}}" -ge 6 ]; then
    echo "=== wave of ${{#wave[@]}} launched; waiting ==="
    wait_for_wave "${{wave[@]}}"; wave=()
  fi
done
[ "${{#wave[@]}}" -gt 0 ] && {{ echo "=== final wave of ${{#wave[@]}} ==="; wait_for_wave "${{wave[@]}}"; }}
echo; echo "=== round-14 $CMD complete (${{#JOBS[@]}} jobs) ==="
kubectl --context "$CTX" -n "$NS" get jobs -l bn14stage="$CMD"
""")
    os.chmod(sh, 0o755)
    total = sum(len(v) for v in by_stage.values())
    print(f"wrote launch_r14.sh  ({total} jobs across {len(by_stage)} stages)")


if __name__ == "__main__":
    emit()
