#!/usr/bin/env python3
"""Round-15 GAMMA job YAMLs — the softmax-output-grid arms at N = 8 (experiment-log 2026-08-23).

One NRP Job per (config, seed). YAML = the round-14 training YAML verbatim except:
  * ConfigMap **kai-bn15-code** (built by make_code_configmap_r15.sh from the CURRENT tree,
    which carries the Job-Beta knob in bnhgq2/qat.py; the stale gate checks for it);
  * labels app bnjet-r15 / bn15 / bn15stage; W&B project BNJetTagAug, group r15-gamma,
    tags r15,gamma,l1x3,<stage>,n8,w1a8.
Run set: stage "gamma" = {r15-gamma-sm4i0-n8-w1a8, r15-gamma-sm6i0-n8-w1a8} x seeds 1-3
= 6 jobs. Control = existing r14-l1x3-n8-w1a8 s1-3 (no retrain: knob-absent code path is
byte-identical, fingerprint gate 2026-08-19).
NOTHING here launches anything. Usage: python gen_r15_gamma_jobs.py
"""
from __future__ import annotations
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "hgq2", "configs"))
SEEDS = [1, 2, 3]
STAGES = {"gamma": [(f"r15-gamma-{arm}-n8-w1a8", s) for arm in ("sm4i0", "sm6i0") for s in SEEDS]}

TEMPLATE = """apiVersion: batch/v1
kind: Job
metadata:
  name: {job}
  labels:
    app: bnjet-r15
    bn15: "{leaf}"
    bn15stage: "{stage}"
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
        app: bnjet-r15
        bn15: "{leaf}"
        bn15stage: "{stage}"
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
          echo "[code] $(date) unpack code from ConfigMap kai-bn15-code (PVC-free)"
          tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1
          md5sum /cmcode/hgq2.tar.gz | awk '{{print "[code] configmap tar md5:", $1}}'
          # ---- STALE-CONFIGMAP GATE: round 14 REQUIRES the L1-realistic feature-subset
          # plumbing. A pre-r14 bnhgq2 would run this config on ALL 16 features — the
          # exact confound this round removes — or crash late. Fail fast instead. ----
          [ -f "$CODE/configs/{config}.json" ] || {{
            echo "[fatal] unpacked code lacks configs/{config}.json -> ConfigMap kai-bn15-code is STALE."
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
          grep -q "softmax_out_bits" "$CODE/bnhgq2/qat.py" || {{
            echo "[fatal] bnhgq2/qat.py lacks quant.softmax_out_bits (Job Beta knob) -> STALE ConfigMap kai-bn15-code."
            exit 1
          }}
          echo "[gate] configs/{config}.json + feature_indices + wandb_util present (ConfigMap kai-bn15-code is fresh)"
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
          export WANDB_GROUP=r15-gamma
          export WANDB_TAGS=r15,gamma,l1x3,{stage},n{npart},{variant}
          # ---- ROUND 15 GAMMA ({stage}): r14-l1x3-n8-w1a8 recipe VERBATIM + quant.softmax_out_bits/softmax_out_i
          # (the ctx-einsum softmax operand grid). Control = the R14 W1A8 n8 checkpoints. ----
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
          name: kai-bn15-code
      - name: work
        emptyDir:
          sizeLimit: 16Gi
"""



def leaf_of(config, seed):
    return f"{config}-s{seed}"


def job_of(config, seed):
    return f"kai-bn15-{config.removeprefix('r15-')}-s{seed}"


def emit():
    names = []
    for stage, runs in STAGES.items():
        for config, seed in runs:
            if not os.path.exists(os.path.join(CONFIGS, f"{config}.json")):
                sys.exit(f"[fatal] missing config {config}.json — run configs/gen_r15_gamma.py first")
            job = job_of(config, seed)
            assert len(job) <= 63, job
            text = TEMPLATE.format(job=job, leaf=leaf_of(config, seed), config=config, seed=seed,
                                   stage=stage, npart="8", variant="w1a8")
            with open(os.path.join(HERE, f"{job}.yaml"), "w") as f:
                f.write(text)
            names.append(job); print(f"wrote {job}.yaml  [{stage}]")
    with open(os.path.join(HERE, "launch_r15_gamma.sh"), "w") as f:
        f.write("#!/usr/bin/env bash\n# Round-15 GAMMA: 6 jobs (sm4i0/sm6i0 x s1-3), all at once (scheduler self-limits).\n"
                "# PREREQ: ConfigMap kai-bn15-code (make_code_configmap_r15.sh). Usage: ./launch_r15_gamma.sh [delete]\n"
                "set -euo pipefail\nCTX=nautilus; NS=cms-ml; HERE=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
                f"JOBS=({' '.join(names)})\n"
                "if [ \"${1:-}\" = delete ]; then for j in \"${JOBS[@]}\"; do kubectl --context $CTX -n $NS delete job $j --ignore-not-found; done; exit 0; fi\n"
                "for j in \"${JOBS[@]}\"; do kubectl --context $CTX -n $NS apply -f \"$HERE/$j.yaml\"; done\n"
                "kubectl --context $CTX -n $NS get jobs -l app=bnjet-r15\n")
    os.chmod(os.path.join(HERE, "launch_r15_gamma.sh"), 0o755)
    print(f"wrote launch_r15_gamma.sh ({len(names)} jobs)")


if __name__ == "__main__":
    emit()
