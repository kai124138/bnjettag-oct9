"""Shell-level test of the pilot-b wrapper tail (fingerprint gate, epoch-0 pod failure, fallback
guards) with stub python/nvidia-smi. Takes each Job's script verbatim from GPU_GATE_PASS on,
substitutes /data, /cmfp, /work. Not a result."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
M = Path('/Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-26-training-batch/manifests')
T = Path(sys.argv[1]); X42 = Path(sys.argv[2])
REAL = shutil.which('python3')

def script(job):
    s = json.loads((M / job).read_text())['spec']['template']['spec']['containers'][0]['args'][0]
    return 'set -euo pipefail\n' + s[s.index('python -c "import tensorflow'):]

def setup(name):
    root = T / name
    if root.exists(): shutil.rmtree(root)
    for d in ('data/chang-n64-20260926/n64/data', 'data/chang-n64-20260926/pilot-b/runs', 'cmfp', 'work', 'bin'):
        (root / d).mkdir(parents=True)
    (root / 'data/chang-n64-20260926/n64/data/READY.json').write_text('{}')
    shutil.copy(M / 'fingerprint/fingerprint_check.py', root / 'cmfp/fingerprint_check.py')
    stub = f'''#!/bin/bash
case "$*" in
  *"import tensorflow"*) echo GPU_GATE_PASS;;
  *fingerprint_check.py*) echo "FINGERPRINT_STUB $*"; if [ "${{FPRC:-0}}" != 0 ]; then echo "GPU_FINGERPRINT_MISMATCH 8287058"; fi; exit ${{FPRC:-0}};;
  *run_pack.py*) echo "RUN_PACK_CALLED $*" | tee -a {root}/run_pack_called; for n in ${{DIVERGE:-}}; do mkdir -p {root}/data/chang-n64-20260926/pilot-b/runs/$n; echo '{{"divergence_epoch_zero_based": '${{DEPOCH:-0}}'}}' > {root}/data/chang-n64-20260926/pilot-b/runs/$n/DIVERGED.json; done; exit ${{RPRC:-0}};;
  *) exec {REAL} "$@";;
esac
'''
    (root / 'bin/python').write_text(stub); (root / 'bin/python').chmod(0o755)
    (root / 'bin/sha256sum').write_text('#!/bin/bash\nexec shasum -a 256 "$@"\n'); (root / 'bin/sha256sum').chmod(0o755)
    (root / 'bin/nvidia-smi').write_text('#!/bin/bash\nexit 1\n'); (root / 'bin/nvidia-smi').chmod(0o755)
    return root

def run(case, job, env_extra, prep=None):
    root = setup(case)
    if prep: prep(root)
    s = script(job)
    s = s.replace('/data/chang-n64-20260926', str(root / 'data/chang-n64-20260926')).replace('/cmfp', str(root / 'cmfp')).replace('/work/fallback', str(root / 'work/fallback')).replace('/work/code/run_pack.py', 'run_pack.py')
    s = s.replace('df -h /data', 'true')
    env = {**os.environ, 'PATH': f"{root/'bin'}:{os.environ['PATH']}", 'BNJ_CAMPAIGN_DIR': str(X42 / 'campaigns/chang0926'),
           'BNJ_RUN_ROOT': str(root / 'data/chang-n64-20260926/pilot-b'), 'JOB_COMPLETION_INDEX': '0', 'NODE_NAME': 'test-node', **env_extra}
    s = s.replace('PACKS=pilot_b_', 'PACKS=pilot_b_')  # campaign-relative packs resolve under BNJ_CAMPAIGN_DIR
    out = subprocess.run(['bash', '-c', s], env=env, capture_output=True, text=True)
    called = (root / 'run_pack_called').exists()
    print(f'CASE {case} job={job} exit={out.returncode} run_pack_called={called}')
    for line in (out.stdout + out.stderr).splitlines():
        if any(k in line for k in ('FINGERPRINT', 'POD_EPOCH0', 'PACK_EPOCH0', 'ARM_STILL_LIVE', 'ARM_NO_CHECKPOINT', 'RUN_PACK_CALLED', 'FAILED', 'OK')):
            print('   ', line[:220])
    return out.returncode, called

K5 = 'pilot-b-k5-job.json'; FB = 'pilot-b-fb48-job.json'
all5 = 'chang0926-a-n64-s1 chang0926-a-n64-s2 chang0926-d-n64-s1 chang0926-cprime-n64-s1 chang0926-e1-n64-s1'
res = {}
res['fp_mismatch'] = run('fp_mismatch', K5, {'FPRC': '9'}) == (9, False)
res['fp_ok_all_div0'] = run('fp_ok_all_div0', K5, {'DIVERGE': all5}) == (10, True)
res['fp_ok_4of5_div0'] = run('fp_ok_4of5_div0', K5, {'DIVERGE': all5.rsplit(' ', 1)[0]}) == (0, True)
res['all_div_epoch3'] = run('all_div_epoch3', K5, {'DIVERGE': all5, 'DEPOCH': '3'}) == (0, True)
res['runpack_fail'] = run('runpack_fail', K5, {'RPRC': '1'}) == (1, True)
def tamper(root): (root / 'cmfp/fingerprint_check.py').write_text('x')
res['fp_sha_tamper'] = run('fp_sha_tamper', K5, {}, tamper)[1] is False
def live(root):
    d = root / 'data/chang-n64-20260926/pilot-b/runs/chang0926-a07-350-n64-s1'; d.mkdir(parents=True)
    (d / 'latest.json').write_text('{}'); (d / 'activation_widths.jsonl').write_text('')
res['fb_live'] = run('fb_live', FB, {}, live) == (1, False)
def nockpt(root):
    d = root / 'data/chang-n64-20260926/pilot-b/runs/chang0926-a07-350-n64-s1'; d.mkdir(parents=True)
    f = d / 'activation_widths.jsonl'; f.write_text(''); old = time.time() - 3600; os.utime(f, (old, old))
res['fb_nockpt'] = run('fb_nockpt', FB, {}, nockpt) == (1, False)
def stale(root):
    d = root / 'data/chang-n64-20260926/pilot-b/runs/chang0926-a07-350-n64-s1'; d.mkdir(parents=True)
    old = time.time() - 3600
    for n in ('latest.json', 'activation_widths.jsonl'):
        (d / n).write_text('{}'); os.utime(d / n, (old, old))
res['fb_ok'] = run('fb_ok', FB, {}, stale) == (0, True)
print('WRAP_TESTS', json.dumps(res))
print('WRAP_TESTS_ALL_PASS' if all(res.values()) else 'WRAP_TESTS_FAIL')
