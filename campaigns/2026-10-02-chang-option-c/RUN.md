# RUN — Chang option (c): CPU gate (2026-10-05)

Nothing here is quotable. Only the CPU gate is authorized; the GPU pilots and the readout are not.

## Authorization

- Kai: "yes approve", conditional on a PREFLIGHT PASS. Saved as `local/2026-10-05-execution/cpugate-approval.json`.
- Review: `review/PREFLIGHT_critical_v1.md`, PASS for the CPU gate only (SHA-256 `c6aa3353…`).
  Launch conditions L1 and L2 were both met before submission.
- L1: the cleared handoff `handoffs/rh-bf4170d542600fef18cb189a` differs from the reviewed
  `rh-c1240347631f771a2c30e37d` only in `brief.approval_ref`, `brief.scientific_gate.{status,reference}`
  and the derived handoff identity labels in `job.json`. Checked with a flattened JSON diff.
- `manifests/cpugate-job.json` and `bundle-manifest.json` are unchanged by the re-prepare.
  `manifests/brief-cpugate.json` now holds the cleared brief. The pending brief is preserved
  inside `rh-c124…/record.json`.

## Launch

| field | value |
| --- | --- |
| Job | `kai-chang1002c-cpugate-691946` |
| handoff | `rh-bf4170d542600fef18cb189a` (`validate`: VALID) |
| submitted | 2026-10-05T00:10:00Z through `tools/run_handoff.py launch --submit` |
| lint | `nrp_doctor lint` OK (notes only) |
| objects created | ConfigMaps `kai-chang1002c-code-6919462cf0` and `kai-rh-bf4170d542600fef18cb189a`; Job |
| prerequisite | fingerprint ConfigMap `kai-chang0926-fp-e9511d1aeb` present (age 6d1h) |
| shape | CPU 8 / 24 GiB, 12 GiB ephemeral, no GPU, `activeDeadlineSeconds` 14400, backoff 0 |
| output | `/data/chang-n64-20260926/option-c-20261002/cpu-gate-691946-r1` |
| started | pod `kai-chang1002c-cpugate-691946-9wvbr` Running 2026-10-05T00:11:01Z on `prp-gpu-2.t2.ucsd.edu`; first log line `/cmcode/hgq2.tar.gz: OK` (bundle hash check). Watch ended there (RULES §4). |
| admission warnings | init container `record-run-handoff` cpu limit/request ratio 10 > 1.2 and memory ratio above 1.2. Warnings only; the Job was admitted. |

## What the gate VERIFY must check (from review B2 and C)

- Exactly the 2 known skips (`test_attn_entropy.py:142`).
- Every test in `test_pid_traced_only.py` and `test_option_c_amendment.py` passed.
- Read `pairing.json` directly; `check_pairing.py` exits 0 even when arms are unpaired.
- Compare `kernel_hashes` against the historical gate JSON.
- A gate PASS does not close the one-bit-alive or attention floor re-trace (B1).

## Follow-up (fresh session)

```
kubectl get job kai-chang1002c-cpugate-691946 -n cms-ml
kubectl logs job/kai-chang1002c-cpugate-691946 -n cms-ml --tail=50
```

A rerun after a failure needs a new Job name and output path (review C).

## Incident 2026-10-05 ~00:45Z: unit-test step FAILED (6 of 118)

The pytest step ended with `6 failed, 110 passed, 2 skipped` in 1764 s. All 6 failures are in
`tests/test_run_pack.py`: `test_isolation_and_retry`,
`test_unrecorded_failure_fails_pod_after_others`, `test_relaunch_starts_a_fresh_heartbeat_clock`,
`test_pod_wide_stall_is_not_charged_to_retry_budgets`, `test_single_arm_stall_is_charged` and
`test_memory_gate_exit_is_not_retried`. At `tests/test_run_pack.py:117` the test expected
`ARM_MEMORY_GATE_FAILED memgate`, but the pack reported every fake arm failed
(`failed ['chang1002c-a-n64-s1', 'chang1002c-b-n64-s1', 'chang1002c-d-n64-s1', 'chang1002c-f-n64-s1']`).

The gate's test criterion (review B2: exactly 2 known skips, everything else passed) is **not
met**. The Job keeps running its later steps; their output is kept as evidence. No code was
touched. Diagnosis: investigator → `REGRESSION_TICKET.md`. A fix needs a new sha, a new
PREFLIGHT and a new gate Job name and output path. The pilots stay blocked.

Diagnosis (investigator, about 90 % confidence, `REGRESSION_TICKET.md`): environment leak. The Job
exports `BNJ_CAMPAIGN_DIR` (`freeze_c.py:139`). `tests/test_run_pack.py:40` builds the child env
from `os.environ` without overriding it, so `run_pack.py:38` reads the real `index.json` instead
of the fixture. Reproduced locally for 2 of the 6 tests. This is not a defect in `run_pack.py`
or in patches 0032/0033. Proposed fix: test-only, set `BNJ_CAMPAIGN_DIR` in `setup()`. It
needs Kai's go-ahead, then a new sha, PREFLIGHT and a gate `-r2`.

## End of gate r1 (Job Failed, about 4 h 34 m)

The final log line was `CPU_GATE_DONE pytest_exit=1 cpu_gate_exit=0 pairing_exit=0`. The 58-config
gate (build, step, reload, floors, cadence) and the A/B/D/R–F pairing check both exited 0. Only
pytest failed, from the `BNJ_CAMPAIGN_DIR` test leak. Bundle 6919462c is superseded by the pilot
program's bundle `b3fb22c8` (`campaigns/2026-10-05-pilot-program/`), which includes the test fix.
The option-(c) pilots `pilotc1/2/3` are not launched; R1 arms H1 (A@350k with and without (c))
replace them.
