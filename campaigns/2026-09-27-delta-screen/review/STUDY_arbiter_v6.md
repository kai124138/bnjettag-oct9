# STUDY arbiter v6: 2026-09-27-delta-screen (Delta wave 2)

Arbiter, fresh context, 2026-09-28. Re-review, iteration n = 6, under Kai's freeze rule
(`.claude/memory/decisions.md`, "2026-09-28 (Kai, direct) ... freeze after review round 6 if only B
items remain": only B items → frozen and launched with them disclosed; any A still blocks).
Artifact: `STUDY.md` (HEAD 31db77d, 1,160 lines, 16,331 words), with `plan.md`, `budget.py`,
`screen_null.py` (§1-§19), `rank_sim.py`. Read: `review/STUDY_physics_v6.md` (+ `physics_v6_rarehigh.py`),
`review/STUDY_critical_v6.md`, `review/STUDY_constructive_v6.md` (+ `constructive_v6_screen_null_out.txt`),
`review/STUDY_validators_v6.txt`, `review/STUDY_arbiter_v5.md`, `docs/methodology/06-review.md`
§6.1-§6.8, `decisions.md` top five entries, `campaigns/2026-09-26-training-batch/review/INCIDENT_stall_20260928.md`
(all), the anchor `PREFLIGHT.md` l. 760-800 and `RUN.md` l. 450-520, and the anchor bundle itself
(extracted, below). No plot-validator file (STUDY has no figures).

## Validator lines

`STUDY_validators_v6.txt`: no mechanical STUDY validator exists; `prose_lint` on STUDY.md scores 0,
"reads human" (16,331 words, 1 em-dash). No A-marked line.

## Independent checks (arbiter)

Design arithmetic and code reading, not results, not quotable.

- **The disputed fact (critical v6, Disputed facts 1): do f2107a04 / e90327d4 carry the leak?
  Settled by reading: neither named bundle is launchable.**
  - `shasum -a 256 campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz` →
    `f2107a042b8c…438e` (191,320 bytes, mtime 2026-09-27 19:44 PDT), the regime-B bundle of anchor
    `PREFLIGHT.md` l. 774-778. Its contents are `26f3cc40 + patches 0001-0029` (l. 781); 0027-0029
    are the [D20] trace-every patches, none a memory fix.
  - Extracted in the scratchpad: `code/bnhgq2/ablation.py:700-702` still does, every epoch,
    `model.save(candidate)` then `validation_model = keras.models.load_model(candidate, compile=False)`,
    the first leak candidate of incident §2 ("fresh model, no `clear_session()`"); anchor PREFLIGHT
    l. 764-765 confirms regime B still "saved, reloaded and validated every epoch". No
    `ValidationReloader`, no `RSS_GATE`, no `host_rss_mb` in the bundle.
  - Those three exist only in the **uncommitted** working-tree `campaigns/2026-09-26-training-batch/code/tree/bnhgq2/ablation.py`
    (l. 589-655; mtime 2026-09-27 23:02 PDT = 2026-09-28 06:02Z, after the tarball and after the
    incident report of ~05:30Z). The fix is in progress; it is frozen into no bundle.
  - Incident §5: whatever the leak source, regime B exceeds 6 GiB per arm before epoch 500
    (reload path: same rate; trace path: about 6.6 GB at epoch 500). So f2107a04 carries the leak,
    or at best a tenth of it, which still breaks the 6 Gi PACK premise.
  - e90327d4: not on disk (the tarball now hashes to f2107a04); it appears only in the
    2026-09-27 ml-engineer entry (`decisions.md` l. 42-43), which predates the incident. A
    pre-incident freeze cannot contain a fix written after it.
  - What PREFLIGHT must show (for the fixer's gate text, below): (i) a bundle sha whose extracted
    `ablation.py` has no fresh per-epoch `load_model` of the candidate (the reloader or an
    equivalent); (ii) host-RSS slope ≤ 5 MB per epoch over ≥ 30 epochs for one E and one A07
    Delta cell (`RSS_GATE` line or W&B `system.proc.memory.rssMB`); (iii) `run_pack.py` with the
    incident §6 heartbeat fix, patch 0038 rebased onto it, `tests/test_run_pack_delta.py` passing;
    (iv) the per-arm memory limit sized as in fix A5.
- **A 5 MB/epoch canary that passes still breaks "6 Gi per arm" for the long arms** (raised here;
  no reviewer computed it). Baseline about 2.1 GB (incident §2 table, RSS at 20:56Z) plus 5 MB × H:
  H 500 about 4.6 GB (fits 6 Gi = 6.44 GB); H 1,000 about 7.1 GB; H 2,000 (rep-C, M032) about
  12.1 GB. The PACK sentence (STUDY l. 884-886) is therefore wrong for the replica and long-horizon
  pods even after the fix. Folded into A (fix A5): the sentence is made true, no gate added.
- **Constructive B1, reproduced** (`constructive_v6_screen_null_out.txt` l. 413-414, 430-432):
  among families with s_int > T, median-g recovery is 0.95 (5M q 0.05, 10,125 of 20,000 draws),
  0.85 (5M q 0.1, 19,705), 0.89 / 0.61 / 0.54 (350k q 0.1 / 0.33 / 0.5). **Further, not raised:**
  at 350k, *Gaussian* median-g recovery above T is still ≥ 0.5 up to σ 2.7 pt (§19a grid l. 418:
  2.2:0.55 … 2.7:0.50), because condition (ii), not (i), sets the 350k T. So "descriptive: recovery
  below 0.5 at this spread" (l. 718) is false under both seed models at 350k between 2.1 and 2.7 pt,
  and under per-run low modes at 5M.
- **Rare high mode, physics B2, re-run** (`uv run --with numpy python review/physics_v6_rarehigh.py`,
  2 s): 350k, T 2.1, median-g / mean-g recovery given s_int ≤ T: q 0.67 0.61 / 0.39 (846 draws),
  q 0.8 0.87 / 0.46, q 0.9 0.98 / 0.55, q 0.95 1.00 / 0.79; 5M, T 1.2: set empty for q ≤ 0.8, 1.00 at
  q ≥ 0.9. Matches physics v6 digit for digit and agrees with critical v6 own check 2 (q 0.6
  0.51-0.53, q 0.67 0.61-0.63).
- **Rank-move at 5M** (`constructive_v6_screen_null_out.txt` l. 458-461): m 37, r 0.9, smallest null
  count 1.2 at T 15; "no grid T" for r < 0.95. Confirmed.
- **Everything else the three reviewers recomputed** (§15a, §18-§19, `rank_sim.py` v6, `budget.py`)
  agrees across all three independent re-runs; no reviewer contradicts another on any number. The
  arbiter did not re-run `screen_null.py` (7 min 51 s; three matching re-runs exist).

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | The 2026-09-28 decision "Delta must not launch on the leaking anchor bundles" is absent: `code_sha` (l. 9) and gate 11 (l. 451-453) name f2107a04 / e90327d4; the gate list (l. 407 "Nothing launches before all of these hold") has no host-memory canary (gate 7 reads GPU memory, epochs 1-3, where a 90 MB/epoch leak adds < 300 MB); gate 4 lacks the run_pack rebase; PACK / Budget (l. 884-886, 848-857) rest on 6 Gi per arm; Reference row (l. 272) omits the stop | cons A1 (grounds 1-3) / crit B1 | A / B | **A** | Case 2. Critical's test ("no sentence is false") is not the test here. A recorded decision imposes a launch requirement, names its gate and threshold, and bars the named base; the STUDY carries none of it and its gate list claims completeness. Same class as arbiter v5 #1 (a rule decided elsewhere, absent from the STUDY), rated A. §6.3 q3 is non-empty (a competing group would have the gate), which §6.3 makes A. The disputed fact is settled against the bundles (Independent checks). The orchestrator's brief records the gate as required by the decision, so adding it is not new machinery. Delegation to PREFLIGHT does not cure it: PREFLIGHT executes the STUDY's gate list, and the Budget and PACK premise is the STUDY's own |
| 2 | Long arms exceed 6 Gi even at the passing canary slope (12.1 GB at H 2,000) | arbiter (raised) | - | **A**, folded into #1 | Case 5. The PACK sentence is false for replica and long-horizon pods even after the fix; one sentence corrects it (fix A5) and routes the per-pod limit to PREFLIGHT (incident §6 PACK-MEM arithmetic). No gate added |
| 3 | A relaunch (heartbeat kill, `restore_checkpoint` from `latest.json` every 25 epochs) resumes one side of a pair while the other ran continuously; no readout column records it; Confounds 5 and the placebo assume uninterrupted runs | cons A1 (ground 4) | A (as part of A1) | **B** | Case 3, correct on the mechanism (incident §1, §4: A-s1 / A-s2 replayed epochs 51-69 from epoch-0050). Not A: the decision does not require it, and a resume replays from a checkpoint rather than changing the arm. It is a missing confound record; a readout column and one Confounds clause, applied now (fix B5). It is a record, not a rule |
| 4 | Label text "descriptive: recovery below 0.5 at this spread" is false for the median-g primary under per-run low modes (5M 0.95 / 0.85 at q 0.05 / 0.1) | cons B1 | B | **B**, corrected now | Case 3, reproduced, and wider than raised: at 350k Gaussian median-g recovery above T is 0.50-0.55 up to 2.7 pt. Conservative direction (under-claim), so B, not A. Under the freeze a false sentence is corrected, not disclosed (fix B1). The robust-s_int alternative is a design change: Known limitations, not adopted |
| 5 | The 350k median-g T is set by the 0.01 floor (2.0 / 2.1 / 2.2 / 2.3 pt at floor 0.005 / 0.01 / 0.02 / 0.05); the ten-seed minimum absorbs seed noise, not the floor | crit B2 / phys C2 | B / C | **B**, disclosed | Case 2: critical's own-check table shows the dependence, physics calls the edge disclosed. B because the sentence "the ten-seed minimum absorbs it" (l. 1015-1016) overstates. Label-only; nothing that runs depends on T. Critical's "ranked, near threshold" label is a new branch, rejected in arbiter v5 row 15, and not adopted. One sentence in [DK8] (fix B2) and a Known-limitations item |
| 6 | The primary (median g) has no interval of its own; the pooled "95 % at equal spread" belongs to mean g; the forest plot does not name its marker | phys B1 / crit B3 / cons C2 | B / B / C | **B**, applied now | Case 1 (two B). A print, not a rule: [min g_s, max g_s], "87.5 % on the median at n = 4, 75 % at n = 3" (1 − 2·0.5ⁿ), and the figures row names the marker and each interval (fix B3) |
| 7 | At 5M the rank-move flag has a threshold only for r ≥ 0.95; below it the family is labelled "companion disagrees at the null level", which asserts a disagreement that was not measured; [L6] relies on the flag without saying so | crit B4 / cons B2 | B / B | **B**, wording corrected now | Case 1. The fallback label misdescribes (a false assertion), so it is reworded now (fix B4). Critical's alternative (rank-move on mean-g ranks) changes a rule: "Where I am not sure" alternative only |
| 8 | Rare high mode (q > 0.5): l. 618-620 says "not simulated … lower recovery … T 1.4 / 1.4 under the v4 rule", stale for the median-g primary | phys B2 / crit C1 | B / C | **B**, corrected now | Case 2. Physics' B stands: the sentence states a mean-g, v4-rule result as if it applied to the primary, which two independent scripts contradict (Independent checks). Replace with the review-script values, labelled as review checks, plus the clause that a median/mean disagreement is expected there (fix B6). No `screen_null.py` change required |
| 9 | "No rule changed" (change log l. 199-200) undersells: 350k T 1.8 → 2.1 (looser) and the 5M rank-move band 0.9-0.95 moved from "read" to uncalibrated | crit adversarial check | (unrated) | **C**, disclosed | True as to rule text; the outcomes moved. One clause in the change log and a Known-limitations item |
| 10 | Stale rationale "one low-mode run in a cell or in the replica moves a 4-seed mean …" (l. 702-703) and "cancels from the order of the means" (l. 626-628) | crit C2 | C | C | Drop "or in the replica"; add "(for mean g; for median g the replica's per-run term enters the order, and §18b, §19 include it)" |
| 11 | "[350k T 2.1 pt by median g, next bullet]" points to the wrong bullet | crit C3 | C | C | "the 'Median-g re-simulation' bullet" |
| 12 | Question could carry the pt clause | crit C4 | C | C | Optional |
| 13 | Kai's entry quotes 0.29, STUDY 0.28 | crit C5 | C | C | No STUDY action |
| 14 | Lines > 150 characters (l. 9, 680, 702, 725, 746, 761, 768), orphan l. 304 | crit C6 | C | C | Reflow |
| 15 | [DK8] block length | crit C7 | C | C | Optional |
| 16 | 350k chance baseline 3/11 = 0.27 | cons C1 / phys C1 | C / C | C | One clause at l. 606 and in Label; print recovery on the "ranked" branch too |
| 17 | Family test / ranking disagreement in the other direction | cons C3 | C | C | One clause |
| 18 | 350k rank-move r ≥ 0.95 row merged on purpose | phys C3 | C | C | One clause |
| 19 | One-line question gives the powerless family test equal billing | phys C4 | C | C | Optional |
| 20 | Tuning asymmetry sentence to confirm STUDY | phys C5 | C | C | Carry at confirm |

No finding is dismissed. The only contested category (row 1) is decided A; every other category
is the reviewers' or higher.

## Earlier A and B findings (arbiter v5 fixes 1-7), by name

| v5 fix | status | evidence |
| --- | --- | --- |
| 1 (A) confirm cap restored | **resolved** | STUDY l. 698-700 "at most 12 confirm cells per confirm wave, taken in median-g order … nothing advances automatically into GPU time"; Falsifier l. 806 "(at most 12 cells go to confirm, Selection rule 'Cap')"; matches DELTA l. 858 with the [DK6] order |
| 2 (B) T rule: floor + ten seeds + minimum, cascade | **resolved as specified; residual → row 5** | Label l. 721-727 states the floor, ten seeds and minimum; [DK8] block l. 1005-1021 per-seed table reproduced 40/40 by critical v6 and matched by physics and constructive; grid sentence l. 1017-1018; [DK8] dated v6 l. 956-957; `plan.md` l. 129 and 156 tagged "[superseded v6]"; v5 change-log T annotated (critical v6 l. 283) |
| 3 (B) [DK16] above-band disclosure | **resolved** | Seeds l. 576-579 (350k 0.61 → 0.71, 0.54 → 0.67; 5M 0.26 → 0.34, 0.26 → 0.29, median g, §19b; output l. 415-416, 431-432); ALTERNATIVES in the [DK16] row (326 runs, 1,188.1 / 2,034.9 pod-hours = Budget l. 860) |
| 4 (B) median g as companion | **superseded by Kai's decision (median primary) and resolved** | Ranking l. 701-712 cites `decisions.md` 2026-09-28; mean g beside it; Kendall τ and the top-12 / top-3 mark l. 711-712; §18b / §19 re-scoring; residuals → rows 6, 7 |
| 5 (B) detectable effect in pt | **resolved** | Family test l. 744-746 (1.65 / 2.40 … 13.05 pt / above grid edge, §15a, reproduced by all three reviewers); box l. 230-232; Falsifier l. 801 |
| 6 (B) seed-shared clause | **resolved** | Box l. 223-225 "because in that model the cell × seed interaction is the within-mode sd, 0.3 pt, by construction" |
| 7 (C) rows 8-21 | **resolved** (row 14 now stale → row 8 here) | critical v6 l. 288 cites a line per row; spot checks: "at most 11" l. 684, s_int 90 % interval l. 718, lost replica seed l. 715, EBOPs column l. 926 |

## Regression triggers (§6.7), each checked

| trigger | status | evidence |
| --- | --- | --- |
| selection on held-out, or changed after results | not met | validation only (l. 630, 789); no result exists; the median switch and T values changed before any run, each dated (l. 954-957) |
| val AUC vs ROC-test AUC > 0.01 | not met | no ROC-test evaluation (l. 789) |
| single-seed / < 100-epoch / lab-pod headline against the record | not met | nothing quotable (l. 918); Reference table has no comparand (l. 268-275) |
| cross-N / input / split / schedule as one series | not met | M009, M038, M040 in their own lists (l. 687-693, 920) |
| gap < seed sd with < 3 seeds | not met | n ≥ 4 |
| reload outside 1e-7; TF32 on | not met | Confounds 8 (about l. 543-544) |
| eBOPs not remeasured on the selected checkpoint | not met | 318 certifications (l. 1100) |
| binary layer with > 2 values | not met | conventions row (binary gate) |
| DSP / C-sim / C-synthesis | not applicable | no synthesis |
| per-class AUC < 0.7 hidden | not met | readout l. 771-772 |
| byte-identical arms / different y arrays | not met; watch | y_val sha asserted (gate 3); placebo's bit-identical reading pre-registered (l. 749-756) |
| failed validation accepted without remediation; tautological validation | not met | the failed validation is the anchor's regime-A pilot (another campaign), with documented remediation (incident §6; RUN.md "Stopped 2026-09-28T05:31Z"; the working-tree fix). For this STUDY nothing has run; T is from simulation only. Fix A makes the remediation a Delta launch gate |
| [D] label replaced without dated amendment | not met; **watch in fix A** | [DK4], [DK13] and `code_sha` change in fix A: the amendment must be dated 2026-09-28 and marked where it applies |
| outward numbers ≠ VERIFY | not applicable | none |
| suspiciously good | not met | seed-shared 1.00 is by construction and stated (box l. 223-225; physics v6 verified the mechanism) |

No trigger is met; no investigator and no `REGRESSION_TICKET.md`. The leak is an execution defect in
the anchor's code, already remediated there; for Delta it is a missing launch gate (row 1), not an
upstream-phase error of this campaign.

## §6.8 validation target

No binding comparand, correctly, for a never-quotable screen (Reference table l. 268-275). Unchanged.

## Motivated reasoning

- **350k T 1.8 → 2.1 (looser), set by a constant.** The median switch was Kai's, argued on recovery,
  not chosen to make a list read "ranked". But the 350k T it produced sits where P(s_int ≤ T | q 0.5)
  crosses the 0.01 floor (critical B2), and the STUDY's "the ten-seed minimum absorbs it" claims more
  than it does. Disclosed (row 5). Nothing that runs depends on T (`budget.py`).
- **"Descriptive: recovery below 0.5"** under-claims what the primary resolves (row 4); §6.3 q4 asks
  for honesty in both directions. Corrected.
- **"No rule changed"** (row 9): literally true, outcomes moved. Disclosed.
- **The leak omission** served no argument in the STUDY; it came from the fixer's scope (the v5 list
  predates the 2026-09-28 decision by hours). Not motivated, but blocking.
- Checked and not found: no interval inflated (paired multiplier simulated, unpaired only for Welch
  cells); no rule moved after results; G3′ failure never read as inferiority (about l. 678-680); "no" not
  claimed as absence (l. 801-803).

## Competing-group question

A group publishing this screen next month would have: a launch gate that names the known host-memory
leak and a per-pod memory limit sized for 2,000-epoch arms (rows 1-2, fixed now); a label whose text
is true for its primary statistic (row 4, fixed now); an interval on the ranking statistic (row 6,
fixed now); a rank-move check that says where it is not calibrated (row 7, fixed now). The floor
dependence of the 350k T (row 5) they might have avoided; it is disclosed.

## Disputed facts for the investigator

None. The one the critical reviewer raised is settled above from the bundle, the anchor PREFLIGHT,
the working tree and the incident file.

## Dismissals

None.

## Verdict: **ITERATE** (iteration 6; the fixer's pass is iteration 7; §6.5 strong warning continues, cap 10)

One Category A stands (row 1 with row 2 folded in). Under Kai's rule it blocks. The iteration is
**limited to the A edits (A1-A7)**. After the fixer applies them, **a solo critical-reviewer check of
only those edits suffices (no full panel)**. On its PASS the design is frozen, and the solo check's
file records "**FROZEN (Kai's rule): PASS with disclosed limitations**", the phrase the 2026-09-28
Kai entry's Check line asks for.

So that no false sentence survives the freeze, the same fixer pass also applies the pre-specified B
wording corrections (B1-B6) and inserts the "Known limitations at freeze" text below verbatim. The
solo check confirms that they are present as written here; it does not re-review their content and
they cannot re-open the loop. No fix adds a rule, a gate or a branch, except gate 14, which the
2026-09-28 decision requires.

### A fixes (blocking), exact edits

Every changed line carries "(amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch
on the leaking anchor bundles')".

- **A1. `code_sha` (frontmatter l. 9).** Replace "Code base = the anchor's regime-B bundle (f2107a04,
  `decisions.md` l. 80, or the re-frozen, uncommitted e90327d4, l. 28; the anchor PREFLIGHT addendum
  for patch 0027 fixes which) plus the Delta patch series" with: "Code base = the anchor's regime-B
  bundle **carrying the host-memory leak fix and the run_pack heartbeat fix** (`decisions.md`
  2026-09-28; anchor incident `review/INCIDENT_stall_20260928.md` §6), not yet frozen, plus the Delta
  patch series rebased onto it. f2107a04 and e90327d4 predate the fix and are not launchable
  (f2107a04 `bnhgq2/ablation.py:702` reloads a fresh model every epoch; STUDY arbiter v6)". Keep the
  rest of the field.
