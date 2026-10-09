---
id: YYYY-MM-DD-<type>
date: YYYY-MM-DD
type: <training-batch | engram | constituent-screen | confirmation | pt-weighting | synthesis | ops | engineering | eval>
status: scratch
question: <one sentence>
supersedes: 
superseded_by: 
code_sha: 
wandb: <project> / <group>
results: 
---

# <title stating the question>

**Question.** <one sentence>. **Null.** <one sentence>. **Bearing on the thesis.** <one sentence>.

## Reference table

| reference | value (metric, split, n, status) | source |
| --- | --- | --- |
| round-14 record, same configuration | | `path:line` |
| | | |

## Arms

| arm | what differs from the baseline | everything held fixed |
| --- | --- | --- |
| BASE | nothing | N=, input set, split, schedule, init |
| | | |

## Seeds

<count>; measured sd for this configuration <value, source>; this design resolves a gap of <value>.

## Selection rule (pre-registered, validation only)

<rule>

## Falsifier

<the result that makes the claim false>

## Budget

arms × epochs = ; GPU-hours ≈ (benchmark: ); arms per pod = ; expected wall time = ; W&B group = .

## Conventions compliance

| convention | row | will implement / not applicable because |
| --- | --- | --- |
| `docs/conventions/jet-tagging-metrics.md` | | |
| `docs/conventions/quantization-and-cost.md` | | |
| `docs/conventions/fpga-synthesis.md` | | |

## Decision labels

- [D1] 
- [A1] 
- [L1] 

## Where I am not sure

- 
