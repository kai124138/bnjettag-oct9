# Sprint plan: the fastest credible path to a paper-tier result

Written 2026-10-05, from three agents: a Fable 5.1 critical-path strategist, an ml-engineer
on training speed, and cluster-ops on live NRP limits. All timings are benchmark telemetry
(one node per shape, no interval); "projected" marks numbers that were never measured. This
plan replaces the base case in `docs/ROADMAP.md` §3 only if Kai signs the Day-0 items in §4.

## 1. Can it be done in one day?

**No, not with the registered 7,000-epoch recipe.** Finishing in 24 h needs either
s/epoch ≤ 24 h ÷ 7,000 = 12.3 s, or no more than 24 h ÷ 47.10 s ≈ 1,835 epochs at today's
fastest measured E speed. The fastest measured row of any kind is 26.04 s/epoch (A07, one arm
on an RTX 4090), more than 2× too slow.

The per-epoch time is bound by kernel launches, not compute: the model is small, all training
data already sits on the GPU, and an A100 is only about 1.2× an RTX 4090 per arm. A bigger GPU
therefore barely helps. The only ways under a day are:

- **A shorter registered recipe** (≤ about 1,000 epochs). This breaks the comparison to
  Chang's 7,000-epoch recipe. The PID controller only reaches 350k near epoch 500, so a short
  run may give no feasible checkpoint at all. Methodology §6.8 would make a short-schedule
  headline a Category A/B finding until the long run exists. The result counts as a pilot,
  not a paper.
- **A roughly 4× trainer speedup** through XLA or fused multi-arm steps. Both are unbuilt.
  XLA is registered off (`jit_compile false`); pairing across arms depends on that, and XLA
  has failed on the A10 before. Turning it on is a STUDY amendment.

What more GPUs do buy: every branch and every seed runs at once instead of one after
another. That takes the plan from about 5–6 weeks (roadmap base case) to **about 7 days**.

## 2. The constraints, besides training time

| type | constraint | cost today | removable? | who |
| --- | --- | --- | --- | --- |
| science | the option (c) readout gates the production design | ~7 days of waiting | **yes:** pre-register every branch and launch them together | Kai signs the branch map |
| engineering | the NB (learned-width) arm has no code; its speed is unmeasured | ~7 days → ~36 h | compressible: build it now, in parallel | ml-engineer |
| human | the §7 decisions are scattered across weeks | 2–4 days | **yes:** one sitting on Day 0 | Kai |
| human | one approval record per launch | 2–24 h each | **yes:** pre-sign the registered launch set | Kai |
| human | mulder needs Kai's MacBook | a week of sessions | partly: dry run now; SSH from WSL is a security call | Kai |
| human | a number moving into the record; anything outward | 2 × (2–24 h) | no, by design | Kai |
| process | review tiers, about 2 rounds × 5 phases | ~5 days → ~1.5 days | compressible: build and review the VERIFY/REPORT pipelines on epoch-500 snapshots while training runs | orchestrator |
| process | no session watches a run; each phase starts a new session | 0–12 h idle at each of 4 boundaries | yes, with ~1 day of building: a readout Job chained to training plus a routine that runs `/review` when VERIFY lands; needs a RULES §4 amendment | Kai + cluster-ops |
| process | code is frozen after launch | 0, or a full relaunch on a bug | no: the CPU gate and canary are the mitigation | — |
| cluster | the namespace's **200-pod quota** is 172/200 used, mostly stale Pending and Unknown pods | about 28 pods of headroom | ask the owners or NRP admins to clear stale pods | Kai / NRP |
| cluster | A100 quota is 24 with **1 free**; H100/H200 quota is 0 | A100s are out for a sprint | quota request | Kai / NRP |
| cluster | the 40 % GPU-utilization floor (3 h rolling, admins delete violators, 3 strikes flags the account) | binds per pod | one arm per pod measured 74–91 % steady (A07); E at one arm per pod never measured | cluster-ops probe |
| cluster | queue delays: 4090 1.5–3.9 h; narrowing the product pool once left pods Pending 34 h | hours | don't narrow pools | — |
| tooling | **Jev does not automate the loop.** It is an advisory classifier; lab loops never launch, watch or resume jobs | — | automation is Kubernetes, `run_handoff` and the orchestrator, plus the ~1 day of building above | — |

