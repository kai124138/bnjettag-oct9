# Pilot program dev: NB arm (0036) and attention bit floor (0037)

Status 2026-10-05: engineering only. No PREFLIGHT, no review, nothing launched. Every number below
is either a deterministic structural trace (static floors on a synthetic sample) or a local smoke
run on the home PC. **None of it is quotable.** Plan and failed approaches: [plan.md](plan.md).

## Layout

| path | what |
| --- | --- |
| `patches/0036-nb-arm.patch` | NB arm. `git diff` against the option-(c) tree (42abed + 0032 + 0033). SHA-256 `9edd3a6c…67be` |
| `patches/0037-attention-bit-floor.patch` | H3 attention bit floor. Also written against the option-(c) tree and independent of 0036. SHA-256 `0b469b52…bb60` |
| `tree/` | option-(c) tree plus a local git repo. Branches: `nb` (`5d43675`), `h3` (`9ca631d`), `combined` (`8025230` = 0036 + 0037) |
| `configs/` | `make_configs.py` and four exploration configs, each `chang1002c-a-n64-s1` with one change. These are not pilot configs (pilot configs are patch 0035's job) |
| `evidence/` | jsc150 quantizer dump, static floors, A-unchanged logs, unit-test log, cross-tree checker |
| `smoke/` | local GPU smoke runner, launcher, `runs/*/smoke_summary.json` |

Patch application was checked on a fresh copy of the option-(c) tree in the order 0034 → 0036 → 0037,
with `patch -p1`: no fuzz, no offsets that fail, and the result is identical to branch `combined`
(the only difference is 0034's test file). 0037 also applies alone to the option-(c) tree.

## 0036: NB arm ([D22], [A22])

- **Key:** `quant.weight: "kbi_learnable"`. This is the name STUDY [A22] registers and that
  `config.py` already accepts. The brief's `kbi_learned` was given as an example. With this patch the
  builder raises on that name, as it does on any weight type that has no branch.
- **Quantizer:** jsc150 `xfm`'s weight quantizer, dumped on the pin (hgq2 0.1.9). The values are kbi,
  k0 1, b0 4, i0 0, RND, SAT_SYM, bc MinMax(0, 23), ic None, MonoL1 1e-8 on b and i, i_decay_speed
  1e-3 (inert under SAT_SYM), and one width per weight (trainable). Source:
  `evidence/jsc150_weight_quantizer_dump.json` and its script. `get_transformer` does not build on the pin
  (`QEinsumDenseBatchnorm('...c,cC->...C')` raises, and `QLinformerAttentionT` is missing). The dump
  therefore enters the exact scope stack of `get_model('xfm', 7, 7, 1e-8, 64, True)` plus
  `get_transformer`, then builds the kernel layer types that xfm uses.
- **Where it applies:** exactly the 9 kernels that A binarizes (`input_proj`, Wq/Wk/Wv/Wo, ffn_fc1/2,
  head_fc1/2), with plain `QEinsumDense`/`QDense`. Biases stay float. The activation, softmax and
  table quantizers, optimizer, schedule, PID, the [D20] trace and the 350k target are A's
  (unchanged config keys). A test checks that the activation quantizers are identical to A's.
- **Other changes:** the [A20] guard accepts binary or kbi weights. `binary_gate` sends NB configs to
  `nb_weight_gate`, which checks the layer set, that widths are trainable and per weight, and that 0
  bits is reachable. NB runs log `weight_bits_mean` and `weight_zero_bits_fraction` each epoch, and
  `ebops_budget.json` gets `weight_widths` (per layer: fraction at 0 bits, mean bits) for the
  selected checkpoint. `static_floor.py` gains the NB modes `zero_w0`, `one_w1` and `one_w0`.
- **Tests:** `tree/tests/test_nb_arm.py`, 11 tests, unittest:
  - the model builds, and its built quantizer equals the dump;
  - an unknown weight type raises;
  - the NB gate passes;
  - one training step moves the kernels and widths;
  - EBOPs bill the real weight bits: `input_proj` costs the same as binary at 1 bit and exactly twice as much at 2 bits, and a 0-bit kernel costs 0 and outputs 0;
  - under EBOPs pressure every width reaches 0;
  - a `.keras` reload round trip gives equal stored EBOPs and predictions;
  - the init kernel hashes equal A's after `matching_initialization` (the [A22] pairing prerequisite);
  - all 58 chang1002c configs match their `config_map.json` SHA-256.
- **A unchanged:** `evidence/check_a_unchanged.py` builds each config in the base tree and the
  patched tree, in separate processes on CPU. It compares every variable's bytes after
  `matching_initialization`, the traced init EBOPs, the loss after one epoch step, and the variables
  after that step. Result: SAME for A-s1, A-s2, A-s3, A07-350-s1, C′-s1, C-s1, E1-s1, F-s1 and R-s1
  (`evidence/a_unchanged_*.log`; 0036 alone, 0037 alone and combined).
  **Correction 2026-10-05 (PREFLIGHT review v1 B3).** The sentence above overstated the logs. No
  0036-alone log exists. `a_unchanged_combined.log` covers 6 configs (A-s1, A-s3, A07-350-s1, C′-s1,
  E1-s1, F-s1), and `a_unchanged_0037.log` covers 4 (A-s1, A07-350-s1, C′-s1, R-s1). A-s2 and C-s1
  were in no log. The full set of 9 has now been run on the final pilot tree: base
  `2026-10-02-chang-option-c/code/tree` (bundle 6919462c) vs the F2 tree (b3fb22c8 + 0042, whose
  training code is byte-equal to b3fb22c8). All 9 are SAME, exit 0
  (`../evidence/fixes-v1/a_unchanged_final_tree_9configs.log`; home PC, CPU, not quotable).

### NB 0-bit floor (structural trace, `static_floor.py`, synthetic n=256, seed 0)

| config | zero (0-bit acts) | zero, weights 0 bit | 1-bit-alive, weights at init (4 bit) | 1-bit-alive, weights 1 bit | 1-bit-alive, weights 0 bit | init |
| --- | --- | --- | --- | --- | --- | --- |
| A (`chang1002c-a-n64-s1`) | **171,526** | n/a | 619,198 | n/a | n/a | 8,913,043 |
| NB (`dev1005-nb-n64-s1`) | **171,526** | 171,526 | 1,372,390 | 619,198 | 368,134 | 12,362,587 |

The NB zero floor equals A's 171,526, the value STUDY [D22] expected. At 0-bit activations every
weight term vanishes, and what remains is attention activation×activation plus the softmax tables.
A reproduces its recorded floors exactly (`campaigns/chang1002c/static_floors.json`). NB's init
EBOPs are higher because weights start at 4 bits ([A22] already flags that the early PID phase
differs).

## 0037: attention bit floor (H3)

- **Key:** `quant.attn_bit_floor: {"bits": 1|2, "sites": [...]}`. The sites are a subset of `q`, `k`
  (the Q·K stream inputs), `v` (the A·V stream input), `softmax_in` (the learned exp-input) and
  `softmax_out` (the softmax output into A·V). Validation is strict: no default sites, bits must be 1
  or 2, the key needs `act_calib: free`, and the softmax sites need `softmax_quant: chang`. When the
  key is absent the builder passes every config through unchanged.
- **Mechanism:** `FlooredKIF` is a subclass of HGQ2's KIF quantizer. Its effective `f` is
  `max(f, bits − i − k·[SAT])`, so the HGQ2 `bits` that EBOPs price and the forward pass uses never
  fall below the floor. The raw `f` is clamped at every training forward, so it cannot drift below
  the floor. The floor is inactive while `trace_minmax(reset=True)` parks `i` at −1e9; without that,
  `f` overflows to NaN (found and fixed here). `FlooredKIFConfig` carries the floor through `.keras`
  reloads.
- **How Chang does it:** jsc150 bounds the bit-count variable of a KBI quantizer: `bc=Min(1)` on the
  Linformer attention tables (`get_llformer`), `bc=Min(4)` on the xfm tables, and a commented
  datalane `kbi bc=Min(1)` scope before xfm's MHA. Our Q/K/V quantizers are KIF WRAP, where `i` is
  tracked and only `f` is trained, so no constraint on a single variable can bound
  `bits = relu(i+f)`. The floor gives the same guarantee (bits ≥ m at every step) without changing
  the parametrisation. See flag F3.
- **Tests:** `tree/tests/test_attn_bit_floor.py`, 8 tests:
  - with the key absent, no floored quantizer is built and the configs are unchanged;
  - at 1 bit the floor does not bind at init: same variables, traced EBOPs and forward as A at seed 1;
  - the site set is correct and 9 kinds of invalid key raise;
  - at the lower bound of every width, the floored Q/K/V read exactly 1 or 2 bits, the other WRAP widths read 0, and Q·K is billed (A: 0);
  - under EBOPs pressure the floored bits stay at 1 and the raw `f` stays at or above the bound;
  - a reload keeps the floor and the EBOPs;
  - one training step works.

### H3 floors (structural trace; target 350,000)

| floor | zero floor | headroom at 350k | status |
| --- | --- | --- | --- |
| none (A) | 171,526 | 178,474 | feasible |
| q, k, v at 1 bit | **269,830** | **80,170** | feasible |
| q, k, v at 2 bits | 564,742 | −214,742 | **STATIC_INFEASIBLE** |
| q, k, v, softmax_out at 1 bit | 368,134 | −18,134 | **STATIC_INFEASIBLE** (= A's `attn_narrow`) |

## Local smoke (RTX 4060 Ti 8 GB; exploration only, never quotable)

GPU TF works in `~/venv-hgq2` (TF 2.21.0, a CUDA 12.5 build) once `LD_LIBRARY_PATH` lists the venv's
`nvidia/*/lib` directories plus `/usr/lib/wsl/lib`. `smoke/run_smoke.sh` sets this. Without it TF
skips the GPU. Data: the first 10 sorted raw train files in `~/data/hls4ml_lhc_jet/train/train`
(90,000 train / 10,000 val after the tree's split, gate and standardisation). This is not the
cluster cache. Each run used the real `ablation.run_training` for 20 epochs, with the config
unchanged except epochs and the checkpoint cadence. Traces ran at epochs 0, 9 and 19, and the PID
stepped at epoch 10. TF32 was off.

| run | s/epoch untraced (median) | traced epochs (s) | task loss e0 → e9 → e19 | traced EBOPs e0 → e9 → e19 | other |
| --- | --- | --- | --- | --- | --- |
| A | 7.47 | 15.2, 15.1 | 1.543 → 1.001 → 0.992 | 12,740,873 → 11,309,574 → 6,764,588 | |
| NB | 7.73 | 16.1, 16.6 | 1.487 → 0.938 → 0.913 | 17,006,858 → 14,550,995 → 8,861,930 | mean weight bits 4.00 → 2.69; 0-bit fraction 0.0 |
| A + floor q,k,v 1 bit | 7.59 | 15.8, 16.0 | 1.543 → 1.037 → 0.979 | 12,739,422 → 11,175,630 → 6,781,006 | Q/K/V mean bits at e19 6.7/5.9/4.1, so the floor never bound |

In all three runs the loss decreases, EBOPs are counted, traced EBOPs fall after the PID step, and
nothing diverged. A projection, not a measurement: scaling linearly to the 558,000-row cache gives
about 46 s per untraced epoch on this card, which is slower than the 30.85 s per A07 epoch measured
on a 3090. This PC is useful for smoke tests and correctness checks, not for pilots.

## Not run, and why

- **The pytest-based suite and `cpu_gate.py`:** pytest is not in `~/venv-hgq2`, and these belong to the
  NRP CPU-gate Job. The new tests and `test_option_c_amendment.py` run under unittest (34 tests OK,
  `evidence/unittest_combined.log`).
- **[A22] pairing gate at all 8 seeds:** tested at seed 1 only. It belongs in the CPU gate.
- **Jev:** `lab_check_protocol` with a baseline was not run. `local/jev-protocols/` holds only
  synthetic fixtures and no frozen snapshot of the training-batch STUDY, and building one needs real
  dataset identity facts. `jev_check_methods` was run on the NB method text (audit
  `jv-c28ab9eab51f4dfca9758ce50b39666f`). Disposition: selection "consistent" (suggestion);
  comparability, uncertainty, provenance, metrics and authority "missing" (review). That is expected
  for engineering text with no PREFLIGHT, code sha, metric labels or intervals yet. Advisory only.
- **hls4ml export of NB or floored models:** untested, and not needed for the pilots.

## Flags

```
F1 DECISION: H3 pilot spec = q, k, v at 1 bit. At 2 bits, or with softmax_out added, the zero floor
  is above 350k (564,742 and 368,134): those R2 arms would be STATIC_INFEASIBLE.
  ALTERNATIVES: run H3 at a higher rung only; softmax_out alone was not traced.
  CONFIDENCE: HIGH (structural)   FLAG FOR HUMAN: YES (R2 design)
F2 DECISION: q,k,v at 1 bit leaves 80,170 EBOPs of headroom at 350k, against A's 178,474. The floor
  costs about 98k of the budget, so H3 at 350k also tests "attention alive, everything else starved".
  CONFIDENCE: HIGH (structural)   FLAG FOR HUMAN: YES
F3 DECISION: the floor is an effective-f clamp on KIF, not jsc150's KBI bc=Min(m).
  ALTERNATIVES: switch Q/K/V to KBI WRAP with bc=Min(m). That also changes the parametrisation and init
  (and ripples into matching_initialization, raw_widths and static_floor).
  CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
F4 DECISION: softmax_in at 1 bit is a no-op. The exp input is SAT with k=1, so it is always >= 1 bit.
  At 2 bits it forces one magnitude bit. inv_iq (WRAP, k0 0) can reach 0 and is not a site.
  CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
F5 DECISION: the [A22] check "a built NB layer is not on the int8 grid" cannot hold at init. The kbi
  grid at b 4, i 0 (step 2^-4) is a subset of the w8 grid (step 2^-5). Implemented as a structural
  check (trainable per-weight kbi, not the frozen KIF w8) plus off-grid values at 8 fractional bits.
  CONFIDENCE: HIGH   FLAG FOR HUMAN: YES (STUDY wording)
F6 DECISION: NB weight widths (b, i) sit with the weights. recovery_after_epochs freezes activation
  widths only, as Delta PLAN_patches noted. No pilot config sets it.
  CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
F7 DECISION: at floor 2 bits, init differs from A because some Q/K/V channels start below 2 bits
  (init EBOPs 9,023,635 vs 8,913,043). At 1 bit the init is identical.
  CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```
