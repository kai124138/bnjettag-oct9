# Current work: accuracy under a computational budget

**Batch `batch20260917` · 17 September 2026**

We are testing which binary-weight transformer architectures improve five-class jet-tagging accuracy while respecting a computational budget and a whole-jet FPGA initiation interval of **II=1**. The immediate work is a controlled 12-configuration training screen. Frozen-backbone classifier fitting and hybrid DSP mappings are separate, conditional follow-ups.

[Detailed protocol](TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md) · [Run configurations](../../code/hgq2/configs/batch20260917/) · [Machine-readable live status](live-status.json) · [Project results](../../README.md)

The [code manifest](code-manifest.json) records the packaged code archive and individual file hashes used for reproducibility. Configuration hashes appear in the live snapshot; a hash records artifact identity, not a successful execution result.

<!-- WANDB_LINK_START -->
[Training curves on Weights & Biases](https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Batch20260917) — project `BNJetTag-Batch20260917`, group `batch20260917`. Run links and measurements will appear after registration; an empty project is not evidence that training has started.
<!-- WANDB_LINK_END -->

## How to follow this work

Start with the status table below, open a run’s W&B link for live curves, and use the architecture table to see exactly what changed. W&B updates during training; the GitHub table is a timestamped snapshot refreshed with the included updater. Promotion decisions and validated results will be recorded separately from preliminary training metrics.

## Live snapshot

The table below is a static snapshot with a reproducible updater. Check its timestamp and the [status JSON](live-status.json) before treating it as current. `planned` means that no submission or remote run is recorded; `queued` requires either an explicit submission record or a remote queue state. A blank metric is unmeasured, not zero. Budget feasibility applies to the selected checkpoint, not merely the requested target.

<!-- LIVE_STATUS_START -->

Snapshot refreshed: **2026-09-17T15:01:57Z**. Source: `initial_planning_snapshot`.

| Run | State | Epochs | Latest val accuracy / AUC | Best feasible val accuracy / AUC | Feasible EBOPs / target | Runtime | Source updated UTC |
|---|---|---:|---:|---:|---:|---:|---|
| A00 | planned | — | — / — | — | — / 350,000 | — | — |
| A01 | planned | — | — / — | — | — / 350,000 | — | — |
| A02 | planned | — | — / — | — | — / 350,000 | — | — |
| A03 | planned | — | — / — | — | — / 350,000 | — | — |
| A04 | planned | — | — / — | — | — / 350,000 | — | — |
| A05 | planned | — | — / — | — | — / 350,000 | — | — |
| A06 | planned | — | — / — | — | — / 350,000 | — | — |
| A07 | planned | — | — / — | — | — / 350,000 | — | — |
| A08 | planned | — | — / — | — | — / 350,000 | — | — |
| A09 | planned | — | — / — | — | — / 500,000 | — | — |
| A10 | planned | — | — / — | — | — / 250,000 | — | — |
| A11 | planned | — | — / — | — | — / 500,000 | — | — |

A paused screening rung is not a completed 1,000-epoch run. Blank metrics are unverified or unavailable. Runtime scope and budget-check details are recorded in [live-status.json](live-status.json).

<!-- LIVE_STATUS_END -->

## What we are trying to learn

The earlier investigation verified the accuracy/AUC calculations and found substantial confusion between particular jet classes. **AUC measures ranking; accuracy measures whether the correct class wins.** AUC of 0.85 does not mean 85% of jets are classified correctly. This batch therefore selects checkpoints by **validation categorical accuracy subject to the final native EBOP target**, using AUC as a secondary measurement.

The first screen addresses four questions:

- Does using 16 or 32 constituents retain useful extra information when the EBOP budget is held fixed?
- Does a smaller feed-forward network leave enough budget for useful activation precision, particularly with channel-wise quantization?
- Can a narrower or shallower transformer improve the accuracy/resource tradeoff?
- Are apparent architecture gains actually consequences of relaxing the computational budget?

Native effective bit operations, or EBOPs, are a computational proxy. They do not establish FPGA resource utilization, throughput, or latency. Those require separate hardware measurements.

## Architecture screen: A00–A11

All rows train the **whole model** with binary projection weights and learned activation widths. The initial screen uses initialization seed 1, three input features (`pt`, `etarel`, `phirel`), and five classes (`g`, `q`, `W`, `Z`, `t`). N is constituent count, D embedding width, F feed-forward hidden width, L transformer blocks, and H attention heads.

