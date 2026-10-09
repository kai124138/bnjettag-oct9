# Method note (SYNTHETIC, corrected v1)

Arm B adds a learned positional bias to the N=8 W1A8 binary transformer; arm A is the baseline.
Each arm trains for 1000 epochs on the same eight seeds, because the expected gap is under 0.005 in AUC.
Selection rule, pre-registered: the checkpoint with the highest validation macro-OvR AUC among checkpoints at or under the eBOP budget; the held-out ROC-test set is never used for selection and is evaluated once, at the end.
Cost is native HGQ2 eBOPs remeasured on the selected checkpoint (zero and random inputs agree), the same checkpoint whose AUC is reported.
The arm B minus arm A gap is reported as the paired-by-seed mean difference in held-out macro AUC with a 95 % t-interval (df = seeds - 1) and the count of seeds on which the sign holds; a gap whose interval covers zero is reported as flat.
Every number carries metric, split, n and status; validation AUC and held-out AUC are labelled separately. No result exists yet; no improvement is claimed.
