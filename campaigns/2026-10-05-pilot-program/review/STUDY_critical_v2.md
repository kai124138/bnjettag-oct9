ITERATE

# STUDY critical review v2: pilot program, 2026-10-05

Reviewer: critical-reviewer, STUDY panel, iteration 2 (06-review §6.5). Written 2026-10-06 JST.
Read-only. Nothing in the campaign was edited except this file.

Inputs (hashes recomputed):
- `STUDY.md` sha256 `95c9b61f…7294` (379 lines, [A3] 14:35 JST; matches JOURNAL:37).
- `PROGRAM.json` sha256 `cca098b190cda920…1dee` (1,853 lines; F7 edit, JOURNAL:41).
- `protocol-r1.json` sha256 `b75e2beb…21d3`. `lab_check_protocol`: protocol sha `57e6aa0e…6a4c`,
  `structural_valid: true`, no findings, `matches_snapshot: false` (no frozen snapshot yet, expected).
- `review/STUDY_{arbiter,critical,physics,constructive}_v1.md`, `JOURNAL.md`, decisions.md
  2026-10-05 15:21 (K1-K4) and 10:08, `PREPARED.json`, `manifests-98dd28/*-job.json`,
  `PREFLIGHT.md` §3b, `dev/README.md`, `docs/chang-vs-bnjettag.md`, gpu-benchmark `VERIFY.md:96,109`.
- Cluster: `kubectl get job kai-pilot1005-cpugate-98dd28 -n cms-ml` = Running 0/1 at the time of
  the check. No GATE_RESULT yet.

## Agreement checks requested (STUDY vs PROGRAM.json vs the frozen bundle)

| item | STUDY | PROGRAM.json | bundle / manifests | agree? |
| --- | --- | --- | --- | --- |
| 24 R1 arms | §4 rows 1-10, 24 pods (STUDY:116-131) | `r1_launch.runs` 24 rows (PROGRAM:255-507) | `index.json` round R1, count 24; PREPARED.json 24 GPU jobs | **yes** for the arm set except the H4 long-warmup arm |
| w100 | **w150 registered**: STUDY:125, :136-137 ("Recorded: ____ … until filled, R1 is as registered"), :200, :203, :229-231, :345-348 | w100 (PROGRAM:29, :150, :400-417, :802) | 0043 w150→w100; index rows 16-17 `A350-C-w100`; jobs `…-w100-s{1,2}-98dd28` | **no** (A1). `protocol-r1.json:223-249` also still w150 |
| caps 144/60/18 | STUDY:310-312 | PROGRAM:45-47 | — | yes |
| 20,800 s pod deadline | STUDY:310 "6 h deadline per pod"; `protocol-r1.json:674` "6 h pod deadline" | PROGRAM:51 `pod_deadline_s` 20800; :52 worst case 143.87 GPU-h | all 24 GPU jobs `template.spec.activeDeadlineSeconds` 20800, `backoffLimitPerIndex` 1 | **no** in text (B1) |
| stop order entropy-only → positive controls → code rule | §10 items 2, 3, 4 (STUDY:290-295) | `r1_stops`/`r2_stops`/`r3_stops` conditions in that order (PROGRAM:700-730, :1117-1147, :1512-1542), after integrity in `r*_readout` | — | yes |
| `r23_bundle_gate` before R1 readout | STUDY:214-220, §10.4 (:294-295) | PROGRAM:526-555; `r1_readout.after` includes it (:626-629) | R2/R3 configs not yet built (F9 open, by design) | yes on order; on failure PROGRAM waits, STUDY stops (B4) |
| production qualify-and-stop, Kai's go | STUDY:245-246, :271-277 | `qualifies_only` (:1274, :1616); `production_fill` notify (:1629-1643); `production_gate` needs `production_go_by_kai` and a later `production_go_at` (:1654-1663, :1851-1852) | — | yes |
| fresh-seed rule | STUDY:253-258 | prose only: `definitions.production_pair.fresh_seeds_only` (:206), referenced in `also_requires` (:1275-1278, :1617-1619); the machine conditions count all seeds (:1208-1270, :1561-1612) | — | **partial** (B2) |
| matched NB config | STUDY:247-248 | :200, :1637, :1733 | — | yes |
| 6/8 early stop | STUDY:278-281 | `production_launch.spec.early_stop` (:1729-1732) only; no step executes it, and `done_notify` ends the program at :1792-1805 | — | text yes; execution unowned (B3) |
| bundle_sha256 98dd2875 | not named; STUDY:7 "R1 bundle sha assigned at PREFLIGHT" | :197 and :1849 `98dd2875b7c902bb…0059` | PREPARED.json `bundle_sha256` identical; ConfigMap `kai-pilot1005-code-98dd2875b7` (JOURNAL:43) | yes (STUDY delegates; consistent) |

