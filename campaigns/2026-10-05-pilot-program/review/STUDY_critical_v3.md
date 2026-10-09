R1 launch: PASS (no A; conditional on L1 GATE_RESULT PASS of kai-pilot1005-cpugate-98dd28, L2 arbiter v3 PASS, L4 byte rule at submission). STUDY: PASS with three B text fixes, none of which touches a launched byte.

# STUDY critical review v3: pilot program, 2026-10-06

Reviewer: critical-reviewer, STUDY panel, iteration 3 (06-review §6.5). Scope from
`review/STUDY_arbiter_v2.md` Question 4: every v2 A/B by name, the P4 grep (PREFLIGHT L3),
agreement of everything that binds the R1 launch, and the readout-blocking register. Read-only;
this file is the only one written.

Inputs (sha256 recomputed):
- `STUDY.md` `11005dfb3c3df956…eac44` (435 lines, [A4] 06:13 JST; JOURNAL:46). Pre-[A4] copy
  `study-history/STUDY_pre_A4_0613.md` (= v2's `95c9b61f`).
- `protocol-r1.json` `62a50e14…fc9a` (file). `lab_check_protocol` against snapshot
  `local/jev-protocols/123d3654….json`: protocol sha `50e9eaac…11bc`, `structural_valid true`,
  findings [], drift [], `matches_snapshot true`.
- `PREFLIGHT.md` `5448a4e3…ae23` (§3c added 06:14, JOURNAL:45).
- `PROGRAM.json` `cca098b1…1dee`: unchanged since v2 (expected; Q1-Q7 are Kai's).
- `PREPARED.json` `325c38b8…cc5d`; `manifests-98dd28/pilot1005-code.tar.gz` sha256 = `98dd2875…0059`.
- Cluster: `kubectl get job kai-pilot1005-cpugate-98dd28 -n cms-ml` = Running 0/1 at the time of
  this review. No GATE_RESULT. L1 is open.

## 1. v2 A and B findings, by name

### STUDY_physics_v2

| finding | status | evidence |
| --- | --- | --- |
| A1 healthy has no accuracy content | **resolved** (rule) | STUDY:175-181 healthy adds `best_feasible_val_acc ≥ 0.50`, one definition for r1, bracket, r_rec, W, V_bin, leads, controls, early stop; :197-200 "attentive, low-acc" and the four-class partition (checked: the four classes partition complete ∧ feasible ∧ non-degenerate rows on acc ≥/< 0.50 × entropy </≥ 0.95); :274-277 W adds mean acc before entropy; "Accuracy is not a criterion" absent (grep 0 hits); :327-328 early stop; protocol `selection.health`. Descriptive half: Q/K 0-bit fractions → arbiter Q2 (open, before readout); softmax zero-entry fraction → R1 VERIFY (arbiter deferral; not written in STUDY §15, C3) |
| B1 attention not shown to cause the loss | **resolved** (text); control deferred | STUDY:229-231; §15 :424-425 |
| B2 E-unc-C under-specified / circular | **resolved** | STUDY:145 (PID target 100,000,000, live controller); :249-253 judged without entropy, "E cut uncalibrated" under §10.2; :342-343; protocol stop rule 3. Headroom 100,000,000 − 171,526 = 99,828,474 (PREFLIGHT §3c row) ✓ |
| B3 transient best checkpoint | **resolved** as ruled | STUDY:205-207. Field names exist in the frozen diag: `cost_split.epoch` (`freeze_p.py:173`), `last_epoch` (`:186`) |
| B4 production seeds overlap | open by design → Q10 / K-c (production) | STUDY D8 :412-413 unchanged |
| B5 no csynth guard | open by design → Q9 / K-d (production) | STUDY:83-84 states no DSP/LUT claim rests on the program |

### STUDY_critical_v2

| finding | status | evidence |
| --- | --- | --- |
| A1 STUDY/protocol say w150 | **resolved** | STUDY:141 row 6 `A350-C-w100`; :150-151 D3 recorded; :239, :242-244 H4/time-limited for w100; :274 W order; :402-404 D3. Protocol diff vs `study-history/protocol-r1_pre_A4_0613.json`: groups/names → `A350-C-w100`, `pid_warmup` 150 → 100 (2 arms). Remaining `w150` tokens are annotated history only (§2 below) |
| B1 "6 h" deadline | **resolved** | STUDY:360, :368-371; protocol stop rule 5. No "6 h" in STUDY or protocol (grep) |
| B2 fresh-seed rule not machine-encoded | open → Q6 (PROGRAM, Kai), binds before R2 readout | PROGRAM unchanged |
| B3 6/8 early stop unowned | open → Q8 (production) | — |
| B4 `r23_bundle_gate` waits silently | open → Q4 (PROGRAM, Kai), before R1 readout. STUDY side already stops (§7 :264, §10.4 :344-345) | — |
| B5 disruption outside worst case | **PREFLIGHT half resolved** (§3c "Spend bound", PREFLIGHT:448-473, orchestrator named as checker at :472); PROGRAM half open → Q7 (`caps.r1_worst_case` still has no caveat, PROGRAM.json `caps`) | — |
| B6 PROGRAM job/handoff refs | open → Q3. Verified still stale: `job_names` `kai-pilot1005-r1-*-98dd28`, `pods_requested: 23`, `r1_readout` PLACEHOLDER (PROGRAM.json:632-637). Does not bind the manual launch | — |
| B7 R3 when Prec cannot qualify | **resolved** in STUDY:286-287 and protocol stop rule 7; PROGRAM mirror → Q1 | — |

### STUDY_constructive_v2

| finding | status | evidence |
| --- | --- | --- |
| A1 controller-error field empty | **definition resolved** (STUDY:210-215, protocol `outputs`); implementation → Q2 or VERIFY recompute | descriptive, never a rule input |
| B1 PREFLIGHT deadline text, A07 margin | **resolved** | PREFLIGHT §3c deadline 20,800 s and A07 margin; STUDY:368-371 |
| B2 a26 on epoch-0475 | open → Q2 | not in STUDY §5 diag list (C3) |

### PREFLIGHT_critical_v2

| finding | status | evidence |
| --- | --- | --- |
| B-new-1 PREFLIGHT does not describe the frozen set | **resolved** | §3c (PREFLIGHT:368-497). The 24 Job/rh-ID rows equal `PREPARED.json` `jobs` (24/24, scripted). Readout `rh-deccad51…` at 43,200 s matches the readout `job.json`. Gate rh-c11b0c23 named |
| B-new-2 bound omits terms | **resolved** | §3c: 143.87 GPU-h + pull/init on retried arms + init-hang + disruption replacements, counted against the cap; checker named |
| B-new-3 STUDY w150 | **resolved** (= crit A1) | above |
| L1 gate PASS | **open** | Job Running 0/1 |
| L2 STUDY arbiter PASS | open (arbiter v3) | — |
| L3 B-new-1/2 in PREFLIGHT | **met**, with residue in PREFLIGHT §4 (B-v3-3) | §2 below |
| L4 gate-cleared re-prep byte rule | at submission | — |
| L5 readout | before readout | — |

## 2. P4 grep (PREFLIGHT L3)

`grep -nE '21,?600|149\.2'` over PREFLIGHT.md, STUDY.md, protocol-r1.json: hits only at
PREFLIGHT:264, :298, :310, :313-327 (struck through or inside the "Superseded" banners), :361-362
(fenced block headed `# SUPERSEDED, not run`), :370 and :398 (§3c, describing what it replaces).
No live occurrence. **Pass.**

`w150`: STUDY:22, :42 ("w150 (w100 since [A4])", "he did, K1, [A4]") and :151 ("no w150 config
exists") are annotated. protocol-r1.json:246, :272 are `reason` strings "w100 replaces w150".
PREFLIGHT:208-209 sit under the §3 "Superseded" banner (:132-135); PREFLIGHT:304 is the 0043
history row. **One live residue: PREFLIGHT:523** (§4 P7 "H4 warmups 50 and 150 … A w150 arm has
350 epochs"), unannotated. See B-v3-3.

## 3. What binds the R1 launch: agreement

Scripted over `protocol-r1.json` `arms`, `code/tree/campaigns/pilot1005/index.json` + the 24
config files (each config sha256 equal to its index `config_sha256`), `PROGRAM.json`
`r1_launch.runs` and `PREPARED.json`.

| item | STUDY | protocol | configs / index | PROGRAM | PREPARED / job.json | agree |
| --- | --- | --- | --- | --- | --- | --- |
| arm × seed set | §4, 24 pods | 24 arms | 24 | 24 runs | 24 GPU jobs | **yes**, identical (arm, seed) sets |
| arch, budget, (c), warmup per row | §4 | per arm | index + config (`pid.target_ebops`, `pid_input`, `pid.warmup`, `experiment.seed`) | per run | — | **yes**, 24/24 |
| w100 | :141 | `pid_warmup` 100 | `pid.warmup` 100 (rows 16-17) | 100 | jobs `…-w100-s{1,2}-98dd28` | **yes** |
| weights / floor | §4 rows 7-9 | NB `kbi_learnable`, qkv1 floor q,k,v 1 bit | NB `kbi_learnable`; qkv1 `{bits 1, sites [q,k,v]}`; others `binary_absmean`, no floor | — | — | **yes** |
| A07 arch | d32, 4 heads | A07 | `d_model` 32, `n_heads` 4 | A07 | — | yes |
| epochs / batch / LR | 500, 2,790, 3e-3 | 500, 2790, 0.003 | config `epochs` 7000, stopped by `run_pack.py "$PACKS" 500` (PREFLIGHT critical v2) | — | — | yes |
| pod deadline | 20,800 s (:360) | 20,800 s | — | `caps.pod_deadline_s` 20800 | `options.pod_deadline_s` 20800 ×26; 24 GPU `job.json` pod `activeDeadlineSeconds` 20800, `backoffLimitPerIndex` 1; every `job.json` sha = PREPARED `job_json_sha256` | **yes** |
| caps 144/60/18, ≤ 24 pods | §11 | stop rule 5 | — | `max_gpu_hours_per_round`, `max_pods` 24 | — | yes |
| worst case | — | — | — | 143.87 | 24 × 21,580 s / 3,600 = 143.867 ✓ | yes |
| bundle | "assigned at PREFLIGHT" | — | — | `bundle_sha256` 98dd2875… | `bundle_sha256` 98dd2875…; tarball sha256 98dd2875… | yes |
| GPU product | RTX 3090 | — | — | RTX 3090 | RTX 3090 | yes |

Numbers re-traced in [A4] text:
- 0.25 · (1 − 0.75^5) = 0.19067 → "0.1907" (STUDY:224) ✓.
- 20,800 − 300 − 420 = 20,080; − 19,400 = 680 (3.4 % of 20,080); − 15,425 = 4,655 (STUDY:368-370) ✓.
- First feedback 110 for w100 s1/s2: `evidence/final-tree-98dd28/cpu_gate.log:72,76`
  (`first_feedback 110 span 10`); 500 − 110 = 390 ✓ (local, not quotable, as labelled).
- b5 first epoch meeting (a): A-s1 389, A-s2 299, D-s1 259; C′-s1, E1-s1 none
  (`rules-b5.txt:13, :56, :116, :179, :227`) → "259-389" ✓.
- 0.320871 / 0.405371: `recovery/readout-preparation/VERIFY.md:116-117` ✓ (phys C4 closed).
- 368,134 / 619,198 / 12,362,587 / 8,913,043: `dev/README.md:70-71`; NB init text :75-77 ✓ (crit C2 closed).
- `FlooredKIF.f` = max(…, f_floor): `qat.py:378-379` ✓.
- Expected spend 105-132 GPU-h (PREFLIGHT §3c): 24 × (15,425 + 300)/3,600 = 104.8; 24 × (19,400 + 300)/3,600 = 131.3. "132" rounds up by 0.7 (C).

## 4. Items deferred to before the R1 readout: are they registered as blocking?

| item | registered where | blocking the readout? |
| --- | --- | --- |
| Q1 PROGRAM mirror of healthy (+ R3 seeds 2-4) | STUDY:60-61 ("Until it lands STUDY governs, and `r1_decide` does not run on the unmirrored PROGRAM (its readout handoff is a placeholder, §10.8)"); JOURNAL:44 | **Governance: yes.** Mechanism: only while `r1_readout` is a PLACEHOLDER. Q3 fills that placeholder, so if Q3 lands before Q1 the stated guard disappears (B-v3-1) |
| Q2 readout re-prep (controller error, epoch-0475 a26, Q/K 0-bit fractions) | STUDY:215 names it only as one of two sources ("re-preparation (arbiter Q2) **or** a VERIFY recompute"); JOURNAL:44 | **Not registered as blocking** in STUDY or PREFLIGHT. PREFLIGHT §3c readout paragraph still names `rh-deccad51` as the readout (B-v3-1) |
| Q3, Q4 (PROGRAM fills, `r23_bundle_gate` timeout) | arbiter v2 table; JOURNAL:44 ("PROGRAM.json batch Q1–Q7 deferred to before the R1 readout") | Q3 is enforced by PREFLIGHT L5 ("with PROGRAM `r1_readout` filled", §3c readout paragraph) and STUDY §10.8. Q4 is backstopped by STUDY §10.4 |
| Q5 R2/R3 configs-only bundle (F9) | STUDY §7 :258-264 and §10.4 :344-345; protocol stop rule 4 | **Yes**, a registered stop |
| Q6, Q7 | arbiter v2 (bind before R2 readout / R2 launch) | not R1-readout blockers by the arbiter's own table |

Arbiter v2 (Question 3) requires that STUDY say it governs until the mirror lands: **it does**
(STUDY:60-61).

## 5. Jev

`jev_check_claims`, audit `jv-9f892dd894fa4ad3b9786bfa945358d2` (jev-1.13.0; advisory, thresholds
"heuristic; not validated on lab data"):

| id | claim (cited source) | Jev | by hand |
| --- | --- | --- | --- |
| c1 | STUDY:315-316 "Chang's pipeline zeroes constituents with pT < 2, so the inputs differ" (`docs/chang-vs-bnjettag.md:138-154`) | supported 0.80, suggestion | **refuted for this program.** The doc's "none" column is BNJetTag R14. All 24 R1 configs set `arch.pt_gate_gev: 2.0` (scripted; origin `campaigns/chang0926/generate.py:116` [D7]); the cache applies it (`prepare_cache.py:119-122`) and the runner asserts it against `data_info` (`run_engram.py:191-193`). The pilots use the same pT < 2 GeV gate and the same 558k/62k split. B-v3-2 |
| c2 | STUDY:141 w100 first feedback epoch 110, 390 epochs left (`cpu_gate.log:72-76`) | overstated 0.15, review | supported: log reads `first_feedback 110`; 390 is arithmetic |
| c3 | STUDY:77 A-s2 0.320871, D-s1 0.405371 (`VERIFY.md:114-117`) | overstated 0.41, review | supported: values exact on `model_best` rows; "weak" is the STUDY's reading, against the 0.50 floor |

`lab_check_protocol`: `matches_snapshot true` against 123d3654 (protocol sha 50e9eaac), no findings.

## A

None.

## B (text only; no launched byte changes)

- **B-v3-1. The R1-readout blockers are not registered in the operative documents.**
  STUDY:60-61 ties the Q1 guard to the PLACEHOLDER, which Q3 removes. Q2 is not a blocker in
  STUDY (:215 offers a VERIFY fallback) or PREFLIGHT §3c (which still names `rh-deccad51` as the
  readout). Fix (one sentence, experiment-designer or ml-engineer):
  - STUDY [A4] and PREFLIGHT §3c readout paragraph: "The R1 readout Job is not submitted until
    arbiter v2 Q1-Q5 have landed. The readout is a Q2 re-preparation, not `rh-deccad51`, unless
    Kai rules otherwise."
  - Or bind Q1 and Q3 into one PROGRAM edit, so the placeholder is never filled without the
    mirror.

  This needs no review loop. Landing it before launch costs minutes and keeps the constraint
  pre-data. It does not gate the launch.
- **B-v3-2. STUDY:315-316 misstates the input difference from the external reference.** The
  pilots apply the same pT < 2 GeV gate (c1 above). Fix: replace "Chang's pipeline zeroes
  constituents with pT < 2 (:150), so the inputs differ" with "The pT < 2 GeV gate and the
  558k/62k split are the same as Chang's (`arch.pt_gate_gev` 2.0, chang0926 [D7]). The
  differences are learned-width weights and 7,000 epochs." This sentence is context in §9 and no
  rule reads it, so it does not gate the launch. Fix it before Kai sees any production readout.
  The error came from v2 crit C3 (my predecessor's note), which the arbiter adopted as P2(i).
- **B-v3-3. PREFLIGHT §4 still describes the superseded build.**
  - :523 P7 "H4 warmups 50 and 150" is the one live w150 (§2).
  - :507-510 P2 reads "no activeDeadlineSeconds on the 23 GPU Jobs … 6 h".
  - :536-537 P11 reads "23 arms … 8 h deadline".
  - :540-545 "Open before any launch" lists items that are closed or moved.

  Fix: one "Superseded by §3c" banner over §4, or per-item notes. This is ml-engineer text. It is
  the remainder of L3 and should land before submission.

## C

- **C1.** STUDY:163 cites `PREFLIGHT.md:519` for the threshold 0.2109624456315518. §3c moved the
  lines, and :519 is now §4 P5/P6. The value appears at PREFLIGHT:156 and :246; cite the
  derivation source instead.
- **C2.** STUDY:194, :197 write the band as "(0.2110, 0.50)", but non-degenerate means
  > 0.2109624456315518. A row in (0.21096, 0.2110] falls in no named class. Write the band as
  "(threshold (c), 0.50)".
- **C3.** Two descriptive items the arbiter placed are not written in STUDY: the softmax zero-entry
  fraction (deferred to R1 VERIFY) is absent from §15, and the Q/K 0-bit fraction and epoch-0475
  a26 (Q2) are absent from the §5 diag list.
- **C4.** PREFLIGHT §3c gives expected spend as "105 to 132". The computed range is 104.8-131.3.
- **C5.** PROGRAM.json is still unsigned with `mode dry-run`. Its F7-era residue is Q1, Q3, Q4,
  Q6 and Q7. This is expected and does not bind a launch under Kai's direct order (JOURNAL:43).

## Verdict

**R1 launch: PASS.**
- Every v2 A is resolved in STUDY and protocol text: crit A1 / B-new-3 (w100), phys A1 (rule),
  and cons A1 (definition).
- Every v2 B that was due before launch is resolved. These are crit B1, B7, B5 (PREFLIGHT half),
  phys B1-B3, cons B1, B-new-1 and B-new-2.
- The rest are open by design and bound to the R1 readout, R2 or production, per the arbiter v2
  Fix list B.
- STUDY, protocol (snapshot-matched), the frozen 98dd2875 configs, PREPARED.json/job.json and
  PROGRAM.json agree on all 24 arms, w100, seeds, budgets, 20,800 s and the caps.

The PASS is conditional on:
- L1, `GATE_RESULT PASS` (the gate is still running);
- arbiter v3;
- the L4 byte rule at submission.

B-v3-1 to B-v3-3 are text only, under about 0.3 agent-h in total, and need no re-review. B-v3-1
and B-v3-3 are best landed before submission. B-v3-2 must land before any production readout
reaches Kai. No new A, so there is no escalation.
