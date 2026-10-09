# STUDY frozen check: 2026-09-27-delta-screen (solo critical-reviewer, after fixer v6)

Critical-reviewer, solo mode, fresh context, 2026-09-28. Scope set by `review/STUDY_arbiter_v6.md`
l. 172-184: check only the A1-A7 edits; confirm B1-B6 and K1-K7 are present as written, with no
re-review of their content. Artifact: `STUDY.md` at HEAD 0e4a502 (working tree clean for this
campaign, `git status --short` empty). Diff base: 73237cb (arbiter v6 commit).

VERDICT: FROZEN (Kai's rule): PASS with disclosed limitations

## Evidence

`git diff 73237cb -- campaigns/2026-09-27-delta-screen/STUDY.md`: 22 hunks, +119 / -23 lines
across the campaign (STUDY.md 119 changed lines). Every hunk maps to an arbiter item:

| item | STUDY.md (edited lines) | check |
| --- | --- | --- |
| A1 `code_sha` | l. 9 | Arbiter text verbatim: "carrying the host-memory leak fix and the run_pack heartbeat fix ... not yet frozen ... f2107a04 and e90327d4 predate the fix and are not launchable (f2107a04 `bnhgq2/ablation.py:702` reloads a fresh model every epoch; STUDY arbiter v6)" plus the amendment tag; the rest of the field is kept (delta.json sha f4ad2571…, anchor git refs unchanged). Resolves: the named bundles are non-launchable |
| A2 gate 11 | l. 462-466 | "the leak-fixed regime-B bundle (gate 14) plus the Delta series, rebased from 77f1ca4e before this gate; f2107a04 and e90327d4 are not launchable" + tag; the "If anchor production ships on another sha" remainder is unchanged |
| A3 gate 14 | l. 471-476 | After gate 13 as specified: ≥ 30 epochs, one E and one A07 Delta cell, `BNJ_RSS_GATE_MB_PER_EPOCH` = 5 or W&B `system.proc.memory.rssMB`, host-RSS slope ≤ 5 MB per epoch per arm, "If it fails, the wave waits", PREFLIGHT records the bundle sha and the E / A07 result. Threshold and scope stated. Gate 7 carries "(GPU memory; host memory is gate 14 …)" l. 441-443 |
| A4 gate 4 | l. 431-434 | Patch 0038 rebased onto the anchor `run_pack.py` fix (heartbeat age from attempt start; no relaunch into a full cgroup; incident §4, §6); `tests/test_run_pack_delta.py` passes on the rebased tree; tag |
| A5 PACK / Budget | PACK l. 921-927; Budget l. 887-889 | "about 2 CPU and 6 Gi host memory per arm" is gone (grep "6 Gi" in STUDY: one site, l. 923, "(6 Gi suffices)" at H 500 only). Per-horizon values 4.6 / 7.1 / 12.1 GB at H 500 / 1,000 / 2,000; recomputed by running `python3 budget.py`: last line "PACK-MEM host memory per arm at baseline 2.1 GB + 5 MB/epoch x H (6 Gi = 6.44 GB): H 500: 4.6 GB; H 1,000: 7.1 GB; H 2,000: 12.1 GB". Arithmetic: 2.1 + 0.005 × 500 / 1,000 / 2,000 = 4.6 / 7.1 / 12.1. Wall-clock sentence "assumes gate 14 passed and no relaunch" present |
| A6 Reference row | l. 277 | "it was stopped 2026-09-28T05:31Z for a host-memory leak of about 80-95 MB per epoch per arm (anchor `RUN.md` 'Stopped 2026-09-28T05:31Z'; incident §2)" + tag |
| A7 change log v7 | l. 207-211 | Arbiter text plus one added clause naming the two new prints (`screen_null.py` §19e, `budget.py` PACK-MEM). Experiment-log stub (`.claude/memory/experiment-log.md` l. 13) Design line names gate 14, the 5 MB threshold, E and A07, ≥ 30 epochs and the non-launchable bundles |
| B1 Label | l. 748-753 | Matches arbiter text; "recovery below 0.5" as a label: 0 remaining sites in STUDY.md / `plan.md` |
| B2 [DK8] | l. 1087-1090; ALTERNATIVES l. 1094-1095 | Matches; adds "`screen_null.py` §19e" as source. §19e output (`review/fixer_v6_screen_null_out.txt` l. 464): 350k median g 2.0 / 2.1 / 2.2 / 2.3, mean g 1.9 / 1.9 / 1.9 / 2.0, as the text says. "absorbs it": 0 sites left |
| B3 interval | G3 l. 698-699; Ranking l. 729-731; figures row l. 967 | Present as written |
| B4 rank-move | l. 801; [L6] l. 1022-1024 | Present; "companion disagrees at the null level": 0 sites in STUDY, one in `plan.md` l. 229 tagged "[superseded v7]" |
| B5 relaunch | Confounds 12 l. 570-571; placebo l. 789; readout l. 812-813 | Present as written |
| B6 rare high mode | l. 639-647 | Arbiter text verbatim |
| K1-K7 | l. 1033-1059 | Inserted verbatim after [L8], before "Where I am not sure" (diff line-by-line against arbiter v6 l. 272-298: identical) |

No hunk outside these items; no rule, gate or branch added beyond gate 14 (§3 of the brief holds).

## Notes (not findings)

1. The anchor tarball `campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz` now
   hashes `ceb174db4809a94a…e821` (recomputed with `shasum -a 256`), staged per the 2026-09-28
   ml-engineer entry, not PREFLIGHT-pinned and not yet through gate 14. STUDY leaves `code_sha`
   "not fixed … not yet frozen", with the sha recorded at PREFLIGHT, which is correct. The same
   ml-engineer entry keeps 6 GiB per arm; that agrees with A5 only at H 500. PREFLIGHT must use the
   A5 per-horizon values for rep-C and M032.
2. `prose_lint` on STUDY.md scores 6 (fixer report): the word "robust" ×3 in K2, which is the
   arbiter's verbatim text. The orchestrator decides.
3. Cosmetic (C, not blocking): in A1 the kept remainder ", on the regime-A pilot bundle 77f1ca4e
   today and rebased onto the regime-B bundle" follows "rebased onto it" and repeats it. C rows 10-20
   were not applied (fixer scope); lines > 150 characters remain at l. 707, 729.
