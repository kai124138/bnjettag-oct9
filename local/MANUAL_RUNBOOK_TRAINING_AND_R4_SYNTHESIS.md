---
title: Manual runbook: training batch and original R4 hardware synthesis
status: current
date: 2026-09-17
---

# Manual runbook: training batch and original R4 hardware synthesis

Updated 17 September 2026. **Execution is now manual. No restart was submitted when preparing this guide.**

## Verified status

- Training Job `kai-batch0917-screen-e100` failed at **16:34 UTC**, reason `MaxFailedIndexesExceeded`; failed indexes **1–3**, seven failed pod attempts. No batch pods remain. This controller status does **not** identify the underlying per-pod failure; original events/pods are no longer available in the inspected namespace.
- Persistent checkpoint state exists: **A00 completed 60 epochs; A01 completed 39**. Those runs can resume. No saved `screening_status.json` was found for the other arms; do not assume they trained.
- R4 export and local/Linux C simulation passed, bit-exact export-to-C outputs on **4,096 jets**. Original float32 checkpoint versus fixed-point export has two changed argmax decisions in that sample; it is not claimed identical to float training.
- Vitis HLS attempts failed in its compiler frontend, before RTL generation. Splitting interface pragmas and adding C linkage to the top function did not resolve it. **Vivado synthesis never started. No hardware result is available.** Nothing remains active in this synthesis chain.
- A VU13P Vivado license probe failed; the xczu7ev probe passed. HLS VU13P and Vivado xczu7ev are different target stages and must be labeled separately.

## 1. Training intent and knobs

Goal: find the best validation categorical accuracy under the chosen native EBOP budget, then test hardware feasibility. Do not rank AUC as though it were accuracy. Use the same split and a single screening seed for comparisons; retain the held-out test set for final evaluation.

Common settings: binary weights, initial activation width 8 with learned widths, three features (pt/etarel/phirel), no normalization, learned positional table, GAP, five outputs, batch256, LR2e-5, softmax probability width10, seed1. The immutable schedule is **1,000 epochs** even when a screening job pauses early.

| Run | --index | Constituents | d_model | FFN | Layers | Heads | Activation granularity | EBOP target | Intent |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| A00 | 0 | 8 | 32 | 64 | 2 | 4 | channel | 350,000 | N8 channel baseline |
| A01 | 1 | 8 | 32 | 64 | 2 | 4 | tensor | 350,000 | Per-tensor versus A00 |
| A02 | 2 | 8 | 32 | 32 | 2 | 4 | channel | 350,000 | Smaller FFN versus A00 |
| A03 | 3 | 8 | 32 | 32 | 2 | 4 | tensor | 350,000 | Per-tensor versus A02 |
| A04 | 4 | 16 | 32 | 32 | 2 | 4 | channel | 350,000 | 16 constituents versus A02 |
| A05 | 5 | 32 | 32 | 32 | 2 | 4 | channel | 350,000 | 32 constituents versus A02 |
| A06 | 6 | 16 | 16 | 32 | 2 | 4 | channel | 350,000 | Smaller embedding versus A04 |
| A07 | 7 | 16 | 32 | 32 | 1 | 4 | channel | 350,000 | One transformer layer versus A04 |
| A08 | 8 | 16 | 32 | 32 | 2 | 2 | channel | 350,000 | Two attention heads versus A04 |
| A09 | 9 | 16 | 32 | 32 | 2 | 4 | channel | 500,000 | Looser EBOP budget versus A04 |
| A10 | 10 | 16 | 32 | 32 | 2 | 4 | channel | 250,000 | Tighter EBOP budget versus A04 |
| A11 | 11 | 8 | 32 | 32 | 2 | 4 | channel | 500,000 | Looser EBOP budget versus A02 |

Screen **12 → 8 → 4** candidates at cumulative **100 → 200 → 400 epochs**. Review feasibility and learning trends before promotion; the first 100 epochs are an early screen. Extend finalists to 1,000 and repeat seeds separately. Do not alter the underlying epoch/decay schedule when resuming.

