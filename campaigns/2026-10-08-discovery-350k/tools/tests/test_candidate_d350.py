"""candidate_check_d350.py and prepare_candidate_d350.py on a throwaway copy of this campaign.

python3 -m unittest campaigns/2026-10-08-discovery-350k/tools/tests/test_candidate_d350.py

The copy (as in test_evaluate_d350.py) links the pilot and training-batch campaigns and nrp-lab
read-only and replaces kubectl with a failing shim on PATH; nothing reaches a cluster. The
synthetic candidate is node c0: config d350-c0-test-s1, the baseline with only its identity keys
changed. Two runs go through the real CPU gate (about 1-2 min each). For the passing case the
copy's main branch first gets a test-only commit that trims tests/ to tests/test_selection.py,
so the run takes minutes rather than the full suite's ~9 minutes. The trimmed suite also leaves
out tests/test_d350.py, whose test_generator_reproduces_committed_configs asserts that index.json
holds exactly the two wave-1 rows: with that test in place any candidate row fails TESTS_FAILED.
"""
import copy
import importlib.util
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CAMP = Path(__file__).resolve().parents[2]
LAB = CAMP.parents[1]
D350 = Path('campaigns/d350')
NODE, CFG = 'c0', 'd350-c0-test-s1'
CERT_TEST = '''"""Coverage stand-in for the synthetic node c0 (no real inference operation is added).
A real test builds the candidate model, compares ablation.model_ebops (traced, read by the PID
controller) with certify_ebops.certify_checkpoint's recomputation, and names each added op (c0_scale)."""
import importlib.util
import os
from pathlib import Path
import sys


def test_c0_certification_stand_in():
    saved = list(sys.path)
    try:
        path = Path(os.environ['D350_EVAL_DIR']) / 'certify_ebops.py'
        spec = importlib.util.spec_from_file_location('d350_certify_ebops', path)
        certify_ebops = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(certify_ebops)
        assert certify_ebops.REL_TOL == 1e-6
        assert 'c0_scale'
    finally:
        sys.path[:] = saved
'''


