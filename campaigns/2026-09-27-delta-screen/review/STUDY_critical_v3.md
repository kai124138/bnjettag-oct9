# STUDY critical review v3: 2026-09-27-delta-screen (Delta wave 2)

Critical reviewer, fresh context, 2026-09-27. Panel mode, re-review, iteration n = 3. No verdict
(the arbiter issues it).
Artifact: `STUDY.md` (1,369 lines, committed in f00fd93), with `plan.md`, `budget.py`,
`screen_null.py`, `rank_sim.py`. Also read: `review/STUDY_validators_v3.txt`,
`review/STUDY_arbiter_v2.md`, `review/STUDY_fixer_v2.md`, `review/STUDY_critical_v2.md` (for the
names of my own v2 findings), and `.claude/memory/decisions.md` (top entries: Kai 2026-09-27 on the
launch gate and [DK6]; ml-engineer on regime B and the generator). Also: anchor STUDY at 96b95f2,
l. 1393-1470 and 1480-1556; the anchor working tree `code/tree/bnhgq2/{ablation,monolith,wandb_util}.py`;
`campaigns/2026-09-26-delta/code/{README.md,GATES.md §6}`; the generated `configs/W2/*.json`; the
experiment-log stub (`.claude/memory/experiment-log.md` l. 11-16); and the research log head.

## Validator output (verbatim)

```
STUDY validators v3 (2026-09-27 16:08)
No mechanical STUDY validator exists; prose_lint on STUDY.md:

Desktop/bnjettag/campaigns/2026-09-27-delta-screen/STUDY.md  —  score 0, reads human
  19939 words · 476 sentences · mean 26 words (σ=20.8) · 13% bullets · 13 em-dashes
```

No line is A-marked, so the validator rule makes nothing Category A. The STUDY has no figures, so
there is no plot-validator or `plot_check.py` output.

## Recomputed (show-your-work)

All of this is design arithmetic. Nothing here is quotable.

- **`screen_null.py`** (`uv run --with numpy,scipy`, 6 s, seed 20260927). Every quoted value
  reproduces to the digit:
  - §4 R2 own-sd critical values: 4.406 (m 12) and 6.751 (m 40) at n 4 (STUDY l. 755-756: 4.41 / 6.75);
    6.948 / 12.984 at n 3 (l. 756: 6.95 / 12.98).
  - Bit-identical branch: 4.426 / 6.791 (l. 778: 4.43 / 6.79); false "yes" 0.103 / 0.096 without an
    offset and 0.261 / 0.258 at 0.707 SE (l. 780-781).
  - R2 rows at n 4, m 12 / 40: equal spread 0.102 / 0.099; one cell 3× 0.105 / 0.102; 25 % at 2×
    0.107 / 0.105; 25 % at 3× 0.111 / 0.108; two-mode 0.053 / 0.038 / 0.042 and 0.050 / 0.089 / 0.062;
    offset 0.103-0.104 / 0.099-0.100; near-deterministic 0.098 / 0.098. All match l. 767-771.
  - n 3 rows: two-mode R2 0.067 / 0.122 / 0.111 (m 12) and 0.080 / 0.237 / 0.136 (m 40). These match
    l. 773 "0.067-0.122 / 0.080-0.237".
  - §5 power: R2 0.204 / 0.046 / 0.022 (m 12) and 0.074 / 0.015 / 0.007 (m 40); R1 0.507 / 0.104 / 0.040
    and 0.378 / 0.055 / 0.019. All match l. 765-766.
  - §6 multipliers: 2.179 / 2.146 (l. 748: 2.18 / 2.15), with nominal coverage 0.934 / 0.932.
  - §7 G3′ two-sided: 0.074 / 0.041 / 0.031; one-sided: 0.137 / 0.080 / 0.062 (l. 721-722).
  - §8: m 12 at T 3 / 5 / 6 for r 0.9 / 0.7 / 0.5 gives 0.9 / 0.9 / 1.0; m 40 gives T 10 at
    r 0.95 = 1.0 and T 15 at r 0.9 = 0.5 (l. 810-812).
  - §10: 0.041 / 0.201, 0.371 / 0.110 (1 − 0.629 / 1 − 0.890), and 0.065 / 0.223, 0.417 / 0.165
    (l. 617-620).
  - §11: 2.923 / 3.622. §12: 0.050; 1.25 / 1.85, 3.05 / 4.55, 6.55 / 9.55 pt. §13: 4.284 / 6.585.
