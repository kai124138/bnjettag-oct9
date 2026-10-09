import copy
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from datetime import timedelta

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harness', ROOT / 'tools/harness.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
FIX = ROOT / 'tests/fixtures/harness'
SUPPORT = ROOT / 'tests/support'


def captured(name):
    doc = json.loads((FIX / name).read_text())
    assert doc['provenance']['kind'] == 'captured'
    return doc


def set_brief(cdir, **limits):
    text = (cdir / h.BRIEF).read_text()
    block = json.loads(re.search(r'```json\n(.*?)\n```', text, re.S).group(1))
    block.update(limits)
    text = re.sub(r'```json\n.*?\n```', lambda _: '```json\n' + json.dumps(block, indent=2) + '\n```',
                  text, flags=re.S)
    (cdir / h.BRIEF).write_text(text)
    return h.load_brief(cdir)


def _bump(cdir, n):
    for _ in range(n):
        with h.locked_state(cdir) as st:
            st['counters']['attempt'] += 1


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp.name)
        self.cdir = self.tmp / 'campaign'
        h.init_campaign(self.cdir, 'synthetic-0001')

    def tearDown(self):
        self.temp.cleanup()


class CapturedRecords(Base):
    """Fixtures are sanitized copies of saved kubectl records (see their provenance field)."""

    def test_engram_indexed_job_with_policy(self):
        obs = h.observe(captured('captured-engram-failedindexes.json'))
        st = {k.split('#')[1]: v['status'] for k, v in obs.items()}
        self.assertEqual(st, {'0': 'failed', '1': 'failed', '2': 'succeeded', '3': 'succeeded'})
        self.assertIsNone(obs['kai-engram-screen-e100-a10364ed#0']['arm'])   # no arm annotation
        idx3 = obs['kai-engram-screen-e100-a10364ed#3']
        self.assertEqual(sum(a['phase'] == 'Failed' for a in idx3['attempts']), 3)
        self.assertEqual(h.classify(obs['kai-engram-screen-e100-a10364ed#1'])[0], 'deterministic')
        brief = set_brief(self.cdir, gpu_h_max=100.0)
        acts, state = h.decide(brief, h.load_state(self.cdir), obs)
        tasks = sorted((q['key'].split('#')[1], q['task']) for q in state['queue'])
        # Index 3 was retried three times by Kubernetes and then succeeded: no harness retry.
        self.assertEqual(tasks, [('0', 'repair'), ('1', 'repair'), ('2', 'evaluate'), ('3', 'evaluate')])

    def test_missing_pod_records_stay_unknown(self):
        obs = h.observe(captured('captured-batch0917-maxfailedindexes.json'))
        for o in obs.values():
            self.assertEqual(o['pod_records'], 0)
            self.assertEqual(h.classify(o), ('unknown', 'no pod records for this index'))
        brief = set_brief(self.cdir, gpu_h_max=100.0)
        _, state = h.decide(brief, h.load_state(self.cdir), obs)
        j = state['resources']['jobs']['kai-batch0917-screen-e100']
        self.assertIsNone(j['measured'])
        self.assertFalse(j['final'])
        self.assertEqual({q['task'] for q in state['queue']}, {'investigate'})

    def test_single_attempt_exit_is_not_called_deterministic(self):
        obs = h.observe(captured('captured-confirm-replay-backoff.json'))
        (o,) = obs.values()
        self.assertEqual(o['status'], 'failed')
        self.assertEqual(h.classify(o), ('unknown', 'single failure with exit 1'))

    def test_completed_job_measures_gpu_time_and_replay_is_idempotent(self):
        doc = captured('captured-batch0918-complete.json')
        brief = set_brief(self.cdir, gpu_h_max=1000.0)
        acts, state = h.decide(brief, h.load_state(self.cdir), h.observe(doc))
        self.assertEqual(len(state['queue']), 15)
        j = state['resources']['jobs']['kai-batch0918-screen-e400']
        self.assertTrue(j['final'])
        self.assertGreater(j['measured'], 0)
        acts2, state2 = h.decide(brief, state, h.observe(doc))
        self.assertEqual([a for a in acts2 if a['kind'] == 'task'], [])
        self.assertEqual(len(state2['queue']), 15)

    def test_real_pilot_manifest_bound(self):
        job = json.loads((ROOT / 'campaigns/2026-10-05-pilot-program/manifests-98dd28-r3/'
                          'r1-h1-e-350k-noc-s2-job.json').read_text())
        bound, note = h.gpu_bound(job)
        self.assertEqual(bound, 10.0)        # 1 GPU x 2 attempts x 18,000 s
        self.assertIn('ignored disruptions', note)


class ConstructedRecords(Base):
    """Constructed from captured records by editing fields; labelled as such."""

    def test_kubernetes_still_retrying_means_no_action(self):
        doc = copy.deepcopy(captured('captured-engram-failedindexes.json'))
        job = next(i for i in doc['items'] if i['kind'] == 'Job')
        job['status'].update(failedIndexes='', conditions=[], active=1)
        doc['items'] = [i for i in doc['items'] if i['kind'] == 'Job' or
                        i['metadata']['labels'].get('batch.kubernetes.io/job-completion-index') == '1']
        obs = h.observe(doc)
        self.assertEqual(obs['kai-engram-screen-e100-a10364ed#1']['status'], 'kubernetes_retrying')
        brief = set_brief(self.cdir, gpu_h_max=100.0)
        acts, state = h.decide(brief, h.load_state(self.cdir), obs)
        self.assertNotIn('kai-engram-screen-e100-a10364ed#1', [q['key'] for q in state['queue']])

    def test_disruption_relaunches_twice_then_investigates(self):
        base = captured('captured-confirm-replay-backoff.json')
        brief = set_brief(self.cdir, gpu_h_max=100.0)
        state = h.load_state(self.cdir)
        tasks = []
        for n in range(3):                       # three successive relaunched Jobs of one arm
            doc = copy.deepcopy(base)
            job = next(i for i in doc['items'] if i['kind'] == 'Job')
            pod = next(i for i in doc['items'] if i['kind'] == 'Pod')
            name = job['metadata']['name'] + f'-a{n}'
            job['metadata']['name'] = name
            job['metadata']['annotations'] = {'bnjettag.io/arm': f'arm-x a{n} test'}
            pod['metadata']['labels'] = {'batch.kubernetes.io/job-name': name, 'job-name': name}
            pod['status']['conditions'].append({'type': 'DisruptionTarget', 'status': 'True'})
            _, state = h.decide(brief, state, h.observe(doc))
            tasks = [q['task'] for q in state['queue']]
        self.assertEqual(tasks, ['relaunch', 'relaunch', 'investigate'])


