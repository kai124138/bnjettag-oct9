---
id: 2026-09-29-gpu-benchmark
date: 2026-09-29
type: engineering
status: designed
question: For Chang wave-1 production and Delta wave 2, which schedulable GPU product projects the earliest finish at the GPUs that can actually schedule, with every gate met, and is any more than 10 % earlier than the A10?
supersedes:
superseded_by:
code_sha: anchor bundle 42abed4b5d2e…c258c0 (frozen); benchmark-code sha in PREFLIGHT
wandb: none by design (`run_training(remote=False)`, `bnhgq2/ablation.py:747`; policy item 1)
results:
---
# Which GPU product finishes Chang wave 1 and Delta wave 2 first?

Implements Kai's decision of 2026-09-28 (`.claude/memory/decisions.md` l. 11-21); "the policy" = `docs/infrastructure/gpu-selection-policy.md`.
Chang = `campaigns/2026-09-26-training-batch/`, Delta = `campaigns/2026-09-27-delta-screen/`, Delta code = `campaigns/2026-09-26-delta/code/`; bare `code/` = here.

**Question.** Which product p gives the earliest projected finish T(p) for (a) and (b) at the GPUs of p that can actually schedule, meeting the memory,
host-RSS, fingerprint, EBOP-check and 40 % rolling-utilization gates, and is any T(p) more than 10 % earlier than the A10's?
- (a) Chang wave 1 (Chang `STUDY.md` l. 606-619; `code/tree/campaigns/chang0926/packs.json` and its configs): E {A, B, D, F} × 8 runs × 7,000 = 224,000
  run-epochs; A07 {C, A07-350} × 8 × 7,000 = 112,000; R × 8 × 1,000 = 8,000 at batch 256.
- (b) Delta wave 2, 248 packable runs (Delta code `manifests/delta_w2_{t0,cells}_packs.json`, index sha256 8a6f262f…; 240 in Delta `STUDY.md` l. 906 plus M006's
  8, `GATES.md` l. 1400-1403). By base class: E 56 runs, 32,000 run-epochs (H 500 × 48, 1,000 × 8); A07 192 runs, 114,000 (H 500 × 176, 1,000 × 4, 1,500 × 4, 2,000 × 8).

**Null.** No practical candidate projects a finish more than 10 % earlier than the A10, so the choice shortens neither campaign beyond the tie margin.
**Not a result.** Scheduling telemetry only: no physics number, no accuracy comparison across products; the benchmark's validation lines are not read.
## Arms: two benchmark Jobs per product, the A10 included (Am. 1): a K_rule Job (E, then A07, at K_rule) and a K_low Job (E, then A07, at K_low); 21 epochs per arm, bundle 42abed4b's `run_training(remote=False)`
| arm | product label (resource key) | memory.total MiB | K_rule E / A07 | K_low E / A07 |
| --- | --- | ---: | --- | --- |
| L40 | `NVIDIA-L40` (`nvidia.com/gpu`) | 46,068 | 9 / 4 | 4 / 2 |
| L40S | `NVIDIA-L40S` (`nvidia.com/gpu`) | 46,068 | 9 / 4 | 4 / 2 |
| 4090 | `NVIDIA-GeForce-RTX-4090` (`nvidia.com/gpu`) | 24,564 | 5 / 2 | 4 / 1 |
| 3090 | `NVIDIA-GeForce-RTX-3090` (`nvidia.com/gpu`) | 24,576 | 5 / 2 | 4 / 1 |
| A6000 | `NVIDIA-RTX-A6000` (`nvidia.com/rtxa6000`) | 49,140 | 10, run at 9 (node cap) / 5 | 4 / 2 |
| A40 | `NVIDIA-A40` (`nvidia.com/a40`) | 46,068 | 9 / 4 | 4 / 2 |
| A100 | `NVIDIA-A100-SXM4-80GB` (`nvidia.com/a100`); one free quota unit: its two Jobs run one after the other (Am. 1), G ≤ 1 now; the PCIe A100s are not benchmarked | 81,920 | 16 / 8 | 4 / 2 |
| A10 (baseline) | `NVIDIA-A10` (`nvidia.com/gpu`), in this benchmark (Am. 1); pilot telemetry a labelled cross-check [L2] | 23,028 | 4 / 2 | 3 / 1 |

