#!/usr/bin/env bash
# Caller launches detached with setsid and redirects this wrapper's stdout/stderr.
set -euo pipefail
BNJET_WORKDIR="${BNJET_WORKDIR:-$HOME/bnjet_ebops_r4_20260917}"
mkdir -p "$BNJET_WORKDIR/tmp"
export TMPDIR="$BNJET_WORKDIR/tmp" TMP="$BNJET_WORKDIR/tmp" TEMP="$BNJET_WORKDIR/tmp"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1
set +u
source /data/software/xilinx/Vitis/2023.2/settings64.sh
set -u
BNJET_RUNNER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BNJET_PYTHON="${BNJET_PYTHON:-/home/users/kayamaguchi/micromamba/envs/bnjet/bin/python}"
exec "$BNJET_PYTHON" "$BNJET_RUNNER_DIR/supervise_synthesis.py" --workdir "$BNJET_WORKDIR"