## Earlier findings, by name

### Arbiter v1 fixes F1-F10

| fix | status | evidence |
| --- | --- | --- |
| F1 K1 asked | **answered, not carried into STUDY** | decisions.md:5-10 (w100); STUDY:136-137, :347-348 still blank (A1) |
| F2 rebuild | done | 0042 + 0043, bundle 98dd2875 (JOURNAL:38-39, :43); PREFLIGHT §3b F2 row; index rows 22-23 (qkv1-450k floor 269,830 headroom 180,170; E-unc target 100,000,000, floor 171,526). CPU gate on 98dd28 still running |
| F3 readout import + dry run | done | PREFLIGHT §3b F5 row: `READOUT_IMPORT_OK`, `CERTIFICATION_ALL_PASS 2 0` on `rh-deccad51` |
| F4 deadline + failure policy | done in manifests; STUDY text stale | 24 jobs at 20,800 s, FailIndex on 5/76/124/137/143, DisruptionTarget Ignore; PROGRAM:51-53. STUDY:310 says 6 h (B1). Disruptions not bounded (B5) |
| F5 readout_diag | done | STUDY:178-181; PREFLIGHT §3b F5 row |
| F6a code rule | resolved | STUDY:214-220, :326-327; PROGRAM:189-198 |
| F6b matched NB, P350 only if V_bin = A350-C, H5 at R2 | resolved | STUDY:247-250, :201, :227-228; PROGRAM:199-205 |
| F6c fresh seeds | resolved in STUDY; partial in PROGRAM | STUDY:253-258; B2 |
| F6d no auto-fire, internal floor, early stop, PREFLIGHT guard | resolved in STUDY | STUDY:245-246, :261-262, :271-281 |
| F6e external reference | resolved, wording loose | STUDY:263-269; C3 |
| F6f text fixes | resolved (individual items below) | — |
| F6g deferred list | resolved | STUDY:364-378 |
| F7 PROGRAM reconcile | done, with residue | PROGRAM:6-36 amendments; B2-B4, B6, C1 |
| F8 PREFLIGHT §2a/§3b | present | PREFLIGHT §3b (left to PREFLIGHT critical v2) |
| F9 R2/R3 configs-only bundle | **open by design** | must finish before the R1 readout; PROGRAM:526-555 enforces order |
| F10 re-review | this panel | — |

### Critical v1

| finding | status | evidence |
| --- | --- | --- |
| A1 R2/R3 not reachable on one bundle | **resolved** | STUDY:7, :214-220, :326-327; PROGRAM:189-198, :526-555 |
| A2 unmatched production pair, NB config undefined | **resolved** | STUDY:247-250, :201; PROGRAM:200, :1733 |
| B1 entropy-only wording, low-acc band | resolved | STUDY:169-176, :197 |
| B2 H3 headroom confound, stale R2 promise | resolved | STUDY:96-98, :128, :199 |
| B3 no healthy A07 rung | resolved | STUDY:197 |
| B4 refutation at absent resolving power | resolved | STUDY:188-192, :201 |
| B5 best checkpoint vs collapse, weak n = 3 screen | resolved per arbiter ruling (diag descriptive + production early stop) | STUDY:180-181, :259, :278-281 |
| B6 cap basis 38.8 s | resolved | STUDY:304-317 (arithmetic below) |
| B7 D-1 entropy-only stop in PROGRAM | resolved | PROGRAM:168-178, :700-708 |
| B7 D-2 `bundle_sha256` | resolved | PROGRAM:93-95, :1849 |
| B7 D-3 amendments list | resolved | PROGRAM:6-36 |
| B7 D-4 production PREFLIGHT in STUDY guards | resolved | STUDY:272-273 |
| B7 D-5 NB production config | resolved | PROGRAM:1733 |
| B7 D-6 350k bracket naming | resolved in STUDY, unstated in PROGRAM | STUDY:227-228; PROGRAM:947 names R2 handoffs `rh-R2-E<rung>-s<seed>` (B6) |
| C1 stale scratch sentence | resolved | STUDY:19, :26, :30-31 |
| C2 arm ids | resolved | STUDY:122-123 |
| C3 rules-b5 citation | resolved | STUDY:125, :203-204 |
| C4 §9 heading | resolved | STUDY:243 |
| C5 qkv1 floor in §5 | resolved | STUDY:146 |
| C6 diverged at 250k | resolved | STUDY:286-287 |
| C7 dev/README line cite | **open (drifted again)** | C2 |

