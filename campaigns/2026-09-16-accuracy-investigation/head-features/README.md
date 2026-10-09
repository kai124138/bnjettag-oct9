# Frozen final-head experiment

The selected R1 channel model improved from **58.7431% to 59.1396%** held-out accuracy on the same 260,000 jets after fitting only its final 32×5 classifier to 100,000 training examples. Held-out macro one-versus-rest softmax AUC rose from **0.850795 to 0.855957**. The paired accuracy gain was **0.39654 percentage points**, with an event-level approximate 95% interval of **0.31908–0.47399 points**. This interval does not represent variation between training seeds.

The selected final head has 160 eight-bit weights. Fourteen earlier weight layers retain their binary classes and weights. Native HGQ2 EBOPs increased from **317,890 to 322,510**, a **1.45%** increase, below the existing 350,000 budget. Kernel values lie exactly on a 1/32 grid within signed 8-bit range. FPGA synthesis, LUT/DSP/FF resources, accumulator/export equivalence, and actual hardware latency remain unmeasured. This is a mixed-precision model; it must not be described as fully binary.

Two fixed ridge strengths, 0.0001 and 0.01, were tried on the training subset only. The first reached its prespecified 150-iteration limit and was excluded; no additional fitting was performed. The second converged in 51 iterations. Its 4-bit and 8-bit quantized heads were compared on the complete internal validation split, with the original binary head also eligible. Only the selected 8-bit candidate was evaluated on held-out data. Its validation accuracy was 59.3871%; the 4-bit candidate scored 58.4806%, below the original 58.8879%.

Training features came exclusively from a seed-20260917 sample of the original 496,000-example training cache. Cache hashes, split-permutation hash, and disjoint training/validation source indices were verified. The original frozen quantized head input and effective kernel/bias reconstructed complete-model logits for 256 validation examples within 1e-5 with identical argmax. The selected saved model was reloaded remotely; output fidelity and 322,510 native EBOPs were verified again. Local checks independently recomputed both held-out accuracies, checked model SHA, and inspected the stored 14 binary layers plus one QDense head.

Artifacts:

- `selected_model.keras`: selected experimental model, SHA256 `579d207239058282cbb54ff8321e61f51367331f6d367489849d452844fd26e4`.
- `selected_head.npz`: effective quantized head kernel and bias.
- `head_test_predictions.npz`: labels, original logits, and selected-model logits.
- `head_report.json`: complete metrics, candidates, and paired interval.
- `manifest.json`, `config.json`, `head_config.json`: frozen-feature provenance and original model configuration.
- `model_structure_verification.json`, `local_verification.json`: independent local checks.
- `extraction-job.json/.log`, `refit-job.json/.log`: actual submitted-job provenance.

The initial 4-CPU/8-GiB, 900-second Job successfully extracted features in 264 seconds, then failed because SciPy was absent. A second 4-CPU/8-GiB, 600-second Job reused the cached features and installed SciPy 1.18.0 explicitly; fitting and evaluation took 25.39 seconds, and the complete second Job finished in 80 seconds including startup. The one-shot manifest has since been corrected to include SciPy. Neither Job requested a GPU. Both Jobs and their new ConfigMap were removed after evidence retrieval; results and the full feature archive remain at `/data/accuracy-head-features-20260917` on the existing PVC. The large feature archive was not transferred locally.
