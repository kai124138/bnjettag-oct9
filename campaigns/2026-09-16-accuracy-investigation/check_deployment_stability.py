"""Choose correction-constant representation using internal selection data only.

All arithmetic candidates use explicit float32 multiplication and addition.
Quantization rounds constants to 8/10/12/16 fractional bits, nearest-even;
it does not simulate saturation, accumulator precision, or folded FPGA heads.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from calibrate_outputs import paired_ci


REPRESENTATIONS = ('fractional8', 'fractional10', 'fractional12', 'fractional16', 'float32')


def constants(scale, bias, representation):
    s, b = np.asarray(scale, dtype=np.float64), np.asarray(bias, dtype=np.float64)
    if representation.startswith('fractional'):
        denominator = 2 ** int(representation.removeprefix('fractional'))
        s, b = np.rint(s*denominator)/denominator, np.rint(b*denominator)/denominator
    return s.astype(np.float32), b.astype(np.float32)


def apply(z, scale, bias):
    # Explicit staged arithmetic; do not implicitly promote input or fuse operations.
    multiplied = np.multiply(z.astype(np.float32), scale, dtype=np.float32)
    return np.add(multiplied, bias, dtype=np.float32)


def summary(y, z, reference=None):
    p = z.argmax(1)
    out = {'accuracy': float((p == y).mean()),
           'top_score_tie_rate': float(((z == z.max(1, keepdims=True)).sum(1) > 1).mean())}
    if reference is not None:
        out['prediction_disagreement_vs_float64'] = float((p != reference.argmax(1)).mean())
        out['paired_vs_float64'] = paired_ci(y, reference, z)
    return out


def selection_indices(y, seed):
    rng = np.random.default_rng(seed)
    selected = []
    for k in range(5):
        ids = rng.permutation(np.flatnonzero(y == k))
        selected.extend(ids[len(ids)//2:])
    return np.asarray(selected)


def choose_representation(selection_accuracy):
    # Prespecified ordering prefers coarser constants on exact accuracy ties.
    return max(REPRESENTATIONS, key=lambda name: selection_accuracy[name])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--arms', nargs='+')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.directory
    report_bytes = (root/'calibration_report.json').read_bytes()
    report = json.loads(report_bytes)
    with np.load(root/'labels.npz', allow_pickle=False) as data:
        onehot = data['validation']
        assert np.isin(onehot, [0, 1]).all() and np.all(onehot.sum(1) == 1)
        yv = onehot.argmax(1)
    select = selection_indices(yv, report['seed'])
    assert len(select) == report['n_select']
    output = {'protocol': 'Keep the previously validation-selected correction. Compare explicit float32 arithmetic and 8/10/12/16 fractional-bit constants on the same internal selection half only. Maximize selection accuracy; exact ties prefer 8,10,12,16 fractional bits, then float32. Freeze representation before accessing held-out test logits/labels. Evaluate that winner plus prespecified float32 and float64 references.',
              'limitations': 'Reusing selection data for this extra representation choice adds validation-selection uncertainty. Event CIs are conditional on this trained model. Constant quantization uses nearest-even rounding with no saturation. This is not bit-accurate FPGA simulation; folding biases into a quantized head or using fused arithmetic needs separate verification.',
              'calibration_report_sha256': hashlib.sha256(report_bytes).hexdigest(),
              'selection_count': len(select), 'seed': report['seed'], 'runs': []}
    runs = [r for r in report['runs'] if args.arms is None or r['arm'] in args.arms]
    if args.arms is not None:
        assert set(args.arms) == {r['arm'] for r in runs}, 'Requested arm missing from calibration report'
    for run in runs:
        source = root/(run['arm']+'.npz')
        with np.load(source, allow_pickle=False) as data:
            zv = data['validation_logits'][select]
        assert zv.shape == (len(select), 5) and np.isfinite(zv).all()
        reference_v = zv.astype(np.float64)*run['scale']+run['bias']
        reported_accuracy = run['selection_accuracy'][run['selected_correction']]
        assert abs((reference_v.argmax(1) == yv[select]).mean()-reported_accuracy) < 1e-12
        params = {name: constants(run['scale'], run['bias'], name) for name in REPRESENTATIONS}
        val = {name: summary(yv[select], apply(zv, *params[name]), reference_v) for name in REPRESENTATIONS}
        winner = choose_representation({name: val[name]['accuracy'] for name in REPRESENTATIONS})
        # The representation choice is complete before held-out data access.
        with np.load(root/'labels.npz', allow_pickle=False) as data:
            onehot = data['test']
            assert np.isin(onehot, [0, 1]).all() and np.all(onehot.sum(1) == 1)
            yt = onehot.argmax(1)
        with np.load(source, allow_pickle=False) as data:
            zt = data['test_logits']
        assert zt.shape == (len(yt), 5) and np.isfinite(zt).all()
        reference_t = zt.astype(np.float64)*run['scale']+run['bias']
        chosen = apply(zt, *params[winner])
        f32 = apply(zt, *params['float32'])
        baseline = summary(yt, zt)
        assert abs(baseline['accuracy']-run['baseline_test']['accuracy']) < 1e-12
        assert abs(summary(yt, reference_t)['accuracy']-run['corrected_test']['accuracy']) < 1e-12
        rec = {'arm': run['arm'], 'selected_correction': run['selected_correction'],
               'prediction_archive_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'selection_representations': val, 'chosen_representation': winner,
               'chosen_scale': params[winner][0].tolist(), 'chosen_bias': params[winner][1].tolist(),
               'baseline_test': baseline, 'float64_corrected_test': summary(yt, reference_t),
               'float32_corrected_test': summary(yt, f32, reference_t),
               'chosen_corrected_test': summary(yt, chosen, reference_t),
               'chosen_vs_uncorrected_test': paired_ci(yt, zt, chosen),
               'float32_vs_uncorrected_test': paired_ci(yt, zt, f32)}
        output['runs'].append(rec)
        print(run['arm'], winner, rec['chosen_vs_uncorrected_test'], flush=True)
    path = args.output or root/'deployment_stability_report.json'
    path.write_text(json.dumps(output, indent=2)+'\n')


if __name__ == '__main__':
    main()