- **`budget.py`**:
  - (4, 4): 302 runs (272 cell, 8 placebo, 20 replica, 2 teacher); 176,000 run-epochs (E 42,000,
    A07 134,000); 1,112.2 / 1,959.0 pod-hours; gate 12.6 / 19.0 h; 5.4 / 9.2 d; 318 certification
    readouts.
  - Rows (6, 4) through (8, 8) match the Budget table (l. 914-922, 953-961).
  - Cheap version: 129 runs, 79,500 run-epochs, 502.4 / 853.1 pod-hours, 2.8 / 4.5 d.
  - "Not packable" row: 268 runs, 156,000 run-epochs, 985.8 / 1,744.2 pod-hours, 4.9 / 8.4 d.
  - E K = 5 alternative: gate 15.8 h, wall clock 5.4 / 9.2 d.
  - Hand checks:
    - 14,000·4 + 27,000·4 + 12,000 = 176,000.
    - 176,000 × 22.75 / 3,600 = 1,112.2.
    - 500 × 91.0 s = 12.64 h; 500 × 136.5 s = 18.96 h.
    - 127.45 + 90.61 / 10 = 136.51.
    - Certification: 272 + 8 + 2 + (rep-A 8 + 4) + rep-A07 4 + (rep-C 16 + 4) = 318.
    - floor(0.9 × 23,028 / 4,354) = 4; 5 × 4,354 = 21,770 MiB = 94.5 %.
- **`rank_sim.py`**: output unchanged and identical to `review/rank_sim.py` (diff empty). It matches the
  fidelity table at l. 649-653 (for example σ 3.14 at +3 pt and ρ 0: mean 0.68, LCB 0.60).
- **Generated configs** (`campaigns/2026-09-26-delta/code/configs/W2`): 312 files = 272 cells +
  12 deferred teacher cells (M027, M035, M036 × 4) + 8 placebos + 20 replicas. By target: 350k 26
  (23 cells + P-350 + rep-A + rep-A07-350), 5M 49, 1.4M 1. Replica `train.epochs`: rep-A seeds 1-8
  are 1,000, rep-C seeds 1-8 are 2,000, rep-A07-350 is 500 (as l. 306-308 says). **No config carries
  `train.ebops_trace_every`** (Counter {None: 312}). That is expected: the series has not yet been
  rebased onto the regime-B bundle (l. 9, launch gate 11).
- **Placebo against replica, flattened key diff** (P-350-s1 vs REP-A-s1, P-5M-s1 vs REP-C-s1).
  `name`, `experiment.arm`, `engram_study.question`, `train.epochs` (500 vs 1,000 / 2,000) and six
  `delta_study.*` keys (`entry`, `kind`, `flags`, `placebo`, `amendment_status`, `horizon_epochs`)
  differ. STUDY Arms l. 192-199 names exactly these classes.
- **Code citations, anchor working tree**:
  - `ablation.py:35` is `digest_json`.
  - `:597` is `keras.utils.set_random_seed(seed)`.
  - `:623` is `'config_sha256': digest_json(cfg)`.
  - `:658-659` is `stage_run_id(cfg['name'], stage)`.
  - `monolith.py:261, 288` build the Keras model name from `cfg['name']`.
  - `wandb_util.py:65, 71`: BNJ_STAGE ∈ {canary, pilot, pilot-b, production}.
  - `enable_op_determinism` appears only at `campaigns/chang0926/evaluate_roc.py:115`.
  - `ablation.py:833-837`: the [A6] snapshot holds the best-feasible-as-of-E files, so reading the
    replica's best-as-of-500 from the snapshot is correct.
  - `ablation.py:483-489` in the working tree (the return at l. 489):
    `return k is None or epoch == 0 or (epoch + 1) % k == 0 or epoch + 1 == cfg['train']['epochs']`.
    The staged patch 0027 therefore traces epoch 0 (701 per 7,000-epoch run, decisions.md l. 84).