class Gates(Base):
    def test_approval_is_bound_to_the_brief(self):
        set_brief(self.cdir, gpu_h_max=5.0)
        with self.assertRaises(h.GateError):
            h.require_approval(self.cdir)
        h.write_approval(self.cdir, 'Kai', interactive=False)
        h.require_approval(self.cdir)
        set_brief(self.cdir, gpu_h_max=50.0)          # agent edits the proposal
        with self.assertRaises(h.GateError):
            h.require_approval(self.cdir)

    def test_cli_approval_needs_a_terminal(self):
        with self.assertRaises(h.GateError):
            h.write_approval(self.cdir, 'Kai')          # unittest stdin is not a terminal here
        self.assertFalse((self.cdir / h.APPROVAL).exists())

    def test_reserved_actions(self):
        h.write_approval(self.cdir, 'Kai', interactive=False,
                         actions=[{'id': 'claim-1', 'kind': 'publication_claim'}])
        self.assertTrue(h.authorize(self.cdir, 'publication_claim', 'claim-1'))
        for kind in ('public_release', 'external_message'):
            with self.assertRaises(h.GateError):
                h.authorize(self.cdir, kind, 'claim-1')
        self.assertTrue(h.authorize(self.cdir, 'internal_record'))

    def test_findings(self):
        h.resolve_finding(self.cdir, {'id': 'C3', 'kind': 'review'}, 'w100 fixed pre-data', 'arbiter')
        for kind in ('numerical', 'authorization'):
            with self.assertRaises(h.GateError):
                h.resolve_finding(self.cdir, {'id': 'X', 'kind': kind}, 'any text', 'arbiter')
        with self.assertRaises(h.GateError):
            h.resolve_finding(self.cdir, {'id': 'C4', 'kind': 'review'}, '  ', 'arbiter')

    def test_measurement_provenance_and_local_notifications(self):
        src = self.tmp / 'm.json'
        src.write_text('{}')
        e = h.record_measurement(self.cdir, 'acc', 0.5, 'validation', 10, 'verified', src, 'x')
        self.assertEqual(e['source_sha256'], h.sha256_file(src))
        with self.assertRaises(h.GateError):
            h.record_measurement(self.cdir, 'acc', 0.5, 'validation', 10, 'verified',
                                 self.tmp / 'none', 'x')
        brief = set_brief(self.cdir, notify_channels=['file', 'email'])
        with self.assertRaises(h.GateError):
            h.notify(self.cdir, brief, 'x', channel='email')   # no adapter: stays local

    def test_campaign_repair_limit(self):
        brief = set_brief(self.cdir, repair_attempts_per_class=5, repairs_total_max=2)
        state = h.load_state(self.cdir)
        kinds = []
        for n in range(3):
            obs = {f'k{n}#0': {'job': f'k{n}', 'index': 0, 'status': 'failed', 'job_terminal': 'Failed',
                           'job_reason': None, 'arm': None, 'role': 'train', 'stage': None,
                           'policy': None, 'pod_records': 1,
                           'attempts': [{'pod': f'p{n}', 'phase': 'Failed', 'reason': None,
                                         'exit_code': 76, 'disruption': False, 'started': None,
                                         'finished': None, 'gpu_h': None, 'gpu_h_kind': 'unknown'}]}}
            acts, state = h.decide(brief, state, obs)
            kinds += [a.get('task', a['kind']) for a in acts if a['kind'] != 'notify']
        self.assertEqual(kinds, ['repair', 'repair', 'stop_branch'])

    def test_frozen_file_change_blocks_submission(self):
        (self.cdir / 'frozen.txt').write_text('v1')
        set_brief(self.cdir, gpu_h_max=10.0, frozen_files={'frozen.txt': h.sha256_file(self.cdir / 'frozen.txt')})
        h.write_approval(self.cdir, 'Kai', interactive=False)
        (self.cdir / 'frozen.txt').write_text('v2')
        with self.assertRaises(h.GateError):
            h.submit(self.cdir, self.cdir)

    def test_job_without_deadline_cannot_be_reserved(self):
        job = {'spec': {'template': {'spec': {'containers': [
            {'resources': {'limits': {'nvidia.com/gpu': '1'}}}]}}}}
        with self.assertRaises(h.GateError):
            h.gpu_bound(job)


class Concurrency(Base):
    def test_parallel_state_updates_are_not_lost(self):
        ctx = multiprocessing.get_context('fork')
        procs = [ctx.Process(target=_bump, args=(self.cdir, 50)) for _ in range(8)]
        for p in procs:
            p.start()
        for p in procs:
            p.join()
        self.assertEqual(h.load_state(self.cdir)['counters']['attempt'], 400)

    def test_task_claim_is_exclusive_until_lease_expires(self):
        with h.locked_state(self.cdir) as st:
            st['queue'].append({'id': 't1', 'task': 'repair', 'key': 'k', 'event': 'e',
                                'detail': {}, 'status': 'pending', 'steps': {},
                                'claimed_by': None, 'lease_expires': None})
        set_brief(self.cdir, lease_s=60)
        t0 = h.now_utc()
        self.assertEqual(h.claim_task(self.cdir, 'claude-code', t0)['id'], 't1')
        self.assertIsNone(h.claim_task(self.cdir, 'codex', t0 + timedelta(seconds=59)))
        self.assertEqual(h.claim_task(self.cdir, 'codex', t0 + timedelta(seconds=61))['claimed_by'],
                         'codex')