- **A2. Gate 11 (l. 451-453).** "**Code base** ([DK4], [DK13]; frontmatter): the leak-fixed regime-B
  bundle (gate 14) plus the Delta series, rebased from 77f1ca4e before this gate; f2107a04 and
  e90327d4 are not launchable. If anchor production ships on another sha, …" (rest unchanged).
- **A3. New gate 14** after gate 13: "14. **Host-memory growth canary** (`decisions.md` 2026-09-28;
  anchor incident §6): on the gate-11 bundle, one E and one A07 Delta cell run ≥ 30 epochs with the
  anchor's RSS gate (`BNJ_RSS_GATE_MB_PER_EPOCH` = 5) or W&B `system.proc.memory.rssMB`; host-RSS
  slope ≤ 5 MB per epoch per arm. If it fails, the wave waits. PREFLIGHT records the bundle sha and
  the result for E and A07 (the decision's Check line)." Gate 7 gets "(GPU memory; host memory is
  gate 14)".
- **A4. Gate 4 (l. 419-421).** Append: "Patch 0038 is rebased onto the anchor's `run_pack.py` fix
  (heartbeat age from the attempt start; no relaunch into a full cgroup; incident §4, §6) and
  `tests/test_run_pack_delta.py` passes on the rebased tree (`decisions.md` 2026-09-28)."
