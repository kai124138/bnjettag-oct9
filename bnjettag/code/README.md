# code/ — what we actually run

Everything current lives in **`hgq2/`**.

| Folder | What it is | Status |
| --- | --- | --- |
| **`hgq2/`** | **The whole pipeline** — native HGQ2 QAT training (`bnhgq2/qat.py` + `bnhgq2/train.py`, launched on NRP via `jobs/`), export with the verification gates and EBOPs (`convert_final.py`), the dataflow/fold probes (`probe_pf_dataflow.py`, `fold_r14n8.py`), the mulder synthesis hand-off (`mulder_csynth.sh`), and report parsing (`parse_csynth.py`). Round-14 analysis: `ebops_r14.py`, `uncertainty_r14.py`. Start at `hgq2/README.md`. | **CURRENT** |
| `hgq2/configs/` | Round-14 run configurations `r14-l1x3-n<N>-<variant>.json`, emitted by `gen_r14.py`. Never hand-edit a generated config — edit the generator and regenerate. | **CURRENT** |
| `jobs/training/variants/` | Nautilus job specifications `kai-bn14-*.yaml` and the ROC jobs `kai-bn14-roc-n<N>.yaml`, emitted by `gen_r14_jobs.py` / `gen_r14_roc_jobs.py`. Launch with `launch_r14.sh`; ConfigMap via `make_code_configmap_r14.sh`. Same rule: edit the generator, not the YAML. | **CURRENT** |
| `plots/` | Figure generation — `make_r14_plots.py`. | **CURRENT** |

Code from earlier rounds — the QKeras trainer, the QKeras-path HLS scripts, the adder-graph
analysis tools, and the pre-R14 probe emitters — moved to `../../_attic/pre-r14/code/` and
`../../_attic/compiler-workstream/` on 2026-08-13.