class Recovery(Base):
    """Local recovery sequence through the real run_handoff submission code and a substitute
    kubectl (tests/support/local_kubectl.py). The agent here is the SIMULATED runner."""

    def setUp(self):
        super().setUp()
        self.kube = self.tmp / 'kube'
        self.kube.mkdir()
        # No test may reach a cluster: any bare `kubectl` (e.g. nrp_doctor's node lookup inside
        # run_handoff's lint) resolves to this shim, which always fails.
        shim = self.tmp / 'bin'
        shim.mkdir()
        (shim / 'kubectl').write_text('#!/bin/sh\necho "no cluster in tests" >&2\nexit 1\n')
        (shim / 'kubectl').chmod(0o755)
        self.saved_env = dict(os.environ)
        os.environ['PATH'] = f"{shim}:{os.environ['PATH']}"
        shutil.copytree(SUPPORT / 'demo_workspace', self.cdir / 'workspace')
        os.environ.update(LOCAL_KUBE_DIR=str(self.kube), RUN_HANDOFF=str(ROOT / 'tools/run_handoff.py'),
                          HANDOFF_ROOT=str(self.cdir / 'handoffs'))
        self.brief = set_brief(
            self.cdir, gpu_h_max=1.0, kubectl=str(SUPPORT / 'local_kubectl.py'),
            selector='campaign=harness-demo', approval_ref='HARNESS-DEMO', workspace='workspace',
            repair_paths=['code/config.json'], runner='simulated',
            runner_command=[sys.executable, str(SUPPORT / 'sim_agent.py')],
            repair_test_command=[sys.executable, 'tools/check.py'],
            prepare_command=[sys.executable, 'tools/prepare.py', '{attempt}'],
            evaluate_command=[sys.executable, 'tools/evaluate.py', '{job}'])
        h.write_approval(self.cdir, 'Kai', interactive=False)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved_env)
        super().tearDown()

    def first_launch(self):
        import subprocess
        out = subprocess.run(self.brief['prepare_command'][:2] + ['0'], cwd=self.cdir / 'workspace',
                             capture_output=True, text=True, check=True).stdout.strip()
        return h.submit(self.cdir, out)

    def creates(self):
        return [json.loads(l) for l in (self.kube / 'calls.log').read_text().splitlines()
                if json.loads(l)[0] == 'create' and 'job.json' in json.loads(l)[2]]

    def ledger(self):
        return [json.loads(l) for l in (self.cdir / h.LEDGER).read_text().splitlines()]

    def test_full_recovery_sequence_and_replay(self):
        self.assertEqual(self.first_launch()['status'], 'submitted')
        acts = h.watch_once(self.cdir)                       # monitor detects the failure
        self.assertIn('repair', [a.get('task') for a in acts])
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'done')   # fix, test, relaunch
        h.watch_once(self.cdir)                              # monitor sees completion
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'done')   # evaluate, record
        self.assertEqual(len(self.creates()), 2)
        led = self.ledger()
        m = [e for e in led if e['type'] == 'measurement']
        self.assertEqual(len(m), 1)
        self.assertEqual(m[0]['split'], 'synthetic')
        repair = next(e for e in led if e['type'] == 'decision' and 'relaunched' in e['decision'])
        self.assertEqual(repair['changed'], ['code/config.json'])
        self.assertEqual(repair['runner'], 'simulated')
        st = h.load_state(self.cdir)
        self.assertTrue(st['resources']['jobs']['kai-harness-demo-a1']['final'])
        # replay: same records, no new work
        self.assertEqual([a for a in h.watch_once(self.cdir) if a['kind'] == 'task'], [])
        self.assertIsNone(h.run_task(self.cdir, 'codex'))
        self.assertEqual(len(self.creates()), 2)

    def test_interrupt_after_each_step_resumes_without_duplication(self):
        self.first_launch()
        h.watch_once(self.cdir)
        later = h.now_utc() + timedelta(seconds=self.brief['lease_s'] + 1)
        steps = ['evidence', 'agent', 'test', 'prepare', 'submit']
        for i, step in enumerate(steps):
            when = later + timedelta(seconds=i * (self.brief['lease_s'] + 1))
            holder = 'claude-code' if i % 2 == 0 else 'codex'
            self.assertEqual(h.run_task(self.cdir, holder, crash_after=step, now=when), 'interrupted')
        final = later + timedelta(seconds=len(steps) * (self.brief['lease_s'] + 1))
        self.assertEqual(h.run_task(self.cdir, 'claude-code', now=final), 'done')
        st = h.load_state(self.cdir)
        self.assertEqual(st['counters']['agent_invocations'], 1)
        self.assertEqual(st['counters']['attempt'], 1)
        self.assertEqual(len(self.creates()), 2)            # first launch + one relaunch

    def test_crash_during_agent_run_discards_partial_edits(self):
        self.first_launch()
        h.watch_once(self.cdir)
        self.assertEqual(h.run_task(self.cdir, 'claude-code', crash_after='agent_started'),
                         'interrupted')
        (self.cdir / 'workspace/code/run.py').write_text('partial edit\n')
        later = h.now_utc() + timedelta(seconds=self.brief['lease_s'] + 1)
        self.assertEqual(h.run_task(self.cdir, 'codex', now=later), 'done')
        self.assertNotEqual((self.cdir / 'workspace/code/run.py').read_text(), 'partial edit\n')
        self.assertEqual(h.load_state(self.cdir)['counters']['agent_invocations'], 2)

    def test_edit_outside_allowed_paths_is_refused_and_restored(self):
        set_brief(self.cdir, repair_paths=['code/run.py'])
        h.write_approval(self.cdir, 'Kai', interactive=False)
        self.first_launch()
        h.watch_once(self.cdir)
        before = (self.cdir / 'workspace/code/config.json').read_text()
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'failed')
        self.assertEqual((self.cdir / 'workspace/code/config.json').read_text(), before)
        self.assertEqual(len(self.creates()), 1)

    def test_repair_that_changes_a_scientific_setting_is_refused(self):
        set_brief(self.cdir, scientific_settings={'code/config.json': ['batch_size']})
        h.write_approval(self.cdir, 'Kai', interactive=False)
        self.first_launch()
        h.watch_once(self.cdir)
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'failed')
        self.assertEqual(json.loads((self.cdir / 'workspace/code/config.json').read_text())['batch_size'], 0)
        self.assertEqual(len(self.creates()), 1)
        d = [e for e in self.ledger() if e.get('decision', '').startswith('repair refused')]
        self.assertEqual(d[0]['settings'], ["code/config.json:batch_size 0 -> 50"])

    def test_submission_gates(self):
        import subprocess
        out = subprocess.run(self.brief['prepare_command'][:2] + ['0'], cwd=self.cdir / 'workspace',
                             capture_output=True, text=True, check=True).stdout.strip()
        set_brief(self.cdir, gpu_h_max=0.2)                  # edit invalidates approval
        with self.assertRaises(h.GateError):
            h.submit(self.cdir, out)
        h.write_approval(self.cdir, 'Kai', interactive=False)
        with self.assertRaises(h.GateError):                 # bound 0.333 GPU-h > 0.2
            h.submit(self.cdir, out)
        self.assertFalse((self.kube / 'calls.log').exists())
        set_brief(self.cdir, gpu_h_max=1.0)
        h.write_approval(self.cdir, 'Kai', interactive=False)
        self.assertEqual(h.submit(self.cdir, out)['status'], 'submitted')
        self.assertEqual(h.submit(self.cdir, out)['status'], 'already-submitted')
        self.assertEqual(len(self.creates()), 1)

    def test_runner_unavailable_leaves_task_for_the_other_tool(self):
        if shutil.which('codex'):
            self.skipTest('codex is installed; this test covers its absence')
        self.first_launch()
        h.watch_once(self.cdir)
        self.assertEqual(h.run_task(self.cdir, 'codex', runner='codex'), 'runner-unavailable')
        self.assertEqual(h.load_state(self.cdir)['queue'][0]['status'], 'pending')
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'done')