- **A5. PACK (l. 884-886) and Budget.** Replace "about 2 CPU and 6 Gi host memory per arm" with:
  "about 2 CPU per arm; host memory per arm ≥ baseline + slope × H (anchor incident §6 PACK-MEM):
  at the gate-14 limit of 5 MB per epoch and a 2.1-GB baseline, about 4.6 GB at H 500 (6 Gi
  suffices), 7.1 GB at H 1,000 and 12.1 GB at H 2,000 (rep-C, M032), so replica and long-horizon
  pods are sized at PREFLIGHT from the measured slope". Add one sentence after the wall-clock
  paragraph (l. 848-853): "The wall clock assumes gate 14 passed and no relaunch."
- **A6. Reference row "Anchor arm A" (l. 272).** After "is descriptive only": "; it was stopped
  2026-09-28T05:31Z for a host-memory leak of about 80-95 MB per epoch per arm (anchor `RUN.md`
  'Stopped 2026-09-28T05:31Z'; incident §2)".
- **A7. Change log v7 entry**, dated 2026-09-28: "fixer after STUDY arbiter v6 (ITERATE, 1 A):
  the 2026-09-28 leak decision carried into `code_sha`, gates 4, 7, 11, new gate 14, PACK, Budget and
  the Reference table; B wording corrections B1-B6; 'Known limitations at freeze' added (Kai's freeze
  rule)." Update the experiment-log stub's Design line to name gate 14. The orchestrator re-runs
  `tools/prose_lint.py`. `budget.py` is unaffected (no run count changes).