- **Kai's decisions**: decisions.md "2026-09-27 (Kai, direct)". (1) The start signal is the regime-B
  pilot's epoch-500 validation readout; the regime-A pilot's readout and production's were declined.
  (2) Mean paired gap, family-pooled spread, LCB80 beside it; "this signs [DK6]". STUDY l. 38-42,
  396-401, 743-744, 1119-1121 and 1204-1207 implement both as stated.

## Earlier A and B findings, checked by name

My v2 findings:

| v2 | finding | status | evidence |
| --- | --- | --- | --- |
| A1 | built on regime A, which Kai abandoned | **resolved** | frontmatter l. 9; change log l. 63-68; identical-across-runs l. 237-240; Selection l. 669-678 (traced epochs only, denominator printed); gate 5 l. 426-429; Budget on 136.5 s l. 930-943; [DK13] l. 1142-1146 |
| A2 | family test not referenced to the placebo | **resolved** | l. 751-756 (d = cell − placebo, own sd, simulated critical value), reproduced above. Residual in the bit-identical branch: new B2 |
| A3 | G3′ has no power | **resolved** | l. 716-727: bound named (two-sided, own sd, df n_p − 1), power printed, "non-inferiority not shown at this n", M023 to `mulder` regardless ([DK15]) |
| B1 | Kai's launch timing | **resolved** | launch gate 1 l. 396-409 quotes Kai and names the regime-B pilot readout; [DK4] l. 1110-1116 |
| B2 | placebo not specified; determinism unknown | **resolved in Arms, residual elsewhere** | Arms l. 190-215 is exact against the config diff. The change log, Question, [DK7] and experiment-log stub still say "only `name`": new B1. The probe is too narrow for the weight put on it: new B2 |
| B3 | heteroscedasticity breaks "0.90 by construction" | **resolved** | "by construction" is gone (grep). Achieved rates are printed at l. 112-117, 137-139, 767-774 and 868-870 |
| B4 | pooled interval under-covers | **resolved** | l. 746-749, simulated 2.18 / 2.15 (reproduced) |
| B5 | rank-move flag has no null rate | **resolved** | l. 806-816, T from §8 (reproduced). Residual: the definition of r, new B5 |
| B6 | [DK6] reverses arbiter fix 9 | **resolved by Kai** | decisions.md top entry; l. 1119-1121 "Not a default" |
| B7 | E planning K = 5 against the 90 % rule | **resolved** | [D16] l. 1094-1099; Budget l. 983-993 (K = 4 planning, K = 5 alternative row, reason stated once) |
| C1-C5 | | applied | 0.81 at l. 139 and 870; m 43 / 40 at l. 108-110; sd named at l. 877; ceiling rates at l. 617-620; families defined once at l. 730-742 |

Arbiter v2 adjudication rows #1-#16 (the A and B rows):

| arb v2 | status | where |
| --- | --- | --- |
| #1 regime B, #2 launch timing, #11 E packing (v1 #4d, #7, #9, #10) | **resolved** | see A1, B1 and B7 above. Code base: l. 9 and gate 11 name "the anchor's regime-B bundle (the sha the PREFLIGHT addendum for patch 0027 names)". Pods: 27 at l. 72, 469-470, 1062-1065, 1156-1158. Anchor re-pinned to 96b95f2 at l. 9. Residual pin issue: C3 |
| #3 heterogeneity, #8 pooled coverage, #16 cheap version at n = 3 | **resolved** | l. 751-774; cheap version at l. 1006-1011 "not calibrated under two-mode seeds" |
| #4 placebo reference | **resolved** | l. 751-752 |
| #5 placebo specification and determinism | **mostly resolved** | l. 190-215, 443-448, 775-785, 898-903. New B1 and B2 |
| #6 replica-side losses | **resolved** | l. 536-544. C1 notes a rationale mismatch |
| #7 G3′ power (v1 #4a) | **resolved** | l. 716-727 |
| #9 rank-move flag | **resolved** | l. 806-816; new B5 |
| #10 ranking primary (v1 #6) | **resolved by Kai** | l. 743-750 |
| #12 [L1] (v1 #19) | **resolved** | l. 1160-1172: long-horizon cells at 500 against their own H, "a count of order changes, not a test"; seed-rank persistence labelled "not a test of [L1]" |
| #13 sd_rep usable count | **resolved** | l. 508-514 |
| #14 accuracy-vs-AUC consequence | **resolved** | l. 835-838 |
| #15 pairing efficiency | **resolved** | l. 839-849, ρ̂ null interval and unpaired companion (reproduced) |

