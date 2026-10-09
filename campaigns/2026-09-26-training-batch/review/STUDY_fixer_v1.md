# STUDY fixer v1: 2026-09-26-training-batch

Fixer, fresh context, 2026-09-27. Input: `review/STUDY_arbiter_v1.md` (ITERATE, 27 items),
`review/STUDY_investigation_350k.md`, `STUDY.md`, `plan.md`, experiment-log stub.

State found: an earlier fixer pass had already edited STUDY.md in place (change log under the
frontmatter; plan.md "Fixer pass after review/STUDY_arbiter_v1.md"). This pass audited every
arbiter item against the file, closed the remaining gaps, and wrote this report. A concurrent
writer touched STUDY.md and plan.md at 00:01-00:02 (fidelity citation `model.py:184` → `:186`,
correct against `reference-code/HGQ2-examples/jsc150/model.py`); every edit here was an exact
string replacement and applied cleanly. The orchestrator should confirm no other agent is still
writing before commit.

Numbers: none recomputed here. Every number stated comes from the arbiter file or the
investigation file, with its label.

## Per finding

```
1 (A) Primary question claimed a test of binary weights / "iso-cost" — RESOLVED
  changed: STUDY frontmatter question, title (l. 30), Question/Null/Bearing (l. 32-51),
    Falsifier "Primary measurement (descriptive, no pass or fail)"; "iso-EBOPs, not iso-cost";
    "binary survives" / "measures what binary costs" removed (earlier pass, audited)
  verified: grep "iso-cost" → only "not iso-cost"; "binary survives", "H0-primary",
    "tolerance", "Inconclusive" → 0 hits; prose_lint score 0
  propagated: experiment-log stub title, Question and Design lines rewritten in place
    (question-first kept); comparisons table and "Where I am not sure" comparand block match
  neighbourhood: every 78.4 occurrence now "descriptive line"; Conventions house-rule row
    "falsifier stated" says the 79.4 distance is descriptive
2 (A) Competing-group answer (arm H) unjustified — RESOLVED
  changed: "Where I am not sure" block "no non-binary arm in this campaign": arm H (jsc150
    xfm-n64, 8 seeds, gated 90/10, same selection, ROC-test once) and the in-house non-binary
    arm (qat.py:333-336) as pre-registered follow-ups, FLAG FOR HUMAN at the canary/launch gate
  verified: block present with the three reasons named by the arbiter
  propagated: Bearing paragraph points to it; §6.8 conventions row; log stub "arm H ... Kai
    decisions at the launch gate"
  neighbourhood: no arm table row added (design unchanged, 56 runs)
  remains / route to: Kai decision (arm H, in-house arm), not a design change here
3 (A) Resolving power sized from the cross-N sd — RESOLVED
  changed: reference table row "Archived Round 14, N=64, context for sd only" (W1A8 69.0 ± 3.1 %,
    FP32 79.1 ± 0.3 %, held-out, n = 260,000, 3 seeds, archived); Seeds: 0.836·sd, k = 6 1.05·sd,
    ±0.16 pt at N=8 sd 0.19 pt, ±2.63 pt at archived N=64 sd 3.14 pt (0.0314), 0.6 / 0.48 pt
    ceilings; epoch-500 sd labelled early estimate; [D13] consequence (> 0.6 pt → Kai before
    epoch 1,000: continue descriptive / add seeds / stop)
  verified: all values copied from arbiter "Independent checks" and fix #3; grep: 2.63, 3.14,
    0.0314, 0.48 each appear once, consistent
  propagated: log stub Design line (0.836·sd, ±0.16, ±2.63, 3.14 pt, epoch-500 rule)
  neighbourhood: cheap-version half-width 1.59·sd and "0.5-point line needs sd ≤ 0.3" read
    consistent with the same t-factors
4 (A) Tie-break order not what the copied config runs — RESOLVED
  changed: Selection rule paragraph (explicit order acc → val AUC → −EBOPs → −epoch, cites
    ablation.py:421); [A13] explicit cost_before_auc=False override + unit test on a
    constructed accuracy tie; [D11] amended
  verified: grep "exactly as `checkpoint_selection_key`" → 0 hits
  propagated: log stub "enforced by [A13]"
  neighbourhood: [A18] strips the other stale inherited fields (#25)
5 (B) Reference uncertainty at tolerance scale — RESOLVED
  changed: [L1] now carries +1.05 pt (Linformer) and +2.7 pt (MHA), single seed,
    test-selected, unverified; unstated selection ("several trained models"); gate question
  verified: values match arbiter #5 and reference-table REPRO-CHANG row
  propagated: Falsifier primary measurement reports A − 79.4 with 95 % interval
  neighbourhood: Null paragraph states no null for the distance
6 (B) Comparand conditioned on a post-hoc diagnostic — RESOLVED
  changed: Falsifier fixes 79.4 unconditionally with the Deep-Set-collapse reason; distances to
    79.8 and 77.9 in every outcome; "Deep Sets is the right comparand if ours collapses" deleted
  verified: grep "right comparand" → 0 hits
  propagated: "Where I am not sure" comparand block
  neighbourhood: attention diagnostic text ends "It does not change the comparand"
7 (B) "Attention alive" conflates Q/K and V — RESOLVED
  changed: Falsifier "Required diagnostic": Q/K 0-bit fraction, V 0-bit fraction, mean
    attention entropy / log 64 over validation n = 62,000; "Is 350k reachable" bullet fixed
    (V pruning removes the branch; Q/K collapse or uniform attention gives the Deep Set)
  verified: grep "attention alive" → 0 hits
  propagated: none needed   neighbourhood: fidelity-table softmax 10-bit row consistent
8 (B) Survivorship, pairing, divergence, stability — RESOLVED
  changed: Selection rule bullets (diverged = no accuracy number, pre-divergence checkpoint not
    in the mean; survivor bias stated; paired gaps over seeds feasible in both, count stated;
    McNemar exact on feasibility/divergence); Recipe claim "R infeasible" and "both infeasible"
    branches; stability falsifier ≥ 4 more diverged A than D seeds
  propagated: log stub Falsifiers clause
  neighbourhood: [A12] DIVERGED.json skip-on-resume agrees with "never relaunched"
9 (B) EBOPs equivalence with Sun et al. asserted — RESOLVED
  changed: [A14] REPRO-CHANG xfm-n64 ratio check, fallback as quantified limitation in [L2]
  propagated: none needed   neighbourhood: [L2] iso-EBOPs wording
10 (B) Budget branch and pod count — RESOLVED
  changed: Budget "Expected [D15] branch" (83-190 s canary, 190-245 s telemetry → report to Kai
    unless s_e ≤ 172.8 s); cheap version and P = 2 waves as likely alternatives; "Kai decision
    at the canary/launch gate", no pod beyond "a couple of pods" without his answer
  propagated: "Where I am not sure" launch-policy and pod-count blocks; log stub
  remains / route to: Kai, launch-gate decision (pod count), not a design change
11 (B) Per-epoch overhead / checkpoint cadence — RESOLVED
  changed: [A15] (wire experiment.checkpoint_every_epochs, tested with [A5]); [D14] says code
    change; canary rule for overhead > 50 % of s_e
  neighbourhood: candidate save/reload/validate stays every epoch, stated in both places
12 (B) Epoch-matched recipe gap — RESOLVED
  changed: Selection rule "held-out ROC-test" bullet: second pre-registered touch for A and D
    at the as-of-epoch-1,000 snapshot; Recipe claim reports A1000 − R, D1000 − R
  propagated: comparisons-table note, log stub
13 (B) Screen N=64-at-350k history — RESOLVED
  changed: [A16] gate before the canary (earlier pass). This pass: [A16] and "Where I am not
    sure" point to review/STUDY_investigation_350k.md (no screen N=64 arm feasible; lowest
    logged EBOPs 4,630,276, A07-N64, zero-based epoch 46; W&B-logged, seed 1, not verified);
    PVC side still to confirm in PREFLIGHT
  verified: values copied from the investigation file "Answer" section
  propagated: log stub Design line (pointer, "PVC check pending")
  neighbourhood: reference-table row "no verified number exists" left true (W&B-only, unverified)
14 (B) [D1] rationale vacuous — RESOLVED
  changed: [D1] drops "lowest of the plain N=64 arms traced", with the amendment note
  neighbourhood: "Where I am not sure" base-architecture block makes no ranking claim
15 (B) A vs F declared unpaired — RESOLVED
  changed: confound 8, comparisons table row A vs F, conventions Seeds row, [A17] (earlier
    pass). This pass: Seeds section adds the pairing rule (A-D paired by seed, R by seed index,
    A − F paired only if [A17] shows only pos_table differs, else Welch; E Welch)
  propagated: all four places now agree
  neighbourhood: F vs E and A vs E stay Welch (shape differs)
```

