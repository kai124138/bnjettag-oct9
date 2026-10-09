"""Generate the matched constituent-count screen; preserve source aliases."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def canonical(cfg):
    c = copy.deepcopy(cfg)
    c.pop('name', None)
    c['arch']['n_part'] = 8
    c['train'].pop('wandb_project', None)
    c['train']['ebops']['selection'] = 'max_accuracy'
    for key in ('arm', 'group', 'seed', 'checkpoint_every_epochs',
                'remote_every_epochs', 'selection_metric'):
        c['experiment'].pop(key, None)
    c['module'] = c.pop('engram_study', {}).get('module')
    return json.dumps(c, sort_keys=True)


def main():
    groups = {}
    for directory, pattern in [('batch20260917', '*.json'),
                               ('batch20260918', '*-s4.json'),
                               ('engram', 'engram-*.json')]:
        for path in sorted((HERE / 'reference_configs' / directory).glob(pattern)):
            cfg = json.loads(path.read_text())
            if 'arch' not in cfg:
                continue
            key = canonical(cfg)
            groups.setdefault(key, []).append((path, cfg))
    assert len(groups) == 19
    template = json.loads((HERE / 'reference_configs/engram/engram-e03-s1.json').read_text())['engram_study']
    rows = []
    for entries in groups.values():
        source, original = entries[0]
        variant = source.stem.split('-')[1]
        for n in (8, 64):
            cfg = copy.deepcopy(original)
            name = f'const0922-{variant}-n{n}-s1-fast50-fp32'
            cfg['name'] = name
            cfg['arch']['n_part'] = n
            cfg['train'].update(epochs=50, lr=0.0002, warmup_epochs=1,
                                decay_epochs=49, wandb_project='BNJetTag-Engram-Experimental')
            cfg['train']['ebops']['selection'] = 'max_accuracy'
            cfg['train']['ebops']['pid']['warmup'] = 1
            cfg['experiment'].update(arm=name, group='constituent-20260922-fast50', seed=1,
                selection_metric='val_categorical_accuracy', checkpoint_every_epochs=1,
                remote_every_epochs=25)
            if 'target_schedule' in cfg['experiment']:
                cfg['experiment']['target_schedule'] = [[0, 525000], [5, 420000], [10, 350000]]
            if 'engram_study' not in cfg:
                cfg['engram_study'] = {**copy.deepcopy(template), 'module': None,
                                        'question': 'Matched architecture control'}
            # Same storage contract at both N. These are estimates, not HLS results.
            cfg['engram_study']['max_replicated_table_bytes'] = 2 * 1024 * 1024
            cfg['constituent_study'] = {
                'protocol': 'fresh 50-epoch exploratory screen; not historical continuation',
                'aliases': [p.stem for p, _ in entries],
                'source_config_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'pair': variant, 'equal_arithmetic_budget_within_pair': True,
                'test_set_used': False, 'tf32_enabled': False,
                'validation_execution': 'freshly reloaded checkpoint',
            }
            path = HERE / 'configs' / (name + '.json')
            path.write_text(json.dumps(cfg, indent=2) + '\n')
            rows.append({'index': len(rows), 'name': name, 'variant': variant,
                         'n_part': n, 'file': path.name,
                         'aliases': cfg['constituent_study']['aliases'],
                         'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    for i in range(0, len(rows), 2):
        a, b = [json.loads((HERE / 'configs' / r['file']).read_text()) for r in rows[i:i+2]]
        for cfg in (a, b):
            cfg['arch']['n_part'] = 0
            cfg.pop('name')
            cfg['experiment'].pop('arm')
        assert a == b, rows[i]['variant']
    (HERE / 'index.json').write_text(json.dumps({'runs': rows, 'count': len(rows)}, indent=2) + '\n')
    print(f'Generated {len(rows)} matched runs, {len(groups)} pairs')


if __name__ == '__main__':
    main()
