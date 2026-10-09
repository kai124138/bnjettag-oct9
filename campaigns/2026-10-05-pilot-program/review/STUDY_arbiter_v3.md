STUDY: PASS (conditional on S1-S3 landing before submission; no panel v4). R1 launch: PASS, conditional on L1 GATE_RESULT PASS on kai-pilot1005-cpugate-98dd28, S1-S3 landed and checked by grep, and the L4 byte rule at submission. No ESCALATE: panel iteration 3 (§6.5 warning noted), no open A.

# STUDY arbiter v3: pilot program, 2026-10-06

Arbiter, opus (06-review §6.5, §6.5.1). Written 2026-10-06 JST. Read-only except for this file.

Inputs:
- `STUDY.md` sha256 `11005dfb3c3df956…235eac44` (recomputed by the arbiter; matches [A4], JOURNAL 06:13).
- `review/STUDY_arbiter_v2.md` (P1-P5, Q1-Q10).
- `review/STUDY_{physics,critical,constructive}_v3.md`, `review/PREFLIGHT_critical_v2.md`.
- `PREFLIGHT.md` §3c and §4, `JOURNAL.md`, `protocol-r1.json`.
- Cluster: `kubectl get job kai-pilot1005-cpugate-98dd28 -n cms-ml` returned Running, 0/1, 26 min, at the time of writing. There is no GATE_RESULT, so L1 is open.
- No pilot data exists. Every change below is pre-data.

## Independent checks (by the arbiter, read-only)

| claim | check | result |
| --- | --- | --- |
| crit B-v3-2: the pilots apply the same pT < 2 GeV gate as Chang | `grep -l '"pt_gate_gev": 2.0'` over the 24 frozen configs in `code/tree/campaigns/pilot1005/configs/` returns 24 files | **confirmed**. STUDY.md:315-316 ("Chang's pipeline zeroes constituents with pT < 2 … so the inputs differ") is wrong |
| crit B-v3-3: PREFLIGHT §4 still describes the superseded build | PREFLIGHT.md:507-510 (P2 "no activeDeadlineSeconds on the 23 GPU Jobs … 6 h"), :523 (P7 "warmups 50 and 150"), :536-537 (P11 "23 arms … 8 h"), :540-545 ("Open before any launch") have no supersession banner | **confirmed** |
| crit B-v3-1: the readout blockers are not registered | STUDY.md:60-61 ties the Q1 guard to the `r1_readout` placeholder. PREFLIGHT.md:442 names `rh-deccad5136f005dcb4250764` as the readout, and Q2 is not mentioned | **confirmed** |
| cons B2: band-edge gap | STUDY.md:194, :197 and `protocol-r1.json:633` write "(0.2110, 0.50)". `nondegenerate_best` means > 0.2109624456315518 (STUDY §10.1). On n = 62,000, 13,080/62,000 = 0.210968, 13,081/62,000 = 0.210984 and 13,082/62,000 = 0.211000 lie in no class | **confirmed** (arithmetic) |
| phys B4: is attention entropy visible to anyone before the readout? | The training code in `code/tree/bnhgq2/` (ablation.py, train.py) logs no attention entropy. It is computed only by a26 at the readout. Per-epoch Q/K widths are logged (`activation_widths.jsonl`), so a 0-bit Q, which is the collapse mechanism, **can** be seen during the run | **partly visible**. This bears on the timing of K-1 below |

Jev `jev_triage_review`, audit `jv-75b0f9ff6147408aa5422c6f3d551d7b` (jev-1.13.0). It is advisory, with thresholds "heuristic; not validated on lab data".

Jev's labels, with confidence and disposition:
- `likely_bug`: cons-B2 (0.83, suggestion), crit-B-v3-2 (0.77, review), crit-B-v3-1 (0.68, review).
- `maintainability`: crit-B-v3-3 (0.43, review).
- `insufficient_evidence`: phys-B1 (0.31), phys-B2 (0.36), phys-B3 (0.40), phys-B4 (0.51), cons-B1 (0.43), all with disposition review.