Memory: node labels (`code/evidence/node_survey_20260929T065531Z.json`; Delta `RUN.md` l. 515-519), in-pod `nvidia-smi` for the A10 (Chang `RUN.md`
l. 696); K per [D2], with the node CPU/RAM cap from `code/evidence/gen_bench.log`. H100, H200, GH200: zero quota.
## Confounds held fixed
Identical in every arm: bundle 42abed4b and pins; the anchor N=64 gated cache (sha256 in PREFLIGHT); batch 2,790; float32, TF32 off, `jit_compile false`;
regime-B trace every 10 epochs; `TF_FORCE_GPU_ALLOW_GROWTH`; the same configs and seeds 1..K per phase; 2 CPU and 8 GiB per arm (Chang `RUN.md` l. 817-819): pinning
a phase's K arms to 2K CPUs enforces the CPU (Am. 1); memory is capped only per pod, at 8 GiB × the Job's largest K, so an arm of the smaller phase may use
8 × K_max / K GiB, up to 32 GiB (fixer v2, critical v2 C2); `BNJ_RSS_GATE_LIMIT_MB` 8,192; W&B off; own run root; bad-node exclusions. Named, not held fixed: node (site, CPU, PVC distance) and driver [L1]; the pilot-telemetry cross-check [L2].
## Measurements and projection [D1]
- **s**, seconds per epoch per process = (9 × median untraced + median traced) / 10 over one-based epochs 2-21 of each arm, slowest arm per phase (a pack
  ends with it). `stop_after` 21 with `train.epochs` unchanged leaves two traced epochs in the window, zero-based 9 and 19 (`bnhgq2/ablation.py:483-489`;
  PREFLIGHT says so if a shortened `train.epochs` traces 20 too). Check: untraced u, traced u + t give u + t/10, Chang's whole-cycle s_e (Chang `STUDY.md` l. 1465-1467).
- **R** = K × 3600 / s run-epochs per GPU-hour, total elapsed ÷ run-epochs beside it; peak GPU memory (pod, per process) against 0.90 × memory.total; mean
  GPU utilization over epochs 2-21 (provisional); host RSS per arm (recorded; the in-code gate needs 105 epochs); queue Q (apply to Running); node, hashes.

**Projected finish** in hours on p, for classes k with run-epochs W_k (Question), longest horizon H_k and pack size K_k:
`T(p) = Q_p + C_p + max( Σ_k W_k · s_k / (3600 · K_k · G_p) , max_k H_k · s_k / 3600 )`. The first term is the design brief's run-epochs ÷ (run-epochs per
GPU-hour × schedulable GPUs), summed over classes sharing p; the second is the critical path, since no run ends before its own horizon. C_p = the delay the
certification canary (110 × s plus its queue) adds beyond the production gate, 0 for the A10 (pilot-b was its canary, Chang `RUN.md` l. 1002-1013). The
REPORT schedules the real packs longest-first (Delta via `budget.py` `schedule()`, replica-first, 10-pod cap). Check (a formula illustration on A10 pilot telemetry at the pilot's K = 5, not [D5]'s K, not quotable; Am. 1): K = 5,
slowest s = 138.9 s (Chang `RUN.md` l. 970-972), R = 130; Chang E at G = 7 is 10.3 d by the first term, under the 11.3 d one 7,000-epoch run takes.

