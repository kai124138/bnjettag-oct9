# STUDY review, constructive, v6: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: constructive-reviewer, fresh context, 2026-09-28. Artifact: `STUDY.md` (1,160 lines, iteration 6,
after fixer v5 and the experiment-designer's median-g re-simulation, commit 31db77d). Read:
`docs/methodology/06-review.md`, `03-phases.md` Phase 1, `review/STUDY_arbiter_v5.md`,
`review/STUDY_fixer_v5.md`, my own `review/STUDY_constructive_v5.md`, `review/STUDY_validators_v6.txt`,
`screen_null.py`, `rank_sim.py`, `.claude/memory/decisions.md` (top three entries), the headings and newest
entries of `experiment-log.md` and `research-log.md`, and
`campaigns/2026-09-26-training-batch/review/INCIDENT_stall_20260928.md` §5-§6. Not read: physics or critical
files of any iteration.

**Freeze context.** Kai (`decisions.md` 2026-09-28): if round 6 finds only new B items, the design is frozen
and launched with them disclosed; any A blocks. I checked each candidate against that bar.

**Verdict in one line.** One Category A, and it does not come from review-added machinery. The STUDY does not
carry the orchestrator's 2026-09-28 decision "Delta must not launch on the leaking anchor bundles". Its
frontmatter names those bundles as the code base, and its launch gates cannot detect the host-memory leak
that stopped the sibling pilot. The fix is text only: a dated amendment, one gate, one readout column and one
Budget sentence. There are two B items. B1 is new in v6: the "descriptive" label text claims "recovery below
0.5", and that is false for the median-g primary in the seed regime the STUDY calls likely. B2: the 5M
rank-move flag cannot fire under median g unless r ≥ 0.95. Three C items.

## Reproduced (evidence)

- `uv run --with numpy,scipy python screen_null.py` (design seed 20260927, nine child seeds; 7 min 51 s wall on
  the laptop, against the 57 s the fixer reports; not a finding). The output is kept at
  `review/constructive_v6_screen_null_out.txt`. Every v6 number the STUDY quotes reproduces:
  - §19a: 5M T by median g 1.2 at all ten seeds; 350k 2.1 / 2.1 / 2.7 / 2.1 / 2.3 / 2.1 / 2.1 / 2.6 / 2.6 /
    2.1, so T = 2.1. Gaussian median-g recovery at T is 0.52 (5M) and 0.56 (350k).
  - §19b rows.
  - §19c: 0.71 / 0.81 / 0.83 at 5M, σ 1.0 (output l. 436).
  - §19d rank-move thresholds: 350k T 6 / 5 / 4 / 3; 5M "no grid T" below r 0.95, and T 12 (0.9) at r ≥ 0.95.
  - §18b: 0.85 / 0.26 / 0.26.
  - §15a: 1.65 / 4.10, 2.50 / 6.25 pt (output l. 397-398).
  - §18d: 0.53 / 0.61.
  ✓
- `uv run --with numpy,scipy python rank_sim.py`: the m = 37 block, median / mean / LCB80, matches the
  fidelity table cell for cell (0.96 / 0.99 / 0.97 ... 0.87 / 0.94 / 0.90). ✓
- Code check (`screen_null.py` l. 127-135, 380-386): the §15 recovery grid, which condition (i) reads, is
  drawn with the replica term (`draw()` subtracts `rep`). So condition (i) is scored in the paired model, and
  that is correct for median g, where the replica term does not cancel. ✓
- §19 adds no random draws. It scores the earlier draws by median (l. 384, 452-454, 464-473, 624-659), so §1-§18
  are unchanged. ✓

## What is done well

- [+] **Every design value moved to the primary statistic without new draws.** §19 re-scores the T rule, the
  extension, the rank-move nulls and the fidelity table by median g on the same draws. The mean-g rows stay
  beside them, so a reader can see what the switch cost (Gaussian 5M 0.77 → 0.66 at σ 1.0) and what it bought
  (per-run q 0.1: 0.28 → 0.85).
