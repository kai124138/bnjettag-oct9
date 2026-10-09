#!/usr/bin/env bash
# Deterministic local check of the corrected note. Exit 0 only if all pass.
f=${1:-method-note-corrected-v1.md}; fail=0
need(){ grep -qiE "$1" "$f" && echo "PASS need: $2" || { echo "FAIL need: $2"; fail=1; }; }
forbid(){ grep -qiE "$1" "$f" && { echo "FAIL forbid: $2"; fail=1; } || echo "PASS forbid: $2"; }
need "highest validation macro-OvR AUC" "selection on validation"
need "never used for selection" "held-out excluded from selection"
need "remeasured on the selected checkpoint" "cost at selected checkpoint"
need "paired-by-seed .*95 % t-interval" "paired 95% t-interval"
need "eight seeds" ">=3 seeds (8 for gap <0.005)"
forbid "select[a-z]* .*highest ROC-test" "ROC-test selection"
forbid "final epoch|final-epoch" "final-epoch cost"
forbid "\(seed 1\)" "single-seed claim"
forbid "improves macro AUC" "unsupported improvement claim"
echo "overall: $([ $fail = 0 ] && echo PASS || echo FAIL)"; exit $fail
