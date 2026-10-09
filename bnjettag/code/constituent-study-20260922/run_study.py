"""One common trainer and strict checkpoint verification for the N8/N64 screen."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

import numpy as np
import run_engram

HERE = Path(__file__).resolve().parent
DATA_ROOT = Path('/data/constituent-study-20260922')
ROOT = DATA_ROOT / 'fp32'


def manifest():
    paths = sorted(HERE.glob('*.py')) + sorted((HERE / 'bnhgq2').glob('*.py'))
    result = {'files': {str(p.relative_to(HERE)): run_engram.file_hash(p) for p in paths},
              'versions': {k: importlib.metadata.version(k) for k in
                           ('tensorflow', 'keras', 'hgq2', 'quantizers', 'numpy', 'scikit-learn')}}
    result['sha256'] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


def contract(cfg, engram):
    spec = cfg['engram_study']['module']
    ledger = None if spec is None else engram.cost_ledger(spec, cfg['arch']['n_part'], cfg['arch']['d_model'])
    reasons = []
    if ledger:
        for metric, limit in [('logical_table_bytes', 'max_logical_table_bytes'),
                              ('replicated_table_bytes_estimate', 'max_replicated_table_bytes')]:
            if ledger[metric] > cfg['engram_study'][limit]:
                reasons.append(f'{metric} exceeds {limit}')
        if ledger['estimated_bitops'] >= cfg['train']['ebops']['pid']['target_ebops']:
            reasons.append('fixed memory arithmetic alone exceeds total eBOP budget')
    return {'memory': ledger, 'static_infeasible_reasons': reasons,
            'target_ebops': cfg['train']['ebops']['pid']['target_ebops'], 'hardware_validated': False}


def preflight(shard, shards):
    ablation, engram = run_engram.runtime()
    import keras
    rows = json.loads((HERE / 'index.json').read_text())['runs']
    reports = []
    out = ROOT / 'preflight'
    out.mkdir(parents=True, exist_ok=True)
    caches = {}
    for n in (8, 64):
        cfg = json.loads((HERE / 'configs' / next(r['file'] for r in rows if r['n_part'] == n)).read_text())
        caches[n] = run_engram.load_cache(DATA_ROOT / f'n{n}' / 'data', cfg)
    assert caches[8][1]['permutation_sha256'] == caches[64][1]['permutation_sha256']
    for split in ('y_train', 'y_val'):
        assert caches[8][1]['array_sha256'][split] == caches[64][1]['array_sha256'][split]
    for row in rows[shard::shards]:
        keras.backend.clear_session()
        cfg = json.loads((HERE / 'configs' / row['file']).read_text())
        run_engram.validate_cfg(cfg)
        arrays, info = caches[cfg['arch']['n_part']]
        sample = np.asarray(arrays[0][:64])
        model, evidence = run_engram.builder_for(info)(cfg, sample, 1)
        ablation.binary_gate(model, cfg)
        trace = ablation.compute_ebops(model, sample[:32])
        predictions = np.asarray(model(sample[:16], training=False))
        assert np.isfinite(predictions).all()
        path = Path('/work') / (row['name'] + '.keras')
        model.save(path)
        loaded = keras.models.load_model(path, compile=False)
        np.testing.assert_allclose(loaded(sample[:16], training=False), predictions, atol=2e-6, rtol=2e-6)
        traced = ablation.compute_ebops(loaded, sample[:32])
        assert traced['total'] == trace['total']
        np.testing.assert_allclose(loaded(sample[:16], training=False), predictions, atol=2e-6, rtol=2e-6)
        path.unlink()
        report = {**row, **contract(cfg, engram), 'parameters': model.count_params(),
                  'initial_cost': engram.accounting(model, trace), 'status': 'PASS'}
        reports.append(report)
        print('CONFIG_PREFLIGHT_PASS', row['name'], 'params', model.count_params(),
              'static_infeasible', report['static_infeasible_reasons'], flush=True)
        del model, loaded
    run_engram.write_json(out / f'shard-{shard}.json', {'status': 'PASS', 'source': manifest(), 'runs': reports})
    print('PREFLIGHT_ALL_PASS', shard, flush=True)


def train(index, stop_after):
    ablation, engram = run_engram.runtime()
    import keras
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)
    assert not tf.config.experimental.tensor_float_32_execution_enabled()
    assert tf.config.list_physical_devices('GPU'), 'Training requires GPU'
    row = json.loads((HERE / 'index.json').read_text())['runs'][index]
    cfg = json.loads((HERE / 'configs' / row['file']).read_text())
    run_engram.validate_cfg(cfg)
    run_engram.validate_tracking_destination(cfg)
    out = ROOT / 'runs' / row['name']
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source = manifest()
        os.environ['BNHGQ2_CODE_SHA256'] = source['sha256']
        if (out / 'source_manifest.json').exists():
            assert json.loads((out / 'source_manifest.json').read_text()) == source
        run_engram.write_json(out / 'source_manifest.json', source)
        limits = contract(cfg, engram)
        run_engram.write_json(out / 'cost_contract.json', limits)
        if limits['static_infeasible_reasons']:
            raise RuntimeError('Static-infeasible arm must be excluded from GPU packs')
        arrays, info = run_engram.load_cache(DATA_ROOT / f"n{cfg['arch']['n_part']}" / 'data', cfg)
        if (out / 'VERIFIED_COMPLETE.json').exists():
            ablation.restore_checkpoint(out, cfg, info)
            print('ALREADY_VERIFIED', row['name'], flush=True)
            return
        start = time.monotonic()
        # Keep the same immutable 50-epoch config for the two-epoch GPU canary
        # and its continuation. Per-epoch checkpoints include optimizer and PID.
        state = ablation.run_training(cfg, arrays, info, out, remote=True,
            stop_after=stop_after, model_builder=run_engram.builder_for(info),
            epoch_observer=engram.diagnostic_observer())
        if (out / 'COMPLETE.json').exists():
            (out / 'COMPLETE.json').replace(out / 'TRAINING_COMPLETE.json')
        selected = state['best_feasible'] or state['lowest']
        filename = 'model_best.keras' if state['best_feasible'] else 'model_min_ebops.keras'
        model = keras.models.load_model(out / filename, compile=False)
        trace = ablation.compute_ebops(model, np.asarray(arrays[0][:256]))
        assert trace['total'] == selected['ebops'], 'Reloaded checkpoint cost mismatch'
        logits = np.asarray(model.predict(arrays[2], batch_size=cfg['train']['val_batch'], verbose=0))
        auc, per_auc, accuracy = ablation.validation_metrics(arrays[3], logits)
        np.testing.assert_allclose([auc, accuracy],
            [selected['val_macro_auc'], selected['val_categorical_accuracy']], atol=1e-7, rtol=0)
        np.savez_compressed(out / 'validation_predictions.npz', labels=np.asarray(arrays[3]), logits=logits)
        report = {**row, 'status': 'verified_screen' if state['completed_epochs'] == 50 else 'verified_canary',
                  'completed_epochs': state['completed_epochs'], 'selected': selected,
                  'checkpoint': filename, 'checkpoint_sha256': run_engram.file_hash(out / filename),
                  'budget_met': state['best_feasible'] is not None,
                  'validation_accuracy': accuracy, 'validation_macro_auc': auc,
                  'validation_per_class_auc': per_auc, 'wall_seconds_this_invocation': time.monotonic() - start,
                  'test_set_used': False, 'hardware_validated': False,
                  'validation_labels_sha256': info['array_sha256']['y_val'],
                  'source_sha256': source['sha256'], **engram.accounting(model, trace)}
        run_engram.write_json(out / 'screen_result.json', report)
        if state['completed_epochs'] == cfg['train']['epochs']:
            run_engram.write_json(out / 'VERIFIED_COMPLETE.json', report)
        print('CHECKPOINT_VERIFICATION_PASS', json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['preflight', 'train'])
    parser.add_argument('--index', type=int, default=0)
    parser.add_argument('--shards', type=int, default=2)
    parser.add_argument('--stop-after', type=int)
    args = parser.parse_args()
    if args.stage == 'preflight':
        preflight(args.index, args.shards)
    else:
        train(args.index, args.stop_after)
