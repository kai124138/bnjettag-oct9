STUDY: ITERATE. R1 launch: ITERATE (not launchable now; launchable after P1-P4 land, panel v3 PASS and GATE_RESULT PASS on kai-pilot1005-cpugate-98dd28). No ESCALATE: panel iteration 2, every open A has a pre-data text fix of at most 1 agent-h, no rebuild.

# STUDY arbiter v2: pilot program, 2026-10-06

Arbiter, opus (06-review §6.5, §6.5.1). Written 2026-10-06 JST. Read-only except for this file.

Inputs (sha256 recomputed by the arbiter):
- `STUDY.md` `95c9b61f78a26840…7294` (written 14:35 on 2026-10-05, before K1).
- `PROGRAM.json` `cca098b190cda920…1dee` (F7, unsigned).
- `protocol-r1.json` `b75e2beb2de45e93…21d3`.
- `PREPARED.json` `325c38b8cac786a0…cc5d` (bundle `98dd2875b7c902bb…0059`).
- `review/STUDY_arbiter_v1.md`; `review/STUDY_{physics,critical,constructive}_v2.md`; `review/PREFLIGHT_critical_v2.md`; `PREFLIGHT.md` §3b; `JOURNAL.md`.
- Cluster: `kubectl get job kai-pilot1005-cpugate-98dd28 -n cms-ml` returned Running, 0/1, at the time of writing. There is no GATE_RESULT yet.
- No pilot data exists. Every rule change below is pre-data.

## Independent checks (by the arbiter, read-only)

| claim | check | result |
| --- | --- | --- |
| STUDY still registers w150 (crit A1, PREFLIGHT B-new-3) | `grep -n w150` returns STUDY.md lines 22, 42, 125, 136-137, 200, 203, 229, 231, 345, 347-348, and `protocol-r1.json` lines 223-224 and 248-249. Kai chose w100 on 2026-10-05 at 15:21 (JOURNAL) | **confirmed** |
| STUDY and the protocol give a "6 h" pod deadline (crit B1) | STUDY.md:310; `protocol-r1.json:674`. PROGRAM.json:51 gives `pod_deadline_s` 20800 | **confirmed** |
| Healthy has no accuracy term beyond (c) (phys A1) | STUDY.md §5 "Healthy = complete AND feasible_any AND nondegenerate_best AND entropy < 0.95". §7.3 "Accuracy is not a criterion". PROGRAM.json:56-62 `definitions.healthy` has no accuracy key. The entropy cut `"lt": 0.95` appears inline 11 times (`grep -c`) | **confirmed** |
| The rule change needs no rebuild | `readout_pilot.py` (frozen) has no `healthy`, `0.95` or `0.50` token. Health is computed only in PROGRAM.json | **confirmed**: the change touches STUDY and PROGRAM only |
| Q/K 0-bit fractions exist already (phys A1, descriptive half) | `analysis/attn_entropy.py:187-188` writes `QK_zero_bit_fraction` and `V_zero_bit_fraction` per block into the a26 record. The readout already runs a26 on every row | **present**. Only surfacing is needed |
| softmax zero-entry fraction (phys A1, descriptive half) | `attn_entropy.py` reports `zero_sum_rows` (:105, :137). That count is rows summing to zero, not the fraction of entries that are zero | **not computed**. The reviewer's "already computed" holds only for Q/K |
| Controller-error field empty for (c) arms (cons A1) | `ablation.py:522` traced iff epoch 0, (e+1) % k == 0, or the last epoch. `:577-578` a post-warmup epoch is stepped only if epoch e − 1 was traced. `:1139` the ratio is None on untraced epochs. `freeze_p.py:176-177` keeps records with a non-None ratio **and** `pid_stepped == 1`. Two consecutive traced epochs never occur after warmup | **confirmed** by code reading |
| Best-feasible checkpoint can precede t_budget (phys B3) | §5: best-feasible "meets (a)", i.e. traced EBOPs ≤ budget. t_budget is the first traced epoch that meets (a) (§5 diag) | **refuted as worded**: best-feasible ≥ t_budget by definition. The "transient early checkpoint" half stands (see B rulings) |

Jev `jev_triage_review`, audit `jv-3d620c90ed48477c9fadf4b262b9f807` (jev-1.13.0). It is advisory and is not a category. Its thresholds are "heuristic; not validated on lab data".