There are no A findings, so the A-disagreement rule (§6.5.1) does not apply. For the five B findings Jev labels `insufficient_evidence`, the reviewers cite the evidence themselves:
- phys B1-B3 cite STUDY §5, §6 and §9 text.
- phys B4 cites `chang-vs-bnjettag.md:107-110`.
- cons B1 cites the code reading at `ablation.py:1103-1139` and the b5 prior.

Nothing independent refutes any of them. **All stand at B.**

## Earlier findings (arbiter v2), by name

I accept critical v3 §1 and §4 as the status of every v2 A and B. I checked spot items myself: the STUDY sha, the w100 row, the healthy rule at STUDY:175-181, the 20,800 s deadline, and the absence of "6 h".

| v2 item | status |
| --- | --- |
| P1 (w100), P2 (healthy rule and text items), P3 / P3a (deadline, controller-error definition) | **landed** in STUDY [A4] and `protocol-r1.json` (snapshot `123d3654`, `matches_snapshot true`) |
| P4 (PREFLIGHT §3c) | **landed**. The §4 residue is B-v3-3 → S2 |
| P5 (panel v3) | **done**: this file |
| phys v2 A1, crit v2 A1, cons v2 A1 (definition) | **resolved** |
| Q1-Q10 | open by design. Re-bound below |
| Deferred: softmax zero-entry fraction (R1 VERIFY), mean-pool control (post-program), readout margin (measure at readout) | unchanged. Crit C3 notes that the first of these is not written in STUDY §15 → folded into R6 |

## Rulings on v3 findings (none dismissed)

All v3 findings are B or C. None is dismissed. Each is assigned to the earliest point where it binds.

### S: must land BEFORE submission of the 24 R1 Jobs (launch conditions)

These are text only. None of them touches a code, config, manifest, handoff or PREPARED byte, so the bundle, the gate and the L4 byte rule are unaffected. No panel v4 is needed: the orchestrator checks them by the greps listed, and the result goes in JOURNAL.

| # | finding | fix | owner | cost (ah) | check |
| --- | --- | --- | --- | --- | --- |
| S1 | crit B-v3-1 | One sentence in STUDY [A4] (near :60-61) and in the PREFLIGHT §3c readout paragraph (:442): "The R1 readout Job is not submitted until arbiter v2 Q1-Q5 have landed. Q1 and Q3 land in one PROGRAM.json edit. The readout is the Q2 re-preparation, not `rh-deccad51`, unless Kai rules otherwise." Also delete the "or a VERIFY recompute" fallback at STUDY:215 as the readout's source. VERIFY may still recompute as a cross-check | experiment-designer (STUDY) + ml-engineer (PREFLIGHT) | 0.1 | `grep -n "Q1-Q5" STUDY.md PREFLIGHT.md` gives ≥ 1 hit each |
| S2 | crit B-v3-3 | A banner "Superseded by §3c (bundle 98dd2875): P2, P7, P11 and the open-before-launch list describe b3fb22/1f7c4e" at the head of PREFLIGHT §4, plus one note on P7: "w100 since K1" | ml-engineer | 0.1 | the banner precedes PREFLIGHT:500. `grep -n "50 and 150"` hits only under it |
| S3 | cons B2 | Replace "acc in (0.2110, 0.50)" with "`nondegenerate_best` and acc < 0.50" at STUDY:194, :197 and `protocol-r1.json:633`. Then run `lab_check_protocol` and `lab_freeze_protocol` again, because the protocol bytes change, and record the new snapshot sha in JOURNAL | experiment-designer | 0.1 | `grep -c "0.2110, 0.50" STUDY.md protocol-r1.json` = 0; new snapshot `matches_snapshot true` |

**In the same designer pass, but not a launch condition:**

| # | finding | fix | cost (ah) | binds at latest |
| --- | --- | --- | --- | --- |
| S4 | crit B-v3-2 | Replace STUDY:315-316 with: "The pT < 2 GeV gate and the 558k/62k split are the same as Chang's (`arch.pt_gate_gev` 2.0, chang0926 [D7]); the differences are learned-width weights and 7,000 epochs." Attribute the "attention-healthy 350k row" label as the lab's reading (phys C5) | 0.05 | R1 readout |

