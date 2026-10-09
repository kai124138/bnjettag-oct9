# STUDY constructive review v10: 2026-09-26-training-batch

Constructive reviewer, fresh context, 2026-09-28. Iteration 10 (ESCALATE tier), scoped to landing
per `review/STUDY_arbiter_v9.md`. Artifact `STUDY.md` at HEAD (2,658 lines); diff read:
`git diff 2e0cac0 HEAD -- STUDY.md` (commits 96b95f2, 9884773, 11764b4, cc36f7c, 22e8692).
Also read: arbiter v9 (fixes 1-5, scope), `plan.md` 'ml-engineer, regime B' (a)-(e) and DECISION
R-B1/R-B2, `PREFLIGHT.md` 'Regime B addendum' (l. 1128-1300), `RUN.md` canary tables
(l. 156-335), `code/tree/bnhgq2/ablation.py` at 42abed4b (l. 483-495, 780-792, 858-906),
`code/tree/campaigns/chang0926/{packs.json,packs_meta.json}`, a production config
(`chang0926-a-n64-s1.json`, `train.ebops.pid`), hgq2 0.1.9 `hgq/utils/sugar/beta_pid.py`
(uv cache copy), `code/evidence/leak_probe_42abed4b_B_115ep.log`,
`logs/pilot-77f1ca-20260928T0531Z-prestop.log`, `docs/methodology/06-review.md` §6.5, and the
newest research-log entries (no published work bears on trace cadence or the PID input under a
budget; nothing to cite).

## Landing verdict

**No landing defect.** Arbiter v9 fixes 1(a)-(i), 2, 3 and 4(a)-(b) are in at every listed site,
and the fixer also covered neighbourhood sites (H paragraph and fidelity row, [D23], [A21], [A23],
Kai rows, DECISION blocks). Slots T, C and P are filled with patch-0027 behaviour and cited to
file and line. I checked the citations against the tree at 42abed4b: `is_traced_epoch`
(`ablation.py:483-489`: `epoch == 0 or (epoch + 1) % k == 0 or last`), `model_ebops` (`:492-495`),
the in-training read before the trace (`:783`), and the split PID assertions (`:861-866` traced,
`:867-871` untraced). Each of the three dated amendments has a change-log entry naming its sources,
its line numbers and "no change to any arm, seed, target, ... Holm member". Remaining
"per-epoch" wordings (l. 943, 2282, 2286) carry a regime-B qualifier in the same or the next
sentence, so they are not defects.

The three B below are **content arising from the amendments**, not landing defects. Under the
v10 scope they go to Kai (B1, B3) or are one-clause text fixes (B2). None blocks the regime-B
pilot pods, which are Pending on A10 capacity.

## Done well

- [+] Slot T/C/P citations were verified against code, not taken from `plan.md`. The epoch-0
  correction (700 → 701 traces, 100 → 101 for R, and the canary pair changed to traced epoch 1
  against epoch 10) was caught after the freeze and carried to every dependent site: the canary
  bullet, the arm-C denominator (51 / 701) and a bracketed note in the v9 entry.
- [+] Slot P states the uncomfortable part plainly: "between traces the controller holds the
  in-training EBOPs, not the traced value, at target." That is the sentence a competing group
  would demand. B1 builds on it.
- [+] The regime-A pod's stop is recorded honestly: checkpoints at 125/150/75/25 and **no
  epoch-500 snapshot**. The regime comparison is made conditional on a resume, not dropped
  without a word and not quietly passed.
- [+] "Neither is a measurement" on the 11.1 d / 9 d arithmetic, and the 14-day rule binds on the
  regime-B canary's measured s_e over whole trace cycles (zero-based epochs 10-29). The s_e
  redefinition (mean, not median, so the trace epoch is included) closes arbiter v9 (iii).
- [+] Host-memory gates have before/after numbers (PREFLIGHT l. 1167-1168: slope 3.237 → 0.004
  MB/epoch on CPU). The operational rule now projects to process epoch 105, not 7,000, and says
  why (PREFLIGHT critical v3 A2). The text says "CPU-tested, none yet proven on a GPU."
