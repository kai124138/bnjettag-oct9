#!/bin/bash
# Fetch E-D1 csynth artifacts from mulder into results/adder-graph/ed1/.
# (Per-experiment fetch script — fetch_mulder_reports.sh is never edited.)
set -eu
cd "$(dirname "$0")/../../results/adder-graph/ed1"
ssh mulder 'cd ~/csynth/ed1 && tar czf - run.log vitis_hls.log \
  prj_ed1/sol1/syn/report prj_ed1/sol1/csim/report 2>/dev/null' | tar xzf -
echo "fetched into $(pwd):"
ls prj_ed1/sol1/syn/report/ 2>/dev/null || echo "  (no syn report — csynth failed?)"
