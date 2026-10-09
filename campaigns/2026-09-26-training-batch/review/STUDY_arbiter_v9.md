# STUDY arbiter v9: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` at c2f5447 (2,353 lines; `git status
--short STUDY.md` empty). Reviews v9: `STUDY_physics_v9.md` (no A; B1-B3; C1-C4),
`STUDY_critical_v9.md` (no A, no B; C1-C3 and a note for the orchestrator),
`STUDY_constructive_v9.md` (no findings; recommends PASS). Validators `STUDY_validators_v9.txt`:
`prose_lint` score 0, no line marked A. STUDY has no figures, so there is no plot-validator file.
Earlier arbiter: `STUDY_arbiter_v8.md`. Also read: `docs/methodology/06-review.md` §6.1-6.8;
`RUN.md` canary sections (l. 120-371, including the W&B pull at c9c9942, committed after c2f5447);
`PREFLIGHT.md` (grep for the K=3 pod: not launched); the top `.claude/memory/decisions.md` entry,
"2026-09-27 (Kai, [D15] branch after the canary)"; `code/tree/bnhgq2/ablation.py:690-712`.
Iteration **9**. §6.5: iteration 10 is the ESCALATE tier.

## Independent checks made by the arbiter

- **Physics B1 (the canary fired the [D15] "> 14 d" branch).** Confirmed. RUN.md l. 156-162 gives
  the mean s/epoch over epochs 1-10 at K=6 on an A10: A-s1 219.65, A-s2 219.37, D-s1 215.16,
  E1-s1 163.88, and C′-s1 293.6 (epochs 1-5 only). RUN.md l. 231-237 gives T_run 17.8 / 17.8 /
  17.4 / 13.3 / 23.8 d. The W&B pull (RUN.md "Trace share and projections") gives a median [D20]
  trace share of 0.420 over 30 A/D epoch samples, a pooled mean of 218.06 s, T_run ≈ 17.67 d, and
  arithmetic projections for a trace every k epochs: 11.8 d at k=5, 11.1 d at k=10, 10.6 d at
  k=25. These are telemetry and projection, not results. STUDY still states the prior-based
  expectation at l. 1287-1298 (112.6 s, 9.1 d, 1,750 pod-hours), l. 1305-1313 ("Expected [D15]
  branch ... fits 14 days"), l. 1397-1400 (15.6 h / 26 h pilot), l. 1556-1557 (876 pod-hours),
  l. 1575, l. 1597-1599, l. 1714-1717 ([D15]), l. 2158 and l. 2283-2288 (FLAG block).
  **Kai has decided the branch** (decisions.md, 2026-09-27): regime B. The [D20] full-split trace
  runs every 10 epochs, and certification at selection is unchanged. A second pilot runs under
  regime B: a K=5 pod (A-s1, A-s2, D-s1, C′-s1, E1-s1) and the K=3 pod (A07-350-s1, C-s1, F-s1).
  The regime-A pod keeps running. The ceiling is about 27 pods at peak (wave 1 about 13 at K=5 on
  the A10 class, wave 2 about 4, Delta 10). Regime B is a **registered option**: STUDY l. 1326-1330
  puts it to Kai word for word ("a full-split trace every k epochs, with candidates saved every
  epoch but the feasibility test applied only on traced epochs ... and the certification retrace
  of the selected checkpoint unchanged"). This is therefore the execution of a registered branch,
  not a new design. The epoch count stays at 7,000 (the decision truncates nothing), so the
  physics worry that the question's 7,000 epochs, "14 points per run" (l. 1249) and "14 restarts"
  (l. 773) are provisional is answered: all three stand.
- **Physics B2 (canary checks with no readable input).** The fact is confirmed for the log files
  (RUN.md l. 164-180, 203-208: `ablation.py:783` prints neither train loss nor trace fields). The
  data now exist: RUN.md's W&B pull (c9c9942) tabulates `loss`, `ebops_trace_seconds` and
  `ebops_trace_over_epoch` per epoch for A-s1, A-s2, D-s1 (epochs 0-9), E1-s1 (0-9) and C′-s1
  (0-4). Train loss is finite and falls from epoch 1 to epoch 10 for A-s1 (2.7120 → 1.4551), A-s2
  (2.6230 → 1.5080) and D-s1 (2.6911 → 1.4340). The STUDY text (l. 1322-1324, 1467, 1480) still
  names no source and no rule for a check that cannot be evaluated, so the finding stands as a
  text fix.
- **Physics B3 (confound 9, "same GPU at seed s").** Confirmed at l. 722-724 and l. 1336-1340.
  Kai's K=5 packing makes it worse than the K=3 case physics raised: a seed block of six
  Chang-schedule arms (A, B, C, D, F, A07-350) does not fit a K=5 pod, so same-seed runs will sit
  in different pods. Pairing survives on TF32 off, `jit_compile false`, seeded data order and the
  GPU-class column. As written, the sentence is false.
- **Consequences of regime B that no reviewer could raise (the decision post-dates the reviews).**
  Traced here against the text:
  (i) [D20] "Per epoch" (l. 1755-1758), "PID signal" (l. 1767-1769, the assertion at
  `ablation.py:698-703` "every epoch") and the DECISION block (l. 2304-2313, "FLAG FOR HUMAN: NO")
  describe an every-epoch trace.
  (ii) The Selection rule (l. 803-805, "every epoch whose freshly traced ... EBOPs") and
  `ablation.py:703-706` (`model_best` is updated on `feasible`) have no untraced epoch.
  (iii) s_e is defined as the "median of epochs 2-10" (l. 1280). Under a 1-in-10 trace, a median
  excludes the trace epoch and understates s_e by about 90.6 / 10 ≈ 9 s per epoch (RUN.md split),
  which is exactly the cost the 14-day rule must see.
  (iv) The canary rule "traced EBOPs at the end of epoch 10 below that at the end of epoch 1"
  (l. 1469) needs a trace at both epochs.
  (v) The interim readouts at 500 / 1,000 / 2,000 / 4,000 / 7,000, the A1000 / D1000 snapshots
  (l. 910) and R's terminal epoch 1,000 need a trace at those epoch ends.
  (vi) Resume (l. 1495-1496) requires equal `config_sha256` and `code_sha256`. Patch 0027 changes
  the code, and `train.ebops_trace_every` changes the config, so regime-A pilot checkpoints cannot
  resume into production.
  (vii) Confound 10 (l. 725-729) requires "the same rule ... in every arm". Wave 2 (NB, H) must use
  the same cadence.
  (viii) The fidelity row "WRAP range update" (l. 493) says the per-epoch reset pins `i` every
  epoch. What `i` does between traces is open for ml-engineer (decisions.md), presumably the in-training tracking (`i_decay_speed` 1e-3); slot P settles it.
  (ix) The K=7 slot rules (l. 1552, 1580-1596; Kai rows "FP32 E arm" and "NB in wave-1 seed
  blocks") assume K=6 seed-block pods. RUN.md l. 244-253 extrapolates six E-sized processes to
  about 26,124 MiB, over the A10's 23,028 MiB. The second-wave plan "4 pods, K=6 with FP32-E"
  (l. 1590-1592) has no measured basis on the A10 class.
- **Crit C2 (l. 1117-1118, "detectable ... only if sd_diff comes in near 1 pt").** Recomputed:
  80 % power at 8 pairs needs d = 1.16 (arbiter v8), so a 1.0-pt gap needs sd_diff ≤ 1.0 / 1.16
  = 0.862 pt. The text is mine (v8 fix 4), and it is loose in the thesis-favourable direction.
  This is a required C.
- **v8 fix sites.** Re-read l. 1178-1179, 1217-1228, 1113-1119, 1375-1394, 1469 and 2158-2159 at
  c2f5447. All landed verbatim, in agreement with the critical and constructive landing tables.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Canary fired the [D15] "> 14 d" branch; STUDY still states "fits 14 days" on the 112.6 s prior at every budget, pilot, second-wave, [D15], Kai-row and FLAG site | phys B1 | B | **B** | Case 3, confirmed from RUN.md l. 156-162, 231-237 and the W&B pull. Kai has decided the branch, so the fix is to write his answer in (fix 1), not to wait. The "provisional epoch count" part is closed: regime B keeps 7,000 epochs |
| 2 | Regime-B amendment: [D20], Selection, s_e definition, canary traced-epoch rule, readout epochs, resume, confound 10, fidelity row, PID signal | arbiter (case 5) | – | **B** | A Kai-decided change of a registered [D] must enter STUDY as a dated amendment before it runs (§6.7, "[D] replaced without a dated amendment"). Each site in checks (i)-(viii) above is currently false under regime B. Fix 1 |
| 3 | Canary loss and trace-share checks have no named source; an unevaluable check is not called a fail | phys B2 | B | **B** | Case 3. The data exist in W&B (RUN.md, c9c9942). The rule text is still missing. Fix 2 |
| 4 | Confound 9 "every Chang-schedule arm at seed s runs on the same GPU" is false under K=3 and under Kai's K=5 | phys B3 | B | **B** | Case 3, and strengthened by the K=5 decision. Fix 3 |
| 5 | K=7 slot rules, the second-wave K=6 plan and the 876 / 438 pod-hour figures rest on K=6 seed blocks and the 112.6 s prior | phys B1 (consequence bullet), arbiter | B (within phys B1) | **B** (folded into fix 1) | RUN.md l. 244-253 memory extrapolation; Kai's K=5 packing. Fix 1(h) |
| 6 | "detectable at 8 pairs only if sd_diff comes in near 1 pt" should read ≤ about 0.86 pt | crit C2 | C | C (required) | My v8 text; the loose wording favours the thesis. Fix 4a |
| 7 | Packet list at l. 1098-1101 loses its "and" | crit C1 | C | C (required) | One-word edit. Fix 4b |
| 8 | Attention figure n = 62,000 is fixed in the spec while `attn_entropy.py:282` accepts `--n_val` | crit C3 | C | C (PREFLIGHT / REPORT) | Not a STUDY edit. The figure takes n from the script's "split validation n" line |
| 9 | Budget-claim sentence should print the Deep-Set-class count; near-collapse region 0.95-0.98; Holm family note; keep the thesis-scope paragraph | phys C1-C4 | C | C (optional) | C1 is already covered by the v8 collapse-label clause ("A's k/8 summary ... prints per arm the count"). C2-C4 are REPORT notes |
| 10 | C′-s1 has no epoch-10 read in the K=6 pod under the per-pod rule | crit (note to orchestrator) | – | RUN record, not STUDY | Under fix 2 an unevaluable check is a fail for that arm. The RUN canary must record C′-s1 as "not evaluated (epoch 5 at close)". The regime-B K=5 pod gives C′-s1 a fresh canary |

## Earlier A and B findings (arbiter v8), by name

| v8 # | finding | status | evidence at c2f5447 |
| --- | --- | --- | --- |
| 1 | FP32-E distance labelled "A − 79.4" | **resolved** | l. 1178-1179 "worded as FP32-E − 79.4 (the same descriptive form as A − 79.4)" |
| 2 | Pilot not as registered (A07-350-s1 OOM, no amendment) | **resolved** | l. 1375-1394 dated amendment (1)-(5); l. 1469 per-pod canary rule; l. 2158-2159 Kai rows. Fix 1(e) below adds "under regime B" to (1) |
| 3 | No collapse label | **resolved** | l. 1217-1228; l. 1412-1413; l. 1258-1260 (cut drawn) |
| 4 | No 80 %-power detectable gap | **resolved** | l. 1113-1119, 1100-1101, 2167. The wording at l. 1117-1118 is tightened by fix 4a (C) |

The v7 A/B findings #1-#9 were closed in arbiter v8. The v8 diff touches none of their sites
except the prescribed Holm edits (l. 1028, 1049-1050). No regression.

## Regression triggers (§6.7), checked independently

- Selection on held-out, or changed after results: **not met**. No result exists. Regime B changes
  which epochs are eligible (traced only) before any selection. The pilot is validation only and
  selects nothing.
- Val/ROC AUC gap > 0.01; single-seed headline; cross-N series; gap < sd at < 3 seeds: **not met**.
- Reload > 1e-7 / TF32: **not met**.
- EBOPs not remeasured: **not met**. Certification retrace of every evaluated checkpoint is
  unchanged (l. 841-854). Under regime B the selected checkpoint is a traced epoch, so logged
  EBOPs equals traced EBOPs by construction, and the full-split retrace tests determinism exactly
  as before.
- Binary > 2 values; DSP / C-sim / C-synth; per-class hidden; byte-identical arms: **not met / not
  applicable**.
- **Failed validation accepted without remediation: not met.** The failed canary item (T_run
  > 14 d) is remediated by the registered route: Kai's decision plus a regime-B canary that must
  itself pass the 14-day rule (fix 1(c)).
- **[D] replaced without a dated amendment: met conditionally.** [D20]'s every-epoch clause and
  the [D15] expectation are being replaced by Kai's decision. The change is legitimate (registered
  option l. 1326-1330, Kai-decided). The trigger is avoided only if the dated amendment (fix 1)
  lands in STUDY **before the regime-B pilot pods are applied**, not merely before production. If
  a regime-B pod runs before fix 1 is committed, the trigger is met and an investigation follows.
- Outward mismatch: not applicable.
- Suspiciously good: none. The canary telemetry (val_accuracy 0.61-0.64 at epoch 10) is
  unremarkable.

**No trigger met, on the condition above.**

## Validation target (§6.8) and competing group

No arm is bound at VERIFY (l. 1561), which is correct. A competing group running a trace every 10
epochs would write down three things before running: which quantity the controller follows
between traces, since the PID then holds the in-training or the stale EBOPs at target, not the
traced value, and traced-epoch feasibility can then fall; that only traced epochs are selectable;
and that a regime comparison on two seeds does not reopen the regime choice on pilot accuracy.
Fix 1 requires all three.

## Disputed facts for the investigator

None. Two facts are open and belong to ml-engineer, who is implementing patch 0027 now: what
BetaPID reads between traces, and the exact traced-epoch set together with the checkpoint cadence.
They are slots in fix 1, and v10 checks that they are filled. They are not disputed.

## Dismissals

None.

## Motivated-reasoning check

- Regime B trades the per-epoch feasibility test for time. The self-serving reading would be "the
  PID still holds EBOPs at target" when, between traces, it may hold a different quantity. Fix
  1(a) slot (P) makes the text say which one, and makes the pilot report traced against in-training
  EBOPs at every traced epoch.
- The regime-A / regime-B pilot comparison has two seeds of A and one of D. Read as a choice, it is
  a forking path: whichever regime looks better at epoch 500 wins. Fix 1(e) pre-registers it as
  descriptive and Kai-only, with no automatic revert. Regime A as production is in any case at 17.7
  d, which Kai declined.
- Kai's 11 d and 9 d figures are arithmetic (decisions.md says so). The 14-day rule binds on the
  regime-B canary's measured s_e, over whole trace cycles (fix 1(c)), never on the projection.

## Verdict

**ITERATE** (STUDY panel, iteration 9 → fixer → v10). No A. Four B: #1-#4, with #5 folded into
#1. **Warning (§6.5): v10 is iteration 10, the ESCALATE tier.** This is not ESCALATE now. The only
item that needed Kai, the [D15] branch after the canary, **is already answered by Kai**
(decisions.md 2026-09-27). Writing his answer into the STUDY is fixer work, not an escalation.

**Scope of v10.** v10 checks only (1) the regime-B amendment of fix 1 at every listed site,
including the ml-engineer slots (P) and (T), which are filled with patch 0027's actual behaviour
and cited to file and line; (2) physics v9 B2 and B3 (fixes 2, 3); (3) the required C edits (fix
4). It is not a fresh review of the whole file. Every item adjudicated at v1-v9 is closed by the
evidence in those arbiter files. The outcomes at v10:
- A landing defect (a site missed, a slot left empty, a number not propagated) gets one more
  fixer pass. It is not a new design review.
- A new A or B that is not a landing defect, and that arises from the amendment's own content
  (for example, patch 0027 behaves so that traced-epoch feasibility cannot be reached), goes to
  Kai as ESCALATE, with the question stated.
- A STUDY PASS still does not launch wave-1 production by itself. Production also needs the
  PREFLIGHT addendum for the patch-0027 bundle ([A21] re-asserted, full-set CPU gate, [A17]), the
  regime-B pilot's canary under the 14-day rule, its epoch-500 A rule and certification, and the
  K=3 pod's A07-350-s1 readout for pods holding A07-350 or C.

## Ordered fixes (fixer; experiment-designer if CANNOT RESOLVE; ml-engineer supplies slots P and T)

Order: fix 1 first. Its core paragraph (1a) must be committed before any regime-B pod is applied.
Then 2, 3 and 4. Every changed number is propagated to every site listed (cascade, §6.7).

**1. (#1, #2, #5) Regime-B amendment: the dated execution of the registered [D15] branch,
Kai-decided.**

(a) **Core paragraph.** Insert it directly after the "Trace-cost risk to the expected branch"
paragraph (after "...the cheap version were declined.", l. 1334). Verbatim, with two slots:

> **[D15] branch executed (2026-09-27, Kai-decided; `.claude/memory/decisions.md` entry
> '2026-09-27 (Kai, [D15] branch after the canary)'; arbiter v9 fix 1).** The K=6 canary on an
> A10 (`RUN.md`, "Canary (epoch 10)" and "Canary — W&B history pull"; telemetry, not results)
> measured a mean of 219.65 / 219.37 / 215.16 s per epoch for A-s1 / A-s2 / D-s1 over epochs
> 1-10 (T_run 17.8 / 17.8 / 17.4 d), 163.88 s for E1-s1 (13.3 d) and 293.6 s for C′-s1 over epochs
> 1-5 (23.8 d). The [D20] trace took a median 0.42 of each A or D epoch (30 epoch samples). The
> single-wave T_run exceeded 14 d, so the registered branch fired and production did not launch.
> Kai chose the option registered above as "a full-split trace every k epochs", with k = 10
> (**regime B**). Declined: accepting about 18 d, and K=3 with about 22 pods. Under regime B:
> (1) the [D20] full-split reset trace runs on the traced epochs only, which are
> [SLOT T: the zero-based epoch indices patch 0027 traces, cited to file:line; the set must
> include the end of epoch 1 and the end of epoch 10 (the canary rule), and the end of epochs
> 500, 1,000, 2,000, 4,000 and 7,000 (readouts, A1000 / D1000, R's terminal epoch). If it does
> not, state the canary comparison pair and the readout epochs that are used instead];
> (2) the feasibility test (a)-(c) is applied only on traced epochs, and only a traced epoch that
> meets (a)-(c) can become `model_best.keras`. An untraced epoch is recorded as "untraced", never
> as feasible or infeasible. The `model_min_ebops.keras` fallback and the [A19] sensitivity copy
> use traced epochs only. [SLOT C: whether a candidate is still saved every epoch, and the
> checkpoint cadence under k = 10, cited to patch 0027];
> (3) between traces, BetaPID reads [SLOT P: the quantity: the last traced EBOPs held, or the
> in-training EBOPs, as patch 0027 implements it, cited to file:line, together with the
> assertion that replaces `ablation.py:698-703`]. Both the in-training and the traced EBOPs are
> logged at every traced epoch, and the pilot readout reports their ratio per run;
> (4) [SLOT P, continued: what the WRAP integer bits `i` do between traces (the in-training
> tracking at `i_decay_speed` 1e-3, [D25], or otherwise) and on a traced epoch (a reset trace on
> the live model, or otherwise), as patch 0027 implements it, cited to file:line. Kai's decision
> leaves this open for ml-engineer; the text states the behaviour, it does not assume it];
> (5) certification of every evaluated checkpoint (Selection rule) is unchanged: a full-split
> reset retrace, relative difference ≤ 1e-6, same `ebops_trace_sample` and `ebops_trace_batch`;
> (6) regime B applies to every arm that has a [D20] trace, in wave 1 and wave 2 (NB, and H on its
> clone), so confound 10's "same rule in every arm" holds. FP32-E has no trace ([D26]);
> (7) the epoch count (7,000; R 1,000), the restart period, the LR peak and batch 2,790 are
> unchanged. Nothing is truncated.
> The 14-day rule now binds on the regime-B canary: T_run = 7,000 × s_e, with s_e measured over
> whole trace cycles (Symbols). The arithmetic from the measured split (RUN.md: trace 90.61 s,
> remainder 127.45 s) gives s_e ≈ 136.5 s and T_run ≈ 11.1 d at K=6. Kai's figure of about 9 d at
> K=5 is also arithmetic. Neither is a measurement. If the regime-B canary's T_run exceeds 14 d,
> production does not launch, and the case goes back to Kai.

(b) **[D20] and its DECISION block.**
- In [D20] "Per epoch" (l. 1754), replace "**Per epoch**, the candidate's ranges and EBOPs" with
  "**On each traced epoch** (every 10 epochs, regime B, [D15] branch executed 2026-09-27,
  Kai-decided; arbiter v9 fix 1), the candidate's ranges and EBOPs".
- Replace the "PID signal" bullet (l. 1767-1769) with the text of slot P from (a)(3), keeping the
  `ebops_in_training` logging clause.
- In the l. 1772 amendment, replace "the trace runs **once** per epoch" with "the trace runs once
  per traced epoch".
- In the DECISION block (l. 2304-2313): the first line becomes "[D20] WRAP ranges and
  feasibility EBOPs are traced every 10 epochs (regime B; Kai, 2026-09-27) on the full training
  split". Replace "FLAG FOR HUMAN: NO (...)" with "FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27:
  regime B after the canary's T_run 17.7 d; decisions.md)".
- Fidelity row "WRAP range update" (l. 493), worded to match slot P: replace "plus a per-epoch `trace_minmax(reset=True)`
  on the live model [D20]" with "plus a `trace_minmax(reset=True)` on the live model every 10
  epochs [D20], regime B", and replace "(the per-epoch reset pins `i` ... every epoch, which
  changes" with "(the reset every 10 epochs pins `i` to the full-split range on traced epochs,
  which changes".
- Fidelity row l. 492: "full training split every epoch" → "full training split every 10 epochs
  (regime B)".
- Selection rule, l. 803: "among every epoch whose freshly traced" → "among every traced epoch
  (regime B, every 10 epochs; [D15] branch executed) whose freshly traced".
- Confound 10 (l. 725-729): append "Under regime B (Kai, 2026-09-27) the trace runs every 10
  epochs in every traced arm, wave 2 included."

(c) **Budget and timing basis.**
- Symbols, s_e (l. 1279-1281): replace "(median of epochs 2-10)" with "(mean over zero-based
  epochs 10-29, two whole trace cycles, trace epochs included; a median would exclude the trace
  epoch; regime B, arbiter v9 fix 1)".
- Title "Illustrative projections" (l. 1287): keep it, and add at its head: "Superseded as the
  basis by the measured canary ([D15] branch executed, above). Kept as the registered prior."
- "Expected [D15] branch" (l. 1305): replace the paragraph's first sentence with "**[D15] branch
  (measured 2026-09-27).** The prior expected 'fits 14 days'; the K=6 canary measured 17.4-17.8 d
  for A and D, and the branch fired (see '[D15] branch executed')."
- [D15] (l. 1714-1717): append "Fired 2026-09-27 (canary 17.7 d); Kai chose regime B (trace every
  10 epochs); the 14-day rule binds on the regime-B canary."
- FLAG block at l. 2283-2288: replace "the expected branch ... is 'fits 14 days single-wave',
  subject to the canary" with "the prior expected 'fits 14 days'; the canary measured 17.7 d and
  the branch fired; Kai chose regime B (2026-09-27)". Replace "FLAG FOR HUMAN: YES (decision at the
  canary/launch gate)" with "FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27, regime B)".
- Pod-hours: at every site that quotes 1,750, 876, 438, 63, 218.9 h or 9.1 d as a plan (l. 1296,
  1297-1298, 1349, 1557, 1575, 1597-1599, 2158, 2283-2285), add "(prior, superseded; pod-hours = pods ×
  T_run from the regime-B canary)". Write no new pod-hour number until the regime-B canary
  measures s_e. If the fixer wants a number, it is the labelled projection 265 h per run at
  136.5 s (K=6 arithmetic).

(d) **Canary rules under regime B.**
- l. 1469: after "traced EBOPs ([D20] sample)", add "(regime B: at the traced epochs of slot T
  that stand for epoch 1 and epoch 10)".
- l. 1462 ("Reports s_e, split into train-step and overhead"): add "; the trace time is reported
  per traced epoch and amortized over the cycle".
- Outputs (l. 1484): the projected finish date uses s_e as redefined in (c).
- Canary window: "Phase 1, canary (epochs 1-10)" (l. 1395) → "Phase 1, canary (stability checks
  at epoch 10; timing over zero-based epochs 10-29, Symbols)". In "Trace-cost risk" (l. 1322-1324)
  replace "at epochs 1-10 and projects" with "over the s_e window (Symbols) and projects".

(e) **Pilot section.** At the end of the v8 amendment (after "(5) ... not 'infeasible'.",
l. 1394), add verbatim:

> *Amended 2026-09-27 ([D15] branch executed, Kai-decided; arbiter v9 fix 1):* a second pilot
> runs under regime B on the same seeds: a K=5 pod with A-s1, A-s2, D-s1, C′-s1 and E1-s1, and the
> K=3 pod of (1) above (A07-350-s1, C-s1, F-s1), which now runs under regime B. Both are built on
> the patch-0027 bundle after its PREFLIGHT addendum ([A21] re-asserted, full-set CPU gate,
> [A17]). The K=6 regime-A pod keeps running and is descriptive. The pilot rules above (canary,
> A rule, certification check, A07-350-s1 rule, C′ rule) are applied to the regime-B pods, and
> those gate production. The certification check also runs on the regime-A pod's snapshots, and
> a mismatch in either pod stops production. The regime comparison, the same arm and seed under
> A and B at epoch 500, is reported descriptively: traced EBOPs, the number of feasible traced
> epochs, the ratio of in-training to traced EBOPs, β, and best-feasible validation accuracy
> (never quoted). It selects nothing, triggers nothing, and does not reopen the regime choice. A
> return to regime A is a Kai decision. Regime-A pilot checkpoints cannot resume into production
> (`code_sha256` and `config_sha256` differ under patch 0027). Regime-B pilot checkpoints may
> resume if both shas match the production bundle.

- l. 1397-1400 (Phase 2 duration): replace the 15.6 h / 26 h projections with "about 19 h at the
  regime-B arithmetic (500 × 136.5 s at K=6; K=5 unmeasured), a projection".
- l. 1495-1496 (canary checkpoints resume rule): append "Regime-A pilot checkpoints do not match
  (patch 0027); see the regime-B amendment."

(f) **Pods and [D16].**
- Pods (l. 1336): replace "Every pod is a **seed block**: pod s holds seed s of A, B, C, D, F and
  A07-350 (K=6)." with "Wave 1 runs at K=5 on the A10 class, about 13 pods (Kai, 2026-09-27,
  [D15] branch executed). Six arms per seed do not fit one K=5 pod, so same-seed runs may sit in
  different pods; the production pod map is fixed at PREFLIGHT from the regime-B pilot's measured
  peak GPU memory per process (the A07 arms from the K=3 pod)."
- Keep "the GPU class of every run is recorded ...".
- [D16] (l. 1718-1719): append "Superseded 2026-09-27 by Kai's packing (K=5 on the A10 class, about
  13 wave-1 pods, about 27 at peak with wave 2 and Delta)."
- "Pod count" paragraph (l. 1348-1352): append the same sentence.
- GPU classes (l. 1345-1346): after "Use the generic classes (A10, L40, 3090, V100-32GB, 2080 Ti)"
  add "; wave 1 is restricted to the A10 class (Kai, 2026-09-27, [D15] branch executed); the generic
  list applies to wave 2 subject to its canary".

(g) **Kai rows** ("Where I am not sure").
- Row "pod count" (l. 2158), status cell: append "; **superseded 2026-09-27** (Kai, [D15] branch):
  about 13 wave-1 pods at K=5 on the A10 class, wave 2 about 4, about 27 at peak with Delta".
- Row "wave-1 packing after the A10 out-of-memory" (l. 2159), status: "**Kai answered
  2026-09-27**: K=5 on the A10 class, pod map at PREFLIGHT from the regime-B pilot's measured
  memory".
- Add a row after it: "| [D15] branch after the canary (arbiter v9 fix 1) | regime B: [D20]
  trace every 10 epochs, certification unchanged, second pilot under regime B | accept about 18 d;
  K=3 with about 22 pods; terminal epoch 2,000 / 4,000; cheap version | **Kai-decided
  2026-09-27** (decisions.md); the regime-B canary must pass the 14-day rule |".

(h) **K=7 rules and the second wave.**
- FP32-E launch exception (l. 1580-1590), "Pods, wave 1 at K=7" (l. 1595-1596), Overlap
  alternative (l. 1551-1553), and Kai rows "FP32 E arm" and "NB in wave-1 seed blocks": append
  "(closed by Kai's K=5 packing, 2026-09-27; no slot 7 exists; reopening it is a Kai decision)".
- "Pods, second wave" (l. 1590-1594): append "The second wave's K per pod is set by its canary's
  measured peak GPU memory. RUN.md extrapolates six E-sized processes to about 26,124 MiB,
  above an A10's 23,028 MiB. If the 24 runs do not fit 4 pods on the chosen class, the case goes
  to Kai before launch (ceiling about 27 pods at peak)."
- Second-wave cost (l. 1556-1557, 1575): the prior label from (c).

(i) **Change log.** Add an entry: "v1, revised after `review/STUDY_arbiter_v9.md` (ITERATE,
iteration 9, 2026-09-27): [D15] branch executed, Kai-decided (regime B: [D20] trace every 10
epochs; second pilot under regime B; K=5 wave-1 packing, about 27 pods at peak); physics v9
B1-B3; no change to any arm, seed, target, batch, epoch count, selection metric or certification
rule; selection restricted to traced epochs." List the sites with line numbers and the sha.

**2. (#3) Canary sources.** After the Stability list (after the ratio sentence ending "not a
result).", l. 1472), add verbatim:

> "Sources (arbiter v9 fix 2): train loss, `ebops_trace_seconds` and `ebops_trace_over_epoch` are
> read from the W&B run history (`ablation.py:754-755`; the per-arm log line at `:783` prints none
> of them). A check whose input cannot be read counts as a canary fail for that arm, not a pass.
> The K=6 pod's canary was read from W&B on 2026-09-27 (`RUN.md`, 'Canary — W&B history pull'):
> train loss finite and falling from epoch 1 to epoch 10 for A-s1, A-s2 and D-s1, and a trace
> share with a median of 0.42. C′-s1 had no epoch-10 read and is recorded as not evaluated."

In "Trace-cost risk" (l. 1322-1323), after "`ebops_trace_over_epoch` (patch 0023)" add "(from
the W&B history)".

**3. (#4) Confound 9 and Pods.** Replace l. 722-724, from "The GPU type is blocked by pod [D16]"
to "GPU-class column.", with:

> "Same-seed runs may sit in different pods (K=5 wave-1 packing, Kai 2026-09-27; K=3 for the
> A07 pod). Every wave-1 pod runs on the A10 class, so every same-seed paired comparison stays
> within one GPU class. Pairing rests on TF32 off, `jit_compile false` and seeded data order, not
> on co-residency. This is also why a pilot checkpoint may resume into production at a different
> K. A run re-created on another class is flagged in the GPU-class column that every paired table
> carries. R, and any wave-2 pairing with wave 1 (A − NB), may cross pods and are covered by the
> same column (arbiter v9 fix 3)."

At Pods l. 1338-1339, replace "each same-seed comparison runs on one GPU type" with "each same-seed
comparison runs on one GPU class (confound 9)".

**4. Required C.**
- (a) l. 1117-1118: replace "only if sd_diff comes in near 1 pt" with "only if sd_diff comes in
  at or below about 0.86 pt (1.0 / 1.16; arbiter v9)".
- (b) l. 1098-1101: delete "and " before "the n the formula gives", and replace the semicolon
  after "measured sd_diff)" with ", and", so the list reads "..., the feasible-pair count, the n
  the formula gives at max(proxy, measured sd_diff), and the 80 %-power detectable gap at 8 pairs
  and at that n, ...; it does not carry".

**5. Optional C** (phys C1-C4, crit C3 as a PREFLIGHT / REPORT note, and the carried v8 fix-6
optionals). Not required for v10.