Jev's labels, with confidence and disposition:
- `likely_bug`: phys-A1 (0.83, suggestion), crit-A1 (0.94, suggestion), cons-A1 (0.63, review), crit-B1 (0.46, review), crit-B6 (0.91, suggestion), crit-B7 (0.27, review).
- `maintainability`: crit-B2 (0.66, review).
- `insufficient_evidence`: phys-B2 (0.69), phys-B5 (0.51), pre-B-new-2 (0.68), all with disposition review.

Jev agrees with the reviewers on all three A findings, so there is no disagreement to rule on. For the B findings Jev labels `insufficient_evidence`, the evidence is the cited text (STUDY.md §6 positive controls and §10.3; §9 guards; PREFLIGHT §3b). Nothing independent refutes them.

## Rulings on the v2 A findings (all stand; none dismissed)

| finding | ruling | fix |
| --- | --- | --- |
| crit A1 / PREFLIGHT B-new-3: STUDY and protocol register w150; bundle, PROGRAM and jobs run w100 | stands, A. Two launched pods would not be registered arms | P1 |
| phys A1: "healthy" lacks accuracy content wherever it drives r1, r_rec, W, V_bin and leads; the H3 lead can be produced by the instrument | stands, A. STUDY's own §5 text says the cut detects 0-bit Q (identical zero logits), and qkv1 forbids 0-bit Q by construction (`FlooredKIF`, cons v2 §2). So an H3 "lead" at val acc ≈ 0.3 is reachable under the current rule. No evidence refutes this. | rule P2 now; PROGRAM mirror Q1; descriptive half Q3 / D2 |
| cons A1: `readout_diag` controller error empty for every (c) arm | stands, A. It is descriptive and never a rule input, so it does not block launch. Its definition is pinned pre-data in P3, and the implementation lands before the readout (Q2) | P3 + Q2 |

## Rulings on v1 findings carried by name

Critical v2 checked every v1 A and B by name with line cites (its §"Earlier findings"). I accept those statuses. Two carry-overs remain:
- F9 (R2/R3 configs-only bundle) is open by design. It binds before the R1 readout (Q4).
- PREFLIGHT v1 A3 (STUDY gate) closes only with a STUDY arbiter PASS. That would be v3 after P1-P4.

## Question 3: does phys A1 have to bind before launch?

**Yes, the rule text in STUDY must land before launch. The PROGRAM.json mirror may follow before the readout.**

The rule is consumed only at r1_decide, after the readout, so on that reading the mirror alone would seem enough. That reading does not hold:
- STUDY.md:15-16 says "Rule changes after an R1 number exists are dated amendments signed by Kai and labelled post hoc".
- An R1 number exists as soon as the pods log validation accuracy and entropy-relevant telemetry, from epoch 1. Logs and W&B stream it.
- A selection-rule change written after launch would be written while the numbers it selects on are visible. That is exactly the pattern 06-review §6.3.3 lists ("a selection rule that changed after results existed").
- The cost of doing it before launch is about 0.3 agent-h of text inside the same designer pass as P1, which is already on the critical path. The gate (≈ 62 min for b3fb22, JOURNAL 16:14) overlaps it.

So the binding sequence is:
- STUDY amendment [A4], pre-data and before launch, carrying the rule and its frozen sha in `protocol-r1.json` → `lab_freeze_protocol`.
- The PROGRAM.json mirror, before the R1 readout. That is a Kai item, because PROGRAM edits are his to authorize, and it is outside the 24-arm/w100/stop-rule/F7 grant.
- Until the mirror lands, STUDY governs. The readout's `r1_decide` must not run on the unmirrored PROGRAM. This is already guaranteed, because `r1_readout` is a PLACEHOLDER (PROGRAM.json:631-637, crit B6) and stop rule 8 holds.

**Rule adopted (P2), designer to word it.** I choose the reviewer's option (i) over option (ii), for these reasons:
- (ii), a paired val-acc gain on every matched seed, is a sign test at n = 2 and adds nothing a floor does not.
- (i) aligns selection with production qualification, which already requires `best_feasible_val_acc ≥ 0.50` (§9).