### B wording corrections (apply in the same pass; each replaces a false or stale sentence)

The fixer greps STUDY.md, `plan.md` and the stub for every site of each phrase and lists them in its
report as "changed" or "unaffected because …".

- **B1 (row 4). Label (l. 718-720).** Replace `otherwise "descriptive: recovery below 0.5 at this
  spread", citing …` with: `otherwise "descriptive: s_int above T, where at least one seed model gives
  recovery below 0.5", citing the recovery rows at the measured s_int (median g §19a Gaussian,
  §19b per-run mode; mean g §15, §18, §18b). Above T recovery can still exceed 0.5: 350k Gaussian
  0.50-0.55 up to 2.7 pt (§19a); per-run low mode, families with s_int > T, 5M 0.95 / 0.85 at q 0.05 /
  0.1 and 350k 0.89 / 0.61 / 0.54 at q 0.1 / 0.33 / 0.5 (§19b). n_low and the mode readout say which
  case applies; no rule reads them.` Same correction wherever "recovery below 0.5" appears.
- **B2 (row 5). [DK8] block (l. 1015-1016).** Replace "the ten-seed minimum absorbs it" with: "the
  ten-seed minimum absorbs the seed noise, not the floor: at the design seed the 350k median-g T is
  2.0 / 2.1 / 2.2 / 2.3 pt at floor 0.005 / 0.01 / 0.02 / 0.05 (mean g 1.9 / 1.9 / 1.9 / 2.0; critical
  v6 own check 1); a 350k s_int of 2.0-2.3 pt is labelled by the floor constant (Known limitations)".
  Add to ALTERNATIVES: "350k T 1.8-2.0 pt (mean-g or floor-0.005 value)".
