#!/usr/bin/env bash
# round-11 stage0: capacity ladder. PREREQ: ConfigMap kai-bn11-code built from code/hgq2
# INCLUDING the r11 configs (see make_code_configmap.sh; the jobs hard-fail on a stale one).
# Staged in waves of 5, matching the round-7 matrix precedent (5 concurrent Zenodo pulls).
# Usage: ./launch_r11_stage0.sh   |   ./launch_r11_stage0.sh delete
set -euo pipefail
CTX="nautilus"; NS="cms-ml"; HERE="$(cd "$(dirname "$0")" && pwd)"
ALL=(kai-bn11-lrprobe-d128-w1a8-stdnn-lr1e4-s1 kai-bn11-lrprobe-d128-w1a8-stdnn-lr1e5-s1 kai-bn11-lrprobe-d128-w1a8-stdnn-lr2e5-s1 kai-bn11-lrprobe-d128-w1a8-stdnn-lr5e5-s1 kai-bn11-lrprobe-d48-w1a8-stdnn-lr2e5-s1 kai-bn11-lrprobe-d48-w1a8-stdnn-lr5e5-s1 kai-bn11-lrprobe-d64-w1a8-stdnn-lr1e4-s1 kai-bn11-lrprobe-d64-w1a8-stdnn-lr1e5-s1 kai-bn11-lrprobe-d64-w1a8-stdnn-lr2e5-s1 kai-bn11-lrprobe-d64-w1a8-stdnn-lr5e5-s1 kai-bn11-lrprobe-d96-w1a8-stdnn-lr1e4-s1 kai-bn11-lrprobe-d96-w1a8-stdnn-lr2e5-s1 kai-bn11-lrprobe-d96-w1a8-stdnn-lr5e5-s1)
if [ "${1:-apply}" = "delete" ]; then
  for j in "${ALL[@]}"; do kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found; done
  exit 0
fi
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
    echo "  ... $pending/${#jobs[@]} still running"; sleep 60
  done
}
wave=()
for j in "${ALL[@]}"; do
  kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found >/dev/null 2>&1 || true
  kubectl --context "$CTX" -n "$NS" apply -f "$HERE/$j.yaml"
  wave+=("$j")
  if [ "${#wave[@]}" -ge 5 ]; then
    echo "=== wave of ${#wave[@]} launched; waiting ==="
    wait_for_wave "${wave[@]}"; wave=()
  fi
done
[ "${#wave[@]}" -gt 0 ] && { echo "=== final wave of ${#wave[@]} ==="; wait_for_wave "${wave[@]}"; }
echo; echo "=== round-11 stage0 complete (13 jobs) ==="
kubectl --context "$CTX" -n "$NS" get jobs -l app=bnjet-r11
