#!/usr/bin/env bash
# R1 relaunch r3: move the 4 exit-76 partial run dirs aside so the r3 Jobs start those arms from epoch 0.
# PREPARED ONLY. NOT RUN. Needs Kai (RULES §3: moving what this session did not create).
#
# Source: review/REGRESSION_TICKET_r2-resume.md §1 (each dir: 1-row activation_widths.jsonl, no latest.json,
# no checkpoints/; run_training raises "History exists without a committed checkpoint", ablation.py:914).
# Nothing is deleted: each dir is renamed to <dir>.r2-partial-<UTC timestamp> on the same PVC.
#
# Where to run: inside a short-lived CPU pod in cms-ml that mounts PVC kai-data read-write at /data
# (the ticket's inspect pod mounted it readOnly; a rename needs readOnly false). Copy this file in, then:
#   bash pvc-rename-aside-r3.sh            # dry run: checks and prints the planned mv commands, changes nothing
#   bash pvc-rename-aside-r3.sh --apply    # performs the 4 renames, after the same checks
# Preconditions the operator checks first, from outside the pod (read-only):
#   kubectl get pods -n cms-ml | grep -E 'kai-p1005r1-(h1-e-350k-c-s2|h4-e-350k-c-w100-s2|h4-e-350k-c-w50-s1|h4-e-350k-c-w50-s2)-'
#     -> no pod Running/Pending/Terminating for these arms (r2 Jobs are Failed; r3 not yet submitted)
# Run it before submitting the 4 fresh-start r3 Jobs; the 4 resume arms are not touched.
set -euo pipefail

RUNS=/data/chang-n64-20260926/pilot-program-20261005/r1/runs
ARMS=(h1-e-350k-c-s2 h4-e-350k-c-w100-s2 h4-e-350k-c-w50-s1 h4-e-350k-c-w50-s2)
TS=$(date -u +%Y%m%dT%H%M%SZ)
case "$#:${1:-}" in
  0:) APPLY=0 ;;
  1:--apply) APPLY=1 ;;
  *) echo "usage: $0 [--apply]"; exit 2 ;;
esac

test -d "$RUNS" || { echo "RUNS_DIR_MISSING $RUNS"; exit 1; }
fail=0
for arm in "${ARMS[@]}"; do
  d="$RUNS/pilot1005-$arm"
  t="$d.r2-partial-$TS"
  # Guards: only the exact ticket state is moved. Any committed state means the dir is not a 1-epoch partial.
  if [ ! -d "$d" ]; then echo "SKIP_MISSING $d"; fail=1; continue; fi
  if [ -e "$d/latest.json" ] || [ -e "$d/checkpoints" ]; then echo "REFUSE_HAS_CHECKPOINT $d"; fail=1; continue; fi
  if [ -e "$d/VERIFIED_COMPLETE.json" ] || [ -e "$d/DIVERGED.json" ]; then echo "REFUSE_FINAL_MARKER $d"; fail=1; continue; fi
  rows=$(wc -l < "$d/activation_widths.jsonl" 2>/dev/null || echo 0)
  if [ "$rows" -gt 1 ]; then echo "REFUSE_HISTORY_ROWS=$rows $d (ticket saw 1)"; fail=1; continue; fi
  if [ -e "$t" ]; then echo "REFUSE_TARGET_EXISTS $t"; fail=1; continue; fi
  echo "PLAN mv -n -- '$d' '$t'   (activation_widths rows=$rows)"
done
[ "$fail" = 0 ] || { echo "CHECKS_FAILED: nothing renamed"; exit 1; }
[ "$APPLY" = 1 ] || { echo "DRY_RUN_OK: rerun with --apply to rename"; exit 0; }

for arm in "${ARMS[@]}"; do
  d="$RUNS/pilot1005-$arm"
  t="$d.r2-partial-$TS"
  mv -n -- "$d" "$t"
  test ! -e "$d" && test -d "$t" || { echo "RENAME_FAILED $d"; exit 1; }
  echo "RENAMED $d -> $t"
  ls -la "$t"
done
echo "RENAME_ASIDE_DONE ts=$TS (4 dirs; nothing deleted)"
