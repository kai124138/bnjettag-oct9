# plan.md: PREFLIGHT, build half (ml-engineer, 2026-10-08)

Notebook for the build half of PREFLIGHT. PROPOSAL.md v2 (amended 2026-10-08) §3, §4, §6, §8, §9.

## Steps (done)

1. Copy the pilot tree (bundle 98dd2875) into `code/`: 393 files, sha256 equal to
   `manifests-98dd28/bundle-manifest.json`. The pilot's `build_tarball` on the copy reproduces
   bundle `98dd2875…0059`. Then `git init -b main`; base commit `90be22e`.
2. Generator `code/campaigns/d350/generate.py`. It rebuilds the pilot config with the pilot
   generator, checked against the file, and asserts an exhaustive diff. Plus byte copies of
   `cpu_gate.py` and `monitor_p.py`, and `tests/test_d350.py`. Commit `d4f6659`.
3. `eval/`: byte copies of four pilot modules, `score.py`, `MANIFEST.json`, and
   `tests/test_score.py` (29 tests).
4. `tools/d350_common.py`, `prepare_attempt.py`, `prepare_score.py`. They load the pilot's
   `freeze_p.py` read-only (hashes pinned in `tools/pinned.json`) and reuse its Job builders.
5. Handoffs prepared for the baseline, the reference and their score Jobs. Each was validated
   offline and linted with a failing `kubectl` shim.
6. CPU gate (`cpu_gate.py` on the two configs) and the full copied-tree suite, both with the
   local CPU venv.

## Tried and failed, or changed

- `gate_check.py cpu-gate|pytest` cannot judge this tree: it expects 24 configs and 166 tests.
  The d350 gate log was checked against the same criteria by hand (PREFLIGHT.md).
- Lint with the failing `kubectl` shim gives ERROR on every GPU Job, because the product map is
  empty without `kubectl get nodes`. The pilot's r3 Job, rc=1 with cluster access, gives the
  same ERROR under the shim (control in `evidence/lint.log`).
- `--resume-from` first refused relaunching to the same stop epoch. Changed to allow it (the
  pilot r2/r3 pattern), with the deadline counted from the source's start epoch.

## Decisions flagged

```
DECISION: BNJ_STAGE=production for every d350 Job (W&B run id key and group suffix only).
ALTERNATIVES: pilot-r1/r2/r3 (misleading group suffix); a wandb_util change adding d350 stages
  (changes bnhgq2 and the manifest sha of the baseline code).
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: run root /data/discovery-350k-20261008/attempts/<arm>-a<attempt>; record dir
  <root>/runs/<config name> (run_study.py appends runs/<name>).
ALTERNATIVES: /data/discovery-350k-20261008/runs/<arm>-a<attempt> (gives runs/.../runs/...).
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```
```
DECISION: score INVALID when the CPU replay accuracy of the selected checkpoint differs from
  the logged value by more than 1e-3 (62 of 62,000 jets).
ALTERNATIVES: record only (no gate); a tighter 1e-7, as run_study.verify_selected uses on the
  same device.
CONFIDENCE: LOW (no GPU-vs-CPU measurement at this size)   FLAG FOR HUMAN: YES
```
```
DECISION: score Job keeps the pilot readout's 2 TF threads and the 3,600 s deadline.
ALTERNATIVES: 8 threads (faster; changes reduction order).
CONFIDENCE: MEDIUM (CPU time per full-split trace measured locally only)   FLAG FOR HUMAN: NO
```