**One correction to the premise:** compute capacity is not the limit, but the **pod quota**
is. A sweep of "all architectures" (Delta's 240 runs at one arm per pod) cannot fit in 28
free pod slots. Packing 4 arms per pod fits 240 runs into 60 pods, but makes each run 4× longer.

## 3. The packing decision that matters most

Throughput per arm is nearly flat in K. Each packed run pays almost the full K× in wall time
while total throughput gains only 6–8 % (A100, E: 11.8 s/arm at K=4 vs 11.1 s/arm at K=16).
For speed, use **one arm per pod**.

| product | class | arms per pod | s/epoch | 7,000-epoch run | steady GPU util | status |
| --- | --- | --- | --- | --- | --- | --- |
| RTX 4090 | A07 | 1 | 26.04 | 50.6 h (2.11 d) | 84.4 % | measured |
| RTX 3090 | A07 | 1 | 30.85 | 60.0 h (2.50 d) | 74.3 % | measured |
| A10 | A07 | 1 | 45.73 | 88.9 h (3.70 d) | 91.3 % | measured |
| A100 | E | 4 | 47.10 | 91.6 h (3.82 d) | 98.5 % | measured; only 1 A100 free |
| any | E | 1 | — | about 1.2–1.8 d | — | **projected; needs a 20-min probe** |

A and NB both use the E architecture. The RTX 3090 pool (25–45 GPUs likely sustained,
1.5–2.5 h queue) fits all 16 A/NB runs at one arm per pod, on one product, which pairing
requires. The 4090 pool (10–16 GPUs) is faster but too small for 16.

Safe speedups that keep the registered science: a compiled EBOPs trace (saves about 15–19 %
of epoch time at one arm per pod), plus validation-file I/O to local disk. Each needs a
determinism probe and a new code sha. **Not on the critical path:** NB still has to be built
anyway, so use that window to land them only if the probe passes the same day.

## 4. The plan (hour 0 = Kai's Day-0 sitting)

| hours | what | jobs / compute | gate |
| --- | --- | --- | --- |
| **H0–2** | **Kai's sitting:** the ROADMAP §7 items 1–5; product = RTX 3090, one arm per pod; the §5.2 stop rule; a dated **branch map** (§5); pre-signed approval records for the registered launch set; ask NRP about stale pods; book mulder | — | everything after this needs no further wait |
| H0–6 | option (c) CPU gate finishes (running since 00:10Z); floor re-trace; **20-min E one-arm-per-pod probe** on a 3090 (s/epoch, GPU util) | 1 GPU, 20 min | probe util > 40 % |
| H0–6 | **mulder dry run** on the existing A-s2 N=64 checkpoint: measure csynth runtime and front-end failures | Kai's MacBook | removes the week-long unknown |
| H6–12 | launch **A × 8 seeds** at 350k under option (c), plus the 1M and 5M ladder rungs, one arm per pod on 3090s | 8 + 16 pods | handoff with the cleared gate; lint |
| H0–36 | **build NB** (learned-width weights, same E architecture, same quantizers otherwise); CPU gate; 110-epoch canary; solo PREFLIGHT review. The STUDY amendment is panel-reviewed in parallel. | CPU + 1 GPU | panel PASS on the amendment |
| **H36–40** | launch **NB × 8 seeds** at 350k, plus the matching ladder rungs | 8–24 pods | — |
| H40–100 | training. Meanwhile, results-analyst and paper-writer build the VERIFY and REPORT pipelines on epoch-500 and epoch-1000 snapshots, and the panel reviews the pipelines, not the numbers. | — | — |
| H≈100 | NB finishes (about 2.5 d at the 3090 speed, projected; NB may be slower) | — | — |
| H100–125 | readout, VERIFY on final arrays, last panel round, **Kai moves numbers into the record** | CPU | panel PASS |
| H125–150 | csynth of the seed-median A and NB on mulder (runtime measured at H0–6) | Kai's MacBook | — |
| H150–170 | REPORT, final panel round, **Kai approves anything outward** | — | panel PASS |

**Total: about 7 days (about Oct 12–13 if Day 0 is Oct 6)**, against Nov 12–18 in the
roadmap base case. The Fable strategist's version packs 4 arms per pod on A100s and comes to
8–9 days; one arm per pod on 3090s saves about 1.5 days and doesn't need the A100 quota.

**Pod budget:** 8 A + 8 NB at 350k, plus 2 extra rungs × 16 = 48 pods at peak. That is over
the 28 free slots. Either clear stale pods first, or pack the 1M and 5M rungs at 2 arms per
pod and accept that they finish later. The 350k pairs at one arm per pod come first.

## 5. The branch map Kai signs on Day 0

Launching before the option (c) readout is legitimate only if every branch and its
reading rule are dated in advance:

| branch | condition, read at the A runs' own epoch-500 snapshots | headline |
| --- | --- | --- |
| (i) | K1 clears and attention is non-uniform at 350k | A − NB at 350k (Tier W) |
| (ii) | K1 clears but the 350k arms stay degenerate | A − NB on the ladder rung where both are non-degenerate (1M or 5M) |
| (iii) | K1 still fires | the ladder headline from (ii), plus K1 reported as a negative finding |
| (iv) | binary is degenerate at every rung up to 5M | characterization paper (Tier N): k/8 collapse counts, attention entropy, the budget where binary recovers |

The production runs' epoch-500 snapshots stand in for the separate option (c) pilots, so the
pilot stage disappears. The cost: GPU-hours spent on branches that turn out dead.

## 6. What would make it faster still (each needs Kai)

- **A pilot-grade answer in about 1 day:** run A vs NB on a registered ≤1,000-epoch recipe
  alongside the real runs. It gives an early direction, labelled as a pilot. It cannot be the
  headline. It also needs NB built first, so it lands around H40–60, not H24.
- **XLA or fused multi-arm training:** a possible ~2–4× speedup. Unbuilt, and it is a STUDY
  amendment that breaks the registered pairing until it is re-proven.
- **Automate the phase boundaries:** a chained readout Job, and a routine that starts
  `/review` when VERIFY lands. About 1 day to build. It removes idle gaps, not the floor.
  It needs RULES §4 amended.

## 7. Risks

- **NB s/epoch is unknown.** Learned-width HGQ recomputes bit widths every step and may be slower than binary. The canary measures it.
- **A bug found after launch** costs a full relaunch, about 2.5 days, because code is frozen.
- **The 40 % floor at one arm per pod** is unmeasured for E. If it fails, pack 2 per pod: about 2× slower per run, still faster than A10 at K=4.
- **csynth for N=64** may take a day or fail in the front end, as N=8 did. The H0–6 dry run is there to find out early.
- **Reviewing interim snapshots** can anchor reviewers on early numbers. The physics-reviewer sees only the final artifact.
