# Exported-graph ROC-test AUC (the five synthesized articles)
#
# metric : ROC-test macro one-vs-rest AUC on the held-out val split (n=260,000)
#          of the EXPORTED hardware graph (convert_final.build_export, beta=fx8,
#          the network actually synthesized) — NOT val AUC, NOT the QAT number
# arbiter: stored GATE1 corr_scores reproduced on the same 4,096 linspace jets
#          before each 260k eval (proves the rebuild is the shipped graph)
# era    : 2  (NEVER compare to era-1 numbers)
# gen    : 2026-08-24 by code/hgq2/export_roc_eval.py -> export_roc_auc.json

## Macro AUC: trained checkpoint vs exported graph

| article | config [hash] | trained AUC (ROC-test) | export AUC | delta (export-trained) | corr(scores) 260k | argmax agree 260k | GATE1 stored / reproduced (4,096) | n |
|---|---|---|---|---|---|---|---|---|
| n8-w1a8-s3 | r14-l1x3-n8-w1a8 [38a20c62] | 0.87241 | 0.87236 | -0.00005 | 0.998770 | 0.9786 | 0.998816 / 0.998816 (exact) | 260000 |
| n8-w1a6-s3 | r14-l1x3-n8-w1a6 [794e925f] | 0.87009 | 0.86991 | -0.00019 | 0.995003 | 0.9571 | 0.995176 / 0.995176 (exact) | 260000 |
| n8-w1a4-s3 | r14-l1x3-n8-w1a4 [5f839ab5] | 0.85333 | 0.85325 | -0.00008 | 0.982122 | 0.9123 | 0.983399 / 0.983399 (exact) | 260000 |
| n16-w1a8-s1 | r14-l1x3-n16-w1a8 [2ae656b6] | 0.89586 | 0.89553 | -0.00033 | 0.997210 | 0.9764 | 0.997384 / 0.997384 (exact) | 260000 |
| n8-gamma-sm4i0-s3 | r15-gamma-sm4i0-n8-w1a8 [ba72a91a] | 0.87233 | 0.87233 | +0.00000 | 0.997958 | 0.9759 | 0.998052 / 0.998052 (exact) | 260000 |

## Per-class AUC of the exported graph

| article | AUC(g) | AUC(q) | AUC(W) | AUC(Z) | AUC(t) | macro |
|---|---|---|---|---|---|---|
| n8-w1a8-s3 | 0.8165 | 0.8657 | 0.8918 | 0.8741 | 0.9137 | **0.8724** |
| n8-w1a6-s3 | 0.8130 | 0.8602 | 0.8910 | 0.8735 | 0.9118 | **0.8699** |
| n8-w1a4-s3 | 0.8018 | 0.8564 | 0.8544 | 0.8462 | 0.9074 | **0.8532** |
| n16-w1a8-s1 | 0.8522 | 0.8795 | 0.9198 | 0.9013 | 0.9249 | **0.8955** |
| n8-gamma-sm4i0-s3 | 0.8163 | 0.8631 | 0.8940 | 0.8754 | 0.9128 | **0.8723** |

## Provenance

- **n8-w1a8-s3**: ckpt `bnjettag/roc-results/r14/n8/_ckpt_dl/w1a8-s3/model_best.keras` · config `bnjettag/code/hgq2/configs/r14-l1x3-n8-w1a8.json` [38a20c62] · beta_mode fx8 · input_std `bnjettag/roc-results/r14/n8/_ckpt_dl/w1a8-s3/input_std.json` · trained ref recomputed from `bnjettag/roc-results/r14/n8/W1A8-s3.npz` (= 0.87241; roc_auc.md quotes 0.8724, consistent=True) · y-alignment vs npz: True · QAT recompute |d| vs npz = 9.9e-07 · GATE1 source `bnjettag/results/synthesis/runs/38a20c62/w1a8-s3-r14n8/export_verify.json`
- **n8-w1a6-s3**: ckpt `bnjettag/models/cache/r14-l1x3-n8-w1a6-s3/model_best.keras` · config `bnjettag/code/hgq2/configs/r14-l1x3-n8-w1a6.json` [794e925f] · beta_mode fx8 · input_std `bnjettag/models/cache/r14-l1x3-n8-w1a6-s3/input_std.json` · trained ref recomputed from `bnjettag/roc-results/r14/n8/W1A6-s3.npz` (= 0.87009; roc_auc.md quotes 0.8701, consistent=True) · y-alignment vs npz: True · QAT recompute |d| vs npz = 4.7e-07 · GATE1 source `bnjettag/results/synthesis/runs/794e925f/w1a6-s3/export_verify.json`
- **n8-w1a4-s3**: ckpt `bnjettag/models/cache/r14-l1x3-n8-w1a4-s3/model_best.keras` · config `bnjettag/code/hgq2/configs/r14-l1x3-n8-w1a4.json` [5f839ab5] · beta_mode fx8 · input_std `bnjettag/models/cache/r14-l1x3-n8-w1a4-s3/input_std.json` · trained ref recomputed from `bnjettag/roc-results/r14/n8/W1A4-s3.npz` (= 0.85333; roc_auc.md quotes 0.8533, consistent=True) · y-alignment vs npz: True · QAT recompute |d| vs npz = 7.4e-07 · GATE1 source `bnjettag/results/synthesis/runs/5f839ab5/w1a4-s3/export_verify.json`
- **n16-w1a8-s1**: ckpt `bnjettag/roc-results/r14/n16/_ckpt_dl/w1a8-s1/model_best.keras` · config `bnjettag/code/hgq2/configs/r14-l1x3-n16-w1a8.json` [2ae656b6] · beta_mode fx8 · input_std `bnjettag/roc-results/r14/n16/_ckpt_dl/w1a8-s1/input_std.json` · trained ref recomputed from `bnjettag/roc-results/r14/n16/W1A8-s1.npz` (= 0.89586; roc_auc.md quotes 0.8959, consistent=True) · y-alignment vs npz: True · QAT recompute |d| vs npz = 3.7e-07 · GATE1 source `bnjettag/results/synthesis/runs/2ae656b6/w1a8-s1-r14n16/export_verify.json`
- **n8-gamma-sm4i0-s3**: ckpt `bnjettag/models/cache/r15-gamma-sm4i0-n8-w1a8-s3/model_best.keras` · config `bnjettag/code/hgq2/configs/r15-gamma-sm4i0-n8-w1a8.json` [ba72a91a] · beta_mode fx8 · input_std `bnjettag/models/cache/r15-gamma-sm4i0-n8-w1a8-s3/input_std.json` · trained ref recomputed from `bnjettag/roc-results/r15-gamma/sm4i0/W1A8-s3.npz` (= 0.87233; roc_auc.md quotes 0.8723, consistent=True) · y-alignment vs npz: True · QAT recompute |d| vs npz = 1.3e-07 · GATE1 source `bnjettag/results/synthesis/runs/ba72a91a/w1a8-s3-r15gamma-sm4i0/export_verify.json`
