# Pilot program: find out why binary collapses at 350k, then launch production automatically

Written 2026-10-05. This is the short map. `ROADMAP.md` is the long view and `SPRINT_PLAN.md`
the speed analysis. Times are hours from **T0**, the moment the CPU-gate fix passes. Numbers
are telemetry or projections, never results.

## 1. Where we are

- **The option (c) CPU gate failed its unit tests on 2026-10-05:** 6 of 118, all in the pack
  runner's retry, stall and memory-gate tests (`campaigns/2026-10-02-chang-option-c/RUN.md`).
  **Cause found (about 90 % confidence, `REGRESSION_TICKET.md`):** the cause is a test-setup leak, not
  a code bug. The gate exports `BNJ_CAMPAIGN_DIR`, and `campaigns/2026-10-05-pilot-program/code/tree/tests/test_run_pack.py:40` copies it
  into its fake runs, so they read the real job list. The fix is one line in the test file. It
  still needs a new sha and a CPU gate rerun (about 30 min of tests, ≤4 h in total), so T0 is
  about 4–6 h after you approve the fix.
- **Nothing else is running.** That is the gap this program closes. From now on, every hour
  should either have pilots on the cluster or code being built for the next round.

## 2. The question and the hypotheses

**Why do binary networks collapse at 350k EBOPs but work at 5M?**

| # | hypothesis | prediction if true | pilot that tests it | needs new code? |
| --- | --- | --- | --- | --- |
| H1 | **Controller signal:** the PID steers on an estimate about 7 % off | option (c) keeps A healthy at 350k | A at 350k with and without (c), same GPU product | no |
| H2 | **Budget floor:** a fixed 171,526 EBOPs (E) or 343,053 (A07) can never shrink. *Corrected 2026-10-06: that fixed part is the attention softmax tables, the same for binary and learned-width weights (`campaigns/2026-10-05-pilot-program/dev/evidence/static_floor_a_nb.json`). The binary-specific cost appears when activations stay on: 619,198 binary vs 368,134 learned widths with zeroed weights.* So too little is left for the activations | health tracks headroom (budget minus floor); A07 dies, E barely survives | **budget ladder:** E at 250k / 350k / 500k / 750k / 1M / 2M / 5M; A07 at 350k / 500k / 1M / 2M / 5M | no (target is a config value) |
| H3 | **Attention starved:** the squeeze sends Q/K/V activations to 0 bits first, so attention goes uniform. Chang's model keeps attention at ≥1 bit. | a minimum of 1–2 bits on Q/K/V restores attention at 350k | A at 350k with an attention bit floor | **yes**, a small quantizer option |
| H4 | **Squeezed too early:** the budget bites before the network has learned features | a later or slower squeeze helps | A at 350k with a longer PID warmup, or unconstrained first and squeezed later | probably no (warmup is a config value; to confirm) |
| H5 | **Binary weights themselves** | NB (learned-width weights, no floor) is healthy at 350k while A is not | NB at 350k and at the ladder's recovery rung | **yes**, NB is unbuilt |

These are not exclusive. The current lead is **H2 plus H3**: binary pays a fixed toll, and
attention is the first thing starved. H1 is a weak suspect, because the controller's error is
only 1.5–5.7 % of headroom in the earlier pilots.

## 3. The rounds

Each pilot is one arm per GPU on RTX 3090s, run to epoch 500, which is where the controller
reaches the budget. Measured for A07: 500 × 30.85 s ≈ 4.3 h, plus 1.5–2.5 h in the queue. E's
speed at one arm per GPU is unmeasured but probably faster. **A round is about 6–7 h.** All
pilots in a round use one product, so they can be compared.

| when | round | pilots (pods) | answers |
| --- | --- | --- | --- |
| T0 → T+7 | **R1, broad sweep** | H1: A ± (c), 2 seeds each (4). H2: E ladder, 7 rungs × 1 seed (7), and A07 ladder, 5 × 1 (5). H4: 2 warmup variants × 2 seeds (4). **20 pods.** | does (c) matter? where does binary recover? does a later squeeze help? |
| T+8 → T+15 | **R2, zoom in** | the 2 ladder rungs around the recovery point × 3 seeds (6); H3 attention floor at 350k × 3 seeds, if its code is ready (3); the best R1 variant × 3 seeds (3). **12 pods.** | where exactly binary breaks; whether protecting attention fixes it |
| T+36 → T+43 | **R3, the decisive test** | NB at 350k × 3 (3); NB at the recovery rung × 3 (3); the best binary fix × 3 (3). **9 pods.** | is it binary weights, or the budget? |
| about T+44 | **answer** | the readout writes a hypothesis verdict and recommends a production config | the headline: binary works at X with fix Y, or binary needs budget ≥ Z |
| T+44 → about T+105 | **production** | A and NB × 8 seeds × 7,000 epochs at the chosen config, one arm per GPU (16 pods, about 2.5 d) | the paper's numbers |

