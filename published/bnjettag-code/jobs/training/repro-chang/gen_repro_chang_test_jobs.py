#!/usr/bin/env python3
"""Generate repro-chang EVAL jobs (CPU-only): run_test.py software pass per finished run.

Fetches the run's Pareto artifact from W&B, builds the jsc150 dataset in-pod, runs
upstream run_test.py with --no-hw-test (keras_metric + comb_metric per checkpoint;
RTL/hw and synthesis happen later on mulder), uploads the metadata.json tree as
evaluation-repro-chang-<model>-n<N>. Cluster CPU eval per the 2026-08-03 standing rule.

Usage: gen_repro_chang_test_jobs.py [model-nN ...]  (default: all 8)
"""

import sys
from pathlib import Path

RUNS = sys.argv[1:] or [f'{m}-n{n}' for m in ('xfm', 'xfmt') for n in (8, 16, 32, 64)]
EXAMPLES_SHA = '6cdc6e3'
HGQ2_SHA = '88ddffde25e8f855c9534015863fa07b269d0b60'

TEMPLATE = """\
apiVersion: batch/v1
kind: Job
metadata:
  name: kai-repro-chang-test-{run}
  labels:
    app: bnjet-repro-chang-test
    reprochang: "test-{run}"
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 86400
  template:
    metadata:
      labels:
        app: bnjet-repro-chang-test
        reprochang: "test-{run}"
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
              - key: kubernetes.io/hostname
                operator: NotIn
                values: [hcc-chase-shor-c4705.unl.edu]
      containers:
      - name: test
        image: python:3.12
        command: ["bash", "-c"]
        args:
        - |
          set -eo pipefail
          export KERAS_BACKEND=jax JAX_PLATFORM_NAME=cpu
          mkdir -p /work/data /work/ckpt /work/out
          echo "[code] $(date) clone HGQ2-examples pinned at {examples_sha}"
          git clone https://github.com/calad0i/HGQ2-examples /work/HGQ2-examples
          git -C /work/HGQ2-examples checkout {examples_sha}
          echo "[setup] $(date) pinned deps (requirements-repro.txt stack, CPU jax)"
          pip install -q --no-cache-dir "jax==0.11.0" "keras==3.14.0" \\
            "git+https://github.com/calad0i/HGQ2@{hgq2_sha}" \\
            "da4ml==0.6.0" "alkaid==0.7.1" \\
            "quantizers>=1.2" "h5py==3.15.1" "tqdm==4.70.0" "wandb==0.28.0" "numpy<2.6"
          echo "[ckpt] $(date) fetch Pareto artifact kai-repro-chang-{run}-pareto:latest"
          python3 - <<'EOF'
          import wandb
          api = wandb.Api()
          art = api.artifact('kayamaguchi-uc-san-diego/bnjettag-bitnet/kai-repro-chang-{run}-pareto:latest')
          art.download(root='/work/ckpt')
          EOF
          n_ckpt=$(ls /work/ckpt/*.keras | wc -l); echo "[ckpt] $n_ckpt checkpoints"
          [ "$n_ckpt" -ge 1 ] || {{ echo "[fatal] no checkpoints"; exit 1; }}
          echo "[data] $(date) Zenodo 3602260 150p train+val"
          cd /work/data
          curl -sSL -o train.tar.gz "https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_train.tar.gz?download=1"
          sz=$(stat -c %s train.tar.gz); [ "$sz" -gt 2500000000 ] || {{ echo "[fatal] train tarball too small ($sz)"; exit 1; }}
          curl -sSL -o val.tar.gz "https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_val.tar.gz?download=1"
          tar -xzf train.tar.gz && rm -f train.tar.gz
          tar -xzf val.tar.gz && rm -f val.tar.gz
          python3 /work/HGQ2-examples/jsc150/tools/prepare_data.py -i ./train/ -o 150c-train.h5 -j 4
          python3 /work/HGQ2-examples/jsc150/tools/prepare_data.py -i ./val/ -o 150c-test.h5 -j 4
          rm -rf ./train/ ./val/
          export WANDB_PROJECT=bnjettag-bitnet
          export WANDB_ENTITY=kayamaguchi-uc-san-diego
          export WANDB_NAME=repro-chang-test-{run}
          export WANDB_RUN_GROUP=repro-chang
          export WANDB_TAGS=repro-chang,jsc150,test,{run}
          upload() {{
            echo "[wandb] $(date) uploading eval outputs"
            find /work/out -name '*.keras' -delete  # traced models are re-derivable; keep the artifact small
            python3 - <<'EOF'
          import wandb
          run = wandb.init(job_type='repro-chang-test')
          art = wandb.Artifact('evaluation-repro-chang-{run}', type='evaluation')
          art.add_dir('/work/out')
          run.log_artifact(art).wait()
          run.finish()
          EOF
          }}
          trap upload EXIT
          echo "[test] $(date) run_test.py {run} --no-hw-test (keras + comb metrics)"
          cd /work/HGQ2-examples/jsc150
          python -u run_test.py -i /work/ckpt -o /work/out -d /work/data -n {n} -f {f} \\
            --no-hw-test -j 1 2>&1 | tee /work/out/test.log
          echo "[done] $(date) test {run}"
        env:
        - name: WANDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: kai-wandb
              key: WANDB_API_KEY
        resources:
          limits:
            cpu: "8"
            memory: 160Gi
            ephemeral-storage: 40Gi
          requests:
            cpu: "8"
            memory: 160Gi
            ephemeral-storage: 40Gi
        volumeMounts:
        - name: work
          mountPath: /work
      volumes:
      - name: work
        emptyDir:
          sizeLimit: 40Gi
"""

here = Path(__file__).parent
for run in RUNS:
    model, n = run.rsplit('-n', 1)
    assert model in ('xfm', 'xfmt') and n.isdigit(), run
    (here / f'kai-repro-chang-test-{run}.yaml').write_text(
        TEMPLATE.format(run=run, n=int(n), f=3, examples_sha=EXAMPLES_SHA, hgq2_sha=HGQ2_SHA))
    print('wrote', f'kai-repro-chang-test-{run}.yaml')