Frozen-backbone classifier recovery, activation-floor/precision refinements, distillation and DSP/reuse comparisons are **later conditional studies**, not jobs to launch in this first batch. Original R4 synthesis below is not a frozen-backbone recovery experiment.

## 2. Resume one training arm first

Run on your laptop from the workspace. The generator below only writes JSON; **kubectl create is the command that launches training**.

```bash
cd /Users/kaiyamaguchi/Desktop/bnjettag-lab

# Confirm the original immutable runtime and storage still exist.
kubectl get configmap kai-batch0917-code-ddd3761d2a -n cms-ml
kubectl get pvc kai-data -n cms-ml

# A00: resume its saved 60 epochs and stop at cumulative epoch 100.
python3 local/training-batch-20260917/make_manual_job.py   --index 0 --stop-after 100   --name kai-batch0917-manual-a00-e100-v1   > local/training-batch-20260917/manual-a00-e100.json

kubectl create -f local/training-batch-20260917/manual-a00-e100.json
kubectl get pods -n cms-ml -l job-name=kai-batch0917-manual-a00-e100-v1 -w
```

In another terminal after the pod is running:

```bash
kubectl logs -n cms-ml -f job/kai-batch0917-manual-a00-e100-v1
```

This is **one GPU, four CPUs, 12 GiB RAM, zero automatic retries**, using the original code archive, configuration, W&B run identity and persistent output root. A failed arm will not cancel the other planned arms through the old Indexed Job's failure threshold. This isolates failures; it does not fix an as-yet-unidentified GPU/pod failure.

Start A01 separately only after A00 startup/resume looks healthy; change `--index 0` to `--index 1` and every job/file name `a00` to `a01`. Use the table for the other indexes. Keep at most **two active single-GPU jobs**. Never submit two jobs for the same arm at once.

For another attempt, use a new outer Job name (`v2`, etc.); the underlying arm and output directory remain unchanged. Do not delete the PVC, overwrite checkpoints, alter the immutable config/code or blindly resubmit the old 12-index Job.

### If the arm fails

Capture evidence while the pod still exists; no compute is launched by these commands:

```bash
kubectl describe job -n cms-ml kai-batch0917-manual-a00-e100-v1
kubectl get pods -n cms-ml -l job-name=kai-batch0917-manual-a00-e100-v1 -o wide
kubectl describe pods -n cms-ml -l job-name=kai-batch0917-manual-a00-e100-v1
kubectl logs -n cms-ml job/kai-batch0917-manual-a00-e100-v1 --tail=200
```

Check the termination reason and exit code before changing training hyperparameters. `OOMKilled`, eviction, scheduler failure, missing credentials and a Python traceback imply different fixes. The earlier batch status alone does not distinguish them.

If the immutable ConfigMap is missing, recreate **that same archive**, not today's working code:

```bash
shasum -a 256 local/training-batch-20260917/launch/hgq2.tar.gz
# Must equal ddd3761d2a566790b42a1c55c036727df624e58a6f65305c1aeca3d05365584d
kubectl create configmap kai-batch0917-code-ddd3761d2a -n cms-ml   --from-file=hgq2.tar.gz=local/training-batch-20260917/launch/hgq2.tar.gz
kubectl patch configmap kai-batch0917-code-ddd3761d2a -n cms-ml   --type=merge -p '{"immutable":true}'
```

### Promotion

For a selected arm, rerun the generator with `--stop-after 200` or `400` and a new outer job name such as `kai-batch0917-manual-a00-e200-v1`. The checkpoint advances to that cumulative epoch count. If already at the target, the trainer should do no additional epochs. Final 1,000-epoch completion and new seeds are separate deliberate launches; do not claim a 100-epoch rung is completed full training.

## 3. R4 hardware study: intent

Model: `ebops-n8-20260912-ablation-r4-gradual-w1a8-s1`, selected feasible epoch959. Its native checkpoint cost is349,550EBOPs; EBOPs do not directly give LUTs, DSPs or latency.

| Stage | Operating point | Question |
|---|---|---|
| Vitis HLS | xcvu13p-flga2577-2-e, 2.5ns, RF1, Latency/io_parallel | What are estimated resources, whole-model latency and achieved initiation interval? |
| Vivado OOC | xczu7ev-ffvc1156-2-e proxy, 2.5ns, four threads | What logic/DSP/BRAM does synthesis actually infer, and what is pre-route timing? |
| Later implementation | Actual integration part and constraints | Does the integrated design fit and meet routed timing/throughput? |