def load_check():
    spec = importlib.util.spec_from_file_location('candidate_check_d350', CAMP / 'tools' / 'candidate_check_d350.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class DetectionRule(unittest.TestCase):
    def test_rules(self):
        m = load_check()
        added = {
            'bnhgq2/build.py': [(1, 'class ChannelScale(keras.layers.Layer):'),
                                (2, "        self.scale = self.add_weight(name='c1_scale', shape=(d,))"),
                                (3, '        return ops.multiply(x, self.scale)'),
                                (4, "    h = QDense(D, name='c1_proj')(h)"),
                                (5, '    # ops.multiply(x, y) in a comment is ignored')],
            'bnhgq2/train.py': [(9, '    loss = loss + 0.5 * ops.mean(ops.square(t - s))')],
            'bnhgq2/ablation.py': [(3, '    # d350-inference-op: c1_teacher_head')],
            'run_pack.py': [(1, 'class Foo(keras.layers.Layer):')],
        }
        ops = m.detect_inference_ops(added, declared=['c1_declared'])
        self.assertEqual(sorted((o['rule'], o['name']) for o in ops if o['name']),
                         [('R1', 'ChannelScale'), ('R2', 'c1_scale'), ('R3', 'c1_proj'),
                          ('R6', 'c1_declared'), ('R6', 'c1_teacher_head')])
        self.assertEqual([o['line'] for o in ops if o['rule'] == 'R5'], [3])   # train.py ops are training-only
        self.assertFalse(any(o['path'] == 'run_pack.py' for o in ops))         # outside bnhgq2/ and campaigns/d350/
        self.assertEqual(m.detect_inference_ops({'bnhgq2/train.py': added['bnhgq2/train.py']}), [])
        self.assertEqual(m.coverage_problems('certify_ebops model_ebops ChannelScale c1_scale c1_proj', ops),
                         ['c1_declared', 'c1_teacher_head'])


class CandidateTools(unittest.TestCase):
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
                        ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'APPROVAL.json', 'scores'))
        for p in (self.c / 'settings').glob('candidate-*'):
            p.unlink()
        self.code = self.c / 'code'
        bin_ = self.tmp / 'bin'
        bin_.mkdir()
        (bin_ / 'kubectl').write_text('#!/bin/sh\nexit 1\n')
        (bin_ / 'kubectl').chmod(0o755)
        self.env = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}", PYTHONDONTWRITEBYTECODE='1')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.code), '-c', 'user.name=t', '-c', 'user.email=t@t', *args],
                              check=True, capture_output=True, text=True).stdout

    def run_tool(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], cwd=self.code, capture_output=True, text=True,
                              env=self.env)

    def trim_tests_on_main(self):
        for p in (self.code / 'tests').glob('test_*.py'):
            if p.name != 'test_selection.py':
                self.git('rm', '-q', str(p.relative_to(self.code)))
        self.git('commit', '-q', '-m', 'test only: trimmed suite')

    def add_candidate(self, cert=False):
        self.git('checkout', '-q', '-b', f'cand-{NODE}')
        d = self.code / D350
        cfg = json.loads((d / 'configs' / 'd350-baseline-e-350k-s1.json').read_text())
        cfg['name'] = cfg['experiment']['arm'] = CFG
        cfg['campaign']['pilot'].update(arm='c0-test-s1', hypothesis='c0')
        data = (json.dumps(cfg, indent=2) + '\n').encode()
        (d / 'configs' / f'{CFG}.json').write_bytes(data)
        (d / 'packs' / f'{CFG}.json').write_text('[[2]]\n')
        index = json.loads((d / 'index.json').read_text())
        row = copy.deepcopy(index['runs'][0])
        row.update(index=2, name=CFG, file=f'{CFG}.json', program_arm='c0-test-s1', d350_arm='c0-test-s1',
                   hypothesis='c0', pack=f'packs/{CFG}.json', config_sha256=hashlib.sha256(data).hexdigest())
        index['runs'].append(row)
        index['count'] = 3
        (d / 'index.json').write_text(json.dumps(index, indent=2) + '\n')
        if cert:
            (self.code / 'tests' / f'test_d350_{NODE}_certification.py').write_text(CERT_TEST)

    def check(self):
        return self.run_tool(self.c / 'tools/candidate_check_d350.py', NODE)

    def prepare(self, node=NODE, attempt=1):
        return self.run_tool(self.c / 'tools/prepare_candidate_d350.py', node, attempt)

    def test_candidate_passes_then_prepares_a_search_handoff(self):
        self.trim_tests_on_main()
        self.add_candidate(cert=True)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-3000:])
        self.assertEqual(r.stdout.strip().splitlines()[-1], f'CANDIDATE_CHECK_PASS {NODE} {CFG}')
        fp = json.loads((self.c / 'settings' / f'candidate-{NODE}-fingerprint.json').read_text())
        base = {x['name']: x for x in json.loads((self.c / 'settings/wave1-fingerprint.json').read_text())}
        self.assertEqual([x['name'] for x in fp], [CFG])
        self.assertEqual({k: v for k, v in fp[0].items() if k != 'name'},
                         {k: v for k, v in base['d350-baseline-e-350k-s1'].items() if k != 'name'})
        # uncommitted change on the checked-out branch, or a missing branch: refused
        self.assertIn('uncommitted', self.prepare().stderr)
        self.assertIn('does not exist', self.prepare('c9').stderr)
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'cand-c0')
        r = self.prepare()
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])
        handoff = Path(r.stdout.strip().splitlines()[-1])
        self.assertTrue(handoff.is_absolute() and handoff.parent == self.c / 'handoffs')
        job = json.loads((handoff / 'job.json').read_text())
        pod = job['spec']['template']['spec']
        self.assertEqual(pod['activeDeadlineSeconds'], 61100)                   # 47 s x 1000 x 1.3
        self.assertEqual(job['spec']['activeDeadlineSeconds'], 2 * 61100)
        self.assertEqual(job['metadata']['labels']['bnjettag.io/stage'], 'search')
        self.assertEqual(job['metadata']['name'], 'kai-d350-c0-test-s1-a1')
        self.assertIn('run_pack.py "$PACKS" 1000', pod['containers'][0]['args'][0])
        rec = json.loads((self.c / 'attempts' / 'c0-test-s1-a1.json').read_text())
        self.assertEqual((rec['branch'], rec['stage'], rec['runtime_factor'], rec['config_name']),
                         (f'cand-{NODE}', 'search', 1.3, CFG))
        self.assertEqual(rec['commit'], self.git('rev-parse', f'cand-{NODE}').strip())
        brief = json.loads((self.c / 'manifests' / 'c0-test-s1-a1' / 'brief.json').read_text())
        self.assertIn(f'settings/candidate-{NODE}-fingerprint.json', brief['changes'])

    def test_modified_baseline_config_is_refused(self):
        self.add_candidate(cert=True)
        p = self.code / D350 / 'configs' / 'd350-baseline-e-350k-s1.json'
        p.write_text(p.read_text().replace('"lr": 0.003', '"lr": 0.002'))
        r = self.check()
        self.assertEqual(r.returncode, 5, r.stdout)
        self.assertTrue(r.stdout.startswith('CONFIG_RULE_VIOLATED'), r.stdout)
        self.assertIn('d350-baseline-e-350k-s1.json (modified)', r.stdout)

    def test_candidate_config_off_target_is_refused(self):
        self.add_candidate(cert=True)
        p = self.code / D350 / 'configs' / f'{CFG}.json'
        p.write_text(p.read_text().replace('"target_ebops": 350000', '"target_ebops": 400000'))
        r = self.check()
        self.assertEqual(r.returncode, 5, r.stdout)
        self.assertIn('config_sha256 differs', r.stdout)
        self.assertIn('EBOPs target must be 350000', r.stdout)

    def test_changed_learning_rate_in_the_training_code_is_refused(self):
        self.add_candidate(cert=True)
        p = self.code / 'bnhgq2' / 'ablation.py'
        text = p.read_text()
        old = "return float(chang_cosine_restarts(tr['lr'], "
        self.assertEqual(text.count(old), 1)
        p.write_text(text.replace(old, "return float(chang_cosine_restarts(tr['lr'] * 0.5, "))
        r = self.check()
        self.assertEqual(r.returncode, 4, r.stdout[-3000:] + r.stderr[-3000:])
        last = r.stdout.strip().splitlines()[-1]
        self.assertTrue(last.startswith('SCIENTIFIC_SETTING_CHANGED d350-baseline-e-350k-s1: '), last)
        self.assertIn('lr:', last)

    def test_added_inference_operation_needs_a_certification_test(self):
        self.add_candidate(cert=False)
        p = self.code / 'bnhgq2' / 'build.py'
        p.write_text(p.read_text() + "\n\ndef _c0_scale(layer, d):\n"
                     "    return layer.add_weight(name='c0_scale', shape=(d,), initializer='ones')\n")
        r = self.check()
        self.assertEqual(r.returncode, 6, r.stdout)
        self.assertIn('R2 bnhgq2/build.py', r.stdout)
        self.assertTrue(r.stdout.strip().splitlines()[-1].startswith(
            f'CERTIFICATION_COVERAGE_MISSING tests/test_d350_{NODE}_certification.py missing'), r.stdout)
        # a coverage test that does not name the operation is not enough
        (self.code / 'tests' / f'test_d350_{NODE}_certification.py').write_text(
            CERT_TEST.replace('c0_scale', 'the scale'))
        r = self.check()
        self.assertEqual(r.returncode, 6, r.stdout)
        self.assertIn('does not mention: c0_scale', r.stdout)
        # the explicit marker counts as an added operation too
        p.write_text(p.read_text().replace("name='c0_scale', ", '') + '# d350-inference-op: c0_gain\n')
        r = self.check()
        self.assertEqual(r.returncode, 6, r.stdout)
        self.assertIn('does not mention: c0_gain', r.stdout)

    def test_wave1_attempt_prepares_byte_identically(self):
        """prepare_attempt.py after the --config-text change: baseline attempt 1, prepared afresh in the
        copy, gives the same manifests, record and job.json as the real handoff rh-7a70ead1448f6104a4aacca9."""
        rec = json.loads((CAMP / 'attempts' / 'baseline-e-350k-s1-a1.json').read_text())
        # Wave 1 was prepared before operations.extra_excluded_nodes existed; with it empty the
        # preparation must reproduce the submitted handoff byte for byte.
        import re as _re
        text = (self.c / 'BRIEF.md').read_text()
        pat = r'```json operations\n(.*?)\n```'
        ops = json.loads(_re.search(pat, text, _re.S).group(1))
        ops['extra_excluded_nodes'] = []
        (self.c / 'BRIEF.md').write_text(_re.sub(pat, lambda _: '```json operations\n' + json.dumps(ops, indent=2) + '\n```',
                                                 text, flags=_re.S))
        shutil.rmtree(self.c / rec['handoff'])
        shutil.rmtree(self.c / 'manifests' / 'baseline-e-350k-s1-a1')
        (self.c / 'attempts' / 'baseline-e-350k-s1-a1.json').unlink()
        r = self.run_tool(self.c / 'tools/prepare_attempt.py', 'baseline-e-350k-s1', 1)
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])
        handoff = Path(r.stdout.strip().splitlines()[-1])
        self.assertEqual(handoff.name, Path(rec['handoff']).name)
        for name in ('job.json', 'record.json', 'handoff-configmap.json', 'source-configmap.json'):
            self.assertEqual((handoff / name).read_bytes(), (CAMP / rec['handoff'] / name).read_bytes(), name)
        for name in ('job.json', 'brief.json', 'configmap.json'):
            self.assertEqual((self.c / 'manifests/baseline-e-350k-s1-a1' / name).read_bytes(),
                             (CAMP / 'manifests/baseline-e-350k-s1-a1' / name).read_bytes(), name)
        self.assertEqual((self.c / 'attempts/baseline-e-350k-s1-a1.json').read_bytes(),
                         (CAMP / 'attempts/baseline-e-350k-s1-a1.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