- [+] **The 5M threshold is now fully seed-stable** (1.2 at all ten seeds). At 350k the spread (2.1-2.7) is
  printed together with its cause: condition (ii) at q 0.5 sits at 0.45-0.50 recovery across 2.2-2.7 pt. The
  ten-seed minimum is taken, so the conservative end is the one used.
- [+] **The box tells the truth about the median's blind spot.** "The median hides a lever that changes the
  low-mode probability; mean g and n_low read that" (l. 227-228). Both statistics are given at the named q.
- [+] **The family test is kept independent of the ranking statistic** (l. 728-730), so Kai's [DK6]
  re-decision did not reopen its calibration.
- [+] **The confirm cap is back** (l. 698-700), in median-g order, with the Falsifier pointing to it (l. 806).
- [+] **The Question sentence is honest.** "It resolves only multi-pt effects" appears beside the family test
  (l. 241-242), and the box gives the pt values (l. 230-232).

## Category A

### A1. The pre-registered code base is the leaking anchor bundle, which a decision already bars from launch, and no launch gate can detect the leak

- **Current state.**
  - Frontmatter `code_sha` (l. 9) and launch gate 11 (l. 451-453) name the code base as "the anchor's
    regime-B bundle (f2107a04 … or the re-frozen, uncommitted e90327d4) plus the Delta patch series".
  - `.claude/memory/decisions.md`, entry "2026-09-28 (orchestrator, from the training-batch session) — Delta
    must not launch on the leaking anchor bundles", records:
    - host memory grows about 80-95 MB per epoch per arm in the chang0926 runner and trainer;
    - `run_pack.py` relaunches die on stale heartbeat mtimes;
    - Delta's rebased series inherits both;
    - Delta launches only on the fixed regime-B bundle;
    - PREFLIGHT runs the memory-growth canary on Delta cells (fail above 5 MB per epoch);
    - patch 0038 is rebased onto the anchor's run_pack fix.

    Its Check line: "Delta's PREFLIGHT names the regime-B bundle sha and a memory-growth canary result for E
    and A07 cells."
  - `INCIDENT_stall_20260928.md` §5 (l. 131-144) says regime B leaks too. At best, if the leak is the trace
    alone, it reaches ~6.6 GB per arm at epoch 500. "No pilot or production configuration reaches epoch 500
    under the current limits without the leak fixed."
  - `grep -i "leak|memory-growth|relaunch|restore"` on STUDY.md finds none of this.
- **Why the STUDY cannot be left as is.**
  1. A binding design input (the code base) names bundles that the decision log bars from launch. This is
     the same defect class as arbiter v5 #1, a rule decided elsewhere that the STUDY does not carry.
  2. Launch gate 7's canary measures **GPU** memory over **epochs 1-3** (l. 432-437). At 80-95 MB per epoch, a
     host leak has added under 300 MB by epoch 3, so the gate cannot see the failure that stopped the anchor's
     regime-A pilot. "Nothing launches before all of these hold" (l. 407) omits the one check the decision
     names.
  3. Budget (l. 884-886) assumes rule PACK at 6 Gi host memory per arm, while the replicas run to 2,000
     epochs. On the named base, §5 of the incident puts each arm over 6 Gi before epoch 500 (about 48 epochs
     if the leak is the validation reload). The (4, 4) row's 5.4 / 9.2 d is therefore stated on a base that
     cannot finish it. That is a projection resting on an infeasible premise.
  4. **Pairing.** If an arm is killed and restarted by `run_pack.py` (heartbeat kill, then
     `restore_checkpoint` from `latest.json`, written every 25 epochs; incident l. 23-33, 116-125), the cell
     is resumed while its replica may have run continuously. The STUDY assumes "same seed, same init, same
     data order" (Confounds 5, l. 537-538). The placebo reads "pod, pack and identity" and assumes
     uninterrupted runs (l. 749-756, Falsifier (iv)). No readout column records a relaunch, so a restart
     would be invisible in the paired table. That is a missing confound record, not only an operations
     concern.