The immediate blocker is a **Vitis2023.2 frontend crash** (`collectPragmaObjects` / `DisaggregatePreprocess`, HLS200-1715). C simulation succeeds. No emitted RTL means there is presently nothing valid to pass to Vivado. Running the same flow is a diagnostic reproduction, **not a known-working fix**.

### Inspect the existing failed attempt on Mulder

```bash
ssh mulder
cd ~/bnjet_ebops_r4_20260917
cat status.json
cat linux_csim_verification.json
tail -80 logs/hls.log
cat hls_prj_rf1/myproject_prj/solution1/.autopilot/db/a.g.ld.0.bc.clang.reflow.err.log
```

Attempts are preserved under `attempts/`. The current third attempt additionally tried explicit C linkage; it still failed. Do not keep rerunning it expecting a different outcome.

### If you want a fresh diagnostic retry

After making a deliberate compatibility correction, regenerate the project/archive and update its verification hash. Recheck Linux fidelity. To reproduce the current failure in a fresh guarded directory (no changes to the previous evidence):

```bash
# On Mulder. This copies the current, still-failing source snapshot.
BNJET_MANUAL_ROOT=$(mktemp -d "$HOME/bnjet_r4_manual_XXXXXX")
cp -a "$HOME/bnjet_ebops_r4_20260917/export" "$BNJET_MANUAL_ROOT/"
cp -a "$HOME/bnjet_ebops_r4_20260917/runner" "$BNJET_MANUAL_ROOT/"
cp "$HOME/bnjet_ebops_r4_20260917/remote_csim.py" "$BNJET_MANUAL_ROOT/"
export BNJET_WORKDIR="$BNJET_MANUAL_ROOT"
setsid nohup bash "$BNJET_MANUAL_ROOT/runner/run_synthesis.sh"   > "$BNJET_MANUAL_ROOT/supervisor.log" 2>&1 < /dev/null &
printf 'Work directory: %s
' "$BNJET_MANUAL_ROOT"
```

The runner enforces exact C-simulation replay before HLS, then queues Vivado only after a successful top-level report and nonempty RTL. Limits:64GiB process-group RSS,50GiB directory,6h HLS/8h Vivado, no overlapping vendor jobs at launch. TMPDIR uses the work directory because system `/tmp` is full.

### Once HLS produces valid RTL

The supervisor normally invokes this itself. For a manual standalone Vivado invocation after HLS succeeds, from the successful work directory:

```bash
source /data/software/xilinx/Vitis/2023.2/settings64.sh
export TMPDIR="$PWD/tmp"
mkdir -p "$TMPDIR" reports/ooc_xczu7ev
BNJET_RTL="$PWD/hls_prj_rf1/myproject_prj/solution1/syn/verilog"
test -s hls_prj_rf1/myproject_prj/solution1/syn/report/myproject_csynth.xml
vivado -mode batch -source "$PWD/runner/ooc.tcl"   -tclargs "$BNJET_RTL" "$PWD/reports/ooc_xczu7ev" myproject "$PWD/runner/clock.xdc"
```

Use the guarded chain for the resource caps. The standalone command has no memory supervisor. Do not launch it concurrently with that chain. Reports are post-synth/post-opt utilization and timing; these are **not** place-and-route closure. RF1 is not proof of II1; read the reported interval. The xczu7ev result is not a VU13P device-fit claim.

## Detailed methods and evidence

- [Training plan, including explicitly labeled frozen-backbone follow-ups](training-batch-20260917/TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md)
- [R4 export theory, code, precision tables and regression evidence](synthesis-r4-gradual-20260917/README.md)
- [Bounded synthesis runner](synthesis-r4-gradual-20260917/runner/README.md)

The two export fixes are already documented: preserve learned activation grids instead of recreating eight-bit grids; repair ReLU followed by a quantizer whose range makes the branch identically zero. They passed C simulation but do not solve the independent Vitis compiler crash.
