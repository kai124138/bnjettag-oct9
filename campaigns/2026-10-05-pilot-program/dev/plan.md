# Pilot program dev — NB arm (0036) and attention bit floor (0037): plan

Owner: ml-engineer (engineering only). Started 2026-10-05 10:15 JST. Governing documents:
`docs/PILOT_PROGRAM.md` (H3, H5; R2/R3), `.claude/memory/decisions.md` (2026-10-05 10:08 entry),
`campaigns/2026-09-26-training-batch/STUDY.md` ([D22] l. 797-810 and 2263-2268, [A22] l. 2474-2494,
table l. 749), the released `reference-code/HGQ2-examples/jsc150/model.py`.
Nothing here launches, touches the cluster, or edits the option-(c) campaign. Numbers from this PC
are exploration only, never quotable.

## Base and layout

- `dev/tree/` = byte copy of `campaigns/2026-10-02-chang-option-c/code/tree` (42abed + 0032 + 0033),
  with a local git repo (`dev/tree/.git`) so each change is its own commit; the base commit is the
  unchanged copy.
- `dev/patches/0036-nb-arm.patch`, `dev/patches/0037-attention-bit-floor.patch`: `git diff` against
  the option-(c) tree, `a/` `b/` prefixes relative to the tree root, so they rebase on top of 0034
  (test env) and 0035 (pilot configs) written by another agent in `../patches/` (not touched here).
  0037 is written against the base too (independent of 0036) so either can land alone; the combined
  tree is checked to apply both.
- `dev/configs/`: example NB and H3 configs derived from `chang1002c-a-n64-s1` (exploration inputs
  for tests, floors and smoke; the pilot configs proper are 0035's job).
- `dev/evidence/`: logs (tests, floors, smoke) and the jsc150 quantizer dump.

## 0036 — NB arm ([D22], [A22])

Key: `quant.weight: "kbi_learnable"` — the name STUDY [A22] registers and `config.py` already
accepts (the brief's `kbi_learned` was an example; the registered name wins).

1. Dump the jsc150 `xfm` weight quantizer on the pin. `get_transformer` does not build on hgq2 0.1.9
   (`QEinsumDenseBatchnorm('...c,cC->...C')` raises in `_compute_fused_einsum_specs`; also
   `QLinformerAttentionT` import), so the dump enters the exact scope stack of
   `get_model('xfm', 7, 7, 1e-8, 64, True)` + `get_transformer` and builds the kernel-carrying layer
   types xfm uses (`QEinsumDense`, `QMultiHeadAttention` projections) on xfm shapes.
   Result (dumped, `evidence/jsc150_weight_quantizer_dump.json`): kbi, k0 1, b0 4, i0 0, RND,
   SAT_SYM, bc MinMax(0, 23), ic None, br MonoL1(1e-8), ir MonoL1(1e-8), i_decay_speed 1e-3 (inert
   under SAT_SYM), per-weight widths (homogeneous_axis ()), trainable.
2. `qat.py`: `_kbi_learnable_kq()` returning exactly that config; NB branch in `dense_einsum` and
   `dense` (plain `QEinsumDense`/`QDense`, same activation quantizers as A); the [A20] guard accepts
   binary or kbi; the builder raises on any `quant.weight` with no branch.
3. `ablation.py`: `binary_gate` dispatches NB configs to `nb_weight_gate` (expected layer set carries
   trainable kbi widths; kernels not on the static int8 grid; returns a per-layer width record);
   NB width record (fraction at 0 bits, mean bits) written to `ebops_budget.json` and to each
   epoch's history line only for NB. A configs take the unchanged path.
4. `static_floor.py`: an NB weight-width mode for the floors (weights at init 4 bits, and at 0/1 bit).
5. Tests (`tests/test_nb_arm.py`, unittest): builds; one train step; EBOPs bill real weight bits and
   a 0-bit weight costs 0; widths trainable and reach 0 under pressure; kernel hashes equal A's at
   init (pairing prerequisite); reload round-trip; A configs and A model unchanged (config bytes,
   model variables, init EBOPs vs base tree).

## 0037 — attention bit floor (H3)

Key: `quant.attn_bit_floor: {"bits": 1 | 2, "sites": [subset of "q", "k", "v", "softmax_in",
"softmax_out"]}`; absent = byte-identical. Mechanism: a registered `FlooredKIFConfig`/`FlooredKIF`
(subclass of HGQ2's KIF quantizer) whose effective `f` is `max(f, bits - i - k·[SAT])`, so HGQ2
`bits` (what EBOPs prices) never drops below the floor; the raw `f` is clamped at each training
forward so it cannot drift below the floor (no hysteresis). Serialises through `.keras` reload.

How Chang keeps attention >= 1 bit: in jsc150, a constraint on the bit-width variable of KBI
quantizers (`bc=Min(4)` on the xfm tables; `bc=Min(1)` on the Linformer attention tables in
`get_llformer`; a commented `QuantizerConfigScope(place='datalane', default_q_type='kbi',
bc=Min(1))` before xfm's MHA). Our Q/K/V quantizers are KIF WRAP (i tracked, f trained), where a
bit-count constraint on a single variable is impossible; the floor reproduces the same guarantee
(bits >= m at every step) without changing the parametrisation. Flagged below.

Tests (`tests/test_attn_bit_floor.py`): absent key -> identical model and EBOPs; key on, init
forward equal to A (floor inactive at init widths); at f = fc.min the floored sites read exactly m
bits and the others 0; EBOPs priced at m bits; reload keeps the floor; validation errors.
Floors: `static_floor.py` learns the floor (expected bits = max(base, m)); measure the zero floor
for q,k,v at 1 and 2 bits and q,k,v + softmax_out at 1 bit.

## Local smoke (RTX 4060 Ti; exploration only)

GPU TF works with `LD_LIBRARY_PATH` set to the venv's `nvidia/*/lib` dirs plus `/usr/lib/wsl/lib`
(checked 10:13 JST: `tf.config.list_physical_devices('GPU')` lists GPU:0). Data: no prepared cache
locally; `~/data/hls4ml_lhc_jet/{train,val}` holds the raw hls4ml files. Plan: a small local cache
from a few raw train files via the tree's own loader if it fits in time; else synthetic tensors.
Runs: A, NB and A + floor (q,k,v at 1 bit) through `ablation.run_training`, 10 epochs, small N,
target 350k, report s/epoch, loss trend, EBOPs counted.

## Approaches tried and failed

- Building the full jsc150 `xfm` on the pin for the dump: fails (see 0036 step 1).
- pytest is not installed in `~/venv-hgq2`; tests are unittest (pytest-compatible).

## Where I am not sure

See README.md "Flags" F1-F7 (H3 floor feasibility at 350k, KIF floor vs KBI bc=Min, the [A22] int8-grid wording, NB widths under recovery freeze).

## Approaches tried and failed (continued)

- FlooredKIF first version: NaN bits after `trace_minmax(reset=True)` (i parked at -1e9 -> f floor +1e9). Fixed by applying the floor only where i > -1e6.
- Equal per-layer EBOPs between NB at 1-bit weights and A: false beyond input_proj, because downstream traced activation ranges differ; the test compares input_proj only.
