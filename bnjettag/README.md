# bnjettag/ — the working tree

Code, trained models, ROC arrays, and synthesis results for **Round 14**. All paths below
are relative to this folder. Project-level orientation: [`../README.md`](../README.md); the
verified record: [`../RESEARCH.md`](../RESEARCH.md).

Material from earlier rounds was moved to `../_attic/` on 2026-08-13 and is not part of the
active tree.

## Map

| Path | What it is | Status |
| --- | --- | --- |
| `code/hgq2/` | **The pipeline**: HGQ2-native QAT training (`bnhgq2/`), export and verification gates (`convert_final.py`), hls4ml conversion, dataflow/fold probes (`probe_pf_dataflow.py`, `fold_r14n8.py`), C-synthesis driving (`mulder_csynth.sh`), report parsing (`parse_csynth.py`). Driven by `run_stage.py` over `configs/*.json`. | current |
| `code/hgq2/configs/` | Round-14 run configurations, `r14-l1x3-n<N>-<variant>.json`, emitted by `gen_r14.py`. | current |
| `code/jobs/training/variants/` | Nautilus job specifications `kai-bn14-*.yaml` plus their generators (`gen_r14_jobs.py`, `gen_r14_roc_jobs.py`) and launch/ConfigMap scripts. | current |
| `code/plots/` | Figure generation (`make_r14_plots.py`). | current |
| `results/r14/` | **The Round-14 store of record**: AUC and HLS tables, EBOPs, uncertainty analysis, figures, verification transcripts. | current |
| `results/synthesis/runs/` | Per-article stores for the two synthesized Round-14 models — `2ae656b6` (n16) and `38a20c62` (n8) — holding export/C-sim gate JSONs, EBOPs, and raw csynth reports including the folded/dataflow operating points. | current |
| `results/hgq2/` | `constraints_map.md` — what HGQ2 + hls4ml can actually convert. New architectures are designed against it. | reference |
| `results/ebops.md` | EBOPs method notes and the published-tagger comparison. | reference |
| `roc-results/r14/`, `roc-results/r14-localeval/` | The `.npz` ROC arrays every AUC is recomputed from, with a `roc_auc.md` claim table beside each. | data |
| `models/` | Trained checkpoints (gitignored; see `models/MODEL.md` for W&B provenance). | data |
| `wandb-api-key.txt` | W&B credential (chmod 600, gitignored). **Never print, paste, or commit.** | secret |

## Conventions

- **Verification gate:** no AUC is quoted anywhere until recomputed from the `.npz`
  (`.claude/skills/verify-roc/`); no resource or latency number until parsed from the raw
  csynth XML.
- **Variants live in the config JSON, not in env vars or code forks:** `arch.n_part`,
  `arch.n_feat`, `quant.weight`, `quant.act_bits`.
- **W&B:** entity `kayamaguchi-uc-san-diego`, project `BNJetTagAug`. Runs carry
  group/job_type/tags and durable outputs are versioned artifacts (`model-<leaf>`,
  `evaluation-*`, `synthesis-*`, dataset) — full layout:
  `../docs/infrastructure/wandb-layout.md`.
