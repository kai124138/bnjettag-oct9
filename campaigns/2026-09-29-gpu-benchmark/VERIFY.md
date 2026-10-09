# VERIFY — GPU-product throughput benchmark (2026-09-29-gpu-benchmark)

Phase 4, results-analyst, 2026-09-29 (data read 17:20-18:30Z). **Telemetry for a scheduling decision, not a physics
result.** There is no tagging metric, no data split and no comparison of trained models across products (STUDY l. 26). The
validation fields in the arm logs were not read. Every number below was recomputed from the Job artifacts by
`code/verify_bench.py`. That script also wrote every table into this file, and one row per printed number into
`verify.json`. It runs the pre-registered analysis, `code/bench_summary.py`, unchanged, and then checks it with an
independent parse. Governing documents: STUDY.md (Amendment 1, [D1]-[D6], rules 1-6, critical v2 B3 and B6), PREFLIGHT.md,
RUN.md. **The choice of product is Kai's;** this artifact names what the pre-registered rule favours and where the data stop.

## In brief

- **Coverage.** Every Job whose pod started finished every phase (counts table). Seven Jobs never started within 6 h:
  the L40, L40S and A40 in both pod shapes, and the RTX A6000's K_rule shape. By rule 3 they are "not practical now".
- **Gates.** Every arm-run completed 21 epochs with exit 0 and `CHECKPOINT_VERIFICATION_PASS` (rule 6). Every pod printed
  `FINGERPRINT 11559681 expected 11559681` (rule 2). No OOM exit and no non-finite loss occurred. Every arm confirmed its CPU pin,
  and no sampled thread left the pinned CPUs (rule 5, with the v2 B1 filter).
- **One exclusion.** RTX 4090, class E, K=5: the pod peak is 91.9 % of memory.total (rule 1), so the 4090 enters T with E at K=4
  only. Two more phases pass rule 1 narrowly, on 60-s samples: the RTX 3090 E at K=5 (89.2 %) and the A100 E at K=16 (88.8 %).
- **The A10 baseline counts, and is not flagged.** Each A10 Job ran once and completed (B3). The one-sided B6 check against
  the pure-pack canary gives ratios 0.9969 (E, K=4) and 1.0643 (A07, K=2), both under the 1.10 limit.