| Config | N | D | F | L | H | Activation granularity | EBOP target | Main comparison |
|---|---:|---:|---:|---:|---:|---|---:|---|
| [A00](../../code/hgq2/configs/batch20260917/batch20260917-a00-s1.json) | 8 | 32 | 64 | 2 | 4 | Channel | 350k | Accuracy-selected reference |
| [A01](../../code/hgq2/configs/batch20260917/batch20260917-a01-s1.json) | 8 | 32 | 64 | 2 | 4 | Tensor | 350k | Granularity alone |
| [A02](../../code/hgq2/configs/batch20260917/batch20260917-a02-s1.json) | 8 | 32 | 32 | 2 | 4 | Channel | 350k | Smaller FFN with channel widths |
| [A03](../../code/hgq2/configs/batch20260917/batch20260917-a03-s1.json) | 8 | 32 | 32 | 2 | 4 | Tensor | 350k | Complete FFN/granularity comparison |
| [A04](../../code/hgq2/configs/batch20260917/batch20260917-a04-s1.json) | 16 | 32 | 32 | 2 | 4 | Channel | 350k | More constituents at matched budget |
| [A05](../../code/hgq2/configs/batch20260917/batch20260917-a05-s1.json) | 32 | 32 | 32 | 2 | 4 | Channel | 350k | More information versus attention cost |
| [A06](../../code/hgq2/configs/batch20260917/batch20260917-a06-s1.json) | 16 | 16 | 32 | 2 | 4 | Channel | 350k | Narrower embedding |
| [A07](../../code/hgq2/configs/batch20260917/batch20260917-a07-s1.json) | 16 | 32 | 32 | 1 | 4 | Channel | 350k | One transformer block |
| [A08](../../code/hgq2/configs/batch20260917/batch20260917-a08-s1.json) | 16 | 32 | 32 | 2 | 2 | Channel | 350k | Fewer heads at fixed D |
| [A09](../../code/hgq2/configs/batch20260917/batch20260917-a09-s1.json) | 16 | 32 | 32 | 2 | 4 | Channel | 500k | Relaxed resource pressure |
| [A10](../../code/hgq2/configs/batch20260917/batch20260917-a10-s1.json) | 16 | 32 | 32 | 2 | 4 | Channel | 250k | Tighter resource pressure |
| [A11](../../code/hgq2/configs/batch20260917/batch20260917-a11-s1.json) | 8 | 32 | 32 | 2 | 4 | Channel | 500k | Complete N/budget comparison |

Every configuration keeps a 1,000-epoch schedule. Screening pauses and resumes the same run at cumulative epochs 100, 200, and 400; it does not restart or shorten the learning-rate schedule. A00 remains a control through epoch 400. The 250k and 500k probes stay separate from the primary 350k comparison.

## Training stages and follow-ups

```mermaid
flowchart TD
    A["A screen: train 12 configurations to epoch 100"] --> B["Promote 8 to cumulative epoch 200"]
    B --> C["Promote 4 to cumulative epoch 400"]
    C --> D["Conditional B-series: refine full-model training"]
    C --> E["Choose two finalists by validation accuracy and budget"]
    D --> E
    E --> F["Continue to 1,000 epochs; confirm seeds 2 and 3"]
    F --> G["Conditional F-series: freeze backbone, fit output component"]
    F --> H["Conditional H-series: zero-DSP and hybrid FPGA mappings"]
    G --> H
```

| Stage | What changes | What remains fixed | Release condition |
|---|---|---|---|
| A | Architecture, activation granularity, or target budget | Common training/data protocol | Preflight and resume checks pass |
| B | Selected precision or optimization setting | Recorded winning 350k architecture | A-screen evidence identifies a useful test |
| F | Final classifier or output offsets | Trained backbone and its quantizers | Finalist checkpoint and cached features verified |
| H | Arithmetic placement and selected reuse settings | Numerical checkpoint, precision, and I/O contract | Export and numerical checks pass |

