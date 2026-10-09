# Ignored artifacts — where the durable copies live

Store policy of 2026-08-24 (decisions.md): the following large artifacts are deliberately NOT in
git. Every number of record derived from them IS tracked beside them.

| Ignored | Size class | Durable copy / how to regenerate |
|---|---|---|
| `roc-results/**/*.npz` (score arrays, 260k jets each) | ~10 MB × 180 | W&B `evaluation-*` artifacts, project `BNJetTagAug` (per `docs/infrastructure/wandb-layout.md`); regenerable by the ROC eval jobs. The per-seed AUC tables (`roc_auc.md`) and every derived table (`results/r14/*.md/.json`) are tracked. |
| `results/synthesis/runs/**/hls_prj*/` + `*.tar.gz` | 10–100 MB each | Rebuilt deterministically by `convert_final.py` / `fold_r14n8.py` from tracked configs + checkpoints (W&B `model-*`); shipped copies also in W&B `synthesis-*` where logged. |
| `results/synthesis/runs/**/csynth.xml` | ~19 MB each | The rollup is in the tracked `csynth_report.json`; the per-module attribution is in the tracked `myproject_csynth.rpt`. |
| `results/synthesis/runs/**/vivado_run.log`, `vivado.log` | ~8 MB each | Load-bearing lines (e.g. `[Synth 8-3323]` DSP demand) are excerpted into tracked files in the same leaf; full logs remain on mulder `~/bnjet_r14/`. |
| `…r14n16/csynth_rf1_partial/*.rpt` | 98 MB | Distilled into the tracked `module_dsp_attribution.json` in the same directory. |
| `results/{r14,hgq2}/runs/` | scratch | W&B run debris; never numbers of record. |
| checkpoints (`models/`, `roc-results/**/_ckpt_dl/`) | — | W&B `model-<leaf>` artifacts (already ignored policy, `models/MODEL.md`). |
