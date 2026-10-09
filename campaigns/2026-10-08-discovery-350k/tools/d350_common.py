"""Shared build code for the discovery-350k handoffs (tools/prepare_attempt.py, tools/prepare_score.py).

Reuses the pilot program's frozen Job builder: campaigns/2026-10-05-pilot-program/freeze_p.py is
loaded read-only (sha256-checked, no bytecode written) and its functions (header, pod_exit_trap,
pilot_tail, pilot_job, cpu_job, build_tarball, manifest_sha) build the scripts and Job objects with
its module settings pointed at this campaign: the R1 r3 options (bounded, RSS gate off, the r3 node
exclusion), one arm per RTX 3090, backoffLimitPerIndex 1, the same image, data cache and GPU
fingerprint gate. Nothing in the pilot directory is written. Code is taken from a git commit of
code/ (git archive), never from the working tree.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

CAMP = Path(__file__).resolve().parents[1]
REPO = CAMP.parents[1]
CODE = CAMP / 'code'
EVAL = CAMP / 'eval'
PILOT = REPO / 'campaigns' / '2026-10-05-pilot-program'
FREEZE_P = PILOT / 'freeze_p.py'
RUN_HANDOFF = REPO / 'tools' / 'run_handoff.py'
CAMPAIGN_LABEL = 'discovery-350k-20261008'
PVC_ROOT = '/data/discovery-350k-20261008'
PILOT_PVC_ROOT = '/data/chang-n64-20260926/pilot-program-20261005'
CAMPAIGN_DIR = '/work/code/campaigns/d350'
EVAL_DIR = '/work/code/d350_eval'
BASE_COMMIT_FILE = CAMP / 'code-base-commit.txt'
APPROVAL_REF = 'DISCOVERY-350K-2026-10-08'
GATE_REFERENCE = 'Kai approval 2026-10-08, campaigns/2026-10-08-discovery-350k/APPROVAL.json'
STAGE_ENV = 'production'      # BNJ_STAGE: only the W&B run-id key and group suffix ('') in this code (wandb_util)
STAGES = ('wave1', 'search', 'confirm', 'followup')
def _policy():
    """The campaign policy from BRIEF.md (authority + operations), validated by the harness."""
    import importlib.util as _u
    spec = _u.spec_from_file_location('d350_harness_policy', REPO / 'tools' / 'harness.py')
    mod = _u.module_from_spec(spec)
    spec.loader.exec_module(mod)
    errs = mod.validate_brief(CAMP)
    if errs:
        raise SystemExit('BRIEF.md invalid: ' + '; '.join(errs))
    global HARNESS
    HARNESS = mod
    return mod.load_brief(CAMP)


HARNESS = None
POLICY = _policy()
S_PER_EPOCH = POLICY['deadline_seconds_per_epoch']        # operations: 39 s/epoch measured x 1.2
RUNTIME_FACTOR_MAX = POLICY['runtime_factor_max']         # authority
CANDIDATE_RUNTIME_FACTOR = POLICY['candidate_runtime_factor']  # operations
SCORE_DEADLINE_S = POLICY['score_deadline_s']             # operations
RUNTIME_FACTOR_NOTIFY = POLICY['runtime_factor_notify']   # operations
R3_EXCLUDE = ['hcc-chase-shor-c4715.unl.edu']   # pilot r3 (review/REGRESSION_TICKET_r2-resume.md option A)
PILOT_R3_BAD = ['hcc-nrp-shor-c6017.unl.edu', 'k8s-chase-ci-07.calit2.optiputer.net',
                'nautilus-ext-gpu01.fullerton.edu', 'ren-gp-argo-01.madren.org']   # manifests-98dd28-r3 NotIn list
SKIP_NAMES = re.compile(r'^\.')    # .gitignore and other dotfiles are not shipped (run_handoff TEXT_EXT)
LABEL_VALUE = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9_.-]{0,61}[A-Za-z0-9])?$')

# sha256 of the pilot files this module executes (freeze_p.py, the training-batch freeze.py it loads, and
# nrp_doctor.py, whose KNOWN_BAD_NODES that file reads), checked before anything is loaded
PINNED_FILE = CAMP / 'tools' / 'pinned.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def fail(message):
    print(f'PREPARE_BLOCKED: {message}', file=sys.stderr)
    raise SystemExit(2)


def check_pinned():
    pins = json.loads(PINNED_FILE.read_text())
    for rel, want in pins.items():
        got = sha((REPO / rel).read_bytes())
        if got != want:
            fail(f'{rel} sha256 {got} differs from tools/pinned.json {want}')
    return pins


def load_freeze_p():
    """The pilot's freeze_p module (module level defines constants and loads the training-batch
    freeze.py the same way; main() is not run)."""
    check_pinned()
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('pilot_freeze_p', FREEZE_P)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*args, check=True):
    r = subprocess.run(['git', '-C', str(CODE), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        fail(f'git {" ".join(args)}: {r.stderr.strip()}')
    return r.stdout.strip()


def default_branch():
    for b in ('main', 'master'):
        if subprocess.run(['git', '-C', str(CODE), 'rev-parse', '--verify', '-q', f'refs/heads/{b}'],
                          capture_output=True).returncode == 0:
            return b
    fail('no main or master branch in code/')


def resolve(ref):
    return git('rev-parse', '--verify', f'{ref}^{{commit}}')


def base_commit():
    return BASE_COMMIT_FILE.read_text().split()[0]


def export_tree(commit, dest):
    """`git archive <commit>` into dest (committed files only; dotfiles dropped)."""
    data = subprocess.run(['git', '-C', str(CODE), 'archive', '--format=tar', commit], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if any(SKIP_NAMES.match(p) for p in parts) or not (member.isfile() or member.isdir()):
                continue
            archive.extract(member, dest, filter='data')
    return dest


def bundle(fp, tree):
    """The pilot's deterministic tarball and run_study manifest sha over `tree`."""
    fp.CODE = Path(tree)
    payload, files = fp.build_tarball()
    msha = fp.manifest_sha()
    return payload, files, msha


