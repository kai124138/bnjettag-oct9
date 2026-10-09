#!/usr/bin/env python3
"""Round-12 KD job YAMLs — the lambda sweep, paired seeds (post-dossier design).

SUPERSEDES the pre-dossier draft `gen_r12_jobs.py` (LR-probe run set, 5 jobs),
which is kept untouched for the record but must NOT be run for this round (its
emit() would also overwrite launch_r12.sh).  This generator emits the
pre-registered run set only:

    kai-bn12-distill-l{50,90,100}-s{1,2,3}   (9 jobs)

from the configs written by `code/hgq2/configs/gen_r12_distill_lambda.py`.
Seeds 1/2/3 are the SAME seeds as the r8-small-w1a8-stdnn baselines (and every
r11 arm), so every KD-vs-baseline comparison is paired: bnhgq2 derives both the
train/val split (np.random.default_rng(seed)) and the student init
(keras.utils.set_random_seed) from the seed, and distill_r12.py replicates that
flow exactly.  The +0.005 AUC target is smaller than the 0.0067 one-seed spread,
so pairing is load-bearing, not a nicety (see R12-PREFLIGHT.md).

The d64-teacher fallback config (r12-distill-d32-w1a8-t64) is deliberately NOT
in the run set — it exists ready-made for a follow-up decision, not for launch.

Structure is the round-11 YAML verbatim except: round label/name, ConfigMap
kai-bn12-code (one ConfigMap per round; kai-bn11-code stays frozen), the
stale-ConfigMap gate (requires the r12 config AND distill_r12.py in the unpacked
tree), the entrypoint (distill_r12.py — the KD loss routes teacher logits
through fit), and BNHGQ2_TEACHER_DIR=/work/teacher (PVC-free: distill_r12.py
fetches the pre-registered d128 teacher checkpoint from W&B by run name using
the pod's WANDB_API_KEY; availability verified read-only 2026-07-26).

Usage (from code/jobs/training/variants/):
    python gen_r12_lambda_jobs.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "hgq2", "configs"))

LAMBDA_TAGS = ("l50", "l90", "l100")
SEEDS = (1, 2, 3)  # paired with the r8-small-w1a8-stdnn / r11 baselines
RUNS = [(f"r12-distill-d32-w1a8-{t}", s) for t in LAMBDA_TAGS for s in SEEDS]

TEMPLATE = """apiVersion: batch/v1
kind: Job
metadata:
  name: {job}
  labels:
    app: bnjet-r12
    bn12: "{leaf}"
spec:
  # backoffLimit 2: an UnexpectedAdmissionError (node GPU device-plugin race, zero side
  # effects) must not kill the Job. Duplicate-W&B-run risk from a mid-train retry is
  # accepted (the ROC fetcher prefers the finished run if duplicates appear).
  backoffLimit: 2
  activeDeadlineSeconds: 14400
  template:
    metadata:
      labels:
        app: bnjet-r12
        bn12: "{leaf}"
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
          # more than enough for a <=300k-param model. De-prefer A100s, flagship = last resort.
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
          mkdir -p /work/code /work/data /work/outputs /work/teacher
          CODE=/work/code
          OUT=/work/outputs/{leaf}
          mkdir -p "$OUT"
          echo "[code] $(date) unpack code from ConfigMap kai-bn12-code (PVC-free)"
          tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1
          md5sum /cmcode/hgq2.tar.gz | awk '{{print "[code] configmap tar md5:", $1}}'
          # ---- STALE-CONFIGMAP GATE: round-12 REQUIRES its own KD config + trainer ----
          [ -f "$CODE/configs/{config}.json" ] && [ -f "$CODE/distill_r12.py" ] || {{
            echo "[fatal] unpacked code lacks configs/{config}.json or distill_r12.py -> ConfigMap kai-bn12-code is STALE."
            echo "[fatal] rebuild it (make_code_configmap_r12.sh) and re-apply."
            exit 1
          }}
          echo "[gate] configs/{config}.json + distill_r12.py present (ConfigMap kai-bn12-code is fresh)"
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
          export BNHGQ2_TEACHER_DIR=/work/teacher
          export WANDB_PROJECT=bnjettag-final
          export WANDB_RUN_NAME={leaf}
          # ---- ROUND-12 KD lambda sweep (W1.5, post-dossier): d32 flagship distilled from
          # r11-d128-w8a8-stdnn-s1 (best-val d128; fetched from W&B inside distill_r12.py,
          # PVC-free). Co-primary endpoints AUC + rejection@0.5; PROMOTE >= 0.8952 /
          # KILL <= 0.8922 ROC-test after the sweep. Seeds paired with r8 baselines. ----
          echo "[train] $(date) {leaf}  config={config}.json seed={seed}"
          cd "$CODE"
          python -u "$CODE/distill_r12.py" \\
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
          # extracted h5 + pip wheels; the d128 teacher checkpoint adds only ~4 MB and its
          # logits are precomputed once, so the r11 sizing carries over). requests==limits.
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
          name: kai-bn12-code
      - name: work
        emptyDir:
          sizeLimit: 16Gi
"""


def leaf_of(config: str, seed: int) -> str:
    return f"{config}-s{seed}"


def job_of(config: str, seed: int) -> str:
    # kai-bn12-distill-l50-s1 etc. (k8s: lowercase alnum + '-', <= 63 chars)
    tag = config.rsplit("-", 1)[1]          # l50 | l90 | l100
    return f"kai-bn12-distill-{tag}-s{seed}"


def emit() -> None:
    names = []
    for config, seed in RUNS:
        if not os.path.exists(os.path.join(CONFIGS, f"{config}.json")):
            sys.exit(f"[fatal] missing config {config}.json — run "
                     "gen_r12_distill_lambda.py first")
        job = job_of(config, seed)
        if len(job) > 63:
            sys.exit(f"[fatal] job name too long ({len(job)}): {job}")
        text = TEMPLATE.format(job=job, leaf=leaf_of(config, seed),
                               config=config, seed=seed)
        with open(os.path.join(HERE, f"{job}.yaml"), "w") as f:
            f.write(text)
        names.append(job)
        print(f"wrote {job}.yaml")
    print(f"{len(names)} jobs (launch with ./launch_r12.sh after preflight_r12.sh "
          "prints PREFLIGHT_ALL_PASS)")


if __name__ == "__main__":
    emit()
