# Campaign batch20260918 — attention design, attention precision, budget schedule

**Status (2026-09-18): frozen, preflighted, dry-run accepted by the server. NOT submitted.**

5 arms x seeds {4,5,6} = 15 full-model runs, all derived from `batch20260917-a04-s1`
(16 constituents, d_model 32, FFN 32, 2 blocks, 4 heads, channel activations, 350k EBOPs).
Each config differs from A04 only in name/seed/group and its one knob.

| index (seed 4/5/6) | arm | change |
| --- | --- | --- |
| 0 / 5 / 10 | b00 | none — reference replication |
| 1 / 6 / 11 | b01 | `arch.n_heads` 4 -> 1 |
| 2 / 7 / 12 | b02 | `arch.pos_enc` "learned" -> "none" |
| 3 / 8 / 13 | b03 | `quant.softmax_out_bits` 10 -> 8 |
| 4 / 9 / 14 | b04 | `experiment.target_schedule` 525k -> 420k@100 -> 350k@200; final target 350k |

Split/order seeds unchanged (1 / 20260912); same N16 cache under `/data/batch20260917/n16`.
Selection: `val_categorical_accuracy` among checkpoints with EBOPs <= 350k (final target).
Screen rung: 400 cumulative epochs of the 1000-epoch schedule; promote b00 + two best arms.

## Code change (bundle sha 774a2d4d18c3…)
- `bnhgq2/qat.py`: `build_qat_model(..., with_pos_enc=True)`; the `AddPositional` layer is added
  only when `with_pos_enc` and `arch.pos_enc == "learned"`; unknown values raise.
  A04 built under shipped vs edited code: identical weight hash, logits and EBOPs (4,295,496).
- `run_batch_screen.py`: `--campaign` (default keeps the 12-arm behaviour); later campaigns
  read `configs/<campaign>/index.json`.
- `check_batch20260918_preflight.py`: all 15 build/grad/save-reload, per-arm effect checks,
  resume + guard checks on b02 (with uninterrupted equivalence) and b04. `preflight-result.json`.

**Known gap:** a b02 (no-PE) checkpoint cannot yet be exported — `convert_*.py`, `extract.py`
and `run_stage.py` all `get_layer("pos_enc")`. Training is unaffected; fix before HLS.

## Launch (needs a human; blocked for the agent as a shared-cluster mutation)
```sh
cd local/training-batch-20260918/launch
python3 ../../../nrp-lab/nrp_doctor.py lint job.json
kubectl create -f code-configmap.json     # immutable; keep until every resume is done
kubectl create -f job.json                # kai-batch0918-screen-e400, parallelism 15
```
Lower concurrency any time: `kubectl patch job kai-batch0918-screen-e400 -n cms-ml --type=merge -p '{"spec":{"parallelism":10}}'`

## Startup monitoring
```sh
kubectl get pods -n cms-ml -l app=kai-batch0918-screen -o wide
python3 ../../../nrp-lab/nrp_doctor.py status          # admission errors / bad nodes
kubectl logs -n cms-ml -l app=kai-batch0918-screen --tail=5 --prefix | grep -E "GPU gate|resume_epoch|epoch 1/"
```
Expect per pod: `[gpu] GPU gate PASS`, `[wandb] authentication PASS`, `resume_epoch=0`,
and b02 with `params=` 512 fewer than b00. Epochs measured 46-122 s on this pool, so 400
epochs is ~5-14 h, inside the 23 h per-process timeout. Recovery = the r3 recipe (new Job
name, same ConfigMap/configs/root; runs resume from `runs/<arm>/latest.json`).
