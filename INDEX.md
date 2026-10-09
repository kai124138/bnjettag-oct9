# Index  (built 2026-10-08 by tools/index.py; edit STUDY.md headers, not this file)

## Campaigns  (newest first; the type is the kind of job; phases: P preflight, R run, V verify, T report)

| date | type | status | campaign | phases | question |
| --- | --- | --- | --- | --- | --- |
| 2026-10-05 | pilot-program | amended [A5] pre-data (STUDY arbiter v3 PASS conditional on S1-S3, landed in [A5]; protocol re-frozen) | `campaigns/2026-10-05-pilot-program` | PR | Why does the binary-weight N=64 E transformer (d24, 2 heads) collapse at 350k EBOPs while A07 (d32, 4 heads) stays healthy at 5M, does health follow budget headroom, and which budget and fix are production candidates for A and NB? |
| 2026-09-29 | engineering | designed | `campaigns/2026-09-29-gpu-benchmark` | PRV | For Chang wave-1 production and Delta wave 2, which schedulable GPU product projects the earliest finish at the GPUs that can actually schedule, with every gate met, and is any more than 10 % earlier than the A10? |
| 2026-09-27 | delta-screen | frozen | `campaigns/2026-09-27-delta-screen` | PR | Which W2 single levers raise the binary N=64 tagger's validation accuracy above a same-seed replica within one cosine cycle, and is any of them above the family's do-nothing placebo at family-wise alpha 0.10? Null - none does. Full specification in Question (the ranking and its "ranked" / "descriptive" label; the floor-family package and G2 feasibility check); significance mode in Appendix A. |
| 2026-09-26 | engineering | scratch | `campaigns/2026-09-26-code-line-merge` *(stub)* | P | Can the two pipeline lines, bnjettag/code/hgq2 (research tree; pt-weighting, 24-run eval) and publication/code/hgq2 (GitHub; Engram, constituent study, post-conference configs), be merged into one tree whose CPU build and checkpoint-reload gates pass for every existing config? |
| 2026-09-26 | delta | designed | `campaigns/2026-09-26-delta` | – | Which of about 100 binarization, recipe, activation-width/EBOPs, architecture and input methods, alone or in pre-registered combinations, change the validation accuracy or 350k feasibility of the binary-weight N=64 tagger relative to the Sun et al. recipe anchor at the same seed, and which of those survive a full-recipe 8-seed confirmation? |
| 2026-09-26 | training-batch | frozen | `campaigns/2026-09-26-training-batch` | PR | What seed-mean ROC-test top-1 accuracy does the binary-weight N=64 tagger (Chang-sized architecture d24, 2 heads, 1 block, FFN 32, no PE [D21]; activation, softmax-output and softmax-table quantizers matched to Chang's code, [D19]) reach when trained with the Sun et al. recipe (7,000 epochs, batch 2,790, LR 3e-3 cosine restarts every 500 epochs, pT >= 2 GeV constituent gate, no sample weights) to a 350k EBOPs target, does it reach that budget non-degenerately in at least 6 of 8 seeds, what is its distance to the published single-model 79.4 % Deep Sets (HGQ) row of arXiv:2510.24784, and does that recipe beat our own recipe at the same target? Second wave (Kai request, 08:40, 2026-09-27): at iso-EBOPs (350k), does the binary arm A lose accuracy against the same model with learned-width HGQ weights (arm NB), and where does Sun et al.'s own xfm model on our split (arm H) sit against both? FP32-E (2026-09-27, Kai request (second set)): what is A − FP32-E, A binary at 350k against the same E model in unconstrained FP32 (arm FP32-E, a labelled package, not iso-EBOPs)? |
| 2026-09-25 | pt-weighting | published | `campaigns/2026-09-25-pt-weighting` *(stub)* | RV | Does per-class pT sample re-weighting (Option E, cap 5 or no cap) improve the N=8 W1A8 tagger's held-out AUC or its high-pT tails against the unweighted baseline, over 8 seeds? |
| 2026-09-23 | confirmation | unreviewed | `campaigns/2026-09-23-confirmation` *(stub)* | – | Confirmation campaign — 2026-09-23 |
| 2026-09-22 | constituent | unreviewed | `campaigns/2026-09-22-constituent-screen` *(stub)* | – | Matched N8/N64 screen LAUNCHED and first progress verified |
| 2026-09-21 | engram | unreviewed | `campaigns/2026-09-21-engram-publication` *(stub)* | – | Engram publication explicitly authorized and pushed |
| 2026-09-21 | results | unreviewed | `campaigns/2026-09-21-results-status` *(stub)* | – | Training results snapshot — 21 September 2026, 17:39 PDT |
| 2026-09-20 | continuation | unreviewed | `campaigns/2026-09-20-continuation-packed` *(stub)* | – | Full continuation,2026-09-20 |
| 2026-09-20 | performance | unreviewed | `campaigns/2026-09-20-performance-index` *(stub)* | T | Performance index 2026-09-20: per-arm metrics table across the batch |
| 2026-09-20 | status | unreviewed | `campaigns/2026-09-20-status` *(stub)* | – | Status snapshot 2026-09-20: which arms completed, which were repacked |
| 2026-09-19 | ops | unreviewed | `campaigns/2026-09-19-ops-incident-r6-hang` *(stub)* | – | Ops incident: r6 trainer hung on an idle GPU for 3d18h (rci-tide-gpu-03), diagnosis and recovery |
| 2026-09-18 | engram | unreviewed | `campaigns/2026-09-18-engram-study` *(stub)* | – | Engram-inspired memory tables in the binary tagger: accuracy first under an augmented cost cap (E00–E03 pilot) |
| 2026-09-18 | training | unreviewed | `campaigns/2026-09-18-training-batch` *(stub)* | – | Training batch 2026-09-18 (b00 seed arms; continuation of the 09-17 batch) |
| 2026-09-17 | synthesis | unreviewed | `campaigns/2026-09-17-synthesis-r4-gradual` *(stub)* | – | R4 gradual-EBOP model: HLS and Vivado synthesis — 2026-09-17 |
| 2026-09-17 | training | unreviewed | `campaigns/2026-09-17-training-batch` *(stub)* | – | r3 resuming correctly; mulder R4 crash signature captured |
| 2026-09-16 | accuracy | unreviewed | `campaigns/2026-09-16-accuracy-investigation` *(stub)* | – | Accuracy investigation — 16 September 2026 (PDT) |

## Literature  (57 notes; entry point `literature/INDEX.md`, never glob the folder)

## Code trees  (the canonical-tree decision needs these facts)

| tree | HEAD | last commit | uncommitted files |
| --- | --- | --- | --- |
| `.` | ? | ? | ? |
| `publication` | e56fd73 | 2026-09-30 | 6 |
| `published/bnjettag_results` | ? | ? | ? |
| `published/bnjettag-code` | ? | ? | ? |
| `published/bnjettag-methodology` | ? | ? | ? |

## Documents

| date | status | document | title |
| --- | --- | --- | --- |
| 2026-10-08 | current | `README.md` | BNJetTag Lab |
| 2026-10-08 | current | `SYSTEM.md` | SYSTEM — how research runs here |
| 2026-10-08 | draft | `docs/agent-harness.md` | Agent harness — current setup and target operating model |
| 2026-09-26 | current | `docs/conventions/README.md` | Conventions |
| 2026-09-26 | current | `docs/conventions/figures.md` | Figures |
| 2026-09-26 | current | `docs/conventions/fpga-synthesis.md` | FPGA synthesis |
| 2026-09-26 | current | `docs/conventions/jet-tagging-metrics.md` | Jet-tagging metrics |
| 2026-09-26 | current | `docs/conventions/quantization-and-cost.md` | Quantization and cost |
| 2026-09-26 | current | `docs/figures/README.md` | docs/figures |
| 2026-09-26 | current | `docs/infrastructure/obsidian-session-notes.md` | Session notes |
| 2026-09-26 | current | `docs/methodology/01-principles.md` | Principles |
| 2026-09-26 | current | `docs/methodology/03-phases.md` | Phases |
| 2026-09-26 | current | `docs/methodology/06-review.md` | Review protocol |
| 2026-09-26 | current | `docs/methodology/README.md` | Methodology |
| 2026-09-26 | current | `docs/methodology/appendix-checklist.md` | Artifact checklists |
| 2026-09-26 | current | `docs/style/CHOICES.md` | Choices |
| 2026-09-21 | current | `local/GPU_DIAGNOSIS_20260921.md` | GPU utilization diagnosis — 21 September 2026 PDT |
| 2026-09-20 | current | `docs/infrastructure/nrp-nautilus-setup.md` | NRP / Nautilus — Setup & Workflow Notes |
| 2026-09-17 | current | `docs/infrastructure/manual-round-runbook.md` | Running a round by hand — the full chain, start to finish |
| 2026-09-17 | current | `nrp-lab/README.md` | nrp-lab — a JupyterLab kernel on a Nautilus GPU |
| 2026-09-17 | current | `local/MANUAL_RUNBOOK_TRAINING_AND_R4_SYNTHESIS.md` | Manual runbook: training batch and original R4 hardware synthesis |
| 2026-09-14 | current | `local/README.md` | local — running the notebooks on this laptop |
| 2026-09-08 | current | `docs/infrastructure/README.md` | infrastructure/ — cluster and machine setup |
| 2026-09-08 | current | `docs/infrastructure/home-pc-cluster-recreation.md` | Home-PC cluster recreation — the prompt for Claude Code on that machine |
| 2026-09-08 | current | `docs/infrastructure/mulder-setup.md` | mulder — the Vitis HLS synthesis box |
| 2026-09-08 | current | `docs/infrastructure/wandb-layout.md` | Weights & Biases layout |
| 2026-09-08 | current | `docs/infrastructure/xup-licence-request.md` | Action: Vivado licence covering xcvu13p (Xilinx/AMD University Program) |
|  |  | `AGENTS.md` | AGENTS |
|  |  | `DATASET.md` | DATASET |
|  |  | `RESEARCH.md` | RESEARCH |
|  |  | `RULES.md` | RULES |
|  |  | `docs/PILOT_PROGRAM.md` | PILOT_PROGRAM |
|  |  | `docs/ROADMAP.md` | ROADMAP |
|  |  | `docs/SPRINT_PLAN.md` | SPRINT_PLAN |
|  |  | `docs/WELCOME_BACK.md` | WELCOME_BACK |
|  |  | `docs/chang-vs-bnjettag.md` | chang-vs-bnjettag |
|  |  | `docs/cheatsheet.md` | cheatsheet |
|  |  | `docs/infrastructure/gpu-selection-policy.md` | gpu-selection-policy |
|  |  | `docs/infrastructure/jev-lab.md` | jev-lab |
|  |  | `docs/infrastructure/lab-migration.md` | lab-migration |
|  |  | `docs/infrastructure/run-handoff.md` | run-handoff |
|  |  | `messages/2026-09-28-two-day-record.md` | 2026-09-28-two-day-record |
|  |  | `messages/BNJetTag-presentation-study-guide.md` | BNJetTag-presentation-study-guide |
|  |  | `messages/STATUS-2026-08-08.md` | STATUS-2026-08-08 |
|  |  | `messages/experiment-inventory-2026-09-22.md` | experiment-inventory-2026-09-22 |
|  |  | `messages/fp32-silicon-baseline-design-2026-09-02.md` | fp32-silicon-baseline-design-2026-09-02 |
|  |  | `messages/meeting-2026-08-25-speaker-notes.md` | meeting-2026-08-25-speaker-notes |
|  |  | `messages/notes-2026-08-13.md` | notes-2026-08-13 |
|  |  | `messages/poster-2026-08-23-speaker-notes.md` | poster-2026-08-23-speaker-notes |
|  |  | `messages/poster-A0-portrait-speech.md` | poster-A0-portrait-speech |
|  |  | `messages/poster-full-speech-2026-08-30.md` | poster-full-speech-2026-08-30 |
|  |  | `messages/r14-russell-draft.md` | r14-russell-draft |
|  |  | `messages/research-reset-2026-09-05.md` | research-reset-2026-09-05 |
|  |  | `messages/weekly-update-2026-08-18-speaker-notes.md` | weekly-update-2026-08-18-speaker-notes |

## Sessions  (136 notes in `sessions/`, newest `2026-09-28-training-batch-orchestrator.md`)
