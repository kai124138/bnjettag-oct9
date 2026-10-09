# STUDY physics review v1: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: physics-reviewer (fresh context). Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md`
(647 lines), with `budget.py`, `plan.md` and the files it cites (`../2026-09-26-delta/delta.json`,
`../2026-09-26-delta/screen_power.py`, anchor `PREFLIGHT.md` l. 490-528). No compiled PDF exists
beside the artifact.

## Figures

| figure | status |
| --- | --- |
| (none shown or cited at STUDY) | Not applicable. There are no results yet. |
| Planned: forest plots of paired g per family (STUDY l. 515) | Plan accepted with conditions. Each plot needs n (seeds) per row, the per-seed points, the GPU-class column, "validation, n = 62,000, screen, not quotable" in the caption, and a null/placebo row (see A1) so a reader can see where the null gaps fall. |

## Verified (recomputed)

- `delta.json` sha256 = f4ad2571...8029204 (`shasum -a 256`). This matches STUDY l. 9.
- `python3 budget.py` reproduces the whole Budget table: 286 / 338 / 390 / 570 runs; 168,000 /
  196,000 / 224,000 / 332,000 run-epochs; 1,695.6 / 3,007.6 pod-hours at (4,4) for r = 1 / 2; 8.8 / 15.1 d;
  and the cheap version at 123 runs, 70,500 run-epochs, 711.5 / 1,211.1 pod-hours. This shows the
  table is internally consistent and nothing more. The 218 s/epoch E basis comes from 3 epochs of a
  mixed pack, and r for A07 is unmeasured. The STUDY states both.
- Cell counts: 68 cells (23 at 350k, 1 at 1.4M, 44 at 5M), 16 in the E class and 52 in the A07 class
  (`budget.py` output). m = 19 = 12 accuracy + 7 floor family. m = 43 = 40 G3 cells + 3 teacher cells
  excluded. The counts are consistent.
- Threshold (c): from the class counts [12479, 11882, 12499, 12579, 12561], n = 62,000,
  p_maj = 0.202887, SE = 0.0016151, c = 0.210962. These match anchor `PREFLIGHT.md`
  `NONDEGENERATE_THRESHOLD`, which is an independent record, so the check is not circular.
- Seed-rule arithmetic: 0.3 / (k_joint · √2) = 0.058 / 0.101 / 0.134 pt for k = 3.66 / 2.09 / 1.58.
  t(0.975, 3)/√4 = 1.591, giving half-widths ±0.48 pt (sd_d 0.3) and ±1.35 pt (sd_d 0.85).
  g_res(8) at 0.6 pt = 1.34 pt. I reran `screen_power.py` and got k_joint 4.83 / 2.50 / 1.83 (5M)
  and 3.66 / 2.09 / 1.58 (350k), the same as the STUDY.

## Findings

### (A) Must resolve

**A1. The ranking-mode "no" answer of the wave is close to unreachable, so the falsifier does not test anything.**
Attack: the STUDY sets the wave's "no" in ranking mode (l. 32-34, l. 409-412) as "no cell's lower 80 %
bound on g exceeds 0 in either family". It also expects ranking mode (l. 344). Under a pure null each
cell's one-sided 80 % lower bound exceeds 0 with probability 0.20. Evidence: I simulated the design
as written, with n = 4 seeds and every cell paired against the same replica seeds (the shared replica
correlates all gaps in a family), taking the null as N(0,1) per run. Results:
- 5M family (43 cells): 8.7 cells are expected above 0, P(none) = 0.16, P(≥ 3) = 0.67.
- 350k family (19 cells): 3.8 cells are expected above 0, P(none) = 0.27.
- P(no cell in either family) ≈ 0.04.

So even if no entry does anything, the wave reports a non-empty "ranked" list about 96 % of the time.
The top of that list goes to Kai at K3a, where it can steer confirm slots. The shared replica makes it
worse: one unlucky replica seed moves all 43 gaps together. What would settle it:
1. A calibrated null inside the wave. Either run a placebo cell (the replica config again, same
   seeds, different pack/pod, or a no-op key) in each family, or state the null count explicitly
   ("≈ 0.2 · m cells above 0 expected under the null").
2. A pre-registered ranking-mode criterion that is an excess over that null, for example "more cells
   above 0 than the 95th percentile of the null count", or a placebo rank line that a nominee must beat.
3. If neither is adopted, drop the claim that ranking mode has a "no" answer.

**A2. Selection and evaluation happen on the same 62,000 jets, and the winner's-curse bias does not cancel in the pair.**
Attack: each run's number is the maximum validation accuracy over up to H feasible checkpoints, read on
the same validation set (l. 358-363). [L6] (l. 578-579) says "both arms of a pair share it". That is
only true if the two arms have the same number of eligible checkpoints and the same epoch-to-epoch
fluctuation. Several entries change exactly those:
- M028 and M029 (peak LR) and M032 (no restarts) change the fluctuation amplitude.
- M034 (latent EMA) smooths the evaluated weights by design.
- M020 (Bop) changes the flip dynamics.
- M008 and M013 (EBOPs controller) and M011 and M012 (activation widths) change which epochs are
  feasible.

