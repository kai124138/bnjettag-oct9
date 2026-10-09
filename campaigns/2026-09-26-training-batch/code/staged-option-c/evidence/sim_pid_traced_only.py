"""Toy simulation for option (c) (staged patch 0032). NOT a result: a synthetic plant, not the model.

Drives hgq2 0.1.9's real `BetaPID` (get_ebops / set_beta monkeypatched) and the staged
`ablation.pid_begin_traced_only` / `is_traced_epoch` over 7,000 epochs, k = 10, the production PID
(p 1.0, i 0.05, d 0, warmup 1, log, beta in [1e-10, 1e-3], init 1e-7), target T = 350,000.

Plant (log10 space, first-order lag toward a beta-dependent equilibrium, per epoch):
    L_eq(beta) = log10(E0) - b * (log10(beta) + 7),   E0 = 9.4e6 (arm A's initial order)
    L <- L + (L_eq - L) / tau + N(0, sigma),  traced E = max(10 ** L, floor)
    in-training E = r * traced E (reading 1: the excess scales the whole total, floor included)
Controllers: A (regime A: traced every epoch), P (regime B slot P, 42abed4b: steps every epoch,
reads in-training on untraced epochs), C/per_epoch and C/per_step (option c, 0032).
Stationary readout: median traced E over the traced epochs of the last 2,000 epochs, / T.

    python sim_pid_traced_only.py   (cwd = code/staged-option-c/code)
"""
import copy
import math
import os
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
sys.path.insert(0, os.getcwd())
import numpy as np
from hgq.utils.sugar import BetaPID
from bnhgq2 import ablation

T, E0, R, EPOCHS, K = 350_000.0, 9.4e6, 1.08, 7000, 10
PID = {'init_beta': 1e-07, 'p': 1.0, 'i': 0.05, 'd': 0.0, 'warmup': 1, 'log': True,
       'min_beta': 1e-10, 'max_beta': 0.001, 'damp_beta_on_target': 0.0}
CFG = {'train': {'epochs': EPOCHS, 'ebops_trace_every': K, 'ebops_trace_sample': 'train_full',
                 'ebops_reload_check': 'stored', 'ebops': {'pid': dict(PID, target_ebops=T)}},
       'experiment': {'snapshot_every_epochs': 500}}


def run(controller, tau, b, r=R, floor=0.0, target=T, sigma=0.003, seed=0, p=None):
    cfg = copy.deepcopy(CFG)
    cfg['train']['ebops']['pid']['target_ebops'] = target
    if p is not None:   # illustration only: the arms' p is 1.0
        cfg['train']['ebops']['pid']['p'] = p
    mode = None
    if controller.startswith('C/'):
        cfg['train']['ebops'].update(pid_input='traced_only', pid_traced_integral=controller[2:])
        mode = ablation.pid_traced_only(cfg)
    rng = np.random.default_rng(seed)
    sim = {'stored': E0, 'beta': PID['init_beta']}
    pid = BetaPID(**cfg['train']['ebops']['pid'])
    pid.get_ebops = lambda: sim['stored']
    pid.set_beta = lambda beta: sim.__setitem__('beta', beta)
    pid.on_train_begin({})
    L = math.log10(E0)
    traced_log = []
    for e in range(EPOCHS):
        if mode is None:
            pid.on_epoch_begin(e, {})
        else:
            ablation.pid_begin_traced_only(pid, cfg, e, mode)
        l_eq = math.log10(E0) - b * (math.log10(sim['beta']) + 7)
        L += (l_eq - L) / tau + rng.normal(0, sigma)
        E = max(10 ** L, floor)
        L = math.log10(E)
        traced = controller == 'A' or ablation.is_traced_epoch(cfg, e)
        if traced:
            traced_log.append((e, E))
        if controller == 'A' or controller == 'P':
            sim['stored'] = E if traced else r * E
            pid.on_epoch_end(e, {})
        elif traced:
            sim['stored'] = E
            pid.on_epoch_end(e, {})
    tail = [E for e, E in traced_log if e >= EPOCHS - 2000]
    late = np.log10(np.array(tail) / target)
    first = next((e for e, E in traced_log if abs(E / target - 1) <= 0.02), None)
    return {'median_over_T': float(np.median(tail) / target), 'sd_log10': float(np.std(late)),
            'first_within_2pct': first, 'beta_end': sim['beta'], 'integral_end': pid.pid.integral}


def line(tag, **kw):
    print(tag + ' ' + ' '.join(f'{k}={v:.4g}' if isinstance(v, float) else f'{k}={v}' for k, v in kw.items()), flush=True)


if __name__ == '__main__':
    print(f'# toy plant, not a result; r={R}, k={K}, epochs={EPOCHS}, T={T:.0f}; '
          f'slot-P prediction T*r^-0.9 = {T * R ** -0.9:.0f} (median/T {R ** -0.9:.4f})')
    # Settled-plant bound (tau << k): e_{n+1} = (1 - b p - b i s) e_n + b p e_{n-1}; Jury: b p < 1 and
    # b (p + i s / 2) < 1, s = 10 (per_epoch) or 1 (per_step).
    for s_ in (10, 1):
        print(f'# settled-plant stability bound, p=1, i=0.05, s={s_}: b < {1 / (1 + 0.05 * s_ / 2):.3f}')
    for b in (0.5, 0.75, 1.0, 1.5):
        for tau in (2, 5, 20, 50):
            for controller in ('A', 'P', 'C/per_epoch', 'C/per_step'):
                line('SIM', controller=controller, b=b, tau=tau, **run(controller, tau, b))
    # illustration only (not an arm knob): halving p restores the fast-plant b = 1 case
    for controller in ('C/per_epoch', 'C/per_step'):
        line('SIM_P0.5_ILLUSTRATION', controller=controller, b=1.0, tau=2, p=0.5, **run(controller, 2, 1.0, p=0.5))
    # A07-350: traced floor 343,053 < T (headroom 6,947); reading 1 puts the in-training floor at
    # r * 343,053 > T. Then a truly infeasible budget (T below the traced floor).
    for controller in ('P', 'C/per_epoch', 'C/per_step'):
        line('SIM_A07_READING1', controller=controller, b=0.5, tau=5, **run(controller, 5, 0.5, floor=343_053.0))
    for controller in ('P', 'C/per_epoch', 'C/per_step'):
        line('SIM_INFEASIBLE_T_0.95_FLOOR', controller=controller, b=0.5, tau=5,
             **run(controller, 5, 0.5, floor=343_053.0, target=0.95 * 343_053.0))
