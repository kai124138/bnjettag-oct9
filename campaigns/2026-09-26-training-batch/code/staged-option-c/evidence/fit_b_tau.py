"""Fit the option-(c) toy plant gain b and lag tau from the stopped regime-A pilot's W&B history.
TELEMETRY, NOT RESULTS. Read-only W&B access; needs WANDB_API_KEY in the environment.

Plant, as in sim_pid_traced_only.py (log10 space, per epoch):
    L_e = a * L_{e-1} + g * lb_e + c,   a = 1 - 1/tau,  g = -b/tau   =>  tau = 1/(1-a),  b = -g/(1-a)
L_e = log10 traced EBOPs at the end of epoch e (W&B `ebops`, what option (c) reads);
lb_e = log10 beta in force during epoch e (W&B `beta` at step e+1: set by BetaPID.on_epoch_begin(e),
unchanged by on_epoch_end). b = -d log10 EBOPs / d log10 beta at equilibrium.

Fits (OLS), per run and pooled with run-specific intercepts, per epoch window:
  arx        L_e = a L_{e-1} + g lb_e + c
  arx+trend  L_e = a L_{e-1} + g lb_e + c + h e         (absorbs the non-beta compression drift)
  diff       dL_e = a dL_{e-1} + g dlb_e + c           (first differences; c = drift rate)
Uncertainty: moving-block bootstrap (block 10 epochs, 2000 reps, per run, rows resampled as
(y, X) tuples), 95 % percentile interval. Closed loop: spectral radius of the fitted (a, g) plant
held for D = 10 epochs with the per_epoch integral (s = 10), p = 1, i = 0.05:
    M = [[A + G (p + i s), G i], [s, 1]],  A = a^D,  G = g (1 - a^D) / (1 - a)
which reduces to the plan's settled-plant recurrence when A = 0, G = -b.

    WANDB_API_KEY=... python fit_b_tau.py            (writes nothing; stdout is the log)
"""
import json
import os
import sys

import numpy as np

ENTITY_PROJECT = 'kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe'
RUNS = {'A-s1': 'c16aff0707b9', 'A-s2': '8560dcb87a4c', 'D-s1': '81df1017a0eb', 'E1-s1': '5fd00a94e508'}
P, I, D, S, T = 1.0, 0.05, 10, 10, 350_000.0
WINDOWS = {'w1 e1-40 (fresh-init collapse)': (1, 40), 'w2 e40-90': (40, 90),
           'w3 e90-end': (90, 10_000), 'w23 e40-end': (40, 10_000)}
NBOOT, BLOCK = 2000, 10


def fetch(cache=None):
    if cache and os.path.exists(cache):
        return json.load(open(cache))
    import wandb
    api = wandb.Api(timeout=120)
    out = {}
    for name, rid in RUNS.items():
        rows = list(api.run(f'{ENTITY_PROJECT}/{rid}').scan_history(
            keys=['epoch', 'beta', 'ebops', 'pid_ebops', 'ebops_in_training', 'learning_rate']))
        out[name] = rows
    if cache:
        json.dump(out, open(cache, 'w'))
    return out


def series(rows):
    by = {}
    for r in rows:                      # keep the last row per epoch (guards against resume replays)
        by[int(r['epoch'])] = r
    ep = np.array(sorted(by))
    assert (np.diff(ep) == 1).all() and ep[0] == 0, 'gap in epochs'
    for e in ep:
        assert abs(by[e]['pid_ebops'] - by[e]['ebops']) <= 1e-6 * by[e]['ebops'], ('pid_ebops != ebops', e)
    L = np.log10([by[e]['ebops'] for e in ep])
    Lt = np.log10([by[e]['ebops_in_training'] for e in ep])
    lb = np.log10([by[e]['beta'] for e in ep])
    lr = np.array([by[e]['learning_rate'] for e in ep])
    return ep, L, Lt, lb, lr


def design(ep, L, lb, lo, hi, form):
    idx = np.arange(max(lo, 2), min(hi, int(ep[-1])) + 1, dtype=int)
    if len(idx) == 0:
        return idx, np.zeros(0), np.zeros((0, 4))
    if form == 'diff':
        y = L[idx] - L[idx - 1]
        X = np.column_stack([L[idx - 1] - L[idx - 2], lb[idx] - lb[idx - 1], np.ones(len(idx))])
    else:
        y = L[idx]
        cols = [L[idx - 1], lb[idx], np.ones(len(idx))]
        if form == 'arx+trend':
            cols.append(idx.astype(float) / 100.)
        X = np.column_stack(cols)
    return idx, y, X


