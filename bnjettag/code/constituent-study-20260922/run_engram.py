#!/usr/bin/env python3
"""Prepare and run a controlled Engram-inspired BNJetTag experiment.

python run_engram.py plan --out /work/engram-configs
python run_engram.py preflight --out /tmp/engram-preflight
python run_engram.py train --config /work/engram-configs/engram-e03-s1.json \
    --data-cache /work/n16/data --out /work/engram/e03-s1 --stop-after 100

Uses the existing resumable GPU trainer, epoch order, PID and accuracy selection.
Only preflight uses small synthetic CPU inputs. Training never downloads data or
submits cluster jobs, and requires a GPU. W&B is opt-in with --track.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_BASE = HERE / 'configs/batch20260917/batch20260917-a04-s1.json'


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest():
    paths = [Path(__file__).resolve(), *sorted((HERE / 'bnhgq2').glob('*.py'))]
    files = {str(p.relative_to(HERE)): file_hash(p) for p in paths}
    versions = {name: importlib.metadata.version(name)
                for name in ('tensorflow', 'keras', 'hgq2', 'quantizers', 'numpy', 'scikit-learn')}
    content = {'files': files, 'versions': versions}
    content['sha256'] = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    return content


def default_spec():
    return dict(bins=8, table_size=512, heads=1, orders=[1], gate='hard',
                value_bits=8, key_bits=8, query_bits=8, gate_bits=4,
                input_bits=16, input_integer=6, residual_bits=24,
                insert_after='bit_block_0_add_attn', hash_seed=17)


def configs(base, seeds):
    """Matched backbone controls and explicitly scoped memory design comparisons."""
    if base['arch']['n_layers'] != 2:
        raise ValueError('This screen expects a two-block base; small arms use one block')
    arms = [
        ('e00', False, None, 'Two-block reference'),
        ('e01', True, None, 'One-block compute-saving control'),
        ('e02', True, {'gate': 'none'}, 'One block + tuple memory, no gate'),
        ('e03', True, {}, 'One block + context-gated tuple memory'),
        ('e04', False, {}, 'Two blocks + same memory under shared total proxy budget'),
        ('e05', True, {'value_bits': 4, 'key_bits': 4}, 'One block + 4-bit tuple memory'),
        ('e06', True, {'bins': 4, 'table_size': 64}, 'One block + smaller exact tuple memory'),
        ('e07', True, {'orders': [2], 'table_size': 257}, 'Rank bigrams: order-dependent control'),
    ]
    for seed in seeds:
        for arm, small, changes, question in arms:
            cfg = copy.deepcopy(base)
            cfg['name'] = f'engram-{arm}-s{seed}'
            if small:
                cfg['arch']['n_layers'] = 1
            cfg['train']['wandb_project'] = 'BNJetTag-Engram-Experimental'
            cfg['train']['ebops']['selection'] = 'max_accuracy'
            cfg['experiment'] = dict(arm=cfg['name'], group='engram-screen', seed=seed,
                                     selection_metric='val_categorical_accuracy',
                                     checkpoint_every_epochs=1, remote_every_epochs=25)
            spec = None if changes is None else {**default_spec(), **changes}
            cfg['engram_study'] = dict(module=spec, question=question,
                                       memory_lr_multiplier=5., memory_weight_decay=0.,
                                       wandb_entity='kayamaguchi-uc-san-diego',
                                       wandb_project_access='PRIVATE',
                                       max_logical_table_bytes=65536,
                                       max_replicated_table_bytes=524288,
                                       cost_convention='native_hgq2_plus_custom_estimate',
                                       status='experimental; training ready, HLS unsupported')
            yield arm, seed, cfg


def runtime():
    os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
    os.environ.setdefault('TF_NUM_INTEROP_THREADS', '2')
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    from bnhgq2 import ablation, engram
    return ablation, engram


def validate_cfg(cfg):
    if cfg['arch']['features'] != ['pt', 'etarel', 'phirel'] or cfg['arch']['n_feat'] != 3:
        raise ValueError('Study requires exactly [pt, etarel, phirel] in that order')
    if cfg['quant']['weight'] != 'binary_absmean' or cfg['quant']['act_calib'] != 'free':
        raise ValueError('Study expects binary backbone weights and free activation widths')
    if cfg['arch'].get('pair_bias', False):
        raise ValueError('Pair-bias preprocessing has separate unaccounted costs; disable for this screen')
    if cfg['experiment']['selection_metric'] != 'val_categorical_accuracy':
        raise ValueError('Checkpoint selection must prioritize validation accuracy')
    if cfg['experiment'].get('distillation'):
        raise ValueError('Distillation is not part of this controlled screen')
    study = cfg['engram_study']
    if study.get('memory_weight_decay') != 0. or not 0 < study.get('memory_lr_multiplier', 0) <= 100:
        raise ValueError('Expected zero table weight decay and a positive table LR multiplier <=100')
    if study['cost_convention'] != 'native_hgq2_plus_custom_estimate':
        raise ValueError('Missing explicit custom-cost convention')
    if any(study[k] <= 0 for k in ('max_logical_table_bytes', 'max_replicated_table_bytes')):
        raise ValueError('Memory budgets must be positive')
    if not study.get('wandb_entity') or study.get('wandb_project_access') != 'PRIVATE':
        raise ValueError('Study must declare its W&B entity and PRIVATE project access')


def validate_tracking_destination(cfg, *, fetch_project=None):
    """Fail before training if inherited environment redirects or exposes this study."""
    from bnhgq2.wandb_util import init_kwargs
    expected_project = cfg['train']['wandb_project']
    expected_entity = cfg['engram_study']['wandb_entity']
    destination = init_kwargs(name=cfg['name'], job_type='train', cfg_project=expected_project)
    if destination['entity'] != expected_entity or destination['project'] != expected_project:
        raise ValueError('W&B environment overrides the declared Engram entity/project; refusing to mix campaigns')
    if os.environ.get('WANDB_MODE', '').lower() != 'online':
        raise ValueError('--track requires explicit WANDB_MODE=online for the private study')
    if fetch_project is None:
        # Pinned wandb 0.28 exposes project access through InternalApi.execute;
        # older vendor.gql / public Api.client examples no longer work.
        from wandb.sdk.internal.internal_api import Api
        api = Api()
        def fetch_project(entity, project):
            result = api.execute('''query EngramProjectAccess($entity: String!, $project: String!) {
                project(name: $project, entityName: $entity) { name access }
            }''', variables={'entity': entity, 'project': project})
            return result.get('project')
    project = fetch_project(expected_entity, expected_project)
    if project is None or str(project.get('access', '')).upper() != 'PRIVATE':
        raise ValueError('The separate W&B project must exist and be verified PRIVATE before --track')
    return {'entity': expected_entity, 'project': expected_project, 'access': 'PRIVATE'}


def builder_for(data_info):
    ablation, engram = runtime()

    def builder(cfg, sample, seed):
        base, evidence = ablation.matching_initialization(cfg, sample, seed)
        spec = cfg['engram_study']['module']
        if spec is None:
            return base, evidence
        tokenizer = engram.fit_tokenizer(sample, data_info['input_std'], spec)
        model = engram.augment_model(base, spec, tokenizer)
        np.testing.assert_array_equal(np.asarray(model(sample[:8], training=False)),
                                      np.asarray(base(sample[:8], training=False)))
        evidence.update(engram_tokenizer=tokenizer, backbone_initial_output_identical=True,
                        engram_value_initialization='zero', engram_spec=spec)
        return model, evidence
    return builder


def load_cache(path, cfg):
    """Read only train/validation, verify every array and the cache's identity."""
    ablation, _ = runtime()
    if not (path / 'READY.json').is_file():
        raise ValueError('Expected committed shared data cache (READY.json)')
    info = json.loads((path / 'data_info.json').read_text())
    for key, value in (('n_part', cfg['arch']['n_part']), ('features', cfg['arch']['features']),
                       ('split_seed', cfg['train']['split_seed']), ('order_seed', cfg['train']['order_seed'])):
        if info.get(key) != value:
            raise ValueError(f'Cache {key} mismatch or missing; expected {value!r}, got {info.get(key)!r}')
    names = ('x_train', 'y_train', 'x_val', 'y_val')
    arrays = tuple(np.load(path / (name + '.npy'), mmap_mode='r', allow_pickle=False) for name in names)
    actual = {}
    for name, array in zip(names, arrays):
        digest = ablation.array_hash(array)
        expected = info.get('array_sha256', {}).get(name)
        if name in ('x_train', 'x_val'):
            expected = expected or info[name[2:] + '_sha256']
        if expected is None or digest != expected:
            raise ValueError(f'Cache hash missing/mismatched for {name}')
        if array.dtype != np.float32 or not np.isfinite(array).all():
            raise ValueError(f'{name} must be finite float32')
        actual[name] = digest
    xt, yt, xv, yv = arrays
    shape = (cfg['arch']['n_part'], cfg['arch']['n_feat'])
    for x, y in ((xt, yt), (xv, yv)):
        if x.shape[1:] != shape or y.shape != (len(x), cfg['arch']['n_classes']):
            raise ValueError('Wrong input/label dimensions')
        if not np.isin(y, [0., 1.]).all() or not np.all(y.sum(-1) == 1) or np.any(y.sum(0) == 0):
            raise ValueError('Expected one-hot labels with every class present')
    if (len(xt), len(xv)) != (496000, 124000):
        raise ValueError('Production screen requires the shared 496000/124000 split')
    info = {**info, 'engram_array_sha256': actual}
    return arrays, info


