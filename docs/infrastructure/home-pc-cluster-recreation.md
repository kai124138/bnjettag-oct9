---
title: Home-PC cluster recreation — the prompt for Claude Code on that machine
status: current
date: 2026-09-08
---

# Home-PC cluster recreation — the prompt for Claude Code on that machine

## Before you paste the prompt (things only YOU can do)

1. **OS**: install Ubuntu 22.04 LTS natively on the PC (dual-boot is fine). Vitis HLS
   2023.2 officially supports Ubuntu 22.04; WSL2 sort-of works for csynth but is
   unsupported and flaky — native Linux saves days of pain.
2. **Transfer the working repo**: `bnjettag-training-results` exists only on your
   laptop (the GitHub repo is the public subset). Copy the whole folder to the PC via
   external drive or `scp` — INCLUDING `bnjettag/code/`, `data/val/`, and
   `bnjettag/results/r14/` and `bnjettag/roc-results/r14/` (results give the verification gates something to check against).
   You can skip `archive/` and `.venv-hgq2/` (it gets rebuilt).
3. **Secrets by hand**: bring `bnjettag/wandb-api-key.txt` yourself (USB, not chat, not
   the prompt). `chmod 600` it.
4. **AMD account**: the Vitis installer needs a free AMD/Xilinx login. Make the account
   and have the credentials ready — the installer will ask interactively.
5. **Disk**: you need ~300 GB free for the Vitis install transient (~110 GB installed),
   plus ~10 GB for data and envs. Check before starting.

---

## THE PROMPT (paste everything below into Claude Code on the PC)

I want you to recreate my research computing setup on this machine. It replaces two
remote systems: an NRP Kubernetes GPU cluster (training) and a Vitis HLS synthesis box
called mulder. This machine: RTX 4060 Ti 8 GB, 32 GB RAM, Intel i5-13600K, Ubuntu 22.04,
~300 GB free disk. The project working repo has been copied to ~/bnjettag-training-results
(if it is not there, stop and ask me). Work through the phases IN ORDER and run the
verification gate at the end of each phase before moving on — do not proceed past a
failing gate.

### Phase 0 — system prep
- `sudo apt update && sudo apt install -y build-essential git curl unzip libtinfo5
  libncurses5 locales graphviz` (libtinfo5/libncurses5 are Vitis runtime requirements on
  Ubuntu 22.04).
- NVIDIA driver: install the latest stable driver (`sudo ubuntu-drivers install`),
  reboot, verify `nvidia-smi` shows the 4060 Ti. Do NOT install a system CUDA toolkit —
  the TensorFlow pip wheels ship their own CUDA 12 libraries.
- Swap: Vitis synthesis of my models peaks at 40–55 GB allocated; this box has 32 GB.
  Create a 64 GB swapfile on the NVMe (`sudo fallocate -l 64G /swapfile && sudo chmod
  600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`, add to /etc/fstab).
  Synthesis will be slower when it swaps, but it will finish instead of being OOM-killed.
  (Sizing baseline: mulder has 125 GB of RAM, so 32 + 64 GB is the tighter machine —
  see `infrastructure/mulder-setup.md`. Per *individual* synthesis this box should be
  roughly twice as fast, since csynth is single-threaded and mulder's EPYC cores top out
  at 3.3 GHz; what we lose is memory headroom and concurrency, not speed.)
