#!/usr/bin/env python3
"""Round-13 job YAMLs — binary weights under EBOPs pressure (R13-DESIGN.md).

Emits one NRP Job per (config, seed) from the r13 configs written by
`code/hgq2/configs/gen_r13.py`.  Structure is the round-11/12 YAML verbatim except:

  * round label / ConfigMap `kai-bn13-code` (one ConfigMap per round, r11/r12 stay frozen);
  * the stale-ConfigMap gate additionally requires `bnhgq2/train.py` to expose
    `ebops_callbacks` — an r11-vintage tree would run the r13 config with the EBOPs
    callbacks SILENTLY ABSENT, i.e. produce a beta = 0 run labelled as a pressured one,
    which is exactly the confound the round exists to measure;
  * `activeDeadlineSeconds: 36000` (10 h) — 1500 epochs + 1500 validation passes do not
    fit r11/r12's 4 h (memo §6 infra note).  `backoffLimit: 2` is unchanged.

Run set (memo §8), staged so the go/no-go gate comes first:
  Stage 0   4 LR probes  (A1 recipe, beta = 0, 300 epochs, seed 1)
  Stage 0b  1 sighter    (A1 verbatim, seed 1) -- does the front ever cross 5e5 EBOPs
  Stage 1   A1, A2       x seeds 1,2,3         -- the headline comparison
  Stage 2   A3, A4       x seeds 1,2,3         -- the confound controls (F3, F4)
= 17 jobs.  `launch_r13.sh <stage>` launches ONE stage at a time on purpose: Stage 1 must
not start before the Stage-0 LR winner has been pinned into the configs
(`gen_r13.py --lr <winner>`) and Stage 0b has been inspected.

NOTHING here launches anything; this only writes files.

Usage (from code/jobs/training/variants/):
    python gen_r13_jobs.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "hgq2", "configs"))

STAGES = {
    "stage0": [(f"r13-lrprobe-w1-freeact-lr{t}", 1)
               for t in ("2e5", "5e5", "1e4", "2e4")],
    "stage0b": [("r13-sighter-w1-freeact-beta", 1)],
    "stage1": ([("r13-small-w1-freeact-beta", s) for s in (1, 2, 3)]
               + [("r13-small-wq-freeact-beta", s) for s in (1, 2, 3)]),
    "stage2": ([("r13-small-w1-freeact-beta0", s) for s in (1, 2, 3)]
               + [("r13-small-w1-fixa8-beta0", s) for s in (1, 2, 3)]),
}

TEMPLATE = """apiVersion: batch/v1
kind: Job
metadata:
  name: {job}
  labels:
    app: bnjet-r13
    bn13: "{leaf}"
    bn13stage: "{stage}"
spec:
  # backoffLimit 2: an UnexpectedAdmissionError (node GPU device-plugin race, zero side
  # effects) must not kill the Job. Duplicate-W&B-run risk from a mid-train retry is
  # accepted (the ROC fetcher prefers the finished run if duplicates appear).
  backoffLimit: 2
  # 10 h: 1500 epochs at batch 1024 (~727k steps) plus 1500 validation passes. r11/r12's
  # 4 h is a round-13 hard failure (R13-DESIGN.md section 6).
  activeDeadlineSeconds: 36000
  template:
    metadata:
      labels:
        app: bnjet-r13
        bn13: "{leaf}"
        bn13stage: "{stage}"
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
          # PREFER the abundant mid-tier (A10/L4/2080-Ti/V100/A40/A5000/3090) — plentiful and
          # more than enough for a 19,201-param model. De-prefer A100s, flagship = last resort.
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
          echo "[code] $(date) unpack code from ConfigMap kai-bn13-code (PVC-free)"
          tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1
          md5sum /cmcode/hgq2.tar.gz | awk '{{print "[code] configmap tar md5:", $1}}'
          # ---- STALE-CONFIGMAP GATE: round 13 REQUIRES its own configs AND the EBOPs
          # callback plumbing. An r11-vintage bnhgq2 would run this config with the beta
          # schedule / FreeEBOPs / ParetoFront SILENTLY ABSENT — a beta=0 run mislabelled
          # as a pressured one, which would invalidate the whole comparison. ----
          [ -f "$CODE/configs/{config}.json" ] || {{
            echo "[fatal] unpacked code lacks configs/{config}.json -> ConfigMap kai-bn13-code is STALE."
            echo "[fatal] rebuild it (make_code_configmap_r13.sh) and re-apply."
            exit 1
          }}
          grep -q "def ebops_callbacks" "$CODE/bnhgq2/train.py" || {{
            echo "[fatal] bnhgq2/train.py has no ebops_callbacks -> ConfigMap kai-bn13-code is STALE."
            exit 1
          }}
          grep -q "_free_act" "$CODE/bnhgq2/qat.py" || {{
            echo "[fatal] bnhgq2/qat.py has no _free_act (learnable act bitwidths) -> STALE ConfigMap."
            exit 1
          }}
          echo "[gate] configs/{config}.json + ebops_callbacks + _free_act present (ConfigMap kai-bn13-code is fresh)"
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
          export WANDB_PROJECT=bnjettag-final
          export WANDB_RUN_NAME={leaf}
          # W&B layout (2026-08-01): entity explicit, runs grouped per round/stage,
          # tagged for UI filtering. bnhgq2.wandb_util reads these at init.
          export WANDB_ENTITY=kayamaguchi-uc-san-diego
          export WANDB_GROUP=r13-{stage}
          export WANDB_TAGS=r13,{stage},{config}
          # ---- ROUND 13 ({stage}): binary weights under HGQ2 EBOPs pressure. Selection is
          # PRE-REGISTERED (R13-DESIGN.md section 5): from the stored Pareto front, the
          # admitted point (ebops <= 5e5) with the highest val macro-OvR AUC; ties -> lower
          # EBOPs -> earlier epoch. The front (and its selected point) is uploaded to W&B
          # under a size-exact durability gate — the pod is emptyDir-only. ----
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
          # RIGHT-SIZED (decisions.md 2026-07-13): deployable-scale jobs are data-bound, not
          # FLOP-bound. 2 cpu / 8Gi mem / 16Gi eph (tarball 2.7 GB deleted post-extract +
          # extracted h5 + pip wheels). The Pareto front adds at most a few tens of MB of
          # .keras files (19,201 params each). requests==limits.
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
          name: kai-bn13-code
      - name: work
        emptyDir:
          sizeLimit: 16Gi