**Schedulable GPUs G_p** [D4], not node count or allocatable: min(quota headroom on p's key from `nrp-lab/nrp_doctor.py status`; the cap, Delta 10 pods
or Chang's pack count at K; an observed count). Observed: at decision time a probe Job per finalist with cap-many production-shaped pods, each running
only the two-minute fingerprint check (Chang `RUN.md` l. 810-813); G_obs = pods Running within 30 min, Q_p = their median wait. Without it, T is given at
G = 1 and at the cap, with the G where the ranking flips. If (a) and (b) pick one product they share G_p; the anchor schedules first (Delta `RUN.md` l. 473).
## Exclusion rules (pre-registered)
1. OOM or a non-finite loss in any arm, or a pod peak above 90 % of memory.total, at a K excludes that K for that product and class; both K excluded drops the class.
2. A fingerprint mismatch (`GPU_FINGERPRINT_MISMATCH`; expected `FINGERPRINT 11559681`, Chang `RUN.md` l. 698) excludes the product.
3. Not Running 6 h after `kubectl apply`: "not practical now" for that Job's pod shape, Job deleted, scheduler message kept [D6] (per Job shape, Am. 1). End
   times follow from each apply plus the per-Job runtime in PREFLIGHT, checked at apply against the regime-B epoch-500 readout (Chang `RUN.md` l. 964-975; Am. 1).
4. The 21-epoch run is a provisional screen. Before production the chosen product passes the full certification: the 110-epoch memory/RSS canary on it (RSS
   gate window 5:105, a fit over process epochs 5-104 projected to the horizon, `bnhgq2/ablation.py:637-678`) and the EBOP certification there (Chang
   `code/tree/campaigns/chang0926/certify_ebops.py`: a reset retrace equals the logged EBOPs within 1e-6, at or under target).
5. (Am. 1) A phase whose steady cgroup cores ÷ K exceed 2.0 × 1.05 = 2.1, or whose 2K-CPU pin was not applied and confirmed by every arm, is above the CPU
   budget: labelled, kept out of T.
6. (Am. 1) A `CHECKPOINT_VERIFICATION` FAIL on any arm of a product excludes the product: production's `run_study.train` runs `verify_selected` after every
   invocation, so at every pause (`run_study.py:150`, asserts l. 172-177). The replay deltas are recorded.
## Matching (the policy, "Scientific and operational constraints")
- Chang: each seed's paired arms on one product, recorded in the evaluation and paired tables: {A, B, D, F, R} on one, {C, A07-350} on one; the second wave
  (H, NB, FP32-E) pairs with A and inherits its product. A − A07-350 is unpaired (Welch) and is labelled if it spans two products.
- Delta: cell, replica and placebo on one product; one per family when possible (350k: E cells, rep-A, P-350, A07 floor cells, rep-A07-350; 5M: cells, rep-C, P-5M); [A1].
## Replication and the selection rule
Timing, not accuracy: one node per Job shape (two Jobs per product, Am. 1), K arms × 20 epochs per phase; node spread is unmeasured [L1], so a gap inside 10 % is a tie by
rule. Pre-registered rule, the policy l. 43-47 (item 3 of "Selection gate before a new production GPU product"), verbatim:
> Prefer the candidate with the earliest projected campaign finish at the number of GPUs that can actually schedule. If two candidates finish within
> 10% of each other, use the less scarce or smaller GPU. Do not wait for a premium GPU if its queue delay exceeds its measured runtime gain. Save the
> benchmark and calculation in PREFLIGHT before generating production manifests; pin the chosen product and resource key in each Job.

[D5] T(p) at each product's own K per class [D3], A10 included, from its benchmark Jobs (Am. 1). Tie set: every p with T(p) ≤ 1.10 × min T, won by the larger G_p, then the smaller
memory.total; queue delay enters through Q_p. Unit of choice: a matching unit (Chang E+R, Chang A07, Delta 350k, Delta 5M); one product per campaign if
within 10 % of the best split. **Decision.** Kai chooses from the REPORT's evidence packet: per product × class × K, s, R, peak memory, utilization, host
RSS, Q; exclusions with cause; T with both terms, G_p and its source; the A10 benchmark row, with the pilot cross-check [L2].
## Falsifier
The screen predicts s. It fails, and the decision moves to canary numbers, if (i) on the A10 K=5 pilot pod (one node) s over one-based epochs 2-21 differs by
over 10 % from the latest same-aligned window (10m + 2 to 10m + 21) before the decision (zero GPU, Chang `logs/`), or (ii) the chosen product's canary s is over
10 % above the screen's (T recomputed, tie rule re-applied). After launch, three-hour utilization under 40 % or throughput over 10 % below the screen's invokes policy item 4.
## Compute budget
(Am. 1) 16 Jobs, two per product with the A10. Compute per Job between two A10 bounds (no candidate measured): per-process s held at the A10's upper
140 s gives 1.63 h for two phases; per-GPU throughput held at the A10's (E 28, A07 44 s per run-epoch, `code/gen_bench.py`) gives 0.75 h (A10 K_low) to
4.67 h (A100 K_rule, K 16/8). About 27.1 GPU-hours at the throughput bound, 32.9 at the larger bound per Job, 40.9 with a 0.5-h header allowance per Job
(`code/evidence/runtime_arithmetic.log`); probe ≤ 10 pods × 3 min per finalist; no `mulder`, nothing local; the canary (about 110 × s per class) is the
policy's cost. The v1 build (one Job per product, A10 from telemetry) is withdrawn.
## Conventions compliance
| rule | how this design meets it |
| --- | --- |
| metric named with split and n | no tagging metric is computed or quoted; timing quantities are defined with their windows |
| no comparison across input sets or N | every phase is N=64 on the one cache; no accuracy is compared at all |
| seeds ≥ 3 or justified | timing study: one node per product, K arms per phase; justified under Replication, [L1] |
| selection rule pre-registered | the policy's item 3 verbatim plus [D3]-[D5], before any benchmark exists |
| falsifier stated | (i), (ii) and the post-launch check |
| no local training or synthesis | NRP Nautilus only; no synthesis |
| W&B group named | none by design (`remote=False`); own run root, so no pilot or production group is touched |
| figures via `docs/style/bnjettag.mplstyle` | none planned; any REPORT figure uses the kit and `tools/plot_check.py` |
| `docs/conventions/` metrics, cost, synthesis | not applicable: no tagging, EBOPs or hardware number; 11559681 is a gate constant |
## Decision labels
- [D1] s, R, window; the critical-path term added to the design brief's formula. [D3] per product and class, the non-excluded K with the earlier T, not the
  higher R: as G grows T tends to H · s (favours low K), at small G to GPU-hours / G (favours high K). [D4] G_p, probe. [D5] tie set, unit. [D6] 6-h window.
- [D2] K_rule = floor(0.90 × memory.total / m_k) (Delta code `canary_k.py:25`; m_E 4,350, m_A07 8,446 MiB, A10 pilot-b, Chang `RUN.md` l. 955, 707), capped by
  K × (2 CPU, 8 GiB) on p's nodes. K_low = the A10 K (E 4, A07 2; Delta `RUN.md` l. 424-427, 504-514), or K_rule − 1 if K_rule ≤ that: equal K isolates card speed.
- [A1] Delta A07 packs go to ≥ 45 GB products only (frozen Delta `STUDY.md` gate 7, l. 444-450) since A07 at K = 3 ran out of memory on an A10 (Delta
  `RUN.md` l. 504-516), unless Kai overrides (asked, l. 526); 24 GB A07 phases inform Chang only.
- [A2] R (batch 256, about 10.9 × the steps per epoch, Chang `STUDY.md` l. 1475-1476, 1926) is not timed by phase E; it follows the E product and is timed in
  its canary. [A3] 88 of Delta's 248 runs (20 E-base, 68 A07-base, M006's Deep Sets among them) are costed at their base class (`k_class_unmeasured`).