## Category A

**None.** No validator line is A-marked. No [D] label is replaced without a dated amendment: [D6]-[D8]
were amended in v2 and [D16] in v3, and Kai's two answers are implemented as he gave them. Every
number I recomputed matches the STUDY. The inconsistencies below are between the STUDY and its own
cited sources or companion text. At STUDY they are B (the mandatory numerical self-consistency
check is A only at VERIFY and REPORT). B3 is a number that contradicts the source it cites; whether
that rises to A is the arbiter's call.

## Category B (should address)

**B1. The placebo is still described as "only `name` changed" in four places. As written, the
stub's PREFLIGHT assertion would fail.**
- Arms l. 192-207 is correct. The placebo differs from the replica in `name`, `experiment.arm`, six
  `delta_study.*` keys, `engram_study.question` and `train.epochs` (the diff above). The assertion
  compares digests "after deleting those identity and provenance keys and setting `train.epochs` to
  one value".
- These places still say "only `name`":
  - The change log, l. 84: "specified as the replica's config with only `name` changed".
  - The Question, l. 124: "the replica's config under another run name".
  - [DK7], l. 1122-1123: "the replica's config under another `name`".
  - The experiment-log stub, `.claude/memory/experiment-log.md` l. 13: "= the replica's config with
    only `name` changed (PREFLIGHT asserts equal digest without name, init kernel hashes, first-step
    CPU loss)".
- Why it matters: an engineer who implements the stub's assertion gets unequal digests, because
  `train.epochs` and `delta_study.*` differ, and will either fail the gate or loosen it ad hoc. The
  fixer's own report noted "not in `name` alone". It propagated the correction to Arms, the X2
  assertion (l. 349-351) and cell-key class (3) (l. 221-222), which are correct, but not to the
  change log, the Question, [DK7] or the stub.
- Fix: in all four places, use the Arms wording (identity and provenance keys plus `train.epochs`,
  with the assertion as in l. 205-207).

**B2. The determinism probe is too narrow to select the placebo branch, and branch (i) gives up
the placebo reference for no gain.**
- The probe (l. 443-448) runs "in the E canary pod, the same E config and seed run twice on one GPU
  product for 3 epochs". Under regime B the first traced epoch is the end of epoch 10 (or epoch 1
  on the staged tree, `ablation.py:489`). So a 3-epoch probe either never exercises the full-split
  reset trace or exercises it once. That trace feeds BetaPID and resets the live WRAP ranges (anchor
  96b95f2, regime-B items (3)-(4)). Bit-identity of the untraced path does not show bit-identity of
  a regime-B run.
- The probe runs on E only. Its outcome selects the branch for P-5M too, and P-5M is an A07-class
  run (4 heads, learned PE) with different kernels.
- Both runs sit in one pod. The placebo is never in its replica's pod (l. 207; GATES §6 "Packs",
  asserted), so what branch (i) needs is identity across pods and nodes, not within one pod.
- Branch (i) (l. 776-783) then switches the family test's reference from the placebo to the
  replica, with a no-offset assumption (false "yes" 0.26 at 0.707 SE, reproduced). If the stack is
  truly bit-identical and the two share a product, then d = cell − placebo equals g exactly, and the
  placebo-referenced test is the same test (critical value 4.41 vs 4.43, 6.75 vs 6.79). When they do
  not share a product, the placebo reference is the offset-robust one. Keeping the placebo as the
  reference in both branches removes the no-offset assumption and makes the test's calibration
  independent of the probe. The probe would then only decide how the placebo's own spread is read.
