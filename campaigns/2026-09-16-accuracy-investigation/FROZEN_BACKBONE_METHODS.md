# Frozen-backbone classifier refitting: methods, theory, code, and results

Documentation date: **17 September 2026**. Experiments ran on 16 September PDT / 17 September UTC. This document describes the completed investigation; it does not claim a new experiment was run during documentation.

## 1. Main method: frozen-backbone classifier refitting

The strongest measured result came from **a frozen-backbone linear classifier refit followed by final-layer quantization**. I retained the channel-wise model's feature extractor, extracted its quantized 32-dimensional final-layer inputs, fitted a multinomial logistic-regression classifier on 100,000 training examples, and tested 4-bit and 8-bit versions of its weights. Candidate selection used internal validation accuracy subject to a measured 350,000-EBOP ceiling. The selected classifier has 160 eight-bit weights and five fitted floating-point biases; the 14 preceding weight layers remain binary.

A separate experiment fitted class-specific output offsets without changing the learned network weights. These are **two alternative models**, not two stages combined into one model.

| Alternative | Source model | Held-out top-1 accuracy | Held-out macro OvR AUC | Native model EBOPs |
|---|---|---:|---:|---:|
| Original best checkpoint | Channel-wise quantization, R1 | 58.7431% | 0.850795 | 317,890 |
| Frozen backbone + 8-bit final classifier | R1 | **59.1396%** | **0.855957** | **322,510** |
| Five rounded output offsets | Reduced feed-forward model, R2 | **59.0600%** | See correction records | 329,838 before separate correction arithmetic |

The refitted head improves accuracy by **0.3965 percentage points**, with a paired event-level 95% interval of **0.3191–0.4740 points**. Native EBOPs increase by **4,620, or 1.45%**. The new head is mixed precision; it must not be described as an entirely binary-weight model. Native EBOPs are a computational estimate, not measured FPGA latency or device resource utilization.

Evidence: [head experiment](head-features/head_report.json), [independent verification](head-features/independent_verification.json), [model structure](head-features/model_structure_verification.json), [saved model](head-features/selected_model.keras), and [output-correction parameters](results/selected_correction.json).

## 2. Dataset and experimental boundaries

Each input is the eight highest-transverse-momentum constituents, sorted by descending `pt` with stable tie handling. Each constituent has three features: `pt`, `etarel`, and `phirel`. Feature standardization comes from the original training split. Labels and score columns use the order **g, q, W, Z, t**.

| Data partition | Events | Use in this investigation |
|---|---:|---|
| Original training subset | 496,000 | Source of frozen features for head fitting; source of original input normalization |
| Head-fitting subset | 100,000 | Uniform sample without replacement from training, RNG seed 20260917 |
| Internal validation | 124,000 | Existing checkpoint selection; selection of the refitted head |
| Calibration fitting fold | 61,999 | Stratified half of internal validation; fit output corrections |
| Calibration selection fold | 62,001 | Other stratified half; select correction and numerical representation |
| Held-out evaluation archive | 260,000 | Evaluate fixed choices; never optimize candidate parameters on its labels |

The dataset publisher calls the separate held-out archive “validation”; project result files call it “test.” These refer to the same 260,000-event archive. The 124,000-event **internal validation** set is different.

For head fitting, the extraction script checked training and validation array hashes, reconstructed the split permutation, checked its hash, and verified that selected training source indices did not intersect validation source indices. This establishes the cached partition relationship; it is not a claim that all dataset files were exhaustively checked for duplicated physical events.

Calibration folds are disjoint from one another, but the original checkpoint was already selected using the full internal validation set. The investigation also reused the held-out archive to report sequential experiments. Candidate selection within each experiment used validation, but these results should still be treated as exploratory single-seed evidence, not a new untouched confirmatory study.

## 3. Theory: why accuracy and AUC can differ so much

### 3.1 Top-1 accuracy

For logits \(z_i\in\mathbb R^5\), the predicted class is

\[
\hat y_i=\arg\max_c z_{ic},\qquad
\mathrm{Accuracy}=\frac{1}{N}\sum_i\mathbf 1[\hat y_i=y_i].
\]

