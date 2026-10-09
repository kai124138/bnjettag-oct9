ITERATE

# STUDY critical review v1: pilot program, 2026-10-05

Reviewer: critical-reviewer, STUDY panel (06-review §6.2). Scope: `STUDY.md` as amended pre-data at 10:46
and 14:14 JST (sha256 `27d43c63…0e86`, 325 lines, read 14:17 JST). `PROGRAM.json` was read from a
snapshot taken at 14:17 JST (sha256 `5bdad964…b3c3`, mtime 10:47; an ml-engineer is editing it). The
disagreements below are recorded, not fixed. Nothing in the campaign was edited except this file.

Also read: 03-phases, 06-review, `docs/PILOT_PROGRAM.md`, decisions.md 2026-10-05 10:08,
experiment-log (top 3), `protocol-r1.json`, `review/PREFLIGHT_critical_v1.md`, `dev/README.md`,
`evidence/`, `study-history/`, `JOURNAL.md`, `code/tree/campaigns/pilot1005/{readout_pilot.py,index.json,generate.py}`,
training-batch `READOUT_epoch500.md`, recovery `readout-preparation/VERIFY.md` and `analysis/rules-b5.txt`,
gpu-benchmark `VERIFY.md:96-141`.

## Numbers traced (recomputed or quoted from source)

| STUDY claim | source | check |
| --- | --- | --- |
| threshold (c) 0.2109624456315518, labels sha `e593f51f…7617` (STUDY:130-131) | training-batch PREFLIGHT.md:519 (`class_counts`, max 12,579 / 62,000 = 0.202887 = p_maj) | ✓; equals readout_pilot.py:54-55 |
| C-s1 heads 0.622127, 0.913695, 0.543640, 0.880046; val acc 0.664726 (STUDY:64-65) | READOUT_epoch500.md:133 | ✓. Mean recomputed 0.739877 ✓. **Note:** that checkpoint is `model_best` at zero-based epoch **19**, 4,880,224 EBOPs (READOUT:122; a26 json `runs[1].checkpoint`). See B5 |
| A-s2 0.320871, D-s1 0.405371 (STUDY:64-65) | recovery VERIFY.md:116-117 | ✓ |
| C′-s1 mean 0.320532 (STUDY:154) | VERIFY.md:140 heads 0.503843, 0.334621, 0.178706, 0.264958 → 0.320532 | ✓ (C′ is A07, target 5M; VERIFY:84-85) |
| 350k range 0.236-0.405 (STUDY:168, 240) | F-s1 0.236177 (READOUT:134), D-s1 0.405371 | ✓ |
| 0.65-0.66 for 5M/unconstrained (STUDY:171, 241) | C-s1 0.664726; A-s1 peak 0.652210 at ep0 4, untraced, 8.1M EBOPs (VERIFY.md:81) | ✓, but both are early or unsqueezed checkpoints (B5) |
| b5 first met (a) at 259-389 (STUDY:115) | rules-b5.txt:13 (A-s1 389), :56 (A-s2 299), :116 (D-s1 259); C′ and E1 never met (a) (:179, :227) | ✓ for the three that met it. No citation in STUDY:115 (C3) |
| Q/K collapse ep0 29-39 (STUDY:114) | rules-b5.txt:37, :97, :160, :251 | ✓ |
| floors and headrooms (STUDY:73-80, 116) | static floors; headroom arithmetic recomputed | ✓ (all 12 headrooms, 80,170 for qkv1) |
| H2 rung mapping (STUDY:85) | smallest A07 rung with headroom ≥ E's | ✓ for all 7 E rungs, incl. 5M → none |
| NB init above A (STUDY:50-51) | dev/README.md:63-64 (init 12,362,587 vs 8,913,043; local, not quotable) | ✓ (rows are 63-64 and the text 66-70; STUDY cites 62-68) |
| R1 cap 138 = 23 × 6; total 1,176 (STUDY:266-270) | arithmetic | ✓ arithmetic. 500 × 30.85 s = 4.28 h ✓. Basis disputed in B6 |
| 30.85 s/epoch (STUDY:266, 269) | gpu-benchmark VERIFY.md:109 (RTX 3090, klow, A07, K = 1) | ✓ for s/epoch. The same row gives **38.8 s total elapsed per run-epoch** |
| study-history hashes (STUDY:43-46) | `sha256sum study-history/*` | ✓ a2f4877a…0c4 (17,860 B, 244 lines), aebef3f0…536 (18,133 B, 246 lines) |
| C1 code citations (STUDY:36-38) | pilot1005/cpu_gate.py:171, chang0926/evaluate_roc.py:144, chang0926/generate.py:203 | ✓ |

