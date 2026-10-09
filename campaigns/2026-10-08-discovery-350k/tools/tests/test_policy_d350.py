"""Campaign policy through the real preparation, lint, run_handoff and harness code, on a
throwaway copy of this campaign with SUBSTITUTED cluster operations.

python3 -m unittest campaigns/2026-10-08-discovery-350k/tools/tests/test_policy_d350.py

The substitute kubectl (also first on PATH, so nrp_doctor's node lookup uses it) stores created
objects, answers lookups from them, serves a constructed node list of RTX 3090 nodes and
constructed Job/Pod records, and logs every call. Nothing reaches a cluster. Passing these tests
does not show that the live cluster path works.
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
WAVE1 = {'kai-d350-baseline-e-350k-s1-a1': 'handoffs/rh-adce3a6b9ad29ca7ab6f1f81',
         'kai-d350-reference-e-5m-s1-a1': 'handoffs/rh-e066021d9a5e350f0bc0ffe4'}
STUB = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
D = Path(os.environ['STUB_DIR'])
args = [a for a in sys.argv[1:] if not a.startswith('--request-timeout')]
if '-n' in args:
    i = args.index('-n'); del args[i:i + 2]
with open(D / 'calls.log', 'a') as f:
    f.write(json.dumps(args) + '\n')
objs = D / 'objects'
objs.mkdir(exist_ok=True)
if args and args[0] == 'get' and args[1] == 'nodes':
    if (D / 'no_nodes').exists():
        print('error: You must be logged in to the server (Unauthorized)', file=sys.stderr); sys.exit(1)
    print((D / 'nodes.json').read_text()); sys.exit(0)
if args[0] == 'create' and args[1] == '-f':
    o = json.loads(Path(args[2]).read_text())
    p = objs / f"{o['kind']}-{o['metadata']['name']}.json"
    if p.exists():
        print('AlreadyExists', file=sys.stderr); sys.exit(1)
    p.write_text(json.dumps(o)); sys.exit(0)
if args[0] == 'get' and '--ignore-not-found' in args:
    p = objs / f'{args[1]}-{args[2]}.json'
    if p.exists():
        print(p.read_text())
    sys.exit(0)
if args[0] == 'get' and args[1] in ('jobs', 'pods') and '-l' in args:
    f = D / f'{args[1]}.json'
    print(f.read_text() if f.exists() else '{"items": []}'); sys.exit(0)
if args[0] == 'logs':
    print('constructed log'); sys.exit(0)
print('unsupported ' + ' '.join(args), file=sys.stderr); sys.exit(2)
'''


def nodes(n=40):
    return {'items': [{'metadata': {'name': f'node{i}.example', 'labels': {
        'nvidia.com/gpu.product': 'NVIDIA-GeForce-RTX-3090', 'kubernetes.io/hostname': f'node{i}.example'}},
        'spec': {}, 'status': {'allocatable': {'nvidia.com/gpu': '4'}, 'conditions': [{'type': 'Ready', 'status': 'True'}]}}
        for i in range(n)]}


def tree_state(root):
    """File hashes of the real campaign (code/.git excluded) plus its code/ branches and HEAD."""
    import hashlib
    live = {'STATE.json', 'LEDGER.jsonl', 'NOTIFY.log', 'cron.log', '.state.lock', '.tick.lock'}
    files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts
             and p.name not in live and 'scores' not in p.relative_to(root).parts}   # written by the live scheduler
    git = subprocess.run(['git', '-C', str(root / 'code'), 'for-each-ref', '--format=%(refname) %(objectname)'],
                         capture_output=True, text=True).stdout
    head = subprocess.run(['git', '-C', str(root / 'code'), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout
    return files, git, head


class Policy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_before = tree_state(CAMP)

    @classmethod
    def tearDownClass(cls):
        # Regression check (2026-10-08): these tests must write only inside their scratch copies.
        after = tree_state(CAMP)
        changed = sorted(k for k in set(cls.real_before[0]) | set(after[0]) if cls.real_before[0].get(k) != after[0].get(k))
        assert not changed and cls.real_before[1:] == after[1:], f'real campaign changed by tests: {changed[:10]}'

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        lab = self.tmp / 'lab'
        (lab / 'campaigns').mkdir(parents=True)
        shutil.copytree(LAB / 'tools', lab / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(LAB / 'nrp-lab', lab / 'nrp-lab', ignore=shutil.ignore_patterns('__pycache__'))
        for c in ('2026-10-05-pilot-program', '2026-09-26-training-batch'):
            os.symlink(LAB / 'campaigns' / c, lab / 'campaigns' / c)
        self.c = lab / 'campaigns' / CAMP.name
        shutil.copytree(CAMP, self.c, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__', 'APPROVAL.json', 'STATE.json', 'LEDGER.jsonl', 'NOTIFY.log', 'cron.log', '.state.lock', '.tick.lock', 'scores', 'events', 'status.json'))
        self.d = self.tmp / 'stub'
        self.d.mkdir()
        (self.d / 'nodes.json').write_text(json.dumps(nodes()))
        bin_ = self.tmp / 'bin'
        bin_.mkdir()
        for name in ('kubectl', 'stub_kubectl'):
            (bin_ / name).write_text(STUB)
            (bin_ / name).chmod(0o755)
        self.saved = dict(os.environ)
        os.environ.update(STUB_DIR=str(self.d), PATH=f"{bin_}:{os.environ['PATH']}")
        spec = importlib.util.spec_from_file_location('h_policy', lab / 'tools/harness.py')
        self.h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.h)
        self.h.init_campaign(self.c, 'discovery-350k-20261008')      # fresh run state, not the live one
        with self.h.locked_state(self.c) as st:
            st['counters']['attempt'] = max(json.loads(f.read_text()).get('attempt', 0)    # as live: above
                                            for f in (self.c / 'attempts').glob('*-a*.json')   # existing attempts
                                            if 'runtime-justification' not in f.name)
        self.edit('operations', kubectl=str(bin_ / 'stub_kubectl'))
        self.h.write_approval(self.c, 'test only', interactive=False)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)
        shutil.rmtree(self.tmp)

    def edit(self, block, **kv):
        text = (self.c / 'BRIEF.md').read_text()
        pat = rf'```json {block}\n(.*?)\n```'
        data = json.loads(re.search(pat, text, re.S).group(1))
        data.update(kv)
        (self.c / 'BRIEF.md').write_text(re.sub(pat, lambda _: f'```json {block}\n' + json.dumps(data, indent=2) + '\n```',
                                                text, flags=re.S))

    def calls(self):
        p = self.d / 'calls.log'
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    def creates(self):
        return [c for c in self.calls() if c[0] == 'create' and c[2].endswith('job.json')]

    def submit_wave1(self):
        return [self.h.submit(self.c, self.c / hd, stage='wave1') for hd in WAVE1.values()]

    def assert_no_destructive_calls(self):
        verbs = {c[0] for c in self.calls()}
        self.assertFalse(verbs & {'delete', 'patch', 'scale', 'replace', 'apply', 'label', 'annotate', 'drain'}, verbs)

    # --- normal path and advisory conditions

    def test_normal_wave1_submission_passes(self):
        out = self.submit_wave1()
        self.assertEqual([o['status'] for o in out], ['submitted', 'submitted'])
        self.assertEqual(len(self.creates()), 2)
        st = self.h.load_state(self.c)['resources']['jobs']
        for job in WAVE1:
            self.assertEqual(st[job]['bound'], 26.244444)
            self.assertEqual(st[job]['authority_sha256'], self.h.brief_sha(self.c))
            self.assertIn('operations_sha256', st[job])
        self.assertEqual([o['status'] for o in self.submit_wave1()], ['already-submitted'] * 2)
        self.assertEqual(len(self.creates()), 2)
        self.assert_no_destructive_calls()

    def test_lint_warning_does_not_block(self):
        # The wave-1 Jobs lint with WARN (backoffLimitPerIndex=1): advisory, submission proceeds.
        self.assertEqual(self.h.submit(self.c, self.c / WAVE1['kai-d350-baseline-e-350k-s1-a1'], stage='wave1')['status'],
                         'submitted')

    def test_missing_cluster_information_defers_then_succeeds(self):
        (self.d / 'no_nodes').write_text('')
        r = self.h.submit(self.c, self.c / WAVE1['kai-d350-baseline-e-350k-s1-a1'], stage='wave1')
        self.assertEqual(r['status'], 'deferred')
        self.assertEqual(self.creates(), [])
        self.assertNotIn('kai-d350-baseline-e-350k-s1-a1', self.h.load_state(self.c)['resources']['jobs'])
        (self.d / 'no_nodes').unlink()
        r = self.h.submit(self.c, self.c / WAVE1['kai-d350-baseline-e-350k-s1-a1'], stage='wave1')
        self.assertEqual(r['status'], 'submitted')
        self.assertEqual(len(self.creates()), 1)

    # --- configuration edits

    def test_operations_edit_needs_no_reapproval(self):
        self.edit('operations', lease_s=1800, agent_invocations_warn=10)
        self.assertEqual(self.h.validate_brief(self.c), [])
        self.assertIsNotNone(self.h.current_approval(self.c))
        self.assertEqual(self.submit_wave1()[0]['status'], 'submitted')

    def test_authority_edit_voids_the_approval(self):
        self.edit('authority', gpu_h_max=300)
        with self.assertRaises(self.h.GateError):
            self.submit_wave1()
        self.assertEqual(self.creates(), [])

    def test_out_of_range_or_misspelled_settings_block_submission(self):
        for kv in ({'repair_attempts_per_class': 9}, {'candidate_runtime_factor': 3.5}, {'lease_seconds': 60}):
            with self.subTest(kv=kv):
                saved = (self.c / 'BRIEF.md').read_text()
                self.edit('operations', **kv)
                self.assertTrue(self.h.validate_brief(self.c))
                with self.assertRaises(self.h.GateError):
                    self.submit_wave1()
                (self.c / 'BRIEF.md').write_text(saved)
        self.assertEqual(self.creates(), [])

    # --- slower workloads get their configured allowance

    def test_runtime_factor_allowance_from_configuration(self):
        def prep(factor):
            return subprocess.run([sys.executable, str(self.c / 'tools/prepare_attempt.py'), 'baseline-e-350k-s1', '7',
                                   '--stage', 'search', '--stop-epoch', '1000', '--runtime-factor', str(factor)],
                                  capture_output=True, text=True)
        r = prep(1.4)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        job = json.loads((Path(r.stdout.strip().splitlines()[-1]) / 'job.json').read_text())
        self.assertEqual(job['spec']['template']['spec']['activeDeadlineSeconds'], 65800)   # 47 x 1000 x 1.4
        self.assertEqual(job['spec']['activeDeadlineSeconds'], 131600)                      # 2 attempts
        self.assertNotEqual(prep(1.6).returncode, 0)        # > runtime_factor_notify 1.5 without evidence
        ev = self.tmp / 'timing.json'
        ev.write_text('{"s_per_epoch_measured": 62}')
        r = subprocess.run([sys.executable, str(self.c / 'tools/prepare_attempt.py'), 'baseline-e-350k-s1', '9',
                            '--stage', 'search', '--stop-epoch', '1000', '--runtime-factor', '1.6',
                            '--runtime-justification', 'measured 62 s/epoch with the added teacher pass',
                            '--timing-evidence', str(ev)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        job = json.loads((Path(r.stdout.strip().splitlines()[-1]) / 'job.json').read_text())
        self.assertEqual(job['spec']['template']['spec']['activeDeadlineSeconds'], 75200)
        self.assertIn('runtime factor 1.6 above 1.5', (self.c / 'NOTIFY.log').read_text())
        self.assertTrue((self.c / 'attempts' / 'baseline-e-350k-s1-a9.runtime-justification.json').is_file())
        self.assertNotEqual(prep(3.1).returncode, 0)        # > runtime_factor_max 3.0

    def test_deadline_allowance_is_a_configuration_edit(self):
        self.edit('operations', deadline_seconds_per_epoch=50)
        self.assertIsNotNone(self.h.current_approval(self.c))                # no re-approval needed
        r = subprocess.run([sys.executable, str(self.c / 'tools/prepare_attempt.py'), 'baseline-e-350k-s1', '8',
                            '--stage', 'search', '--stop-epoch', '1000'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        job = json.loads((Path(r.stdout.strip().splitlines()[-1]) / 'job.json').read_text())
        self.assertEqual(job['spec']['template']['spec']['activeDeadlineSeconds'], 50000)
        # an already prepared wave-1 handoff keeps the deadline it was built with
        old = json.loads((self.c / WAVE1['kai-d350-baseline-e-350k-s1-a1'] / 'job.json').read_text())
        self.assertEqual(old['spec']['template']['spec']['activeDeadlineSeconds'], 47000)

    # --- recovery and monitoring problems

    def failed_records(self, job, disrupted):
        pod_conditions = [{'type': 'DisruptionTarget', 'status': 'True'}] if disrupted else []
        (self.d / 'jobs.json').write_text(json.dumps({'items': [{
            'kind': 'Job', 'metadata': {'name': job, 'labels': {'campaign': 'discovery-350k-20261008',
                                                                'bnjettag.io/role': 'train', 'bnjettag.io/stage': 'wave1'}},
            'spec': {'completionMode': 'Indexed', 'completions': 1},
            'status': {'failedIndexes': '0', 'conditions': [{'type': 'Failed', 'status': 'True'}]}}]}))
        (self.d / 'pods.json').write_text(json.dumps({'items': [{
            'kind': 'Pod', 'metadata': {'name': job + '-0-x', 'labels': {'batch.kubernetes.io/job-name': job,
                                                                         'batch.kubernetes.io/job-completion-index': '0'}},
            'spec': {'containers': [{'resources': {'limits': {'nvidia.com/gpu': '1'}}}]},
            'status': {'phase': 'Failed', 'conditions': pod_conditions, 'containerStatuses': [{'state': {'terminated': {
                'exitCode': 137, 'startedAt': '2026-10-09T00:00:00Z', 'finishedAt': '2026-10-09T02:00:00Z'}}}]}}]}))

    def test_infrastructure_failure_resumes_once_without_duplicates(self):
        self.submit_wave1()
        job = 'kai-d350-baseline-e-350k-s1-a1'
        self.failed_records(job, disrupted=True)
        r1 = self.h.tick(self.c, 'cron')
        self.assertEqual(r1, 'done', (self.c / 'NOTIFY.log').read_text()[-800:])
        new = [c for c in self.creates() if 'a2' in c[2] or len(self.creates()) == 3]
        self.assertEqual(len(self.creates()), 3)                 # 2 wave-1 + 1 relaunch
        names = sorted(p.name for p in (self.c / 'attempts').glob('baseline-*'))
        att = json.loads((self.c / 'attempts' / names[-1]).read_text()) if len(names) > 1 else self.fail(names)
        self.assertEqual(att['resume_from'], 'baseline-e-350k-s1-a1')
        for _ in range(3):                                       # replay: no second relaunch
            self.h.tick(self.c, 'cron')
        self.assertEqual(len(self.creates()), 3)
        self.assertTrue(self.h.load_state(self.c)['resources']['jobs'][job].get('superseded_by'))
        self.assert_no_destructive_calls()

    def test_monitoring_failure_issues_no_commands_against_jobs(self):
        self.submit_wave1()
        bad = self.tmp / 'bin' / 'stub_kubectl'
        self.edit('operations', kubectl=str(self.tmp / 'missing_kubectl'))
        self.assertTrue(self.h.tick(self.c, 'cron').startswith('monitor-error'))
        self.edit('operations', kubectl=str(bad))
        self.assert_no_destructive_calls()

    def test_submission_stop_keeps_monitoring_and_evaluation(self):
        self.submit_wave1()
        with self.h.locked_state(self.c) as st:
            st['stopped'] = True
            st['queue'].append({'id': 'evaluate-x', 'task': 'evaluate', 'key': 'kai-x#0', 'event': 'x', 'detail': {},
                                'status': 'pending', 'steps': {}, 'claimed_by': None, 'lease_expires': None})
            st['queue'].append({'id': 'repair-y', 'task': 'repair', 'key': 'kai-y#0', 'event': 'y', 'detail': {},
                                'status': 'pending', 'steps': {}, 'claimed_by': None, 'lease_expires': None})
        claimed = self.h.claim_task(self.c, 'cron')
        self.assertEqual(claimed['task'], 'evaluate')            # repair held back, evaluation runs
        self.assertIsNone(self.h.claim_task(self.c, 'cron'))
        self.assertEqual(self.h.tick(self.c, 'cron')[:4] in ('idle', 'done', 'pend', 'fail', 'task'), True)
        self.assert_no_destructive_calls()


if __name__ == '__main__':
    unittest.main()
