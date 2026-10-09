# STUDY constructive review, v7 (diff-scoped, iteration 7)

Campaign `campaigns/2026-09-26-training-batch/`. Artifact `STUDY.md` at 5c49230 (2,205 lines).
Scope, per `review/STUDY_arbiter_v6.md` ("v7 scope, binding"): check that fixes 1-11 landed as
written at every listed site, that fix 10's script and tests exist with a pass line, and that no
site was missed; also the text pass after PREFLIGHT gate v2 (change-log entry "v6, text pass",
l. 257-264). Diff `git diff 09e0d8c 5c49230 -- STUDY.md`. A new B only if an edited sentence is
itself wrong (a number, a sign, a contradiction with code). Reviewer: constructive-reviewer,
2026-09-27, fresh context. Read: arbiter v6, my v6, the diff, `PREFLIGHT.md` l. 135-205,
`.claude/memory/decisions.md` l. 1-40, `code/analysis/{attn_entropy,test_attn_entropy}.py`,
`code/evidence/pytest_shipped_77f1ca4e.log`, `code/tree/bnhgq2/wandb_util.py:58-86`,
`code/tree/bnhgq2/ablation.py:565-630`. Other reviewers' v7 output not read.

## Status of my v6 findings, by name

| v6 | finding | status | where (line numbers at 5c49230) |
| --- | --- | --- | --- |
| B1 | K=7 join gated on memory only | **Resolved** | Budget, FP32-E launch rule l. 1438-1446: K=7 re-canary with (i) memory, (ii) T_run ≤ 14 d at K=7, no K=6 scaling accepted, (iii) finite loss; K=8 clause; Overlap bullet (NB) l. 1409-1410; Kai rows l. 2020, 2022 (col. 3); [D26] DECISION l. 2112. Residual wording in the NB row's col. 4, C3 below |
| B2 | "at least \|U\|" off the unadjusted interval | **Resolved** | A − NB l. 981-982 ("only when U < 0 and the verdict below is 'falsified'; otherwise ... 'unadjusted 95 %'"); FP32-E l. 1053-1055 (same, 'resolved cost'). L > 0 branch now symmetric ("A exceeds FP32-E by at least L pt", investigator before REPORT) |
| C1 | Holm price unstated | **Resolved** | l. 975-978 |
| C2 | no plausibility check on FP32-E | **Resolved** (arbiter fix 4) | l. 1079-1083; epoch-500 print l. 1460-1462. One residual, C1 below |
| C3 | cost bullet "16 runs at K=4" | **Resolved** in substance | l. 1415. Residual, C2 below |
| C4 | duplicated splice at the `i_decay_speed` sites | **Resolved** | reference table rows, [D25] body, [A21] constraint: each now states patch 0024 and the PREFLIGHT re-assert once |
| C5 | Question presupposes the sign | **Resolved** | body l. 273; frontmatter `question:` l. 6 |
| C6 | stack the decomposition | Not applied (optional, per arbiter) | A − FP32-E and NB − FP32-E now share a panel separate from A − NB (l. 1156-1158), which carries most of the value |

Arbiter v6 fixes checked at every listed site: 1 (a) l. 828-830, (b) l. 986-997 and 1058-1068,
(c) l. 1076-1077; 2 as above; 3 claim string l. 1047-1050, Scope l. 324-326, Bearing l. 317;
4; 5 at l. 562-565, conventions row "Validation checks 1-4", [D26] body, [D26] DECISION, [A25]
pinned-0.1.9 bullet; 6 at [A22], [A25], conventions row; 7, 8, 9 as prescribed; 10 [A26] l.
1942-1951, "softmax tap" replaced, pilot "pending" clause; 11 all required C items. No listed site
missed (grep for "memory fits", "and memory", "no quantizer variables in any layer", "softmax
tap", "16 runs at K=4" outside history, "how far is A below": none left in live text).

## Category A

None. No selection on held-out, no projection stated as a result, no tautological comparison. The
text pass after PREFLIGHT gate v2 changes no arm, seed, target or selection rule.

## What is done well (keep)

- [+] **[A26] exists, is tested, and says what it cannot see.** `code/analysis/attn_entropy.py`
  (322 lines) and `test_attn_entropy.py` (176 lines) cover three builds, A, C′ and an fp32
  skeleton (`quant.weight "none"`), through save and reload: uniform logits give 1 within 1e-6,
  one-hot logits give < 1e-6, plus a `main()` run on the epoch-500 snapshot layout. Pass lines:
  staged, 7 passed and 2 skipped (`PREFLIGHT.md`); shipped bundle 77f1ca4e, `71 passed, 2
  skipped` (`code/evidence/pytest_shipped_77f1ca4e.log:73`; both skips are the C′ `main()` case,
  `test_attn_entropy.py:142`). The script records that the model has no attention mask
  (`attn_entropy.py:25`), which is the honest statement (see C5).
- [+] **Fix 3's branches carry the right signs.** L ≤ 0 → "cost at most |L|"; L > 0 → "A exceeds
  FP32-E by at least L" and an investigator hand-off; "close" is never a verdict (claim string,
  Scope, Bearing). A reader now takes away an interval, not a word.
