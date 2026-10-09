#!/usr/bin/env python3
"""Round-15 GAMMA ROC-eval job YAMLs — CPU-only, one Job per softmax-grid arm (sm4i0, sm6i0).
Clone of gen_r14_roc_jobs.py: ConfigMap kai-bn14-roc-code (roc_final.py unchanged since
2026-08-03), VAL split from Zenodo (n=260,000 asserted), checkpoints artifact-first from W&B
(model-r15-gamma-<arm>-n8-w1a8-s<seed>), --run-prefix r15-gamma-<arm>-n8 --variants w1a8 so
roc_final.py's <prefix>-<variant>-s<seed> contract resolves the new run names. Control = the
existing roc-results/r14/n8/W1A8-s{1,2,3}.npz. NOTHING here launches anything.
Usage: python gen_r15_gamma_roc_jobs.py
"""
from __future__ import annotations
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["sm4i0", "sm6i0"]

TEMPLATE = """apiVersion: batch/v1
kind: Job
metadata:
  name: {job}
  labels:
    app: bnjet-r15-roc
    bn15roc: "{arm}"
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 14400
  template:
    metadata:
      labels:
        app: bnjet-r15-roc
        bn15roc: "{arm}"
    spec:
      restartPolicy: Never
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/arch
                operator: In
                values: [amd64]
      containers:
      - name: roc
        image: python:3.12
        command: ["bash", "-c"]
        args:
        - |
          set -eo pipefail
          export KERAS_BACKEND=tensorflow MPLBACKEND=Agg CUDA_VISIBLE_DEVICES=""
          mkdir -p /work/code /work/data /work/out
          CODE=/work/code
          echo "[code] $(date) unpack ConfigMap kai-bn14-roc-code"
          tar -xzf /cmcode/hgq2.tar.gz -C "$CODE" --strip-components=1
          md5sum /cmcode/hgq2.tar.gz | awk '{{print "[code] configmap tar md5:", $1}}'
          # stale gate: this eval NEEDS the r14 eval-side plumbing
          grep -q "def feature_indices" "$CODE/bnhgq2/data.py" || {{ echo "[fatal] stale CM: no feature_indices"; exit 1; }}
          grep -q "wandb-log" "$CODE/roc_final.py" || {{ echo "[fatal] stale CM: roc_final.py lacks --wandb-log"; exit 1; }}
          grep -q "input_std applied from checkpoint" "$CODE/roc_final.py" || {{ echo "[fatal] stale CM: roc_final.py lacks per-model input_std"; exit 1; }}
          echo "[gate] roc-code ConfigMap is fresh"
          export PYTHONPATH="$CODE:$PYTHONPATH"
          echo "[setup] $(date) pinned deps (CPU tensorflow)"
          pip install -q --no-cache-dir "tensorflow-cpu==2.21.0" "keras==3.15.0" "hgq2==0.1.9" "quantizers==1.2.2" "scikit-learn==1.9.0" "h5py==3.14.0" "wandb==0.28.0" "hls4ml==1.3.0" "numpy==2.5.0" "matplotlib==3.10.0"
          echo "[data] $(date) fetch HLS4ML LHC Jet 150p VAL split from Zenodo (the ROC-test set)"
          python -u -c 'import urllib.request; urllib.request.urlretrieve("https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_val.tar.gz?download=1", "/work/data/val.tar.gz")'
          tar -xzf /work/data/val.tar.gz -C /work/data && rm -f /work/data/val.tar.gz
          DATA=$(dirname "$(find /work/data -name 'jetImage_*.h5' -print -quit)")
          [ -n "$DATA" ] || {{ echo "[fatal] no jetImage_*.h5 after extract"; exit 1; }}
          echo "[data] DATA=$DATA ($(ls "$DATA" | wc -l) files)"
          export WANDB_PROJECT=BNJetTagAug
          export WANDB_ENTITY=kayamaguchi-uc-san-diego
          export WANDB_GROUP=r15-gamma
          export WANDB_TAGS=r15,gamma,l1x3,eval,n{n},{arm}
          echo "[roc] $(date) eval-all R15 GAMMA {arm} N={n} (3 models, checkpoints artifact-first from W&B)"
          cd "$CODE"
          python -u "$CODE/roc_final.py" eval-all \\
            --data "$DATA" --out /work/out --expect-n 260000 \\
            --n-part {n} --features pt,etarel,phirel \\
            --ckpt-source wandb --run-prefix r15-gamma-{arm}-n{n} \\
            --variants w1a8 --seeds 1,2,3 --wandb-log \\
            --title "R15 GAMMA {arm} BitNet jet tagger - ROC (l1x3, N={n}, softmax grid arm)" \\
            --table-title "# ROUND 15 GAMMA {arm} (l1x3, N={n}) - ROC-test AUC (W1A8 + softmax_out grid {arm})" \\
            --table-source "# source : recomputed from roc-results/r15-gamma/{arm}/*.npz (y, score)"
          n_npz=$(ls /work/out/*.npz | wc -l)
          echo "[done] $(date) {arm} N={n}: $n_npz npz produced (durable copy = evaluation-r15-gamma-{arm}-n{n} artifact)"
          [ "$n_npz" = "3" ] || {{ echo "[fatal] expected 3 npz, got $n_npz"; exit 1; }}
        env:
        - name: WANDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: kai-wandb
              key: WANDB_API_KEY
        resources:
          limits:
            cpu: "4"
            memory: 8Gi
            ephemeral-storage: 20Gi
          requests:
            cpu: "4"
            memory: 8Gi
            ephemeral-storage: 20Gi
        volumeMounts:
        - name: cmcode
          mountPath: /cmcode
        - name: work
          mountPath: /work
      volumes:
      - name: cmcode
        configMap:
          name: kai-bn14-roc-code
      - name: work
        emptyDir:
          sizeLimit: 20Gi
"""


if __name__ == "__main__":
    for arm in ARMS:
        job = f"kai-bn15-roc-{arm}"
        with open(os.path.join(HERE, f"{job}.yaml"), "w") as f:
            f.write(TEMPLATE.format(job=job, n=8, arm=arm))
        print(f"wrote {job}.yaml")
