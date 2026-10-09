CPU gate kai-chang1002c-cpugate-691946: PASS (with two launch conditions, L1 and L2 below)

# PREFLIGHT critical review v1: Chang option (c), 2026-10-05

Reviewer: critical-reviewer (solo, 06-review §6.2 PREFLIGHT tier). Scope: launch readiness of the CPU
gate (handoff `rh-c1240347631f771a2c30e37d`). Pilots pilotc1/2/3 are graded separately and do not
block it. Everything here was checked read-only. No kubectl apply/create was run, nothing was
submitted, and no campaign file was edited. Jev `jev_check_claims` was not run; every number below
was recomputed or read from the cited file:line.

## Checks run (all reproduced, not taken from the campaign's own logs)

| check | result |
| --- | --- |
| sha256 `patches/0032` vs staged `2026-09-26-training-batch/code/patches-staged/0032…patch` | both `f475c69e487f…508be`; `cmp` byte-identical; matches AMENDMENT_DRAFT.md:66 |
| sha256 `patches/0033` | `23536dfe…736b`, matches PREFLIGHT.md:26 and build_tree.py:27 |
| `build_tree.py --out <scratchpad>` (42abed payload + 0032 + 0033) | `TREE_MATCHES` |
| independent rebuild of the deterministic tarball from `code/tree` | `6919462c…9da3`, 243,904 B, 326 files. Equals the disk tarball, the `configmap.json` payload, and the payload in all five handoff `source-configmap.json`; `bundle-manifest.json` has 326 entries, 0 mismatches |
| manifest SHA recomputed (run_study.manifest construction, pinned versions) | `7ab48738…544f`; CPU and training pins identical for the six manifest packages |
| PREPARED.json `record_sha256` / `job_json_sha256` vs files, all 5 handoffs | all equal; record sha prefix = rh- ID |
| `run_handoff.py validate rh-c124…` (offline, code read: validate_dir only reads) | `VALID` |
| `nrp_doctor.py lint` on the cpugate handoff job.json (live node map) | exit 0, OK, notes only |
| AMENDMENT_DRAFT.md sha256 now | `64372c63…7b2f` = the hash the design PASS reviewed (REVIEW_DRAFT.md:7) |
| STUDY.md, decision JSON sha256 | equal to AMENDMENT_DRAFT.md:63-64 |
| 58 configs: per-arm count; A/B/D/R/F seeds 1-8 present for pairing | A,B,C,D,F,R,A07-350 ×8; C′, E1 ×1; all 40 pairing files exist |
| `static_floors.json` chang1002c vs chang0926 | byte-identical (copied, as PREFLIGHT.md:44-45 says) |

CPU gate manifest (`handoffs/rh-c124…/job.json`): CPU 8 and memory 24Gi, with requests equal to
limits. Ephemeral storage 12Gi, emptyDir 12Gi, no GPU resource, `CUDA_VISIBLE_DEVICES=-1`,
`WANDB_MODE=disabled`. `activeDeadlineSeconds` 14400, `backoffLimit` 0, TTL 7 d,
`automountServiceAccountToken: false`. Both containers pin
`python@sha256:4d1caded…` (receipt `local/2026-10-01-execution/python-readout-image.json`,
amd64 present). The digest was already used by the recovery readout handoffs. The bundle hash is
verified in-pod with `sha256sum -c` before extraction, and the manifest SHA is asserted before any
test runs. These values agree with PREFLIGHT.md:73.

Writes. The init container writes only `/data/run-handoffs/rh-<id>`; `install` never overwrites a
conflicting record. The main container writes only to
`OUT=/data/chang-n64-20260926/option-c-20261002/cpu-gate-691946-r1`, guarded by
`test ! -e "$OUT"` and a plain `mkdir`. No repo file or capture references `option-c-20261002` or
`pilot-c-20261002`. `BNJ_RUN_ROOT` points to the new pilot-c root, but nothing in the gate uses it.
`cpu_gate.py` and `check_pairing.py` never read it, and every test that runs `run_training` or
`run_pack` uses `tmp_path` or overrides the root (`tests/test_run_pack.py:40`,
`analysis/test_attn_entropy.py:159-161`). The cache is only read, through the init container's
`data_info.json` hash. Nothing touches the 42abed runs, the `pilot/` or `pilot-b/` roots, or the
historical campaign tree. `freeze_c.py:58` sets `dont_write_bytecode` when it imports the historical
freeze.py.

## Launch conditions (not ITERATE; satisfy them at action time)