- [+] **Survivor bias is priced into the headline**, not only admitted in prose (l. 828-830,
  986-997, 1058-1068), and A against FP32-E gets its own feasibility counts with exact McNemar.
- [+] **K=7 join now needs a measurement**, and "no scaling of the K=6 s_e is accepted in place of
  (ii)" closes the obvious shortcut. The primary arm's run length is protected.
- [+] **CPU→GPU certification rule** (l. 1288-1296) matches `decisions.md` l. 10-25 condition for
  condition; one retry, allowed only when `stored_ebops == logged_ebops`, reported in RUN.md and
  VERIFY.md. Pre-registered before any readout, so it is not a forking path.
- [+] **Stage-aware run id matches code and does not break resume.** `stage_run_id` hashes
  `stage + NUL + name` (`wandb_util.py:74-78`); checkpoints resume from the `out` directory
  passed to `run` (`ablation.py:567, 581`), not from the run id, so "a production run resumed
  from a pilot checkpoint opens a new production-stage W&B run" is true and the pilot → production
  hand-off still finds its checkpoint.
- [+] **Gate arithmetic checks.** "`PREFLIGHT_ALL_PASS 66 production 64 pilot_only 2` (58 and 56
  now, plus FP32-E's 8)" against `code/evidence/cpu_gate_d25.log:119` (58 / 56 / 2).

## Category B

Three, each one clause; none touches an arm, seed, target, selection rule, or the running pilot.
B1 and B2 are in arbiter v6 fix 1's prescribed text; as the arbiter did for its own v5 wording at
v6 #5, they are listed to be fixed, not closed by citation.

### B1. The imputation pair count omits seeds that fail in both arms

- **Current state.** A − NB headline (l. 993-994) and precision-package headline (l. 1063-1064):
  "partner-only failures stay excluded; the interval is recomputed over the 8 − (partner-only)
  pairs."
- **Problem.** A seed with no accuracy number in either arm is neither A-only nor partner-only,
  so it is counted inside "8 − (partner-only)" but has no partner value to pair with. The stated n
  is wrong whenever a seed fails in both arms (reachable for A − NB: both arms run under the same
  PID at 350k).
- **Improved state.** "... recomputed over the 8 − (partner-only) − (both-failed) pairs; seeds
  failed in both arms are excluded and counted beside it."
- **Why.** The n printed beside an interval has to be the n it was computed on.
- **Effort.** Low (one clause, two sites).

### B2. "Worst-case imputation" mislabels a surviving-minimum imputation

- **Current state.** l. 996 and l. 1066: "labelled 'worst-case imputation, not a measurement'",
  two sentences after "the surviving-A minimum is used ... because it is the least extreme value
  that does not assume a failed binary seed did better than every surviving one."
- **Problem.** A failed seed's accuracy is unbounded below (a degenerate or infeasible binary seed
  can sit far under the surviving minimum; Round 14 had 67.18 % beside 72.64 %). The label tells a
  reader the sensitivity line bounds the damage, which it does not; the misreading favours the
  thesis. The paragraph contradicts itself ("least extreme" vs "worst-case").
- **Improved state.** "labelled 'surviving-minimum imputation, not a worst case and not a
  measurement'".
- **Why.** Honest framing of the one number that prices survivor bias.
- **Effort.** Low (label text, two sites).

### B3. W&B canary group stated for wave 1 only; code appends to the config's group

- **Current state.** l. 1476-1477: "pilot and canary log into `chang-n64-20260926-canary`,
  production into the config's group."
