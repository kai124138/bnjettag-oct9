# Session 2026-10-04 — Jev integration, Chang and Delta summary, next steps

Written 2026-10-05 for the 2026-10-04 session. **Nothing here is a validated result.** Every
number is quoted as written in its source, with that source's own status label. Paths are
relative to the lab root. Nothing was launched, pushed or deleted in this session.

## 1. Jev integration

Before this session Jev worked, but nothing used it. The MCP server, skill, CLI, tests and
runbook existed, and the 2026-10-02 smoke run passed. But no agent, command, method doc or
memory entry referenced it. The agent definitions, `/review` and `.claude/settings.json` that
CLAUDE.md relies on were also missing, so the JFC loop had no reviewers to give Jev to.

| piece | state now | where |
| --- | --- | --- |
| MCP server `jev-lab` | live; key from the environment; enabled in project settings | `.mcp.json`, `.claude/settings.json` |
| 13 agent definitions (SYSTEM.md §4 roles), each naming its Jev tools | created | `.claude/agents/` |
| `/review <id> <PHASE>` | created; follows 06-review §6.2 | `.claude/commands/review.md` |
| kubectl-lint PreToolUse hook | registered; tested: a bad manifest exits 2, `ls` exits 0 | `.claude/settings.json` |
| SessionStart brief | registered | `.claude/settings.json` → `tools/brief.py` |
| method docs | "Jev in the loop" paragraph; review and owner-protocol pointers | `SYSTEM.md` §4, `docs/methodology/06-review.md` §6.2, `03-phases.md` step 6 |
| decision record | "Jev adopted, advisory only" | `.claude/memory/decisions.md` |
| index | rebuilt; `index-head.md` restored | `INDEX.md`, `.claude/memory/index-head.md` |

Where each tool sits:

| loop step | agent | Jev tool |
| --- | --- | --- |
| STUDY, PREFLIGHT | experiment-designer, ml-engineer | `lab_check_protocol`, `lab_freeze_protocol`, `jev_check_methods` |
| RUN failures | cluster-ops, investigator | `jev_triage_logs`, `jev_rank_snippets` |
| VERIFY, REPORT, every review | results-analyst, critical-reviewer, paper-writer, fixer | `jev_check_claims` |
| CHECK | arbiter | `jev_triage_review` (second opinion only) |
| literature | physics-researcher, physics-reviewer | `jev_screen_papers`, `jev_rank_snippets` |

Checks: `tools/jev_lab.py doctor` reports key available; 34/34 unit tests OK. Jev's policy
hash moved from `e8a26bf5…` to `2130cfca…` because it hashes the methodology docs edited here,
so any open lab loop now stops on hash drift. That is by design.

## 2. Chang recipe runs

Common recipe (`campaigns/2026-09-26-training-batch/STUDY.md:5`): 7,000 epochs, batch 2,790,
LR 3e-3 with cosine restarts every 500 epochs, pT ≥ 2 GeV, 350k EBOPs target, N=64, binary
weights; inputs pt/etarel/phirel (delta-screen PREFLIGHT gate 3b). Validation split n = 62,000
(training-batch `PREFLIGHT.md:519`).

### 2.1 Runs

Wall time runs from the first pod start to the end (completion, failure or deletion).