What runs in parallel so no hour is idle:
- **T0 → T+36, building:** NB code (ml-engineer, about 36 h, the longest pole) and the H3 attention-floor option (about half a day).
- **T0 → T+24, the autopilot** (§4).
- **The home PC's RTX 4060 Ti:** speed probes, NB smoke tests and quick local checks.
- **Results-analyst:** builds the pilot readout and the VERIFY pipeline as soon as R1 data appears.

Peak use is 20 pods, inside the about 28 free slots in the namespace's 200-pod quota. Each
pod's GPU utilization at one arm per GPU measured 74–91 % for A07. E is checked at R1 launch
(the 40 % floor).

## 4. The autopilot: monitors that launch the next step for us

Before the 2026-10-05 RULES §4 amendment nothing watched a run, so every phase waited for a new session. The
autopilot replaces that wait. It is a small service on the always-on home PC.

**How it works:**
1. **A cron job every 15 minutes** runs `tools/autopilot.py`. It needs no AI and makes no judgment calls.
2. It reads **`campaigns/2026-10-05-pilot-program/PROGRAM.json`**, a plan you sign: the rounds, their pre-built handoffs, and a **decision rule** for each round.
3. It checks job states with `kubectl get` and reads each pod's end-of-run line.
4. When a round finishes, it launches that round's **readout Job**. The readout computes the pre-registered metrics: feasible, degenerate, validation accuracy, attention entropy.
5. It applies the decision rule mechanically, for example: "launch R2 at the two rungs bracketing the first one where 3/3 seeds are non-degenerate".
6. It submits the next pre-signed handoff through `run_handoff.py launch --submit`. Lint and the gate checks still apply.
7. It **pushes a notification** to your phone at every launch, every readout and every stop.
8. **Production launch** is the last rule. It fires automatically only if a pre-registered condition holds, for example: the chosen config has ≥3/3 seeds feasible and non-degenerate at epoch 500, and validation accuracy is above the threshold. Otherwise it stops and asks you.

**Guardrails:**
- It only launches handoffs listed in the signed `PROGRAM.json`.
- It never edits code.
- It stops on any failure, test error or unexpected state.
- Hard caps: 24 pods and a GPU-hour budget per round.
- It checks GPU utilization 30 min after each launch and pings you if a pod is under 40 %.
- Every action is appended to `local/autopilot/log.jsonl`.

**AI steps** (designing the next round when no rule covers it, running `/review` on a readout)
run as a headless `claude -p` session that the cron starts. Their output goes to you as a
notification. They never launch anything.

**Build:** about 1 day (cluster-ops writes it, ml-engineer writes the readout Job,
critical-reviewer reviews it), finished during R1.

**Rule changes (applied 2026-10-05, decisions.md 10:08 entry; `tools/autopilot.py` has not been built, and decisions.md 2026-10-07 item 4 plans a later read-only watcher):** RULES §4 gets "the autopilot may poll job state and
start pre-signed steps"; RULES §3 gets "launches listed in a signed PROGRAM.json count as
approved".

## 5. The home PC (this machine)

RTX 4060 Ti (8 GB), i5-13600K, 20 threads, 27 GB RAM visible to WSL, up 8 days. Uses:
- **The autopilot host.** It is always on and already has `kubectl` access.
- **Local GPU work:** one E arm fits in 8 GB; A07 (about 8.4 GB) does not. Use it for:
  - the E speed probe;
  - NB and attention-floor smoke tests before they reach the cluster;
  - determinism checks;
  - and readout analysis.

  Numbers from this machine are exploration only, never quotable (CLAUDE.md), and a different
  GPU product can't be paired with cluster runs. It needs a CUDA-enabled TensorFlow
  environment checked first.
- The CLAUDE.md line "nothing heavy on this laptop" was written for a laptop. This machine is
  a desktop. Your instruction to use it updates that rule.

## 6. What you sign to start

1. **This program:** the hypotheses, the rounds, and RTX 3090 with one arm per GPU.
2. **The decision rules** in `PROGRAM.json`, including the production auto-launch condition. I draft them; you approve.
3. **The RULES §3 and §4 amendments** for the autopilot.
4. **Spend:** about 41 pilot pods × about 6 h ≈ 250 GPU-h, plus production at 16 pods × about 2.5 d ≈ 960 GPU-h on 3090s.
5. **Using the home PC's GPU** for local exploration.

## 7. What can go wrong

- **The CPU-gate fix takes longer** (a real bug in the pack runner): T0 moves out.
- **E at one arm per GPU falls under 40 % utilization:** pack 2 per GPU, and rounds take about 8–9 h.
- **3090s are busy:** widen the product pool, but keep each round on one product.
- **NB slips:** R3 moves, but R1 and R2 still answer H1 to H4.
- **The autopilot acts on a bad readout:** caps, the stop-on-anything rule and notifications limit the damage. Production launches only under a strict signed condition.