- **B3 (row 6). G3 report (l. 672) and Ranking (l. 704).** After "median g and mean g" add "; the
  median with [min g_s, max g_s], the order-statistic interval, 87.5 % on the population median at
  n = 4 (75 % at n = 3)". Figures row (l. 926): "each bar's interval named" → "marker = median g with
  its order-statistic interval; mean g with its own-sd 95 % t-interval and the pooled '95 % at equal
  spread' interval, each named; per-seed points".
- **B4 (row 7). Rank-move fallback (l. 767-768).** Replace `labelled "companion disagrees at the null
  level"` with `labelled "rank-move flag not calibrated at this r (§19d)"`. [L6] (l. 981): after "are
  the check" add "; at 5M the rank-move flag is calibrated only at r ≥ 0.95, and below that the
  companions and the eligible-epoch count are the check".
- **B5 (row 3). Relaunch record.** Confounds, new item: "**Relaunch:** a run killed and resumed by
  `run_pack.py` restarts from its last 25-epoch checkpoint while its pair may have run
  continuously; recorded, not controlled." Readout per cell: add "relaunched (yes / no, epoch
  restored from) per run; a pair with exactly one side relaunched is marked". The placebo reading
  lists relaunches.
- **B6 (row 8). Rare high mode (l. 618-620).** Replace "q > 0.5 (a rare high mode …) is not simulated;
  the physics review's variant … not re-run here." with: "q > 0.5 (a rare high mode, the shape of the
  archived three values) is not in `screen_null.py`. Two review checks with the same model
  (`review/physics_v6_rarehigh.py`, seed 606; critical v6 own check 2, seeds 20260927 / 1 / 2) give,
  at 350k and T 2.1 pt, median-g recovery among draws with s_int ≤ T of 0.51-0.53 at q 0.6, 0.61-0.63
  at q 0.67, 0.77-0.87 at q 0.75-0.8 and 0.98 at q 0.9; mean g, the companion, 0.39 / 0.46 / 0.55 at
  q 0.67 / 0.8 / 0.9. At 5M (T 1.2 pt) the set is empty below q 0.9 and recovers 1.00 above. The
  median-g T holds under a rare high mode; the mean-g companion does not, so a median / mean
  disagreement mark (Ranking) is expected there. Review scripts, design arithmetic."