| # | job | date (UTC) | GPU / node | arms | status | wall time | source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0 | 8 × `kai-repro-chang-*` (released-code replication) | 2026-08-04 → 08-08 | product not recorded | xfm/xfmt × N 8/16/32/64, seed 42 | complete; xfmt-n64 needed 5 attempts (`trace_model` failures) | — | `_attic/repro-chang/repro-chang/comparison.md:29-32`; dates `messages/STATUS-2026-08-08.md:318` |
| R1 | `kai-chang0926-cache-c5d6f0` | 2026-09-27 | CPU, node-2-11.sdsc | data cache | complete | 2m40s | training-batch `PREFLIGHT.md:504-507` |
| R2 | `kai-chang0926-pilot-77f1ca` (regime A, K=6) | 2026-09-27 → 09-28 | A10, hcc-nrp-shor-c5825 | A-s1, A-s2, D-s1, A07-350-s1, C′-s1, E1-s1 | killed on Kai's decision | ≈8.7 h | `RUN.md:18-49,480-494` |
| R3 | `kai-chang0926-pilotb3-42abed` (regime B, K=3) | 2026-09-28 → 09-29 | A10, gpu-16 then gpu-17 (mghpcc) | A07-350-s1, C-s1, F-s1 | complete, `PACK_DONE diverged [] failed []` | ≈16.8 h | `RUN.md:630-1041` |
| R4 | `kai-chang0926-readoutb3-42abed` | 2026-09-29 | CPU, nrp-00.rcac.purdue | readout of R3 | complete, `CERTIFICATION_ALL_PASS 4 0` | 105 min | `RUN.md:1059-1064` |
| R5 | `kai-chang0926-pilotb5-42abed` (regime B, K=5) | 2026-09-29 | A10, hcc-nrp-shor-c5805 | A-s1, A-s2, D-s1, C′-s1, E1-s1 | complete | ≈20.7 h | `RUN.md:800-803`; recovery `REPORT.md:38` |
| R6 | `kai-chang1001-readoutb5-42abed-r1` | 2026-10-01 | CPU 8 / 24 GiB | readout of R5 | **Failed** (8 MiB export guard); certification itself passed | ≈72.7 min | recovery `readout-preparation/RUN.md:3-24,104-118` |
| R7 | 16 × `kai-gpubench-*` | 2026-09-29 | many products | 21-epoch benchmark arms | 9 complete; 7 not scheduled within the 6 h cutoff | — | `campaigns/2026-09-29-gpu-benchmark/RUN.md:123-130` |
| R8 | option (c): `kai-chang1002c-{cpugate,pilotc1,pilotc2,pilotc3,readoutc}-691946` | prepared 2026-10-02 | CPU, A10 | 8 pilot arms | **not submitted**; scientific gate pending | — | `campaigns/2026-10-02-chang-option-c/PREFLIGHT.md:3-7,71-77` |

### 2.2 Telemetry and readout numbers

None of these is quotable. Status is as labelled in the source.

| run | arm | metric | split, n | value | status (source label) | source |
| --- | --- | --- | --- | --- | --- | --- |
| R0 | xfm N=64 | test accuracy at ≤350k | test, 260k | 80.56 % | "COMPLETE, UNVERIFIED", seed 42, selected on test | `comparison.md` |
| R0 | xfmt N=64 | test accuracy at ≤350k | test, 260k | 80.85 % | same | `comparison.md` |
| R2 | A-s1 | val_AUC, epoch 1 → 10 | validation, 62,000 | 0.8218 → 0.8782 | telemetry | training-batch `RUN.md:184-190` |
| R2 | A-s1 | val_AUC at epoch 145 (05:12Z health check; checkpoint at stop was epoch 125), EBOPs 440,289 | validation, 62,000 | 0.7732 | telemetry | `RUN.md:373,433,493` |
| R2 | all traced arms | projected wall time | — | 17.8 / 17.8 / 17.4 / 13.3 / 23.8 days; only E1 fits the 14-day rule | projection | `RUN.md:231-237` |
| R3 | A07-350-s1 | epoch 500: EBOPs, val_AUC | validation, 62,000 | 381965, 0.500000 (infeasible) | telemetry | `RUN.md:1047` |
| R3 | C-s1 | epoch 500: EBOPs, val_AUC | validation, 62,000 | 4592840, 0.808829 (feasible) | telemetry | `RUN.md:1048` |
| R4 | C-s1 | best feasible val accuracy (AUC) | validation, 62,000 | 0.664726 (0.900360) | pilot readout, "never quoted", single seed | `READOUT_epoch500.md:133` |
| R4 | F-s1 | best feasible val accuracy (AUC) | validation, 62,000 | 0.236177 (0.594849) | same | `READOUT_epoch500.md:134` |
| R6 | A-s2 | certified feasible checkpoint: EBOPs, val acc, AUC | validation, 62,000 | 339,168, 0.320871, 0.644662 | "diagnostic, unreviewed… not quotable" | recovery `readout-preparation/VERIFY.md:55-58,105,116` |
| R6 | D-s1 | same | validation, 62,000 | 323,222, 0.405371, 0.730096 | same | `VERIFY.md:55-58,117` |
| R6 | A-s1 | feasible but degenerate: min EBOPs, val acc | validation, 62,000 | 315,512, 0.202129 | same | `VERIFY.md:74-83` |
| R7 | E, K=4 | s/epoch, A10 (krule Job) vs RTX 4090 (klow Job) | 4 × 20 arm-epochs | 114.10 vs 55.41 | benchmark telemetry | gpu-benchmark `VERIFY.md:98,112` |
| R7 | A07, K=2 | s/epoch, A10 vs RTX 4090 (both krule Jobs) | 2 × 20 arm-epochs | 96.56 vs 48.29 | same | `VERIFY.md:99,111` |