The true class must beat all four other scores on the same event. Softmax preserves their order, so logits and softmax probabilities give the same argmax, apart from finite-precision ties.

### 3.2 Macro one-versus-rest AUC

For each class \(c\), AUC compares scores for positive and negative examples:

\[
\mathrm{AUC}_c=\Pr(s_c(X^+)>s_c(X^-))
+\tfrac12\Pr(s_c(X^+)=s_c(X^-)),
\qquad
\mathrm{MacroAUC}=\frac15\sum_{c=1}^{5}\mathrm{AUC}_c.
\]

The project uses softmax probabilities for these class scores. AUC compares a score **across events**; accuracy compares different class scores **within an event**. Therefore, 0.85 AUC does not imply 85% categorical accuracy. The [scikit-learn multiclass ROC explanation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_roc.html) describes the OvR construction.

This normalized synthetic example, included in the regression tests, has **AUC 1.0 for every class but only 20% accuracy**:

| True class | Score g | Score q | Score W | Score Z | Score t | Predicted class |
|---|---:|---:|---:|---:|---:|---|
| g | 0.80 | 0.05 | 0.05 | 0.05 | 0.05 | g |
| q | 0.55 | 0.30 | 0.05 | 0.05 | 0.05 | g |
| W | 0.55 | 0.05 | 0.30 | 0.05 | 0.05 | g |
| Z | 0.55 | 0.05 | 0.05 | 0.30 | 0.05 | g |
| t | 0.55 | 0.05 | 0.05 | 0.05 | 0.30 | g |

Each class's positive example has the largest score in its column, yet g wins every row. This is a mathematical counterexample, not an estimate of actual model performance.

### 3.3 Other metrics that can mislead

Counting correctness separately across five one-hot entries is **binary entry-wise accuracy**, not jet classification accuracy. An all-negative output already scores 80% by that metric. For archived N=8 W1A8 seed 1, entry-wise threshold accuracy was 86.010%, while categorical accuracy was 62.401%.

Scalar temperature scaling,

\[
p_c=\operatorname{softmax}(z/T)_c,\quad T>0,
\]

cannot change the argmax in exact arithmetic. It can improve probability calibration but cannot fix top-1 accuracy by itself. Class-specific biases or scales can change the winner. Also, a class-specific logit transformation need not preserve **softmax-based** OvR AUC because the probability denominator changes per event. [Guo et al., section 4.2](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf) provides the calibration background.

## 4. First establish the actual measurements

### 4.1 Archived predictions

I recomputed metrics from all 60 existing Round-14 prediction archives. Checks included valid one-hot labels, class counts, identical event/label order, finite normalized probabilities, ties, all class-column permutations, confusion matrices, top-2 accuracy, and agreement with saved AUC metadata. All 60 archived AUCs agreed within \(10^{-12}\); the identity column permutation gave the highest categorical accuracy in every archive. This is evidence against a systematic class-order error, not proof that every possible pipeline defect is absent.

| Archived configuration | Mean accuracy | Mean AUC | Training seeds |
|---|---:|---:|---:|
| N=8, FP32 | 64.628% | 0.88643 | 3 |
| N=8, W8A8 | 64.481% | 0.88622 | 3 |
| N=8, W1A8 | 62.236% | 0.87122 | 3 |
| N=16, W1A8 | 67.520% | 0.89561 | 3 |

These are fixed-precision models, not matched 350k-budget ablations. For N=8 W1A8 seed 1, g/q and W/Z mutual confusion accounted for 40.35% of errors. The corresponding pair-restricted AUCs were approximately 0.755 and 0.835. Thus, a high overall OvR AUC can coexist with difficult specific class pairs. Full seed uncertainties and comparisons are in the [archive audit](prediction-audit/README.md).

