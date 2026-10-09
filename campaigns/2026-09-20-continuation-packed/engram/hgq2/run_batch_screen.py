#!/usr/bin/env python3
"""Run one indexed, resumable screening arm against a validated shared cache."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=int, default=int(os.environ.get('JOB_COMPLETION_INDEX', '0')))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--stop-after', type=int, default=100)
    parser.add_argument('--campaign', default='batch20260917')
    args = parser.parse_args()
    code = Path(__file__).resolve().parent
    if args.campaign == 'batch20260917':
        names = [f'batch20260917-a{i:02d}-s1' for i in range(12)]
    else:
        # Later campaigns list their runs in configs/<campaign>/index.json, in index order.
        runs = json.loads((code / 'configs' / args.campaign / 'index.json').read_text())['runs']
        assert [run['index'] for run in runs] == list(range(len(runs))), 'index.json out of order'
        names = [run['name'] for run in runs]
    if not 0 <= args.index < len(names) or args.stop_after not in (100, 200, 400):
        parser.error(f'Expected index 0..{len(names) - 1} and cumulative screening epoch 100, 200, or 400')
    name = names[args.index]
    config = code / 'configs' / args.campaign / (name + '.json')
    cfg = json.loads(config.read_text())
    root = args.root / f'n{cfg["arch"]["n_part"]}'
    data = root / 'data'
    cache_lock = (data / 'prepare.lock').open('a')
    fcntl.flock(cache_lock.fileno(), fcntl.LOCK_SH)
    import numpy as np
    def array_hash(array):
        return hashlib.sha256(np.ascontiguousarray(array).view(np.uint8)).hexdigest()
    arrays = {key: np.load(data / f'{key}.npy', mmap_mode='r')
              for key in ('x_train', 'y_train', 'x_val', 'y_val')}
    assert (data / 'READY.json').exists(), 'Data cache not committed'
    info = json.loads((data / 'data_info.json').read_text())
    assert info['n_part'] == cfg['arch']['n_part']
    assert info['features'] == cfg['arch']['features']
    shape = (cfg['arch']['n_part'], cfg['arch']['n_feat'])
    for split, count in [('train', 496000), ('val', 124000)]:
        assert arrays['x_' + split].shape == (count, *shape), 'Wrong constituent cache'
        assert arrays['y_' + split].shape == (count, 5), 'Wrong label cache'
        assert array_hash(arrays['x_' + split]) == info[split + '_sha256']
        assert array_hash(arrays['y_' + split]) == info['array_sha256']['y_' + split]
        assert np.isfinite(arrays['x_' + split]).all()
        assert np.isfinite(arrays['y_' + split]).all()
        assert np.all(arrays['y_' + split].sum(axis=1) == 1)
    assert info['split_seed'] == cfg['train']['split_seed']
    assert info['order_seed'] == cfg['train']['order_seed']
    del arrays
    cache_lock.close()
    out = root / 'runs' / cfg['experiment']['arm']
    out.mkdir(parents=True, exist_ok=True)
    state = dict(run=name, index=args.index, n_part=shape[0],
                 screening_target_epochs=args.stop_after,
                 config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
                 code_sha256=os.environ.get('BNHGQ2_CODE_SHA256'),
                 status='starting', updated_at_unix=time.time())
    atomic_json(out / 'screening_status.json', state)
    command = [sys.executable, '-u', str(code / 'run_ablation.py'), 'train',
               '--config', str(config), '--root', str(root),
               '--benchmark-epochs', str(args.stop_after), '--track']
    print(f'[screen] {name}: cumulative epoch target {args.stop_after}', flush=True)
    result = subprocess.run(command, check=False)
    state.update(status='failed' if result.returncode else 'paused_for_promotion',
                 exit_code=result.returncode, updated_at_unix=time.time())
    if result.returncode == 0:
        latest = json.loads((out / 'latest.json').read_text())
        checkpoint = json.loads((out / 'checkpoints' / latest['checkpoint'] / 'state.json').read_text())
        assert checkpoint['completed_epochs'] >= args.stop_after
        state['completed_epochs'] = checkpoint['completed_epochs']
        state['best_feasible'] = checkpoint['best_feasible']
        state['train_seconds'] = checkpoint['train_seconds']
    atomic_json(out / 'screening_status.json', state)
    if result.returncode:
        raise SystemExit(result.returncode)
    print(f'SCREENING_RUNG_PASS {name} epochs={state["completed_epochs"]}', flush=True)


if __name__ == '__main__':
    main()
