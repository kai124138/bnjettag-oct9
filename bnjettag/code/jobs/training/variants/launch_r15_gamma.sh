#!/usr/bin/env bash
# Round-15 GAMMA: 6 jobs (sm4i0/sm6i0 x s1-3), all at once (scheduler self-limits).
# PREREQ: ConfigMap kai-bn15-code (make_code_configmap_r15.sh). Usage: ./launch_r15_gamma.sh [delete]
set -euo pipefail
CTX=nautilus; NS=cms-ml; HERE="$(cd "$(dirname "$0")" && pwd)"
JOBS=(kai-bn15-gamma-sm4i0-n8-w1a8-s1 kai-bn15-gamma-sm4i0-n8-w1a8-s2 kai-bn15-gamma-sm4i0-n8-w1a8-s3 kai-bn15-gamma-sm6i0-n8-w1a8-s1 kai-bn15-gamma-sm6i0-n8-w1a8-s2 kai-bn15-gamma-sm6i0-n8-w1a8-s3)
if [ "${1:-}" = delete ]; then for j in "${JOBS[@]}"; do kubectl --context $CTX -n $NS delete job $j --ignore-not-found; done; exit 0; fi
for j in "${JOBS[@]}"; do kubectl --context $CTX -n $NS apply -f "$HERE/$j.yaml"; done
kubectl --context $CTX -n $NS get jobs -l app=bnjet-r15