- Fix: (a) run the probe past at least two traced epochs (for example to epoch 21), in two
  different pods of the same GPU product, for both E and A07. (b) Or, simpler, keep d = cell −
  placebo in both branches, and let the probe decide only whether the placebo check (iv) and the
  placebo's rank are read. For (iv) in branch (i), say what happens when every per-seed g is 0 and
  sd = 0, since t is then undefined: for example, "any nonzero per-seed placebo g flags".

**B3. The "What can be packed today" row overstates the packable set against the source it cites.**
- STUDY l. 967-972 (and `budget.py` l. 193-194, `plan.md` l. 89) gives 268 runs (240 cell, 8
  placebo, 20 replica) and 156,000 run-epochs, citing `code/GATES.md` §6.
- GATES §6 "Packs" lists these as unpacked: `cache_not_built M009 (N=32), M038 (ungated), M040
  (derived features), M041 (real-slot std); floor_untraced M006; GATE_FAIL M047, M048, M049, P-T1,
  P-T2`. It shows "cells: 83 pods, 220 arms".
- 248 − 220 = 28 = (M009, M038, M040 at 350k and 5M, M041 at 5M) × 4 seeds. So the packable set
  today is 220 + 20 = **240 runs**, not 268. The STUDY's own launch gate 13 (l. 476-477) says those
  four caches are unbuilt and "those cells are unpacked until they are".
- Fix: either subtract the four cache cells, with pod-hours and wall clock re-run by `budget.py`, or
  rename the row "without the X4/X5 exclusions (caches not yet built also excluded: −28 runs)". The
  fixer's "packable today" also belongs in "Where I am not sure" [DK1], where 268 is repeated
  (l. 1212).

**B4. The long-horizon cells are ranked in the same list as the H = 500 cells, with no label.**
- The paired single-lever list (l. 786-787) holds "the 12 accuracy cells on A" at 350k and "the G3
  cells on C" at 5M. Those include M015 (H 1,000), M031 (H 1,500) and M032 (H 2,000).
- Each g is horizon-matched against its replica, but the list orders gaps measured after 500, 1,000,
  1,500 and 2,000 epochs as one series. Replica drift and restart count differ by horizon, and M032
  is "one cosine over H" by construction. This is the "comparison across schedules as one series"
  pattern. The STUDY already pulls these cells out of the family test (l. 739-740) and has no
  placebo at their horizon ([L8]), but it does not mark or separate them in the ranking.
- Their spread also enters s_pool ("pooled over the ranked cells only", l. 745).
- **Contradiction:** [L8] l. 1196-1197 says the long-horizon cells "use the H-500 placebo as their
  reference, labelled so". Arms l. 214-215 and Selection l. 739-740 say they have no placebo at their
  horizon, sit outside the family test, and are reported against the replica. These are two
  pre-registrations of one rule.
- Fix: either list the long-horizon cells in a fourth list, "horizon H ≠ 500", or mark each row with
  its H and exclude it from s_pool. Rewrite [L8] to match Selection l. 739-740.

**B5. The rank-move flag's correlation r is not defined in a way that matches its simulation.**
- `screen_null.py` §8 draws r as the correlation of primary and companion noise within one
  configuration (no true effects).
- The STUDY (l. 808) sets T from "the observed family-pooled run-level correlation r of primary and
  companion values". If r is computed across runs without centring per cell, real between-cell
  differences inflate it. That selects a smaller T, which flags more cells than the ~1 null flag the
  rule targets.
- The pairing section already centres per cell (l. 842, "cells centred per cell").
- Fix: define r on values centred per cell (or per cell and seed-mean), the same way as ρ̂, and say
  so at l. 808.

**B6. The literature request is stated but not tracked.**
- l. 1367-1369 say a physics-researcher note on screen design and seed-variance methodology "is
  requested, not assumed".
