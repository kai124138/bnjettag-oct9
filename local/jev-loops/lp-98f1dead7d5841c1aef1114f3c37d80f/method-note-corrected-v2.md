# Method note (SYNTHETIC, corrected v2)

Arm B adds a learned positional bias to the N=8 W1A8 binary transformer; arm A is the baseline.
Arms are matched: same N, input set, split, schedule and initialisation; only the positional bias differs.
Each arm trains for 1000 epochs on the same eight seeds, because the expected gap is under 0.005 in AUC.
Selection rule, pre-registered: the checkpoint with the highest validation macro-OvR AUC among checkpoints at or under the eBOP budget.
The held-out ROC-test set is never used for selection and is evaluated once, at the end.
Cost is native HGQ2 eBOPs measured on the selected checkpoint; zero-input and random-input measurements must agree.
Final-epoch cost is never reported beside best-checkpoint AUC; cost and AUC come from the same selected checkpoint.
The selected checkpoint reloads within 1e-7 on the metric with TF32 off.
The gap is paired by seed: mean difference in held-out macro AUC with a 95 % t-interval (df = seeds - 1) and the count of seeds on which the sign holds.
A gap whose interval covers zero is reported as flat.
Code sha, ConfigMap name and generated configs are recorded in PREFLIGHT.md before launch.
Every number carries metric, split, n and status. No result exists yet; no improvement is claimed.