The related [Ultrafast jet classification paper, Table 1](https://arxiv.org/html/2402.01876v2) reports eight-constituent MLP accuracy of 64.6% alongside class AUCs of 0.84–0.92. This supports the metric interpretation; different splits and preprocessing prevent a direct ranking against our models.

### 4.2 Fresh checkpoint evaluation

I ran one CPU batch job on Nautilus, using the existing code bundle and dataset volume. The exporter read each run's committed checkpoint generation, copied its paired state/model into a new snapshot, and saved validation and test logits once. It recorded SHA-256 digests and recomputed native HGQ2 EBOPs. Copying from the committed generation avoids pairing a changing live model with unrelated checkpoint-selection metadata.

| Checkpoint | Held-out accuracy | Held-out macro AUC | Native EBOPs |
|---|---:|---:|---:|
| R0 tensor-wise | 57.4758% | 0.844527 | 348,526 |
| R1 channel-wise | 58.7431% | 0.850795 | 317,890 |
| R2 reduced feed-forward | 58.3131% | 0.853526 | 329,838 |
| R3 8-bit attention probabilities | 57.3435% | 0.845380 | 340,174 |
| R4 gradual budget | 57.5085% | 0.846941 | 349,550 |
| R5 fixed-width recovery | 56.9404% | 0.840727 | 349,390 |
| R6 distillation, interim | 56.9123% | 0.841338 | 348,366 |

All rows use the same 260,000 held-out events. R4 had become feasible since the preceding published snapshot. R6 is explicitly an interim checkpoint. The previously reported R1 AUC of 0.851884 was a **different-split validation-selection measurement**.

Minimal metric computation, equivalent to the independent verification:

```python
import numpy as np
from scipy.special import softmax
from sklearn.metrics import roc_auc_score

truth = y_onehot.argmax(axis=1)
accuracy = np.mean(logits.argmax(axis=1) == truth)
probabilities = softmax(logits.astype(np.float64), axis=1)
per_class_auc = roc_auc_score(y_onehot, probabilities, average=None)
macro_auc = per_class_auc.mean()
```

All 14 fresh validation/test AUC calculations matched an independent sklearn calculation within \(10^{-12}\). Fresh CPU validation AUC did not exactly reproduce historical training selection AUC: the largest difference was \(8.245\times10^{-5}\), for R1. Float32 versus float64 softmax explained only about \(2\times10^{-8}\) there. Inspection of the SAT quantizers found no evidence that the EBOP tracing path changed learned widths. CPU/GPU arithmetic and ties remain hypotheses; this residual is retained as unresolved rather than hidden. See [reproducibility review](metric-research/auc-reproducibility-review.md).

## 5. Method A: class-specific output correction

### 5.1 Parameterization and selection

The candidate decision rule was

\[
\hat y=\arg\max_c(a_c z_c+b_c).
\]

| Candidate | Fitting procedure | Effective free parameters |
|---|---|---:|
| Identity | No fitting | 0 |
| Bias by NLL | Minimize softmax negative log-likelihood; anchor last bias at zero | 4 |
| Vector scaling by NLL | Fit positive scales and anchored biases | 9 |
| Bias by accuracy | Coordinate threshold proposals, accept only realized accuracy improvements | 4 relative biases |
| Vector scaling + accuracy bias | NLL scales, then coordinate bias refinement | 9 effective parameters |

The NLL fitter used L-BFGS-B, up to 100 iterations and `ftol=1e-10`. Biases were bounded to [-3, 3]; vector log-scales were bounded to [-2, 2], making scales positive. These fits used parameter bounds, not an added ridge penalty. The bias accuracy search made at most four coordinate passes. For each coordinate, it considered score-crossing thresholds, exact ties, interval midpoints and bounds, and verified actual floating-point argmax accuracy before accepting an update. It is a coordinate heuristic, not a proof of global optimum.

The stratified fit/selection split used seed 20260917. Each arm's correction was chosen by selection-fold accuracy; exact ties favored fewer fitted parameters. The arm itself was also chosen using selection-fold accuracy. Held-out labels were not used by these choice rules. See [calibrate_outputs.py](calibrate_outputs.py).

### 5.2 Rounding experiment and usable constants

For the selected correction, I compared explicit float32 arithmetic and constants rounded to 8, 10, 12 or 16 fractional bits. Selection again used the internal selection fold. R2's selected representation was 10 fractional bits:

```python
# R2 checkpoint only; class order g, q, W, Z, t.
bias = np.array([
    0.3115234375, 0.0908203125, 0.322265625,
    0.0, -0.255859375,
], dtype=np.float32)
corrected_logits = np.add(logits.astype(np.float32), bias,
                          dtype=np.float32)
predicted_class = corrected_logits.argmax(axis=1)
```

All selected scales are one, so this is equivalent to the staged multiply/add implementation in [apply_correction.py](apply_correction.py). That script also checks the caller-supplied checkpoint identifier. The constants must not be applied to another checkpoint or to probabilities instead of logits.

| Comparison | Accuracy gain, percentage points | Paired event-level 95% interval |
|---|---:|---:|
| R2 float64 correction versus original R2 | +0.7381 | [0.6369, 0.8393] |
| R2 rounded correction versus original R2 | +0.7469 | [0.6424, 0.8514] |
| R2 rounded correction versus original R1 | +0.3169 | [0.1629, 0.4709] |

The rounded correction reaches 59.0600%. It shifts class recall: g and W improve, while q, Z and t decline. The R1 validation-selected correction slightly reduced its held-out accuracy; that negative result is retained in [calibration_report.json](results/calibration_report.json). The correction is therefore not a universal improvement for every model.

![R2 confusion matrices before and after rounded correction](results/confusion.png)

This test quantized **constants**, not the entire arithmetic pipeline. Saturation, FPGA accumulator precision, fused operations and folding into the existing bias were not validated. The baseline R2 model costs 329,838 native EBOPs; a separately applied correction is not included in that number.

## 6. Main experiment: frozen-backbone classifier refit

### 6.1 Extract the correct features

Let \(h_i\in\mathbb R^{32}\) be the frozen backbone output after the original final layer's input quantizer. The original logits are

\[
z_i=h_iW_0+b_0,\qquad W_0\in\mathbb R^{32\times5}.
\]

Extracting the quantized features preserves the activation grid on which the real final classifier operates:

```python
head = model.get_layer("head_fc2")
backbone = keras.Model(model.inputs, head.input)
h = head.iq(backbone(x, training=False), training=False)
reconstructed = h @ head.qkernel + head.qbias
```

The extractor compared this reconstruction with the full original model on 256 validation examples, requiring numerical agreement within the stated tolerances and identical predicted classes. It then cached 100,000 training, 124,000 validation and 260,000 held-out feature vectors. Full original validation/test accuracy was reproduced. The feature cache stayed on the remote volume to avoid transferring approximately 62 MB of uncompressed feature arrays.

Source: [export_head_features.py](export_head_features.py). Cache hashes and index-disjointness evidence: [manifest.json](head-features/manifest.json).

### 6.2 Objective and optimizer

For optimizer conditioning only, standardize these **head features** using statistics from the 100,000 fitting examples:

\[
\tilde h_j=(h_j-\mu_j)/\sigma_j.
\]

Standard deviations below \(10^{-6}\) are replaced by 1. This second standardization is separate from the model's original input preprocessing. Fit weights \(V\) and biases \(c\) by minimizing

\[
L(V,c)=\frac1n\sum_i\left[
\log\sum_k\exp((\tilde h_iV+c)_k)
-(\tilde h_iV+c)_{y_i}\right]
+\frac{\lambda}{2}\lVert V\rVert_F^2.
\]

This is multinomial logistic regression with L2 regularization on the standardized-coordinate weights; biases are not penalized. The fitting objective is cross-entropy, while **model selection uses accuracy**. Because the backbone is fixed, optimization involves only 160 weights and five biases. No gradients are propagated through the transformer.

Core implementation from [refit_head.py](refit_head.py), with `x` denoting standardized training features:

```python
def objective(p):
    w, b = p[:-5].reshape(-1, 5), p[-5:]
    z = x @ w + b
    loss = np.mean(logsumexp(z, axis=1) - z[np.arange(len(y)), y])
    loss += ridge * np.sum(w * w) / 2
    residual = softmax(z, axis=1)
    residual[np.arange(len(y)), y] -= 1
    gradient = np.r_[
        (x.T @ residual / len(y) + ridge * w).ravel(),
        residual.mean(0),
    ]
    return loss, gradient

result = minimize(objective, start, method="L-BFGS-B", jac=True,
                  options={"maxiter": 150, "ftol": 1e-9})
```

Warm-start parameters reproduce the original classifier in standardized coordinates: \(V_0=\operatorname{diag}(\sigma)W_0\), \(c_0=b_0+\mu W_0\). After fitting, fold normalization back into the final classifier:

\[
W=\operatorname{diag}(1/\sigma)V,\qquad b=c-\mu W.
\]

Thus, inference does not require an additional feature-standardization layer. An independent synthetic test checked the gradient by finite differences (maximum error \(3.07\times10^{-10}\)) and the folding algebra (maximum logit error \(2.06\times10^{-12}\)). See [test_head_fit.py](metric-research/test_head_fit.py).

### 6.3 Quantize only the final kernel

For each converged fit, construct signed 4-bit and 8-bit kernels with a per-tensor power-of-two step:

\[
e=\left\lceil\log_2\frac{\max|W|}{2^{B-1}-1}\right\rceil,
\quad \Delta=2^e,\quad
W_q=\Delta\operatorname{clip}\left(\operatorname{round}_{\rm even}(W/\Delta),
-2^{B-1},2^{B-1}-1\right).
\]

The implementation guards a zero maximum magnitude with \(10^{-12}\). HGQ2 performs the actual quantization using a `QDense` final layer; the existing input-quantizer weights are copied unchanged:

```python
quant = QuantizerConfig(
    "kif", "weight", k0=1,
    i0=bits - 1 + step_exponent, f0=-step_exponent,
    round_mode="RND_CONV", overflow_mode="SAT",
    trainable=False, heterogeneous_axis=(),
)
layer_cfg = dict(old_head.get_config())
layer_cfg["name"] = candidate_name
layer_cfg["kq_conf"] = keras.saving.serialize_keras_object(quant)
head = QDense.from_config(layer_cfg)
candidate = keras.Model(model.inputs, head(old_head.input))
head.iq.set_weights(old_head.iq.get_weights())
head._kernel.assign(w.astype("float32"))
head.bias.assign(b.astype("float32"))
cost = compute_ebops(candidate, raw_validation_inputs[:256])["total"]
```

This is post-fit quantization of a refitted linear head, **not end-to-end quantization-aware retraining**. Biases retain the existing dummy/float bias quantizer. The selected kernel uses one sign bit, two integer bits excluding sign, and five fractional bits: a step of 1/32. Observed effective weights range from -3.125 to 2.40625, exactly on that grid.

### 6.4 Candidate results, including failures

| Head candidate | Ridge strength | Optimizer outcome | Validation accuracy | Native EBOPs | Decision |
|---|---:|---|---:|---:|---|
| Original binary head | — | Existing checkpoint | 58.8879% | 317,890 | Baseline eligible |
| Refitted head | 0.0001 | Hit 150-iteration limit | Not evaluated as eligible | — | Excluded |
| Refitted 4-bit head | 0.01 | Converged in 51 iterations | 58.4806% | 319,870 | Lower accuracy |
| Refitted 8-bit head | 0.01 | Converged in 51 iterations | **59.3871%** | **322,510** | Selected |

The two ridge strengths and bit widths were fixed before this head experiment's candidate evaluation. Only converged, budget-feasible candidates could replace the original model. The decision rule maximized `(validation_accuracy, -ebops)`. The held-out score for the new candidate was computed after that choice. The unsuccessful fit was not extended or silently removed from the record.

The saved selected model was reloaded remotely and its output and EBOP count checked again. Full held-out predictions were evaluated from cached frozen features through the selected native head; equivalence with the full candidate model was checked on 256 validation inputs. This was not a second full end-to-end inference pass over all 260,000 held-out inputs after model reload.

### 6.5 Per-class result and interpretation

| True class | Original R1 recall | Refitted-head recall |
|---|---:|---:|
| g | 47.8437% | 50.2099% |
| q | 55.9265% | 54.4761% |
| W | 64.1964% | 65.0866% |
| Z | 51.2257% | 52.4016% |
| t | 74.3645% | 73.3054% |

The gain is not uniform across classes. It demonstrates that a modest improvement is possible without changing the backbone; it does not prove that final-layer bit width alone explains the gain, because both fitting and precision changed. A matched refit of a strictly binary head would be needed to isolate the precision effect.

## 7. Statistical treatment

Predictions are paired on the same held-out events. For each event define

\[
d_i=\mathbf1[\text{new correct}]-\mathbf1[\text{old correct}],\quad
\hat\Delta=\overline d,\quad
\mathrm{CI}_{95}=\overline d\pm1.96\frac{s_d}{\sqrt N}.
\]

```python
d = (new.argmax(1) == truth).astype(float) - (old.argmax(1) == truth)
delta = d.mean()
half_width = 1.96 * d.std(ddof=1) / np.sqrt(len(d))
ci95 = (delta - half_width, delta + half_width)
```

The refitted head corrected 5,796 previously wrong events and broke 4,765 previously correct events: **1,031 additional correct classifications out of 260,000**. Multiply fractional deltas and interval limits by 100 to express percentage points.

| Paired comparison | Accuracy delta, percentage points | Approximate 95% interval |
|---|---:|---:|
| Refitted R1 head versus original R1 | +0.3965 | [0.3191, 0.4740] |
| Refitted R1 head versus rounded R2 correction | +0.0796 | [-0.0719, 0.2312] |

The head has the highest observed accuracy, but the second interval includes zero: these data do not establish that it is more accurate than the rounded-bias alternative. These intervals assume event-level sampling and condition on fixed trained models; they do not include seed variation, model-search uncertainty or unmodeled event dependence. Archive comparisons across three training seeds used a separate paired Student-t interval with two degrees of freedom; events from multiple seeds were not treated as independent replications.

## 8. Training-code correction

The original ablation loop logged training-batch `categorical_accuracy` alongside independently computed `val_macro_auc`, without validation accuracy. Its feasible checkpoint selection optimized validation AUC only. The separately published held-out accuracy was still calculated correctly.

I changed [publication/code/hgq2/bnhgq2/ablation.py](../../publication/code/hgq2/bnhgq2/ablation.py) to measure validation accuracy using the existing validation logits, log explicit training and validation fields, and permit accuracy-based selection for **new** experiments:

```python
cfg["experiment"]["selection_metric"] = "val_categorical_accuracy"

# For a budget-feasible checkpoint, maximize:
key = (point["val_categorical_accuracy"], point["val_macro_auc"],
       -point["ebops"], -point["epoch"])
```

Default selection remains AUC, followed by lower cost and earlier epoch. Accuracy selection uses AUC as its first tie-breaker. Configuration/code digest guards reject incompatible resumes. Existing historical checkpoint points without accuracy remain usable for default AUC selection; missing historical accuracy is not fabricated. Unconstrained best-AUC checkpoint semantics are retained, and infeasible fallback metadata identifies minimum-cost fallback honestly.

This change adds no validation inference pass. It is a reporting/selection improvement, not the source of the measured 59.1396% result: that result came from the separate frozen-head experiment. Active historical training was not patched.

## 9. Compute use and verification

Three agents independently handled the archive audit, code/theory review, and compute inventory. Local CPU processes performed numerical analysis; Nautilus ran bounded inference and fitting jobs; Mulder provided an independent numerical/arithmetic check. No new full transformer training or GPU allocation was needed for this investigation.

| Work | Location and resource bound | Measured duration / outcome |
|---|---|---|
| Audit 60 archived prediction files | Local, one numerical process | About 16 seconds |
| Seven-checkpoint evaluation | Nautilus, 4 CPU / 8 GiB, 1,800-second deadline | 761-second job; each 260k test inference about 33–35 seconds |
| Save/resume integration tests | Nautilus, 2 CPU / 8 GiB, 900-second deadline | Successful job 204 seconds; three two-epoch synthetic cases |
| Frozen feature extraction | Nautilus, 4 CPU / 8 GiB, 900-second deadline | Extraction 264 seconds; subsequent fitter initially failed on missing SciPy |
| Head-fit retry using cached features | Nautilus, 4 CPU / 8 GiB, 600-second deadline | Job 80 seconds; fitting/evaluation 25.39 seconds |
| Metric/arithmetic cross-check | Mulder, one thread, 30-second timeout | Approximately 12 seconds, existing Python/NumPy |

The first integration attempt also lacked scikit-learn. Both dependency failures and actual submitted-job records are retained. Corrected manifests include the required packages. Cached outputs were reused, and temporary Jobs/ConfigMaps were removed after evidence retrieval. Persistent data remain on the project's volume.

The model architecture retains the same final 32×5 matrix dimensions. Higher weight precision increases computational cost and can change synthesis mapping; no assumption of unchanged FPGA latency is made. Mulder's warm vectorized bias-add throughput measurement excluded inference and argmax and is not a single-event hardware latency measurement. HLS synthesis, place-and-route, and export accumulator equivalence were not performed.

| Verification | Evidence / result |
|---|---|
| Archived AUC and prediction integrity | All 60 archived AUCs reproduced; label/order/normalization checks |
| Fresh prediction metrics | 14 validation/test AUC comparisons agree with sklearn within 1e-12 |
| Snapshot identity and EBOPs | SHA-256 checks and seven native cost remeasurements |
| Calibration and representation behavior | Nine focused tests for synthetic recovery, tie handling, monotonic accepted updates, temperature invariance, selection and paired intervals |
| Checkpoint-selection helpers | Six regression tests |
| Real TensorFlow/HGQ2 save/resume | Accuracy-feasible, AUC-feasible and accuracy-infeasible cases passed |
| Head fitting mathematics | Gradient and normalization-folding checks on disjoint synthetic samples |
| Selected model | Reload, numerical checks, quantization-grid check, 14 binary layers + one QDense head |
| Repository validation | 50 Python sources and 36 configurations passed |

## 10. Code and artifact map

All paths in this table are relative to this document. The full executable scripts are the authority; abbreviated snippets above explain their core operations.

| File | Purpose |
|---|---|
| [prediction-audit/audit.py](prediction-audit/audit.py) | Recompute archived metrics and integrity diagnostics |
| [export_diagnostics.py](export_diagnostics.py) | Export paired validation/test logits from committed checkpoints |
| [diagnostic-job.yaml](diagnostic-job.yaml) | Resource-bounded seven-model evaluation manifest |
| [calibrate_outputs.py](calibrate_outputs.py) | Fit and select bias/vector corrections |
| [check_deployment_stability.py](check_deployment_stability.py) | Select numerical representation on validation |
| [apply_correction.py](apply_correction.py) | Apply saved correction with a checkpoint identifier guard |
| [export_head_features.py](export_head_features.py) | Extract frozen quantized features and verify split provenance |
| [refit_head.py](refit_head.py) | Fit, quantize, budget-check, select and save the final classifier |
| [head-feature-job.yaml](head-feature-job.yaml) | Corrected combined extraction/refit manifest |
| [head-refit-job.yaml](head-refit-job.yaml) | Retry using existing feature cache |
| [verify_new_predictions.py](verify_new_predictions.py) | Independent sklearn checks and paired comparisons |
| [test_calibrate_outputs.py](test_calibrate_outputs.py), [test_deployment_stability.py](test_deployment_stability.py) | Correction tests |
| [metric-research/test_selection.py](metric-research/test_selection.py) | Selection and metric regression tests |
| [metric-research/integration_smoke.py](metric-research/integration_smoke.py) | Real training/save/resume smoke test |
| [metric-research/test_head_fit.py](metric-research/test_head_fit.py) | Synthetic fitting/gradient/folding verification |
| [head-features/selected_model.keras](head-features/selected_model.keras) | Experimental mixed-precision model |
| [head-features/input_std.json](head-features/input_std.json) | Original training-set input normalization |
| [head-features/selected_model_metadata.json](head-features/selected_model_metadata.json) | Input contract, class order, identity and results |
| [results/selected_correction.json](results/selected_correction.json) | Separate R2 bias-correction parameters |

Important checkpoint identities:

```text
Original R1 channel model:
d76050090655a68546e8bee51b695ef34c42083bcbd52832758b96f0e06f6e4c

Original R2 reduced-feed-forward model, for the bias correction:
cf3894ba89e0427bcf92d3e6aa16068d82adc7e7f9fceea8e13b2703ac5af86c

Selected R1 mixed-precision model:
579d207239058282cbb54ff8321e61f51367331f6d367489849d452844fd26e4
```

### 10.1 Recompute local analysis

Run from the **lab repository root**, using a Python environment with NumPy, SciPy and scikit-learn:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

python3 local/accuracy-investigation/prediction-audit/audit.py
python3 local/accuracy-investigation/calibrate_outputs.py \
  local/accuracy-investigation/remote-results
python3 local/accuracy-investigation/check_deployment_stability.py \
  local/accuracy-investigation/remote-results
python3 local/accuracy-investigation/verify_new_predictions.py
python3 -m unittest discover -s local/accuracy-investigation -p 'test_*.py'
python3 local/accuracy-investigation/metric-research/test_selection.py
```

These commands require the original archived predictions and downloaded `remote-results/` arrays; the large binaries are locally available but ignored by Git. Analysis scripts rewrite their generated report JSONs. For archival reproduction, copy the input directories first and preserve the recorded report hashes.

### 10.2 Remote reproduction dependencies

The recorded inference/head-fitting environment used Python 3.12, TensorFlow 2.21.0, Keras 3.15.0, HGQ2 0.1.9, quantizers 1.2.2, h5py 3.14.0, hls4ml 1.3.0, NumPy 2.5.0 and SciPy 1.18.0. The training integration additionally required scikit-learn 1.9.0. Local verification used a different NumPy environment, so recorded environment versions accompany results.

The YAMLs depend on namespace `cms-ml`, PVC `kai-data`, existing training ConfigMap `kai-ebops-abl-code-64d7fd909b`, and separately staged diagnostic scripts. They are experiment manifests, not standalone portable launchers. Training code archive SHA-256:

```text
64d7fd909bd71c731f882bc3344e69c055d7abed10087a460c767787882e063c
```

Remote persistent artifacts are under `/data/accuracy-diagnostics-20260917` and `/data/accuracy-head-features-20260917`. Temporary diagnostic ConfigMaps were deleted, so they must be recreated before rerunning their Jobs. Several extraction paths use `exist_ok=False`; a fresh rerun needs new output paths, adjusted script references and unique resource names. The head-refit manifest instead assumes the existing feature cache and may overwrite its selected-model/report outputs. Review these paths before a rerun; the documentation commands above do not launch remote work automatically.

## 11. What the evidence establishes—and what remains open

The accuracy–AUC gap is primarily explained by different metric definitions together with real class confusion. The logging/selection mismatch was actionable, but it did not make the published argmax accuracy incorrect. The frozen-head experiment provides a modest measured improvement within the native cost budget, and the bias experiment offers a separate option with binary network weights retained.

The observed gains are conditional on one trained backbone and one dataset. Fresh seeds and untouched evaluation data are needed for stronger confirmation. The higher-precision head's export compatibility, FPGA area, accumulator precision and latency have not been established. The existing strict all-binary training/export gates should not be assumed to accept a model with a QDense final layer without explicit support. Improvements to total accuracy also trade off per-class recall; deployment criteria should include the desired class-specific efficiencies and mistag rates.

This work did not demonstrate that 85% categorical accuracy is attainable with these inputs or under this cost ceiling, nor that the final classifier is the sole bottleneck.