- **Improved state** (text, no rule reopened):
  - (a) A dated amendment (2026-09-28) to `code_sha` and launch gate 11: "the regime-B bundle **carrying
    the host-memory leak fix and the run_pack heartbeat fix** (decisions.md 2026-09-28), plus the Delta
    series rebased onto it (patch 0038 onto the anchor's run_pack fix); sha fixed at PREFLIGHT. f2107a04 and
    e90327d4 are not launchable unless PREFLIGHT shows the leak fix is in them."
  - (b) Launch gate 14: "memory-growth canary per class (E, A07): host RSS slope over ≥ 30 epochs ≤ 5 MB per
    epoch per arm on Delta cells, measured as the anchor's gate; if it fails, the wave waits."
  - (c) Readout and Confounds 11: a per-run column "relaunched: yes/no, epochs restored from", beside the GPU
    class. A pair in which exactly one side was relaunched is marked. The placebo reading lists relaunches.
  - (d) One Budget sentence: "the (4, 4) wall clock assumes no relaunch and the leak fixed (gate 14)."
- **Grounds 2-4 carry the A on their own.** The frontmatter already defers the choice between the two shas
  to the anchor PREFLIGHT addendum, so ground 1 alone could be read as PREFLIGHT's to settle. Grounds 2-4 are
  design content: the gate list, the Budget premise and the confound record.
- **Why A.** It is missing required validation: the decision names the gate and its threshold. It also
  contradicts a recorded decision on a binding field, and the omission is not review-added machinery. The fix
  was known before this round (the decision predates v6 by hours). The fixer's scope was the arbiter v5 list,
  so it did not fold it in. Under the freeze, this cannot become a disclosed limitation: launching on the
  named base is what the decision forbids.
- **Effort.** Low: four text edits, under an hour. No script changes.

## Category B

### B1. The "descriptive" label claims "recovery below 0.5", which is false for the median-g primary in the regime the STUDY calls likely

- **Current state.** Label (l. 713-720): if s_int > T, the list is "descriptive: recovery below 0.5 at this
  spread". s_int is the non-robust residual sd of the cell × seed matrix, so every low-mode run inflates it.
  The median, now primary, discards those runs. Condition (ii) of the T rule guards against a false "ranked"
  only. Nothing guards against a false "descriptive".
- **Evidence** (§19b, design seed, my run; the same lines as the STUDY's source), per-run two-mode seeds:

  | family, q | share of families labelled descriptive (s_int > T) | median-g recovery in those families |
  | --- | --- | --- |
  | 5M, q 0.05 | 10,125 / 20,000 = 51 % | 0.95 |
  | 5M, q 0.10 | 19,705 / 20,000 = 99 % | 0.85 |
  | 350k, q 0.10 | 1,528 / 20,000 = 8 % | 0.89 |
  | 350k, q 0.33 | 19,124 / 20,000 = 96 % | 0.61 |
  | 350k, q 0.50 | 19,887 / 20,000 = 99 % | 0.54 |

  The box (l. 221-229) describes a per-run low mode with small q as a live possibility. In that case the 5M
  list is almost always labelled "recovery below 0.5" while its primary recovers 0.85-0.95. At 5M the
  mean-g statement was true under v5 (mean-g recovery above T at q 0.1 is 0.28, §18 output l. 364). At 350k it
  was already marginal (0.52 above the mean-g T 1.8 at q 0.1, l. 371). The v6 switch made it false and
  left the text unchanged.
- **Improved state** (text only, adds no rule): "descriptive: s_int above T; median-g recovery below 0.5 under
  Gaussian seeds at this spread (§19a). Under a per-run low mode it can be higher (§19b, rows for s_int > T);
  the mode readout and n_low say which case applies." This is a cross-reference; no rule reads the mode flag.
  Print the §19b above-T rows beside the label in the family header. The better fix is a robust s_int
  (median-polish residuals, MAD-scaled) with T re-derived. That is a design change, so it goes under
  ALTERNATIVES or into the follow-up, with medium effort.
- **Why B, not A.** The error runs conservative (under-claiming), which is the arbiter v5 row-5 precedent. But
  under the freeze, "disclosed as a known limitation" cannot mean leaving a false sentence in a pre-registered
  label that VERIFY will print. The wording change is the disclosure.
- **Effort.** Low: one sentence in Label, one in [DK8].

### B2. At 5M the rank-move flag, the main winner's-curse check, is inoperative unless r ≥ 0.95, and the fallback label misdescribes that

- **Current state.** [L6] (l. 978-981) names the companions, the eligible-epoch count and the rank-move flag
  as the check for eleven cells whose checkpoint count or fluctuation differs from the replica's. l. 761-768
  and §19d: at 5M, median-g ranks give a grid T only at r ≥ 0.95 (T 12, null
  0.9). At r 0.9 the smallest null count is 1.2 (T 15). Below 0.95 the family goes to Kai labelled "companion
  disagrees at the null level". No data give the expected r between best-of-51 and last-epoch accuracy
  (centred per cell). The STUDY discloses the "no grid T" rows, so the arbiter may read this as a C. It is a B
  because [L6] relies on the flag, and nothing states that at 5M the flag is probably inactive.
- **Improved state.**
  - Rename the fallback "rank-move flag not calibrated at this r (§19d)". That describes what happened and
    does not assert disagreement.
  - State in [L6] that at 5M the flag operates only at r ≥ 0.95, and that below that the eligible-epoch count
    and the split-half companion are the check.
  - Optionally, have PREFLIGHT estimate r from the replica seeds 5-8 per-epoch logs once they reach epoch 500.
    This gives no extra run and no decision; it only says in advance which branch applies.
- **Why.** A reader of the 5M header should not take the absence of flags as absence of winner's-curse
  movement.
- **Effort.** Low.

## Category C

- **C1. 350k chance baseline missing.** One +1-pt cell in the top 3 of 11 is chance 3/11 = 0.27. "Ranked" at
  350k means median-g recovery ≥ 0.5, which is 0.56 at T = 2.1, about twice chance. The 5M chance (0.028) is
  stated at l. 595. Add the 350k chance at l. 606 and in the Label.
- **C2. The forest plot does not name its marker** (`figures.md` row, l. 926). The list is ordered by median
  g, but the interval belongs to mean g on s_pool. Specify the marker (median g), the interval (mean g, s_pool,
  "95 % at equal spread"), and the per-seed points. Then a reader does not see non-monotone bars and infer an
  error.
- **C3. The family test and the ranking can disagree in the other direction too.** The STUDY notes that "a
  cell can sit above the placebo with a negative g" (l. 735). The reverse case is systematic under the named
  seed model and is not stated: a top median-g cell whose own-sd t on mean d is pulled under the critical value
  by one low-mode run. Add one clause.

## Checklist (06-review §6.3)

1. Conventions: every row present (l. 911-927); the declared deviations are justified. With A1 fixed, yes.
2. Reference table: present, sourced, no comparand (l. 265-280). Yes.
3. What a competing group would have: a code base with a verified memory-growth gate (A1) and a spread
   statistic matched to the ranking statistic (B1).
4. Uncertainties in both directions: the family test is called powerless with its pt values; B1 is an
   under-claim in the label.
5. Limitations attempted: yes (companions, g_rep, extension, [L1] zero-GPU checks).
6. Context: not applicable at STUDY (no result).

## Disputed facts

None. A1 rests on `decisions.md` (2026-09-28 entry), `INCIDENT_stall_20260928.md` §5 l. 131-144, and STUDY
l. 9, 407, 432-437, 451-453 and 884-886. Whether f2107a04 / e90327d4 already contain a leak fix is not asserted
anywhere I found. The incident says the source "is not yet measured". If the ml-engineer shows a fixed sha
exists, A1's (a) becomes naming it.