- **L1. The launched record is not the reviewed record.** `rh-c124…` carries
  `scientific_gate: pending`, and `launch --submit` refuses it (run_handoff.py, `need(... == 'cleared')`).
  PREFLIGHT.md:101-110 re-prepares through `freeze_c.py --only cpugate --gate-cleared … --approval-ref …`,
  which yields a new rh- ID. Before submitting, diff the new `record.json` against
  `rh-c124…/record.json`. The only allowed differences are `brief.approval_ref`,
  `brief.scientific_gate` and the identity fields derived from them: run-id label, handoff
  annotations, handoff ConfigMap name and path. The bundle `6919462c…`, manifest `7ab48738…`, image
  digest, script, resources and output path must be byte-equal. This PASS covers that record and no
  other.
- **L2. Approval reference.** `--approval-ref` must be a dated Kai authorization saved in a file
  (for example under `local/2026-10-0x-execution/`) that cites this review. "Kai approved conditional
  on PASS" has to exist as a record before it is quoted. `freeze_c.py:376` rejects only a missing
  value or one starting with `PENDING`.

## Findings: CPU gate

**A.** None.

**B1. The gate's floor coverage is narrower than PREFLIGHT and the amendment say.**
PREFLIGHT.md:58 lists "floors re-traced" as a CPU-gate check. `cpu_gate.py:130-135` re-traces only
the **zero-bit** floor, once per arm at seed 1 (`with_attn_rule=False`). It compares that value with
the config's `nondegenerate.zero_floor_ebops`, not with `static_floors.json` as the brief's
expectation says (`brief-cpugate.json` expected_metrics[1]). AMENDMENT_DRAFT.md:39 requires
zero-bit, one-bit-alive and narrow/full attention floors re-traced "with HGQ2's own path, including
E1/C′". The `one`/`attn_narrow`/`attn_full` values in `chang1002c/static_floors.json` are the
chang0926 values, byte-copied and never re-traced. This does not block the gate: it measures what
it measures. But a gate PASS must not be recorded as closing the amendment's floor gate. Fix:
before pilots, re-trace those floors (CPU, offline, e.g. the chang0926 `trace_floors.py` route) or
state the limitation, and correct PREFLIGHT.md:58.

**B2. The pytest expectation cannot fail on skips or a short collection.** The brief only says
"all pass; skips listed". The staged baseline is exactly `100 passed, 2 skipped`, both skips at
`analysis/test_attn_entropy.py:142`
(`2026-09-26-training-batch/code/staged-option-c/evidence/pytest_staged_option_c.log:16`). The tree
has no other skip, skipif or importorskip. The run_training integration tests for 0032/0033
(`tests/test_pid_traced_only.py`; see the note at `tests/test_option_c_amendment.py:5-6`) have never
been executed anywhere, so this gate is their first run. In the gate's VERIFY, require exactly the
2 known skips, and require that every test in `test_pid_traced_only.py` and
`test_option_c_amendment.py` appears as passed in `pytest.log`. Any other skip is a FAIL. No job
change is needed.

**C1.** `check_pairing.py:52-57` exits 0 on `UNPAIRED`, so `pairing_exit=0` in `CPU_GATE_DONE` does
not mean "paired". Read the `*_F_PAIRING` lines or `pairing.json`. UNPAIRED is a registered outcome
(Welch fallback), not a failure.

**C2.** `cpu_gate.json` records `kernel_hashes` for all 58 configs. Compare them offline against the
historical `cpu_gate_d25.json` / `cpu_gate_shipped_77f1ca4e_full.json`. That directly checks the
amendment's "do not borrow a fingerprint" requirement (AMENDMENT_DRAFT.md:39) before the pilots rely
on `--expect 11559681`, and it costs no cluster time.

**C3.** `tests/test_pid_traced_only.py:158` drops `learning_rate` when it compares straight and
resumed telemetry. If the two differ beyond float formatting, that is a resume defect hidden by the
test. Look at the field in the run once.

**C4.** The script sets OMP and TF intra-op threads to 2 on an 8-CPU request, and the work is serial.
The staged suite took 193 s locally. The pod is over-provisioned for its 4 h deadline, which is
harmless.

**C5.** A failed or timed-out gate cannot be rerun under the same identity: the Job name, `-r1` and
`test ! -e` are fixed by `freeze_c.py:248,397`. A rerun needs a reviewed new name and output path.
That is the intended fail-closed behaviour; note it in RUN.md if it happens.

**C6.** Re-preparing overwrites `manifests/brief-cpugate.json` and `cpugate-job.json`, and it
rewrites the tarball, configmap and bundle-manifest. These rebuild deterministically: the rebuild
above matched. `PREPARED-cleared.json` is overwritten on every `--only` invocation
(`freeze_c.py:463-464,482`), so a later pilot clearance erases the cpugate clearance record. Keep a
per-job copy or commit between invocations.

**C7.** The `pid_traced_only` docstring (`bnhgq2/ablation.py:509`) still calls `per_epoch` "the
default". The code now requires the key explicitly (lines 526-527). This is wording only.