def enforce_memory(cfg, engram):
    spec = cfg['engram_study']['module']
    if spec is None:
        return None
    ledger = engram.cost_ledger(spec, cfg['arch']['n_part'], cfg['arch']['d_model'])
    for cost, limit in (('logical_table_bytes', 'max_logical_table_bytes'),
                        ('replicated_table_bytes_estimate', 'max_replicated_table_bytes')):
        if ledger[cost] > cfg['engram_study'][limit]:
            raise ValueError(f'{cost}={ledger[cost]} exceeds {limit}={cfg["engram_study"][limit]}')
    if ledger['estimated_bitops'] >= cfg['train']['ebops']['pid']['target_ebops']:
        raise ValueError('Memory module estimate alone exhausts arithmetic budget')
    return ledger


def train(args):
    ablation, engram = runtime()
    import keras
    import tensorflow as tf
    cfg = json.loads(args.config.read_text())
    validate_cfg(cfg)
    tracking = validate_tracking_destination(cfg) if args.track else None
    if args.stop_after is not None and not 1 <= args.stop_after <= cfg['train']['epochs']:
        raise ValueError('--stop-after must be within the configured full schedule')
    ledger = enforce_memory(cfg, engram)
    if not tf.config.list_physical_devices('GPU'):
        raise RuntimeError('Full training requires a GPU; use preflight for CPU verification')
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with (args.data_cache / 'prepare.lock').open('a') as cache_lock:
            fcntl.flock(cache_lock, fcntl.LOCK_SH)
            arrays, info = load_cache(args.data_cache, cfg)
            manifest = source_manifest()
            os.environ['BNHGQ2_CODE_SHA256'] = manifest['sha256']
            manifest_path = args.out / 'source_manifest.json'
            if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
                raise ValueError('Source or dependency versions changed; use a new output directory')
            write_json(manifest_path, manifest)
            if tracking is not None:
                write_json(args.out / 'tracking_destination.json', tracking)
            write_json(args.out / 'cost_contract.json', dict(module=ledger,
                       target=cfg['train']['ebops']['pid']['target_ebops'],
                       convention='native_hgq2_plus_custom_estimate',
                       selection='highest validation accuracy under augmented arithmetic and memory budgets',
                       hardware_validated=False))
            if not (args.out / 'COMPLETE.json').exists():
                ablation.run_training(cfg, arrays, info, args.out, remote=args.track,
                                      stop_after=args.stop_after, model_builder=builder_for(info),
                                      epoch_observer=engram.diagnostic_observer())
            else:
                # Check identity even when training is already committed.
                ablation.restore_checkpoint(args.out, cfg, info)
            latest = json.loads((args.out / 'latest.json').read_text())['checkpoint']
            state = json.loads((args.out / 'checkpoints' / latest / 'state.json').read_text())
            name = 'model_best.keras' if state['best_feasible'] else 'model_min_ebops.keras'
            selected = state['best_feasible'] or state['lowest']
            model = keras.models.load_model(args.out / name, compile=False)
            trace = ablation.compute_ebops(model, np.asarray(arrays[0][:256]))
            if trace['total'] != selected['ebops']:
                raise RuntimeError('Selected checkpoint cost did not reproduce after reload')
            logits = np.asarray(model.predict(arrays[2], batch_size=cfg['train']['val_batch'], verbose=0))
            auc, per_auc, accuracy = ablation.validation_metrics(arrays[3], logits)
            np.testing.assert_allclose([auc, accuracy],
                                      [selected['val_macro_auc'], selected['val_categorical_accuracy']],
                                      atol=1e-7, rtol=0)
            np.savez_compressed(args.out / 'validation_predictions.npz',
                                labels=np.asarray(arrays[3]), logits=logits)
            report = {**engram.accounting(model, trace), 'run': cfg['name'], 'checkpoint': name,
                      'checkpoint_sha256': file_hash(args.out / name),
                      'completed_epochs': state['completed_epochs'], 'selected': selected,
                      'budget_met': state['best_feasible'] is not None,
                      'validation_accuracy': accuracy, 'validation_macro_auc': auc,
                      'validation_per_class_auc': per_auc,
                      'validation_labels_sha256': ablation.array_hash(arrays[3]),
                      'validation_inputs_sha256': info['val_sha256'],
                      'seed': cfg['experiment']['seed'], 'test_set_used': False,
                      'hardware_validated': False}
            for layer in model.layers:
                if isinstance(layer, engram.JetEngram):
                    np.savez_compressed(args.out / 'memory_tables.npz',
                        values=engram.fixed_np(layer.values.numpy(), layer.spec['value_bits'], 1),
                        **({'keys': engram.fixed_np(layer.keys.numpy(), layer.spec['key_bits'], 0)}
                           if layer.spec['gate'] == 'hard' else {}))
                    write_json(args.out / 'memory_tokenizer.json', layer.tokenizer)
                    ids, masks = engram.address_numpy(np.asarray(arrays[0][:4096]), layer.tokenizer, layer.spec)
                    report['train_sample_occupied_slots'] = [int(len(np.unique(ids[..., i][masks[..., i]])))
                                                             for i in range(ids.shape[-1])]
                    report['occupancy_note'] = 'Occupancy is not a hash-collision measurement.'
            write_json(args.out / 'engram_result.json', report)
            if args.track:
                # The epoch trainer has finished its SDK session. Resume the SAME
                # remote run only to attach its review artifacts, never create another.
                import wandb
                from bnhgq2.wandb_util import init_kwargs, log_files_artifact
                run_id = hashlib.sha256(cfg['name'].encode()).hexdigest()[:12]
                with wandb.init(**init_kwargs(name=cfg['name'], job_type='train',
                                cfg_project=cfg['train']['wandb_project'], group=cfg['experiment']['group']),
                                id=run_id, resume='must') as review_run:
                    review_run.summary.update({
                        'selected_validation_accuracy': accuracy,
                        'selected_validation_macro_auc': auc,
                        'selected_native_backbone_ebops': report['native_hgq2_backbone_ebops'],
                        'selected_custom_estimated_bitops': report['custom_estimated_bitops'],
                        'selected_augmented_cost': report['selection_cost'],
                        'selected_cost_convention': report['selection_cost_convention'],
                        'screening_completed_epochs': state['completed_epochs'],
                        'physics_test_set_used': False, 'hardware_validated': False})
                    names = (name, 'config.json', 'data_info.json', 'activation_widths.jsonl',
                             'engram_result.json', 'cost_contract.json', 'source_manifest.json',
                             'tracking_destination.json', 'validation_predictions.npz',
                             'memory_tables.npz', 'memory_tokenizer.json', 'initialization.json')
                    files = [str(args.out / name) for name in names if (args.out / name).is_file()]
                    files.extend(str(path) for path in sorted((HERE / 'study').glob('*.md')))
                    log_files_artifact(review_run, name='engram-review-' + cfg['name'],
                                       type='evaluation', files=files,
                                       metadata={'scope': 'exploratory_validation_screen',
                                                 'completed_epochs': state['completed_epochs'],
                                                 'cost_convention': report['selection_cost_convention']})
            print(json.dumps(report, indent=2))


