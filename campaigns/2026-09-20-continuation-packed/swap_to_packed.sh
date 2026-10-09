#!/usr/bin/env bash
# Replace one single-arm continuation Job with its packed twin (build_packed.py).
#   swap_to_packed.sh engram|arch|attn      run from the repo root; canary engram first
# Deletes the old Job, waits until NONE of its pods exist (two writers must never share a
# runs/<arm>/ directory), then applies the packed Job. Arms resume from latest.json.
set -euo pipefail
NS=cms-ml; D=local/continuation-20260920; L=${1:?engram|arch|attn}
OLD=$(python3 -c "import json;print(json.load(open('$D/$L-job.json'))['metadata']['name'])")
NEW=$D/$L-packed-job.json
python3 nrp-lab/nrp_doctor.py lint "$NEW"
echo "--- last epoch per pod before stop"
for p in $(kubectl -n $NS get pods -l job-name="$OLD" -o name); do
  echo "$p $(kubectl -n $NS logs "$p" --tail=1 | cut -c1-40)"
done | tee "$D/$L-swap-before.txt"
kubectl -n $NS delete job "$OLD" --ignore-not-found
until [ -z "$(kubectl -n $NS get pods -l job-name="$OLD" --no-headers 2>/dev/null)" ]; do sleep 5; done
echo "--- old pods gone; applying $NEW"
kubectl -n $NS apply -f "$NEW"
echo "verify once Running:  kubectl -n $NS logs -l continuation=full1000-20260920-packed --prefix --tail=200 | grep resume_epoch"
echo "                      kubectl -n $NS exec <pod> -- nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader -l 5"