**C8.** The result binds to bundle `6919462c…`. If Kai's decision on PREFLIGHT §5.2 (a
pre-registered stop or readout criterion) changes code or the monitor, the bundle changes and the
gate must be rerun.

## Findings: later pilots (graded; not blocking the CPU gate)

**B3. The pod-3 duration bound is false.** PREFLIGHT.md:97-98 says "the slowest historical pilot-b
arm (138.5 s/epoch) bounds it at about 19 h". The same table lists C′-s1 at **221.2 s/epoch** (A10,
pilot-b K=5, mean of the last 30 epochs, telemetry, not a result;
`2026-09-26-training-batch/RUN.md:973`). 500 × 221.2 s ≈ 30.7 h at K=5. K=2 may be faster, but that
is unmeasured, so 138.5 s/epoch is not a bound. Correct the sentence and the time-to-readout plan.

**B4. Amendment gates not yet supplied before the pilots.** These are listed in PREFLIGHT §5.4 but
need to be on the pilot checklist:
- the floor re-trace (B1);
- the fixed non-degeneracy threshold recheck from the same validation labels
  (`nondegenerate_threshold.py` needs the cache and is not in the CPU gate);
- an independent review of b5 VERIFY and the matched regime-A/B table (AMENDMENT_DRAFT.md:36, the
  first gate "in order");
- Kai's §5.2 decision, which must be written before any pilot outcome exists.

PREFLIGHT §5 states all of these honestly. They remain launch blockers for the pilots.

**B5. GPU product is unsettled under the policy.** `gpu-selection-policy.md` §3 selects by
earliest finish. The benchmark measures the RTX 4090 at about 2× the A10 (PREFLIGHT.md:155-157). A10
is defensible for matched-product comparison with pilot-b (policy "Scientific and operational
constraints", first bullet), but the choice has to be Kai's and recorded (§5.3). If a product other
than A10 is chosen, the pilot manifests are regenerated and need re-review, plus the 110-epoch
product canary.

**C9. Packing vs the 90 % limit: correct as arithmetic.** Recomputed from `RUN.md:953-955`
per-process peaks:
- pod 1: 4 × 4,350 = 17,400 MiB / 23,028 = 75.6 %;
- pod 2: 2 × 8,446 = 16,892 MiB = 73.4 %;
- pod 3: 4,346 + 5,110 = 9,456 MiB = 41.1 %;
- total 43,748 MiB > 2 × 0.9 × 23,028 = 41,450 MiB, so three pods is the minimum.

Pod 1 and pod 2 match the benchmark's measured A10 shapes: E K=4 17,425 MiB (75.7 %) and A07 K=2
16,906 MiB (73.4 %) (`2026-09-29-gpu-benchmark/VERIFY.md:98-99`). The historical sums
reproduce the pod totals to within about 30 MiB (K=5: 22,510 vs 22,540). The caveat: the
per-process peaks were read about 170 min into pilot-b, and E1 grew from 2,830 MiB to 4,350 MiB
between regimes A and B. Growth over 500 epochs is unmeasured, and the 90 % line is notify-only
(`GPU_SAMPLE`). Treat a sustained `GPU_SAMPLE` above 90 % as a stop-at-checkpoint item with Kai.

**C10. 40 % utilization floor (rule PACK).** Lint passes with 4/2/2 arms. The A10 benchmark shows
95-97 % mean utilization at E K=3/4 and 80.2 % at A07 K=1 (VERIFY.md:98-101). The thinnest pod
(pod 3: F + C′) is therefore unlikely to fall below 40 %. The policy's rolling 3-h check can be
computed from the new `GPU_SAMPLE` lines. Confirm that `nvidia-smi` is present in the python image
under the GPU runtime. If it is absent, the sampler prints errors and nothing is measured.

**C11.** The canary arrival "about 20–25 minutes after arms start" (PREFLIGHT.md:99) holds for pod 1
at 114 s/epoch. For C′ at up to 221 s/epoch it is about 40 min or more.

**C12.** PREFLIGHT.md:7 and :162-163 call for an arbiter after this review. 06-review §6.2 sets the
PREFLIGHT tier as critical-reviewer solo. Either cite the reason for the extra tier or drop it.

## Verdict

CPU gate: **PASS**, subject to L1 (diff of the re-prepared record against `rh-c124…`) and L2 (a
dated approval record). B1 and B2 are settled in the gate's VERIFY or PREFLIGHT text. They do not
require a job change. Pilots: not reviewed for launch. B3-B5 and §5.1-5.4 remain open. The verdict
line for `.claude/memory/review-reports.md` is left for the orchestrator, because this review was
limited to writing one file.