C items (no re-review), all present after audit:

```
16 §6.8 binding-baseline sentence — conventions row "Baseline binding at VERIFY"
17 figures pre-registered — Falsifier "Figures" paragraph; figures.md row
18 winner's curse (0.16 pt at 62,000; 0.12 pt at 124,000) and per-run val − held-out gap —
   Selection rule bullet; 90/10 flag block
19 EBOPs-at-selection wording — "Feasibility is the cost outcome" bullet
20 MLP Mixer label — reference-table band row
21 fidelity table (7/7 width init, key_dim 16 vs 12, β0, value-wise, input quantizer) — present
22 Holm family — Falsifier opening paragraph (budget and stability as count rules; Holm over
   the two p-values; reasoning in plan.md)
23 gate-then-standardize — [A3] third bullet
24 AUC-selected sensitivity — Selection rule bullet and [A19]
25 stale inherited fields + config diff — [A18]
26 K=6 memory prior (3,849 / 23,028 MiB; ×10.9) — canary bullet
27 "5M" wording — this pass corrected it again: the investigator found the reason recorded
   (publication/docs/current-work/CONFIRMATION_RUNS_20260924.md:26, post hoc from the screen
   endpoints), so the arbiter's "reason not recorded" was itself superseded
```

Additional instruction (orchestrator): "Downstream use" paragraph after Bearing names
`campaigns/2026-09-26-method-atlas/` as treating this study as its wave 0 anchor (from its
BRIEF.md); the log stub notes it too.

Regression check: `python3 tools/prose_lint.py STUDY.md` → score 0, 0 em-dashes. No mechanical
STUDY validator exists. Design unchanged: 7 arms × 8 seeds = 56 runs, same selection rule,
same falsifiers, no [D] label replaced beyond the arbiter-directed amendments.

## Record / outward copies for Kai

- `.claude/memory/project-context.md` ("Current vs archived") and `.claude/memory/decisions.md:13`
  date the N64 5M target from 2026-09-10; the investigator finds it first on 2026-09-24. Not edited.
- No README, RESEARCH.md §7 row or messages/ draft quotes this campaign (grep checked).

## Kai decisions routed to the canary/launch gate

Arm H and the in-house non-binary arm (follow-ups); pod count beyond "a couple of pods"; the
[D15] branch (expected: report to Kai before launch); the other FLAG FOR HUMAN blocks.