S1-S4 total about 0.35 ah. They can be done inside the remaining gate wall time (gate submitted 05:58; the b3fb22 gate took 62 min, JOURNAL 16:14). So they cost the launch about nothing.

**Why S1-S3 bind before submission and the others do not:**
- S1 is the one guard that keeps the readout from running on an unmirrored PROGRAM or on the readout handoff the panel now knows is incomplete. As written, the guard disappears as soon as Q3 fills the placeholder.
- S2 removes the last live statement of a superseded configuration from the document the launch cites (L3).
- S3 closes a hole in a registered selection rule. A rule edit after launch would be post hoc under STUDY:15-16, as ruled in arbiter v2 Question 3. Its cost is near zero.

### R: must land BEFORE the R1 readout is submitted (not this session)

**R1. phys B1: condition H1/H3/H4 reads on the control's class.**
- Fix: list the §5 class of every control row beside each H1/H3/H4 verdict. Read H3 "lead" only when the A350-C rows are "low-acc uniform"; otherwise read "lead (accuracy, not attention)".
- Owner: experiment-designer, text. Cost: 0.15 ah.
- Why not before launch: no rule consumes the H verdicts (STUDY §6). The classes need a26 entropy, which exists only at the readout.

**R2. phys B2: H2 refutation asymmetry.**
- Fix: either count "low-acc uniform" at 5M as not-supported when E-unc-C passes, or state why it is weaker evidence.
- I recommend counting it. It is unhealthy on accuracy alone, and E-unc-C passing removes the "recipe cannot reach 0.50 on E" excuse.
- Owner: experiment-designer, text. Cost: 0.1 ah.
- H2 is descriptive at n = 1 per rung.

**R3. phys B3: A at r_rec is selected, not independently qualified.**
- Fix (minimum): §9 states it, and names the production 6/8 early stop as the only independent check on A at r_rec. The +1 fresh-seed alternative is K-3.
- Owner: experiment-designer, text. Cost: 0.1 ah.

**R4. phys B4: the D1 ruling on accurate uniform-attention rows.**
- This is Kai's (K-1). The registered rule stays until he rules: an entropy-only failure stops for Kai (§10.2).
- That rule is conservative. It spends nothing and selects nothing.

**R5. cons B1: controller-error windows.**
- Fix: add `min(ebops / target_ebops)` and a settled window `epoch ≥ max(warmup, t_budget)`, with n per statistic, to STUDY:210-215 and `protocol-r1.json:700`. Implement it in the Q2 heredoc.
- Phys C1 is answered by the settled window and by naming which `ebops` is used.
- Cost: 0.1 ah of text, plus about 3 lines inside Q2.
- It is descriptive and never a rule input.
- If S3's designer pass has time, land the text then. It is pre-data either way, but before launch it is cleaner.

**R6. Q2: readout-only re-preparation.**
- Scope as in arbiter v2, plus R5.
- Register in STUDY §5 the a26 on `checkpoints/epoch-0475` and the Q/K 0-bit fractions (cons C1, crit C3).
- Register in STUDY §15 the softmax zero-entry deferral to R1 VERIFY (crit C3).
- Name the null-entropy row an integrity stop at §10.1 (cons C3).
- Then a solo PREFLIGHT critical review of the new readout handoff.
- Owner: ml-engineer. Cost: 0.75 + 0.3 ah, plus 0.1 ah text.

**R7. Q1, Q3, Q4, Q6, Q7: the PROGRAM.json mirror.**
- This is Kai's (K-2).
- Q1 and Q3 go in one edit (S1). Q6 and Q7 bind formally at R2, but they belong in the same signed batch.
- Cost: about 2 ah in the main session.

**R8. Q5 (F9): the R2/R3 configs-only bundle.**
- Byte-diff, cpu_gate + pair_nb, and a solo PREFLIGHT review.
- Owner: ml-engineer. Cost: 2.0 ah + gate.
- It is a registered stop (§10.4), so the R1 readout cannot be read without it.

Items R1-R3 and R5 change only how a lead or a descriptive field is read. No selection rule changes and no pod is spent. They may be written after launch, provided they are a dated amendment [A5] marked "written after launch, before any readout; no a26 entropy or class computed". Q/K widths stream during the run, so the amendment must not be conditioned on them. If the designer pass for S1-S4 has slack before GATE_RESULT, land R1-R3 and R5 in it instead. That is preferred.

