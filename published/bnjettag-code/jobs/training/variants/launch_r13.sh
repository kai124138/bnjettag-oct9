#!/usr/bin/env bash
# Round 13 — binary weights under EBOPs pressure (code/hgq2/R13-DESIGN.md).
#
# ONE STAGE AT A TIME, ON PURPOSE:
#   stage0   4 LR probes (A1 recipe, beta=0, 300 ep). Winner rule: best epoch INSIDE the
#            budget, then highest val macro AUC, ties -> lower LR. Pin it with
#            `python ../../../hgq2/configs/gen_r13.py --lr <winner>` and RE-RUN
#            gen_r13_jobs.py before stage0b/1/2.
#   stage0b  the beta sighter (A1, seed 1, full 1500-epoch schedule) = the GO/NO-GO:
#            does the front ever cross 5e5 EBOPs? If not, the terminal beta is revised
#            AND LOGGED before stage1 — never mid-campaign.
#   stage1   A1 + A2 x seeds 1,2,3   (the headline comparison)
#   stage2   A3 + A4 x seeds 1,2,3   (the confound controls F3 / F4)
#
# PREREQS: ConfigMap kai-bn13-code built from code/hgq2 INCLUDING the r13 configs and the
# EBOPs-callback plumbing (make_code_configmap_r13.sh; the jobs hard-fail on a stale one),
# AND preflight_r13.sh printing PREFLIGHT_ALL_PASS. Staged in waves of 5 (r7 precedent).
#
# Usage: ./launch_r13.sh stage0 | stage0b | stage1 | stage2 | delete
set -euo pipefail
CTX="nautilus"; NS="cms-ml"; HERE="$(cd "$(dirname "$0")" && pwd)"
stage0=(kai-bn13-lrprobe-w1-freeact-lr2e5-s1 kai-bn13-lrprobe-w1-freeact-lr5e5-s1 kai-bn13-lrprobe-w1-freeact-lr1e4-s1 kai-bn13-lrprobe-w1-freeact-lr2e4-s1)
stage0b=(kai-bn13-sighter-w1-freeact-beta-s1)
stage1=(kai-bn13-small-w1-freeact-beta-s1 kai-bn13-small-w1-freeact-beta-s2 kai-bn13-small-w1-freeact-beta-s3 kai-bn13-small-wq-freeact-beta-s1 kai-bn13-small-wq-freeact-beta-s2 kai-bn13-small-wq-freeact-beta-s3)
stage2=(kai-bn13-small-w1-freeact-beta0-s1 kai-bn13-small-w1-freeact-beta0-s2 kai-bn13-small-w1-freeact-beta0-s3 kai-bn13-small-w1-fixa8-beta0-s1 kai-bn13-small-w1-fixa8-beta0-s2 kai-bn13-small-w1-fixa8-beta0-s3)
ALL=("${stage0[@]}" "${stage0b[@]}" "${stage1[@]}" "${stage2[@]}")
CMD="${1:-}"
if [ "$CMD" = "delete" ]; then
  for j in "${ALL[@]}"; do kubectl --context "$CTX" -n "$NS" delete job "$j" --ignore-not-found; done
  exit 0
fi
case "$CMD" in
  stage0)  JOBS=("${stage0[@]}") ;;
  stage0b) JOBS=("${stage0b[@]}") ;;
  stage1)  JOBS=("${stage1[@]}") ;;
  stage2)  JOBS=("${stage2[@]}") ;;
  *) echo "usage: $0 stage0|stage0b|stage1|stage2|delete"; exit 2 ;;
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
  if [ "${#wave[@]}" -ge 5 ]; then
    echo "=== wave of ${#wave[@]} launched; waiting ==="
    wait_for_wave "${wave[@]}"; wave=()
  fi
done
[ "${#wave[@]}" -gt 0 ] && { echo "=== final wave of ${#wave[@]} ==="; wait_for_wave "${wave[@]}"; }
echo; echo "=== round-13 $CMD complete (${#JOBS[@]} jobs) ==="
kubectl --context "$CTX" -n "$NS" get jobs -l bn13stage="$CMD"