"""


def leaf_of(config: str, seed: int) -> str:
    return f"{config}-s{seed}"


def job_of(config: str, seed: int) -> str:
    # k8s names: lowercase alnum + '-', <= 63 chars. The config names already comply.
    return f"kai-bn13-{config.removeprefix('r13-')}-s{seed}"


def emit() -> None:
    by_stage: dict[str, list[str]] = {}
    for stage, runs in STAGES.items():
        names = []
        for config, seed in runs:
            if not os.path.exists(os.path.join(CONFIGS, f"{config}.json")):
                sys.exit(f"[fatal] missing config {config}.json — run gen_r13.py first")
            job = job_of(config, seed)
            if len(job) > 63:
                sys.exit(f"[fatal] job name too long ({len(job)}): {job}")
            text = TEMPLATE.format(job=job, leaf=leaf_of(config, seed),
                                   config=config, seed=seed, stage=stage)
            with open(os.path.join(HERE, f"{job}.yaml"), "w") as f:
                f.write(text)
            names.append(job)
            print(f"wrote {job}.yaml  [{stage}]")
        by_stage[stage] = names

    lists = "\n".join(f'{s}=({" ".join(j)})' for s, j in by_stage.items())
    sh = os.path.join(HERE, "launch_r13.sh")
    with open(sh, "w") as f:
        f.write(f"""#!/usr/bin/env bash
# Round 13 — binary weights under EBOPs pressure (code/hgq2/R13-DESIGN.md).
#
# ONE STAGE AT A TIME, ON PURPOSE:
#   stage0   4 LR probes (A1 recipe, beta=0, 300 ep). Winner rule: best epoch INSIDE the
#            budget, then highest val macro AUC, ties -> lower LR. Pin it with
#            `python ../../../hgq2/configs/gen_r13.py --lr <winner>` and RE-RUN
#            gen_r13_jobs.py before stage0b/1/2.
#   stage0b  the beta sighter (A1, seed 1, full 1500-epoch schedule) = the GO/NO-GO:
#            does the front ever cross 5e5 EBOPs? If not, the terminal beta is revised
#            AND LOGGED before stage1 — never mid-campaign.
#   stage1   A1 + A2 x seeds 1,2,3   (the headline comparison)
#   stage2   A3 + A4 x seeds 1,2,3   (the confound controls F3 / F4)
#
# PREREQS: ConfigMap kai-bn13-code built from code/hgq2 INCLUDING the r13 configs and the
# EBOPs-callback plumbing (make_code_configmap_r13.sh; the jobs hard-fail on a stale one),
# AND preflight_r13.sh printing PREFLIGHT_ALL_PASS. Staged in waves of 5 (r7 precedent).
#
# Usage: ./launch_r13.sh stage0 | stage0b | stage1 | stage2 | delete
set -euo pipefail
CTX="nautilus"; NS="cms-ml"; HERE="$(cd "$(dirname "$0")" && pwd)"
{lists}
ALL=("${{stage0[@]}}" "${{stage0b[@]}}" "${{stage1[@]}}" "${{stage2[@]}}")
CMD="${{1:-}}"
if [ "$CMD" = "delete" ]; then
  for j in "${{ALL[@]}}"; do kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found; done
  exit 0
fi
case "$CMD" in
  stage0)  JOBS=("${{stage0[@]}}") ;;
  stage0b) JOBS=("${{stage0b[@]}}") ;;
  stage1)  JOBS=("${{stage1[@]}}") ;;
  stage2)  JOBS=("${{stage2[@]}}") ;;
  *) echo "usage: $0 stage0|stage0b|stage1|stage2|delete"; exit 2 ;;
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
  if [ "${{#wave[@]}}" -ge 5 ]; then
    echo "=== wave of ${{#wave[@]}} launched; waiting ==="
    wait_for_wave "${{wave[@]}}"; wave=()
  fi
done
[ "${{#wave[@]}}" -gt 0 ] && {{ echo "=== final wave of ${{#wave[@]}} ==="; wait_for_wave "${{wave[@]}}"; }}
echo; echo "=== round-13 $CMD complete (${{#JOBS[@]}} jobs) ==="
kubectl --context "$CTX" -n "$NS" get jobs -l bn13stage="$CMD"
""")
    os.chmod(sh, 0o755)
    total = sum(len(v) for v in by_stage.values())
    print(f"wrote launch_r13.sh  ({total} jobs across {len(by_stage)} stages)")


if __name__ == "__main__":
    emit()