- **Campaign (a), Chang wave 1.** At each assumed G the pre-registered rule favours a single product, with no tie. That
  product is the A100-SXM4-80GB at G = 1 (the a100 quota allows one GPU now: a single-GPU campaign) and the RTX 4090 at every
  G from 2 to 16. The A10's projected finish is 1.651 to 1.876 times as long as the 4090's. The null ("no practical
  candidate more than 10 % earlier than the A10") is rejected for campaign (a) at every assumed G of the grid, and cannot be
  judged at the G that can actually schedule, since G_p was not measured.
- **Campaign (b), the Delta screen's wave two.** [A1] allows its A07 packs only on the large-memory products, which leaves
  two measured products (≥ 45 GB): the A100 (one GPU under the quota) and the RTX A6000 (its K_low shape only). The A100 leads
  at G = 1 and the A6000 at every larger G. The A10 is not [A1]-eligible, so the pre-registered comparison with the A10 has
  no eligible baseline for campaign (b). If Kai overrides [A1], the RTX 4090 leads at every G above 1.
- **G_p was not measured.** No [D4] probe Job ran, so every T is at an assumed G. The pools differ widely (static ceilings
  table), and the 4090's pool is the smallest of the leaders. The break-even tables give how many GPUs of each product match
  the leader.
- **Node spread was not measured** ([L1]: one node per Job shape). No cross-product ratio here has an interval. The
  pre-registered tie margin of 10 % is the only allowance. Every leader's margin survives inflating that leader's s by the
  factor 1.0643, the largest B6 deviation.
- **One RUN.md claim does not reproduce.** RUN.md l. 53-54 says "proc_threads is 25 on every one of them". Recomputed on the
  same rows, it is 25 on 341 and 61 on 5. The claim is descriptive; the pin result it supports stands.

| count | value | source |
| --- | --- | --- |
| Jobs applied (two per product, eight products) | 16 | campaigns/2026-09-29-gpu-benchmark/manifests/bench_plan.json |
| Jobs complete, every phase ok | 9 | logs/*/job.json (succeeded 1), pod logs BENCH_DONE |
| Jobs "not practical now" (rule 3, [D6]) | 7 | RUN.md l. 89-91, 114-117; logs/*/scheduler-message-6h.txt |
| phases measured (product x class x K) | 18 | data/bench_summary.json |
| arm-runs, each at 21 epochs with exit 0 | 70 | pod logs, ARM_EXIT lines |
| arm-runs with CHECKPOINT_VERIFICATION_PASS (rule 6) | 70 | arm logs |
| arm-runs with a FAIL, an OOM exit or a non-finite loss | 0 | arm logs, pod logs |
| pods printing FINGERPRINT 11559681 expected 11559681 (rule 2) | 9 | pod logs |
| phases excluded under rule 1 | 1 | data/bench_summary.json |
| phases above the rule-5 limit of 2.1 cores per arm | 0 | data/bench_summary.json |
| sampler rows past epoch 1 with an arm thread outside its pinned CPUs | 0 | data/gpu-bench/*/samples.csv |
| run-epochs timed | 1,470 | arm logs |

## Data and provenance

The PVC directory `/data/chang-n64-20260926/gpu-bench/` was copied read-only through the pilot pod
`kai-chang0926-pilotb5-42abed-0-qqjmt` with GNU tar. The copy leaves out model files, checkpoints, validation predictions
and activation-width traces, none of which the analysis reads. A full inventory of every PVC file (size, mtime) is kept
in `data/pvc_inventory_full.tsv`, and every copied file's size equals its inventory entry. The copy is `chmod a-w`.

The analysis root `data/bench-root/<slug>-<shape>/` is made of symlinks. It points at the PVC copy for `plan.json`,
`samples.csv`, `bench_result.json` and the phase directories. From `logs/kai-gpubench-<slug>-<shape>/` it takes `job.json`,
`pod.json` and the kubectl pod log, the latter as `pod-<pod>.log`. The kubectl log is the PVC tee plus its first two lines
(`BENCH_POD … <stamp>`, `HOSTNAME_NODE`); the script asserts this on all nine pods. `bench_summary.py` needs the `BENCH_POD`
stamp to order A10 attempts (B3). The seven deleted Jobs have no PVC data, and they enter through `--plan` as rule-3 rows.

| item | value |
| --- | --- |
| PVC `gpu-bench/` files, all (inventory `data/pvc_inventory_full.tsv`) | 1,678 files, 1,568,375,293 bytes |
| left on the PVC: `*.keras`, `*.npz`, `activation_widths.jsonl`, `checkpoints/` (never read by the analysis) | 784 files, 1,565,906,836 bytes |
| copied read-only to `data/gpu-bench/` (every size equal to the inventory: True) | 894 files, 2,468,457 bytes |
| `code/bench_summary.py` sha256 (fixer v2, PREFLIGHT l. 55) | `cd5f5b6410e09b4e43a16ca97d16905deb1c108fe719cf1e20a7e84924f514ef` |
| in-process `summarize_bench` equals the CLI output `data/bench_summary.json` | True |
| a100 quota snapshot 2026-09-29T18:28:07Z (`data/resourcequota_snapshot.json`) | used 23 of 24, headroom 1 |

## Headline: every product × class × K (STUDY [D1], rules 1-6)

Definitions (STUDY l. 47-51, PREFLIGHT "Analysis script"):

- **s [D1].** For each arm, (9 × median untraced + median traced) / 10 over one-based epochs 2-21: 18 untraced epochs and the
  traced epochs 10 and 20, from the arm's single fresh attempt (`resume_epoch=0`). The phase's s is its slowest arm. Check:
  with untraced u and traced u + t the formula gives u + t/10, as [D1] states. Every arm's traced epochs are exactly 1, 10
  and 20.
- **R** = K × 3600 / s, run-epochs per GPU-hour; every phase has all K arms at 21 epochs, so R is defined on every row.
- **Total elapsed per run-epoch** = phase wall seconds ÷ (K × 21). It includes epoch 1 (the first trace), the start
  stagger and `verify_selected`, so it is not a steady-state rate.
- **Peak.** The largest pod `nvidia-smi` memory.used in the phase's 60-s samples, against memory.total.
- **Utilization.** The mean over all the phase's samples, and over the steady window (all K arms live, all past epoch 1,
  none at epoch 21).
- **Cores per arm.** Steady cgroup CPU cores ÷ K, against rule 5's 2.1.
- **Q.** Job creation (the apply) to the container's `startedAt`: the B1 fallback, because a finished pod carries
  `Ready False`. It is one pod per shape, a snapshot [L3] standing in for the probe's Q_p (critical v2 C7).
- **n.** K arms × 20 epochs per arm for s and R. The sample counts are in the gates table and in `verify.json`.

| product | Job | class | K | n (arms × epochs) | s [D1], s/epoch | R, run-epochs per GPU-h | total elapsed s per run-epoch | peak GPU MiB / card MiB | peak % of card (rule 1: 90 %) | GPU util %, all / steady | cores per arm (rule 5: 2.1) | Q, h (s), apply → running | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A10 | krule | E | 4 | 4 × 20 | 114.10 | 126.2 | 30.1 | 17,425 / 23,028 | 75.7 % | 97.5 / 100.0 | 0.556 | 0.01 (19 s) | in T |
| A10 | krule | A07 | 2 | 2 × 20 | 96.56 | 74.6 | 53.2 | 16,906 / 23,028 | 73.4 % | 96.4 / 99.1 | 0.543 | 0.01 (19 s) | in T |
| A10 | klow | E | 3 | 3 × 20 | 80.75 | 133.8 | 29.8 | 13,069 / 23,028 | 56.8 % | 95.3 / 99.7 | 0.575 | 0.01 (18 s) | in T |
| A10 | klow | A07 | 1 | 1 × 20 | 45.73 | 78.7 | 56.2 | 8,455 / 23,028 | 36.7 % | 80.2 / 91.3 | 0.588 | 0.01 (18 s) | in T |
| A100-SXM4-80GB | krule | E | 16 | 16 × 20 | 177.46 | 324.6 | 11.6 | 72,709 / 81,920 | 88.8 % | 99.3 / 100.0 | 0.520 | 0.29 (1,032 s) | in T |
| A100-SXM4-80GB | krule | A07 | 8 | 8 × 20 | 142.23 | 202.5 | 18.9 | 69,125 / 81,920 | 84.4 % | 98.0 / 100.0 | 0.544 | 0.29 (1,032 s) | in T |
| A100-SXM4-80GB | klow | E | 4 | 4 × 20 | 47.10 | 305.7 | 14.5 | 18,181 / 81,920 | 22.2 % | 88.1 / 98.5 | 0.653 | 3.82 (13,744 s) | in T |
| A100-SXM4-80GB | klow | A07 | 2 | 2 × 20 | 45.05 | 159.8 | 27.5 | 17,285 / 81,920 | 21.1 % | 78.8 / 95.7 | 0.654 | 3.82 (13,744 s) | in T |
| RTX 3090 | krule | E | 5 | 5 × 20 | 85.51 | 210.5 | 18.0 | 21,921 / 24,576 | 89.2 % | 99.9 / 100.0 | 0.511 | 1.50 (5,408 s) | in T |
| RTX 3090 | krule | A07 | 2 | 2 × 20 | 57.11 | 126.1 | 31.7 | 16,963 / 24,576 | 69.0 % | 96.4 / 99.3 | 0.534 | 1.50 (5,408 s) | in T |
| RTX 3090 | klow | E | 4 | 4 × 20 | 71.08 | 202.6 | 18.8 | 17,538 / 24,576 | 71.4 % | 94.6 / 100.0 | 0.543 | 2.45 (8,829 s) | in T |
| RTX 3090 | klow | A07 | 1 | 1 × 20 | 30.85 | 116.7 | 38.8 | 8,484 / 24,576 | 34.5 % | 61.6 / 74.3 | 0.623 | 2.45 (8,829 s) | in T |
| RTX 4090 | krule | E | 5 | 5 × 20 | 68.28 | 263.6 | 14.4 | 22,571 / 24,564 | 91.9 % | 95.4 / 100.0 | 0.586 | 1.50 (5,405 s) | excluded: rule 1: pod peak above 90 % of memory.total |
| RTX 4090 | krule | A07 | 2 | 2 × 20 | 48.29 | 149.1 | 28.1 | 17,223 / 24,564 | 70.1 % | 96.8 / 99.9 | 0.593 | 1.50 (5,405 s) | in T |
| RTX 4090 | klow | E | 4 | 4 × 20 | 55.41 | 259.9 | 15.0 | 18,058 / 24,564 | 73.5 % | 97.2 / 99.9 | 0.606 | 3.91 (14,060 s) | in T |
| RTX 4090 | klow | A07 | 1 | 1 × 20 | 26.04 | 138.3 | 34.1 | 8,614 / 24,564 | 35.1 % | 65.4 / 84.4 | 0.667 | 3.91 (14,060 s) | in T |
| RTX A6000 | klow | E | 4 | 4 × 20 | 77.32 | 186.2 | 20.4 | 17,562 / 49,140 | 35.7 % | 100.0 / 100.0 | 0.512 | 4.38 (15,770 s) | in T |
| RTX A6000 | klow | A07 | 2 | 2 × 20 | 65.53 | 109.9 | 36.1 | 16,975 / 49,140 | 34.5 % | 95.4 / 98.8 | 0.525 | 4.38 (15,770 s) | in T |
| L40S | klow | E, A07 | E 4 / A07 2 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.09 (21,927 s) | not practical now (rule 3, [D6]) |
| L40 | klow | E, A07 | E 4 / A07 2 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.04 (21,739 s) | not practical now (rule 3, [D6]) |
| A40 | klow | E, A07 | E 4 / A07 2 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.04 (21,730 s) | not practical now (rule 3, [D6]) |
| L40S | krule | E, A07 | E 9 / A07 4 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.85 (24,660 s) | not practical now (rule 3, [D6]) |
| RTX A6000 | krule | E, A07 | E 9 / A07 5 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.85 (24,657 s) | not practical now (rule 3, [D6]) |
| L40 | krule | E, A07 | E 9 / A07 4 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.85 (24,654 s) | not practical now (rule 3, [D6]) |
| A40 | krule | E, A07 | E 9 / A07 4 | 0 (never Running) | – | – | – | – | – | – | – | ≥ 6.85 (24,651 s) | not practical now (rule 3, [D6]) |

The not-practical rows give Q as a lower bound, from the apply to the deletion; those pods never started.

## Gates per phase (rules 1, 2, 5, 6) and the per-arm spread

| product | Job | phase | node (CPU) | arms ok, exit 0 at 21 epochs | CHECKPOINT_VERIFICATION PASS (rule 6) | OOM (exit 7) | non-finite loss | fingerprint 11559681 (rule 2) | ARM_CPUS OK / thread rows in pin (rule 5) | cache = anchor | host RSS peak, MB | per-arm s, min–max (sd) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A10 | krule | p1-E-k4 | hcc-nrp-shor-c6009.unl.edu (AMD EPYC 7502 32-Core) | 4/4 | 4/4 | no | no | match | 4/4; 144 rows, 0 outside | yes | 2,368 | 110.32–114.10 (1.65) |
| A10 | krule | p2-A07-k2 | hcc-nrp-shor-c6009.unl.edu (AMD EPYC 7502 32-Core) | 2/2 | 2/2 | no | no | match | 2/2; 66 rows, 0 outside | yes | 2,441 | 96.13–96.56 (0.31) |
| A10 | klow | p3-E-k3 | hcc-nrp-shor-c5821.unl.edu (AMD EPYC 7502 32-Core) | 3/3 | 3/3 | no | no | match | 3/3; 80 rows, 0 outside | yes | 2,323 | 79.86–80.75 (0.46) |
| A10 | klow | p4-A07-k1 | hcc-nrp-shor-c5821.unl.edu (AMD EPYC 7502 32-Core) | 1/1 | 1/1 | no | no | match | 1/1; 15 rows, 0 outside | yes | 2,415 | 45.73–45.73 (K = 1) |
| A100-SXM4-80GB | krule | p1-E-k16 | sphinx.sdstate.edu (AMD EPYC 7713 64-Core) | 16/16 | 16/16 | no | no | match | 16/16; 866 rows, 0 outside | yes | 2,678 | 166.58–177.46 (3.41) |
| A100-SXM4-80GB | krule | p2-A07-k8 | sphinx.sdstate.edu (AMD EPYC 7713 64-Core) | 8/8 | 8/8 | no | no | match | 8/8; 361 rows, 0 outside | yes | 2,684 | 134.80–142.23 (2.84) |
| A100-SXM4-80GB | klow | p3-E-k4 | gp-engine.usd.edu (AMD EPYC 7713 64-Core) | 4/4 | 4/4 | no | no | match | 4/4; 58 rows, 0 outside | yes | 2,365 | 45.78–47.10 (0.66) |
| A100-SXM4-80GB | klow | p4-A07-k2 | gp-engine.usd.edu (AMD EPYC 7713 64-Core) | 2/2 | 2/2 | no | no | match | 2/2; 28 rows, 0 outside | yes | 2,473 | 41.42–45.05 (2.57) |
| RTX 3090 | krule | p1-E-k5 | nautilus01.hsrn.nyu.edu (AMD EPYC 7443P 24-Core) | 5/5 | 5/5 | no | no | match | 5/5; 134 rows, 0 outside | yes | 2,438 | 81.88–85.51 (1.41) |
| RTX 3090 | krule | p2-A07-k2 | nautilus01.hsrn.nyu.edu (AMD EPYC 7443P 24-Core) | 2/2 | 2/2 | no | no | match | 2/2; 38 rows, 0 outside | yes | 2,491 | 56.15–57.11 (0.67) |
| RTX 3090 | klow | p3-E-k4 | fiona-1.famu.edu (AMD EPYC 7453 28-Core) | 4/4 | 4/4 | no | no | match | 4/4; 87 rows, 0 outside | yes | 2,380 | 67.75–71.08 (1.51) |
| RTX 3090 | klow | p4-A07-k1 | fiona-1.famu.edu (AMD EPYC 7453 28-Core) | 1/1 | 1/1 | no | no | match | 1/1; 10 rows, 0 outside | yes | 2,413 | 30.85–30.85 (K = 1) |
| RTX 4090 | krule | p1-E-k5 | hcc-nrp-shor-c5834.unl.edu (AMD EPYC 7282 16-Core) | 5/5 | 5/5 | no | no | match | 5/5; 104 rows, 0 outside | yes | 2,418 | 63.92–68.28 (1.81) |
| RTX 4090 | krule | p2-A07-k2 | hcc-nrp-shor-c5834.unl.edu (AMD EPYC 7282 16-Core) | 2/2 | 2/2 | no | no | match | 2/2; 32 rows, 0 outside | yes | 2,457 | 47.54–48.29 (0.53) |
| RTX 4090 | klow | p3-E-k4 | hcc-nrp-shor-c5226.unl.edu (AMD EPYC 7282 16-Core) | 4/4 | 4/4 | no | no | match | 4/4; 66 rows, 0 outside | yes | 2,368 | 51.78–55.41 (1.55) |
| RTX 4090 | klow | p4-A07-k1 | hcc-nrp-shor-c5226.unl.edu (AMD EPYC 7282 16-Core) | 1/1 | 1/1 | no | no | match | 1/1; 9 rows, 0 outside | yes | 2,434 | 26.04–26.04 (K = 1) |
| RTX A6000 | klow | p3-E-k4 | gpu00.nrp.hpc.udel.edu (AMD EPYC 7443P 24-Core) | 4/4 | 4/4 | no | no | match | 4/4; 98 rows, 0 outside | yes | 2,370 | 74.27–77.32 (1.43) |
| RTX A6000 | klow | p4-A07-k2 | gpu00.nrp.hpc.udel.edu (AMD EPYC 7443P 24-Core) | 2/2 | 2/2 | no | no | match | 2/2; 43 rows, 0 outside | yes | 2,432 | 64.53–65.53 (0.71) |

The last column is the spread across the arms of a phase, with seeds 1-8 per class; this is a timing study, not a seed
study. The spread comes from start order and the arms' shared GPU, not from nodes. [D1] takes the slowest arm on purpose,
since a pack ends with it.

## [D2] memory check: predicted and measured peaks

| product | class | K_rule | predicted peak % (PREFLIGHT l. 237-244, from A10 per-process peaks) | measured pod peak % | measured per-process peak, MiB | A10 per-process peak m_k, MiB ([D2]) |
| --- | --- | --- | --- | --- | --- | --- |
| A10 | E | 4 | 75.6 % | 75.7 % | 4,350 | 4,350 |
| A10 | A07 | 2 | 73.4 % | 73.4 % | 8,446 | 8,446 |
| A100-SXM4-80GB | E | 16 | 85.0 % | 88.8 % | 4,538 | 4,350 |
| A100-SXM4-80GB | A07 | 8 | 82.5 % | 84.4 % | 8,634 | 8,446 |
| RTX 3090 | E | 5 | 88.5 % | 89.2 % | 4,378 | 4,350 |
| RTX 3090 | A07 | 2 | 68.7 % | 69.0 % | 8,474 | 8,446 |
| RTX 4090 | E | 5 | 88.5 % | 91.9 % | 4,508 | 4,350 |
| RTX 4090 | A07 | 2 | 68.8 % | 70.1 % | 8,604 | 8,446 |
| RTX A6000 | E | 4 (K_low; K_rule not practical now) | – | 35.7 % | 4,384 | 4,350 |
| RTX A6000 | A07 | 2 (K_low; K_rule not practical now) | – | 34.5 % | 8,480 | 8,446 |

[D2] sized K_rule from the A10's per-process peaks. The per-process footprint is larger on every other card. That is why the
4090's E at K=5 went over 90 % although PREFLIGHT predicted 88.5 %.

## Reproduction check

The independent parse (`code/verify_bench.py`: its own regular expressions over arm logs, pod logs, `samples.csv`,
`job.json` and `pod.json`) recomputed 19 fields per phase. Each was checked against `bench_summary.py`'s row: equality for
s, R, wall per run-epoch, peak, utilization, cores per arm, Q and RSS, plus the flags. The in-process `summarize_bench` output
equals the CLI's `data/bench_summary.json`.

| product | Job | phase | fields recomputed by the independent parse (s, R, wall per run-epoch, peak, util all and steady, cores/K, Q, RSS, traced epochs, epoch count, attempts, verification, ARM_CPUS, thread masks, loss, exits, fingerprint, cache, card MiB) | result |
| --- | --- | --- | --- | --- |
| A10 | krule | p1-E-k4 | 19 checks against `bench_summary.py` | ✓ all equal |
| A10 | krule | p2-A07-k2 | 19 checks against `bench_summary.py` | ✓ all equal |
| A10 | klow | p3-E-k3 | 19 checks against `bench_summary.py` | ✓ all equal |
| A10 | klow | p4-A07-k1 | 19 checks against `bench_summary.py` | ✓ all equal |
| A100-SXM4-80GB | krule | p1-E-k16 | 19 checks against `bench_summary.py` | ✓ all equal |
| A100-SXM4-80GB | krule | p2-A07-k8 | 19 checks against `bench_summary.py` | ✓ all equal |
| A100-SXM4-80GB | klow | p3-E-k4 | 19 checks against `bench_summary.py` | ✓ all equal |
| A100-SXM4-80GB | klow | p4-A07-k2 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 3090 | krule | p1-E-k5 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 3090 | krule | p2-A07-k2 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 3090 | klow | p3-E-k4 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 3090 | klow | p4-A07-k1 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 4090 | krule | p1-E-k5 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 4090 | krule | p2-A07-k2 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 4090 | klow | p3-E-k4 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX 4090 | klow | p4-A07-k1 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX A6000 | klow | p3-E-k4 | 19 checks against `bench_summary.py` | ✓ all equal |
| RTX A6000 | klow | p4-A07-k2 | 19 checks against `bench_summary.py` | ✓ all equal |

The telemetry that RUN.md quotes:

| RUN.md claim | where | claimed | recomputed | source of the recompute | ✓/✗ |
| --- | --- | --- | --- | --- | --- |
| a10-klow p3-E-k3 PHASE_DONE wall | RUN.md l. 71 | 1,880.3 s | 1,880.3 s | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-klow/kai-gpubench-a10-klow-smvnq.log L153` | ✓ |
| a10-klow p3-E-k3 steady cores per arm | RUN.md l. 71 | 0.575 | 0.575 (samples.csv pairs: 0.575) | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-klow/kai-gpubench-a10-klow-smvnq.log L153` | ✓ |
| a10-klow p4-A07-k1 PHASE_DONE wall | RUN.md l. 71 | 1,180.1 s | 1,180.1 s | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-klow/kai-gpubench-a10-klow-smvnq.log L158` | ✓ |
| a10-klow p4-A07-k1 steady cores per arm | RUN.md l. 71 | 0.588 | 0.588 (samples.csv pairs: 0.588) | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-klow/kai-gpubench-a10-klow-smvnq.log L158` | ✓ |
| a10-krule p1-E-k4 PHASE_DONE wall | RUN.md l. 72 | 2,530.5 s | 2,530.5 s | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-krule/kai-gpubench-a10-krule-g8b5c.log L155` | ✓ |
| a10-krule p1-E-k4 steady cores per arm | RUN.md l. 72 | 0.556 | 0.556 (samples.csv pairs: 0.556) | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-krule/kai-gpubench-a10-krule-g8b5c.log L155` | ✓ |
| a10-krule p2-A07-k2 PHASE_DONE wall | RUN.md l. 72 | 2,235.3 s | 2,235.3 s | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-krule/kai-gpubench-a10-krule-g8b5c.log L162` | ✓ |
| a10-krule p2-A07-k2 steady cores per arm | RUN.md l. 72 | 0.543 | 0.543 (samples.csv pairs: 0.543) | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a10-krule/kai-gpubench-a10-krule-g8b5c.log L162` | ✓ |
| a100-sxm4-80gb-krule p1-E-k16 PHASE_DONE wall | RUN.md l. 73 | 3,902.7 s | 3,902.7 s | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a100-sxm4-80gb-krule/kai-gpubench-a100-sxm4-80gb-krule-kqnx5.log L177` | ✓ |
| a100-sxm4-80gb-krule p1-E-k16 steady cores per arm | RUN.md l. 73 | 0.520 | 0.520 (samples.csv pairs: 0.520) | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a100-sxm4-80gb-krule/kai-gpubench-a100-sxm4-80gb-krule-kqnx5.log L177` | ✓ |
| a100-sxm4-80gb-krule p2-A07-k8 PHASE_DONE wall | RUN.md l. 73 | 3,181.5 s | 3,181.5 s | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a100-sxm4-80gb-krule/kai-gpubench-a100-sxm4-80gb-krule-kqnx5.log L196` | ✓ |
| a100-sxm4-80gb-krule p2-A07-k8 steady cores per arm | RUN.md l. 73 | 0.544 | 0.544 (samples.csv pairs: 0.544) | `campaigns/2026-09-29-gpu-benchmark/logs/kai-gpubench-a100-sxm4-80gb-krule/kai-gpubench-a100-sxm4-80gb-krule-kqnx5.log L196` | ✓ |
| A100 pin check: proc rows past epoch 1 | RUN.md l. 52 | 346 | 346 | `campaigns/2026-09-29-gpu-benchmark/data/gpu-bench/a100-sxm4-80gb-krule/samples.csv data rows 1-487 (L2-L488), the read RUN.md made at about 10:30Z` | ✓ |
| A100 pin check: rows outside the pinned set | RUN.md l. 52-53 | 0 | 0 | `campaigns/2026-09-29-gpu-benchmark/data/gpu-bench/a100-sxm4-80gb-krule/samples.csv data rows 1-487 (L2-L488), the read RUN.md made at about 10:30Z` | ✓ |
| A100 pin check: proc_threads is 25 on every one of them | RUN.md l. 53-54 | 25 on all 346 | 25 on 341, 61 on 5 | `campaigns/2026-09-29-gpu-benchmark/data/gpu-bench/a100-sxm4-80gb-krule/samples.csv data rows 1-487 (L2-L488), the read RUN.md made at about 10:30Z` | ✗ (descriptive; the pin result above stands) |
| A100 pin check: GPU utilization mean over 31 samples | RUN.md l. 55 | 95.3 % | 95.26 % over 31 samples in the first 487 rows | `campaigns/2026-09-29-gpu-benchmark/data/gpu-bench/a100-sxm4-80gb-krule/samples.csv data rows 1-487 (L2-L488), the read RUN.md made at about 10:30Z` | ✓ |
| A100 pin check: peak GPU memory | RUN.md l. 55-56 | 72,709 / 81,920 MiB (88.8 %) | 72,709 MiB; whole phase 72,709 MiB | `campaigns/2026-09-29-gpu-benchmark/data/gpu-bench/a100-sxm4-80gb-krule/samples.csv data rows 1-487 (L2-L488), the read RUN.md made at about 10:30Z` | ✓ |
| A100 K_rule started about 17 min after its apply | RUN.md l. 46-47 | about 17 min | 17.2 min | job.json, pod.json | ✓ |

RUN.md's A100 read at about 10:30Z was taken while the phase was running. The first rows of `samples.csv`, as many as RUN.md
counted, reproduce it; its GPU samples include the setup row. The whole phase has more samples, and its values are in the
headline table. The two are not compared with each other.

## Rule 3: the seven "not practical now" Jobs

| Job | applied (job.json) | deleted (RUN.md) | pod state at deletion (pod.json) | Q lower bound, h | scheduler: the product-node buckets | anti-affinity named |
| --- | --- | --- | --- | --- | --- | --- |
| `kai-gpubench-l40s-klow` | 2026-09-29T09:32:18Z | 2026-09-29T15:37:45Z (RUN.md l. 89) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.09 | 1 Insufficient cpu, 2 Insufficient nvidia.com/gpu | no |
| `kai-gpubench-l40-klow` | 2026-09-29T09:35:26Z | 2026-09-29T15:37:45Z (RUN.md l. 90) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.04 | 5 Insufficient cpu, 6 Insufficient nvidia.com/gpu | no |
| `kai-gpubench-a40-klow` | 2026-09-29T09:35:35Z | 2026-09-29T15:37:45Z (RUN.md l. 91) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.04 | 1 Insufficient cpu, 2 Insufficient nvidia.com/a40 | no |
| `kai-gpubench-l40s-krule` | 2026-09-29T10:27:54Z | 2026-09-29T17:18:54Z (RUN.md l. 114) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.85 | 2 Insufficient cpu, 2 Insufficient nvidia.com/gpu | no |
| `kai-gpubench-rtx-a6000-krule` | 2026-09-29T10:27:57Z | 2026-09-29T17:18:54Z (RUN.md l. 115) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.85 | 3 Insufficient nvidia.com/rtxa6000, 5 Insufficient cpu | no |
| `kai-gpubench-l40-krule` | 2026-09-29T10:28:00Z | 2026-09-29T17:18:54Z (RUN.md l. 116) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.85 | 6 Insufficient cpu, 6 Insufficient nvidia.com/gpu | no |
| `kai-gpubench-a40-krule` | 2026-09-29T10:28:03Z | 2026-09-29T17:18:54Z (RUN.md l. 117) | Pending, no startTime, PodScheduled False (Unschedulable) | ≥ 6.85 | 2 Insufficient cpu, 2 Insufficient nvidia.com/a40 | no |

Each pod was Pending with no `startTime` when it was deleted. Every scheduler message counts the product's nodes as short of
GPU, CPU or both. None names the pod anti-affinity, so the self-inflicted wait of critical v2 C7 did not occur. RUN.md records
the K_rule wave's 6-h check at 17:18Z instead of 16:28Z, because the orchestrator's laptop lost DNS. It changes nothing: the
saved pod JSON shows those pods still Pending at 17:18Z.

## The A10 baseline: B3 attempt rule and B6 one-sided check

| A10 phase | attempt (B3) | counted | A10 s [D1] | slowest arm of the pure-pack canary | limit (× 1.10) | ratio | flag (B6) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E K=4 (krule) | 1 of 1 | True | 114.10 | 114.455 | 125.9005 | 0.9969 | no |
| A07 K=2 (krule) | 1 of 1 | True | 96.56 | 90.730 | 99.8030 | 1.0643 | no |
| E K=3 (klow) | 1 of 1 | True | 80.75 | – (not an anchored K) | – | – | – |
| A07 K=1 (klow) | 1 of 1 | True | 45.73 | – (not an anchored K) | – | – | – |

B3: each A10 Job had one attempt, and it completed, so the first complete attempt counts. No phase is listed out of T, and
both classes have a counted A10 phase with R ("A10 baseline measured"). B6 checks E at K=4 and A07 at K=2 only (STUDY l.
163-165); neither is flagged. The pilot telemetry [L2] is not used anywhere in T.

## Card speed at equal K

K_low was chosen to isolate card speed at equal K ([D2]). A ratio above 1.00 means that product is faster than the A10.

| class, K | product | Job | s [D1] | A10 s / product s (1.00 = A10 speed) |
| --- | --- | --- | --- | --- |
| E K=4 | A10 | krule | 114.10 | 1.00 |
| E K=4 | A100-SXM4-80GB | klow | 47.10 | 2.42 |
| E K=4 | RTX 3090 | klow | 71.08 | 1.61 |
| E K=4 | RTX 4090 | klow | 55.41 | 2.06 |
| E K=4 | RTX A6000 | klow | 77.32 | 1.48 |
| A07 K=2 | A10 | krule | 96.56 | 1.00 |
| A07 K=2 | A100-SXM4-80GB | klow | 45.05 | 2.14 |
| A07 K=2 | RTX 3090 | krule | 57.11 | 1.69 |
| A07 K=2 | RTX 4090 | krule | 48.29 | 2.00 |
| A07 K=2 | RTX A6000 | klow | 65.53 | 1.47 |
| A07 K=1 | A10 | klow | 45.73 | 1.00 |
| A07 K=1 | RTX 3090 | klow | 30.85 | 1.48 |
| A07 K=1 | RTX 4090 | klow | 26.04 | 1.76 |

These are ratios of single-node measurements. Node spread is unmeasured [L1], so no interval exists on them. Inside 1.10 is
a tie by rule. On the A10 itself, K_low gives the higher R in both classes: 133.8 against 126.2 run-epochs per GPU-hour for
E, and 78.7 against 74.6 for A07 (headline table). That is why T takes the A10 at its K_low K pair (3/1) at every G.

## Noise: what this benchmark can and cannot resolve

- **Arm spread within a phase** is in the gates table (sd over arms, ddof=1). It is small next to the cross-product ratios,
  and [D1] already takes the slowest arm.
- **Node-to-node spread is unmeasured** [L1]. Each Job shape ran on one node, and no product ran the same K on two nodes.
  No interval can be put on any ratio between products. The STUDY's 10 % tie margin is the pre-registered allowance.
- **The only evidence across nodes and bundles** is B6: the same card, class and K on another node and bundle, with W&B on,
  gives ratios 0.9969 and 1.0643.
- **Stress test** (the checks tables): each leader's s is inflated by the factor 1.0643 and T is recomputed. No leader changes
  at any G, and no tie set grows.
- **Design note.** One node per shape can separate the products whose T ratios are well above 1.10, which covers every leader
  here. It cannot separate ratios near 1.10. Two nodes per shape, or a timed probe, would give a spread estimate.

## Projection T(p)

**Formula** (STUDY l. 53-58): T(p) = Q_p + C_p + max(Σ_k W_k·s_k / (3600·K_k·G), max_k H_k·s_k / 3600), in hours. W_k and
H_k come from the STUDY's Question (l. 20-23). Campaign (a) has E and A07 with a 7,000-epoch horizon; its R class (8,000
run-epochs at batch 256) is not timed [A2] and is left out of T. Campaign (b) has E and A07 by base class [A3], with longest
horizons 1,000 and 2,000 epochs. Readings used, each a flagged decision below:

- **K per [D3].** At each G, the K pair (E/A07) with the earliest T, over the non-excluded K of that product. The pair is
  printed beside each T.
- **C_p.** For every product but the A10, Q plus 110 × the larger class s (the two class canaries run in parallel), taken in
  full as an upper bound. The sum reading is in the decomposition tables. C_p is 0 for the A10 (STUDY l. 55-56).
- **Q_p.** The benchmark pod's wait for the shape that held that K; the larger of the two when a pair spans both shapes.
- **G.** An assumed G_p, because [D4]'s observed count was not measured. The a100 quota headroom is known: 1 at the 18:28:07Z
  snapshot. The capped view puts each product at min(G, quota headroom, joint static ceiling, pack count or the 10-pod cap).
  The joint static ceiling is the most pods of that K pair (at most the campaign's packs of each class) that the product's
  schedulable nodes could hold at once by allocatable GPU, CPU and memory after the node reserve. It is exact per node, and
  an upper bound, because other tenants' pods are invisible.
- **[A1].** Campaign (b) runs only on the ≥ 45 GB products, since both of its families contain A07 runs. The 24 GB rows are
  shown as references marked †.

STUDY's Check recomputed (s 138.9 s at K = 5, A10 pilot telemetry, a formula illustration): R = 129.6 (STUDY: 130), Chang E first term at G = 7 = 10.29 d (STUDY: 10.3 d), one 7,000-epoch run = 11.25 d (STUDY: 11.3 d).
Limiting cases on the A10 Chang row: two identical products give T ratio 1.000; at G → large, T tends to Q + C + max H·s/3600 = 157.0 h (critical path 157.0 h + Q).

| constant | value | source |
| --- | --- | --- |
| stop_after: epochs per arm | 21 | STUDY l. 47-49; PREFLIGHT arm table |
| [D1] window: one-based epochs per arm (2-21) | 20 | STUDY l. 47 |
| [D1] untraced epochs per arm in the window | 18 | STUDY l. 47-49 (traced 10 and 20) |
| [D1] traced epochs per arm in the window | 2 | STUDY l. 48 |
| sampler interval, s | 60 | PREFLIGHT Alignment 5; pod log BENCH_PLAN_OK sample_s |
| rule 1: pod peak limit, % of memory.total | 90 | STUDY l. 65 |
| rule 5: steady cores per arm limit | 2.1 | STUDY l. 72 |
| rule 3 / [D6]: window after the apply, h | 6 | STUDY l. 67 |
| [D5] tie factor | 1.10 | STUDY l. 87 |
| policy item 4 utilization floor, % | 40 | STUDY l. 94; PREFLIGHT B5 |
| C_p canary length, epochs | 110 | STUDY l. 55-56 |
| [D4] campaign (b) pod cap | 10 | STUDY l. 60-61 |
| [A1] minimum card memory for campaign (b) A07 packs, GB | 45 | STUDY l. 118 |
| campaign (a) E run-epochs W | 224,000 | STUDY l. 20-21 |
| campaign (a) A07 run-epochs W | 112,000 | STUDY l. 21 |
| campaign (a) horizon H, epochs | 7,000 | STUDY l. 20-21 |
| campaign (a) R run-epochs (untimed, [A2]) | 8,000 | STUDY l. 21 |
| campaign (a) R batch size | 256 | STUDY l. 21 |
| campaign (b) E run-epochs W (base class) | 32,000 | STUDY l. 23 |
| campaign (b) A07 run-epochs W (base class) | 114,000 | STUDY l. 23 |
| campaign (b) E longest horizon H, epochs | 1,000 | STUDY l. 23 |
| campaign (b) A07 longest horizon H, epochs | 2,000 | STUDY l. 23 |
| fingerprint gate constant | 11,559,681 | STUDY l. 66 |
| seconds per hour in R = K x 3600 / s | 3,600 | STUDY l. 50 |
| host-RSS gate: process epochs the in-code gate needs | 105 | STUDY l. 51, 69-70 |
| alternative reading of "10 % earlier": T(p) < 0.90 x T(A10) | 0.90 | STUDY l. 19 (this VERIFY: the reading not used) |

Inputs per product, class and K, and the static ceilings. The ceilings are upper bounds on G_p and not G_p itself: they
assume empty nodes, and the benchmark's own pods waited hours for one GPU of the 4090, 3090, A6000 and A100 (headline table).

| product | class | K | Job | s [D1] | Chang GPU-h, W·s/(3600·K) | Chang critical path, H·s/3600 (h) | Delta GPU-h | Delta critical path (h) | canary 110·s/3600 (h) | Q (h) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A10 | E | 4 | krule | 114.10 | 1,774.9 | 221.9 | 253.6 | 31.7 | 3.49 | 0.01 |
| A10 | E | 3 | klow | 80.75 | 1,674.7 | 157.0 | 239.2 | 22.4 | 2.47 | 0.01 |
| A10 | A07 | 2 | krule | 96.56 | 1,502.1 | 187.8 | 1,528.9 | 53.6 | 2.95 | 0.01 |
| A10 | A07 | 1 | klow | 45.73 | 1,422.9 | 88.9 | 1,448.3 | 25.4 | 1.40 | 0.01 |
| A100-SXM4-80GB | E | 16 | krule | 177.46 | 690.1 | 345.1 | 98.6 | 49.3 | 5.42 | 0.29 |
| A100-SXM4-80GB | E | 4 | klow | 47.10 | 732.7 | 91.6 | 104.7 | 13.1 | 1.44 | 3.82 |
| A100-SXM4-80GB | A07 | 8 | krule | 142.23 | 553.1 | 276.6 | 563.0 | 79.0 | 4.35 | 0.29 |
| A100-SXM4-80GB | A07 | 2 | klow | 45.05 | 700.9 | 87.6 | 713.4 | 25.0 | 1.38 | 3.82 |
| RTX 3090 | E | 5 | krule | 85.51 | 1,064.1 | 166.3 | 152.0 | 23.8 | 2.61 | 1.50 |
| RTX 3090 | E | 4 | klow | 71.08 | 1,105.7 | 138.2 | 158.0 | 19.7 | 2.17 | 2.45 |
| RTX 3090 | A07 | 2 | krule | 57.11 | 888.3 | 111.0 | 904.2 | 31.7 | 1.74 | 1.50 |
| RTX 3090 | A07 | 1 | klow | 30.85 | 959.8 | 60.0 | 976.9 | 17.1 | 0.94 | 2.45 |
| RTX 4090 | E | 4 | klow | 55.41 | 861.9 | 107.7 | 123.1 | 15.4 | 1.69 | 3.91 |
| RTX 4090 | A07 | 2 | krule | 48.29 | 751.2 | 93.9 | 764.6 | 26.8 | 1.48 | 1.50 |
| RTX 4090 | A07 | 1 | klow | 26.04 | 810.0 | 50.6 | 824.4 | 14.5 | 0.80 | 3.91 |
| RTX A6000 | E | 4 | klow | 77.32 | 1,202.8 | 150.3 | 171.8 | 21.5 | 2.36 | 4.38 |
| RTX A6000 | A07 | 2 | klow | 65.53 | 1,019.3 | 127.4 | 1,037.5 | 36.4 | 2.00 | 4.38 |

| product | schedulable nodes | allocatable GPUs on them | pods of the production shape by allocatable, per K (2K CPU, 8K Gi) | joint ceiling of each K pair E/A07, campaign (a) | joint ceiling of each K pair E/A07, campaign (b) | a100 quota headroom |
| --- | --- | --- | --- | --- | --- | --- |
| A10 | 30 | 237 | K 4: 237, K 3: 237, K 2: 237, K 1: 237 | 4/2: 16, 4/1: 24, 3/2: 19, 3/1: 27 | 4/2: 110, 4/1: 206, 3/2: 115, 3/1: 211 | no quota object |
| A100-SXM4-80GB | 16 | 77 | K 16: 57, K 8: 73, K 4: 77, K 2: 77 | 16/8: 4, 16/2: 10, 4/8: 10, 4/2: 16 | 16/8: 28, 16/2: 77, 4/8: 38, 4/2: 77 | 1 |
| RTX 3090 | 30 | 115 | K 5: 43, K 4: 54, K 2: 98, K 1: 114 | 5/2: 15, 5/1: 23, 4/2: 16, 4/1: 24 | 5/2: 98, 5/1: 114, 4/2: 98, 4/1: 114 | no quota object |
| RTX 4090 | 3 | 16 | K 4: 9, K 2: 14, K 1: 16 | 4/2: 13, 4/1: 16 | 4/2: 14, 4/1: 16 | no quota object |
| RTX A6000 | 5 | 27 | K 4: 9, K 2: 17 | 4/2: 13 | 4/2: 17 | no quota object |

### Campaign (a): Chang wave 1

T in hours at an assumed G, with the K pair E/A07 in brackets. * marks a G above the a100 quota headroom, ‡ a G above the
joint static ceiling of that K pair on the product's nodes.

| product | memory.total MiB | G = 1 | G = 4 | G = 8 | G = 13 | G = 16 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A10 | 23,028 | 3,097.6 (3/1) | 774.4 (3/1) | 387.2 (3/1) | 238.3 (3/1) | 193.6 (3/1) |  |
| A100-SXM4-80GB | 81,920 | 1,249.2 (16/8) | 333.4 (4/8)* | 188.3 (4/2)* | 119.3 (4/2)* | 100.7 (4/2)* | * G above the a100 quota headroom (1 free at 2026-09-29T18:28:07Z; 1 at 08:41Z, 3 at 11:57Z) |
| RTX 3090 | 24,576 | 1,958.0 (5/2) | 493.7 (5/2) | 249.7 (5/2) | 160.5 (4/2) | 145.3 (4/2) |  |
| RTX 4090 | 24,564 | 1,622.6 (4/2) | 412.8 (4/2) | 211.1 (4/2) | 133.6 (4/2) | 117.2 (4/1) | E at K=4 only (K=5 excluded, rule 1) |
| RTX A6000 | 49,140 | 2,233.2 (4/2) | 566.6 (4/2) | 288.9 (4/2) | 182.0 (4/2) | 161.5 (4/2)‡ | ‡ G above the static ceiling of its nodes (table of ceilings); K_low shape only (its K_rule shape was not practical now) |

What the pre-registered rule favours at equal G. The tie set is every eligible product with T ≤ 1.10 × min T. At equal G
the larger-G_p criterion of [D5] cannot separate products, so the tie goes to the smaller memory.total:

| G | eligible now | leader, T h | tie set (T ≤ 1.10 × min) | [D5] pick at equal G (smaller memory.total) | T(A10) / T(leader) | more than 10 % earlier than the A10? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | A10, A100-SXM4-80GB, RTX 3090, RTX 4090, RTX A6000 | A100-SXM4-80GB 1,249.2 | A100-SXM4-80GB | A100-SXM4-80GB | 2.480 | yes |
| 4 | A10, RTX 3090, RTX 4090, RTX A6000 | RTX 4090 412.8 | RTX 4090 | RTX 4090 | 1.876 | yes |
| 8 | A10, RTX 3090, RTX 4090, RTX A6000 | RTX 4090 211.1 | RTX 4090 | RTX 4090 | 1.834 | yes |
| 13 | A10, RTX 3090, RTX 4090, RTX A6000 | RTX 4090 133.6 | RTX 4090 | RTX 4090 | 1.784 | yes |
| 16 | A10, RTX 3090, RTX 4090, RTX A6000‡ | RTX 4090 117.2 | RTX 4090 | RTX 4090 | 1.651 | yes |

The [D4]-capped view, with each product at its own bound; ties go to the larger G_eff, then the smaller memory.total:

| G asked | A10: T h (G_eff) | A100-SXM4-80GB: T h (G_eff) | RTX 3090: T h (G_eff) | RTX 4090: T h (G_eff) | RTX A6000: T h (G_eff) | leader | tie set (T ≤ 1.10 × min) | [D5] pick (larger G_eff, then smaller memory.total) | T(A10) / T(leader) | more than 10 % earlier than the A10? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3,097.6 (1) | 1,249.2 (1) | 1,958.0 (1) | 1,622.6 (1) | 2,233.2 (1) | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | 2.480 | yes |
| 4 | 774.4 (4) | 1,249.2 (1, a100 quota) | 493.7 (4) | 412.8 (4) | 566.6 (4) | RTX 4090 | RTX 4090 | RTX 4090 | 1.876 | yes |
| 8 | 387.2 (8) | 1,249.2 (1, a100 quota) | 249.7 (8) | 211.1 (8) | 288.9 (8) | RTX 4090 | RTX 4090 | RTX 4090 | 1.834 | yes |
| 13 | 238.3 (13) | 1,249.2 (1, a100 quota) | 160.5 (13) | 133.6 (13) | 182.0 (13) | RTX 4090 | RTX 4090 | RTX 4090 | 1.784 | yes |
| 16 | 193.6 (16) | 1,249.2 (1, a100 quota) | 145.3 (16) | 117.2 (16) | 182.0 (13, static ceiling) | RTX 4090 | RTX 4090 | RTX 4090 | 1.651 | yes |

Break-even: the fewest GPUs of each product whose T is at or under the RTX 4090's T at G. "Never" means the product's floor
at large G (Q + C + critical path) is above the 4090's T.

| RTX 4090 G | RTX 4090 T, h | A10: fewest G at or under it | A100-SXM4-80GB: fewest G at or under it | RTX 3090: fewest G at or under it | RTX A6000: fewest G at or under it |
| --- | --- | --- | --- | --- | --- |
| 1 | 1,622.6 | 2 | 1 | 2 | 2 |
| 4 | 412.8 | 8 | 4 (above the a100 quota) | 5 | 6 |
| 8 | 211.1 | 15 | 8 (above the a100 quota) | 10 | 12 |
| 13 | 133.6 | never (floor 157.0 h) | 12 (above the a100 quota) | never (floor 145.3 h) | never (floor 161.5 h) |
| 16 | 117.2 | never (floor 157.0 h) | 14 (above the a100 quota) | never (floor 145.3 h) | never (floor 161.5 h) |

Both terms of T (the STUDY's decision packet, l. 89-90), with C_p in its two readings:

| product | G | K E/A07 | Q, h | C_p, h (max of the class canaries) | C_p, h (sum reading) | first term Σ W·s/(3600·K·G), h | critical path max H·s/3600, h | T, h | T with the C_p sum, h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A10 | 1 | 3/1 | 0.01 | 0.00 | 0.00 | 3,097.6 | 157.0 | 3,097.6 | 3,097.6 |
| A10 | 16 | 3/1 | 0.01 | 0.00 | 0.00 | 193.6 | 157.0 | 193.6 | 193.6 |
| A100-SXM4-80GB | 1 | 16/8 | 0.29 | 5.71 | 10.05 | 1,243.2 | 345.1 | 1,249.2 | 1,253.6 |
| A100-SXM4-80GB | 16 | 4/2 | 3.82 | 5.26 | 6.63 | 89.6 | 91.6 | 100.7 | 102.0 |
| RTX 3090 | 1 | 5/2 | 1.50 | 4.12 | 5.86 | 1,952.4 | 166.3 | 1,958.0 | 1,959.8 |
| RTX 3090 | 16 | 4/2 | 2.45 | 4.62 | 6.37 | 124.6 | 138.2 | 145.3 | 147.0 |
| RTX 4090 | 1 | 4/2 | 3.91 | 5.60 | 7.07 | 1,613.1 | 107.7 | 1,622.6 | 1,624.1 |
| RTX 4090 | 16 | 4/1 | 3.91 | 5.60 | 6.39 | 104.5 | 107.7 | 117.2 | 118.0 |
| RTX A6000 | 1 | 4/2 | 4.38 | 6.74 | 8.75 | 2,222.0 | 150.3 | 2,233.2 | 2,235.2 |
| RTX A6000 | 16 | 4/2 | 4.38 | 6.74 | 8.75 | 138.9 | 150.3 | 161.5 | 163.5 |

Leader by G, scanned over every G from 1 to 32:

| view | leader, and the [D5] pick where it differs, by G (from G = …) |
| --- | --- |
| equal G, now | A100-SXM4-80GB from G = 1; RTX 4090 from G = 2 |
| equal G, a100 quota not binding | A100-SXM4-80GB from G = 1 |
| [D4]-capped | A100-SXM4-80GB from G = 1; RTX 4090 from G = 2 |

Checks on the ranking: the compute term alone, the sum reading of C_p, the LPT schedule of the real equal-horizon packs, and
the stress test on the leader.

| G | view | leader (T with Q + C) | leader by the compute term only | leader with C_p as the sum reading | leader by LPT pack schedule | leader T, h | same leader with s × 1.0643, T h | leader after the stress | tie set after the stress |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | equal G | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | 1,249.2 | 1,329.5 | A100-SXM4-80GB | A100-SXM4-80GB |
| 4 | equal G | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 412.8 | 438.8 | RTX 4090 | RTX 4090 |
| 8 | equal G | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 211.1 | 224.2 | RTX 4090 | RTX 4090 |
| 13 | equal G | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 133.6 | 141.7 | RTX 4090 | RTX 4090 |
| 16 | equal G | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 117.2 | 124.3 | RTX 4090 | RTX 4090 |
| 1 | [D4]-capped | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | 1,249.2 | 1,329.5 | A100-SXM4-80GB | A100-SXM4-80GB |
| 4 | [D4]-capped | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 412.8 | 438.8 | RTX 4090 | RTX 4090 |
| 8 | [D4]-capped | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 211.1 | 224.2 | RTX 4090 | RTX 4090 |
| 13 | [D4]-capped | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 133.6 | 141.7 | RTX 4090 | RTX 4090 |
| 16 | [D4]-capped | RTX 4090 | RTX 4090 | RTX 4090 | RTX 4090 | 117.2 | 124.3 | RTX 4090 | RTX 4090 |

The formula is a lower bound on a pack schedule whenever G does not divide the packs. The REPORT schedules the real packs;
the check below uses LPT on equal-horizon packs, with any partial pack at the full-K s, which is an upper bound.

| G | product (K E/A07) | packs E + A07 | formula compute term, h | LPT makespan of the packs, h | LPT / formula |
| --- | --- | --- | --- | --- | --- |
| 1 | A100-SXM4-80GB (16/8) | 2 + 2 | 1,243.2 | 1,243.2 | 1.000 |
| 1 | A10 (3/1) | 11 + 16 | 3,097.6 | 3,149.9 | 1.017 |
| 4 | RTX 4090 (4/2) | 8 + 8 | 403.3 | 403.3 | 1.000 |
| 4 | A10 (3/1) | 11 + 16 | 774.4 | 826.7 | 1.068 |
| 8 | RTX 4090 (4/2) | 8 + 8 | 201.6 | 201.6 | 1.000 |
| 8 | A10 (3/1) | 11 + 16 | 387.2 | 423.8 | 1.095 |
| 13 | RTX 4090 (4/2) | 8 + 8 | 124.1 | 187.8 | 1.513 |
| 13 | A10 (3/1) | 11 + 16 | 238.3 | 266.8 | 1.120 |
| 16 | RTX 4090 (4/1) | 8 + 16 | 107.7 | 107.7 | 1.000 |
| 16 | A10 (3/1) | 11 + 16 | 193.6 | 245.9 | 1.270 |

Largest LPT / formula over the five measured products and G = 1-32 (Chang, chosen K): 1.833 (A100-SXM4-80GB at G = 15, K 4/2).

If the a100 quota did not bind (hypothetical; a quota change is outside this benchmark):

| G | condition | leader, T h | tie set | [D5] pick at equal G | T(A10) / T(leader) |
| --- | --- | --- | --- | --- | --- |
| 1 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 1,249.2 | A100-SXM4-80GB | A100-SXM4-80GB | 2.480 |
| 4 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 333.4 | A100-SXM4-80GB | A100-SXM4-80GB | 2.323 |
| 8 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 188.3 | A100-SXM4-80GB | A100-SXM4-80GB | 2.057 |
| 13 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 119.3 | A100-SXM4-80GB | A100-SXM4-80GB | 1.997 |
| 16 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 100.7 | A100-SXM4-80GB | A100-SXM4-80GB | 1.923 |

The two matching units of [D5], each on its own at an assumed G, with the K in brackets. First the unit Chang E+R (R untimed,
so this is E alone):

| product | G = 1 | G = 4 | G = 8 | G = 13 | G = 16 |
| --- | --- | --- | --- | --- | --- |
| A10 | 1,674.7 (K 3) | 418.7 (K 3) | 209.3 (K 3) | 157.0 (K 3) | 157.0 (K 3) |
| A100-SXM4-80GB | 696.1 (K 16) | 192.2 (K 4)* | 100.7 (K 4)* | 100.7 (K 4)* | 100.7 (K 4)* |
| RTX 3090 | 1,069.7 (K 5) | 271.6 (K 5) | 145.3 (K 4) | 145.3 (K 4) | 145.3 (K 4) |
| RTX 4090 | 871.4 (K 4) | 225.0 (K 4) | 117.2 (K 4) | 117.2 (K 4) | 117.2 (K 4) |
| RTX A6000 | 1,213.9 (K 4) | 311.8 (K 4) | 161.5 (K 4) | 161.5 (K 4) | 161.5 (K 4) |

| G | leader (a100 quota applied) | tie set | T(A10) / T(leader) |
| --- | --- | --- | --- |
| 1 | A100-SXM4-80GB | A100-SXM4-80GB | 2.406 |
| 4 | RTX 4090 | RTX 4090 | 1.861 |
| 8 | RTX 4090 | RTX 4090 | 1.786 |
| 13 | RTX 4090 | RTX 4090 | 1.339 |
| 16 | RTX 4090 | RTX 4090 | 1.339 |

Then the unit Chang A07:

| product | G = 1 | G = 4 | G = 8 | G = 13 | G = 16 |
| --- | --- | --- | --- | --- | --- |
| A10 | 1,422.9 (K 1) | 355.7 (K 1) | 177.9 (K 1) | 109.5 (K 1) | 88.9 (K 1) |
| A100-SXM4-80GB | 558.0 (K 8) | 184.2 (K 2)* | 96.6 (K 2)* | 96.6 (K 2)* | 96.6 (K 2)* |
| RTX 3090 | 893.0 (K 2) | 226.8 (K 2) | 115.8 (K 2) | 79.7 (K 1) | 65.8 (K 1) |
| RTX 4090 | 755.7 (K 2) | 192.3 (K 2) | 98.4 (K 2) | 70.9 (K 1) | 59.2 (K 1) |
| RTX A6000 | 1,030.0 (K 2) | 265.6 (K 2) | 138.2 (K 2) | 138.2 (K 2) | 138.2 (K 2) |

| G | leader (a100 quota applied) | tie set | T(A10) / T(leader) |
| --- | --- | --- | --- |
| 1 | A100-SXM4-80GB | A100-SXM4-80GB | 2.550 |
| 4 | RTX 4090 | RTX 4090 | 1.850 |
| 8 | RTX 4090 | RTX 4090 | 1.808 |
| 13 | RTX 4090 | RTX 4090 | 1.544 |
| 16 | RTX 4090 | RTX 4090 | 1.501 |

### Campaign (b): the Delta screen, wave two

T in hours at an assumed G, with the K pair E/A07 in brackets. G above the 10-pod cap is capped ([D4]). * marks a G above the
a100 quota headroom. † marks a 24 GB card, a reference only unless Kai overrides [A1].

| product | memory.total MiB | G = 1 | G = 4 | G = 8 | G = 10 | notes |
| --- | --- | --- | --- | --- | --- | --- |
| A10 | 23,028 | 1,687.5 (3/1)† | 421.9 (3/1)† | 210.9 (3/1)† | 168.8 (3/1)† | † [A1]: Delta A07 needs ≥ 45 GB; a reference only, unless Kai overrides |
| A100-SXM4-80GB | 81,920 | 667.6 (16/8) | 171.4 (16/8)* | 88.7 (16/8)* | 85.0 (16/8)* | * G above the a100 quota headroom (1 free at 2026-09-29T18:28:07Z; 1 at 08:41Z, 3 at 11:57Z) |
| RTX 3090 | 24,576 | 1,061.8 (5/2)† | 269.7 (5/2)† | 137.6 (5/2)† | 111.2 (5/2)† | † [A1]: Delta A07 needs ≥ 45 GB; a reference only, unless Kai overrides |
| RTX 4090 | 24,564 | 897.2 (4/2)† | 231.4 (4/2)† | 120.5 (4/2)† | 98.3 (4/2)† | † [A1]: Delta A07 needs ≥ 45 GB; a reference only, unless Kai overrides; E at K=4 only (K=5 excluded, rule 1) |
| RTX A6000 | 49,140 | 1,220.4 (4/2) | 313.4 (4/2) | 162.3 (4/2) | 132.1 (4/2) | K_low shape only (its K_rule shape was not practical now) |

What the pre-registered rule favours at equal G, under [A1]:

| G | eligible now | leader, T h | tie set (T ≤ 1.10 × min) | [D5] pick at equal G (smaller memory.total) | T(A10) / T(leader) | more than 10 % earlier than the A10? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | A100-SXM4-80GB, RTX A6000 | A100-SXM4-80GB 667.6 | A100-SXM4-80GB | A100-SXM4-80GB | 2.528 (A10 not eligible under [A1]) | no eligible A10 baseline under [A1] |
| 4 | RTX A6000 | RTX A6000 313.4 | RTX A6000 | RTX A6000 | 1.346 (A10 not eligible under [A1]) | no eligible A10 baseline under [A1] |
| 8 | RTX A6000 | RTX A6000 162.3 | RTX A6000 | RTX A6000 | 1.300 (A10 not eligible under [A1]) | no eligible A10 baseline under [A1] |
| 10 | RTX A6000 | RTX A6000 132.1 | RTX A6000 | RTX A6000 | 1.278 (A10 not eligible under [A1]) | no eligible A10 baseline under [A1] |

The [D4]-capped view:

| G asked | A100-SXM4-80GB: T h (G_eff) | RTX A6000: T h (G_eff) | leader | tie set (T ≤ 1.10 × min) | [D5] pick (larger G_eff, then smaller memory.total) | T(A10) / T(leader) | more than 10 % earlier than the A10? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 667.6 (1) | 1,220.4 (1) | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | 2.528 (reference) | no eligible A10 baseline under [A1] |
| 4 | 667.6 (1, a100 quota) | 313.4 (4) | RTX A6000 | RTX A6000 | RTX A6000 | 1.346 (reference) | no eligible A10 baseline under [A1] |
| 8 | 667.6 (1, a100 quota) | 162.3 (8) | RTX A6000 | RTX A6000 | RTX A6000 | 1.300 (reference) | no eligible A10 baseline under [A1] |
| 10 | 667.6 (1, a100 quota) | 132.1 (10) | RTX A6000 | RTX A6000 | RTX A6000 | 1.278 (reference) | no eligible A10 baseline under [A1] |

Break-even against the RTX A6000:

| RTX A6000 G | RTX A6000 T, h | A10: fewest G at or under it | A100-SXM4-80GB: fewest G at or under it | RTX 3090: fewest G at or under it | RTX 4090: fewest G at or under it |
| --- | --- | --- | --- | --- | --- |
| 1 | 1,220.4 | 2 ([A1] override) | 1 | 1 ([A1] override) | 1 ([A1] override) |
| 4 | 313.4 | 6 ([A1] override) | 3 (above the a100 quota) | 4 ([A1] override) | 3 ([A1] override) |
| 8 | 162.3 | never within the 10-pod cap | 5 (above the a100 quota) | 7 ([A1] override) | 6 ([A1] override) |
| 10 | 132.1 | never within the 10-pod cap | 6 (above the a100 quota) | 9 ([A1] override) | 8 ([A1] override) |

Both terms of T, with C_p in its two readings:

| product | G | K E/A07 | Q, h | C_p, h (max of the class canaries) | C_p, h (sum reading) | first term Σ W·s/(3600·K·G), h | critical path max H·s/3600, h | T, h | T with the C_p sum, h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A10 | 1 | 3/1 | 0.01 | 0.00 | 0.00 | 1,687.5 | 25.4 | 1,687.5 | 1,687.5 |
| A10 | 10 | 3/1 | 0.01 | 0.00 | 0.00 | 168.8 | 25.4 | 168.8 | 168.8 |
| A100-SXM4-80GB | 1 | 16/8 | 0.29 | 5.71 | 10.05 | 661.6 | 79.0 | 667.6 | 671.9 |
| A100-SXM4-80GB | 10 | 16/8 | 0.29 | 5.71 | 10.05 | 66.2 | 79.0 | 85.0 | 89.4 |
| RTX 3090 | 1 | 5/2 | 1.50 | 4.12 | 5.86 | 1,056.2 | 31.7 | 1,061.8 | 1,063.5 |
| RTX 3090 | 10 | 5/2 | 1.50 | 4.12 | 5.86 | 105.6 | 31.7 | 111.2 | 113.0 |
| RTX 4090 | 1 | 4/2 | 3.91 | 5.60 | 7.07 | 887.7 | 26.8 | 897.2 | 898.7 |
| RTX 4090 | 10 | 4/2 | 3.91 | 5.60 | 7.07 | 88.8 | 26.8 | 98.3 | 99.8 |
| RTX A6000 | 1 | 4/2 | 4.38 | 6.74 | 8.75 | 1,209.3 | 36.4 | 1,220.4 | 1,222.4 |
| RTX A6000 | 10 | 4/2 | 4.38 | 6.74 | 8.75 | 120.9 | 36.4 | 132.1 | 134.1 |

Leader by G, scanned over every G from 1 to the 10-pod cap:

| view | leader, and the [D5] pick where it differs, by G (from G = …) |
| --- | --- |
| equal G, now | A100-SXM4-80GB from G = 1; RTX A6000 from G = 2 |
| equal G, a100 quota not binding | A100-SXM4-80GB from G = 1 |
| [D4]-capped | A100-SXM4-80GB from G = 1; RTX A6000 from G = 2 |
| equal G, [A1] overridden | A100-SXM4-80GB from G = 1; RTX 4090 from G = 2 |
| [D4]-capped, [A1] overridden | A100-SXM4-80GB from G = 1; RTX 4090 from G = 2 |

Checks on the ranking (the compute term alone, the sum reading of C_p, and the stress test on the leader):

| G | view | leader (T with Q + C) | leader by the compute term only | leader with C_p as the sum reading | leader T, h | same leader with s × 1.0643, T h | leader after the stress | tie set after the stress |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | equal G | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | 667.6 | 710.5 | A100-SXM4-80GB | A100-SXM4-80GB |
| 4 | equal G | RTX A6000 | RTX A6000 | RTX A6000 | 313.4 | 333.0 | RTX A6000 | RTX A6000 |
| 8 | equal G | RTX A6000 | RTX A6000 | RTX A6000 | 162.3 | 172.2 | RTX A6000 | RTX A6000 |
| 10 | equal G | RTX A6000 | RTX A6000 | RTX A6000 | 132.1 | 140.0 | RTX A6000 | RTX A6000 |
| 1 | [D4]-capped | A100-SXM4-80GB | A100-SXM4-80GB | A100-SXM4-80GB | 667.6 | 710.5 | A100-SXM4-80GB | A100-SXM4-80GB |
| 4 | [D4]-capped | RTX A6000 | RTX A6000 | RTX A6000 | 313.4 | 333.0 | RTX A6000 | RTX A6000 |
| 8 | [D4]-capped | RTX A6000 | RTX A6000 | RTX A6000 | 162.3 | 172.2 | RTX A6000 | RTX A6000 |
| 10 | [D4]-capped | RTX A6000 | RTX A6000 | RTX A6000 | 132.1 | 140.0 | RTX A6000 | RTX A6000 |

If Kai overrides [A1], or the a100 quota did not bind:

| G | condition | leader, T h | tie set | [D5] pick at equal G | T(A10) / T(leader) |
| --- | --- | --- | --- | --- | --- |
| 1 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 667.6 | A100-SXM4-80GB | A100-SXM4-80GB | 2.528 |
| 1 | Kai overrides [A1] | A100-SXM4-80GB 667.6 | A100-SXM4-80GB | A100-SXM4-80GB | 2.528 |
| 1 | Kai overrides [A1] and the a100 quota is not binding | A100-SXM4-80GB 667.6 | A100-SXM4-80GB | A100-SXM4-80GB | 2.528 |
| 4 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 171.4 | A100-SXM4-80GB | A100-SXM4-80GB | 2.462 |
| 4 | Kai overrides [A1] | RTX 4090 231.4 | RTX 4090 | RTX 4090 | 1.823 |
| 4 | Kai overrides [A1] and the a100 quota is not binding | A100-SXM4-80GB 171.4 | A100-SXM4-80GB | A100-SXM4-80GB | 2.462 |
| 8 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 88.7 | A100-SXM4-80GB | A100-SXM4-80GB | 2.378 |
| 8 | Kai overrides [A1] | RTX 4090 120.5 | RTX 4090 | RTX 4090 | 1.751 |
| 8 | Kai overrides [A1] and the a100 quota is not binding | A100-SXM4-80GB 88.7 | A100-SXM4-80GB | A100-SXM4-80GB | 2.378 |
| 10 | a100 quota not binding (hypothetical) | A100-SXM4-80GB 85.0 | A100-SXM4-80GB | A100-SXM4-80GB | 1.985 |
| 10 | Kai overrides [A1] | RTX 4090 98.3 | RTX 4090 | RTX 4090 | 1.717 |
| 10 | Kai overrides [A1] and the a100 quota is not binding | A100-SXM4-80GB 85.0 | A100-SXM4-80GB | A100-SXM4-80GB | 1.985 |

The matching units of campaign (b) are its families (350k, 5M). Their run-epoch split is not in the STUDY, which gives only
base-class totals, and the pack files were not read. Per-family T is left to the REPORT.

## Selection rule, as pre-registered

- **Which numbers.** For each arm, epochs 2-21 of its single fresh attempt; the slowest arm of each phase ([D1]). For the A10,
  the first complete attempt of each Job (B3), which is its only attempt.
- **Which K.** [D3]: the non-excluded K with the earlier T at each G, not the higher R. Rule 1 removes K=5 for the RTX 4090's
  E, and rule 3 removes every K_rule K of the RTX A6000.
- **Which products.** Those with data and no product-wide exclusion under rules 2 and 6: the A10, A100-SXM4-80GB, RTX 3090,
  RTX 4090 and RTX A6000. Rule 3 drops the L40, L40S and A40 as "not practical now" for both shapes.
- **Tie set** ([D5], policy item 3 quoted in STUDY l. 82-85): T ≤ 1.10 × min T, won by the larger G_p and then the smaller
  memory.total. With G_p unmeasured, the equal-G tables apply the memory criterion and the capped tables apply G_eff first.
  No tie set here holds more than one product, so neither criterion decides anything.
- **"More than 10 % earlier than the A10"** is read as T(A10) > 1.10 × T(p), the [D5] tie boundary. The other reading,
  T(p) < 0.90 × T(A10), differs only in a narrow band just above 1.10 that no ratio in the tables falls in.
- **Queue.** "Do not wait for a premium GPU if its queue delay exceeds its measured runtime gain" enters through Q_p and C_p
  inside T. For the A100, the binding delay is a quota change, not a queue, and its length is unknown.
- **Unit of choice** ([D5]). The two matching units of campaign (a), Chang E+R and Chang A07, pick the same product at every G
  of the grid (unit tables). So "one product per campaign if within 10 % of the best split" holds trivially for campaign (a).
  For campaign (b) the family units cannot be priced (per-family run-epochs are not in the STUDY).

## Verdict per claim

- **Question (a), Chang wave 1, at an assumed G.** Resolved at each G of the grid: the A100-SXM4-80GB at G = 1, the RTX 4090
  from G = 2 to 16, each alone in its tie set, in both the equal-G and the capped views. The A100's lead at G = 1 is the
  single-GPU case that the quota allows, a whole campaign on one GPU (1,249.2 h), not a plan anyone would run. **At the
  GPUs that can actually schedule: not resolvable with these data.** G_p was not probed ([D4]), and the ranking at the true
  G_p depends on the pools; see the break-even table.
- **Question (b), the Delta screen's wave two, at an assumed G.** Resolved under [A1] (campaign (b) tables): the A100 at
  G = 1, the RTX A6000 from G = 2. The same caveat on G_p applies. The A6000 is priced from its K_low shape only.
- **"Is any T(p) more than 10 % earlier than the A10's?"** For campaign (a), yes at every assumed G of the grid (the
  selection tables): the null is falsified for campaign (a) at those G. It is **not resolvable at the GPUs that can actually
  schedule**, because no probe ran. It is a telemetry statement from one node per shape; each ratio is far above the 1.10
  margin and survives the stress test. For campaign (b), **not resolvable as posed**, because the A10 is not eligible under
  [A1]. The ratios to the A10 are in the tables, as references.
- **Falsifier (i)** (STUDY l. 92-93): "on the A10 K=5 pilot pod (one node) s over one-based epochs 2-21 differs by over 10 %
  from the latest same-aligned window (10m + 2 to 10m + 21) before the decision". **Not evaluated here.** Its window is "the
  latest … before the decision", and the decision has not been made. Read it at decision time with
  `code/bench_summary.py a10 --offset <10m>` on the pilot-b K=5 logs (PREFLIGHT ran an offset window as the machinery check).
- **Falsifier (ii)** (the chosen product's canary s over 10 % above the screen's): after the rule-4 canary. Not yet
  applicable.
- **Post-launch check** (three-hour utilization under 40 %, or throughput over 10 % below the screen): after launch. Every
  phase here has steady utilization well above 40 % (headline table).

## Rules and quantities the data cannot answer

- **[D4] G_p and Q_p.** No probe Job ran. G is assumed; Q is one pod per shape (C7). Three pods (the RTX 3090 K_low and
  K_rule, the RTX 4090 K_rule) started between 11:57:24Z and 11:57:47Z, just after the A100 K_rule and A10 pods ended. The
  anti-affinity's topologyKey is the hostname, so it is not the cause. Q reflects cluster events, not a per-product queue.
- **Rule 4.** The 110-epoch memory/RSS canary and the EBOP certification are due on whichever product Kai picks; C_p prices
  their duration only.
- **Host-RSS gate.** It needs 105 epochs; the 21-epoch runs record RSS peaks only (gates table).
- **NRP's rolling 3-h 40 % window.** The pod header before the sampler is not sampled. RUN.md records no NRP alert, and no
  phase is under 40 % in its steady window.
- **Unmeasured classes.** Campaign (a)'s R class [A2]; campaign (b)'s variant classes, costed at their base class [A3]; and
  per-family T for campaign (b).
- **Absent products.** The L40, L40S and A40 have no timing at all, and the RTX A6000 has none at its K_rule K. "Not practical
  now" is a snapshot [L3] from one day.
- **Node spread** [L1]: no interval on any cross-product ratio.

## Where I am not sure

```
DECISION: copy the PVC without model files, checkpoints, validation predictions and activation-width traces, all
unread by the analysis (inventory of all files kept).   ALTERNATIVES: the full tar through the GPU-priority pilot pod
(provenance table).   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
DECISION: feed bench_summary.py the kubectl pod log (the PVC tee plus BENCH_POD and HOSTNAME_NODE).   ALTERNATIVES: the
PVC tee, which has no BENCH_POD stamp, so B3 would order attempts by file mtime.   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
DECISION: T per campaign on one product with both classes sharing G, the K pair chosen by the earlier T at each G [D3].
ALTERNATIVES: per-unit T (the unit tables, same leaders); a split across products (needs G_p per product).
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: C_p = Q + 110 x the larger class s (parallel class canaries), taken in full.   ALTERNATIVES: the sum reading
(decomposition tables; no leader changes); C_p near 0 if the canary finishes before the production gate opens.
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: Q_p = the benchmark pod's apply-to-start wait for the shape holding that K.   ALTERNATIVES: the [D4] probe,
not run. The compute-only check (no Q, no C) gives the same leaders.   CONFIDENCE: LOW   FLAG FOR HUMAN: YES
DECISION: bound G by the a100 quota headroom and the static allocatable ceiling (code/gen_bench.py:142-150) in the
capped view.   ALTERNATIVES: equal G only (also shown; same leaders).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: [A1] applied to all of campaign (b), because both of its families contain A07 runs.   ALTERNATIVES: its E-base
runs on 24 GB cards, which splits the 350k family across products.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: "more than 10 % earlier" read as T(A10) > 1.10 x T(p).   ALTERNATIVES: T(p) < 0.90 x T(A10); same answers
here.   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```

## What needs Kai

1. **G_p.** The rankings hold at every assumed G, but the real G_p is unknown. For campaign (a) the 4090 leads from G = 2,
   and its pool is 3 schedulable nodes; both of its benchmark pods waited hours (headline). The 3090's pool is far larger, and
   the break-even table shows how many 3090s match a given number of 4090s. Options: the [D4] probe at decision time
   (`code/gen_bench.py --probe`), or a choice with the table in hand.
2. **[A1] for campaign (b).** The 24 GB cards held A07 at K=2 at 69.0 % (RTX 3090), 70.1 % (RTX 4090) and 73.4 % (A10) of
   memory, and at K=1 near a third of it (headline table). The A07-at-K=3 OOM that motivated [A1] is not what these phases
   ran. With an override, the 4090 leads campaign (b) from G = 2.
3. **The a100 quota.** One A100 is free now. At G = 1 the A100 leads both campaigns; above that it needs a quota change
   (what-if tables).
4. **Near-limit memory.** The RTX 3090's E at K=5 (89.2 %) and the A100's E at K=16 (88.8 %) pass rule 1 on 60-s samples.
   The chosen product's rule-4 canary is where a missed peak would show.
5. **Rule 4 and falsifier (i).** The chosen product still needs the 110-epoch canary and the EBOP certification, and
   falsifier (i) is read at decision time.
6. **RUN.md l. 53-54.** Correct it to "25 on 341 of 346 rows, 61 on 5" when convenient (reproduction table).

## Commands (from `campaigns/2026-09-29-gpu-benchmark/`)

```
# PVC inventory and read-only copy, through the pilot pod (tar of small files only)
kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- sh -c 'cd /data/chang-n64-20260926 && find gpu-bench -type f -printf "%s\t%TY-%Tm-%TdT%TH:%TM:%.2TSZ\t%p\n" | sort -k3' > data/pvc_inventory_full.tsv
kubectl -n cms-ml exec kai-chang0926-pilotb5-42abed-0-qqjmt -- tar -C /data/chang-n64-20260926 --exclude='*.keras' --exclude='*.npz' --exclude='activation_widths.jsonl' --exclude='checkpoints' -cf - gpu-bench | tar -xf - -C data/
chmod -R a-w data/gpu-bench data/pvc_inventory_full.tsv
# a100 quota snapshot ([D4] quota term)
kubectl -n cms-ml get resourcequota -o json > data/resourcequota_snapshot.json; date -u +%Y-%m-%dT%H:%M:%SZ > data/resourcequota_snapshot.utc
# analysis root, the pre-registered analysis (CLI), then every recomputed number, verify.json and this file
uv run --no-project python code/verify_bench.py --root-only
python3 code/bench_summary.py bench --root data/bench-root --plan manifests/bench_plan.json --out data/bench_summary.json > data/bench_summary.log
uv run --no-project python code/verify_bench.py > data/verify_bench.log
python3 ../../tools/verify_check.py VERIFY.md
```

`code/verify_bench.py` needs only the standard library; `uv run --no-project` keeps it out of any vendored environment.
Its log `data/verify_bench.log` repeats every table, and `data/verify_tables.md` holds them without the prose.
