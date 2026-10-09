#!/usr/bin/env python3
"""Run the local recovery sequence once, in a fresh sandbox, with a chosen agent runner.

    python3 tests/support/recovery_demo.py <sandbox dir> --runner simulated|claude|codex
        [--resume-with simulated|claude|codex]

`--resume-with` interrupts the first runner's task after the agent step and lets the second
continue from the shared state. Uses the local kubectl substitute; a PATH shim makes any bare
`kubectl` fail, so nothing reaches a cluster. The real runners spend model tokens.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import timedelta

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / 'tests/support'
spec = importlib.util.spec_from_file_location('harness', ROOT / 'tools/harness.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sandbox')
    ap.add_argument('--runner', default='simulated', choices=['simulated', 'claude', 'codex'])
    ap.add_argument('--resume-with', choices=['simulated', 'claude', 'codex'])
    a = ap.parse_args()
    sb = Path(a.sandbox).resolve()
    if sb.exists():
        shutil.rmtree(sb)
    cdir, kube, shim = sb / 'campaign', sb / 'kube', sb / 'bin'
    for d in (kube, shim):
        d.mkdir(parents=True)
    (shim / 'kubectl').write_text('#!/bin/sh\necho "no cluster in demo" >&2\nexit 1\n')
    (shim / 'kubectl').chmod(0o755)
    os.environ.update(PATH=f"{shim}:{os.environ['PATH']}", LOCAL_KUBE_DIR=str(kube),
                      RUN_HANDOFF=str(ROOT / 'tools/run_handoff.py'),
                      HANDOFF_ROOT=str(cdir / 'handoffs'))
    h.init_campaign(cdir, 'harness-demo')
    shutil.copytree(SUPPORT / 'demo_workspace', cdir / 'workspace')
    text = (cdir / h.BRIEF).read_text()
    block = json.loads(re.search(r'```json\n(.*?)\n```', text, re.S).group(1))
    block.update(gpu_h_max=1.0, kubectl=str(SUPPORT / 'local_kubectl.py'),
                 selector='campaign=harness-demo', approval_ref='HARNESS-DEMO',
                 workspace='workspace', repair_paths=['code/config.json'], runner=a.runner,
                 runner_command=[sys.executable, str(SUPPORT / 'sim_agent.py')],
                 repair_test_command=[sys.executable, 'tools/check.py'],
                 prepare_command=[sys.executable, 'tools/prepare.py', '{attempt}'],
                 evaluate_command=[sys.executable, 'tools/evaluate.py', '{job}'],
                 codex_bin=os.environ.get('CODEX_BIN', 'codex'),
                 codex_model=os.environ.get('CODEX_MODEL'))
    (cdir / h.BRIEF).write_text(re.sub(r'```json\n.*?\n```', lambda _: '```json\n' +
                                       json.dumps(block, indent=2) + '\n```', text, flags=re.S))
    h.write_approval(cdir, 'Kai (demo, non-interactive)', interactive=False)
    first = subprocess.run([sys.executable, 'tools/prepare.py', '0'], cwd=cdir / 'workspace',
                           capture_output=True, text=True, check=True).stdout.strip()
    log = [('submit attempt 0', h.submit(cdir, first))]
    log.append(('watch', h.watch_once(cdir)))
    if a.resume_with:
        log.append((f'{a.runner}: run until agent step', h.run_task(cdir, a.runner,
                                                                    crash_after='agent')))
        later = h.now_utc() + timedelta(seconds=h.load_brief(cdir)['lease_s'] + 1)
        log.append((f'{a.resume_with}: resume', h.run_task(cdir, a.resume_with,
                                                           runner=a.resume_with, now=later)))
    else:
        log.append((f'{a.runner}: repair task', h.run_task(cdir, a.runner)))
    log.append(('watch', h.watch_once(cdir)))
    log.append(('evaluate task', h.run_task(cdir, a.runner, runner=a.runner)))
    log.append(('replay watch', h.watch_once(cdir)))
    log.append(('replay step', h.run_task(cdir, 'replay', runner=a.runner)))
    for name, result in log:
        print(f'{name}: {json.dumps(result)}')
    st = h.load_state(cdir)
    print('queue:', [(q['id'], q['status'], sorted(q['steps'])) for q in st['queue']])
    print('agent invocations:', st['counters']['agent_invocations'])
    print('job creates:', sum(1 for l in (kube / 'calls.log').read_text().splitlines()
                              if json.loads(l)[:1] == ['create'] and 'job.json' in l))
    for t in (cdir / h.EVIDENCE).glob('*/agent-output.txt'):
        print(f'--- {t.parent.name} agent output (last 1500 chars) ---')
        print(t.read_text()[-1500:])
    print('--- ledger ---')
    print((cdir / h.LEDGER).read_text())
    print('--- notifications ---')
    print((cdir / h.NOTIFY).read_text())


if __name__ == '__main__':
    main()
