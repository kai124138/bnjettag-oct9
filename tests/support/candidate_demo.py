#!/usr/bin/env python3
"""End-to-end candidate task on a scratch copy of the discovery campaign, with the REAL configured
runners (Codex implements, Claude reviews), the real candidate check and preparation, and a
SUBSTITUTED cluster (stub kubectl: node list, object store, call log). Nothing reaches NRP.

python3 tests/support/candidate_demo.py <scratch dir>

The candidate is a control configuration d350-c0-ctl-s1, identical to the baseline except for its
identity: a permissible change that exercises the path, not a scientific candidate.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

LAB = Path(__file__).resolve().parents[2]
CAMP = LAB / 'campaigns' / '2026-10-08-discovery-350k'
sys.path.insert(0, str(LAB / 'campaigns' / '2026-10-08-discovery-350k' / 'tools' / 'tests'))
import test_policy_d350 as tp  # noqa: E402  (stub kubectl and node list)

SPEC = """# Candidate C0: control configuration (integration demonstration)

Hypothesis: none (control). Purpose: exercise the candidate path with a permissible change.

Add a new run configuration `d350-c0-ctl-s1` that is byte-for-byte the same training setup as
`campaigns/d350/configs/d350-baseline-e-350k-s1.json`, changing only identity fields: `name` ->
`d350-c0-ctl-s1`, and any other identity keys the existing configs use for naming (look at how the
two existing configs differ: only identity keys and the reference's target). Keep every training,
quantization, data and EBOPs setting identical, the EBOPs target 350000, binary weights, N=64.

Also add, consistently with the existing two rows:
- a row for it at the END of `campaigns/d350/index.json` `runs` (same fields as the baseline row,
  its own name, file, index = its position, config_sha256 = sha256 of the new config file bytes,
  pack path);
- its pack file `campaigns/d350/packs/d350-c0-ctl-s1.json` containing [[<its index>]].

Do not change the two existing configs, their rows or packs, generate.py, any existing test, the
evaluator, data or EBOPs code. No new inference operation is added, so no certification test is
needed. Check your work by running: `python -m pytest -q tests/test_d350.py` (it must still pass).
Acceptance: the new files exist and are consistent; nothing else changed.
"""


def main():
    sb = Path(sys.argv[1]).resolve()
    if sb.exists():
        shutil.rmtree(sb)
    lab = sb / 'lab'
    (lab / 'campaigns').mkdir(parents=True)
    shutil.copytree(LAB / 'tools', lab / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(LAB / 'nrp-lab', lab / 'nrp-lab', ignore=shutil.ignore_patterns('__pycache__'))
    for c in ('2026-10-05-pilot-program', '2026-09-26-training-batch'):
        os.symlink(LAB / 'campaigns' / c, lab / 'campaigns' / c)
    c = lab / 'campaigns' / CAMP.name
    shutil.copytree(CAMP, c, symlinks=True, ignore=shutil.ignore_patterns(
        '__pycache__', 'APPROVAL.json', 'STATE.json', 'LEDGER.jsonl', 'NOTIFY.log', 'cron.log', 'scores', 'events', 'status.json'))
    stub = sb / 'stub'
    stub.mkdir()
    (stub / 'nodes.json').write_text(json.dumps(tp.nodes()))
    binp = sb / 'bin'
    binp.mkdir()
    for n in ('kubectl', 'stub_kubectl'):
        (binp / n).write_text(tp.STUB)
        (binp / n).chmod(0o755)
    os.environ.update(STUB_DIR=str(stub), PATH=f"{binp}:{os.environ['PATH']}")
    spec = importlib.util.spec_from_file_location('h_demo', lab / 'tools/harness.py')
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.init_campaign(c, 'discovery-350k-20261008')
    text = (c / 'BRIEF.md').read_text()
    pat = r'```json operations\n(.*?)\n```'
    ops = json.loads(re.search(pat, text, re.S).group(1))
    ops['kubectl'] = str(binp / 'stub_kubectl')
    (c / 'BRIEF.md').write_text(re.sub(pat, lambda _: '```json operations\n' + json.dumps(ops, indent=2) + '\n```',
                                       text, flags=re.S))
    h.write_approval(c, 'demo copy only (substituted cluster)', interactive=False)
    (c / h.INTEGRATION_PASS).write_text('{"note": "demo copy only"}\n')
    ideas = json.loads((c / 'ideas.json').read_text())
    ideas['nodes'].append({'id': 'C0', 'parent': 'R0', 'hypothesis': 'control (integration demonstration)',
                           'spec': 'plan/specs/C0.md', 'status': 'open', 'score': None, 'branch': None,
                           'notes': 'demo', 'outcome': 'not evaluated'})
    (c / 'ideas.json').write_text(json.dumps(ideas, indent=2))
    (c / 'plan' / 'specs').mkdir(parents=True, exist_ok=True)
    (c / 'plan' / 'specs' / 'C0.md').write_text(SPEC)
    with h.locked_state(c) as st:
        st['queue'].append({'id': 'implement-C0', 'task': 'implement', 'key': 'C0', 'event': 'demo',
                            'detail': {'node': 'C0', 'parent': 'R0', 'spec': 'plan/specs/C0.md'},
                            'status': 'pending', 'steps': {}, 'claimed_by': None, 'lease_expires': None})
    t0 = time.time()
    r1 = h.run_task(c, 'claude-code', crash_after='review')
    print(f'run 1 (interrupted after review): {r1}  {time.time() - t0:.0f} s')
    st = h.load_state(c)
    print('steps after run 1:', sorted(st['queue'][0]['steps']), 'agent calls:', st['counters']['agent_invocations'])
    later = h.now_utc() + __import__('datetime').timedelta(seconds=h.load_brief(c)['lease_s'] + 1)
    t0 = time.time()
    r2 = h.run_task(c, 'codex', now=later)
    print(f'run 2 (resumed by another holder): {r2}  {time.time() - t0:.0f} s')
    st = h.load_state(c)
    q = st['queue'][0]
    print('final status:', q['status'], '| agent calls:', st['counters']['agent_invocations'])
    print(json.dumps({k: v for k, v in q['steps'].items() if k in ('branch', 'implement', 'review', 'check',
                                                                    'commit', 'prepare', 'submit')}, indent=1)[:3000])
    calls = [json.loads(l) for l in (stub / 'calls.log').read_text().splitlines()] if (stub / 'calls.log').exists() else []
    print('job creates:', [x[2].split('/')[-2] for x in calls if x[0] == 'create' and x[2].endswith('job.json')])
    r3 = h.run_task(c, 'claude-code', now=later + __import__('datetime').timedelta(hours=3))
    log = stub / 'calls.log'
    n = sum(1 for x in [json.loads(l) for l in log.read_text().splitlines()] if x[0] == 'create'
            and x[2].endswith('job.json')) if log.exists() else 0
    print('replay:', r3, '| job creates now:', n)
    print('notifications:\n' + (c / 'NOTIFY.log').read_text())
    print('evidence:', c / 'evidence' / 'implement-C0')


if __name__ == '__main__':
    main()