- **Problem.** `stage_group` returns `group + "-canary"` for pilot and canary
  (`wandb_util.py:62, 81-86`), so a wave-2 config (group `chang-n64-20260926-wave2`) logs its
  canary to `chang-n64-20260926-wave2-canary`, as l. 1469 and l. 1419 say. The new sentence,
  read literally, contradicts both the code and those lines for every second-wave canary run.
- **Improved state.** "pilot and canary log into the config's group with `-canary` appended
  (`chang-n64-20260926-canary` for wave 1, `chang-n64-20260926-wave2-canary` for wave 2),
  production into the config's group."
- **Why.** The sentence is what the RUN owner will check W&B against.
- **Effort.** Low.

## Category C

- **C1. Plausibility trigger needs an exit criterion.** l. 1079-1083 withholds A − FP32-E "until
  the cause is found or ruled out" when FP32-E's validation seed-mean is below A's or below
  79.4 %. The 79.4 % limb compares a validation mean on our gated 90/10 split against a
  single-model test number on Sun et al.'s split, and FP32-E is a small model (E: 6,253 trainable
  kernel, bias and PE entries, `PREFLIGHT` / reference table); a sound FP32-E can sit below it, so
  expect this limb to fire. Pre-register what "ruled out" means (for example: training curves
  plateaued, selection epoch not at a boundary, [A25] pairing and `y` checks pass; the report then
  prints A − FP32-E with the trigger and the investigation's outcome beside it). Otherwise this is
  arbiter #6, closed. Low.
- **C2. Cost bullet pod-hours.** l. 1415: "16 runs at K=4 on 4 pods (24 runs at K=6 with FP32-E,
  same pods) ≈ 4 × 218.9 h ≈ 876 pod-hours" places the K=6 run count inside a figure computed at
  K=4 s_e. Label it "≈ 876 pod-hours at K=4; K=6 raises s_e (FP32-E below)". Low.
- **C3. NB Kai row, last column.** l. 2022 col. 3 carries fix 2; col. 4 still reads "decided at
  the canary" and "K=8 does not fit" (memory-only wording the Budget text replaced at l. 1445).
  "decided at the K=7 re-canary"; "a K=8 re-canary does not pass (i) to (iii)". Low.
- **C4. Stale pointers.** (a) l. 1470-1471 keep "The runner's run id is sha256(config
  name)[:12]" directly before the amendment that replaces it; strike or mark "superseded". (b)
  l. 800 and l. 1289 cite "the top of `.claude/memory/decisions.md`"; that file is newest-on-top, so cite the
  entry's heading and date. (c) The change-log "v1, revised after arbiter v6" line numbers
  (l. 218-256) were taken at 99f0a2d; the PREFLIGHT text pass shifted the file (e.g. A − NB
  headline now l. 982-997). Low.
- **C5. Entropy reading under zero-padding.** `attn_entropy.py:25`: no attention mask, so
  zero-padded constituents are attended keys with identical logits. Under the pT ≥ 2 GeV gate many
  jets have far fewer than 64 real constituents, so the normalised entropy is pulled toward 1 by
  the padding fraction, and the reading "near 1 means uniform attention, a Deep Set" (l. 1118)
  is confounded. Add a companion line from the same forward pass restricted to real query rows and
  real keys (probabilities renormalised over real keys, divided by log n_real, jets with
  n_real ≥ 2), and print the mean n_real per arm. Descriptive only; blocks nothing. Low-medium.
- **C6. "`main()` has never run end to end"** (l. 1299-1300) reads as either script; the test log
  shows `attn_entropy` `main()` ran on the A build. Name `certify_ebops.main()`. Low.
- **C7. Readout bundle sha.** l. 1300-1301 allow a new bundle for the readout Job only; RUN.md
  and VERIFY should then record both shas (training code, certification code) beside each
  certification. Low.

## Disputed facts for the investigator

None. The one code question raised in this pass (does the stage-aware run id break the pilot →
production resume?) was traced: no (`ablation.py:567, 581`).

## Recommendation to the arbiter

No A. All eight v6 findings resolved (C6 optional, not applied); fixes 1-11 present at every
listed site; [A26] script and tests exist with pass lines on the shipped bundle. Three one-clause
B: B1 (both-failed seeds missing from the imputation pair count) and B2 ("worst-case" label on a
surviving-minimum imputation), both in fix 1's text and governing VERIFY wording; B3 (canary
group sentence contradicts `wandb_util.py` for wave 2), governing W&B bookkeeping. None bears on
the running pilot or on wave-1 production composition. Seven C, all low.
