#!/usr/bin/env bash
# Round 14 — L1-realistic (N,3) inputs, constituent-count sweep (decisions.md 2026-08-01).
#
#   stage1  N in {8,16,32,64} x fp32/w8a8/w1a8 x s1-3  (36 jobs: baselines + thesis)
#   stage2  N in {8,16,32,64} x w1a6/w1a4     x s1-3  (24 jobs: activation ladder)
#
# PREREQS: ConfigMap kai-bn14-code built from code/hgq2 INCLUDING the r14 configs and
# the feature-subset plumbing (make_code_configmap_r14.sh; jobs hard-fail on a stale
# one). Staged in waves of 6.
#
# Usage: ./launch_r14.sh stage1 | stage2 | delete
set -euo pipefail
CTX="nautilus"; NS="cms-ml"; HERE="$(cd "$(dirname "$0")" && pwd)"
stage1=(kai-bn14-l1x3-n8-fp32-s1 kai-bn14-l1x3-n8-fp32-s2 kai-bn14-l1x3-n8-fp32-s3 kai-bn14-l1x3-n8-w8a8-s1 kai-bn14-l1x3-n8-w8a8-s2 kai-bn14-l1x3-n8-w8a8-s3 kai-bn14-l1x3-n8-w1a8-s1 kai-bn14-l1x3-n8-w1a8-s2 kai-bn14-l1x3-n8-w1a8-s3 kai-bn14-l1x3-n16-fp32-s1 kai-bn14-l1x3-n16-fp32-s2 kai-bn14-l1x3-n16-fp32-s3 kai-bn14-l1x3-n16-w8a8-s1 kai-bn14-l1x3-n16-w8a8-s2 kai-bn14-l1x3-n16-w8a8-s3 kai-bn14-l1x3-n16-w1a8-s1 kai-bn14-l1x3-n16-w1a8-s2 kai-bn14-l1x3-n16-w1a8-s3 kai-bn14-l1x3-n32-fp32-s1 kai-bn14-l1x3-n32-fp32-s2 kai-bn14-l1x3-n32-fp32-s3 kai-bn14-l1x3-n32-w8a8-s1 kai-bn14-l1x3-n32-w8a8-s2 kai-bn14-l1x3-n32-w8a8-s3 kai-bn14-l1x3-n32-w1a8-s1 kai-bn14-l1x3-n32-w1a8-s2 kai-bn14-l1x3-n32-w1a8-s3 kai-bn14-l1x3-n64-fp32-s1 kai-bn14-l1x3-n64-fp32-s2 kai-bn14-l1x3-n64-fp32-s3 kai-bn14-l1x3-n64-w8a8-s1 kai-bn14-l1x3-n64-w8a8-s2 kai-bn14-l1x3-n64-w8a8-s3 kai-bn14-l1x3-n64-w1a8-s1 kai-bn14-l1x3-n64-w1a8-s2 kai-bn14-l1x3-n64-w1a8-s3)
stage2=(kai-bn14-l1x3-n8-w1a6-s1 kai-bn14-l1x3-n8-w1a6-s2 kai-bn14-l1x3-n8-w1a6-s3 kai-bn14-l1x3-n8-w1a4-s1 kai-bn14-l1x3-n8-w1a4-s2 kai-bn14-l1x3-n8-w1a4-s3 kai-bn14-l1x3-n16-w1a6-s1 kai-bn14-l1x3-n16-w1a6-s2 kai-bn14-l1x3-n16-w1a6-s3 kai-bn14-l1x3-n16-w1a4-s1 kai-bn14-l1x3-n16-w1a4-s2 kai-bn14-l1x3-n16-w1a4-s3 kai-bn14-l1x3-n32-w1a6-s1 kai-bn14-l1x3-n32-w1a6-s2 kai-bn14-l1x3-n32-w1a6-s3 kai-bn14-l1x3-n32-w1a4-s1 kai-bn14-l1x3-n32-w1a4-s2 kai-bn14-l1x3-n32-w1a4-s3 kai-bn14-l1x3-n64-w1a6-s1 kai-bn14-l1x3-n64-w1a6-s2 kai-bn14-l1x3-n64-w1a6-s3 kai-bn14-l1x3-n64-w1a4-s1 kai-bn14-l1x3-n64-w1a4-s2 kai-bn14-l1x3-n64-w1a4-s3)
ALL=("${stage1[@]}" "${stage2[@]}")
CMD="${1:-}"
if [ "$CMD" = "delete" ]; then
  for j in "${ALL[@]}"; do kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found; done
  exit 0
fi
case "$CMD" in
  stage1)  JOBS=("${stage1[@]}") ;;
  stage2)  JOBS=("${stage2[@]}") ;;
  *) echo "usage: $0 stage1|stage2|delete"; exit 2 ;;
esac
wait_for_wave() {
  local jobs=("$@")
  while true; do
    local pending=0
    for j in "${jobs[@]}"; do
      local done_n
      done_n=$(kubectl --context "$CTX" -n "$NS" get job "$j" \
        -o jsonpath='{.status.succeeded}{.status.failed}' 2>/dev/null || true)
      [ -n "$done_n" ] || pending=$((pending+1))
    done
    [ "$pending" -eq 0 ] && break
    echo "  ... $pending/${#jobs[@]} still running"; sleep 120
  done
}
wave=()
for j in "${JOBS[@]}"; do
  kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found >/dev/null 2>&1 || true
  kubectl --context "$CTX" -n "$NS" apply -f "$HERE/$j.yaml"
  wave+=("$j")
  if [ "${#wave[@]}" -ge 6 ]; then
    echo "=== wave of ${#wave[@]} launched; waiting ==="
    wait_for_wave "${wave[@]}"; wave=()
  fi
done
[ "${#wave[@]}" -gt 0 ] && { echo "=== final wave of ${#wave[@]} ==="; wait_for_wave "${wave[@]}"; }
echo; echo "=== round-14 $CMD complete (${#JOBS[@]} jobs) ==="
kubectl --context "$CTX" -n "$NS" get jobs -l bn14stage="$CMD"