- Install `uv` (https://astral.sh/uv) for python management.
- GATE 0: `nvidia-smi` shows the GPU; `free -h` shows ~64 GB swap; 250+ GB disk free.

### Phase 1 — the training environment (mirrors the cluster pods exactly)
- Create a venv at ~/bnjettag-training-results/.venv-hgq2 with Python 3.12 (uv).
- Install EXACTLY these pins (they mirror the verified cluster environment — do not
  "upgrade" anything):
  `tensorflow[and-cuda]==2.21.0 keras==3.15.0 hgq2==0.1.9 quantizers==1.2.2
  scikit-learn==1.9.0 h5py==3.14.0 wandb==0.28.0 hls4ml==1.3.0 numpy==2.5.0
  matplotlib==3.11.0 python-docx pyyaml`
- KNOWN TRAP 1: the TF 2.21 wheel's RPATH discovery of the nvidia-*-cu12 wheel libs is
  broken. After install, export
  `LD_LIBRARY_PATH=$(python -c "import glob; print(':'.join(sorted(glob.glob('<venv>/lib/python3.12/site-packages/nvidia/*/lib'))))")`
  and put that export in an activation hook so it is always set.
- KNOWN TRAP 2: `da4ml` (needed only for distributed-arithmetic emissions) pins
  numba→numpy≤2.4, conflicting with our numpy 2.5.0. Default env keeps numpy 2.5.0
  WITHOUT da4ml. If I ever ask for a DA emission, downgrade to numpy 2.4.6 + install
  `da4ml>=0.5.2,<0.6` in that moment, and verify a reference AUC still reproduces.
- GATE 1 (all must pass):
  a. `python -c "import tensorflow as tf; assert tf.config.list_physical_devices('GPU')"`
     sees the 4060 Ti.
  b. A real matmul + a one-batch keras fit run on GPU without cuDNN errors.
  c. Reference-number reproduction: from the repo root,
     load a `bnjettag/roc-results/r14/n16/*.npz` array and recompute
     `roc_auc_score(y, score, multi_class="ovr", average="macro")` — it must equal
     0.8964 to 4 decimals. This proves the numeric stack matches the one that produced
     every verified number in the project.

### Phase 2 — data
- Download the public dataset (both splits) from Zenodo record 3602260:
  `hls4ml_LHCjet_150p_train.tar.gz` (~2.7 GB; hard-fail if the file is smaller than
  2,500,000,000 bytes) into ~/data/hls4ml_lhc_jet/train/, and
  `hls4ml_LHCjet_150p_val.tar.gz` (~1.14 GB; hard-fail below 1,000,000,000 bytes) into
  ~/data/hls4ml_lhc_jet/val/. Extract both; keep the val extraction consistent with the
  repo's existing `data/val` layout (jetImage_*.h5 files in one directory).
- GATE 2: counting jets via h5py across the val split gives 260,000+ and the train split
  loads with the repo's own loader
  (`bnjettag/code/hgq2/bnhgq2/train.py::load_train_data`, `n_part=10`).

### Phase 3 — training stack verification (the cluster replacement)
- From `bnjettag/code/hgq2/`, build all current configs the way the cluster preflight
  does: for every `configs/r7*.json` and `configs/r8*.json`, `bnhgq2.qat.build_qat_model`
  must build with param counts exactly 19,201 (small quantized), 19,075 (small fp32),
  5,345 (tiny quantized), 5,219 (tiny fp32), and every binary config must pass the
  {−1,+1} effective-weight gate (exactly two symmetric values, zero zeros, 15 layers).
- Run one REAL smoke train on GPU: `run_stage.py train --config configs/r8-small-w1a8-stdnn.json
  --seed 1 --smoke --out-dir /tmp/smoke` with `BNHGQ2_TRAIN_DATA` pointed at the val dir
  and `WANDB_MODE=offline`. It must exit 0 and write model_best.keras + input_std.json.
- W&B: run `wandb login` interactively with me present (the key is in
  `bnjettag/wandb-api-key.txt`, chmod 600 — never print or commit it). Then verify a
  checkpoint fetch: download `model_best.keras` from run `r8-small-w1a8-stdnn-s2` in
  project `bnjettag-final` (entity `kayamaguchi-uc-san-diego`) and confirm its file size
  is 725,321 bytes.
- GATE 3: configs build with exact params + binary gates; smoke exits 0; W&B fetch
  matches the byte size.

### Phase 4 — Vitis HLS 2023.2 (the mulder replacement)
- Download the AMD "Vitis Unified Installer 2023.2" (web installer) from
  https://www.xilinx.com/support/download.html — I will log in with my AMD account when
  it asks. Install the FULL Vitis 2023.2 (not standalone Vitis HLS): my synthesis
  scripts source `settings64.sh` from a full install, which provides both `vitis_hls`
  and `vitis-run`. Deselect device families we do not need EXCEPT keep UltraScale+
  (the target is xcvu13p-flga2577-2-e). Install to /tools/Xilinx (default).
  Expect a very large download; the installer supports resume.
- C synthesis needs NO license — do not set up any license manager.
- After install: `source /tools/Xilinx/Vitis/2023.2/settings64.sh` in the shell profile
  guarded behind an alias (`alias vitis-env='source ...'`) so it does not pollute the
  python env by default (Vitis ships its own old libstdc++ that can break python).
- GATE 4a: `vitis_hls -version` prints 2023.2 and `which vitis-run` resolves after
  sourcing.
- GATE 4b — the real acceptance test, end to end on this machine: from the repo, take
  the already-emitted tarball
  a stored hls project tarball under `bnjettag/results/synthesis/runs/`, extract it to a work
  dir, and run the repo's synthesis wrapper pattern:
  `vitis_hls -f build_prj.tcl "reset=1 csim=0 synth=1 cosim=0 validation=0 export=0 vsynth=0"`.
  This is the norm-free RF=8 whole model. On this CPU expect very roughly 3–6 hours and
  a memory peak near 13 GB (no swap pressure). When it finishes, parse
  `.../syn/report/csynth.xml` with `bnjettag/code/hgq2/parse_csynth.py` (DSP mode): the
  totals MUST be DSP = 1,764 and LUT = 3,910,515, and the census must show every binary
  layer at 0 DSP. Reproducing mulder's number exactly is the proof this box is a valid
  mulder replacement.
- Note the box's limits honestly in a final report: single synthesis at a time (32 GB +
  swap), deployable-scale models only (the 6.4M-parameter monolith needs >100 GB and is
  out of scope here), and A6/A4-style runs (40–55 GB allocated) will lean on swap and
  run slow but should complete.

### Phase 5 — conversion loop closure
- With the training env (NOT the Vitis shell): run the repo's conversion driver on a
  locally-fetched checkpoint:
  `convert_final.py --variant w1a8 --seed 2 --config configs/r8-small-w1a8-stdnn.json
  --checkpoint <fetched model_best.keras> --input-std <fetched input_std.json> --rf 8
  --run-dir /tmp/convert-test`. GATE 5: GATE2 in its output reports bit-exact
  (max|Δ|=0.0) C-sim, matching the recorded result.

### Final deliverable
Write `~/bnjettag-training-results/HOME-PC.md` recording: every installed version, the
LD_LIBRARY_PATH hook, the swap config, all five gate results with numbers, wall-clock
for the acceptance synthesis, and the box's measured limits. Nothing goes in that file
that a gate did not actually verify.

Throughout: never print, echo, or commit the W&B key; if any gate fails, stop and show
me the failure rather than working around it silently.

---

## What this box will and won't replace (for your expectations)

**Replaces well**: the full dev loop — training small/tiny/r8 models (minutes per run on
the 4060 Ti), conversions and C-sim, whole-model csynth at deployable scale (hours, one
at a time), ROC evaluation, everything offline.

**Doesn't replace**: parallel seed sweeps (one GPU vs the cluster's dozens), the
6.4M-parameter monolith synthesis (>100 GB RAM), concurrent syntheses (the OOM lesson —
mulder killed one at 54 GB with three running; this box runs exactly one).