C items (rows 10-20): apply before commit where marked; no re-review.

### Known limitations at freeze (insert verbatim as a new section after [L8], before "Where I am not sure")

```
## Known limitations at freeze

Frozen under Kai's rule of 2026-09-28 (`decisions.md`): STUDY review round 6 left these as
Category B; they are disclosed, not fixed, and VERIFY reads every list with them.

- **K1. The 350k label threshold depends on a constant.** T = 2.1 pt is where
  P(s_int ≤ T | q 0.5) crosses the 0.01 floor, not where recovery crosses 0.5: T is 2.0 / 2.1 /
  2.2 / 2.3 pt at floor 0.005 / 0.01 / 0.02 / 0.05 (design seed). A 350k list with s_int between
  2.0 and 2.3 pt carries its label by that choice. Labels only; nothing that runs depends on T.
- **K2. The label reads a non-robust spread; the ranking is robust.** s_int counts every
  low-mode run; median g discards it. Under a per-run low mode a "descriptive" list can recover
  0.85-0.95 (5M) by median g (Label, §19b). A robust s_int (median-polish residuals, MAD-scaled)
  with T re-derived was not adopted.
- **K3. The primary has only an order-statistic interval.** Median g carries [min g_s, max g_s]
  (87.5 % at n = 4, 75 % at n = 3); the "95 % at equal spread" and own-sd intervals belong to
  mean g.
- **K4. The 5M rank-move flag is calibrated only at r ≥ 0.95** (§19d, m 37: null count 1.2 at
  T 15, r 0.9). Below that the companions and the eligible-epoch count are the winner's-curse
  check, and the absence of a flag is not evidence of no rank movement. Running the flag on
  mean-g ranks (T 10 / 15) was not adopted.
- **K5. The rare high mode is checked only by review scripts** (`review/physics_v6_rarehigh.py`;
  critical v6), not in `screen_null.py`; the median-g label holds there, the mean-g companion
  recovers 0.39-0.55.
- **K6. Relaunches are recorded, not controlled.** A resumed run replays from its last 25-epoch
  checkpoint; its pair may not have.
- **K7. v6 moved outcomes without changing rule text.** Scoring by median g raised the 350k T
  from 1.8 to 2.1 pt (looser) and left the 5M rank-move band 0.90-0.95 uncalibrated (was T 15).
```

