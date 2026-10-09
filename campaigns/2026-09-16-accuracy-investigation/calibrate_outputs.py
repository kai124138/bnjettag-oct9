"""Validation-only choice of small affine output corrections, then held-out test.

No neural-network training. The held-out archive never fits/selects a correction.
The internal validation split was used for model selection already; confirm any
deployment improvement with new seeds / fresh untouched data.
"""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from scipy.stats import rankdata


def auc(y, p):
    return [float((rankdata(p[:, k])[y == k].sum() - (y == k).sum()*((y == k).sum()+1)/2)
                  / ((y == k).sum()*(y != k).sum())) for k in range(5)]


def metrics(y, z):
    pred = z.argmax(1)
    p = softmax(z, axis=1)
    cm = np.bincount(5*y+pred, minlength=25).reshape(5, 5)
    per_auc = auc(y, p)
    return {'accuracy': float((pred == y).mean()), 'macro_auc': float(np.mean(per_auc)),
            'per_class_auc': per_auc, 'confusion': cm.tolist(),
            'recall': (cm.diagonal()/cm.sum(1)).tolist(),
            'class_counts': cm.sum(1).tolist(), 'predicted_counts': cm.sum(0).tolist(),
            'top2_accuracy': float((np.argsort(z, axis=1)[:, -2:] == y[:, None]).any(1).mean()),
            'nll': float(np.mean(logsumexp(z, axis=1)-z[np.arange(len(y)), y])),
            'tie_rate': float(((z == z.max(1, keepdims=True)).sum(1) > 1).mean())}


def paired_ci(y, base, new):
    d = (new.argmax(1) == y).astype(float) - (base.argmax(1) == y)
    delta = d.mean()
    width = 1.96 * np.std(d, ddof=1) / np.sqrt(len(d))
    return {'delta': float(delta), 'ci95': [float(delta-width), float(delta+width)],
            'corrected': int((d == 1).sum()), 'broken': int((d == -1).sum()),
            'scope': 'paired event-level normal interval; one seed, not training uncertainty'}


def fit_nll(z, y, vector=False):
    z = z.astype(float)
    n = len(y)
    def unpack(v):
        return (np.exp(v[:5]), np.r_[v[5:], 0.]) if vector else (np.ones(5), np.r_[v, 0.])
    def loss(v):
        scale, bias = unpack(v)
        q = z*scale+bias
        value = np.mean(logsumexp(q, axis=1)-q[np.arange(n), y])
        residual = softmax(q, axis=1)
        residual[np.arange(n), y] -= 1
        gb = residual.mean(0)[:4]
        gradient = np.r_[(residual*z*scale).mean(0), gb] if vector else gb
        return value, gradient
    fit = minimize(loss, np.zeros(9 if vector else 4), jac=True, method='L-BFGS-B',
                   bounds=([(-2., 2.)]*5 + [(-3., 3.)]*4) if vector else [(-3., 3.)]*4,
                   options={'maxiter': 100, 'ftol': 1e-10})
    if not fit.success:
        raise RuntimeError(f'Calibration optimizer failed: {fit.message}')
    s, b = unpack(fit.x)
    return s, b


def fit_accuracy_bias(z, y, initial=None):
    """Tie-aware coordinate proposals with verified improvements, up to four passes.

    Include equality thresholds because argmax breaks ties by column index.
    Verify realized floating-point accuracy before every accepted update.
    """
    bias = np.zeros(5) if initial is None else initial.copy()
    for _ in range(4):
        before = (np.argmax(z+bias, axis=1) == y).sum()
        for k in range(5):
            others = z+bias
            others[:, k] = -np.inf
            rival = others.argmax(1)
            threshold = others[np.arange(len(y)), rival] - z[:, k]
            order = np.argsort(threshold, kind='stable')
            t = threshold[order]
            gain = (y == k).astype(int) - (rival == y).astype(int)
            start = np.r_[0, np.flatnonzero(t[:-1] != t[1:])+1]
            end = np.r_[start[1:]-1, len(t)-1]
            thresholds = t[start]
            cumulative = np.cumsum(gain[order])[end]
            before_group = np.r_[0, cumulative[:-1]]
            # At equality only rivals with a larger column index lose to k.
            equality_gain = np.add.reduceat((gain*(k < rival))[order], start)
            equality_counts = before_group + equality_gain
            # Midpoints avoid nextafter values rounding back to ties after z+b.
            between = thresholds[:-1] + (thresholds[1:]-thresholds[:-1])/2
            candidates = np.r_[thresholds, between]
            counts = np.r_[equality_counts, cumulative[:-1]] + (rival == y).sum()
            valid = np.abs(candidates) <= 3
            counts[~valid] = -1
            current = (np.argmax(z+bias, axis=1) == y).sum()
            # Numerical threshold arithmetic can differ from realized argmax.
            # Check the strongest proposal and both allowed boundary values.
            proposals = [-3., 3.]
            if counts.max() > current:
                idx = np.flatnonzero(counts == counts.max())
                proposals.append(candidates[idx[np.argmin(np.abs(candidates[idx]-bias[k]))]])
            best_value, best_count = bias[k], current
            for value in proposals:
                trial = bias.copy()
                trial[k] = value
                realized = (np.argmax(z+trial, axis=1) == y).sum()
                if realized > best_count:
                    best_value, best_count = value, realized
            bias[k] = best_value
        if (np.argmax(z+bias, axis=1) == y).sum() == before:
            break
    return bias


