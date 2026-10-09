# Live publication reconciliation review

Date: 2026-10-01. Verdict: **PASS — operational reconciliation only**.

Reviewed the changes to recovery `REPORT.md` and these publication files:
`README.md`, `docs/current-work/README.md`,
`docs/current-work/RESULTS_AND_NEXT_STEPS_20261001.md` and
`docs/current-work/results-status-20261001.json`. No A, B or C findings remain.
No remote calls, source-code edits, arrays, model execution or scientific
recomputation were used in this review.

## Preservation and evidence checks

- Compared status JSON with `git show HEAD` at
  `e56fd7361f0299c1721aa053506d1eabc092cdba`; that baseline JSON also exactly matches
  recorded `origin/main` at `6da5003809a3ccd371ec6ba83a09276a594ab9ab`.
  All **16 original source records, including their hashes, are unchanged**.
- The complete pT, architecture/attention, Engram, Delta and GPU-benchmark JSON
  sections are unchanged. Chang's b3 result/scientific-gate fields and the prior b5
  progress record remain unchanged. Confirmation's historical records and numerical
  inputs are preserved; only operational status, references and limitations change.
  The report's completed-science section is byte-identical to its Git baseline.
  The root README diff changes operational prose without changing its scientific
  numbers or conclusions.
- All **seven newly cited source hashes** reproduce from local bytes. The five
  cluster-capture stored hashes reproduce again. The four access-receipt stored
  hashes also reproduce; only PVC status and mount observations are used in this
  reconciliation. The JSON's operational artifact hashes, Job UIDs, conditions,
  timestamps and PVC fields agree with the captures.
- Confirmation is correctly reported as `Failed=True`, `FailedIndexes`, transition
  **2026-09-26T07:24:11Z**. The report explicitly separates `status.failed=5` from
  scientific-arm failures and retains the unresolved per-arm diagnosis.
- Chang b5 is correctly reported as `Complete=True`, completion
  **2026-09-29T20:52:06Z**, `succeeded=1`. Five arm outcomes, checkpoints and the
  full readout remain unestablished. Empty pod/readout observations are bounded to
  the recorded queries and are not used to infer deletion, never-ran history or
  absence of artifacts. K1 and the (c)/(d) decision remain pending.
- `captures/access-20261001T0518Z/pvc.json` supports `kai-data` being `Bound`,
  `100Gi`, `ReadWriteMany` at **05:17:47.601818Z**. `mounts.json` supports no matching
  mounts among returned `cms-ml` pods at **05:17:48.902193Z**. Neither establishes
  PVC contents, checkpoint validity or a completed recovery route.
- The JSON distinguishes recorded `source_stdout_sha256` claims from independently
  checked stored hashes, and separately identifies the collector's reviewed/operator-
  reported execution identity. Raw stdout was not independently reproduced.

## Publication and scope

The compatibility counts agree with the approved final preflight and its independent
audit: **217 = 21 contracts + 100 builds + 96 reload comparisons**; synthetic maximum
difference 0.0, tolerance 1e-7. Historical metric reproduction, calibrated-width
remeasurement, 74 unattributed paths and hardware validation remain pending. These
counts do not change any scientific result or retire uncovered entry points.

The compatibility document exists at local Git commit
`e56fd7361f0299c1721aa053506d1eabc092cdba` and its bytes match the reviewed document.
New prose links use that absolute commit URL, so publication to main does not require
the compatibility file to exist on main. Relative Markdown links in the three public
Markdown files resolve in recorded `origin/main`. Draft PR #1 and its commit match
`local/2026-10-01-execution/publish-receipt.json`; no fresh remote PR-state check was
performed. The text correctly presents the work as a draft, not a merged change.

`REPORT.md` resolves **LIVE_CAPTURE_REVIEW C1**: its opening and missing-evidence
table now use the recovered terminal conditions and retain the actual arm-log/PVC
gaps. The prepared reader route remains separate; no new workload, readout, resume,
launch or scientific gate is authorized by these updates.

Reviewed public file SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `README.md` | `95bfa1c26fc1a21190486e1445f15a47a259c7e11d6101283142f9683c10840e` |
| `docs/current-work/README.md` | `a53e6a662109bebc901c354c7dcdda85b3b568a5022eb25f3f5e3ca15cfb1ad2` |
| `docs/current-work/RESULTS_AND_NEXT_STEPS_20261001.md` | `26666b23ef023472b720ebe6066d7e167ec94016e479e6b02928916587f4cd95` |
| `docs/current-work/results-status-20261001.json` | `eb34b44cf8413f72128df25c1dc147de5e311f4f642e1f1f1ec07f5fd1747bd3` |