def summarize(args):
    rows = [json.loads(p.read_text()) for p in sorted(args.root.glob('*/engram_result.json'))]
    # Do not promote across different input samples or unequal training prefixes.
    grouped = {}
    for row in rows:
        key = (row['validation_inputs_sha256'], row['validation_labels_sha256'], row['completed_epochs'], row['seed'])
        grouped.setdefault(key, []).append(row)
    output = []
    for (inputs, labels, epochs, seed), group in grouped.items():
        eligible = [r for r in group if r['budget_met']]
        front = [r for r in eligible if not any(
            q['validation_accuracy'] >= r['validation_accuracy'] and q['selection_cost'] <= r['selection_cost']
            and (q['validation_accuracy'] > r['validation_accuracy'] or q['selection_cost'] < r['selection_cost'])
            for q in eligible)]
        output.append(dict(validation_inputs_sha256=inputs, validation_labels_sha256=labels,
                           completed_epochs=epochs, seed=seed,
                           ranked=sorted(group, key=lambda r: (r['budget_met'], r['validation_accuracy'],
                                                               -r['selection_cost']), reverse=True),
                           pareto_runs=[r['run'] for r in front],
                           note='Validation screen only; confirm paired seeds and independent test before claiming a gain.'))
    if not rows:
        raise ValueError('No */engram_result.json files found')
    write_json(args.out, output)
    print(f'Wrote {len(rows)} run summaries in {len(output)} comparable groups to {args.out}')