def select_correction(accuracies):
    """Validation accuracy first; fewer fitted parameters break exact ties."""
    parameters = {'identity': 0, 'bias_nll': 4, 'bias_accuracy': 4,
                  'vector_nll': 9, 'vector_accuracy': 9}
    return max(accuracies, key=lambda name: (accuracies[name], -parameters[name]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root = args.directory
    with np.load(root/'labels.npz') as labels:
        yv, yt = labels['validation'].argmax(1), labels['test'].argmax(1)
    rng = np.random.default_rng(20260917)
    # Stratified disjoint halves, fixed before looking at any correction's result.
    fit, select = [], []
    for k in range(5):
        ids = rng.permutation(np.flatnonzero(yv == k))
        fit.extend(ids[:len(ids)//2]); select.extend(ids[len(ids)//2:])
    fit, select = np.array(fit), np.array(select)
    report = {'protocol': 'Fit one stratified half of internal validation; select on the other half by accuracy, tie prefer fewer parameters. Evaluate fixed choice on held-out test. No test labels used for choice.',
              'n_fit': len(fit), 'n_select': len(select), 'seed': 20260917, 'runs': []}
    for path in sorted(root.glob('r*.npz')):
        start = time.perf_counter()
        with np.load(path) as data:
            zv, zt = data['validation_logits'].astype(float), data['test_logits'].astype(float)
        candidates = {'identity': (np.ones(5), np.zeros(5))}
        candidates['bias_nll'] = fit_nll(zv[fit], yv[fit])
        candidates['vector_nll'] = fit_nll(zv[fit], yv[fit], vector=True)
        candidates['bias_accuracy'] = (np.ones(5), fit_accuracy_bias(zv[fit], yv[fit]))
        s, b = candidates['vector_nll']
        candidates['vector_accuracy'] = (s, fit_accuracy_bias(zv[fit]*s, yv[fit], b))
        val_acc = {name: float(((zv[select]*s+b).argmax(1) == yv[select]).mean())
                   for name, (s, b) in candidates.items()}
        winner = select_correction(val_acc)
        s, b = candidates[winner]
        transformed = zt*s+b
        rec = {'arm': path.stem, 'selected_correction': winner,
               'selection_accuracy': val_acc, 'scale': s.tolist(), 'bias': b.tolist(),
               'baseline_test': metrics(yt, zt), 'corrected_test': metrics(yt, transformed),
               'paired_improvement': paired_ci(yt, zt, transformed),
               'validation_paired_improvement': paired_ci(yv[select], zv[select], zv[select]*s+b),
               'baseline_validation': metrics(yv, zv),
               'temperature_argmax_invariant': bool(np.array_equal(zt.argmax(1), (zt/2).argmax(1))),
               'candidate_parameters': {name: {'scale': a.tolist(), 'bias': c.tolist()} for name,(a,c) in candidates.items()},
               'seconds': time.perf_counter()-start}
        report['runs'].append(rec)
        (root/'calibration_report.json').write_text(json.dumps(report, indent=2))
        print(path.stem, winner, rec['baseline_test']['accuracy'], rec['corrected_test']['accuracy'], rec['paired_improvement'], flush=True)
    # Choose model+correction by internal selection accuracy, never test accuracy.
    report['validation_selected_arm'] = max(report['runs'], key=lambda r: r['selection_accuracy'][r['selected_correction']])['arm']
    (root/'calibration_report.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