### Physics v1

| finding | status | evidence |
| --- | --- | --- |
| A1 selection seeds reused | resolved in STUDY; PROGRAM prose only | STUDY:253-256; B2 |
| A2 Prec auto-launch up to 5M | resolved | STUDY:245-246; PROGRAM:1651-1663 |
| A3 no physics reference | resolved (stated internal; external reference given as context) | STUDY:261-269; C3 |
| B1 mean-pool control; mask and normaliser | text resolved, control deferred | STUDY:155-156 (confirmed `analysis/attn_entropy.py:25`, no mask); STUDY:368-369 |
| B2 H2′, absolute vs relative headroom | resolved | STUDY:83-85, :91, :198 |
| B3 single-seed ladders | resolved | STUDY:197, :223-224 |
| B4 multiplicity | resolved | STUDY:188-192 (1 − (15/16)^5 = 0.2758, recomputed) |
| B5 qkv1 headroom confound | resolved | STUDY:82, :128 (450,000 − 269,830 = 180,170) |
| B6 epoch 500 vs restarts | resolved as a stated risk plus early stop | STUDY:278-281, :361-362 |
| B7 H5 names prunable weights | resolved | STUDY:94, :99-101 |
| C1-C5 | resolved | STUDY:6, :49-52; :128; :65-68; :101-102 |

### Constructive v1

| finding | status | evidence |
| --- | --- | --- |
| A1 R2/R3 reachable | resolved (F6a + F9) | as crit A1 |
| A2 trajectory table | resolved | STUDY:178-181 |
| A3 a26 on `model_unconstrained.keras` | resolved | STUDY:180 |
| A4 E positive control | resolved | STUDY:129, :208-210; index row 23 |
| B1 A07-350k → qkv1-450k | resolved | STUDY:128; PROGRAM:481-498 |
| B2 H3 R2 promise | resolved (text) | STUDY:98 |
| B3 w100 | **in bundle and PROGRAM, not in STUDY** | A1 |
| B4 A07-5M positive control | resolved | STUDY:123, :208-210; PROGRAM:179-188 |
| B5 per-epoch entropy observer | deferred with cost | STUDY:366-367 |
| C1 NB 1-bit init | deferred | STUDY:370-371 |
| C2 r1 is a locator | resolved | STUDY:223-224 |
| C3 epoch_seconds note | resolved | STUDY:304-306 |

## Numbers traced (recomputed or quoted)

