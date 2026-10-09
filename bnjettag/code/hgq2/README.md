# HGQ2 pipeline (`code/hgq2/`) — train, export, convert, verify

Updated 2026-08-01. The QKeras→HGQ2 *porting* pipeline this README used to describe
(`run_stage.py extract/calibrate/port`, gates against the r5 `.npz`) is **legacy** —
kept working but no longer the path any current number comes from. The current
pipeline is HGQ2-native end to end:

```
(a) bnhgq2/qat.py  build_qat_model (line 290) — native HGQ2 QAT model,
    binary {−1,+1} weights via BitQEinsumDense/BitQDense (absmean STE)
(b) bnhgq2/train.py — trainer; runs on NRP via jobs/training/variants/*.yaml,
    checkpoints to W&B
(c) convert_final.py — the conversion driver:
      pull checkpoint → re-export to the hardware graph (bnhgq2/build.py:63,
      weights pinned ±1, static KIF activation grids, β folded/CSD-2)
      → GATE 1 → hls4ml convert (bnhgq2/convert.py:53) → GATE 2 (C-sim)
      → EBOPs → results store + tarball for mulder
(d) mulder_csynth.sh / fetch_mulder_reports.sh — Vitis C-synthesis on mulder,
    reports back into the store
```

Headline config: `configs/r14-l1x3-n16-w1a8.json` (d32, 2 layers, 4 heads,
norm-free, A8, input standardization). Driver: `run_convert_r7.sh` (pass
`--config r14-l1x3-n16-w1a8`; the script's default config is older).

## Verification gates (what "verified" means here)

1. **GATE 1 — trained QAT ↔ export graph** (`export_verify.json`): Pearson corr of
   softmax scores on 4,096 real jets; nominal threshold corr ≥ 0.9999.
   The r8-stdnn flagship characterizes at **0.98907** — a genuine ceiling of the
   static-grid export, documented in `LEDGER.md` (2026-07-18), not a silent pass.
2. **GATE 2 — export graph ↔ hls4ml C-sim** (`csim_verify.json`): hls4ml `predict`
   (compiled C-sim via the generated bridge, no hand-written testbench) vs the export
   model on 128 real jets; threshold corr ≥ 0.997. The r8 flagship is bit-exact
   (corr 1.0).

Both gate JSONs land in `../../results/synthesis/runs/<hash>/<article>/`.

## Layout (current files first)

| Path | Role |
| --- | --- |
| `bnhgq2/qat.py` | **The model.** Native HGQ2 QAT graph; `BitQEinsumDense`/`BitQDense` (binary absmean), hand-composed attention (QEinsumDense + QEinsum + QSoftmax). |
| `bnhgq2/train.py` | Trainer (NRP entry). |
| `bnhgq2/build.py` | Export/hardware graph: ±1-pinned kernels, static activation grids. |
| `bnhgq2/convert.py` | `convert_from_keras_model` call (Vitis, VU13P, io_parallel, `bit_exact=True`) + C-sim + `pack_for_mulder`. |
| `convert_final.py` | Conversion driver (gates, EBOPs, hls4ml fixups: `patch_resource_einsum_check`, `fix_relu_saturation`, `widen_weighted_accum`). |
| `bnhgq2/compat.py` | Runtime shims for stock hls4ml 1.3.0 / keras 3.15 / hgq2 0.1.9 (nothing installed is patched on disk). |
| `bnhgq2/subln.py`, `hls_templates/nnet_subln.h`, `test_subln.py` | SubLN hls4ml extension — **legacy** (headline model is norm-free). |
| `configs/*.json` | One model+quantization spec per file. |
| `LEDGER.md` | Dated change ledger (authoritative history, newest on top). |
| `distill_r12.py`, `eval_r11.py`, `roc_final.py`, `rejection.py`, `aggregate.py`, `parse_csynth*.py` | Analysis / campaign tooling. |
| `bnhgq2/extract.py`, `port.py`, `verify.py`, `gold.py`, `run_stage.py` | Earlier QKeras porting mode (era of the r5 gates). |

A complete audit of this pipeline vs upstream (every monkeypatch, every deviation
from calad0i/HGQ2-examples `jsc150`) is in `../../../_attic/reports/AUDIT.md`.

## Environment

Local venv at repo root: `../../../.venv-hgq2` (Python 3.12, hgq2 0.1.9, hls4ml 1.3.0,
keras 3.15, TF 2.21 backend). Training on NRP; synthesis on mulder only.