- [+] Arm-C constraint-active readout: pre-registered before any arm-C data exist, states its
  source, and is descriptive only. N = 10 is labelled a designer choice, and C′ gets the same
  three quantities with "expected to bind; reported, not assumed". This is the right way to add
  a readout late.
- [+] Arbiter v9 C2 fix (≤ 0.86 pt, 1.0 / 1.16) is in and tightens the wording in the direction
  that goes against the thesis.

## Category A

None.

## Category B (content-level; from the amendments' own content)

### B1. The 9:1 mixed PID input gives each arm its own effective traced target, and the STUDY does not say so or register what happens

- **Current state.** Slot P (l. 1483-1494, copied at l. 2053-2065) says the PID reads in-training
  EBOPs on 9 of 10 epochs and traced EBOPs on the tenth, and that the pilot readout "reports their
  ratio per run". It does not state what that does to the quantity selection tests. The pilot
  A rule's Kai options (l. 1611-1615: re-target, one-head/Linformer primary, stop) predate regime
  B. `plan.md` DECISION R-B1 (l. 890-893) says "No measurement of the in-training / traced ratio
  exists yet ... the regime-A canary pull did not fetch it."
- **Why it matters (arithmetic from code, not a measurement).** hgq2 0.1.9 `PID.__call__` does
  `integral += err` with no anti-windup. In log mode β = 10^(p·err + i·Σerr) with
  err = log10(EBOPs/target). The production config uses p 1.0, i 0.05, d 0
  (`chang0926-a-n64-s1.json`, `train.ebops.pid`). The integral is stationary only when the
  cycle-mean err is 0. With a roughly constant ratio r = traced / in-training, that gives
  0.9·log10(in/T) + 0.1·log10(tr/T) = 0, so traced EBOPs settle near **T · r^0.9**.
  - r > 1 (in-training `i` decays toward the batch max, up to 0.2 bits per epoch at 1e-3 × 200
    steps, [D25] l. 2115-2116, so up to about 1.8 bits over nine untraced epochs): traced epochs
    sit above target, and feasibility at 350k comes only from fluctuations. That means fewer
    feasible candidates, lower k, and selection on noise.
  - r < 1 (in-training `i` rising as activations grow; the CPU leak probe, a diverged toy at
    β = 1e-3, shows in-training above traced by about 1-2 %, `leak_probe_42abed4b_B_115ep.log`
    epochs 109-115): traced EBOPs sit below target, the budget goes partly unused, and the
    result is biased against the thesis.
  - r that differs by arm (E vs A07, binary vs NB's learned widths): confound 10's "same rule in
    every arm" holds for the rule but not for the effective traced target. A − NB, A − D and the
    E/A07 ladders then compare arms at different effective budgets.
  This is the case arbiter v9 anticipated ("traced-epoch feasibility can then fall"). The text
  names the mechanism but not the consequence.
- **Improved state.** (i) One sentence in the core paragraph after "(3)": "At a constant ratio
  r = traced / in-training, the integral term settles traced EBOPs near T · r^0.9 (arithmetic,
  hgq2 0.1.9 `PID.__call__`, p 1, i 0.05); the pilot measures r." (ii) The epoch-500 readout
  prints, per run, the median over traced epochs 100-500 of log10(r) and the implied traced
  offset 0.9·log10(r), beside the headroom-in-use fraction it already reports. (iii) The A rule's
  Kai packet adds one option: the R-B1 alternative (feed the PID the last traced value on
  untraced epochs, or scale the target by the measured r), labelled a code change and a new
  bundle.
- **Zero-GPU action (RUN, before the pilot-b epoch-500 readout).** Pull `ebops`, `ebops_in_training`
  and `ebops_in_training_over_traced` from the regime-A W&B history (project
  `BNJetTag-ChangRecipe`, canary group; A-s1, A-s2, D-s1 to epochs 125-150, E1-s1 to 75, C′-s1 to
  25). The runner logs the ratio on every traced epoch (`ablation.py:894-895`), which is every
  epoch under regime A. Caveat: regime A measures one epoch of drift, and regime B has up to
  nine, so this bounds r from the conservative side. It is telemetry, not a result.
- **Category and route.** B, content-level: it can change a production action (the A rule's
  fail branch) and every between-arm claim at iso-EBOPs. It goes to Kai only if the measured r
  moves traced EBOPs by more than an arm's noise. It blocks nothing now. **Effort:** low (text)
  plus low (W&B pull).

### B2. The arm-C "constraint slack" label can attach to a run whose traced EBOPs exceed 5M in the labelling window

- **Current state.** l. 1671-1679: a run is "constraint slack" iff β sits at its lower bound 1e-10
  on each of the last 10 traced epochs. (i) and (ii) "decide nothing". At k ≥ 5 of 8 the arm is
  labelled "5M does not bind under [D19]".
- **Why.** With no anti-windup (`PID.__call__` integrates, `BetaPID.on_epoch_begin` clamps
  afterwards), a C run that sits below 5M for a long stretch builds a large negative integral.
  Example: at err ≈ −0.4 over 6,000 epochs, i·Σerr ≈ −120 decades. β then stays at the floor
  even if widths regrow at β = 1e-10 and traced EBOPs cross 5M, because the P term (+log10 of the
  overshoot) cannot offset the integral. (iii) then holds while the constraint is being violated,
  and the label says "does not bind" about a run whose late epochs are infeasible. The label
  describes a saturated controller, not a slack constraint.
- **Improved state.** One clause: "constraint slack" iff (iii) holds **and** no traced epoch in
  the same last-10 window exceeds 5,000,000. If (iii) holds and m > 0 of them exceed it, label
  the run "β at floor (integral wound up), 5M exceeded on m of 10". (i) is already computed, so
  no code change. The same applies to C′.
- **Category.** B: it changes a claim label that VERIFY would print. Not blocking; it must land
  before any arm-C label is written. **Effort:** low.

### B3. The regime-B timing arithmetic covers only the E arms; by the same arithmetic the A07 pods (16 of 56 runs) sit over the 14-day bound

- **Current state.** l. 1508-1512: "s_e ≈ 136.5 s and T_run ≈ 11.1 d at K=6" is computed from
  the A/D split (RUN.md: trace 90.61 s, remainder 127.45 s). The only A07-architecture timing,
  C′-s1 at 293.6 s (23.8 d), is quoted (l. 1442-1443) but never carried into the regime-B
  arithmetic. Production packs 4 A07 pods (C, A07-350) at K=4 (`packs_meta.json`), while the
  pilot times A07-350 at K=3. The rule says "the 14-day rule now binds on the regime-B canary"
  without saying which pod's s_e.
- **Arithmetic (telemetry, not a result).** RUN.md l. 318-324, C′-s1 epochs 0-4: mean
  train-step + validation 163.3 s, mean trace 130.4 s. Regime B: 163.3 + 130.4 / 10 ≈ 176.3 s,
  so T_run ≈ 7,000 × 176.3 s ≈ **14.3 d**, above the bound of 172.8 s. Caveats, all of them
  real: five epochs including epoch 0; C′ is SAT, not [D19] WRAP; K=6 under contention with five
  other arms; A07-350 has no timing at all (OOM). At K=3 or K=4 it may well fit. The point is
  that nobody knows, and the text's only number (11.1 d) reads as "regime B fits".
- **Improved state.** (i) Print the A07 arithmetic beside the E arithmetic, labelled a
  projection with the caveats above. (ii) State that the wave's T_run is the slowest pod
  group's ("a pack's wall time is set by its slowest process", l. 1882, applied to wave 1).
  E pods are judged on the K=5 pod's s_e; A07 pods on the K=3 pod's s_e, with the K=3 → K=4
  difference stated (measured at K=3; production at K=4 is either re-timed on its first 30
  epochs under the same rule or packed at K=3). (iii) Name the branch "E pods pass, A07 pods
  exceed 14 d": A07 pods at K=3 or K=2 on more pods, or Kai.
- **Category.** B: it changes a number the text leads with and a production action for 4 of
  13 pods. It does not block the pilot; the A07 pods already wait for the K=3 readout
  (`packs_meta.json` `wait_for_k3_readout`). **Effort:** low.

## Category C

- **C1. Matched-epoch regime comparison, recoverable now.** The epoch-500 A-vs-B comparison is
  lost unless regime A is resumed. A-s1, A-s2 and D-s1 have regime-A W&B history to epochs
  125-150, and pilot-b will have traced epochs 10, 20, ..., 120 at the same seeds. Tabulate
  traced EBOPs, β and feasibility at matched traced epochs, descriptively. It costs nothing, it is
  the direct test of B1's r effect on the traced series, and it replaces most of the lost
  comparison. Effort: low.
- **C2. Pods paragraph says "Wave 1 runs at K=5 ... about 13 pods"** (l. 1514). `packs_meta.json`
  has 4 pods at K=5 and 9 at K=4 (A07 pods and R). Write "K=5 for the E arms, K=4 for the A07
  pairs and R (13 pods)". Effort: low.
- **C3. β sampling in the arm-C rule.** β logged at the end of a traced epoch was set at that
  epoch's `on_epoch_begin` from the previous epoch's `_ebops`, which is an in-training value
  under regime B (`beta_pid.py` `on_epoch_begin` / `on_epoch_end`). This does not matter for C
  (far from 5M), but `plan.md` l. 1024-1026 already says "report β on traced rows only, or say
  which rows". Add "(β set from the preceding epoch's in-training EBOPs)" so a reader does not
  assume β reacts to the traced value. Effort: low.
- **C4. Consolidation.** The change log is now about 90 lines of site lists at l. 298-386. The
  per-site line numbers go stale with every amendment, and the file is 2,658 lines. Per the
  review-loop convergence note, consider moving site lists to the commit messages and keeping
  one line per amendment. Presentation only. Effort: low.

## Disputed facts for the investigator

- **In-training / traced EBOPs ratio under regime A.** Question: what are the per-arm median
  and trend of `ebops_in_training_over_traced` over epochs 1-125 (A-s1, A-s2), 1-150 (D-s1),
  1-75 (E1-s1) and 1-25 (C′-s1)? Paths: W&B `BNJetTag-ChangRecipe`, regime-A canary group
  (`RUN.md`, 'Canary — W&B history pull', which fetched other keys); key written at
  `code/tree/bnhgq2/ablation.py:894-895` (same key at 77f1ca4e, per `plan.md` l. 892-893).
  Feeds B1. Not disputed in fact; it is simply unread.

## Recommendation

PASS on landing: no landing defect. B1-B3 are content-level B that arise from the amendments'
own content (arbiter v9 scope), so they go to Kai as ESCALATE with the questions below.
- **B1 (Kai):** do you accept the 9:1 PID input knowing traced EBOPs settle near T · r^0.9, with
  the R-B1 alternative (PID fed the last traced value, or target scaled by r) registered as an
  epoch-500 option? Or should the PID input switch before production?
- **B2 (Kai, or arbiter as a text fix):** accept the tightened label, "constraint slack" iff
  (iii) holds and no traced epoch in the same last-10 window exceeds 5M?
- **B3 (Kai):** accept that the A07 pods are timed at K=3 and packed at K=4, and name the branch
  for the case where only the A07 pods exceed 14 d (K=3 or K=2 on more pods, or stop the A07
  arms)?

Nothing here needs Kai's answer before the regime-B pilot pods are applied. The B text
pre-registers branches that the epoch-500 packet will carry. The fixer writes B1 (i)-(iii), B2
and B3 (i)-(iii) once Kai answers. RUN does the zero-GPU W&B pull (B1, disputed fact above)
before the pilot-b epoch-500 readout.
