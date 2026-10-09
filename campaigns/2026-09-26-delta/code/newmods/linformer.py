"""attn-linformer: binary sequence projections E, F (N -> k) on K and V (Delta M004, M053, M054,
M056, M060; card A10). T2 new module; training side only.

Source: Wang, Li, Khabsa, Fang, Ma, "Linformer: Self-Attention with Linear Complexity",
arXiv:2006.04768 (2020): K' = E K, V' = F V with E, F in R^{k x N}, attention softmax(Q K'^T /
sqrt(d)) V'. Re-implemented; nothing lifted from HGQ2-examples (no LICENSE there).

Here E and F are binary {-beta, +beta} kernels (qat.BitQEinsumDense, absmean STE, 1-bit KBI
kq for EBOPs), shape (N, k), shared across heads (Linformer "headwise sharing"), no bias. The
scores are (B, H, N, k) instead of (B, H, N, N), so the softmax and the Q.K and A.V products
shrink by N/k (64/8 = 8 at the Delta default linformer_k 8).

**Export gap (follow-up, not done here).** hgq2 0.1.9 has no QLinformerAttentionT (checked
in the pinned wheel, code-surface §0), and convert_binary.py / build.py know no sequence
projection. Nothing trained with this layer can go to hls4ml until that export path exists;
no synthesis or DSP claim may be made for it.

Wiring (WIRING.md): inside qat.build_qat_model's block loop, when cfg['arch'].get('attn_kind')
== 'linformer', replace the scores / softmax / ctx lines with a call to `linformer_attention`,
passing the builder's own closures (`dense_einsum`, `einsum`, `softmax`, `stream_iq`) and the
softmax-output quantizer conf it already builds; add `linformer_binary_layers(cfg)` to
ablation.expected_binary_layers; matching_initialization copies every other kernel by path
and shape, so an arm pairs "if hash" with the anchor (Delta pairing rule).
"""
from __future__ import annotations

from hgq.layers.ops.einsum import QEinsum


def linformer_attention(blk, q, k, v, *, lin_k, dense_einsum, einsum, softmax, attn_iq, stream_iq, scale):
    """q, k, v: (B, T, H, E) KerasTensors -> ctx (B, T, H, E), the shape the standard path yields.

    dense_einsum(name, equation, out_shape, x, bias_axes=None) is qat.build_qat_model's
    closure (binary kernel, activation quantizer on its input, calibration tap). einsum and
    softmax are its closures too; attn_iq is the softmax-output quantizer conf; stream_iq()
    returns a fresh stream quantizer conf."""
    T, H, E = int(k.shape[1]), int(k.shape[2]), int(k.shape[3])
    if not 1 <= int(lin_k) <= T:
        raise ValueError(f'linformer_k must be in [1, n_part={T}]; got {lin_k}')
    kp = dense_einsum(f'{blk}_attn_Elin', 'bthe,tk->bkhe', (int(lin_k), H, E), k)
    vp = dense_einsum(f'{blk}_attn_Flin', 'bthe,tk->bkhe', (int(lin_k), H, E), v)
    scores = einsum(f'{blk}_attn_scores', 'bthe,bkhe->bhtk', [q, kp], [stream_iq(), stream_iq()])
    attn = softmax(f'{blk}_attn_softmax', scores, scale)
    return QEinsum('bhtk,bkhe->bthe', iq_confs=[attn_iq, stream_iq()], name=f'{blk}_attn_ctx')([attn, vp])


def linformer_binary_layers(cfg):
    """Extra binary layer names a Linformer model carries (for expected_binary_layers)."""
    if cfg['arch'].get('attn_kind') != 'linformer':
        return set()
    return {f'bit_block_{i}_attn_{s}' for i in range(cfg['arch']['n_layers']) for s in ('Elin', 'Flin')}