def compare(args):
    """Paired, class-stratified accuracy bootstrap; no test-set model selection."""
    left, right = [json.loads((p / 'engram_result.json').read_text())
                   for p in (args.baseline, args.candidate)]
    for key in ('validation_inputs_sha256', 'validation_labels_sha256', 'completed_epochs', 'seed'):
        if left[key] != right[key]:
            raise ValueError(f'Paired comparison requires matching {key}')
    if not left['budget_met'] or not right['budget_met']:
        raise ValueError('Both selected checkpoints must satisfy their budgets')
    arrays = []
    for directory, report in ((args.baseline, left), (args.candidate, right)):
        with np.load(directory / 'validation_predictions.npz', allow_pickle=False) as data:
            labels, logits = data['labels'], data['logits']
            if labels.shape != logits.shape or not np.isfinite(logits).all():
                raise ValueError('Invalid predictions')
            digest = hashlib.sha256(np.ascontiguousarray(labels).view(np.uint8)).hexdigest()
            if digest != report['validation_labels_sha256']:
                raise ValueError('Prediction label hash mismatch')
            correctness = logits.argmax(-1) == labels.argmax(-1)
            np.testing.assert_allclose(correctness.mean(), report['validation_accuracy'], atol=1e-12, rtol=0)
            arrays.append((labels, correctness))
    np.testing.assert_array_equal(arrays[0][0], arrays[1][0])
    classes = arrays[0][0].argmax(-1)
    b, c = arrays[0][1], arrays[1][1]
    rng = np.random.default_rng(2718)
    deltas = np.zeros(args.draws)
    contingency = []
    for label in range(arrays[0][0].shape[1]):
        mask = classes == label
        counts = np.bincount((2 * b[mask] + c[mask]).astype('int64'), minlength=4)
        if not mask.any():
            raise ValueError('Missing class in validation')
        resamples = rng.multinomial(int(mask.sum()), counts / mask.sum(), size=args.draws)
        deltas += resamples[:, 1] - resamples[:, 2]
        contingency.append(counts.tolist())
    deltas /= len(b)
    result = dict(baseline=left['run'], candidate=right['run'],
                  accuracy_delta=float(c.mean() - b.mean()),
                  paired_stratified_95pct_interval=np.quantile(deltas, [.025, .975]).tolist(),
                  bootstrap_draws=args.draws, bootstrap_seed=2718,
                  contingency_per_class_00_01_10_11=contingency,
                  native_backbone_ebops_delta=right['native_hgq2_backbone_ebops'] - left['native_hgq2_backbone_ebops'],
                  augmented_cost_delta=right['selection_cost'] - left['selection_cost'],
                  caveat='Validation-only screening interval, conditional on selected checkpoints. '
                         'Not corrected for multiple comparisons or training-seed uncertainty.')
    write_json(args.out, result)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('plan', help='Write the eight-arm screen; no training')
    plan.add_argument('--base', type=Path, default=DEFAULT_BASE)
    plan.add_argument('--seeds', type=int, nargs='+', default=[1])
    plan.add_argument('--out', type=Path, required=True)
    check = sub.add_parser('preflight', help='Synthetic CPU correctness checks, including resume')
    check.add_argument('--out', type=Path, required=True)
    run = sub.add_parser('train', help='Run/resume one arm on a GPU using the existing immutable data cache')
    run.add_argument('--config', type=Path, required=True)
    run.add_argument('--data-cache', type=Path, required=True)
    run.add_argument('--out', type=Path, required=True)
    run.add_argument('--stop-after', type=int, help='Cumulative epoch boundary; preserves full LR schedule')
    run.add_argument('--track', action='store_true')
    summary = sub.add_parser('summarize', help='Rank completed screens by accuracy, then cost')
    summary.add_argument('--root', type=Path, required=True)
    summary.add_argument('--out', type=Path, required=True)
    paired = sub.add_parser('compare', help='Paired bootstrap accuracy difference on matching validation jets')
    paired.add_argument('--baseline', type=Path, required=True)
    paired.add_argument('--candidate', type=Path, required=True)
    paired.add_argument('--draws', type=int, default=2000)
    paired.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'plan':
        base = json.loads(args.base.read_text())
        generated = list(configs(base, args.seeds))
        if len(set(args.seeds)) != len(args.seeds) or any(s < 0 for s in args.seeds):
            parser.error('Seeds must be unique nonnegative integers')
        args.out.mkdir(parents=True, exist_ok=True)
        for arm, seed, cfg in generated:
            validate_cfg(cfg)
            path = args.out / f'{cfg["name"]}.json'
            if path.exists() and json.loads(path.read_text()) != cfg:
                raise ValueError(f'Refusing to overwrite a different experiment: {path}')
            write_json(path, cfg)
        write_json(args.out / 'index.json', {'base_config_sha256': file_hash(args.base),
                   'runs': [{'file': f'{cfg["name"]}.json', 'name': cfg['name'],
                             'question': cfg['engram_study']['question']} for arm, seed, cfg in generated]})
        print(f'Wrote {len(generated)} configurations to {args.out}')
    elif args.command == 'preflight':
        runtime()
        from check_engram import run_checks
        run_checks(args.out)
    elif args.command == 'train':
        train(args)
    elif args.command == 'summarize':
        summarize(args)
    else:
        if args.draws < 1000:
            parser.error('Use at least 1000 bootstrap draws')
        compare(args)


if __name__ == '__main__':
    main()
