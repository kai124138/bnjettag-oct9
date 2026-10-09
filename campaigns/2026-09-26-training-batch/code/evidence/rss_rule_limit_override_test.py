"""PREFLIGHT gate v6 fix: rss_rule_epoch10_20.awk honours `-v limit=`, default 8192 (2026-09-28).
Same synthetic logs as rss_rules_8192_test.py, run with no -v limit, -v limit=8192 and
-v limit=6144, plus the four Delta canary v2 arm logs. System awk; a check, not a result.
Expected boundary delta (rss20 - rss10) at rss10 2150: (8192-2150)/9.5 = 636.0, (6144-2150)/9.5 = 420.4."""
import subprocess
from pathlib import Path

M = Path(__file__).resolve().parents[2] / 'manifests'
D = M.parents[1] / '2026-09-27-delta-screen' / 'logs'


def log(series, attempts_before=None):
    lines = ['==== ARM_ATTEMPT 1']
    if attempts_before:
        lines += [f'[epoch {i}/7000] EBOPs=1 host_rss_mb={v:.0f}' for i, v in enumerate(attempts_before, 1)]
        lines.append('==== ARM_ATTEMPT 2')
    lines += [f'[epoch {i}/7000] EBOPs=1 ' + ('host_rss_mb=na' if v is None else f'host_rss_mb={v:.0f}')
              for i, v in enumerate(series, 1)]
    return '\n'.join(lines) + '\n'


def lin(base, d10, n=20):
    return [base + d10 * (i - 10) / 10 for i in range(1, n + 1)]


cases = [(n, log(lin(2150, d))) for n, d in [('d145', 145), ('d420', 420), ('d425', 425), ('d470', 470),
                                            ('d630', 630), ('d650', 650), ('d900', 900)]]
cases += [('reset', log(lin(2150, 145), attempts_before=lin(2150, 900, 15))),
          ('pending', log(lin(2150, 145, 12))), ('na', log([None] * 20))]
cases += [(f'delta-E-k4-s{s}', (D / f'canary-v2-E-k4-s{s}.log').read_text()) for s in (1, 2, 3, 4)]
for extra in ([], ['-v', 'limit=8192'], ['-v', 'limit=6144']):
    tag = extra[1] if extra else 'default'
    for name, text in cases:
        p = subprocess.run(['awk', '-v', f'arm={name}', *extra, '-f', str(M / 'rss_rule_epoch10_20.awk')],
                           input=text, capture_output=True, text=True)
        print(f'[{tag}] exit={p.returncode} {p.stdout.strip()}')