- [L1] One node per Job shape (Am. 1): up to two nodes per product, not chosen; each pod logs the node's CPU model, core counts and RAM, named beside each s.
  Contention on the pinned CPUs is not measured beyond the pod's cgroup CPU use: a busy node can slow a phase unflagged, so the product looks slower (critical v2 C6).
  The anti-affinity can hold a Job Pending while its sibling holds the product's only free node (L40S and A40 have two each): that Q is partly self-inflicted,
  and is labelled if it ever stands in for the probe's Q_p (critical v2 C7).
  [L2] (Am. 1: a labelled cross-check, no longer the baseline) A10 pilot telemetry = mixed packs on 42abed4b, W&B on: K=5 {A-s1, A-s2, D-s1, C′-s1, E1-s1}
  at 97.9 %, K=3 {A07-350-s1, C-s1, F-s1} at 92.3 % of memory (Chang `RUN.md` l. 953-956), both over the 90 % rule; at the compliant K (E 4, A07 2) pilot s is
  likely an upper bound. Delta's pure A10 canaries, [D1] s: E-k4 111.5-114.5 s, A07-k2 90.4-90.7 s (Delta bundle 705a554b, W&B on; `code/bench_summary.py a10`
  on Delta `logs/canary-v2-E-k4-s{1..4}.log`, `logs/canary-a07-rep-c-s{1,2}-20260929T0608Z.log`); the 104.3-104.5 s of Delta `RUN.md` l. 424 is an
  all-epoch median, not a [D1] s. [L3] G_p and Q_p are snapshots.