| claim | source | check |
| --- | --- | --- |
| 38.8 s total elapsed per run-epoch, 30.85 s training, RTX 3090, A07, K = 1, n = 1 × 20 epochs (STUDY:304-305) | gpu-benchmark `VERIFY.md:96` (header), `:109` | ✓ |
| 500 × 38.8 s = 5.39 h (STUDY:310) | arithmetic | ✓ 19,400 s |
| production 960 / 1,207 GPU-h (STUDY:313) | 7,000 × 30.85 × 16 / 3,600 = 959.8; × 38.8 = 1,207.1 | ✓ |
| pilots 222; program 1,182-1,429 (STUDY:315-316) | 144 + 60 + 18; 222 + 960; 222 + 1,207 | ✓ |
| R1 worst case 143.87 GPU-h (PROGRAM:52) | 24 × (600 + 20,800 + 180) / 3,600 = 143.867 | ✓ arithmetic; scope limited (B5) |
| CP bounds 0/2 ≤ 0.842, 3/3 ≥ 0.292, 0/3 ≤ 0.708 (STUDY:185-186) | 1 − 0.025^(1/2), 0.025^(1/3), 1 − 0.025^(1/3) | ✓ 0.8419, 0.2924, 0.7076 |
| P(some 2/2 vs 0/2) = 0.276 (STUDY:189-190) | 1 − (15/16)^5 | ✓ 0.2758 |
| qkv1 headroom 80,170 / 180,170 (STUDY:82) | 350,000 / 450,000 − 269,830; index row 22 `headroom_zero` 180170 | ✓ |
| NB 0-bit-weight, 1-bit-alive 368,134 vs binary 619,198 (STUDY:100) | `dev/README.md:70-71` | ✓ values; cited line :64 is stale (C2) |
| NB init 12,362,587 vs 8,913,043 (STUDY:205) | `dev/README.md:70-71` | ✓ values; cited :63-64, :66-70 stale (C2) |
| E-unc PID target ≥ init (STUDY:129) | index row 23 `target_ebops` 100,000,000; PREFLIGHT §3b F2 row: E init 9,429,139 (synthetic sample, `final-tree-b3fb22/cpu_gate.log:7`) | ✓; STUDY says "ml-engineer records which" and the record is in PREFLIGHT, not STUDY (C4) |
| Chang/Sun MHA-64 77.9 %, Linformer-64 79.8 % at 350k, N = 64 (STUDY:263-266) | `docs/chang-vs-bnjettag.md:95-101` ("Acc (%)", every row 350k, :103) | ✓ values; "top-1 test" not in the cited lines (C3) |
| MHA-64 collapsed to a Deep Set (STUDY:267-268) | `chang-vs-bnjettag.md:107-110` | ✓ |
| bundle 98dd2875b7c902bb…0059 | PROGRAM:197, :1849; PREPARED.json `bundle_sha256` | ✓ identical |

Jev `jev_check_claims` (audit `jv-e706317bf1534487a787e6e6364f643d`, jev-1.13.0, advisory):

| id | claim | source | Jev | by hand |
| --- | --- | --- | --- | --- |
| c1 | Chang/Sun 77.9 % / 79.8 % top-1 test at 350k, N = 64 (STUDY:263-266) | chang-vs-bnjettag.md:90-110 | overstated (0.37), review | **overstated in wording**: the table header is "Acc (%)"; "top-1" and "test" are not in those lines (C3). Values exact |
| c2 | NB 368,134 vs binary 619,198 (STUDY:100) | dev/README.md:68-71 | supported (0.79), review | supported; line cite stale (C2) |
| c3 | 38.8 s upper bound, 30.85 s training (STUDY:304-305) | gpu-benchmark VERIFY.md:96-109 | overstated (0.29), review | supported. "Upper bound" is the arbiter's reading (arbiter v1:21: 20-epoch total elapsed amortizes startup over 20 epochs) |
| c4 | E-unc target 100,000,000 above E init (PREFLIGHT §3b) | PREFLIGHT.md:294 | supported (0.79), review | supported |
| c5 | Kai chose w100 (decisions.md) | decisions.md:5-14 | supported (0.80), suggestion | supported, and this is exactly what STUDY does not yet record (A1) |

## A (must resolve before PASS)

### A1. The registered STUDY (and `protocol-r1.json`) still say w150; the bundle, PROGRAM and handoffs run w100

- Kai chose w100 on 2026-10-05 15:21 (decisions.md:5-10). Its Check line says "STUDY.md §4/§9/§11
  and PROGRAM.json reflect K1–K3". PROGRAM does (PROGRAM:29, :150, :400-417, :802). The 98dd28 bundle
  does (index rows 16-17, jobs `kai-p1005r1-h4-e-350k-c-w100-s{1,2}-98dd28`).
- STUDY was last written at 14:35 (sha `95c9b61f`, JOURNAL:37), before K1. It registers
  `A350-C-w150` (STUDY:125), leaves the D3 record blank and says "until filled, R1 is as registered
  (w150)" (STUDY:136-137, :347-348). It also names w150 in the W order (STUDY:229-231) and in the H4
  time-limited reading (STUDY:200, :203). `protocol-r1.json:223-249` registers `pid_warmup: 150`.
- So by the STUDY's own text, two of the 24 launched pods are not the registered arm. The R1
  readout would carry an arm id (`A350-C-w100`) that the STUDY does not define, and STUDY's W order
  names an arm that will not exist.