def configmap(fp, name, payload, msha, base_text):
    import base64
    bsha = sha(payload)
    assert len(base64.b64encode(payload)) < 1_000_000, len(payload)
    return {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': {'user': 'kai', 'campaign': CAMPAIGN_LABEL},
                         'annotations': {'bnjettag.io/bundle-sha256': bsha, 'bnjettag.io/manifest-sha256': msha,
                                         'bnjettag.io/base': base_text}},
            'binaryData': {fp.KEY: base64.b64encode(payload).decode()}}


def point_fp(fp, run_root, stop_epoch, pod_deadline_s, tags):
    """freeze_p module settings for one discovery-350k Job (the pilot r3 options)."""
    fp.RUN_ROOT = run_root
    fp.CAMPAIGN_DIR = CAMPAIGN_DIR
    fp.STAGE = STAGE_ENV
    fp.TAGS = tags
    fp.LABELS = {'user': 'kai', 'campaign': CAMPAIGN_LABEL}
    fp.STOP_AFTER = stop_epoch
    fp.POD_DEADLINE_S = pod_deadline_s
    fp.OPTS.update(bounded=True, readout_pythonpath=False, diag=False)
    fp.R2.update(rss_gate=False, job_suffix='')
    fp.R3['exclude_nodes'] = list(R3_EXCLUDE) + [n for n in POLICY.get('extra_excluded_nodes', [])
                                                 if n not in R3_EXCLUDE]
    fp.R3['expected_start'] = {}
    assert fp.BACKOFF_PER_INDEX_BOUNDED == 1 and fp.GPU_PRODUCT == ['NVIDIA-GeForce-RTX-3090']
    bad = list(fp.H.PILOT_B_BAD_NODES)
    missing = set(PILOT_R3_BAD) - set(bad)
    if missing:
        fail(f'node exclusion list lost pilot r3 hosts: {sorted(missing)}')
    extra = [n for n in POLICY.get('extra_excluded_nodes', []) if n not in bad + list(R3_EXCLUDE)]
    return bad + list(R3_EXCLUDE) + extra       # BRIEF operations extra_excluded_nodes


def write_same(path, data):
    """Never rewrite a prepared artifact with different bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            fail(f'{path} exists with different content (attempt identities are immutable)')
        return
    path.write_bytes(data)


def run_handoff_prepare(fp, job_path, cm_path, brief_path):
    r = subprocess.run([sys.executable, str(RUN_HANDOFF), 'prepare', '--job', str(job_path), '--configmap', str(cm_path),
                        '--brief', str(brief_path), '--data-info', str(fp.EXPORT_INFO), '--data-path', fp.DATA_INFO_PATH,
                        '--out', str(CAMP / 'handoffs')], capture_output=True, text=True)
    if r.returncode != 0:
        fail(f'run_handoff prepare: {r.stderr.strip()}')
    handoff = Path(r.stdout.strip().splitlines()[-1]).resolve()
    return handoff, sha((handoff / 'record.json').read_bytes()), sha((handoff / 'job.json').read_bytes())


def check_label(value, what):
    if not LABEL_VALUE.match(value):
        fail(f'{what} {value!r} is not a valid label value')
    return value


def tmpdir():
    return tempfile.TemporaryDirectory(prefix='d350-')
