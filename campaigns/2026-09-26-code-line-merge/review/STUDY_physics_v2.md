# Physics/engineering review of STUDY_v2

Date: 2026-10-01  
Verdict: **PASS — design only; compatibility execution remains pending.**

Scope: reviewed only `STUDY_v2.md` and its cited `inventory_20261001.json`. No source execution, checkpoint tensors, data arrays, earlier reviews, or methodology documents were inspected.

The design supports a controlled source merge without training. Its fixed-checkpoint null, exact historical config retention, public-default contract, and separate engineering/historical-metric gates address the relevant scientific risks. The inventory corroborates docstring-only differences in the central graph, quantization, and data modules, while identifying substantive changes in orchestration and interfaces. This is useful change-scope evidence, not an inference-equivalence result.

The limits are stated correctly: only 29 research configs have matching checkpoint metadata; nine research configs and every exact public config identity lack matches in the scanned roots. The 280 file entries are neither 280 independent runs nor verified checkpoint content identities. Architecture/quantizer aliases cannot erase differences in selection metadata, data paths, or provenance. D3, D4, and gate 4 prevent those gaps from becoming an unsupported scientific PASS or a claim to cover frozen Chang/Delta extensions.

The CPU builds, isolated reload comparisons, and bounded synthetic weighting fixtures are feasible without optimizer steps. Together with reviewed diffs, they can support the explicitly limited engineering claim. They cannot establish saved validation metrics or new training outcomes; the design appropriately leaves historical replay and final retirement dependent on their own evidence.

## A — must fix

None for approval of this design. This verdict does not clear any implementation gate, historical replay, launch, or retirement of an old entry point.

## B — should fix during implementation

1. **Make selection and evaluation contracts observable in the preflight matrix.** D2 preserves schedules, validation selection, splits, and cap feasibility, while the inventory reports non-docstring changes in `bnhgq2/train.py`, `run_stage.py`, `run_ablation.py`, and `export_roc_eval.py`. Build counts and fixed-checkpoint inference do not exercise these contracts. Add bounded fixtures that compare row IDs/order, label-to-score alignment, score dtype and preprocessing, plus constructed callback/schedule settings and selection decisions on fabricated epoch records. No optimizer or real-data run is needed. Gate 5 already covers weighting alignment; extend that explicitness to the other affected paths.

2. **Specify probe content beyond input shape.** Gate 3 requires deterministic probes but defines coverage only by shape. Include ordinary nonconstant inputs and supported zero/padding, sign, and quantization-boundary cases; exercise the actual preprocessing/evaluation entry point where it is adapted. Record probe-generation parameters and hashes. These probes improve fault detection for binary/quantized models without turning a finite regression suite into a universal equivalence proof.

## C — suggestions

- Supplement parameter counts and graph shapes with a normalized layer/connectivity/quantizer configuration comparison. Equal counts and shapes alone permit different computations; the existing source review remains necessary.
- Give every preflight row an explicit original-source side and source-manifest hash, checkpoint content hash, preprocessing hash, environment-lock hash, and gate status. The inventory's short metadata config hashes should remain candidate lookup keys until the exact mapping required by gate 3 is established.

Accept the design and proceed to the bounded implementation checks. Keep `MISSING`/`PENDING` visible and retain the corresponding historical entry points until their required gates pass.
