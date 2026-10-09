# results/synthesis/ — per-article export and synthesis store

One directory per *article*: a specific trained checkpoint taken through export, the
verification gates, hls4ml conversion, and Vitis C-synthesis. Written by
`code/hgq2/convert_final.py` (and, for the folded operating points,
`code/hgq2/fold_r14n8.py` / `probe_pf_dataflow.py`).

Layout: `runs/<config-hash>/<article>[/<variant-tag>]/`.

| Article | What it is |
| --- | --- |
| `runs/38a20c62/w1a8-s3-r14n8/` | **The n8 silicon point.** Export gates, EBOPs, and the two synthesized results — `csynth_rf1/` (fx8, 4,133 DSP) and `csynth_rf1_fabric/` (0 DSP in the whole design). |
| `runs/2ae656b6/w1a8-s1-r14n16/` | The n16 article. Export gates pass; `csynth_rf1_partial/` holds the partial attribution from the run that died at 17.7 h without a full report. |
| `runs/*/...-pf*` | Folded / dataflow operating points (partition factor, softmax partitioning, dataflow). Parsed table: `../r14/hls_r14_folded.md`. |

Per-article files: `export_verify.json` (GATE1 score correlation + the β-encoding ladder),
`csim_verify.json` (GATE2 hls4ml C-sim bit-exactness), `ebops.json`, `convert.json`, the
mulder-ready project tarball, and the raw csynth reports. Pre-v5 export state is preserved
alongside as `*.pre-v5-2026-08-04.json`.

The parsed numbers of record live in `../r14/hls_r14.md` and `../r14/hls_r14_folded.md` —
raw report always beside the parsed table, and no number enters a document until it has been
read back out of the XML.

> **Naming note (2026-08-13).** This directory was called `results/final/` — named after the
> July "FINAL" campaign, which Round 14 superseded. The Round-14 syntheses had been written
> into it, so it was renamed to describe what it holds rather than which campaign created it.
> The four genuinely pre-R14 run directories moved to `_attic/pre-r14/results/final/`.
> Provenance JSONs written before the rename still record the old path; see
> `../r14/PROVENANCE-NOTE-2026-08-13.md`.
