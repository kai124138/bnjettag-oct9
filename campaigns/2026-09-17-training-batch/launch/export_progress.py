"""Read only this campaign's W&B summaries; emit no credentials or raw configs."""
import hashlib
import json
import wandb

project = 'kayamaguchi-uc-san-diego/BNJetTag-Batch20260917'
allowed = {hashlib.sha256(f'batch20260917-a{i:02d}-s1'.encode()).hexdigest()[:12] for i in range(12)}
keys = {'completed_epochs', 'epochs_run', 'epoch', 'phase', 'screening_target_epochs',
        'val_categorical_accuracy', 'val_macro_auc', 'ebops', 'epoch_seconds',
        'best_feasible_val_accuracy', 'best_feasible_val_macro_auc', 'best_feasible_ebops',
        'best_feasible_epoch', 'train_seconds', '_runtime', '_timestamp'}
records = []
for run in wandb.Api(timeout=30).runs(project, filters={'group': 'batch20260917'}):
    if run.id in allowed:
        summary = dict(run.summary)
        records.append({'id': run.id, 'state': run.state,
                        'summary': {k: v for k, v in summary.items() if k in keys}})
print(json.dumps({'runs': records}, allow_nan=False))