### 2.3 What went wrong

| incident | root cause | source |
| --- | --- | --- |
| A07-350-s1 OOM on all 3 attempts in the K=6 pod | K=6 does not fit 23 GiB at batch 2,790 | training-batch `RUN.md:98` |
| 4 arms stalled 2026-09-28 ~01:32Z, GPU at 0 % | host-memory leak of 80–95 MB per epoch per arm filled the 36 GiB cgroup | `review/INCIDENT_stall_20260928.md:37-44` |
| C′-s1, E1-s1 lost their remaining attempts | relaunched arms inherited stale heartbeats; retry budget is pod-wide | `INCIDENT:113-120` |
| W&B shows pre-resume values for A-s1/A-s2 epochs 51–69, F-s1 26–43, A07-350/C 26–27 | W&B drops out-of-order steps on resume; disk is authoritative | `RUN.md:458-462,907-911` |
| Pilot-b pods Pending 17–66 min | A10 saturation ("0/532 nodes") | `RUN.md:657-671,695-697,802` |
| RSS gate script hard-coded 8192 MiB while the pod ran at 6144 | manual override needed | `RUN.md:599-607` |
| b5 readout Job Failed | 5 activation-history files exceeded the frozen 8 MiB export guard | recovery `readout-preparation/RUN.md:78-81` |
| Memory logs reset at migration | 2026-09-27/28 decision and incident entries cited by RUN.md no longer exist; Delta incidents back-filled this session, Chang stall/OOM entries still absent | `decisions.md:3`, `experiment-log.md:11` |

### 2.4 What went well

- The fingerprint gate (initial EBOPs 11559681) held on every pilot-b and benchmark pod.
- Every RSS gate passed after the leak fix.
- Certification passed 4 of 4 in both readouts.
- The K=3 pack finished early once F-s1 paused.
- R0 matched or beat the paper at 7 of 8 points; xfmt N=8 is 66.25 % against 66.3 % (`comparison.md:24`). It is single-seed and selected on test, so it is not independent evidence.

### 2.5 Findings

- **At 350k EBOPs, attention collapses in every arm, and accuracy is poor or gone.** Every
  350k-target attention head is exactly uniform (b5 VERIFY `:144`). A07-350 is a constant
  classifier from epoch 240 (`READOUT_epoch500.md:105`), A-s1 is degenerate, and E1 stalls at
  356,745 (b5 VERIFY `:74-96`). A-s2, D-s1 and F-s1 reach feasible but weak checkpoints (val
  acc 0.320871, 0.405371, 0.236177; single seed, validation n = 62,000). A-s1, A-s2 and E1
  are labelled Deep-Set class (b5 VERIFY `:149-151`), as are A07-350 and F-s1
  (`READOUT_epoch500.md:132,134`). D-s1 reduces to a uniform average of V (b5 VERIFY `:146-148`).
