# How the Research Is Done

The methodology record of the BNJetTag project: a binary-weight ({−1, +1}) transformer
jet tagger for the CMS Level-1 trigger, trained with quantization-aware training and
synthesized to FPGA through hls4ml and Vitis HLS. This repository documents how the
work is actually done — the machines, the pipeline, the code, the verification gates,
and the incidents that shaped all of it — as a set of notebooks in the style of the
[hls4ml tutorial](https://github.com/fastmachinelearning/hls4ml-tutorial), next to the
code they explain.

It is not a tutorial you can run end to end: training needs a GPU cluster and
synthesis needs a Vitis HLS machine. But the notebooks show the real commands, configs,
and job manifests at every step, the code in `code/` is the actual pipeline, and the
cells that read files in this repository run as-is.

## The notebooks

| Notebook | What it covers |
|---|---|
| [Part 1 — Overview and infrastructure](part1_overview_and_infrastructure.ipynb) | The research question, the three machines, the pipeline and its gates, and how NRP / W&B / mulder are set up |
| [Part 2 — Data](part2_data.ipynb) | The HLS4ML LHC Jet dataset, the held-out discipline, top-N inputs, and standardization as part of the model |
| [Part 3 — Model and quantization](part3_model_and_quantization.ipynb) | The transformer, absmean binarization and the straight-through estimator, activation grids, EBOPs |
| [Part 4 — Designing and training](part4_designing_and_training.ipynb) | Config-plus-seed experiments, preflight, pre-registration, job manifests, launching and monitoring on the cluster |
| [Part 5 — Evaluation](part5_evaluation.ipynb) | The two AUCs, the recompute-from-arrays verification gate, and when a difference is real |
| [Part 6 — Hardware](part6_hardware.ipynb) | The export graph, the two fidelity gates, reuse factor, C-synthesis on mulder, and the standard report checks |
| [Part 7 — Artifact atlas and records](part7_artifact_atlas_and_records.ipynb) | Where every artifact lives end to end, and the rules that keep the record honest |
| [Part 8 — Timeline and lessons](part8_timeline_and_lessons.ipynb) | The rounds in order, where the time went, and every incident and dead end with the rule it left behind |

## The code

`code/` is the actual pipeline, not a simplified copy:

- `code/bnhgq2/` — the training package: `qat.py` (the binary quantizer and QAT layers),
  `data.py` (loading, top-N, standardization), `train.py` (the trainer and its
  durability gate), `binarize.py` / `build.py` (the export graph), `ebops_calc.py`,
  `wandb_util.py`, and the rest of the package as it runs.
- `code/` — the stage drivers: `run_stage.py`, `roc_final.py` (evaluation),
  `convert_final.py` (hls4ml conversion and the fidelity gates), `ebops_r14.py`,
  `parse_csynth.py` / `parse_csynth_modules.py`, `mulder_csynth.sh`,
  `fetch_mulder_reports.sh`, `preflight_r13.sh`.
- `code/configs/` — a real generated config (`r14-l1x3-n8-w1a8.json`), the round-8
  flagship config, and the generator that emits them (`gen_r14.py`).
- `code/jobs/` — a real Kubernetes job manifest (`kai-bn14-l1x3-n8-w1a8-s1.yaml`), the
  manifest generators, the ConfigMap builder, and the launch script.
- `examples/` — real artifacts from the round-14 record: an `export_verify.json` with
  the GATE-1 encoding ladder, and the two parsed C-synthesis reports (fx8 and
  fabric-multiplier variants, both RF = 1) that the hardware notebook reads.

## Viewing and running

GitHub renders the notebooks directly. To open them locally:

```
git clone https://github.com/kai124138/bnjettag-methodology.git
cd bnjettag-methodology
jupyter lab        # any Python 3 with jupyter; the runnable cells need only numpy
```

Cells that read `code/...` or `examples/...` run anywhere. Cells prefixed with a
`# runs on: NRP` or `# runs on: mulder` comment show the real commands but need the
cluster or the synthesis machine. The workflow diagrams in `figures/` are placeholders
to be replaced with redrawn versions; the remaining figures are copies of the
publication figures from the research tree, captioned with their generator and source
data.

## Relation to the rest of the project

The research working tree holds the living results record (`RESEARCH.md`, which maps
every claim to its source file), the frozen reports, and the result stores that
in-text citations like `bnjettag/results/...` point to. The verified results are
published separately at
[kai124138/bnjettag_results](https://github.com/kai124138/bnjettag_results).
