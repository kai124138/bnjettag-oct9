# Compute inventory — 2026-09-16

Read-only inspection; no remote workloads launched, stopped, or modified.

## NRP Nautilus

- Namespace `cms-ml`; network access succeeds with sandbox escalation. Initial sandbox DNS failure was not an infrastructure outage.
- Existing runtime: `kai-ebops-abl-0912-e1000-6-rbzb8`, image `python:3.12`, code `/work/code`, Python `/usr/local/bin/python`.
- R6 has 4 CPU, 12 GiB RAM, and one NVIDIA L40 allocated. One instantaneous sample showed 0% GPU utilization and 969 MiB GPU memory; it is insufficient to establish sustained utilization.
- R0–R5 completed; R6 at resumable checkpoint `epoch-0898` when inspected. Do not contend with its training process for evaluation.
- A100 quota requests 6/24; H100/H200/GH200 quotas zero; namespace pod usage 27/200. Availability is not a scheduling guarantee.
- Existing immutable code ConfigMap: `kai-ebops-abl-code-64d7fd909b`. Archive sha256: `64d7fd909bd71c731f882bc3344e69c055d7abed10087a460c767787882e063c`.
- Persistent volume claim `kai-data`; experiment root `/data/ebops-n8-20260912-ablation`.
- Dataset cache under `data/`: x_train 46 MB, y_train 9.5 MB, x_val 12 MB, y_val 2.4 MB. Train/internal-validation sizes 496,000/124,000; standardization computed from train only.
- Held-out raw data `/data/hls4ml_lhc_jet/val/val` contains 260,000 jets.
- `evaluation/` has only categorical-accuracy JSON and Markdown from September 15, no logits/prediction arrays.
- Each `runs/<arm>/model_best.keras` is under 0.75 MB. R0–R5 have final `ebops_budget.json` selection metadata.
- R4 now has a feasible checkpoint: epoch 959 zero-based, validation macro AUC 0.8476823303826355, EBOPs 349550. Previous accuracy report omitted it because it was not yet available.
- R6 best remains epoch 183 zero-based, AUC 0.8419752161356773, EBOPs 348366. Read `latest.json` once and use `checkpoints/<checkpoint>/model_best.keras` together with its `state.json` for internally consistent snapshots.

Recommended diagnostic allocation: one bounded CPU Job, 4 CPU / 8 GiB RAM / 16 GiB temporary storage, 30-minute deadline, no GPU; use the existing ConfigMap and PVC. Set `CUDA_VISIBLE_DEVICES=-1`, `TF_NUM_INTRAOP_THREADS=4`, `TF_NUM_INTEROP_THREADS=2`, `OMP_NUM_THREADS=4`, `WANDB_MODE=offline`. Existing compatible package versions are TensorFlow 2.21.0, Keras 3.15.0, hgq2 0.1.9, quantizers 1.2.2, h5py 3.14.0, hls4ml 1.3.0, NumPy 2.5.0. Export logits once for all seven selected checkpoints; run calibration and statistical analyses against saved arrays locally.

## Mulder

SSH `mulder` succeeded. Live load average 1.00/1.15/1.34; 117 GiB RAM available. Documented hardware: 64 logical CPUs, 32 physical cores, 125 GiB RAM. Another user's simulation uses about one core. No `nvidia-smi` executable found.

NFS home is 99% full, with 747 GB available. Legacy project exists at `/home/users/kayamaguchi/bnjettagfastml`; no current EBOP checkpoint cache or compatible venv found in the bounded directory inspection. Suitable for eventual Vitis synthesis, but moving inference here would add setup and transfer cost without improving this first diagnostic. Do not synthesize until a validated model/output change exists.

## Local artifacts

`baseline_accuracy_20260915.json` is the unchanged existing remote report copied locally. Its selected-validation AUC is not held-out AUC. Its R3/R6 status reflects September 15 snapshots; R3 has since completed and R4 is now feasible.

## Independent Mulder numerical verification

Subsequent targeted inspection found existing Python 3.10.10 and NumPy 1.26.4 in `/home/users/kayamaguchi/micromamba/envs/bnjet`. Executed `mulder_numerical_crosscheck.py` through SSH stdin with `timeout 30s` and one BLAS/OpenMP thread. No installation, remote files, or model inference was required. Result `mulder_numerical_crosscheck.json` records host and UTC time. Total wall time was 11.98 seconds including imports and arithmetic benchmarks.

Five-class synthetic data demonstrated raw-logit one-versus-rest AUC 1.0 with top-1 accuracy 20%, and class-bias correction raised accuracy to 100% while preserving raw-logit AUC. This is a mathematical mechanism check, not evidence that class offsets explain the trained model's gap. Positive scalar temperatures 0.1, 0.5, 1, 2, and 10 preserved argmax, including after softmax.

Warm NumPy float32 arithmetic benchmark at batch size 4096, 2000 repetitions: five class-bias additions cost 0.00928 microseconds per jet; five scales plus five biases cost 0.01826 microseconds per jet. These are vectorized CPU throughput measurements excluding model inference and argmax; they do not establish single-event latency or FPGA resources/latency.
