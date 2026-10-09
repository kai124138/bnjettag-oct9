#!/usr/bin/env python3
"""ROC curves for one finished run, computed on the home PC, for the `runs` pane.

Downloads the run's newest `resume-<arm>` checkpoint artifact from W&B, loads `model_best.keras`
with the campaign's own bnhgq2 code, predicts the validation split of the local cache
(local/runs-cache/n64/data, rebuilt by the pipeline's prepare_cache.py; its array hashes must equal
the cluster cache's) and writes one-vs-rest ROC points per class to local/runs-cache/roc/<arm>.json.

Home PC numbers: monitoring only, never quotable (CLAUDE.md). The replayed accuracy is compared with
the run's W&B `best_feasible_val_accuracy` so a wrong checkpoint or data mismatch shows up.

~/venv-hgq2/bin/python tools/runs_roc.py --arm d350-reference-e-5m-s1 [--force]
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'local' / 'runs-cache'
OUT = CACHE / 'roc'
ENTITY = 'kayamaguchi-uc-san-diego'
CLASSES = ['g', 'q', 'W', 'Z', 't']  # hls4ml LHC jet dataset label order
# The cluster's N64 cache (chang-n64-20260926), as captured 2026-10-01; the local rebuild must match.
CLUSTER_INFO = ROOT / 'campaigns/2026-10-01-recovery/captures/pvc-20261001T0555Z/chang-n64-20260926/n64/data/data_info.json'
POINTS = 120


def find_config(arm):
    paths = sorted(ROOT.glob(f'campaigns/*/configs/{arm}.json'), reverse=True)
    if not paths:
        sys.exit(f'no config for {arm}')
    return paths[0]


def check_cache(cfg):
    data = CACHE / f"n{cfg['arch']['n_part']}" / 'data'
    if not (data / 'READY.json').is_file():
        sys.exit(f'local cache missing: {data} (rebuild with prepare_cache.py)')
    local = json.loads((data / 'data_info.json').read_text())
    for key in ('features', 'split_seed', 'validation_split', 'pt_gate_gev'):
        if local.get(key) != (cfg['arch'] if key in ('features', 'pt_gate_gev') else cfg['train']).get(key):
            sys.exit(f'local cache {key} does not match the run config')
    cluster = json.loads(CLUSTER_INFO.read_text())['array_sha256'] if CLUSTER_INFO.is_file() else {}
    same = bool(cluster) and all(local['array_sha256'][k] == cluster.get(k) for k in ('x_val', 'y_val'))
    return data, local['array_sha256']['y_val'], same


def thin(fpr, tpr, n=POINTS):
    """Keep about n points spread over the curve, always both ends."""
    import numpy as np
    if len(fpr) <= n:
        return fpr, tpr
    keep = np.unique(np.linspace(0, len(fpr) - 1, n).round().astype(int))
    return fpr[keep], tpr[keep]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--arm', required=True)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f'{args.arm}.json'

    cfg_path = find_config(args.arm)
    cfg = json.loads(cfg_path.read_text())
    code = cfg_path.parent.parent / 'code'
    data, y_sha, matches_cluster = check_cache(cfg)

    import wandb
    api = wandb.Api(timeout=60)
    project = f"{ENTITY}/{cfg['train']['wandb_project']}"
    runs = api.runs(project, filters={'display_name': args.arm})
    if not runs:
        sys.exit(f'no W&B run named {args.arm} in {project}')
    run = runs[0]
    arts = [a for a in run.logged_artifacts() if a.type == 'checkpoint' and a.name.startswith(f'resume-{args.arm}:')]
    if not arts:
        sys.exit('no checkpoint artifact on W&B for this run')
    art = max(arts, key=lambda a: a.version if isinstance(a.version, int) else int(str(a.version).lstrip('v')))
    if out.is_file() and not args.force and json.loads(out.read_text()).get('artifact') == art.name:
        print(out)
        return

    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
    sys.path.insert(0, str(code))
    import numpy as np
    import keras
    from sklearn.metrics import roc_curve, auc
    from bnhgq2 import ablation  # registers the custom layers, as eval/score.py does

    with tempfile.TemporaryDirectory() as tmp:
        files = [f for f in art.files() if f.name.endswith('/model_best.keras')]
        if not files:
            sys.exit(f'no feasible best checkpoint: {art.name} holds no model_best.keras '
                     f'(W&B best_feasible_val_accuracy = {run.summary.get("best_feasible_val_accuracy")})')
        path = files[0].download(root=tmp, replace=True).name
        model = keras.models.load_model(path, compile=False)
        x_val = np.load(data / 'x_val.npy', mmap_mode='r')
        y_val = np.load(data / 'y_val.npy')
        logits = np.asarray(model.predict(x_val, batch_size=cfg['train'].get('val_batch', 4096), verbose=0))
    macro, per, acc = ablation.validation_metrics(y_val, logits)
    probs = np.exp(logits - logits.max(-1, keepdims=True))
    probs /= probs.sum(-1, keepdims=True)
    curves = []
    for c, name in enumerate(CLASSES):
        fpr, tpr, _ = roc_curve(y_val[:, c], probs[:, c])
        f, t = thin(fpr, tpr)
        curves.append({'class': name, 'auc': float(auc(fpr, tpr)), 'fpr': f.round(5).tolist(), 'tpr': t.round(5).tolist()})
    wandb_acc = run.summary.get('best_feasible_val_accuracy')
    result = {
        'arm': args.arm, 'artifact': art.name, 'checkpoint': files[0].name, 'wandb_run': run.id,
        'split': 'validation', 'n': int(len(y_val)), 'computed_on': 'home PC', 'status': 'monitoring, not quotable',
        'labels_sha256_y_val': y_sha, 'cache_matches_cluster': matches_cluster,
        'val_accuracy': acc, 'val_macro_auc': float(macro),
        'wandb_best_feasible_val_accuracy': wandb_acc,
        'replay_matches_wandb': wandb_acc is not None and abs(acc - wandb_acc) < 1e-3,
        'curves': curves,
    }
    tmp_out = out.with_suffix('.tmp')
    tmp_out.write_text(json.dumps(result))
    os.replace(tmp_out, out)
    print(out)


if __name__ == '__main__':
    main()
