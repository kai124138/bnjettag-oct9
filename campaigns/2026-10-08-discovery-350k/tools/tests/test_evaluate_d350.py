"""Evaluate glue against a stubbed kubectl, on a throwaway copy of this campaign.

python3 -m unittest campaigns/2026-10-08-discovery-350k/tools/tests/test_evaluate_d350.py

The copy links the pilot and training-batch campaigns and nrp-lab read-only (the prepare tools
check pinned files there) and replaces kubectl: object creation goes to a stub that records calls
and serves scripted Job states and logs; a failing `kubectl` shim on PATH keeps lint offline.
Nothing reaches a cluster. Score Jobs never run here; the stub supplies their last log line.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

CAMP = Path(__file__).resolve().parents[2]
LAB = CAMP.parents[1]
STUB = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
D = Path(os.environ['STUB_DIR'])
args = [a for a in sys.argv[1:] if not a.startswith('--request-timeout')]
if '-n' in args:
    i = args.index('-n'); del args[i:i + 2]
with open(D / 'calls.log', 'a') as f:
    f.write(json.dumps(args) + '\\n')
if args[0] == 'create':
    sys.exit(0)
if args[0] == 'get' and '--ignore-not-found' in args:
    sys.exit(0)
if args[0] == 'get' and args[1] == 'job':
    st = D / (args[2] + '.state')
    cond = [{'type': st.read_text().strip(), 'status': 'True'}] if st.exists() else []
    print(json.dumps({'status': {'conditions': cond}}))
    sys.exit(0)
if args[0] == 'logs':
    p = D / (args[1].split('/', 1)[1] + '.log')
    print(p.read_text() if p.exists() else '')
    sys.exit(0)
sys.exit(2)
'''


class EvaluateGlue(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        lab = self.tmp / 'lab'
        (lab / 'campaigns').mkdir(parents=True)
        shutil.copytree(LAB / 'tools', lab / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        os.symlink(LAB / 'nrp-lab', lab / 'nrp-lab')
        for c in ('2026-10-05-pilot-program', '2026-09-26-training-batch'):
            os.symlink(LAB / 'campaigns' / c, lab / 'campaigns' / c)
        self.c = lab / 'campaigns' / CAMP.name
        shutil.copytree(CAMP, self.c, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__', 'APPROVAL.json', 'STATE.json', 'LEDGER.jsonl', 'NOTIFY.log', 'cron.log', '.state.lock', '.tick.lock', 'scores', 'events', 'status.json'))
        self.stub_dir = self.tmp / 'stub'
        self.stub_dir.mkdir()
        bin_ = self.tmp / 'bin'
        bin_.mkdir()
        (bin_ / 'stub_kubectl').write_text(STUB)
        (bin_ / 'stub_kubectl').chmod(0o755)
        (bin_ / 'kubectl').write_text('#!/bin/sh\nexit 1\n')
        (bin_ / 'kubectl').chmod(0o755)
        self.env = dict(os.environ, STUB_DIR=str(self.stub_dir), PATH=f"{bin_}:{os.environ['PATH']}")
        spec = importlib.util.spec_from_file_location('h', lab / 'tools/harness.py')
        h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(h)
        h.init_campaign(self.c, 'discovery-350k-20261008')         # fresh run state, not the live one
        text = (self.c / 'BRIEF.md').read_text()
        ops = json.loads(re.search(r'```json operations\n(.*?)\n```', text, re.S).group(1))
        ops['kubectl'] = str(bin_ / 'stub_kubectl')
        (self.c / 'BRIEF.md').write_text(re.sub(r'```json operations\n.*?\n```', lambda _: '```json operations\n' +
                                                json.dumps(ops, indent=2) + '\n```', text, flags=re.S))
        h.write_approval(self.c, 'test only', interactive=False)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def evaluate(self, job):
        return subprocess.run([sys.executable, str(self.c / 'tools/evaluate_d350.py'), job],
                              capture_output=True, text=True, env=self.env)

    def score_job(self, run, k=-1):
        return json.loads((self.c / 'evidence/scores' / f'{run}.json').read_text())['attempts'][k]

    def finish(self, score_job, state, last_line):
        (self.stub_dir / f'{score_job}.state').write_text(state)
        (self.stub_dir / f'{score_job}.log').write_text(f'setup\n{last_line}\n')

    def test_scientific_invalid_from_a_failed_score_job(self):
        job, run = 'kai-d350-baseline-e-350k-s1-a1', 'baseline-e-350k-s1-a1'
        self.assertEqual(self.evaluate(job).stdout.strip(), 'PENDING')
        self.finish(self.score_job(run)['score_job'], 'Failed',
                    'INVALID[scientific]: no feasible checkpoint in epochs < 1000')
        r = self.evaluate(job)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(r.stdout.strip(), 'INVALID[scientific]: no feasible checkpoint in epochs < 1000')

    def test_evaluator_failure_then_valid_second_attempt(self):
        job, run = 'kai-d350-reference-e-5m-s1-a1', 'reference-e-5m-s1-a1'
        self.evaluate(job)
        first = self.score_job(run)
        self.finish(first['score_job'], 'Failed', 'INVALID[evaluator]: internal error: transient')
        self.assertEqual(self.evaluate(job).stdout.strip(), 'PENDING')
        second = self.score_job(run)
        self.assertEqual(second['k'], 2)
        cmd1 = json.dumps(json.loads((Path(first['handoff']) / 'job.json').read_text()))
        cmd2 = json.dumps(json.loads((Path(second['handoff']) / 'job.json').read_text()))
        self.assertNotIn('--score-attempt', cmd1)          # attempt-1 handoffs unchanged
        self.assertIn('--score-attempt 2', cmd2)           # B2: attempt 2 writes score-s2.json
        self.finish(second['score_job'], 'Complete',
                    'SCORE_JSON_BEGIN\n{"primary": 0.4012, "secondary": {"feasible_acc_epoch_500": 0.39}}\n'
                    'SCORE_JSON_END\n0.4012')
        r = self.evaluate(job)
        self.assertEqual(r.returncode, 0)
        metrics = json.loads(Path(r.stdout.strip()).read_text())
        self.assertEqual((metrics['value'], metrics['score_attempt'], metrics['split'], metrics['n']),
                         (0.4012, 2, 'validation', 62000))
        sec = json.loads(Path(metrics['result_file']).read_text())   # secondary measurements kept
        self.assertEqual(sec['secondary']['feasible_acc_epoch_500'], 0.39)

    def test_diverged_is_not_retried(self):
        job, run = 'kai-d350-baseline-e-350k-s1-a1', 'baseline-e-350k-s1-a1'
        self.evaluate(job)
        self.finish(self.score_job(run)['score_job'], 'Failed', 'INVALID[diverged]: DIVERGED.json present')
        r = self.evaluate(job)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(len(json.loads((self.c / 'evidence/scores' / f'{run}.json').read_text())['attempts']), 1)

    def test_killed_score_job_retried_once_then_evaluation_failure(self):
        job, run = 'kai-d350-baseline-e-350k-s1-a1', 'baseline-e-350k-s1-a1'
        self.evaluate(job)
        self.finish(self.score_job(run)['score_job'], 'Failed', 'pip install ...')
        self.assertEqual(self.evaluate(job).stdout.strip(), 'PENDING')
        self.finish(self.score_job(run)['score_job'], 'Failed', 'pip install ...')
        r = self.evaluate(job)
        self.assertEqual(r.returncode, 2)          # an evaluation failure, not a result


if __name__ == '__main__':
    unittest.main()