- Fix, pre-data, text only (about 0.3 ah): a dated note in the [A3] block or a short [A4] citing
  decisions.md 2026-10-05 15:21. Fill the D3 "Recorded" lines. Rename row 6 to `A350-C-w100`
  (warmup 100; first feedback at ep 110 leaves 390 epochs, STUDY:345-346). Update STUDY:200, :203 and
  :229-231 (state whether the "time-limited" reading still applies to w100). Update
  `protocol-r1.json` and rerun `lab_check_protocol`.

## B (fix before PASS; text or PROGRAM edits, no rebuild)

### B1. The pod deadline differs between STUDY and what launches
STUDY:310 and `protocol-r1.json:674` say a "6 h deadline per pod". PROGRAM:51 and all 24 manifests
use 20,800 s (5.78 h), chosen for a hard 144 GPU-h with one 600 s pre-arm retry (PREFLIGHT §3b:
D = 20,820 s gives 144.0). The run_pack budget is then about 20,800 − 300 − 420 = 20,080 s, against
500 × 38.8 s = 19,400 s: 680 s (3.4 %) of slack at the pessimistic A07 bound. E and NB are
unmeasured on the 3090 (STUDY:305-306). A deadline exit (124) gives `status` ≠ complete, which is
an integrity stop for the whole round (STUDY:286). Fix: state 20,800 s and the margin in §11, and
say that a deadline hit is an integrity stop.

### B2. PROGRAM's machine conditions do not encode the fresh-seed rule
- STUDY:253-256 counts only seeds not used to choose W, V_bin or r1. PROGRAM's P350 counts all
  `V_bin` rows at 350k ≥ 3 and all NB350-C rows ≥ 3 (PROGRAM:1208-1251). Prec requires NB 3/3 and
  only that *healthy* A rows at r_rec have acc ≥ 0.50 (PROGRAM:1561-1612). It never requires A seeds
  2-4 healthy.
- The fresh-seed rule appears only as a prose string in `also_requires` (PROGRAM:206, :1275-1278,
  :1617-1619). `P350_only_if` is machine-form (:201-205); `fresh_seeds_only` is not.
- Example: W = A350-C. NB350-C then has seeds 1, 2 (selection) and 3 (fresh). The machine condition
  passes on 3 rows and `production_fill` says "QUALIFIES by rule" (PROGRAM:1637). Under STUDY it is
  unqualified (STUDY:257 says so).
- Containment: nothing launches without Kai's go (PROGRAM:1654-1663). The risk is a wrong
  "qualified" label in front of Kai.
- Also, PROGRAM's P350 requires *every* V_bin and NB row (selection seeds included) to be healthy
  with acc ≥ 0.50. STUDY requires that only of the fresh rows. Stricter, but a disagreement. Fix:
  express the fresh-seed filter as a `seed` `not_in` where-clause per arm, and align the all-rows
  scope with STUDY (or amend STUDY to the stricter form).

### B3. The production 6/8 early stop has no executor
STUDY:278-280 pre-registers it. PROGRAM puts it only in `production_launch.spec.early_stop`
(:1729-1732). No step reads a production epoch-500 readout, and `done_notify` ends the program 30 min
after launch (:1788-1805). `tools/autopilot.py` does not exist in the workspace (JOURNAL:15 says the
build was blocked), so no PROGRAM step executes on its own anyway. Fix (needed before production,
not before R1): name the owner and the mechanism (a production readout Job at epoch 500 plus a
PROGRAM step, or a manual check written into the production PREFLIGHT).

### B4. On an R2/R3 bundle that is not ready, STUDY stops and PROGRAM waits
STUDY §7 (:220) and §10.4 (:294-295): configs not gated before the R1 readout stops the program for
Kai. `r23_bundle_gate.on_false` is `wait` with no timeout (PROGRAM:552-553), and its job condition
names no job ("R2/R3 configs-only bundle CPU gate", :542). The outcome is safe, since the readout
never runs, but the program waits silently where STUDY says notify. Fix: give the step a timeout →
`stop_notify_kai` and the job name once built.

### B5. Disruption retries are outside the "worst case ≤ 144"
Manifests set `podFailurePolicy` DisruptionTarget → Ignore (e.g. `r1-ctl-e-unc-c-s1-job.json`).
A preempted pod is replaced without counting against `backoffLimitPerIndex`, at up to another
20,800 s. PREFLIGHT §3b says so ("Not bounded by the Job spec … DisruptionTarget replacements").
PROGRAM:52 states the worst case as 143.87 ≤ 144 without that caveat. STUDY §10.6 relies on a cap
check that no running process performs. Fix: add the caveat to PROGRAM `caps`, and name who checks
spend (the orchestrator at follow-up; RULES §4).

