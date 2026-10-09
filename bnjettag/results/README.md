# results/ — the Round-14 stores

| Path | What it is | Status |
| --- | --- | --- |
| **`r14/`** | **The store of record.** AUC tables, EBOPs (`ebops_r14.json`), uncertainty analysis (`uncertainty_r14.{json,md}`), the HLS tables (`hls_r14.md`, `hls_r14_folded.md`), figures, and the dated verification transcripts. | **CURRENT** |
| **`final/runs/`** | Per-article stores for the two synthesized models — `2ae656b6` (n16) and `38a20c62` (n8): export and C-sim gate JSONs, EBOPs, raw csynth reports, and the folded/dataflow operating-point variants (`*-pf*`). | **CURRENT** |
| `hgq2/` | `constraints_map.md` — what HGQ2 + hls4ml can and cannot convert. New architectures are designed against it. Plus the `2ae656b6` per-stage run store. | reference |
| `ebops.md` | EBOPs method notes and the published-tagger comparison (two conventions, never mixed). | reference |

Sibling folder `../roc-results/`: the `.npz` ROC arrays every AUC is recomputed from —
`r14/` (the cluster evaluation of record) and `r14-localeval/` (the local cross-check).

Results from earlier rounds moved to `../../_attic/pre-r14/results/` on 2026-08-13.
