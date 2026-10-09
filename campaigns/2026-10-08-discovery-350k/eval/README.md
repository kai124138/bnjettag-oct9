# Frozen evaluator: `eval/score.py`

`score.py <run record dir>` computes the primary metric of PROPOSAL.md §4. It prints exactly one
line on stdout. On success that line is the validation top-1 accuracy of the best feasible
checkpoint over zero-based epochs below the stop epoch (default 1000). On failure it is
`INVALID[<class>]: <reason>` with exit status 2, or 3 for an internal error. The result is written
beside the record as `score-s<K>.json`, K given by `--score-attempt` (default 1), in both cases.
A file of the same attempt with a different primary result is never overwritten; the scorer
reports INVALID instead. A new attempt writes a new file and leaves earlier ones in place.

## Invalid-reason classes and second attempts

`INVALID_REASONS.json` lists literal prefixes of every reason `score.py` can emit and the class of
each. `scientific`: the run trained and was read correctly but no checkpoint meets the four
conditions ("no feasible checkpoint in epochs <"). `evaluator`: certification, CPU-replay,
manifest, threshold or selection mismatches and internal errors. `infrastructure`: missing
snapshot, records or files, truncated runs. **Any reason that matches no prefix is treated as
`evaluator` by the consumer** (`score.classify` does the same). A second score attempt
(`--score-attempt 2`) may be run only for `evaluator` and `infrastructure` reasons; `scientific`
is final. `score.py` itself only writes its attempt file and does not enforce this. The file is
covered by `MANIFEST.json`.

## What is reused, not reimplemented

| file here | copied from (bundle 98dd2875, byte for byte) | used for |
| --- | --- | --- |
| `readout_pilot.py` | `campaigns/pilot1005/readout_pilot.py` | `records` (contiguity 0..stop-1), `key` (acc, AUC, -EBOPs, -epoch), `THRESHOLD_C`, `LABELS_SHA256` |
| `certify_ebops.py` | `campaigns/pilot1005/certify_ebops.py` | `certify_checkpoint`: fresh reset retrace on the full training split, rel. tol. 1e-6, <= target |
| `nondegenerate_threshold.py` | `campaigns/pilot1005/nondegenerate_threshold.py` | `main`, run unchanged on a one-row index of the run's config: re-derives p_maj + 5 SE from the cache's y_val |
| `attn_entropy.py` | `analysis/attn_entropy.py` | `analyze` on the selected checkpoint (secondary only) |

`MANIFEST.json` holds the sha256 of these four files, `score.py` and `INVALID_REASONS.json`. The scorer refuses to
run if any of them differs. A change to any of them is a new evaluator version, and needs its own
review before any score from it is used.

## Feasibility (all four, as in the pilot)

1. traced EBOPs at or below the run's target (`--expect-target`, default 350,000; the reference
   is scored with 5,000,000);
2. EBOPs above the 0-bit floor (171,526 for E);
3. validation accuracy above the threshold of 0.2109624456315518, the majority-class rate plus
   5 SE of y_val (n = 62,000);
4. `certify_ebops.certify_checkpoint` returns CERTIFIED for the selected snapshot file
   `snapshots/epoch-<stop>/model_best.keras`.

## Input checks that also give INVALID

These run in addition to the feasibility conditions:

- the eval files do not match the manifest;
- `DIVERGED.json` is present;
- the target is not the expected one;
- the stop epoch is not a snapshot boundary;
- the `epoch-<stop>` snapshot is missing or not at completed_epochs == stop;
- the per-epoch records have a gap;
- the run's threshold, labels sha or 0-bit floor differ from the frozen values;
- the threshold re-derived from the cache differs;
- the runner's best_feasible differs from the recomputed selection;
- the run's training split sha differs from the cache's;
- the selected checkpoint's validation accuracy, replayed on CPU, differs from the logged value
  by more than 1e-3. This tolerance was chosen without data; see PREFLIGHT.md.

## Secondary measurements (`score.json` → `secondary`, recorded and not ranked)

- **Accuracy at epochs 500 and 1,000.** For each, the record of zero-based epoch E-1: whether it
  was traced, whether it was feasible, and its accuracy if it was. Beside that, the best feasible
  accuracy as of the epoch-E snapshot.
- **Feasible-epoch counts.** The number of feasible epochs, and the number with accuracy ≥ 0.50.
- **Selected checkpoint.** Its validation macro AUC and its activation widths (mean bits).
- **Budget arrival.** The first epoch whose traced EBOPs met the target, zero- and one-based.
- **Minimum traced EBOPs.**
- **Windowed accuracy.** The best feasible accuracy per 200-epoch window, one-based (601-800,
  801-1000, …), for the slow-starter rule.
- **Attention entropy** of the selected checkpoint, computed by `attn_entropy.analyze` on CPU.
  When it fails, it is null with a reason (for example `n_part` other than 64). A head with a
  non-finite value (all-zero softmax rows) is written as null with a reason and left out of the
  mean; `n_heads_excluded` counts them, and the mean is null with a reason when none is finite.
  This never changes the primary score.

GPU-hours are not read here; they come from the harness ledger.

## Certification must cover the actual inference operations

`certify_ebops` re-traces `layer.ebops` of every HGQ layer with `enable_ebops`. Arithmetic a
candidate adds outside those layers is not counted, and neither is arithmetic at a precision
HGQ does not see. Examples are a learned per-channel weight scale, a teacher branch left in the
graph, or a new normalisation. **Any candidate that adds inference operations needs its
certify_ebops coverage verified before its score is accepted.** The verification shows, on the
candidate's checkpoint, that every added operation is inside an EBOPs-counted layer at its actual
precision. Otherwise its cost must be added and documented (PROPOSAL §11 item 7). Until that is
done, a candidate's score is recorded as unaccepted.

## How the score Job uses it

`tools/prepare_score.py <run name>` ships these files as `/work/code/d350_eval/` beside the code
of the commit that trained the run. That code is needed to deserialize the checkpoint's layers.
The scoring logic never comes from a candidate branch. Some files the proposal protects from
candidate edits may differ from the base commit: the EBOPs computation, data and split code, the
copied readout scripts, and the ablation functions the score calls. If so, the preparation is
refused unless a reviewed reason is given.

Records that `score.py` does not verify are trusted as logged. These are the per-epoch records of
epochs other than the selected one, which feed the secondary measurements. The selected one is
checked independently: by the recomputed selection, the retrace and the CPU replay.

## Tests

From the campaign directory:

```
/home/kaimoe/lab/.venvs/preflight-20261001/bin/python -m pytest -q -p no:cacheprovider eval/tests
```

The tests use synthetic run directories in the style of the pilot's `tests/test_readout_pilot.py`.
They cover the valid path, the frozen tie-break, the reference target and idempotent reruns, per-attempt
score files, a NaN attention head, reason-class coverage, and 22 INVALID cases, one of them the internal-error path with exit status 3. One end-to-end test trains a tiny model with the frozen runner on CPU and runs
the real certification and CPU replay on it.
