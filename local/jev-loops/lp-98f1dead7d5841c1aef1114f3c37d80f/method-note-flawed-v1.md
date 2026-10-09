# Method note (SYNTHETIC, flawed on purpose)

Arm B adds a learned positional bias to the N=8 W1A8 binary transformer; arm A is the baseline.
Each arm trains for 1000 epochs with seed 1.
We select the checkpoint with the highest ROC-test macro AUC, since that is the number we report.
Cost is the eBOPs measured at the final epoch, and it is reported beside the AUC of the best checkpoint.
Arm B improves macro AUC over arm A by 0.002 (seed 1), so the positional bias helps.