## What Kai must decide (at the launch gate)

1. **Launch waits for a frozen, leak-fixed bundle.** The fix exists today only as uncommitted
   edits in the anchor's working tree (`code/tree/bnhgq2/ablation.py`, `ValidationReloader`,
   `RSS_GATE`, 2026-09-28 06:02Z). Delta cannot launch until the anchor freezes it into a bundle,
   gate 14 passes on E and A07 Delta cells, and patch 0038 is rebased. Launch gate 1 (the regime-B
   pilot's epoch-500 readout) cannot happen on f2107a04 either (incident §5).
2. **Replica and long-horizon pod memory** (fix A5): about 12 GB per arm for rep-C and M032 at the
   passing slope, against 6 Gi; fewer arms per pod or a larger limit, sized at PREFLIGHT. This may
   change the P = 10 packing and the wall clock; PREFLIGHT restates the Budget.
3. **350k label threshold** (K1): 2.1 pt as frozen, or the mean-g / floor-0.005 value 1.8-2.0 pt.
   Labels only.
4. **5M rank-move flag** (K4): median-g ranks as frozen, or mean-g ranks (calibrated at r ≥ 0.9).
5. **Carried from v5:** [DK16] extension (in band only; above T at 350k, 326 runs, 1,188.1 /
   2,034.9 pod-hours; or n = 6); no compute touchpoint at the replica gate (302 runs, 1,112.2 /
   1,959.0 pod-hours, 240 packable today); [DK18] 350k follow-up (84 runs, 366.5 pod-hours) or the
   slack label at K3; X5, the non-binary path under [A20]; carried defaults [DK1]-[DK5], [DK7],
   [DK9]-[DK16], [DK18]; [DK8] as amended v6. [DK6] (median g primary) and launch gate 1 are
   already Kai-decided.