- No request is recorded: there is nothing in `research-log.md` (grep: no screen-design,
  seed-variance, winner's-curse or successive-halving entry), `plan.md` or `decisions.md`.
- [L1] (whether rank after 500 epochs predicts rank after 7,000) is the design's largest unmeasured
  assumption, and prior art on multi-fidelity screening bears directly on it.
- Fix: file the request with a named owner (orchestrator to physics-researcher) before PREFLIGHT,
  and cite it at l. 1367.

## Category C (suggestions)

- **C1.** Replica-side losses (l. 536-541) re-simulate "the family test's critical value" at n′. The
  family test is d = cell − placebo and does not contain the replica, so a replica loss does not need
  to cost the test a seed. It is harmless: dropping is independent of d under the model and only
  costs power. Say why the test's seed set follows the ranking's, or keep the test at n. Also say
  whether a rep-A seed lost at 1,000 only (M015's horizon) lowers n for the H 500 list (l. 537,
  "at the horizon").
- **C2.** Traced epochs. l. 669-675 gives the committed-text rule (no epoch 0) as primary and hedges.
  The anchor working tree (`code/tree/bnhgq2/ablation.py:489`, patch 0027 as staged, bundle
  f2107a04) traces `epoch == 0` (the anchor STUDY's `:483-487` citation predates the epoch-0 addition), so 51 per cycle is the expected count. Keep "PREFLIGHT prints", but
  state the staged tree's rule as the expectation.
- **C3.** Pins.
  - Anchor `RUN.md` is pinned at e620173 (l. 9), but the trace / remainder split (90.61 / 127.45 s)
    behind the 136.5-s basis comes from the "Canary — W&B history pull", committed in c9c9942. Pin
    RUN.md there.
  - The regime-B bundle has already been frozen twice: f2107a04 (decisions.md l. 80) and e90327d4
    (re-frozen, uncommitted, decisions.md l. 28). Naming both, with "PREFLIGHT fixes which", would
    stop anyone reading f2107a04 as final.
- **C4.** [L1](a) reads M015, M031 and M032 at their epoch-500 [A6] snapshot. Those readouts are not
  in the 318 certification count (only one selected checkpoint per cell run is counted). Either
  certify them (+16 at n = 4), or label the 500-epoch values "uncertified, [L1] only".
- **C5.** In the bit-identical branch, the placebos (8 runs, 25.3 / 37.9 pod-hours) carry
  information only where their GPU product differs from the replica's. If the probe is taken at face
  value, say whether they still launch.
- **C6.** The ranking interval (Kai's pooled spread) is simulated at equal spread only (§6). Under
  the STUDY's own heteroscedastic rows, the "95 %" pooled interval under-covers for high-variance
  cells. The per-cell own sd is printed beside it (l. 827). Label the pooled interval "95 % at equal
  spread".
- **C7.** Pod-hours are slot-seconds, so they do not bill partly empty pods. Examples: the rep-C pack
  holding seeds 4-6 runs to 2,000 with seeds 5 and 6 stopped at 500 (GATES §6 "Pod cap"), and the
  last pack of each (class, H) group. Real GPU-pod-hours are higher. Add one line saying so.
- **C8.** `plan.md` l. 20-23 and 36-38 ("What will be computed": 218 s at K = 6; the anchor at HEAD
  dde5ca7; "Selection rule (anchor HEAD l. 750-862)") are the v1 plan and are not marked superseded.
  The notebook is chronological and the fixer-v2 section is current, but add a "(v1, superseded by
  fixer v2)" tag.

## Competing-group question

If another group ran this screen next month, what would they have that we do not?
- **A literature grounding for the one-cycle, multi-arm screen.** Examples: multi-fidelity or
  successive-halving screening, and seed-variance and winner's-curse handling in ML benchmarking.
  `.claude/memory/research-log.md` has no entry on screen design or seed-variance methodology
  (grep: none). The STUDY says a physics-researcher note "is requested, not assumed" (l. 1367-1369),
  but no request is recorded anywhere I can find. The absence is justified for a never-quotable
  screen, so it is not Category A. The request should be tracked: B6 above.
- **A determinism measurement that covers the regime-B trace path and both architecture classes**
  (B2).

Nothing else. The calibration, power, loss rules and Kai's decisions are all in place.

## Disputed facts for the investigator

None. Every item above was settled from the artifact, the generated configs, GATES §6 or the anchor
tree, with the line cited.
