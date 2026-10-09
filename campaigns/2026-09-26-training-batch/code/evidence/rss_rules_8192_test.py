"""Synthetic-log check of manifests/rss_rule_epoch10_20.awk (limit 8192) and
manifests/rss_proj7000_epoch20.awk (2026-09-28, 8 GiB per-arm resize). System awk; not a result."""
import random
import subprocess
from pathlib import Path

M = Path(__file__).resolve().parents[2] / 'manifests'


def log(series, attempts_before=None):
    lines = ['==== ARM_ATTEMPT 1']
    if attempts_before:
        lines += [f'[epoch {i}/7000] EBOPs=1 host_rss_mb={v:.0f}' for i, v in enumerate(attempts_before, 1)]
        lines.append('==== ARM_ATTEMPT 2')
    lines += [f'[epoch {i}/7000] EBOPs=1 ' + ('host_rss_mb=na' if v is None else f'host_rss_mb={v:.0f}')
              for i, v in enumerate(series, 1)]
    return '\n'.join(lines) + '\n'


def run(awk, name, text):
    p = subprocess.run(['awk', '-v', f'arm={name}', '-f', str(M / awk)], input=text, capture_output=True, text=True)
    print(f'{awk} exit={p.returncode} {p.stdout.strip()}')


def lin(base, d10, n=20):   # rss10 = base, rss20 = base + d10, linear
    return [base + d10 * (i - 10) / 10 for i in range(1, n + 1)]


# epoch-10/20 rule: projection = rss10 + 9.5 * delta; boundary delta (8192 - 2150) / 9.5 = 636.0
for name, s in [('d145', lin(2150, 145)), ('d470', lin(2150, 470)), ('d630', lin(2150, 630)),
                ('d650', lin(2150, 650)), ('d900', lin(2150, 900))]:
    run('rss_rule_epoch10_20.awk', name, log(s))
run('rss_rule_epoch10_20.awk', 'reset', log(lin(2150, 145), attempts_before=lin(2150, 900, 15)))
run('rss_rule_epoch10_20.awk', 'pending', log(lin(2150, 145, 12)))
run('rss_rule_epoch10_20.awk', 'na', log([None] * 20))

# epoch-20 projection to 7,000
rng = random.Random(20260928)
for name, base, slope, noise in [('flat', 2150, 0.004, 0), ('s0.55', 2150, 0.55, 0), ('delta_worst', 2303, 0.63, 0),
                                 ('s0.90', 2150, 0.90, 0), ('incident85', 2150, 85, 0), ('s0.30_noise60', 2150, 0.30, 60)]:
    s = [base + slope * (i - 5) + (rng.uniform(-noise, noise) if noise else 0) for i in range(1, 21)]
    run('rss_proj7000_epoch20.awk', name, log(s))
run('rss_proj7000_epoch20.awk', 'reset', log([2150 + 0.004 * i for i in range(20)],
                                            attempts_before=[2150 + 85 * i for i in range(30)]))
run('rss_proj7000_epoch20.awk', 'pending', log([2150] * 19))
run('rss_proj7000_epoch20.awk', 'na', log([2150] * 7 + [None] + [2150] * 12))

# Real GPU telemetry: Delta canary v2 arm logs (commit a3a3362; Delta's patches on 42abed4b; K=4, A10;
# telemetry, not a result). Both rules on the healthy E-k4 arms, then the in-code gate form
# (least squares over process-epoch list indices 5..end, projected to 7,000) for comparison.
import re
D = M.parents[1] / '2026-09-27-delta-screen' / 'logs'
for s in (1, 2, 3, 4):
    f = D / f'canary-v2-E-k4-s{s}.log'
    text = f.read_text()
    run('rss_rule_epoch10_20.awk', f'delta-E-k4-s{s}', text)
    run('rss_proj7000_epoch20.awk', f'delta-E-k4-s{s}', text)
    v = [float(x) for x in re.findall(r'host_rss_mb=([0-9.]+)', text)]
    w = v[5:105]
    n = len(w)
    mx, my = (n - 1) / 2, sum(w) / n
    sl = sum((x - mx) * (y - my) for x, y in enumerate(w)) / sum((x - mx) ** 2 for x in range(n))
    b = my - sl * mx
    print(f'gate-form delta-E-k4-s{s} fit_indices 5-{4 + n} slope_mb_per_epoch {sl:.3f} baseline_mb {b:.0f} '
          f'projection_mb_at_7000 {b + sl * 7000:.0f} vs 6144 {"FAIL" if b + sl * 7000 > 6144 else "PASS"} '
          f'vs 8192 {"FAIL" if b + sl * 7000 > 8192 else "PASS"}')