## Where I am not sure
- DECISION: K_low = the class's A10 K [D2]. ALTERNATIVES: the code's default max(1, K_run // 2) (`code/gen_bench.py:24, 82-83`; `code/evidence/k_low_rules.log`),
  equal on L40, L40S, A40, A6000, but E 2 not 4 on 4090/3090 and 8/4 not 4/2 on A100. CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES (`--k-low-rule study-d2` or amend).
- DECISION: G_p from the fingerprint probe. ALTERNATIVES: T as a curve over G only. CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES.
- DECISION: "less scarce" = larger G_p, then smaller memory. ALTERNATIVES: quota-keyed products rank scarce first. CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES.
- Resolved by Am. 1 (orchestrator, 2026-09-29): the A10 runs in this benchmark; the pilot telemetry is a labelled cross-check. (Was: A10 from pilot telemetry.)
- DECISION: critical-path term added to the design brief's formula [D1]. ALTERNATIVES: throughput term only (the Check). CONFIDENCE: HIGH. FLAG FOR HUMAN: YES.
## Amendment 1 (2026-09-29, before any benchmark number)
Source: `review/PREFLIGHT_critical_v1.md` (ITERATE: A1, A2, B1-B6). The orchestrator decided the routes on 2026-09-29 within Kai's policy (the policy's item 1
lists the A10 among the products to run on the same code and inputs); the fixer transcribed them here, tagged "(Am. 1)" in place; the experiment-designer may confirm.
Fixer v2 (`review/PREFLIGHT_critical_v2.md`, PASS with B items) added its B3 and B6 as "Critical v2" bullets and corrected the memory clause, [L1] and B5, tagged "fixer v2", at about 09:55Z:
after the first K_low applies (09:30-09:36Z), before either A10 Job is applied and before any summary runs on benchmark data.
- **A1.** The A10 runs in this benchmark: K_rule E 4, A07 2 (floor(0.90 × 23,028 / m)); K_low = K_rule − 1, E 3, A07 1 ([D2]). Kai's priority rule, pilots
  first: an A10 benchmark Job is applied only while no Chang pilot-b pod is Pending, and deleted if one goes Pending while it has a pod. c6017 and the bad
  nodes stay excluded. [D5] prices the A10 from these phases by the same [D1]-[D4] rules; the pilot telemetry is the labelled cross-check [L2].
- **A2, B6.** Two Jobs per product (K_rule; K_low); each pod requests 2 CPU and 8 GiB × its own largest K. Each phase's K arms are pinned to exactly 2K CPUs,
  the first 2K of the pod's allowed set, with pilot-b's thread environment. Rule 5 is new; [D6] is per Job shape.
- **The fixer's choice, accepted by the orchestrator (`decisions.md` 2026-09-29).** A required pod anti-affinity on `bnjettag.io/gpu-bench-pinned` keeps two pinned benchmark pods off one
  node, where both would pin the same first 2K CPUs of a shared pool. Rollback: remove it in `code/gen_bench.py` `job()`, regenerate, re-lint, re-dry-run;
  the driver ConfigMap is unaffected.
- **B1-B4.** Q runs from apply to Ready, else to the container's start. R needs every arm at `stop_after` (21) epochs; every non-ok arm is listed; an OOM is
  the driver's exit-7 classification only. Rule 6 is new. Each pod logs its node's CPU and RAM; one node per Job shape is a limitation [L1].
- **B5.** Per-Job runtime is in PREFLIGHT. At the throughput bound with the header allowance: A100 K_rule 5.17 h, A6000 K_rule 3.25 h, the 46 GB K_rule Jobs
  3.00 h, the other 11 from 1.25 h (A10 K_low) to 1.83 h (24 GB K_rule); those 11 reach 2.13 h at the per-process bound with the header (fixer v2, critical v2 C3: was
  "the rest 2.13 h" at the throughput bound). NRP's 40 % alert looks back 3 h, so a shorter pod is judged over its whole life, pip install included
  (`docs/infrastructure/nrp-nautilus-setup.md:281-283`); this is an accepted risk (fixer v2, critical v2 B5; PREFLIGHT "Deadlines"). A phase under 40 % mean GPU
  utilization, or a pod NRP flags (most likely a short K_low pod), is a finding, not an exclusion.
- **Critical v2 B3 (fixer v2; before either A10 Job is applied).** An A10 Job deleted by the priority rule, or ending incomplete, is
  re-run at most once, into a fresh directory (the old one moved aside, never deleted). An attempt is complete when every phase of its Job has all K arms at
  21 epochs; the first complete attempt counts, and the phases of any other attempt are listed, never pooled, and kept out of T. An arm stopped during
  `verify_selected` (any product) is `verify_interrupted`, not a rule-6 FAIL. With no counted A10 phase of a class that has R and no exclusion, the headline
  comparison for that class reads "A10 baseline not measured"; the [L2] telemetry is never promoted to the baseline.
- **Critical v2 B6 (fixer v2; before any A10 number is read).** One-sided check of the pinned A10 against production-shaped load: at E K=4 and A07 K=2, a counted A10
  [D1] s more than 10 % above the slowest arm of Delta's pure-pack A10 canary (114.455 s and 90.73 s, `code/evidence/a10_delta_canary_crosscheck.json`;
  PREFLIGHT's 114.45 is 114.455 at two decimals) flags the baseline, and the headline comparison goes to Kai with both readings (`code/bench_summary.py`).
- **C7 and the cross-check.** Rule 3's "applied by about 08:00Z" timing is withdrawn. [L2] now quotes [D1]-basis s; the Check is labelled a formula illustration.