class Scheduling(Recovery):
    """The scheduled path (`harness.py tick`), credentials, reserves, scoring and interpretation."""

    def failing_kubectl(self, message):
        bad = self.tmp / 'bad_kubectl'
        bad.write_text(f'#!/bin/sh\necho "{message}" >&2\nexit 1\n')
        bad.chmod(0o755)
        set_brief(self.cdir, kubectl=str(bad))
        h.write_approval(self.cdir, 'Kai', interactive=False)

    def test_credential_failure_is_reported_once_and_recovery_noted(self):
        self.first_launch()
        good = self.brief['kubectl']
        self.failing_kubectl('error: You must be logged in to the server (Unauthorized)')
        self.assertEqual(h.tick(self.cdir, 'cron'), 'monitor-error:credentials')
        self.assertEqual(h.tick(self.cdir, 'cron'), 'monitor-error:credentials')
        log = (self.cdir / h.NOTIFY).read_text()
        self.assertEqual(log.count('monitor cannot read the cluster (credentials)'), 1)
        self.assertIn('oidc-login', log)
        self.assertEqual(h.load_state(self.cdir)['queue'], [])
        set_brief(self.cdir, kubectl=good)
        h.write_approval(self.cdir, 'Kai', interactive=False)
        self.assertEqual(h.tick(self.cdir, 'cron'), 'done')      # monitor + repair task
        self.assertIn('reads the cluster again (was: credentials)',
                      (self.cdir / h.NOTIFY).read_text())

    def test_network_failure_classified(self):
        self.failing_kubectl('Unable to connect to the server: dial tcp: i/o timeout')
        self.assertEqual(h.tick(self.cdir, 'cron'), 'monitor-error:network')

    def test_overlapping_passes_are_skipped(self):
        import fcntl
        with open(self.cdir / '.tick.lock', 'a+') as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            self.assertEqual(h.tick(self.cdir, 'cron'), 'busy')

    def test_scheduled_sequence_end_to_end(self):
        self.first_launch()
        results = [h.tick(self.cdir, 'cron') for _ in range(4)]
        self.assertEqual(results, ['done', 'done', 'idle', 'idle'])   # repair, evaluate
        self.assertEqual(len(self.creates()), 2)
        self.assertEqual(len([e for e in self.ledger() if e['type'] == 'measurement']), 1)

    def test_stage_reserves_protect_later_stages(self):
        import subprocess
        set_brief(self.cdir, gpu_h_max=1.0, reserve_gpu_h={'confirm': 0.5})
        h.write_approval(self.cdir, 'Kai', interactive=False)
        out = subprocess.run(self.brief['prepare_command'][:2] + ['0'], cwd=self.cdir / 'workspace',
                             capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(h.stage_cap(h.load_brief(self.cdir), 'search'), 0.5)
        self.assertEqual(h.submit(self.cdir, out, stage='search')['status'], 'submitted')  # 0.333
        out2 = subprocess.run(self.brief['prepare_command'][:2] + ['1'], cwd=self.cdir / 'workspace',
                              capture_output=True, text=True, check=True).stdout.strip()
        with self.assertRaises(h.GateError):       # 0.333 + 0.333 > 0.5 for search
            h.submit(self.cdir, out2, stage='search')
        self.assertEqual(h.submit(self.cdir, out2, stage='confirm')['status'], 'submitted')

    def test_score_jobs_get_no_tasks(self):
        doc = captured('captured-batch0918-complete.json')
        for it in doc['items']:
            if it['kind'] == 'Job':
                it['metadata']['labels']['bnjettag.io/role'] = 'score'
        _, state = h.decide(set_brief(self.cdir), h.load_state(self.cdir), h.observe(doc))
        self.assertEqual(state['queue'], [])

    def test_evaluation_pending_then_invalid_is_not_a_number(self):
        script = self.tmp / 'eval_stub.py'
        script.write_text('import sys, pathlib\n'
                          'p = pathlib.Path(sys.argv[1])\n'
                          'if not p.exists():\n    p.write_text("x"); print("PENDING"); sys.exit(0)\n'
                          'print("INVALID: no feasible checkpoint (EBOPs never <= 350000)"); sys.exit(3)\n')
        set_brief(self.cdir, evaluate_command=[sys.executable, str(script), str(self.tmp / 'flag')])
        h.write_approval(self.cdir, 'Kai', interactive=False)
        with h.locked_state(self.cdir) as st:
            st['queue'].append({'id': 'evaluate-x', 'task': 'evaluate', 'key': 'kai-x#0', 'event': 'x',
                                'detail': {}, 'status': 'pending', 'steps': {}, 'claimed_by': None,
                                'lease_expires': None})
        self.assertEqual(h.run_task(self.cdir, 'cron'), 'pending')
        self.assertEqual(h.run_task(self.cdir, 'cron'), 'done')
        led = self.ledger()
        self.assertEqual([e for e in led if e['type'] == 'measurement'], [])
        ev = [e for e in led if e['type'] == 'evaluation']
        self.assertFalse(ev[0]['valid'])
        self.assertTrue(ev[0]['reason'].startswith('INVALID'))

    def test_interpretation_limited_to_its_paths(self):
        writer = self.tmp / 'interp.py'
        writer.write_text('import json, pathlib, sys\n'
                          'pathlib.Path("ideas.json").write_text(json.dumps({"nodes": []}))\n'
                          'if len(sys.argv) > 1: pathlib.Path("PROPOSAL.md").write_text("changed")\n')
        set_brief(self.cdir, interpret_paths=['ideas.json', 'plan/*'],
                  interpret_command=[sys.executable, str(writer)])
        h.write_approval(self.cdir, 'Kai', interactive=False)
        self.first_launch()
        self.assertEqual(h.tick(self.cdir, 'cron'), 'done')   # repair
        self.assertEqual(h.tick(self.cdir, 'cron'), 'done')   # evaluate, queues interpret
        self.assertEqual(h.tick(self.cdir, 'cron'), 'done')   # interpret
        self.assertTrue((self.cdir / 'ideas.json').exists())
        set_brief(self.cdir, interpret_command=[sys.executable, str(writer), 'bad'])
        h.write_approval(self.cdir, 'Kai', interactive=False)
        with h.locked_state(self.cdir) as st:
            st['queue'].append({'id': 'interpret-y', 'task': 'interpret', 'key': 'k', 'event': 'y',
                                'detail': {}, 'status': 'pending', 'steps': {}, 'claimed_by': None,
                                'lease_expires': None})
        self.assertEqual(h.run_task(self.cdir, 'cron'), 'failed')


class HardBound(Recovery):
    """gpu_bound_mode 'hard' through the real submission code (run_handoff) and the substitute
    kubectl. The guarantee itself (Kubernetes ending the Job at its deadline) is not simulated;
    these tests cover what the harness reserves, refuses and does when the guarantee fails."""

    def prep(self, attempt, deadline=None):
        import subprocess
        env = dict(os.environ)
        if deadline:
            env['DEMO_JOB_DEADLINE'] = str(deadline)
        else:
            env.pop('DEMO_JOB_DEADLINE', None)
        return subprocess.run(self.brief['prepare_command'][:2] + [str(attempt)], cwd=self.cdir / 'workspace',
                              capture_output=True, text=True, check=True, env=env).stdout.strip()

    def hard(self, cap, **kw):
        set_brief(self.cdir, gpu_bound_mode='hard', gpu_h_max=cap, **kw)
        h.write_approval(self.cdir, 'Kai', interactive=False)

    def test_job_without_job_deadline_refused_before_any_cluster_call(self):
        self.hard(10.0)
        with self.assertRaises(h.GateError):
            h.submit(self.cdir, self.prep(0))
        self.assertFalse((self.kube / 'calls.log').exists())

    def test_reservation_is_the_hard_bound_and_cap_refuses(self):
        self.hard(1.0)                                  # demo Job: 1 GPU, grace 30 s (default)
        out = self.prep(0, deadline=1200)               # bound (1200 + 30 + 300) s = 0.425 GPU-h
        r = h.submit(self.cdir, out)
        self.assertAlmostEqual(r['reserved_gpu_h'], 0.425, places=6)
        self.assertEqual(h.load_state(self.cdir)['resources']['jobs'][r['job']]['bound'], r['reserved_gpu_h'])
        h.submit(self.cdir, self.prep(1, deadline=1200))                    # 0.85 committed
        with self.assertRaises(h.GateError):                               # + 0.425 > 1.0
            h.submit(self.cdir, self.prep(2, deadline=1200))
        self.assertEqual(len(self.creates()), 2)

    def test_reserves_for_later_stages_are_held_under_hard_bounds(self):
        self.hard(1.0, reserve_gpu_h={'confirm': 0.5})
        with self.assertRaises(h.GateError):            # search cap = 1.0 - 0.5 reserve: one 0.425 Job fits, two do not
            h.submit(self.cdir, self.prep(0, deadline=1200), stage='search')
            h.submit(self.cdir, self.prep(1, deadline=1200), stage='search')
        self.assertEqual(len(self.creates()), 1)

    def test_measured_use_above_the_bound_stops_submissions(self):
        self.hard(10.0)
        r = h.submit(self.cdir, self.prep(0, deadline=1200))
        doc = {'items': [
            {'kind': 'Job', 'metadata': {'name': r['job'], 'labels': {}, 'annotations': {}},
             'spec': {'completionMode': 'Indexed', 'completions': 1},
             'status': {'conditions': [{'type': 'Failed', 'status': 'True'}], 'failedIndexes': '0'}},
            {'kind': 'Pod', 'metadata': {'name': 'p1', 'labels': {'batch.kubernetes.io/job-name': r['job'],
                                                                  'batch.kubernetes.io/job-completion-index': '0'}},
             'spec': {'containers': [{'resources': {'limits': {'nvidia.com/gpu': '1'}}}]},
             'status': {'phase': 'Failed', 'conditions': [], 'containerStatuses': [{'state': {'terminated': {
                 'exitCode': 1, 'startedAt': '2026-10-08T00:00:00Z', 'finishedAt': '2026-10-08T01:00:00Z'}}}]}}]}
        h.watch_once(self.cdir, doc)                    # 1.0 GPU-h measured > 0.425 bound
        self.assertTrue(h.load_state(self.cdir)['stopped'])
        self.assertIn('GPU bound violated', (self.cdir / h.NOTIFY).read_text())
        with self.assertRaises(h.GateError):
            h.submit(self.cdir, self.prep(1, deadline=1200))


class Candidate(Recovery):
    """The implement task through the real harness code: SIMULATED implementer, reviewer, check
    and preparation (tests/support/sim_candidate.py), real run_handoff submission to the local
    kubectl substitute."""

    def setUp(self):
        super().setUp()
        import subprocess
        self.ws = self.cdir / 'workspace'
        g = ['git', '-C', str(self.ws), '-c', 'user.name=t', '-c', 'user.email=t@t']
        subprocess.run(['git', 'init', '-q', str(self.ws)], check=True)
        subprocess.run(g + ['add', '-A'], check=True)
        subprocess.run(g + ['commit', '-qm', 'base'], check=True)
        self.base = subprocess.run(g + ['rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
        (self.cdir / 'ideas.json').write_text(json.dumps({'nodes': [{'id': 'R0', 'code_revision': self.base},
                                                                    {'id': 'C1', 'parent': 'R0'}]}))
        (self.cdir / 'plan' / 'specs').mkdir(parents=True)
        (self.cdir / 'plan' / 'specs' / 'C1.md').write_text('add code/scales.py with SCALE = 1.0')
        (self.cdir / 'evidence').mkdir(exist_ok=True)
        (self.cdir / h.INTEGRATION_PASS).write_text('{}')
        self.configure()

    def configure(self, implement='ok', verdict='PASS', check='ok'):
        sim = [sys.executable, str(SUPPORT / 'sim_candidate.py')]
        set_brief(self.cdir, implement_runner='simulated', review_runner='simulated',
                  runner_command=sim + ['implement', implement], interpret_command=sim + ['review', verdict],
                  candidate_check_command=sim + ['check', '{node}', check],
                  candidate_prepare_command=sim + ['prepare', '{node}', '{attempt}'],
                  candidate_paths=['code/*'], candidate_protected=['tools/*'])
        h.write_approval(self.cdir, 'Kai', interactive=False)

    def queue(self):
        with h.locked_state(self.cdir) as st:
            st['queue'].append({'id': 'implement-C1', 'task': 'implement', 'key': 'C1', 'event': 'p1',
                                'detail': {'node': 'C1', 'parent': 'R0', 'spec': 'plan/specs/C1.md'},
                                'status': 'pending', 'steps': {}, 'claimed_by': None, 'lease_expires': None})

    def git(self, *a):
        import subprocess
        return subprocess.run(['git', '-C', str(self.ws), *a], capture_output=True, text=True).stdout.strip()

    def test_candidate_reaches_budget_checked_submission(self):
        self.queue()
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'done')
        st = h.load_state(self.cdir)
        steps = st['queue'][0]['steps']
        commit = steps['commit']['commit']
        self.assertEqual(self.git('rev-parse', 'cand-c1'), commit)
        self.assertEqual(self.git('rev-parse', f'{commit}^'), self.base)          # branched from the parent
        job = json.loads((Path(steps['prepare']['handoff']) / 'job.json').read_text())
        self.assertEqual(job['metadata']['annotations']['bnjettag.io/code-commit'], commit)
        self.assertEqual(self.git('rev-parse', f'{commit}^{{tree}}'), steps['implement']['tree'])
        self.assertEqual(len(self.creates()), 1)
        self.assertEqual(st['resources']['jobs'][steps['submit']['job']]['stage'], 'search')
        self.assertEqual(st['counters']['agent_invocations'], 2)                   # implement + review

    def test_interrupt_after_every_step(self):
        self.queue()
        later = h.now_utc()
        steps = ['branch', 'implement', 'review', 'check', 'commit', 'prepare', 'submit']
        for i, step in enumerate(steps):
            later = later + timedelta(seconds=self.brief['lease_s'] + 1)
            holder = 'claude-code' if i % 2 == 0 else 'codex'
            self.assertEqual(h.run_task(self.cdir, holder, crash_after=step, now=later), 'interrupted', step)
        later = later + timedelta(seconds=self.brief['lease_s'] + 1)
        self.assertEqual(h.run_task(self.cdir, 'claude-code', now=later), 'done')
        self.assertEqual(len(self.creates()), 1)
        self.assertEqual(h.load_state(self.cdir)['counters']['agent_invocations'], 2)
        self.assertIsNone(h.run_task(self.cdir, 'codex', now=later + timedelta(hours=3)))   # replay
        self.assertEqual(len(self.creates()), 1)

    def test_crash_during_implementation_discards_partial_edits(self):
        self.queue()
        self.assertEqual(h.run_task(self.cdir, 'claude-code', crash_after='implement_started'), 'interrupted')
        (self.ws / 'code' / 'partial.py').write_text('half\n')
        later = h.now_utc() + timedelta(seconds=self.brief['lease_s'] + 1)
        self.assertEqual(h.run_task(self.cdir, 'codex', now=later), 'done')
        commit = h.load_state(self.cdir)['queue'][0]['steps']['commit']['commit']
        self.assertNotIn('code/partial.py', self.git('show', '--name-only', '--format=', commit).split())

    def test_refusals_submit_nothing(self):
        for kw, why in (({'implement': 'protected'}, 'outside the permitted'), ({'implement': 'none'}, 'no change'),
                        ({'verdict': 'FAIL'}, 'review verdict FAIL'), ({'check': 'fail'}, 'candidate check failed')):
            with self.subTest(kw=kw):
                self.git('checkout', '-q', '-f', 'master') or self.git('checkout', '-q', '-f', 'main')
                with h.locked_state(self.cdir) as st:
                    st['queue'] = []
                self.configure(**kw)
                self.queue()
                self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'failed')
                self.assertIn(why, (self.cdir / h.NOTIFY).read_text())
                self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertFalse((self.kube / 'calls.log').exists() and self.creates())

    def test_integration_gate_holds_submission(self):
        (self.cdir / h.INTEGRATION_PASS).unlink()
        self.queue()
        self.assertEqual(h.run_task(self.cdir, 'claude-code'), 'waiting-integration')
        self.assertFalse((self.kube / 'calls.log').exists())
        (self.cdir / h.INTEGRATION_PASS).write_text('{}')
        later = h.now_utc() + timedelta(seconds=self.brief['lease_s'] + 1)
        self.assertEqual(h.run_task(self.cdir, 'claude-code', now=later), 'done')
        self.assertEqual(len(self.creates()), 1)


for _name in [n for n in dir(Recovery) if n.startswith('test_')]:
    setattr(Candidate, _name, None)          # the recovery tests do not apply to a git workspace


class DecisionPath(Base):
    """Stage gate, plan dispatch and replay, on constructed state (no runner here)."""

    def setUp(self):
        super().setUp()
        self.brief = set_brief(self.cdir, gpu_h_max=100.0, interpret_paths=['ideas.json', 'plan/*'])
        (self.cdir / 'ideas.json').write_text(json.dumps({'nodes': [{'id': 'R0'}, {'id': 'C1', 'parent': 'R0'}]}))
        with h.locked_state(self.cdir) as st:
            for job in ('kai-b', 'kai-r'):
                st['resources']['jobs'][job] = {'tracked': True, 'stage': 'wave1', 'reserved': 1.0}
                st['observations'][f'{job}#0'] = {'job': job, 'index': 0, 'status': 'succeeded',
                                                  'role': 'train', 'stage': 'wave1'}

    def interprets(self):
        return [q for q in h.load_state(self.cdir)['queue'] if q['task'] == 'interpret']

    def test_waits_for_the_pair_and_queues_once(self):
        h._record_evaluation(self.cdir, 'kai-b#0', {'valid': True, 'value': 0.31})
        self.assertIsNone(h.maybe_queue_interpret(self.cdir, 'wave1'))
        self.assertEqual(self.interprets(), [])
        h._record_evaluation(self.cdir, 'kai-r#0', {'valid': False, 'reason': 'INVALID[scientific]: x'})
        iid = h.maybe_queue_interpret(self.cdir, 'wave1')
        self.assertEqual(h.maybe_queue_interpret(self.cdir, 'wave1'), iid)       # replay
        self.assertEqual(len(self.interprets()), 1)
        self.assertEqual(self.interprets()[0]['detail']['results']['kai-r#0']['valid'], False)

    def test_finished_index_not_handled_twice_when_records_change(self):
        doc = captured('captured-confirm-replay-backoff.json')
        brief = set_brief(self.cdir, gpu_h_max=100.0)
        _, state = h.decide(brief, h.load_state(self.cdir), h.observe(doc))
        n = len(state['queue'])
        gone = {'items': [i for i in doc['items'] if i['kind'] == 'Job']}       # pods deleted later
        _, state = h.decide(brief, state, h.observe(gone))
        self.assertEqual(len(state['queue']), n)
        self.assertEqual(sum(state['counters']['repairs'].values()), 1)

    def test_finished_job_without_pod_records_counts_its_lifetime_bound(self):
        brief = set_brief(self.cdir, gpu_h_max=100.0)
        job = {'kind': 'Job', 'metadata': {'name': 'kai-z', 'labels': {}, 'annotations': {}},
               'spec': {'completionMode': 'Indexed', 'completions': 1, 'parallelism': 1,
                        'podReplacementPolicy': 'Failed', 'template': {'spec': {'containers': [
                            {'resources': {'limits': {'nvidia.com/gpu': '1'}}}]}}},
               'status': {'startTime': '2026-10-08T09:30:00Z', 'failedIndexes': '0', 'conditions': [
                   {'type': 'Failed', 'status': 'True', 'lastTransitionTime': '2026-10-08T10:09:00Z'}]}}
        with h.locked_state(self.cdir) as st:
            st['resources']['jobs']['kai-z'] = {'tracked': True, 'reserved': 26.24, 'bound': 26.24}
        _, state = h.decide(brief, h.load_state(self.cdir), h.observe({'items': [job]}))
        self.assertAlmostEqual(state['resources']['jobs']['kai-z']['lifetime_upper'], 0.65, places=6)
        self.assertAlmostEqual(h.committed_gpu_h(state), 2.65, places=6)        # 0.65 + fixture's 2 x 1.0, not 26.24
        job['spec']['podReplacementPolicy'] = 'TerminatingOrFailed'               # overlap possible: no bound
        _, state = h.decide(brief, h.load_state(self.cdir), h.observe({'items': [job]}))
        self.assertAlmostEqual(h.committed_gpu_h(state), 28.24, places=6)

    def test_superseded_job_not_required(self):
        with h.locked_state(self.cdir) as st:
            st['resources']['jobs']['kai-r']['superseded_by'] = 'kai-r2'
        h._record_evaluation(self.cdir, 'kai-b#0', {'valid': True, 'value': 0.31})
        self.assertIsNotNone(h.maybe_queue_interpret(self.cdir, 'wave1'))

    def write_plan(self, pid, actions):
        (self.cdir / 'plan' / 'specs').mkdir(parents=True, exist_ok=True)
        (self.cdir / 'plan' / 'specs' / 'C1.md').write_text('spec')
        (self.cdir / 'plan' / 'next.json').write_text(json.dumps(
            {'plan_id': pid, 'decision': 'PROCEED', 'reasoning': 'r', 'actions': actions}))

    def test_dispatch_once_and_refusals(self):
        self.write_plan('p1', [{'type': 'implement', 'node': 'C1', 'spec': 'plan/specs/C1.md'},
                               {'type': 'implement', 'node': 'C9', 'spec': 'plan/specs/C1.md'},
                               {'type': 'submit', 'handoff': 'handoffs/rh-x', 'stage': 'wave1'},
                               {'type': 'delete_everything'},
                               {'type': 'escalate', 'reason': 'test'}])
        out = h.dispatch_plan(self.cdir, h.load_brief(self.cdir), 't')
        outcomes = [r['outcome'] if isinstance(r['outcome'], str) else 'submitted' for r in out['results']]
        self.assertEqual(outcomes[0], 'queued')
        self.assertTrue(outcomes[1].startswith('refused: unknown idea node'))
        self.assertTrue(outcomes[2].startswith('refused'))
        self.assertTrue(outcomes[3].startswith('refused: action type not permitted'))
        self.assertEqual(outcomes[4], 'notified')
        self.assertEqual(h.dispatch_plan(self.cdir, h.load_brief(self.cdir), 't')['status'],
                         'already dispatched')
        impl = [q for q in h.load_state(self.cdir)['queue'] if q['task'] == 'implement']
        self.assertEqual(len(impl), 1)
        self.assertIn('NEEDS KAI (p1): test', (self.cdir / h.NOTIFY).read_text())

    def test_dispatched_implement_task_is_queued_once(self):
        self.write_plan('p2', [{'type': 'implement', 'node': 'C1', 'spec': 'plan/specs/C1.md'}])
        h.dispatch_plan(self.cdir, h.load_brief(self.cdir), 't')
        h.dispatch_plan(self.cdir, h.load_brief(self.cdir), 't')
        self.assertEqual(len([q for q in h.load_state(self.cdir)['queue'] if q['task'] == 'implement']), 1)

    def test_disruption_replacements_are_counted_after_the_fact(self):
        """The submission bound excludes pods replaced after ignored disruptions, but their
        measured time is counted in committed use for every later submission."""
        doc = copy.deepcopy(captured('captured-confirm-replay-backoff.json'))
        pod = next(i for i in doc['items'] if i['kind'] == 'Pod')
        for n in range(3):               # three pods of one Job, 1 GPU each
            p = copy.deepcopy(pod)
            p['metadata']['name'] += f'-{n}'
            p['spec']['containers'][0]['resources'] = {'limits': {'nvidia.com/gpu': '1'}}
            t = p['status']['containerStatuses'][0]['state']['terminated']
            t.update(startedAt=f'2026-10-01T0{n}:00:00Z', finishedAt=f'2026-10-01T0{n}:50:00Z')
            doc['items'].append(p)
        doc['items'].remove(pod)
        job = next(i for i in doc['items'] if i['kind'] == 'Job')['metadata']['name']
        with h.locked_state(self.cdir) as st:
            st['resources']['jobs'][job] = {'tracked': True, 'stage': 'wave1', 'reserved': 1.0}
        _, state = h.decide(self.brief, h.load_state(self.cdir), h.observe(doc))
        self.assertAlmostEqual(state['resources']['jobs'][job]['measured'], 2.5, places=4)
        self.assertGreater(h.committed_gpu_h(state), 1.0)          # above the reservation


class WorkspaceSnapshot(Base):
    def test_git_workspace_snapshot_twice_and_restore(self):
        import subprocess
        ws = self.tmp / 'ws'
        ws.mkdir()
        (ws / 'a.py').write_text('v1\n')
        subprocess.run(['git', 'init', '-q', str(ws)], check=True)
        subprocess.run(['git', '-C', str(ws), '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(ws), '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x'],
                       check=True)
        snap = self.tmp / 'snap'
        h._snapshot(ws, snap)
        h._snapshot(ws, snap)                       # read-only git objects must not block a re-snapshot
        self.assertFalse((snap / '.git').exists())
        (ws / 'a.py').write_text('edited\n')
        (ws / 'new.py').write_text('x\n')
        h._restore(snap, ws)
        self.assertEqual((ws / 'a.py').read_text(), 'v1\n')
        self.assertFalse((ws / 'new.py').exists())
        self.assertEqual(subprocess.run(['git', '-C', str(ws), 'status', '--porcelain'],
                                        capture_output=True, text=True).stdout, '')


class Hook(unittest.TestCase):
    CAMPAIGN = 'campaigns/2026-10-08-' + 'discovery-350k'

    def run_hook(self, command):
        import subprocess
        ev = json.dumps({'tool_name': 'Bash', 'tool_input': {'command': command}, 'cwd': str(ROOT)})
        return subprocess.run([sys.executable, str(ROOT / '.claude/hooks/pre-kubectl-lint.py')],
                              input=ev, capture_output=True, text=True).returncode

    def test_direct_submit_of_discovery_handoff_blocked(self):
        self.assertEqual(self.run_hook(f'python3 tools/run_handoff.py launch {self.CAMPAIGN}/handoffs/rh-x '
                                       '--submit --approval-ref X'), 2)

    def test_invocation_from_inside_campaign_dir_blocked(self):
        import subprocess
        ev = json.dumps({'tool_name': 'Bash', 'cwd': str(ROOT / self.CAMPAIGN), 'tool_input': {
            'command': 'python3 ../../tools/run_handoff.py launch handoffs/rh-x --submit'}})
        r = subprocess.run([sys.executable, str(ROOT / '.claude/hooks/pre-kubectl-lint.py')],
                           input=ev, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_mention_in_text_not_blocked(self):
        self.assertEqual(self.run_hook(f"cat > {self.CAMPAIGN}/notes.md <<'X'\n- a hook refuses a direct "
                                       "`run_handoff.py launch --submit`\nX"), 0)

    def test_heredoc_body_is_not_a_command(self):
        body = (f"cat > notes.md <<'EOF'\npython3 tools/run_handoff.py launch {self.CAMPAIGN}/handoffs/rh-x --submit\nEOF\n"
                "echo done")
        self.assertEqual(self.run_hook(body), 0)
        self.assertEqual(self.run_hook(body + f"\npython3 tools/run_handoff.py launch {self.CAMPAIGN}/h/rh-x --submit"), 2)

    def test_other_commands_unaffected(self):
        self.assertEqual(self.run_hook(f'python3 tools/run_handoff.py launch {self.CAMPAIGN}/handoffs/rh-x'), 0)
        self.assertEqual(self.run_hook(f'python3 tools/harness.py submit {self.CAMPAIGN} h/rh-x'), 0)
        self.assertEqual(self.run_hook('python3 tools/run_handoff.py launch other/rh-y --submit'), 0)


if __name__ == '__main__':
    unittest.main()
