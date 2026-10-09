#!/usr/bin/env bash
# Run Vitis HLS csynth on hls4ml-1.3.0-generated projects (shipped as tarballs).
#
# Usage (on mulder):  ./mulder_csynth.sh <tarball> [<tarball> ...]
# Each tarball extracts to a project dir containing build_prj.tcl.
# Output: <project>/csynth_report.json next to the extracted project.
#
# Toolchain per code/hls/RUN_CSYNTH_ON_VITIS.md (2026-07-02 correction): the FULL
# Vitis settings64.sh must be sourced (provides vitis-run AND vitis_hls).
set -uo pipefail

source /data/software/xilinx/Vitis/2023.2/settings64.sh
command -v vitis_hls >/dev/null || { echo "FATAL: vitis_hls not on PATH"; exit 1; }

HERE="$(cd "$(dirname "$0")" && pwd)"

for tb in "$@"; do
  name=$(basename "$tb" .tar.gz)
  wd="$HERE/$name"
  echo "=== $name  $(date) ==="
  # Never silently destroy reports from a previous run of the same name: a killed run still
  # leaves the per-module csynth reports, which carry the per-module DSP attribution even
  # when the top-level rollup was never written (r14n16, 2026-08-04).
  if [ -d "$wd/myproject_prj/solution1/syn/report" ]; then
    keep="$HERE/${name}_prev_$(date +%Y%m%d%H%M%S).tar.gz"
    tar czf "$keep" -C "$wd" myproject_prj/solution1/syn/report vitis_hls.log csynth_stdout.log 2>/dev/null
    echo "  preserved previous reports -> $keep"
  fi
  rm -rf "$wd"; mkdir -p "$wd"
  tar -xzf "$tb" -C "$wd" --strip-components=1
  cd "$wd"
  # Synthesis only. The stage flags MUST be written into build_opt.tcl: hls4ml 1.3.0's
  # build_prj.tcl sources build_opt.tcl and never parses the string passed to
  # `vitis_hls -f`, so the old CLI-arg form was silently ignored and every run also did
  # csim + Verilog cosim + validation (found 2026-08-04: the r14n8 run's "FAIL" was the
  # validation log-diff, not synthesis).
  cat > build_opt.tcl <<'OPT'
array set opt {
    reset      1
    csim       0
    synth      1
    cosim      0
    validation 0
    export     0
    vsynth     0
    fifo_opt   0
}
OPT
  # Big designs die at the final top-level RTL step (r14n16: SIGKILL at 112.5 GB of 125 GB).
  # Trace peak memory and the design-size phase totals so a doomed run is visible in hours
  # rather than at the kill.
  ( while kill -0 $$ 2>/dev/null; do
      grep -o 'current allocated memory: [0-9.]* GB' csynth_stdout.log 2>/dev/null | tail -1
      grep -oE '\| HW Transforms .*' csynth_stdout.log 2>/dev/null | tail -1
      date '+%F %T'; echo '---'; sleep 600
    done ) > memwatch.log 2>&1 &
  watch_pid=$!
  ( time vitis_hls -f build_prj.tcl ) > csynth_stdout.log 2>&1
  rc=$?
  kill "$watch_pid" 2>/dev/null
  xml=$(find . -path "*/syn/report/csynth.xml" | head -1)
  if [ $rc -ne 0 ] || [ -z "$xml" ]; then
    echo "FAIL rc=$rc (no csynth.xml); tail of log:"
    tail -25 csynth_stdout.log
    cd "$HERE"; continue
  fi
  python3 "$HERE/parse_csynth.py" "$xml" > csynth_report.json
  echo "--- $name report ---"
  cat csynth_report.json
  cd "$HERE"
done
echo "=== all done $(date) ==="