- **K1 fires.** The A07-350 offset is 1,707.4 against a threshold of 694.7, and the C-s1 vs
  A07-350 pair differs by 0.075343 > 0.02 (`READOUT_epoch500.md:43,244-249`). Production is blocked.
- **For the b5 arms, the PID input offset does not explain the failures.** For A-s1, A-s2,
  D-s1 and E1-s1 the in-training vs traced offset is 1.5–5.7 % of headroom (b5 VERIFY
  `:225-231`). A07-350 is different: its offset is 0.2458 of headroom, which fired K1's offset
  clause; K1 also fired on the C-s1 vs A07-350 pairwise clause (`READOUT_epoch500.md:43`).
  Option (c) targets A07-350's offset; whether it clears K1 or the b5 arms' weakness is what
  the pilot tests (`SCIENTIFIC_GATES.md:30`).
- **Kai chose option (c), traced cost into the PID, on 2026-10-01** (`decisions.md`). The code
  and five Jobs are prepared offline (R8) but not reviewed or launched.
- **Regime A at 7,000 epochs was too slow.** Four of the five traced arms projected 17.4–23.8
  days on an A10; only E1, at 13.3 days, fit the 14-day rule. Kai switched to regime B (trace
  every 10 epochs) (`STUDY.md:1528-1536`; `RUN.md:231-237`).
- **A100 leads at one GPU and the RTX 4090 at 2–16 GPUs; the A10 takes 1.651–1.876× as long.**
  How many GPUs can actually schedule was never measured (gpu-benchmark `VERIFY.md:22-33`).

## 3. Delta campaign

Delta is a pre-registered queue of 103 methods (50 single, 53 combined) to try on the binary
N=64 tagger (`campaigns/2026-09-26-delta/`). The wave-2 screen
(`campaigns/2026-09-27-delta-screen/`) is frozen at STUDY, has PREFLIGHT and RUN, and has
**no VERIFY or REPORT**. **No physics cell has launched.** Every Delta Job so far was a
memory canary or a node check.

### 3.1 Jobs

| # | job / pod | date (UTC) | GPU / node | what | status | incident |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `kai-delta0926-canary` / `-6q8kn` | 09-28 09:17Z | A10, c6017 | E-k4, E-k5, A07-k3 memory canary | showed Succeeded, but nothing was measured | all 12 arms failed at start (W&B project missing); wrapper hid it (`RUN.md:57-112`) |
| 2 | same, re-applied / `-6cnrd` | 09-28 09:28Z | A10, c6017 | same, wrapper fixed | stopped and deleted by the orchestrator at ~09:50Z (`RUN.md:251-260`; the earlier "unknown actor" note at `:290-298` predates that record) | epoch-0 NaN in every rep-A arm; wrong initial EBOPs; `ablation.py:1280` NaN crash (`RUN.md:251-303`) |
| 3 | `kai-delta0926-discrim-c6017` | 09-28 | A10, c6017 | single-process fingerprint | complete | fingerprint correct: c6017 is healthy with one process (`PREFLIGHT.md:466-481`) |
| 4 | `kai-delta0926-discrim-other` | 09-28 | A10, c5809 | same | complete | same; the fault needs 4–5 processes per GPU (`REGRESSION_TICKET.md` §8) |
| 5a | `kai-delta0926-canary-v2` / `-w4cqm` | 09-28 19:55Z | A10, c5925 | E-k4 | deleted | operator edit set `WANDB_MODE=disabled`; arms refused to start (`RUN.md:353-364`) |
| 5b | `kai-delta0926-canary-v2` / `-5crk2` | 09-28 20:11Z | A10, c6013 | E-k4, 110 epochs | stopped at epoch ~100 to free the A10 for the Chang pilot | none; no NaN (`RUN.md:382-428`) |
| 6 | `kai-delta0926-canary-a07` (1st) | 09-29 ~00:15Z | — | A07-k3 | withdrawn while Pending | — |
| 7 | `kai-delta0926-canary-a07` / `-tsrq7` | 09-29 03:03Z | A10, c5813 | A07-k3, 110 epochs | pod exit 7; Job deleted | seed 3 OOM before epoch 1; stale `k_result` fields (`RUN.md:482-544`) |