A single checkpoint's sampling SE is 0.16 pt (l. 56, verified 0.164 pt). The expected maximum over
tens to hundreds of partly independent late-cycle checkpoints is of order 1-2.5 SE, so a differential
bias of a few tenths of a point is plausible. That is the size of g0 = 0.3 pt, and it points in a
direction set by the manipulated variable: noisier training scores higher. No figure or number in the
artifact bounds it. What would settle it, at zero GPU cost:
- Fix a permutation of the 62,000 validation jets into a select half and a read half (31,000 each),
  select on the first half and read g on the second. Or read the fixed end-of-cycle checkpoint at
  epoch H beside best-as-of-H.
- Pre-register which one is primary.
- Report the per-run count of eligible checkpoints beside every gap.

### (B) Should address

**B1. The resolving power is stated at assumed sds, not at the only measured one, and there is no stop line.**
The only seed sd in the Reference table is 3.14 pt (l. 55; archived, held-out, 3 seeds, sizing only).
"What n = 4 resolves" (l. 349-353) uses 0.3 and 0.85 pt. At sd_d = √2 · 3.14 = 4.44 pt the n = 4
half-width is ±7.1 pt (computed), and `screen_power.py` itself prints g_res(8) = 8.12 pt for that sd.
The STUDY omits that line. Pairing only helps if seed correlation across packs is high, and the STUDY
does not assume bit-identity across packs (l. 310-312). No argument is given that the paired sd will
be about 10× below the archived unpaired one. The replica guard (l. 341-342) can only switch the mode
and never pauses a family. That leaves open 1,700-3,000 pod-hours spent ranking gaps well inside the
noise. Settle:
- State the resolving power at 3.14 pt.
- Pre-register an sd_rep ceiling (from the rep-A / rep-C epoch-500 read that runs first anyway).
  Above it, n = 4 cannot rank gaps of the size the Delta entries predict, and the family pauses and
  goes to Kai instead of launching.

**B2. The floor-family feasibility (G2) is partly decided by construction.**
Entries such as M001, M002, M004, M005, M006 and M009 change the architecture. If their Z01 static
floor falls well below 350,000, "reaches 350k" follows mostly from the trace before any training.
Checks (b) and (c) are thin guards (floor > 0 headroom; accuracy above 21 %). Settle: report the
traced headroom (350,000 − own floor) beside k_e and k_base, and state that a rescue with large static
headroom is a structural fact, not a training effect.

**B3. Floor-family accuracy against A measures a package but sits in the advance family.**
These cells are Welch, cross-architecture (A07-derived + entry vs E; l. 93-101, 313-315). They count in
m = 19 and are eligible to advance, but their gap is the architecture swap plus the entry, not the
entry. In addition, `screen_power.py` sizes every cell with the paired SE (1/√n). A Welch cell has
roughly √2 larger SE and df ≈ 2(n−1), so the 350k k_joint row overstates the power for 7 of 19 cells.
Settle: take the floor-family accuracy out of the advance decision (report it descriptively as a
labelled package), or size it with its own SE.

**B4. The baseline asymmetry bears directly on the thesis.**
The binary model gets 46 single levers screened and the winners go to confirm. M047-M050 (ternary,
int8, HGQ, int8 input_proj) run once at the binary recipe for 500 epochs, untuned (l. 138-141, 386).
At confirm the thesis comparison (binary vs non-binary at iso-EBOPs) would then set a tuned binary
model against baselines tuned less hard. That favours binary. Settle: state in "Bearing on the thesis"
that confirm either gives the matched non-binary arm the same recipe-level winners (the training-only
levers M028-M034 apply to any weight scheme) or labels the gap "binary tuned, baseline not".

**B5. Per-class AUC is promised but not in the readout.**
The Conventions table (l. 505, 508 item 5) promises per-class AUCs per cell with any class under 0.7
called out. The "Readout per cell" list (l. 391-394) has macro AUC only. Add per-class validation AUC
(5 classes) to the readout, so that a collapse of one class in a binary cell cannot hide behind the
accuracy or macro number.

### (C) Suggestions

- **C1. The bases are not yet trainable.** 52 of 68 cells run on A07-class architectures. No [D19] A07
  epoch has completed anywhere (A07-350-s1 OOM ×3, C′-s1 OOM ×2; l. 449-451). Launch gate 7 tests
  memory, not non-degenerate training, and a batch change is forbidden (l. 616-617). State the fallback
  if K = 3 on a 23-GB card still OOMs, for example "≥ 45 GB products only, else the 5M family pauses".
- **C2. Ranking statistic.** With df = 3, ranking by each cell's own lower 80 % bound rewards cells
  with a small s by chance. Report a second ranking that uses a family-pooled sd_d (from the replica
  pairs or pooled residuals) and state which one is primary.
- **C3. Branch S with a df = 1 sd.** It is already flagged (l. 597-601). The replica guard makes it
  safe in the conservative direction, so the upper-bound alternative is not needed. Note that.
- **C4. The anchor-primary branch is almost empty.** The STUDY expects every family to be
  replica-primary (l. 254-257). Consider fixing replica-primary now (the "always replica-primary"
  alternative at l. 591). This removes one read-time branch and one decision that depends on the
  results.

## Verdict

I would not approve this for launch as written, so the verdict is ITERATE. What decides it most is A1:
in its expected mode the design reports a "ranked" list with about 96 % probability even if no entry
does anything, so it needs an in-wave null (a placebo cell or a stated null count) before 286 runs
are spent. A2 costs no GPU and should be fixed in the same revision.