The rule:
- **Healthy** = the current four terms AND `best_feasible_val_acc ≥ 0.50`. This one definition is used everywhere healthy is used: r1, the bracket, r_rec, W, V_bin, every H1-H5 lead and not-supported cell, the positive controls, and the production 6/8 early stop.
- Rows in (0.2110, 0.50) with entropy < 0.95 are **unhealthy**, labelled descriptively "attentive, low-acc". That is the case where attention is restored but the network is not useful.
- The entropy-only failure (acc ≥ 0.50, entropy ≥ 0.95) is unchanged and still stops for Kai.
- The four classes then partition every complete, feasible, non-degenerate row.
- §7.3: strike "Accuracy is not a criterion". Insert "then higher mean `best_feasible_val_acc` over the arm's seeds" after the `feasible_any` count and before entropy. This is validation, the frozen selection split.
- Consequence to state in the text: if no E rung reaches healthy under the floor, §7.1 stops for Kai (characterization pivot). That is intended. Production qualification would fail at the same floor anyway, so R2 pods are no longer spent on a bracket that cannot qualify.
- The 0.50 floor stays internal-only (§9 text unchanged).

## Fix list A: must land BEFORE the R1 launch

All of these are pre-data text. None rebuilds the bundle, changes a handoff byte or touches PROGRAM.json. Agent-hours (ah) are this arbiter's estimates.

| # | fix | owner | rebuild | cost | closes | PROGRAM.json |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | STUDY [A4] header block citing decisions.md 2026-10-05 15:21 (K1-K4). Rename row 6 to `A350-C-w100` (warmup 100; first feedback at epoch 110 leaves 390 epochs, from the local cpu_gate `evidence/final-tree-98dd28/cpu_gate.log:72,76`, not quotable). Fill both D3 "Recorded" lines. Update :22, :42, :200, :203 (state whether "time-limited" still applies to w100), :229, :231. Update `protocol-r1.json:223-249` | experiment-designer | no | 0.3 | crit A1, PREFLIGHT B-new-3, cons v1 B3 | no |
| P2 | In the same [A4]: the healthy rule above (§5, §6 table, §7.1-7.4, §8, §9 early stop). Plus these text items:<br>(a) phys B1: one sentence saying no R1/R2 verdict attributes the accuracy loss to attention while the mean-pool control is deferred.<br>(b) phys B2: E-unc-C uses PID target 100,000,000 (crit C4). It is judged healthy on the same rule, with its entropy recorded as the E calibration value. If its entropy is ≥ 0.95 at acc ≥ 0.50, the existing §10.2 stop fires and the text names it "E cut uncalibrated".<br>(c) phys B3: health is read on the best-feasible checkpoint. Its epoch and the epoch-500 snapshot acc/entropy (diag) are listed beside every row that feeds a derivation, never as a criterion.<br>(d) crit B7: R3 runs only if A at r_rec has seeds 2-4 healthy.<br>(e) cons C1: qkv1 t_uniform is None by construction, so H3's mechanism is read from site_order and cost_split.<br>(f) phys C1: label 0.276 a crude independence bound, or give 0.190.<br>(g) phys C3: n = 1 per rung in the H2 row.<br>(h) phys C4: path and line of A-s2/D-s1.<br>(i) phys C5 and crit C3: "Acc (%)" as in the source, the MHA-64 collapse noted as context, and Chang's pT < 2 zeroing.<br>(j) crit C2: dev/README `:70-71`.<br>(k) cons C2: E-unc-C `share_of_total` only.<br>Then rerun `lab_check_protocol` and run `lab_freeze_protocol` | experiment-designer | no | 0.7 | phys A1 (rule), phys B1 (text), B2, B3, crit B7, C2-C4, cons C1-C2, phys C1-C5 | no (mirror is Q1) |
| P3 | Covers crit B1 and P3a. STUDY §11 and `protocol-r1.json:674`: replace "6 h" with 20,800 s, state the A07 margin (680 s at 38.8 s/epoch, gpu-benchmark `VERIFY.md:109`, n = 1 × 20 epochs; 4,655 s at 30.85 s), and say that a deadline hit is an integrity stop. **P3a, same pass:** pin the controller-error definition in §5 diag, pre-data: over traced epochs ≥ warmup, the same filter for noC and (c), the median and max of `ebops / target_ebops` and of `ebops_in_training_over_traced` | experiment-designer | no | 0.2 | crit B1, cons B1, cons A1 (definition) | no |
| P4 | PREFLIGHT.md §3c "Frozen 98dd2875 (2026-10-06)". It holds the 24-row job/rh-ID table from PREPARED.json, gate rh-c11b0c23, readout rh-deccad51 at 43,200 s, D = 20,800, and the bound "143.87 GPU-h + Σ first-attempt pull/init over retried arms + disruption replacements, all counted against the cap when they occur", with the orchestrator named as spend checker at follow-up (RULES §4). Mark §3b's 21,600 / 149.2 text superseded | ml-engineer | no | 0.4 | PREFLIGHT B-new-1, B-new-2, crit B5 (PREFLIGHT half) | no |
| P5 | Re-review: STUDY panel v3 and arbiter v3 (Question 4). Critical v3 also confirms by grep that P4 landed (PREFLIGHT L3) | orchestrator | no | ~0.5 wall, overlapping the gate | PREFLIGHT v1 A3 / L2 | no |

