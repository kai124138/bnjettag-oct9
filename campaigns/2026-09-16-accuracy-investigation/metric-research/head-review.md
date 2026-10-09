Frozen-head experiment review

No blocking leakage or fitting-math problem found in export_head_features.py and refit_head.py as reviewed. Staged experiment files were not changed.

The extractor checks the expected source checkpoint digest, raw training/validation tensor hashes, cached normalization agreement, and reconstructed source-index disjointness. The 100,000-row sample is drawn exclusively from the training partition. The fitting function derives its mean/std and loss/gradient exclusively from training features/labels. It selects the four prespecified ridge/weight-width candidates on validation accuracy under a measured EBOP constraint; held-out scores do not enter that selection.

Standardization folding is mathematically correct. Given x'=(x-m)/s, the warm-start parameters are W'=sW and b'=b+mW. Fitted parameters return to raw feature units as W=W'/s and b=b'-mW. A local independent synthetic test using 3,000 training and 1,000 validation examples, 32 features with unequal scales/nonzero means, and one constant feature verified maximum folded-logit error 2.06e-12. Twenty finite-difference derivative checks gave maximum relative error 3.07e-10. The optimizer converged in 36 iterations, objective 1.825877 to .103661, final gradient norm 1.67e-5, validation accuracy 98.3% on the known synthetic linear signal. This accuracy is only a regression-test outcome.

Integration considerations:

- Extracted features are already input-quantized, then old(xv) and head(xv) quantize them again. Inference quantization on a fixed power-of-two grid should be idempotent. Existing first-256-row comparisons against full native model inference are appropriate guards; an idempotence assertion would make the assumption explicit if the quantizer implementation changes.
- refit_head.py reports source-model SHA but does not independently verify the cached feature archive SHA against manifest.json/source-model SHA. The present isolated output directory and extractor's fixed expected checkpoint digest protect the intended run; future reused caches should enforce manifest/source matching at refit entry.
- Success=false optimizers are excluded, even if their unfinished solution might improve accuracy. This is a conservative bounded-experiment choice, not a fitting error.
- Post-training per-tensor weight quantization can lose improvements from the floating-point fit when channels have different scales; validation selection and the retained binary baseline prevent choosing a worse candidate. Neither binary-backbone preservation nor a native EBOP pass proves hardware latency/export equivalence for the newly mixed-precision head.
- Baseline held-out metrics are computed before candidate fitting in the script, but are not used by the fitting or selection code. The experiment remains exploratory after earlier held-out results have been inspected; fresh seeds/data are needed for a broader generalization claim.

Reproduce the CPU test: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 local/accuracy-investigation/metric-research/test_head_fit.py. Numerical evidence: head-fit-test-result.json.