The default B queue contains four candidate refinements: an activation-width cap, a protective width floor plus cap, 8-bit attention probabilities, and a learning-rate comparison. Width constraints need implementation and native-bitwidth tests before use. Other B rows remain conditional; see the [full protocol](TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md#b-series-conditional-training-refinements).

The F-series compares the original frozen model, output-bias fitting, and 4-bit/8-bit final classifiers. Head refitting and output-bias fitting are **alternative models**. Refitting an 8-bit final layer yields a mixed-precision model with a binary backbone; it does not produce an entirely binary network.

```mermaid
flowchart LR
    X["Jet inputs"] --> B["Frozen binary backbone"]
    B --> V["Fixed penultimate features"]
    V --> O["Original final head"]
    V --> Q["Fit 4-bit or 8-bit final head"]
    O --> C["Alternative: fit five logit offsets"]
    O --> Y["Five-class prediction"]
    Q --> Y
    C --> Y
```

## Hardware: II=1 with optional DSP use

The H-series starts at reuse factor 1 and compares **0%, 1%, 2.5%, and 5% device-wide DSP caps** on identical checkpoints. These are exploratory caps, not confirmed integration allocations. Binary sign/addition operations remain fabric-based initially; eligible nonbinary products can be mapped to DSPs. Reuse factors 2 and 4 are conditional follow-ups on selected nonbinary operations.

```mermaid
flowchart LR
    C["Fixed numerical checkpoint"] --> Z["H00: zero DSP"]
    C --> D["H01-H03: DSP caps 1%, 2.5%, 5%"]
    Z --> G["Require whole-jet II=1 and numerical agreement"]
    D --> G
    G --> M["Measure LUT, FF, memory, DSP, latency, timing"]
```

II=1 means accepting a new **whole jet** every clock cycle, not merely one token per cycle. The requested clock is 2.5 ns, with latency below 1 microsecond as a provisional screening ceiling pending integration requirements. Neither setting is a measured result. Selected designs require multi-transaction co-simulation and implementation timing checks; synthesis estimates alone are insufficient.

## Historical measurements versus this batch

These are **completed, exploratory single-seed results from the earlier investigation**, not A-series outcomes. Accuracy and AUC below use the 260,000-event held-out archive; EBOPs are native model estimates.

| Earlier model | Held-out accuracy | Macro OvR AUC | Native EBOPs |
|---|---:|---:|---:|
| R1, channel-wise activation quantization | 58.7431% | 0.850795 | 317,890 |
| R2, smaller FFN with tensor-wise quantization | 58.3131% | 0.853526 | 329,838 |
| R1 frozen backbone + 8-bit final classifier | 59.1396% | 0.855957 | 322,510 |

The head refit improved R1 accuracy by 0.3965 percentage points, with a paired event-level 95% interval of 0.3191–0.4740 points. This interval does not include training-seed variability. Its FPGA feasibility is unverified, and the result does not predict an improvement on a new backbone.

Historical head-refit evidence: [experiment record](../../results/post_conference/frozen_backbone/head_report.json) and [independent numerical verification](../../results/post_conference/frozen_backbone/independent_verification.json).

Training uses 496,000 events and internal validation uses 124,000. The separate 260,000-event archive has already been inspected in earlier work; it is excluded from sweep selection but is not a new untouched confirmatory benchmark. Finalist reports will distinguish validation selection, held-out evaluation, initialization-seed variation, and per-event uncertainty.

## Resource discipline and reporting

The A-screen allocation is **2,800 epoch passes**: 12×100, then 8×100 additional, then 4×200 additional. At most two GPU training jobs run concurrently. Epoch passes are not GPU-hours; measured seconds per epoch and peak memory determine the remaining-cost forecast. Frozen-feature preparation, head fitting, metric checks, and hardware synthesis use suitable CPU resources.

Conditional default B refinements, finalist continuation, and seeds 2/3 bring the full proposed allocation to **8,800 epoch passes** if every stage proceeds, excluding optional tests, head fits, teacher training, and hardware builds. Promotion decisions retain budget feasibility, matched-prefix controls, and the reason each run continues or stops.

Each run record should contain its config/code/data hashes, selected checkpoint and epoch, validation accuracy/AUC, native cost and width distributions, duration, and promotion outcome. Finalists add confusion matrices, class-wise metrics, seed variation, and measured hardware results. Failed or over-budget runs remain visible in the record.

## Refreshing this page

The [snapshot updater](../../code/analysis/update_current_work.py) always emits the 12 configured A-series runs. It can consume a local API-shaped JSON export without third-party packages or query W&B with its optional Python SDK. These commands run from the repository root:

```sh
# Local supplied snapshot; no network access or wandb package required.
python code/analysis/update_current_work.py --input-json current-runs.json

# Fetch current run summaries using the optional wandb SDK.
python code/analysis/update_current_work.py --wandb

# Include confirmed job submissions not yet registered on W&B.
python code/analysis/update_current_work.py --wandb --launch-record submitted-runs.json
```

`current-runs.json` must contain a `runs` array. Each entry uses `id`, `state`, a `summary` object, and optionally an ISO timestamp `updated_at`. IDs are the first 12 hexadecimal characters of SHA-256 of the configuration's `name`. Summary fields are the runner's `completed_epochs`, `phase`, `val_categorical_accuracy`, `val_macro_auc`, `best_feasible_val_accuracy`, `best_feasible_val_macro_auc`, `best_feasible_ebops`, and `best_feasible_epoch` (one-based). `_runtime` and `_timestamp` supply runtime and source freshness when available. The optional submission file contains `{"submitted_run_ids": ["deterministic-run-id"]}`; it records submission, not completion.

The updater reconstructs an allowlisted public record, checks reported best-checkpoint cost against the configured target, and preserves failures. It does not publish arbitrary summaries, raw configuration objects, machine metadata, or error traces. A `finished` W&B session with `phase=paused_for_promotion` remains paused. Full completion requires `phase=complete` and the configured 1,000 completed epochs. W&B fetch failures leave the previous snapshot unchanged. This cost check does not reload models or establish FPGA feasibility.

`--initialize` is only for creating the initial planning snapshot; it contains no run measurements and should not be used to refresh an active batch. Source `local_snapshot` means a supplied file was processed, while `wandb_api` means W&B was queried at the recorded refresh time. Per-run source timestamps can be older. Runtime identifies whether it came from cumulative training seconds or the W&B run/session counter.

Refresh is **manual unless an independently configured scheduled workflow is enabled**. The presence of this updater does not establish hourly updates, public anonymous API access, or a continuously live GitHub page. The W&B project link provides the interactive curves; the JSON and table preserve a timestamped snapshot.
