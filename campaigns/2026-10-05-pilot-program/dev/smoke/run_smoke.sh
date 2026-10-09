#!/usr/bin/env bash
# Local GPU smoke (home PC RTX 4060 Ti). Exploration only, never quotable.
# usage: run_smoke.sh <variant: a|nb|h3qkv1> [files] [epochs]
set -euo pipefail
DEV=$(cd "$(dirname "$0")/.." && pwd)
SP=$HOME/venv-hgq2/lib/python3.12/site-packages/nvidia
export LD_LIBRARY_PATH=$(ls -d $SP/*/lib | tr '\n' ':')/usr/lib/wsl/lib
v=$1; files=${2:-10}; epochs=${3:-20}
case $v in
  a) cfg=$DEV/tree/campaigns/chang1002c/configs/chang1002c-a-n64-s1.json ;;
  *) cfg=$DEV/configs/dev1005-$v-n64-s1.json ;;
esac
out=$DEV/smoke/runs/$v-f$files-e$epochs
rm -rf "$out"
exec $HOME/venv-hgq2/bin/python $DEV/smoke/smoke.py "$cfg" --tree $DEV/tree --data $HOME/data/hls4ml_lhc_jet/train/train \
  --files $files --epochs $epochs --out "$out"