def ols(blocks):
    """blocks: list of (y, X) per run; pooled with run-specific intercepts (column 2 is the intercept)."""
    n_runs = len(blocks)
    ys, Xs = [], []
    for k, (y, X) in enumerate(blocks):
        dummies = np.zeros((len(y), n_runs))
        dummies[:, k] = 1.
        Xs.append(np.column_stack([X[:, :2], dummies, X[:, 3:]]))
        ys.append(y)
    y, X = np.concatenate(ys), np.vstack(Xs)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef[0], coef[1]


def b_tau(a, g):
    if a >= 1:
        return float('nan'), float('inf')
    return -g / (1 - a), 1 / (1 - a)


def rho(a, g, p=P, i=I, D=D, s=S):
    if a >= 1:
        return float('nan')
    A = a ** D
    G = g * (1 - a ** D) / (1 - a)
    M = np.array([[A + G * (p + i * s), G * i], [s, 1.]])
    return float(max(abs(np.linalg.eigvals(M))))


def boot(blocks, rng):
    out = []
    for _ in range(NBOOT):
        bb = []
        for y, X in blocks:
            n = len(y)
            starts = rng.integers(0, max(n - BLOCK, 0) + 1, size=int(np.ceil(n / BLOCK)))
            sel = np.concatenate([np.arange(s0, min(s0 + BLOCK, n)) for s0 in starts])[:n]
            bb.append((y[sel], X[sel]))
        a, g = ols(bb)
        b, tau = b_tau(a, g)
        out.append((a, g, b, tau, rho(a, g)))
    return np.array(out)


def ci(x):
    x = x[np.isfinite(x)]
    if len(x) < NBOOT // 2:
        return f'[n/a: {NBOOT - len(x)} of {NBOOT} reps a>=1]'
    return f'[{np.percentile(x, 2.5):.3g}, {np.percentile(x, 97.5):.3g}]'


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else None
    data = {k: series(v) for k, v in fetch(cache).items()}
    rng = np.random.default_rng(20260928)
    print('# TELEMETRY, NOT RESULTS. Regime-A pilot (stopped), traced every epoch, far from target '
          f'(T={T:.0f}); b, tau fitted on traced log10 EBOPs vs log10 beta.')
    print(f'# option (c) bound (settled plant, p={P}, i={I}, D={D}, per_epoch): b < {1 / (P + I * D / 2):.3f}')
    for k, (ep, L, Lt, lb, lr) in data.items():
        print(f'RUN {k} epochs 0-{ep[-1]} ({len(ep)} rows after dedupe) ebops {10 ** L[0]:.4g}->{10 ** L[-1]:.4g} '
              f'beta {10 ** lb[0]:.3g}->{10 ** lb[-1]:.3g} lr {lr[0]:.3g}->{lr[-1]:.3g}')
    for signal in ('traced', 'in_training'):
        for form in ('arx', 'arx+trend', 'diff'):
            for wname, (lo, hi) in WINDOWS.items():
                blocks, pr = [], []
                for k, (ep, L, Lt, lb, lr) in data.items():
                    Ls = L if signal == 'traced' else Lt
                    idx, y, X = design(ep, Ls, lb, lo, hi, form)
                    if len(y) < 15:
                        continue
                    blocks.append((y, X))
                    a, g = ols([(y, X)])
                    b, tau = b_tau(a, g)
                    corr = np.corrcoef(lb[idx], idx)[0, 1]
                    pr.append(f'{k}:b={b:.3g},tau={tau:.3g},a={a:.3f},rho={rho(a, g):.3g},corr(lb,e)={corr:.3f}')
                if not blocks:
                    continue
                a, g = ols(blocks)
                b, tau = b_tau(a, g)
                bs = boot(blocks, rng)
                print(f'FIT signal={signal} form={form} {wname} pooled n={sum(len(y) for y, _ in blocks)}: '
                      f'b={b:.3g} CI{ci(bs[:, 2])} tau={tau:.3g} CI{ci(bs[:, 3])} a={a:.4f} '
                      f'rho_c={rho(a, g):.3g} CI{ci(bs[:, 4])} boot_frac(b>=0.80)={np.mean(bs[:, 2] >= 0.8):.3f}')
                print('    per-run ' + ' | '.join(pr))
    # p that restores the settled-plant bound for a given b: p < 1/b - i*D/2 and p < 1/b
    for bval in (0.8, 1.0, 1.2, 1.5):
        print(f'# p_max for b={bval}: settled bound p < {1 / bval - I * D / 2:.3f}')


if __name__ == '__main__':
    main()
