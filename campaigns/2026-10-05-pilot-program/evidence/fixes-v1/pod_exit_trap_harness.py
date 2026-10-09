import importlib.util, subprocess, sys, tempfile, os
from pathlib import Path
C = Path('/home/kaimoe/lab/bnjettag/campaigns/2026-10-05-pilot-program')
spec = importlib.util.spec_from_file_location('freeze_p', C / 'freeze_p.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.OPTS['bounded'] = True
m.POD_DEADLINE_S, m.RESERVE_S, m.PREARM_RETRY_S, m.KILL_AFTER_S = 8, 2, 3, 1
root = Path(tempfile.mkdtemp())
m.RUN_ROOT = str(root)
name = 'armx'
(root / 'runs' / name).mkdir(parents=True)
def script(pre, fake, marker=False):
    rp = '\n'.join(m.run_pack_line(name)).replace('python -u /work/code/run_pack.py "$PACKS" 500', fake)
    mk = f'touch {root}/runs/{name}/RSS_GATE_FAIL.json\n' if marker else f'rm -f {root}/runs/{name}/RSS_GATE_FAIL.json\n'
    return 'set -euo pipefail\n' + m.pod_exit_trap() + '\n' + mk + pre + '\nRP=0; PACKS=x\n' + rp + '\nexit "$RP"\n'
cases = [
  ('pre-arm failure at 0 s', 'false', 'true', False, 75),
  ('pre-arm failure at 4 s (> window)', 'sleep 4; false', 'true', False, 76),
  ('fingerprint-style exit 7 early', '(exit 7) || FP=$?; exit "$FP"', 'true', False, 75),
  ('run_pack exit 0', 'true', 'true', False, 0),
  ('run_pack exceeds budget (TERM honoured)', 'true', 'sleep 30', False, 124),
  ('run_pack ignores TERM -> KILL', 'true', "bash -c 'trap \"\" TERM; sleep 30'", False, 124),
  ('run_pack exit 1 with RSS_GATE_FAIL.json', 'true', 'bash -c "exit 1"', True, 5),
  ('run_pack exit 1, no marker (training failure)', 'true', 'bash -c "exit 1"', False, 76),
  ('epoch-0 all diverged exit 10', 'true', 'true; exit 10', False, 10),
  ('budget already spent before start', 'sleep 7', 'true', False, 124),
]
bad = 0
for label, pre, fake, marker, want in cases:
    p = subprocess.run(['bash', '-c', script(pre, fake, marker)], capture_output=True, text=True, timeout=60)
    ok = p.returncode == want; bad += not ok
    print('PASS' if ok else 'FAIL', f'{label}: exit {p.returncode} (want {want})', '|', ' '.join(p.stdout.split('\n')[-3:]).strip())
print('TRAP_HARNESS', 'ALL_PASS' if not bad else f'{bad} FAIL', len(cases))