### Production (unchanged from v2)

Q8 (owner of the 6/8 early stop), Q9 (csynth guard, K-d) and Q10 (fresh-seed subset, K-c) bind at the production gate.

### Grade C (fold into the next designer pass; no dismissal)

| item | fix | cost (ah) |
| --- | --- | --- |
| crit C1 | STUDY:163 cites the derivation source of the 0.2109624456315518 threshold, not PREFLIGHT:519 | 0.02 |
| crit C4 | PREFLIGHT §3c expected spend "104.8 to 131.3" | 0.02 |
| phys C2 | record the β trajectory for E-unc-C in `readout_diag.json` (Q2) | 0.05 |
| phys C3 | W tie-break after mean accuracy → fixed arm order, not entropy | 0.05 |
| phys C4 | E and NB at K = 1 have unmeasured utilization. Already covered by §10.5 and PREFLIGHT P4, so no change | 0 |
| cons C2 | log10 ratios, optional | 0 |
| crit C5 | no action; this is K-2 | 0 |

## Verdicts

**STUDY: PASS**, conditional on S1-S3 landing before submission.
- All three reviewers pass the artefact: physics PASS, critical PASS (R1 launch), constructive PASS.
- No A is open. Every v2 A is resolved in text (crit v3 §1).
- The remaining B findings are text or Kai items, bound above with costs and dates.

**R1 launch (24 pods, bundle 98dd2875, handoffs per PREPARED.json): PASS**, conditional on:
- L1: `GATE_RESULT PASS` in the log of `kai-pilot1005-cpugate-98dd28`. If the gate fails, there is no launch: stop and report (RULES §5).
- S1-S3 landed, with the greps above recorded in JOURNAL.
- L4: the gate-cleared re-preparation byte rule (PREFLIGHT critical v2) at submission.

Then STOP, per Kai's order. The R1 readout is not submitted this session in any case: R6-R8 are open.

## Needs Kai (one at a time, in this order)

**K-1. phys B4 / D1: rows with acc ≥ 0.50 and entropy ≥ 0.95 ("accurate, uniform attention").**
- Today such a row stops the whole program (§10.2). A mean-pooled head is a Deep Set, and the cited MHA-64 row reached 77.9 % "Acc (%)" (source label, their test split) at 350k. So this is a foreseeable R1 outcome at higher E rungs.
- **Recommended default:** such a row counts as healthy for r1, the bracket, r_rec, W and V_bin. It is labelled "accurate, attention-collapsed" in every table and is excluded from the H3/H2′ attention-mechanism reads. If E-unc-C is in this class, its entropy is recorded as the E calibration value and does not stop the program. Any production candidate in this class is flagged to Kai, who already sees every candidate under stop 7.
- **Timing:** best answered **before launch**. Q/K widths stream during the run, so a later ruling would be made with collapse signals partly visible and must be labelled post hoc (STUDY:15-16).
- If Kai has not answered at submission, launch anyway under the registered stop-for-Kai rule. It is conservative and spends nothing.
- Cost to land: 0.15 ah of designer text (STUDY §5, §6, §10.2, D1; `protocol-r1.json`; re-freeze).

**K-2. Authorize the PROGRAM.json batch Q1, Q3, Q4, Q6 and Q7 (about 2 ah, main session).**
- **Recommended default:** authorize it as one signed batch after launch and before the R1 readout, with Q1 and Q3 in the same edit (S1).

**K-3. phys B3: an independent check on A at r_rec.**
- **Recommended default:** the text label (R3), with the production 6/8 early stop as the independent check, and no extra pod now.
- Revisit at the R2 readout. The alternative is +1 fresh A seed at r_rec in R3, which raises the R3 cap from 3 to 4 pods: at most 5.99 GPU-h per pod (24 × 21,580 s = 143.87 GPU-h over 24 pods, PREFLIGHT §3c).

**K-c, K-d (carried from v2).** D8 seeds and the csynth guard, both at the production gate. Recommended defaults are unchanged: keep seeds 1-8 and report the fresh-seed subset; add the csynth guard.