### 3.2 Packing (canary telemetry, single seed, not quotable)

| class | GPU | K | GPU peak | host-RSS slope | s/epoch | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E | A10 | 4 | 17,425 / 23,028 MiB (75.7 %) | 0.45–0.63 MB/epoch, PASS | 104.3–104.5 | E packs at K=4 | delta-screen `RUN.md:420-428` |
| A07 | A10 | 3 | OOM on s3 | — | — | fails | `RUN.md:503-505` |
| A07 | A10 | 2 | 16,906 / 23,028 MiB (73.4 %) | 0.457, 0.515 MB/epoch, PASS | — | K=2 holds, but not as a clean certificate | `RUN.md:506-553`; recovery `SCIENTIFIC_GATES.md:40` |

Last-epoch validation telemetry (n = 62,000): E-k4 val_AUC 0.787–0.819 at epoch 99–100, all
infeasible: 453k–512k EBOPs on the last traced epoch (epoch 100 for s1, 90 for s2–s4). A07 s1 at epoch 110 had val_AUC 0.857564 at 3,795,449 EBOPs,
feasible against its 5M target (`logs/canary-a07-rep-c-s1-20260929T0608Z.log:117`).

### 3.3 Went well / went wrong / findings

- **Well:** the green-but-failed wrapper bug was caught and fixed (`FAIL=1`, `exit 7`). Two
  cheap single-process discriminator Jobs ruled out a plain bad-GPU explanation. RSS slopes are
  far under the 5 MB/epoch limit.
- **Wrong:** the epoch-0 NaN on c6017 was not reproduced single-process. It is attributed to a
  fault that needs 4–5 processes per GPU, and the node is excluded as a precaution
  (delta-screen `PREFLIGHT.md:483-490`). Two code faults are still open: `ablation.py:1280` NaN
  serialization and no epoch-0 whole-pack divergence rule in `run_pack.py`
  (`SCIENTIFIC_GATES.md:32`). The `stage_run_id` W&B collision was accepted by decision
  (`RUN.md:374-381`). One operator edit broke a launch. Delta always yielded the A10 to Chang.
- **Findings:** E packs at K=4 and A07 at K=2 on a 24 GB card. A07 planning K changed 3 → 2 in
  `code/memory_measurements.json`, uncommitted. The 2026-10-02 audit says to prioritize the H /
  NB / FP32-E / A arms "rather than a broad Delta sweep"
  (`local/2026-10-02-accuracy-audit/findings.json`, recommended_order).

### 3.4 Open gates (delta-screen `PREFLIGHT.md:155-186`; recovery `SCIENTIFIC_GATES.md:46-62`)

