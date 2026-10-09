# VERIFY — <campaign id>

Every number below was recomputed in this session from the named artifact with the command
shown. Labels: metric · split · n · status.

## Recompute

```
uv run --with numpy,scikit-learn python <script or inline> 
```

## Selection (as pre-registered in STUDY.md)

Rule: . Selected checkpoints: .

## Numbers

| arm | seed | metric | split | n | value | artifact |
| --- | --- | --- | --- | --- | --- | --- |

Seed-averaged (mean ± sample sd, ddof=1):

| arm | metric · split · n | mean ± sd | seeds |
| --- | --- | --- | --- |

## Gaps

| comparison | mean Δ | 95 % interval (paired, df) | seeds lower / total | verdict |
| --- | --- | --- | --- | --- |

## Per-class and binned

## Cost and hardware

| arm | eBOPs remeasured (zero / random inputs) | binary layers verified | LUT / FF / DSP / BRAM | II / latency / Fmax | C-sim fidelity |
| --- | --- | --- | --- | --- | --- |

## Consistency with the record

Baseline vs `<reference source>`: pull = .

## Verdicts

| STUDY claim | verdict | evidence line |
| --- | --- | --- |

## verify.json

Written beside this file by the recompute script, one row per number above:

```json
[{"claim": "C1", "quantity": "BASE macro AUC", "value": 0.8711, "metric": "macro-OvR AUC",
  "split": "ROC-test", "n": 260000, "seeds": 8, "status": "seed-averaged",
  "source": "roc-results/<dir>/<arm>-s<k>.npz"}]
```

## Sanity

```
$ python3 tools/verify_check.py <this file>
```
