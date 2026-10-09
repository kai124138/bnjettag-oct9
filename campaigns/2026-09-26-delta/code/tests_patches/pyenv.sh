#!/usr/bin/env bash
# Run python in the pinned CPU environment (pins = bundle requirements-cpu.txt minus
# wandb, which no test here imports). HGQ2_WHEEL may point at a local copy of the
# PyPI wheel (sha256 749754214b97f2531e1f8e609308755fe857064f47d350e9ffb878fb5017c43c).
set -euo pipefail
HGQ=${HGQ2_WHEEL:-hgq2==0.1.9}
export KERAS_BACKEND=tensorflow TF_CPP_MIN_LOG_LEVEL=2 CUDA_VISIBLE_DEVICES=""
export TF_NUM_INTRAOP_THREADS=${TF_NUM_INTRAOP_THREADS:-1} TF_NUM_INTEROP_THREADS=${TF_NUM_INTEROP_THREADS:-1}
export TF_DETERMINISTIC_OPS=1 PYTHONHASHSEED=0
exec uv run --quiet --no-project --python 3.12 \
  --with tensorflow==2.21.0 --with keras==3.15.0 --with "$HGQ" --with quantizers==1.2.2 \
  --with numpy==2.5.0 --with scikit-learn==1.9.0 --with h5py==3.14.0 --with hls4ml==1.3.0 python "$@"