`lab_check_protocol` on `protocol-r1.json`: `structural_valid: true`, no findings, protocol sha
`cb51862c…5f70` (matches JOURNAL:27); `matches_snapshot: false` (no frozen snapshot yet, as expected
before STUDY PASS).

Jev `jev_check_claims` (audit `jv-67f7fc2d751f48a1ba7f4de2a810f740`, advisory):

| id | claim (STUDY line) | source given | Jev | by hand |
| --- | --- | --- | --- | --- |
| c1 | b5 first met (a) 259-389 (115) | rules-b5.txt:13 | absent (0.30) | supported across :13, :56, :116; Jev saw only :13. STUDY gives no source (C3) |
| c2 | C-s1 heads and 0.664726 (64-65) | READOUT:133 | supported (0.22) | supported |
| c3 | A-s2/D-s1 weak, 0.320871/0.405371 (64-65) | VERIFY.md:116-117 | overstated (0.35) | supported (values exact; "weak" is VERIFY.md:104-110's own reading) |
| c4 | 500 × 30.85 s ≈ 4.3 h per pod (266) | gpu-benchmark VERIFY.md:109 | overstated (0.46) | **overstated as a pod-time basis**: 30.85 is training s/epoch, and wall time per run-epoch is 38.8 s (B6) |
| c5 | NB starts above A in EBOPs, 4-bit init (50) | dev/README.md:62-70 | supported (0.77) | supported |

## Earlier findings ([A2] claims to address them), by name

| finding (PREFLIGHT_critical_v1) | status | evidence |
| --- | --- | --- |
| **B4** entropy cut calibrated on A07 only | **partly resolved** | The entropy-only stop exists (STUDY:159-166, 252-256), but the amendment summary (STUDY:26-27, "fails healthy *only* on entropy") and the §5 definition (STUDY:159-162, which adds acc ≥ 0.50) disagree. Also missing from PROGRAM.json. See B1, D-1 |
| **B5** w150 time-limited and confounded | **resolved as registered** | STUDY:115, 185, 304-311: inconclusive (time-limited) is pre-registered. D3 awaits Kai (STUDY:308-311) |
| **B6** H2 undefined if E recovers only at 5M | **resolved** | STUDY:85, 183, 195-197. A related undefined case remains (B3) |
| **C1** `campaign.production: true` | **resolved** | STUDY:33-41; citations verified |
| **C4** pre-amendment text in scratch only | **resolved, text stale** | `study-history/` holds both files with the stated hashes, but STUDY:47-49 still says "scratch only … waits for the orchestrator" (C1 below) |
| **C5** NB init EBOPs | **resolved** | STUDY:50-51, 188-193 |
| B1 (PROGRAM `bundle_sha` vs readout `bundle_sha256`) | **open** in PROGRAM.json | PROGRAM:67-69, :543, :913, :1254; readout_pilot.py:250 writes `bundle_sha256` (D-2) |
| C2 (arm ids) | **open** | STUDY:112-113 "E250-C … E5M-C", "A07-350-C …"; PROGRAM and index.json use `E250k-C`, `E5000k-C`, `A07-350k-C` (C2 below) |
| A3 (STUDY not reviewed) | being addressed by this panel | STUDY:5 still says "draft … not reviewed" |

## A (must resolve)

### A1. R2 and R3 cannot run on "the same bundle", and a new sha stops the program by rule

- STUDY:7 says "one bundle for R1-R3". §7 (STUDY:199) says R2 uses the "same bundle as R1". §12
  (STUDY:282) says "all pilot rounds use one bundle; a new sha stops the program".
- Bundle b3fb22c8 contains only the R1 configs. `pilot1005/configs/` has 23 files. `index.json` has
  `round: "R1"`, `count: 23`, and the rounds Counter is {R1: 23}. `generate.py:38` hard-codes
  `ROUND = 'R1'`.
- `readout_pilot.py:230-233` reads the readout rows from the bundled `index.json` by round, and
  errors when there are none. So no R2 config, R2 index row or R2 readout exists in this bundle.
  PROGRAM:792-793 assumes "pre-built" R2 handoffs that this bundle cannot supply.
- As written, then, reaching R2 needs a new bundle, and a new bundle triggers the §12 stop. Avoiding
  the stop after R1 data exist would take a post-hoc amendment (STUDY:279-280). That is the
  pre-registration failure the rule exists to prevent.
- Fix, pre-data, choose one:
  (a) Redefine "same code" now. The R2/R3 bundle must be byte-equal to b3fb22c8 outside
  `campaigns/pilot1005/{configs,packs,index.json,config_map.json,r1_packs.json}`, checked by a
  file-by-file diff at the R2 PREFLIGHT, and the configs must be generated by the same `generate.py`
  with only round, seed, budget and arm changed. State whether a CPU-gate rerun is required.
  (b) Pre-build every R2/R3 candidate config (E rungs × seeds 2-4, 6 variants × seeds 3-5, NB at
  each E rung > 350k × seeds 1-3) into one bundle before R1. This changes the sha, so the CPU gate
  submitted at 14:11 (JOURNAL:26) must rerun.
  (a) is cheaper.

### A2. The production pair (and the R2 H5 comparison) is not matched when V_bin ≠ A350-C, and NB's production configuration is undefined

- P350 is "(350k, V_bin) … each as A and NB" (STUDY:224-225). A launches "V_bin's binary
  configuration" (STUDY:236).
- V_bin can be A350-noC, A350-C-w50, A350-C-w150 or A350-C-qkv1 (STUDY:211-212; PROGRAM:692-707).
- The P350 rule checks NB350-C only, which runs with (c), warmup 1 and no floor (STUDY:117, 227;
  PROGRAM:1040-1068). The STUDY never says whether production NB gets V_bin's warmup, floor or (c)
  status.
- Two cases follow:
  - If NB gets V_bin's settings, the NB configuration launched for 960 GPU-h was never piloted.
  - If it does not, A − NB at 8 paired seeds, which is the program's bearing (STUDY:59-60),
    confounds the weight type with warmup, floor or controller.
- The pre-amendment text had this matched: "NB@350k … uses the best binary fix's configuration with
  only the weights changed" (`study-history/STUDY_v0.md`, §8). The 10:46 amendment dropped that
  clause.
- The same confound reaches H5 in R2. STUDY:186 reads NB350-C against V_bin at seeds 1-3. With
  V_bin = w50 or qkv1, two columns differ, which contradicts "only the listed column differs"
  (STUDY:119).
- Fix, pre-data, one of:
  - P350 is allowed only when V_bin ∈ {A350-C} (otherwise use Prec, or stop for Kai);
  - or NB production = V_bin's configuration with only `quant.weight` changed, plus an R2 pod for
    that NB variant at seeds 1-3 before P350 can fire;
  - and in either case, define H5 at R2 as NB350-C against A350-C at matched seeds (W/V_bin only
    adds seeds when it is A350-C).

## B (fix before PASS)

### B1. Entropy-only failure: the wording conflicts, and a band remains undecidable (B4 follow-up)

- STUDY:26-27 says a row failing healthy "*only* on entropy" stops the program and "is never read as
  unhealthy". The definition at STUDY:159-162 also requires `best_feasible_val_acc ≥ 0.50`.
- The H2 refutation clause (STUDY:183) says "E unhealthy at 5M on a criterion other than entropy
  alone".
- Take a row with status complete, feasible, non-degenerate, acc in (0.2110, 0.50) and entropy ≥ 0.95:
  - by §5 it is unhealthy and not an entropy-only failure, so nothing stops;
  - by §6 H2 it fails on entropy alone, so H2 is not refuted;
  - by §7.1, if it is the E 5M row, "no E rung healthy" fires the pivot stop for a reason that is
    not H2.
- The A-s1 peak of 0.652210 (VERIFY.md:81) suggests that a working E clears 0.50, so this band is
  unlikely but not excluded.
- Fix: make STUDY:26-27 and STUDY:183 use the §5 definition verbatim, and state H2's verdict in that
  band ("inconclusive").

### B2. H3 refutation is confounded with H2, and the claimed R2 H3 arm no longer exists

- qkv1 at 350k has 80,170 headroom, against 178,474 for A350-C (STUDY:116, 78). If H2 holds, the floor
  arm is predicted to be *worse* than A350-C. So "qkv1 0 healthy ⇒ H3 refuted" (STUDY:184) is what H2
  predicts too. dev/README.md:151-153 (F2) says the same thing. A qkv1 success is informative; a
  qkv1 failure is not.
- STUDY:91-92 says "R2's direct H3 arm separates them". That held for the pre-amendment R2
  (STUDY_v0 §7.4). After 10:46, R2 has an H3 arm only if W = qkv1 (STUDY:205-210). The "→ R2 (≥ 3)"
  in STUDY:184 is therefore not guaranteed.
- Fix: refuted becomes "inconclusive (headroom-confounded)" unless qkv1 is also run at a rung where
  its headroom ≥ A350-C's 178,474 (zero floor 269,830 → 448,304, i.e. the 500k rung) and fails there.
  Strike or condition the R2 sentence at STUDY:91-92.

### B3. H2 verdict is undefined when A07 has no healthy rung

STUDY:183 refutes on "A07 ≥ 2 rungs from the prediction" but does not define the A07 recovery rung
when no A07 rung is healthy (for example, E recovers at 500k, so the prediction is A07 1M, and A07 at
5M is unhealthy). C-s1 (A07, 5M) was healthy on the 42abed code, but at epoch 19 (READOUT:122). State
it: "no A07 rung healthy = beyond 5M", counted as ≥ 2 rungs when the prediction is ≤ 1M.

### B4. Refutations are read at a resolving power the STUDY itself says is absent

- STUDY:175 says that with 2 seeds, only 2/2 against 0/2 separates arms.
- Yet these R1 rows count as refutations:
  - H3 refuted on qkv1 0/2 (the Clopper-Pearson upper bound for 0/2 is 0.842, recomputed);
  - H5 refuted on "NB count ≤ binary count", which includes 0/2 vs 0/2 and 1/2 vs 1/2;
  - H4 refuted on both warmups ≤ A350-C, which includes 0/2 vs 0/2.
- H5's gloss "0/3: then the cause is the budget, not binary" (STUDY:88) also overreaches. The [A2]
  note itself (STUDY:188-192) says that an NB difference includes a different squeeze trajectory.
- No rule consumes these verdicts, so this affects only what the readout reports.
- Fix: call a symmetric 0/n vs 0/n "no separation (inconclusive)", and drop the "budget, not binary"
  clause.

### B5. "Healthy" is read on the best checkpoint, which can precede a collapse; this matters for a 960 GPU-h trigger at n = 3

- Entropy and accuracy are taken on the best-feasible checkpoint (STUDY:133-137; readout_pilot.py:170).
  The only healthy reference, C-s1, is its epoch-19 checkpoint at 4.88M EBOPs (READOUT:122). A-s2 was
  feasible at ep0 299 and then a constant classifier (AUC 0.500000) from ep1 350 to 400
  (VERIFY.md:105-110). So a row can be "healthy" while the run has collapsed by epoch 500.
- On the decision itself: 3/3 at n = 3 has a Clopper-Pearson lower bound of 0.292 (recomputed; STUDY:176
  says so). At a true per-seed health rate of 0.5, P(3/3) = 0.125. A 3/3 pass is therefore a weak
  screen of the rate production will see over 8 seeds × 7,000 epochs, and epoch 500 does not see a
  restart (STUDY:324-325).
- What contains the risk: production also needs Kai's re-signed fill (STUDY:234-235) and a production
  PREFLIGHT critical PASS (PROGRAM:1408-1412). So the trigger is not fully unattended.
- Fix, pre-data, both cheap:
  - add one readout field, the entropy (and val acc) of the epoch-500 snapshot, and require it for
    P350/Prec as well (field list STUDY:123-125);
  - pre-register a production early-stop: a readout at production epoch 500 using the same health
    rule, which stops both Jobs if fewer than 6/8 seeds per arm are healthy. This bounds the downside
    to about 1/14 of 960 GPU-h.
  - Also rename §9 "fires without asking", since Kai re-signs (C4).

### B6. The spend caps assume the training-only epoch rate, and the production cap is short of the measured wall rate

- gpu-benchmark VERIFY.md:109 (3090, A07, K = 1) gives 30.85 s/epoch, but **38.8 s total elapsed per
  run-epoch**. At that rate:
  - R1: 500 × 38.8 s = 5.39 h, which fits 6 h with 0.6 h slack and no room for a retry
    (PREFLIGHT_critical_v1 A2, open on the PREFLIGHT side).
  - Production: 7,000 × 38.8 s = 75.4 h per pod, × 16 = **1,207 GPU-h**, against the 960 cap
    (STUDY:269). With pilot caps of 216, the total is 1,423, above the 1,200 Kai approved
    (decisions.md:18).
- If the production deadline is set to the per-pod basis of 60 h (STUDY:272-273), pods stop at about
  5,567 epochs (60 × 3,600 / 38.8), short of the 7,000 registered.
- Production A/NB are E-architecture runs, and E's 3090 K = 1 rate is unmeasured. R1 measures it.
- Fix: base the production projection and the §9 guard (`spend-so-far + 960`) on the R1-measured wall
  time per epoch of the chosen arm × 7,000 × 16. Stop for Kai if that exceeds the remaining budget.
  Set the production deadline from the same number.

### B7. STUDY ↔ PROGRAM.json disagreements (snapshot 14:17; to be reconciled by the editor, not here)

- **D-1.** No entropy-only stop anywhere in PROGRAM.json. `r1_decide` (PROGRAM:591-616), `W`
  (:635-691), `r_rec` (:963-1000) and `r3_decide` derive from the readout directly. That contradicts
  STUDY:252-256 ("checked before every other scientific stop"). As drafted, an entropy-only E 5M row
  would route to `stop_notify_pivot` with the message "no E rung healthy" (PROGRAM:1535). An
  entropy-only row at a high rung, with a lower rung healthy, would let R2 launch.
- **D-2.** `bundle_sha` (PROGRAM:67, :543, :913, :1254) vs the readout's `bundle_sha256`
  (readout_pilot.py:250). This is PREFLIGHT B1, still open.
- **D-3.** `amendments` (PROGRAM:6-13) lists only the 10:46 amendment. [A2] and the D3 pending choice
  are absent.
- **D-4.** `production_gate` requires a production PREFLIGHT critical PASS (PROGRAM:1408-1412), but
  STUDY §9's guards (STUDY:234-235) do not list it. Add it to the STUDY.
- **D-5.** The production spec (PROGRAM:1436-1456) does not say which NB configuration launches (A2).
- **D-6.** The PROGRAM's P350 counts rows with `arm == $V_bin`. If R2 names the 350k bracket rows
  `E350k-C` rather than `A350-C`, seeds 3-4 drop out of the V_bin count when V_bin = A350-C
  (PROGRAM:1007-1018 with :716 `minus: bracket_runs`). Fix the naming of the 350k rung in R2.
- Agreeing: caps 138/60/18/960/1,200 (PROGRAM:17-28 = STUDY:264-270), the healthy definition
  (PROGRAM:30-37), the 15 readout fields (PROGRAM:38-54 = readout_pilot.py:51-53), the W/V_bin
  ordering, other-side s3, the (c)-harmful stop (PROGRAM:742-779), the R1/R3 row counts 23/3, and the
  P350 and Prec conditions.

## C (suggestions)

- **C1.** STUDY:47-49: the earlier texts are now in `study-history/` (JOURNAL:28; hashes verified).
  Update the sentence. STUDY:21 ("scratch copy only") is stale too, though it is inside the
  10:46 block.
- **C2.** Align the arm ids at STUDY:112-113 with `E250k-C … E5000k-C` and `A07-350k-C …` (PREFLIGHT C2).
- **C3.** Cite rules-b5.txt:13, :56 and :116 for "259-389" (STUDY:115). Note that E1-s1 and C′-s1 never
  met (a) in 500 epochs (:227, :179). Time-to-budget can make a w1 row infeasible as well, so
  `feasible_any` false reads "time-limited" for w150 but "unhealthy" for every other arm.
- **C4.** §9 heading "fires without asking" conflicts with the guard "Kai re-signed that fill"
  (STUDY:222, 234-235). Say "fires after Kai's id-only re-sign".
- **C5.** §5 (b) uses "the architecture's 0-bit floor". For qkv1 the readout uses the row's
  `zero_floor_ebops` 269,830 (readout_pilot.py:127). Say so in STUDY.
- **C6.** "diverged" is a plausible scientific outcome at 250k but stops the whole program
  (STUDY:245). Keep it if intended, but say that it is.
- **C7.** STUDY:50 cites dev/README.md:62-68. The rows are 63-64 and the text 66-70.

## 06-review §6.3 answers

1. Conventions: validation-only selection, ROC-test untouched (STUDY:277-278). a26 reads x_val, and
   the readout reads run files only. Yes.
2. Reference table: no formal table. §1 prior state gives single-seed validation values with sources
   (verified above). This is acceptable for a directional pilot. The healthy reference is an epoch-19
   checkpoint (B5).
3. What a competing group would have: a matched NB-vs-A production pair (A2), a headroom-matched H3
   control (B2), and an E entropy reference (B4 of PREFLIGHT, still unavailable).
4. Resolving power: stated honestly for support (STUDY:175-176), but refutations exceed it (B4). The
   production trigger at n = 3 is weak and needs the early-stop (B5).
5. Limitations: the E speed and the epoch-500 cut are stated (STUDY:324-325). The cap basis is not
   (B6).
6. Context: pilots are not results by rule (STUDY:14-15). No pull is required.

## Verdict

**ITERATE.**
- A1 (bundle rule contradiction) and A2 (unmatched production/H5 pair) are both pre-data text
  changes, about 1-2 agent-hours with B1-B6. A1 option (a) leaves the running CPU gate valid.
- B7 is for whoever finalizes PROGRAM.json before Kai signs.
- R1 must not launch until this panel's arbiter passes (PREFLIGHT A3).