Then launch under L1 (GATE_RESULT PASS), L2 (STUDY arbiter v3 PASS), L3 (P4) and L4 (gate-cleared re-preparation, byte rule) from PREFLIGHT_critical_v2. Then STOP, per Kai's order.

Total before launch is about 1.6 ah across two owners in parallel (designer 1.2, ml-engineer 0.4). P1-P3 are one designer pass. Critical path: designer pass ≈ 1 h → panel v3 ≈ 0.5 h, set against a gate submitted at 05:58.

## Fix list B: must land BEFORE the R1 readout, R2 or production (not this session)

| # | fix | owner | rebuild | cost | closes | PROGRAM.json | binds before |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 | Mirror P2 into PROGRAM.json: `definitions.healthy` adds `best_feasible_val_acc ≥ 0.50`; the 11 inline `"lt": 0.95` health sites get the same term; the W/V_bin ordering gets the acc key; R3 gets seeds 2-4 (crit B7) | main session under Kai | no | 0.75 | phys A1 (mirror), crit B7 | **yes (Kai)** | R1 readout |
| Q2 | Readout-only re-preparation (`--only readout`), with a new crafted-harness case built from the real stepped/traced pattern. It includes:<br>• the controller-error filter per P3a, cons A1(a);<br>• a26 on `checkpoints/epoch-0475/model.keras`, cons B2;<br>• `QK_zero_bit_fraction`/`V_zero_bit_fraction` surfaced per row from the a26 record, phys A1 descriptive half.<br>No bundle or GPU handoff change. A solo PREFLIGHT critical review of the readout handoff follows (≈ 0.3 ah) | ml-engineer | no (readout handoff only; new rh-ID) | 0.75 + 0.3 | cons A1, cons B2, phys A1 (descriptive, Q/K) | fills `r1_readout` (Q4) | R1 readout |
| Q3 | crit B6 + C1 + PREFLIGHT C4: job-name pattern `kai-p1005r1-*-98dd28`; the 24 handoff IDs listed (or PREPARED.json pinned by sha); `r1_readout` filled with Q2's rh-ID, job and OUT; `pods_requested` 24 | main session under Kai | no | 0.5 | crit B6, C1; PREFLIGHT C4, L5 | **yes (Kai)** | R1 readout / any autopilot use |
| Q4 | crit B4: `r23_bundle_gate` gets a timeout → `stop_notify_kai` and the job name once F9 builds it | main session under Kai | no | 0.1 | crit B4 | **yes (Kai)** | R1 readout |
| Q5 | F9 (arbiter v1): R2/R3 configs-only bundle, byte-diff, cpu_gate + pair_nb, solo PREFLIGHT review; 350k rows emitted as `program_arm` `A350-C` (crit B6 D-6) | ml-engineer | configs-only bundle | 2.0 + gate | crit v1 A1, cons v1 A1 (complete) | `r23_bundle_gate` job name | R1 readout (STUDY §7) |
| Q6 | crit B2: the fresh-seed filter as machine `seed not_in` where-clauses, with the all-rows scope aligned with STUDY (or STUDY amended to the stricter form; designer's call, before the R1 readout) | main session under Kai | no | 0.5 | crit B2 | **yes (Kai)** | R2 readout (prod_qualify) |
| Q7 | crit B5 (PROGRAM half): a disruption caveat in `caps.r1_worst_case`, and the spend checker named | main session under Kai | no | 0.1 | crit B5 | **yes (Kai)** | R2 launch |
| Q8 | crit B3: an owner and mechanism for the production 6/8 early stop (a production epoch-500 readout Job plus a PROGRAM step, or a manual check written into the production PREFLIGHT) | experiment-designer + ml-engineer | no | 1.0 | crit B3 | yes (Kai) | production |
| Q9 | phys B5: add a csynth DSP/LUT/II check (`mulder`) of the candidate's selected checkpoint to the §9 guards, or state that it is absent and why. A STUDY text amendment is pre-data for production | experiment-designer | no | 0.2 text (+ csynth run ≈ 1-2 ah at the production gate) | phys B5 | yes (guard list) | production |
| Q10 | phys B4: report the fresh-seed subset beside the 8-seed production result (text), with D8 decided at the production gate (K-c) | experiment-designer | no | 0.1 | phys B4 | no | production |

## Deferred (each with cost, reason and date)

- **The softmax zero-entry fraction, phys A1 descriptive half. Deferred to R1 VERIFY.**
  - Cost: about 1 ah, either a diag model-load loop in the readout heredoc or a VERIFY-time recompute from the copied checkpoints.
  - Why it does not change the conclusion: with the accuracy floor in healthy (P2), no lead can come from an entropy drop alone. The column is reading context, never a rule input, and the Q/K 0-bit fractions (Q2) already separate "logits no longer exactly zero" from a collapsed head.
  - When: R1 VERIFY (results-analyst).
- **phys B1, the mean-pool control pod. Deferred, unchanged from v1.**
  - Cost: ~3-4 ah of architecture code + a gate + 1 pod. Trading the w100 s2 pod would need that code, a rebuild and a third gate (~62 min) before launch, and it would reset the F6a byte-equal baseline.
  - The text half is adopted (P2a). It is the first post-program follow-up.
- **cons C3 / PREFLIGHT C2, readout deadline margin.** No change now (0 ah). Measure it against the R1 readout wall time.

## Question 4: third full panel round, or a solo critical check?

**A full panel v3, scoped to the [A4] diff and P4, followed by arbiter v3.** The reasons:
- 06-review §6.5 requires that every ITERATE at a panel tier write `STUDY_{physics,critical,constructive}_v<n>.md` and an arbiter file. A solo check of a STUDY rule change would be "fix → advance without a re-review" at the panel tier, which §6.5 names a process failure.
- P2 changes the central decision rule. The fresh-context physics reviewer is the one who raised it, and it is the right check that the new rule says what physics meant.
- Cost: three opus reviewers in parallel, about 0.5 h wall. They overlap the CPU gate, so the delay to launch is at most about 0.5 h. A solo check would save perhaps 15 min.
- Scope instruction for v3:
  - physics, fresh: STUDY [A4] only;
  - critical: every v2 A/B by name, plus the P4 grep for L3;
  - constructive: P2/P3a only.
- This is panel iteration 3, so the §6.5 warning applies. If v3 raises a new A that needs more than text, the arbiter escalates to Kai rather than loops.

## Needs Kai (one at a time, in this order)

- **K-a. Authorize the PROGRAM.json edits Q1, Q3, Q4, Q6 and Q7 (about 2 ah total in the main session), before the R1 readout.** These go beyond the 24-arm/w100/stop-rule/F7 grant. Recommended default: **authorize them as one batch after R1 is launched and before the readout**, with Kai's signature (`signed_by_kai`) on the result. None of them is needed for the launch, which runs under Kai's direct order.
- **K-b. The healthy rule (P2) adds `best_feasible_val_acc ≥ 0.50` to every selection and lead.** Recommended default: **accept.** It is pre-data. It aligns selection with production qualification. Its cost is that a program in which no E rung reaches 0.50 stops for Kai at r1_decide instead of spending R2. This is a scientific-rule choice in Kai's study, so he should see it, but the launch need not wait if he has not answered: STUDY [A4] registers it, and he can overrule it pre-readout with a dated post hoc amendment.
- **K-c. D8, production seeds 1-8 (pairing with training-batch) vs 9-16 (all fresh).** Recommended default: **keep 1-8** for the [A17] pairing, and report the fresh-seed subset beside the 8-seed result (Q10). Decide at the production gate.
- **K-d. A csynth guard before production (Q9).** Recommended default: **add it.** It costs about 1-2 ah of `mulder` time, set against about 960-1,207 GPU-h of production (STUDY §11 arithmetic: 7,000 × {30.85, 38.8} s × 16 / 3,600).
