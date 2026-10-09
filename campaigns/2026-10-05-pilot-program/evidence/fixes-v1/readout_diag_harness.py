"""F5 harness: DIAG_PY from freeze_p.py on crafted run directories with known answers (synthetic)."""
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
C = Path('/home/kaimoe/lab/bnjettag/campaigns/2026-10-05-pilot-program')
spec = importlib.util.spec_from_file_location('freeze_p', C / 'freeze_p.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
root = Path(tempfile.mkdtemp())
runs, out = root / 'runs', root / 'ro' / 'diag'
out.mkdir(parents=True)
rows = [{'name': 'a', 'program_arm': 'A350-C', 'seed': 1, 'budget': 350000, 'round': 'R1', 'variant': None},
        {'name': 'nb', 'program_arm': 'NB350-C', 'seed': 1, 'budget': 350000, 'round': 'R1', 'variant': 'nb'}]
(root / 'index.json').write_text(json.dumps({'runs': rows}))
def rec(e, q, k, v, ebops, pl=None, stepped=1, ratio=None, wb=None):
    w = {'bit_block_0_attn_scores__in0': {'bits': q}, 'bit_block_0_attn_scores__in1': {'bits': k},
         'bit_block_0_attn_ctx__in1': {'bits': v}, 'input_proj_in': {'bits': [2.0, 2.0]}}
    r = {'epoch': e, 'widths': w, 'ebops': ebops, 'ebops_traced': int(ebops is not None), 'per_layer': pl,
         'pid_stepped': stepped, 'ebops_in_training_over_traced': ratio, 'val_categorical_accuracy': 0.3 + e / 1000,
         'val_macro_auc': 0.7}
    if wb is not None:
        r['weight_bits_mean'] = wb
    return r
for name in ('a', 'nb'):
    run = runs / name
    (run / 'snapshots' / 'epoch-0010').mkdir(parents=True)
    recs = [rec(0, [1, 1], [1, 1], [1, 1], 900000, ratio=1.0, wb=4.0),
            rec(1, [0, 1], [1, 1], [0, 0], None, stepped=0, wb=3.5),
            rec(2, [0, 0], [1, 1], [0, 0], None, stepped=0, wb=3.0),     # Q all zero -> uniform at 2
            rec(9, [0, 0], [0, 0], [0, 0], 340000, pl={'blk0_attn_softmax': 100000, 'blk0_attn_Wq': 40000,
                                                         'ffn_1': 150000, 'input_proj': 30000, 'head': 20000},
                ratio=1.2, wb=2.0)]
    (run / 'activation_widths.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in recs))
    (run / 'snapshots' / 'epoch-0010' / 'state.json').write_text(json.dumps({'best_feasible': None, 'best_auc': {'epoch': 0}}))
(out / 'a26-last-a.json').write_text(json.dumps({'runs': [{'status': 'ok', 'checkpoint': 'x', 'entropy': {'b0': {'heads': [
    {'entropy_over_log_n': 0.5}, {'entropy_over_log_n': 1.0}]}}}]}))
(out / 'a26-unc-a.json').write_text(json.dumps({'runs': [{'status': 'ok', 'checkpoint': 'u', 'entropy': {'b0': {'heads': [
    {'entropy_over_log_n': 0.25}]}}}]}))
p = subprocess.run([sys.executable, '-', str(runs), str(root / 'index.json'), str(out), '10'], input=m.DIAG_PY,
                   capture_output=True, text=True)
print(p.stdout.strip(), p.stderr[-2000:])
d = json.loads((out.parent / 'readout_diag.json').read_text())
a, nb = d['arms']
checks = {
    'descriptive flag': d['descriptive_only'] is True and d['rule_input'] is False,
    't_uniform = 2 (Q all zero in the only block)': a['t_uniform'] == 2,
    't_budget = 9': a['t_budget'] == 9,
    'site order: V first (1), Q (2), K (9), input_proj never': [s for s, _ in a['site_order']] ==
        ['bit_block_0_attn_ctx__in1', 'bit_block_0_attn_scores__in0', 'bit_block_0_attn_scores__in1', 'input_proj_in']
        and a['site_order'][-1][1] is None,
    'cost split at min-EBOPs epoch 9': a['cost_split']['epoch'] == 9 and a['cost_split']['share_of_budget'] == {
        'attention_nonsoftmax': 40000 / 350000, 'ffn': 150000 / 350000, 'head_and_other': 20000 / 350000,
        'input_proj': 30000 / 350000, 'softmax_tables': 100000 / 350000},
    'controller error over stepped epochs (1.0, 1.2)': a['controller_error']['n'] == 2 and a['controller_error']['median'] == 1.1
        and a['controller_error']['max'] == 1.2,
    'NB weight bits at t_budget and epoch 9': nb['nb_weight_bits_mean'] == {'at_t_budget': 2.0, 'at_epoch_9': 2.0}
        and 'nb_weight_bits_mean' not in a,
    'a26 last and unconstrained means': a['last_epoch']['attn_entropy_norm_mean'] == 0.75
        and a['unconstrained']['attn_entropy_norm_mean'] == 0.25 and 'unconstrained' not in nb,
}
for k, v in checks.items():
    print('PASS' if v else 'FAIL', k)
print('DIAG_HARNESS', 'ALL_PASS' if all(checks.values()) else 'FAIL', len(checks))