### B6. PROGRAM handoff and job references do not match PREPARED.json
- `r1_launch.job_names` is `kai-pilot1005-r1-*-98dd28` (PROGRAM:253). The real names are
  `kai-p1005r1-…-98dd28` (PREPARED.json `jobs`). `r1_util`/`r1_wait` resolve
  `$r1_launch.job_names`, so a literal match finds zero jobs.
- `r1_launch.handoffs` is a sentence ("filled from PREPARED.json …", PROGRAM:249-251), not the 24
  `rh-…` IDs, and PREPARED.json's sha is not pinned. RULES §3 counts "launches listed in a PROGRAM.json
  that Kai signed" as approved. Here the signature would not list them. `none_placeholder` passes
  trivially on that string (:517-518).
- `r1_readout` is still `PLACEHOLDER:rh-R1-readout` / `PLACEHOLDER:kai-pilot1005-r1ro-<sha6>`
  (PROGRAM:631-637). PREPARED.json has `rh-deccad5136f005dcb4250764` / `kai-pilot1005-r1ro-98dd28`.
  By STUDY §10.8 a placeholder stops the program at the readout.
- R2 bracket naming (crit v1 D-6) is fixed in STUDY:227-228, but PROGRAM:947 still templates
  `rh-R2-E<rung>-s<seed>`. F9 must emit the 350k rows as `program_arm` `A350-C`.
- Also `signed_by_kai: false` (PROGRAM:3). Kai verified by hand (JOURNAL:42) but has not signed.
- Fix: list the 24 handoff IDs and the readout ID (or pin PREPARED.json by sha), correct the job-name
  pattern, and have Kai sign. Launch itself is under Kai's direct order (JOURNAL:42), so this does
  not block R1, only autopilot execution.

### B7. R3 can run when Prec cannot qualify
STUDY §8 (:240-241) runs R3 when A at r_rec has ≥ 3 of 4 seeds healthy, seed 1 included. The [A3]
rule (STUDY:255-256) needs seeds 2-4 healthy for Prec. If seeds 1, 2 and 3 are healthy and seed 4
is not, R3 spends 3 pods (≤ 18 GPU-h) on a candidate that is already unqualified. That may still be
worth it for H5 at r_rec, but STUDY should say which. Fix: gate R3 on seeds 2-4 at r_rec, or state
that R3 is also an H5 read.

## C (notes)

- **C1.** `r1_launch.condition` `pods_requested: 23` (PROGRAM:512). It is stale (24) and vacuous as
  written.
- **C2.** dev/README line cites drifted: STUDY:100 `:64` and STUDY:205 `:63-64, text :66-70`. The
  table is now at `dev/README.md:70-71` (crit v1 C7 again).
- **C3.** STUDY:264-265 "top-1 **test** accuracy": the cited lines say "Acc (%)" (chang-vs-bnjettag.md:95).
  Also note that Chang's pipeline zeroes constituents with pT < 2 (chang-vs-bnjettag.md:149), so the
  reference is not same-input. Context only; no rule uses it.
- **C4.** STUDY:129 "ml-engineer records which". Record in STUDY that E-unc-C uses PID target
  100,000,000 (index row 23; PREFLIGHT §3b), not "EBOPs term off".
- **C5.** MHA-64 at 77.9 % collapsed to a Deep Set (STUDY:267-268). That external fact supports phys
  B1: uniform attention can still mean a usable tagger. The deferred mean-pool control
  (STUDY:368-369) is the right follow-up.

## Verdict

**ITERATE.**
- All A findings from the three v1 reviews are resolved in STUDY text, with residue in PROGRAM
  (B2, B6). So are all F6 sub-items.
- One new A: STUDY and `protocol-r1.json` were not updated for K1, so the registered R1 arm (w150)
  differs from the frozen bundle and PROGRAM (w100).
- Every fix is pre-data, text or PROGRAM only, with no rebuild. A1 + B1 + B7 + C2-C4 come to about
  0.5 ah (experiment-designer). B2-B6 are about 1 ah of PROGRAM edits, which need Kai's
  authorization as before.
- R1 can launch under Kai's direct order once A1 and B1 land and the 98dd28 gate passes. B2-B4 bind
  before R2 and production, not before R1.