- **Pending:** gate 1 (anchor epoch-500 readout), 2 (Kai's [DK] answers), 5 (horizon check),
  6 (Bop measurement), 7 (determinism probe; not built), 7/14/15 on the chosen GPU product,
  12 (pods and quota).
- **Contradiction, A07 product eligibility:** RUN.md:551 says the GPU policy overrides the
  ≥45 GB rule [A1]; the GPU benchmark VERIFY still applies [A1].
- **Contradiction, rebase:** ONBOARDING §5.4 says option (c) forces a Delta rebase;
  SCIENTIFIC_GATES.md:50 says it does not.

## 4. Next steps under JFC and the NRP job plan

Nothing below has launched. Each launch needs its gate, a lint-clean manifest (the hook
enforces it), and a run handoff through `tools/run_handoff.py`. The hook now refuses direct
`kubectl apply` of a Job.

| order | step | NRP jobs | resources | gate before it runs | approves |
| --- | --- | --- | --- | --- | --- |
| 1 | `/review 2026-10-02-chang-option-c PREFLIGHT` (critical-reviewer, solo tier) | none | 1 opus agent | — | — |
| 2 | Option (c) CPU gate: full pytest, 58 configs build/step/reload, floors, cadence | `kai-chang1002c-cpugate-691946` | CPU 8 / 24 GiB, 4 h deadline | review PASS; fingerprint ConfigMap `kai-chang0926-fp-e9511d1aeb` present | **Kai** |
| 3 | Option (c) pilots to epoch 500 | `kai-chang1002c-pilotc1/2/3-691946` | 3 × A10: pilotc1 4 arms, 8 CPU / 32 GiB; pilotc2 and pilotc3 2 arms each, 4 CPU / 16 GiB | CPU gate passes; smoke first; launch, then leave (RULES §4) | **Kai** |
| 4 | Option (c) epoch-500 readout | `kai-chang1002c-readoutc-691946` | CPU 8 / 24 GiB, 4 h | pilots done; new session | Kai |
| 5 | Audit arms H (released-code), NB (learned-width HGQ), FP32-E (ceiling), A (binary) | none yet: needs a STUDY | — | STUDY → panel review → PREFLIGHT | Kai |
| 6 | Delta: fix the two open code faults under a new PREFLIGHT sha, then E and A07 product canaries | `kai-delta*-canary-*` (new identities) | per GPU policy | [A1] product rule and [DK] answers from Kai; option (c) pilot read first | Kai |

Order rationale: K1 blocks Chang production, and option (c) is the chosen fix. The (c) pilot
is the cheapest experiment that can clear or confirm K1. The audit puts the H / NB / FP32-E /
A comparison ahead of any Delta sweep. Delta waits on the code fixes and two of Kai's rulings.

**Option (c) risk:** the b5 readout says the PID offset is too small to explain the b5 arms'
failures, so (c) may clear the A07-350 part of K1 and still leave weak 350k arms. The pilot readout should decide that, and the step 5 STUDY can be
written while the pilots run.

## 5. Needs Kai

1. Authorize the option (c) CPU gate once step 1 returns PASS.
2. Delta A07 product eligibility: keep [A1] ≥45 GB, or let the GPU policy override it.
3. Whether option (c) forces a Delta rebase.
4. Whether to add `hcc-nrp-shor-c6017.unl.edu` to `KNOWN_BAD_NODES` in `nrp-lab/nrp_doctor.py`.
5. The context budget is 169 lines against a 150 cap now that `index-head.md` exists again.
   The fix is to trim CLAUDE.md or RULES.md, or to raise the cap.
6. `SYSTEM.md` §7 still lists Mac-migration decisions that look obsolete in the WSL workspace.

## 6. Update 2026-10-05: Kai's answers and what followed

| question | answer | what was done |
| --- | --- | --- |
| Option (c) CPU gate | approved, conditional on review | PREFLIGHT review PASS (CPU gate only); `kai-chang1002c-cpugate-691946` submitted 2026-10-05T00:10:00Z (`campaigns/2026-10-02-chang-option-c/RUN.md`) |
| Delta A07 ≥45 GB rule [A1] | drop it; keep the 40 % utilization floor | the GPU policy governs A07; 90 % memory ceiling and rule PACK kept (`gpu-selection-policy.md`, `decisions.md`) |
| Delta rebase onto (c) | "do what is scientifically sound" | no rebase now; rebase once if (c) becomes production; no Delta cell before the (c) readout (`decisions.md`, MEDIUM confidence, flagged) |
| c6017 | add it | in `KNOWN_BAD_NODES` |
| context budget | trim | CLAUDE.md and RULES.md trimmed, 169 → 131 lines; no rule removed |
| SYSTEM.md §7 | remove obsolete items | the two Mac-migration items removed |

The review graded the later pilots as not yet cleared:
- B3: the pod-3 duration is about 30.7 h, not 19 h.
- B4: the floor re-trace, the non-degeneracy threshold recheck, the b5 VERIFY review and Kai's
  §5.2 stop-criterion decision are all still unsupplied.
- B5: the GPU product (A10 or RTX 4090) is still to be chosen.
