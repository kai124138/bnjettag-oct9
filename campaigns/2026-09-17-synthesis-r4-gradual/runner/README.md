# Bounded R4 synthesis runner

Prepared locally only; these files do not connect or launch themselves remotely.

Copy this directory to `~/bnjet_ebops_r4_20260917/runner/`. The work directory must already contain `export/hls_prj_rf1.tar.gz`, `export/verification.json`, `export/csim_inputs.npy`, `export/csim_reference.npy`, and `remote_csim.py`. It must not contain a previous extracted `hls_prj_rf1` directory. The supervisor enforces both export gates, checks the archive SHA when included in verification metadata, and verifies unchanged HLS part/clock/RF.

The caller can launch externally with `setsid bash ~/bnjet_ebops_r4_20260917/runner/run_synthesis.sh`, redirecting stdin from `/dev/null` and stdout/stderr to a launcher log in the work directory. The wrapper sources the full Vitis 2023.2 settings and defaults to the existing bnjet Python. It sets TMPDIR/TMP/TEMP inside the work directory because system `/tmp` is full.

One nonblocking flock serializes the entire chain:

1. Build Linux C emulator, maximum 10 minutes.
2. Replay all 4096 gated examples with the provided `remote_csim.py`, maximum 10 minutes; require strict bit equality and zero maximum difference.
3. Vitis HLS csynth only, maximum 6 hours: VU13P `xcvu13p-flga2577-2-e`, 2.5 ns, RF=1. Generated build options explicitly disable C simulation, cosimulation, validation, IP export, and Vivado synthesis. HLS retains its exported 27% scheduling uncertainty.
4. Vivado out-of-context synthesis then `opt_design`, maximum 8 hours, four threads, `xczu7ev-ffvc1156-2-e`. The clock-only 2.5-ns XDC is read before synthesis, matching the historical OOC comparison. Both post-synthesis and post-optimization utilization/timing reports and checkpoints are required.

Each stage starts only when no other Vitis/Vivado process is active and at least 80 GiB MemAvailable exists. Runtime guards stop only the process group started by this runner if group RSS exceeds 64 GiB, MemAvailable falls below 8 GiB, free disk falls below 20 GiB, the work directory exceeds 50 GiB, or the stage exceeds its wall limit. Resource samples occur every 10 seconds; directory size is refreshed every 30 seconds. A graceful group termination is followed by group kill if needed. No unrelated processes are signaled. Failure prevents all subsequent stages.

Inspect `status.json` (atomic), `runner.pid`, `samples.jsonl`, `logs/`, `linux_csim_verification.json`, and `reports/`. The supervisor also records raw HLS XML fields and emitted RTL hashes. HLS results target VU13P; Vivado OOC results target xczu7ev and cannot be treated as VU13P utilization or routed timing. RF=1 alone does not establish full-jet initiation interval 1; inspect the actual top-level HLS report. Neither post-synth nor post-opt OOC timing is place-and-route closure.

Local checks passed: `bash -n`; Python compilation and Python 3.6 AST compatibility; positive/negative export-gate checks; Tcl syntactic completeness; and the constraint-before-synthesis ordering check. No vendor tools were launched as part of these checks.
