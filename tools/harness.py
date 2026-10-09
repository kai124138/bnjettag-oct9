#!/usr/bin/env python3
"""Campaign state, gates, watcher and recovery steps for the autonomous loop (docs/agent-harness.md).

Standard library only. Cluster access is read-only (`kubectl get`, `kubectl logs`) except through
`submit`, which calls tools/run_handoff.py with the kubectl binary named in the brief. Tests and
the local demo pass a substitute kubectl; nothing here contacts an external service.
"""
import argparse
import contextlib
import fcntl
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
STATE, BRIEF, APPROVAL = 'STATE.json', 'BRIEF.md', 'APPROVAL.json'
HANDOFF, NOTIFY, LEDGER, EVIDENCE = 'HANDOFF.md', 'NOTIFY.log', 'LEDGER.jsonl', 'evidence'
HANDOFF_MAX_LINES = 60

DEFAULT_LIMITS = {
    'gpu_h_max': 0.0,
    'infra_relaunches_per_key': 2,
    'repair_attempts_per_class': 3,
    'repairs_total_max': None,       # campaign-wide repair limit across all classes
    'agent_invocations_max': 20,
    'lease_s': 1800,
    'runner': 'simulated',
    'runner_command': None,          # argv for the simulated runner
    'workspace': None,               # directory an agent may edit, relative to the campaign
    'repair_paths': [],              # globs inside the workspace an agent may change
    'repair_test_command': None,     # argv run in the workspace; must exit 0 before relaunch
    'prepare_command': None,         # argv; {attempt} is replaced; prints a handoff directory
    'evaluate_command': None,        # argv; {job} is replaced; prints a metrics JSON path
    'workspace_command': None,       # argv; {job}; puts the workspace at the failed run's code
    'approval_ref': None,
    'kubectl': 'kubectl',
    'namespace': 'cms-ml',
    'selector': None,
    'notify_channels': ['file'],
    'reserve_gpu_h': {},             # {stage: GPU-h} held back from earlier stages
    'stage_order': ['wave1', 'search', 'confirm', 'followup'],
    'interpret_paths': [],           # globs (campaign-relative) an interpreting agent may write
    'candidate_attempts_max': 5,     # implement actions a plan may dispatch over the campaign
    'dispatch_actions': ['implement', 'submit', 'stop', 'escalate'],
    'interpret_command': None,       # argv for a simulated interpreter
    'scientific_settings': {},       # {json file in workspace: [keys]} a repair may not change
    'frozen_files': {},              # {campaign-relative path: sha256} checked before submission
    'gpu_bound_mode': 'reservation', # 'hard': only Jobs whose GPU time Kubernetes caps are accepted
    'max_concurrent_gpu_jobs': None,
    'elapsed_days_max': None,
    'elapsed_behavior': 'stop_new_submissions',
    'agent_invocations_warn': None,
    'elapsed_days_warn': None,
    'implement_runner': 'codex',
    'review_runner': 'claude',
    'candidate_paths': [],
    'candidate_protected': [],
    'candidate_check_command': None, # argv; {node}
    'candidate_prepare_command': None,  # argv; {node} {attempt}; prints a handoff directory
    'codex_bin': 'codex',            # full path when codex is not on PATH
    'codex_model': None,             # e.g. gpt-6.1-sol; None uses the Codex config default
}
RESERVED = {'publication_claim', 'public_release', 'external_message'}
INTERNAL = {'internal_record', 'notify', 'launch', 'relaunch', 'repair', 'investigate', 'evaluate'}
UNWAIVABLE_FINDINGS = {'numerical', 'authorization'}
MEASUREMENT_STATUS = {'verified', 'unverified', 'exploratory'}

INFRA_POD_REASONS = {'Evicted', 'NodeLost', 'UnexpectedAdmissionError', 'Preempting'}
DEADLINE_EXIT = 124
KNOWN_DETERMINISTIC_EXIT = {76}     # lab convention: training-phase failure (bnhgq2)

BRIEF_TEMPLATE = """# Campaign brief: {campaign}

Drafted by the agent. Approval is not written here: Kai approves with
`python3 tools/harness.py approve <campaign dir>`, which writes APPROVAL.json bound to the
exact limits block below. Any later edit to the block invalidates that approval.

## Question and hypothesis

(to be written)

## Objectives

(to be written)

## Machine-readable limits

```json
{limits}
```
"""


class GateError(Exception):
    """A check that cannot be waived to keep the loop moving."""


def now_utc():
    return datetime.now(timezone.utc)


def iso(t):
    return t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) if s else None


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def sha_text(s):
    return hashlib.sha256(s.encode()).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def append_line(path, text):
    with open(path, 'a') as f:
        f.write(text.rstrip('\n') + '\n')
        f.flush()
        os.fsync(f.fileno())


# ---------------------------------------------------------------- campaign files and state

EMPTY_STATE = {'observations': {}, 'events_seen': [], 'queue': [], 'counters':
               {'repairs': {}, 'infra_relaunches': {}, 'agent_invocations': 0, 'attempt': 0},
               'resources': {'jobs': {}}, 'lock': None, 'stopped': False}


def init_campaign(cdir, campaign):
    cdir = Path(cdir)
    cdir.mkdir(parents=True, exist_ok=True)
    limits = dict(DEFAULT_LIMITS, campaign=campaign)
    created = []
    for name, body in [
        (BRIEF, BRIEF_TEMPLATE.format(campaign=campaign, limits=json.dumps(limits, indent=2))),
        (HANDOFF, f'# Handoff: {campaign}\n\nNo work recorded yet.\n'),
        (NOTIFY, ''), (LEDGER, '')]:
        if not (cdir / name).exists():
            (cdir / name).write_text(body)
            created.append(name)
    if not (cdir / STATE).exists():
        write_json(cdir / STATE, dict(json.loads(canon(EMPTY_STATE)), campaign=campaign))
        created.append(STATE)
    (cdir / EVIDENCE).mkdir(exist_ok=True)
    return created


# Campaign briefs may hold two labelled blocks: ```json authority (Kai's commitments, permissions
# and protected commands; bound to APPROVAL.json) and ```json operations (settings the agent may
# adjust inside the ranges the authority block sets; not approval-bound). A single unlabelled
# block (tests, demos) is read as before and is entirely approval-bound.
_LIST, _DICT, _STR, _NUM, _INT = list, dict, str, (int, float), int
AUTHORITY_SCHEMA = {
    # key: (type, nullable, check, meaning)
    'campaign': (_STR, False, None, 'campaign id'),
    'gpu_h_max': (_NUM, False, lambda v: v > 0, 'GPU-hours: campaign maximum'),
    'reserve_gpu_h': (_DICT, False, lambda v: all(isinstance(x, (int, float)) and x >= 0 for x in v.values()),
                      'GPU-hours held back for each later stage'),
    'stage_order': (_LIST, False, None, 'stages in order'),
    'gpu_bound_mode': (_STR, False, lambda v: v in ('hard', 'reservation'), 'how a Job is bounded'),
    'max_concurrent_gpu_jobs': (_INT, False, lambda v: v >= 1, 'unfinished GPU Jobs at once'),
    'elapsed_days_max': (_NUM, True, lambda v: v > 0, 'days from the first training submission; null = none'),
    'elapsed_behavior': (_STR, False, lambda v: v in ('stop_new_submissions', 'review'),
                         'what reaching elapsed_days_max does'),
    'candidate_attempts_max': (_INT, False, lambda v: v >= 0, 'implement actions over the campaign; 0 = none'),
    'repairs_total_max': (_INT, False, lambda v: v >= 0, 'repairs over the campaign; 0 = none'),
    'infra_relaunches_max': (_INT, False, lambda v: v >= 0, 'upper limit for infra_relaunches_per_key'),
    'agent_invocations_max': (_INT, False, lambda v: v >= 0, 'headless agent calls; 0 = none'),
    'runtime_factor_max': (_NUM, False, lambda v: v >= 1, 'largest per-epoch time factor a Job may get'),
    'approval_ref': (_STR, False, None, 'run_handoff approval reference'),
    'namespace': (_STR, False, None, 'cluster namespace'),
    'selector': (_STR, False, None, 'label selector for this campaign'),
    'notify_channels': (_LIST, False, lambda v: v == ['file'] or set(v) <= {'file'}, 'local only'),
    'dispatch_actions': (_LIST, False, lambda v: set(v) <= {'implement', 'submit', 'stop', 'escalate'},
                         'plan actions the dispatcher may carry out'),
    'runner': (_STR, False, lambda v: v in ('simulated', 'claude', 'codex'), 'repair/interpret runner'),
    'implement_runner': (_STR, False, lambda v: v in ('simulated', 'claude', 'codex'), 'candidate implementer'),
    'review_runner': (_STR, False, lambda v: v in ('simulated', 'claude', 'codex'), 'candidate reviewer'),
    'codex_model': (_STR, True, None, 'Codex model'),
    'runner_command': (_LIST, True, None, 'simulated runner argv (tests)'),
    'interpret_command': (_LIST, True, None, 'simulated interpreter argv (tests)'),
    'workspace': (_STR, False, None, 'agent-editable directory'),
    'repair_paths': (_LIST, False, None, 'globs a repair may change'),
    'candidate_paths': (_LIST, False, None, 'globs a candidate may change'),
    'candidate_protected': (_LIST, False, None, 'globs a candidate may never change'),
    'interpret_paths': (_LIST, False, None, 'globs an interpretation may write'),
    'scientific_settings': (_DICT, False, None, 'per-key JSON settings a repair may not change'),
    'frozen_files': (_DICT, False, None, 'files whose sha256 must match before submission'),
    'repair_test_command': (_LIST, True, None, 'protected repair check'),
    'prepare_command': (_LIST, True, None, 'relaunch preparation'),
    'workspace_command': (_LIST, True, None, 'workspace checkout before a repair'),
    'evaluate_command': (_LIST, True, None, 'frozen evaluation'),
    'candidate_check_command': (_LIST, True, None, 'protected candidate check'),
    'candidate_prepare_command': (_LIST, True, None, 'candidate handoff preparation'),
}
OPERATIONS_SCHEMA = {
    'lease_s': (_INT, False, lambda v, a: 60 <= v <= 86400, 'task lease, seconds'),
    'infra_relaunches_per_key': (_INT, False, lambda v, a: 0 <= v <= a['infra_relaunches_max'],
                                 'harness relaunches after infrastructure failures, per arm'),
    'repair_attempts_per_class': (_INT, False, lambda v, a: 0 <= v <= a['repairs_total_max'],
                                  'repairs per failure class'),
    'agent_invocations_warn': (_INT, True, lambda v, a: 0 <= v <= a['agent_invocations_max'],
                               'notify when this many agent calls are used; null = no warning'),
    'elapsed_days_warn': (_NUM, True, lambda v, a: v > 0 and (a['elapsed_days_max'] is None or v <= a['elapsed_days_max']),
                          'notify after this many days; null = no warning'),
    'deadline_seconds_per_epoch': (_NUM, False, lambda v, a: 1 <= v <= 600,
                                   'pod deadline allowance per epoch, seconds (measured time x margin)'),
    'candidate_runtime_factor': (_NUM, False, lambda v, a: 1 <= v <= a['runtime_factor_max'],
                                 'default per-epoch time factor for candidates'),
    'runtime_factor_notify': (_NUM, False, lambda v, a: 1 <= v <= a['runtime_factor_max'],
                              'above this factor a handoff needs recorded timing evidence and a reason; Kai is notified'),
    'score_deadline_s': (_INT, False, lambda v, a: 600 <= v <= 86400, 'score Job deadline, seconds'),
    'extra_excluded_nodes': (_LIST, False, lambda v, a: all(isinstance(x, str) and x for x in v),
                             'nodes excluded from new handoffs in addition to the lab list (observed faults)'),
    'kubectl': (_STR, False, None, 'kubectl binary'),
    'codex_bin': (_STR, False, None, 'Codex binary'),
}


def _blocks(cdir):
    text = (Path(cdir) / BRIEF).read_text()
    auth = re.search(r'```json authority\n(.*?)\n```', text, re.S)
    if auth:
        ops = re.search(r'```json operations\n(.*?)\n```', text, re.S)
        return json.loads(auth.group(1)), (json.loads(ops.group(1)) if ops else {}), True
    m = re.search(r'```json\n(.*?)\n```', text, re.S)
    if not m:
        raise GateError(f'{BRIEF}: no machine-readable limits block')
    return json.loads(m.group(1)), {}, False


def brief_block(cdir):
    return _blocks(cdir)[0]


def validate_brief(cdir):
    """Errors in a labelled brief: unknown or missing keys, wrong types, values out of range.
    An unlabelled (legacy) brief is not validated. Errors block new submissions and agent work."""
    auth, ops, labelled = _blocks(cdir)
    if not labelled:
        return []
    errs = []
    for block, schema, name in ((auth, AUTHORITY_SCHEMA, 'authority'), (ops, OPERATIONS_SCHEMA, 'operations')):
        for k in sorted(set(block) - set(schema)):
            errs.append(f'{name}: unknown key {k!r}')
        for k, (typ, nullable, check, _) in schema.items():
            if k not in block:
                errs.append(f'{name}: missing key {k!r}')
                continue
            v = block[k]
            if v is None:
                if not nullable:
                    errs.append(f'{name}: {k} may not be null')
                continue
            if isinstance(v, bool) or not isinstance(v, typ):
                errs.append(f'{name}: {k} has the wrong type')
                continue
            try:
                ok = check is None or (check(v) if name == 'authority' else check(v, auth))
            except Exception as e:
                ok, errs = False, errs + [f'{name}: {k} could not be checked ({e})']
            if not ok:
                errs.append(f'{name}: {k}={v!r} outside its allowed range')
    return errs


def load_brief(cdir):
    auth, ops, _ = _blocks(cdir)
    brief = dict(DEFAULT_LIMITS)
    brief.update(auth)
    brief.update(ops)
    return brief


def brief_sha(cdir):
    return sha_text(canon(brief_block(cdir)))


def operations_sha(cdir):
    return sha_text(canon(_blocks(cdir)[1]))


@contextlib.contextmanager
def locked_state(cdir):
    """Exclusive read-modify-write of STATE.json across processes on this machine."""
    cdir = Path(cdir)
    with open(cdir / '.state.lock', 'a+') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            state = json.loads((cdir / STATE).read_text())
            yield state
            write_json(cdir / STATE, state)
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def load_state(cdir):
    return json.loads((Path(cdir) / STATE).read_text())


def write_handoff(cdir, text):
    lines = text.rstrip('\n').split('\n')
    if len(lines) > HANDOFF_MAX_LINES:
        raise ValueError(f'{HANDOFF} has {len(lines)} lines; the limit is {HANDOFF_MAX_LINES}')
    (Path(cdir) / HANDOFF).write_text('\n'.join(lines) + '\n')


def acquire_lock(cdir, holder, ttl_s=3600, now=None):
    """Campaign work lease: which tool (Claude Code or Codex) is driving the campaign."""
    now = now or now_utc()
    with locked_state(cdir) as state:
        lock = state.get('lock')
        if lock and lock['holder'] != holder and parse_iso(lock['expires']) > now:
            return False
        state['lock'] = {'holder': holder, 'expires': iso(now + timedelta(seconds=ttl_s))}
        return True


def release_lock(cdir, holder):
    with locked_state(cdir) as state:
        if state.get('lock') and state['lock']['holder'] == holder:
            state['lock'] = None
            return True
        return False


# ---------------------------------------------------------------- approval and gates

def write_approval(cdir, approver, actions=(), interactive=True, confirm=None):
    """Kai's approval, bound to the current limits block. The CLI path requires a terminal
    and the typed campaign id; agents run without a terminal."""
    brief = load_brief(cdir)
    if interactive:
        if not sys.stdin.isatty():
            raise GateError('approval requires an interactive terminal')
        typed = (confirm or input)(f"Type the campaign id ({brief.get('campaign')}) to approve: ")
        if typed.strip() != brief.get('campaign'):
            raise GateError('confirmation did not match; nothing written')
    record = {'campaign': brief.get('campaign'), 'brief_sha256': brief_sha(cdir),
              'approved_by': approver, 'approved_at': iso(now_utc()),
              'actions': [dict(a) for a in actions]}
    write_json(Path(cdir) / APPROVAL, record)
    return record


def current_approval(cdir):
    p = Path(cdir) / APPROVAL
    if not p.exists():
        return None
    rec = json.loads(p.read_text())
    return rec if rec.get('brief_sha256') == brief_sha(cdir) else None


def require_approval(cdir):
    if current_approval(cdir) is None:
        raise GateError('no approval matches the current brief limits')


def authorize(cdir, kind, action_id=None):
    if kind in RESERVED:
        rec = current_approval(cdir)
        if rec and action_id and any(a.get('id') == action_id and a.get('kind') == kind
                                     for a in rec.get('actions', [])):
            return True
        raise GateError(f'{kind} {action_id or ""} needs Kai\'s approval'.strip())
    if kind in INTERNAL:
        return True
    raise GateError(f'unknown action kind: {kind}')


def resolve_finding(cdir, finding, reasoning, by):
    """Records a reviewer disagreement as resolved with the given reasoning. This records a
    decision; it does not judge the reasoning. Numerical and authorization findings are refused."""
    kind = finding.get('kind')
    if kind in UNWAIVABLE_FINDINGS:
        raise GateError(f'{kind} finding {finding.get("id")} cannot be waived')
    if kind != 'review':
        raise GateError(f'unknown finding kind: {kind}')
    if not reasoning or not reasoning.strip():
        raise GateError('resolution needs written reasoning')
    entry = {'type': 'finding_resolved', 'finding': finding, 'reasoning': reasoning.strip(),
             'by': by, 'at': iso(now_utc())}
    append_line(Path(cdir) / LEDGER, canon(entry))
    return entry


def record(cdir, entry):
    entry = dict(entry, at=entry.get('at') or iso(now_utc()))
    append_line(Path(cdir) / LEDGER, canon(entry))
    return entry


def record_measurement(cdir, metric, value, split, n, status, source, by):
    """Internal recording: automatic, with provenance. It does not check that the value was
    computed from the source."""
    if status not in MEASUREMENT_STATUS:
        raise GateError(f'status must be one of {sorted(MEASUREMENT_STATUS)}')
    if not metric or not split or not isinstance(n, int) or n <= 0:
        raise GateError('measurement needs metric, split and a positive integer n')
    src = Path(source)
    if not src.is_file():
        raise GateError(f'source not found: {source}')
    return record(cdir, {'type': 'measurement', 'metric': metric, 'value': value, 'split': split,
                         'n': n, 'status': status, 'source': str(source),
                         'source_sha256': sha256_file(src), 'by': by})


def notify(cdir, brief, message, channel='file'):
    if channel not in brief.get('notify_channels', ['file']):
        raise GateError(f'notification channel {channel!r} is not approved in the brief')
    if channel != 'file':
        raise GateError(f'channel {channel!r} has no adapter; external delivery is undecided')
    line = f'{iso(now_utc())} [file] {message}'
    append_line(Path(cdir) / NOTIFY, line)
    return line


# ---------------------------------------------------------------- reading real records

def _index_set(s):
    out = set()
    for part in (s or '').split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-')
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def _gpus(containers):
    return sum(int((c.get('resources') or {}).get('limits', {}).get('nvidia.com/gpu', 0))
               for c in containers)


def _attempt(pod, now):
    st, m = pod.get('status', {}), pod.get('metadata', {})
    conds = {c.get('type') for c in st.get('conditions') or [] if c.get('status') == 'True'}
    exit_code = started = finished = None
    for c in st.get('containerStatuses') or []:
        t = (c.get('state') or {}).get('terminated') or {}
        r = (c.get('state') or {}).get('running') or {}
        if t:
            if t.get('exitCode') not in (None, 0) or exit_code is None:
                exit_code = t.get('exitCode')
            started, finished = t.get('startedAt') or started, t.get('finishedAt') or finished
        elif r:
            started = r.get('startedAt') or started
    gpus = _gpus((pod.get('spec') or {}).get('containers', []))
    gpu_h = None
    if started:
        end = parse_iso(finished) if finished else now
        gpu_h = round(gpus * max(0.0, (end - parse_iso(started)).total_seconds()) / 3600, 6)
    return {'pod': m.get('name'), 'phase': st.get('phase'), 'reason': st.get('reason'),
            'exit_code': exit_code, 'disruption': 'DisruptionTarget' in conds,
            'started': started, 'finished': finished, 'gpu_h': gpu_h,
            'gpu_h_kind': 'measured' if finished else ('estimated' if started else 'unknown')}


def observe(doc, now=None):
    """Turn a kubectl List of Jobs and Pods into one observation per Job index.

    The arm comes from the `bnjettag.io/arm` annotation when present, else None. Missing pod
    records leave exit codes and GPU time as None."""
    now = now or now_utc()
    items = doc.get('items', [])
    pods_by_job = {}
    for it in items:
        if it.get('kind') == 'Pod':
            lab = it.get('metadata', {}).get('labels', {})
            job = lab.get('batch.kubernetes.io/job-name') or lab.get('job-name')
            pods_by_job.setdefault(job, []).append(it)
    out = {}
    for it in items:
        if it.get('kind') != 'Job':
            continue
        m, spec, st = it['metadata'], it.get('spec', {}), it.get('status', {})
        name = m['name']
        conds = {c['type']: c.get('reason') for c in st.get('conditions') or []
                 if c.get('status') == 'True'}
        terminal = 'Failed' if 'Failed' in conds else ('Complete' if 'Complete' in conds else None)
        ended = st.get('completionTime') or next((c.get('lastTransitionTime') for c in st.get('conditions') or []
                                                   if c.get('type') == terminal and c.get('status') == 'True'), None)
        lifetime = {'job_start': st.get('startTime'), 'job_end': ended if terminal else None,
                    'job_gpus': _gpus(spec.get('template', {}).get('spec', {}).get('containers', [])),
                    'job_parallelism': spec.get('parallelism') or 1,
                    'job_one_pod_at_a_time': spec.get('podReplacementPolicy') == 'Failed'}
        indexed = spec.get('completionMode') == 'Indexed'
        n = spec.get('completions') or 1
        done, failed = _index_set(st.get('completedIndexes')), _index_set(st.get('failedIndexes'))
        pods = pods_by_job.get(name, [])
        for i in (range(n) if indexed else [None]):
            mine = [p for p in pods if not indexed or p['metadata'].get('labels', {}).get(
                'batch.kubernetes.io/job-completion-index') == str(i)]
            attempts = sorted((_attempt(p, now) for p in mine), key=lambda a: a['started'] or '')
            if indexed:
                if i in done:
                    status = 'succeeded'
                elif i in failed or terminal:
                    status = 'failed'
                elif any(a['phase'] == 'Running' for a in attempts):
                    status = 'running'
                elif any(a['phase'] == 'Failed' for a in attempts):
                    status = 'kubernetes_retrying'
                else:
                    status = 'pending'
            else:
                status = {'Complete': 'succeeded', 'Failed': 'failed'}.get(terminal) or (
                    'running' if any(a['phase'] == 'Running' for a in attempts) else
                    'kubernetes_retrying' if any(a['phase'] == 'Failed' for a in attempts)
                    else 'pending')
            key = name if i is None else f'{name}#{i}'
            out[key] = {'job': name, 'index': i, 'status': status, 'job_terminal': terminal,
                        'job_reason': conds.get(terminal) if terminal else None,
                        'arm': (m.get('annotations') or {}).get('bnjettag.io/arm'),
                        'role': (m.get('labels') or {}).get('bnjettag.io/role', 'train'),
                        'stage': (m.get('labels') or {}).get('bnjettag.io/stage'),
                        'policy': spec.get('podFailurePolicy'), 'attempts': attempts,
                        'pod_records': len(attempts), **lifetime}
    return out


def classify(obs):
    """infra / deadline / deterministic / unknown for a failed index, from its pod records."""
    att = obs['attempts']
    if not att:
        return 'unknown', 'no pod records for this index'
    last = att[-1]
    if last['disruption'] or last['reason'] in INFRA_POD_REASONS:
        return 'infra', f"last attempt disrupted ({last['reason'] or 'DisruptionTarget'})"
    if last['exit_code'] == DEADLINE_EXIT or last['reason'] == 'DeadlineExceeded':
        return 'deadline', 'pod deadline reached'
    if last['exit_code'] in KNOWN_DETERMINISTIC_EXIT:
        return 'deterministic', f"exit {last['exit_code']} is a known deterministic failure"
    codes = [a['exit_code'] for a in att if a['phase'] == 'Failed']
    if len(codes) >= 2 and len(set(codes)) == 1 and codes[0] not in (None, 0):
        return 'deterministic', f'{len(codes)} attempts all exited {codes[0]}'
    if last['exit_code'] is None:
        return 'unknown', 'exit code not in the pod record'
    return 'unknown', f"single failure with exit {last['exit_code']}"


# ---------------------------------------------------------------- resources

DEADLINE_ENFORCEMENT_MARGIN_S = 300    # Job-controller reaction time added to the hard bound


def gpu_bound(job, mode='reservation'):
    """Upper bound on GPU-hours a Job can allocate.

    'hard': Kubernetes ends every pod of the Job at the Job-level activeDeadlineSeconds, retries
    and pods replaced after ignored disruptions included. With podReplacementPolicy Failed no
    replacement overlaps its predecessor, so at most `parallelism` pods hold GPUs at once and
    GPU time <= GPUs x parallelism x (Job deadline + termination grace + controller margin).
    Jobs without these properties are refused in this mode.
    'reservation' (default): the smaller of GPUs x attempts x pod deadline and the Job-deadline
    bound; pods replaced after ignored disruptions are outside the pod-deadline term."""
    spec = job.get('spec', {})
    tspec = spec.get('template', {}).get('spec', {})
    gpus = _gpus(tspec.get('containers', []))
    if gpus == 0:
        return 0.0, 'no GPU requested'
    par = spec.get('parallelism') or 1
    grace = tspec.get('terminationGracePeriodSeconds', 30)
    if mode == 'hard':
        if not spec.get('activeDeadlineSeconds'):
            raise GateError('hard GPU bound needs a Job-level activeDeadlineSeconds')
        if spec.get('podReplacementPolicy') != 'Failed':
            raise GateError('hard GPU bound needs podReplacementPolicy: Failed')
        secs = spec['activeDeadlineSeconds'] + grace + DEADLINE_ENFORCEMENT_MARGIN_S
        return (round(gpus * par * secs / 3600, 6),
                'hard: Job deadline enforced by Kubernetes; includes retries and replacements')
    n = spec.get('completions') or 1
    if spec.get('completionMode') == 'Indexed':
        tries = n * ((spec.get('backoffLimitPerIndex') if spec.get('backoffLimitPerIndex')
                      is not None else spec.get('backoffLimit', 6)) + 1)
    else:
        tries = n + (spec.get('backoffLimit') if spec.get('backoffLimit') is not None else 6)
    bounds = []
    if tspec.get('activeDeadlineSeconds'):
        bounds.append(gpus * tries * tspec['activeDeadlineSeconds'] / 3600)
    if spec.get('activeDeadlineSeconds'):
        bounds.append(gpus * par * spec['activeDeadlineSeconds'] / 3600)
    if not bounds:
        raise GateError('Job has no pod or Job deadline; its GPU use cannot be bounded')
    ignores = any(r.get('action') == 'Ignore' for r in (spec.get('podFailurePolicy') or {})
                  .get('rules', []))
    return round(min(bounds), 6), ('excludes pods replaced after ignored disruptions'
                                   if ignores else 'deadline x attempts')


def committed_gpu_h(state):
    """Measured use of finished Jobs plus, for unfinished ones, the larger of the reservation
    and the running estimate."""
    total = 0.0
    for j in state['resources']['jobs'].values():
        if j.get('final') and j.get('measured') is not None:
            total += j['measured']
        elif j.get('lifetime_upper') is not None:
            total += max(j['lifetime_upper'], j.get('estimated') or 0.0)
        else:
            total += max(j.get('reserved') or 0.0, j.get('estimated') or 0.0)
    return round(total, 6)


def _update_resources(state, observations):
    per_job = {}
    for o in observations.values():
        e = per_job.setdefault(o['job'], {'measured': 0.0, 'estimated': 0.0, 'unknown': 0,
                                          'pods': 0, 'terminal': o['job_terminal'],
                                          'life': {k: o.get(k) for k in ('job_start', 'job_end', 'job_gpus',
                                                                         'job_parallelism', 'job_one_pod_at_a_time')}})
        e['pods'] += len(o['attempts'])
        for a in o['attempts']:
            if a['gpu_h'] is None:
                e['unknown'] += 1
            elif a['gpu_h_kind'] == 'measured':
                e['measured'] += a['gpu_h']
            else:
                e['estimated'] += a['gpu_h']
    for name, e in per_job.items():
        j = state['resources']['jobs'].setdefault(name, {'reserved': None, 'tracked': False})
        j['measured'] = round(e['measured'], 6)
        j['estimated'] = round(e['measured'] + e['estimated'], 6)
        j['unknown_pods'] = e['unknown']
        j['pod_records'] = e['pods']
        j['final'] = (bool(e['terminal']) and e['pods'] > 0 and e['unknown'] == 0
                      and e['estimated'] == 0)
        if e['pods'] == 0:
            j['measured'] = j['estimated'] = None     # no pod records: usage unknown
        life = e['life']
        if (not j['final'] and e['terminal'] and life.get('job_start') and life.get('job_end')
                and life.get('job_one_pod_at_a_time')):
            # A finished Job holds at most `parallelism` GPUs at a time for no longer than its own
            # lifetime: a strict upper bound on its use when pod records are gone.
            secs = (parse_iso(life['job_end']) - parse_iso(life['job_start'])).total_seconds()
            j['lifetime_upper'] = round(max(0.0, secs) * life['job_gpus'] * life['job_parallelism'] / 3600, 6)
        else:
            j.pop('lifetime_upper', None)
        if j['final']:
            j['reserved'] = None


# ---------------------------------------------------------------- decisions

def event_id(obs):
    last = obs['attempts'][-1]['pod'] if obs['attempts'] else None
    return sha_text(canon([obs['job'], obs['index'], obs['status'], last]))[:16]


def decide(brief, state, observations):
    """Pure step: returns (actions, new_state). Acts only on states Kubernetes has finished with."""
    state = json.loads(canon(state))
    actions = []
    _update_resources(state, observations)
    seen = set(state['events_seen'])
    for key, obs in sorted(observations.items()):
        state['observations'][key] = {k: obs.get(k) for k in ('job', 'index', 'status', 'arm',
                                                               'pod_records', 'role', 'stage')}
        if obs['status'] not in ('succeeded', 'failed'):
            continue        # running, pending, or Kubernetes still retrying under its policy
        ev = event_id(obs)
        if ev in seen:
            continue
        seen.add(ev)
        handled = state.setdefault('handled', {})
        if key in handled:
            # A Job index whose finished state was already acted on: later changes to its records
            # (e.g. Kubernetes deleting evicted pods) are not a new event.
            continue
        handled[key] = {'status': obs['status'], 'event': ev}
        if obs.get('role') == 'score':
            # Scoring Jobs are read by the evaluate step that started them; never evaluated or
            # repaired as experiments themselves.
            if obs['status'] == 'failed':
                actions.append({'kind': 'notify', 'message': f'score job {key} failed'})
            continue
        if obs['status'] == 'succeeded':
            actions.append({'kind': 'task', 'task': 'evaluate', 'key': key, 'event': ev})
            continue
        cls, why = classify(obs)
        state['observations'][key]['class'] = cls
        if cls == 'infra':
            # Counted per arm across its relaunched Jobs (each relaunch is a new Job name).
            lineage = (obs.get('arm') or '').split()[0] if obs.get('arm') else key
            n = state['counters']['infra_relaunches'].get(lineage, 0)
            if n < brief['infra_relaunches_per_key']:
                state['counters']['infra_relaunches'][lineage] = n + 1
                actions.append({'kind': 'task', 'task': 'relaunch', 'key': key, 'event': ev,
                                'why': why})
                continue
            cls, why = 'unknown', f'infrastructure relaunch limit reached; {why}'
        if cls in ('deterministic', 'deadline', 'unknown'):
            code = obs['attempts'][-1]['exit_code'] if obs['attempts'] else None
            ckey = f'{cls}:{code}'
            n = state['counters']['repairs'].get(ckey, 0)
            total = sum(state['counters']['repairs'].values())
            if brief.get('repairs_total_max') is not None and total >= brief['repairs_total_max']:
                actions.append({'kind': 'stop_branch', 'key': key,
                                'why': f"campaign repair limit {brief['repairs_total_max']} reached"})
            elif n < brief['repair_attempts_per_class']:
                state['counters']['repairs'][ckey] = n + 1
                actions.append({'kind': 'task', 'task': 'repair' if cls != 'unknown'
                                else 'investigate', 'key': key, 'event': ev, 'why': why,
                                'class': cls, 'exit_code': code})
            else:
                actions.append({'kind': 'stop_branch', 'key': key,
                                'why': f'repair limit reached for {ckey}'})
        actions.append({'kind': 'notify', 'message':
                        f"{key} failed: {cls} ({why})"})
    state['events_seen'] = sorted(seen)
    for name, j in state['resources']['jobs'].items():
        used = max(j.get('measured') or 0.0, j.get('estimated') or 0.0)
        if j.get('bound') is not None and used > j['bound'] + 1e-6 and not j.get('bound_violation'):
            j['bound_violation'] = True
            state['stopped'] = True
            actions.append({'kind': 'notify', 'message': f'GPU bound violated by {name}: {used} > '
                            f"{j['bound']} GPU-h; submissions stopped (the Kubernetes deadline did "
                            'not hold as assumed)'})
    if brief['gpu_h_max'] and committed_gpu_h(state) > brief['gpu_h_max']:
        if not state['stopped']:
            actions.append({'kind': 'notify', 'message': 'campaign stopped: committed GPU-h '
                            f"{committed_gpu_h(state)} exceeds {brief['gpu_h_max']}"})
        state['stopped'] = True
    tasks = [a for a in actions if a['kind'] == 'task']
    room = brief['agent_invocations_max'] - state['counters']['agent_invocations']
    agent_tasks = [a for a in tasks if a['task'] in ('repair', 'investigate')]
    if len(agent_tasks) > max(room, 0):
        dropped = agent_tasks[max(room, 0):]
        actions = [a for a in actions if a not in dropped]
        actions.append({'kind': 'notify', 'message': f'agent invocation limit: {len(dropped)} '
                                                     'task(s) not queued'})
    for a in actions:
        if a['kind'] == 'task':
            tid = f"{a['task']}-{a['event']}"
            if not any(q['id'] == tid for q in state['queue']):
                state['queue'].append({'id': tid, 'task': a['task'], 'key': a['key'],
                                       'event': a['event'], 'detail': {k: a.get(k) for k in
                                       ('why', 'class', 'exit_code')}, 'status': 'pending',
                                       'steps': {}, 'claimed_by': None, 'lease_expires': None})
    return actions, state


# ---------------------------------------------------------------- kubectl access

def kubectl(brief, *args, check=True):
    argv = [brief['kubectl'], '--request-timeout=30s', '-n', brief['namespace'], *args]
    return subprocess.run(argv, capture_output=True, text=True, check=check)


def fetch_records(brief):
    if not brief.get('selector'):
        raise GateError('brief has no Job label selector')
    jobs = json.loads(kubectl(brief, 'get', 'jobs', '-l', brief['selector'], '-o', 'json').stdout)
    names = [j['metadata']['name'] for j in jobs.get('items', [])]
    pods = {'items': []}
    if names:
        pods = json.loads(kubectl(brief, 'get', 'pods', '-l',
                                  f"batch.kubernetes.io/job-name in ({','.join(names)})",
                                  '-o', 'json').stdout)
    return {'items': jobs.get('items', []) + pods.get('items', [])}


def watch_once(cdir, doc=None, now=None):
    """One monitor pass: read records, decide, queue tasks, write notifications."""
    brief = load_brief(cdir)
    doc = doc if doc is not None else fetch_records(brief)
    observations = observe(doc, now)
    with locked_state(cdir) as state:
        actions, new = decide(brief, state, observations)
        state.clear()
        state.update(new)
    for a in actions:
        if a['kind'] == 'notify':
            notify(cdir, brief, a['message'])
        elif a['kind'] == 'stop_branch':
            notify(cdir, brief, f"stop {a['key']}: {a['why']}")
            record(cdir, {'type': 'decision', 'decision': 'STOP THIS BRANCH', 'key': a['key'],
                          'why': a['why']})
            if a['key'] != '*':
                _record_evaluation(cdir, a['key'], {'valid': False, 'reason': f"branch stopped: {a['why']}"})
                maybe_queue_interpret(cdir, stage_of(load_state(cdir), a['key']))
    return actions


# ---------------------------------------------------------------- submission

def elapsed_days(state):
    """Days since the first campaign GPU submission (score Jobs excluded); None before one."""
    starts = [j.get('submitted_at') for j in state['resources']['jobs'].values()
              if j.get('submitted_at') and (j.get('bound') or 0) > 0]
    if not starts:
        return None
    return (now_utc() - parse_iso(min(starts))).total_seconds() / 86400


def stage_cap(brief, stage):
    """GPU-h available to a stage: the total limit minus the reserves of every later stage."""
    order = brief.get('stage_order') or []
    later = order[order.index(stage) + 1:] if stage in order else []
    return round(brief['gpu_h_max'] - sum((brief.get('reserve_gpu_h') or {}).get(s, 0.0)
                                          for s in later), 6)


def submit(cdir, handoff_dir, run_handoff=None, stage=None):
    """Reserve worst-case GPU time, then submit through tools/run_handoff.py.

    Enforced only for launches made through this function. A reservation stays until records
    show the Job finished with measured pod times. Repeating a call for the same Job does not
    reserve or submit twice; run_handoff's own lookup handles a Job already on the cluster."""
    brief = load_brief(cdir)
    errs = validate_brief(cdir)
    if errs:
        raise GateError('brief invalid: ' + '; '.join(errs[:5]))
    require_approval(cdir)
    for rel, want in (brief.get('frozen_files') or {}).items():
        f = Path(cdir) / rel
        if not f.is_file() or sha256_file(f) != want:
            raise GateError(f'frozen file changed or missing: {rel}; submissions refused')
    job = json.loads((Path(handoff_dir) / 'job.json').read_text())
    name = job['metadata']['name']
    stage = stage or job['metadata'].get('labels', {}).get('bnjettag.io/stage') or 'wave1'
    bound, note = gpu_bound(job, brief.get('gpu_bound_mode', 'reservation'))
    with locked_state(cdir) as state:
        if state['stopped']:
            raise GateError('new submissions are stopped for this campaign')
        entry = state['resources']['jobs'].get(name)
        if entry and entry.get('submission') == 'submitted':
            return {'job': name, 'status': 'already-submitted'}
        if not entry and bound > 0:
            days = elapsed_days(state)
            if (brief.get('elapsed_days_max') is not None and days is not None
                    and days > brief['elapsed_days_max'] and brief['elapsed_behavior'] == 'stop_new_submissions'):
                raise GateError(f"elapsed {days:.1f} d > {brief['elapsed_days_max']} d: no new GPU submissions")
            if brief.get('max_concurrent_gpu_jobs'):
                live = [n for n, j in state['resources']['jobs'].items() if j.get('tracked') and (j.get('bound') or j.get('reserved'))
                        and not j.get('final') and j.get('submission') == 'submitted']
                if len(live) >= brief['max_concurrent_gpu_jobs']:
                    return {'job': name, 'status': 'deferred',
                            'why': f'{len(live)} unfinished GPU Jobs (limit {brief["max_concurrent_gpu_jobs"]})'}
        if not entry:
            cap = stage_cap(brief, stage)
            if committed_gpu_h(state) + bound > cap:
                raise GateError(f'GPU-h limit for stage {stage}: committed '
                                f'{committed_gpu_h(state)} + bound {bound} > {cap} '
                                f"(total {brief['gpu_h_max']} minus later-stage reserves)")
            state['resources']['jobs'][name] = {'reserved': bound, 'bound': bound, 'bound_note': note,
                                                'tracked': True, 'submission': 'intent',
                                                'stage': stage, 'authority_sha256': brief_sha(cdir),
                                                'operations_sha256': operations_sha(cdir)}
    argv = [sys.executable, str(run_handoff or ROOT / 'tools/run_handoff.py'), 'launch',
            str(handoff_dir), '--submit', '--approval-ref', str(brief['approval_ref']),
            '--kubectl', brief['kubectl']]
    res = subprocess.run(argv, capture_output=True, text=True)
    out = res.stdout + res.stderr
    if res.returncode != 0 and 'cannot read nodes' in out and 'lint blocked launch' in out:
        # Lint could not read the cluster's node list: that is missing information, not an
        # invalid Job. Nothing was created (lint runs before any cluster write); try again later.
        with locked_state(cdir) as state:
            state['resources']['jobs'].pop(name, None)
        return {'job': name, 'status': 'deferred', 'why': 'lint could not read cluster nodes'}
    with locked_state(cdir) as state:
        e = state['resources']['jobs'][name]
        e['submission'] = 'submitted' if res.returncode == 0 else 'refused-or-ambiguous'
        if res.returncode == 0:
            e['submitted_at'] = iso(now_utc())
        e['submit_output'] = out[-2000:]
    if res.returncode != 0:
        notify(cdir, brief, f'submission of {name} refused or ambiguous; reservation kept')
        raise GateError(f'run_handoff refused {name}: {(res.stderr or res.stdout).strip()[-300:]}')
    record(cdir, {'type': 'submission', 'job': name, 'reserved_gpu_h': bound, 'bound_note': note,
                  'handoff': str(handoff_dir), 'stage': stage, 'authority_sha256': brief_sha(cdir),
                  'operations_sha256': operations_sha(cdir)})
    return {'job': name, 'status': 'submitted', 'reserved_gpu_h': bound, 'stage': stage}


# ---------------------------------------------------------------- agent runners and tasks

SNAPSHOT_SKIP = ('.git', '__pycache__')


def _snapshot(ws, dest):
    """Copy the workspace for restoration, without .git (its history stays in place)."""
    if Path(dest).exists():
        shutil.rmtree(dest)
    shutil.copytree(ws, dest, ignore=shutil.ignore_patterns(*SNAPSHOT_SKIP))


def _restore(snapshot, ws):
    """Put the workspace back to the snapshot; .git is left untouched."""
    ws = Path(ws)
    for entry in ws.iterdir():
        if entry.name in SNAPSHOT_SKIP:
            continue
        shutil.rmtree(entry) if entry.is_dir() and not entry.is_symlink() else entry.unlink()
    shutil.copytree(snapshot, ws, dirs_exist_ok=True)


def _tree(ws):
    ws = Path(ws)
    return {str(p.relative_to(ws)): sha256_file(p) for p in sorted(ws.rglob('*')) if p.is_file()
            and not any(part in SNAPSHOT_SKIP for part in p.relative_to(ws).parts)}


def agent_call_allowed(cdir, brief, tid):
    """True if one more headless agent call fits agent_invocations_max. At the limit the task
    waits (one notice); nothing else is stopped. Warns once at agent_invocations_warn."""
    with locked_state(cdir) as state:
        used = state['counters']['agent_invocations']
        notes = state.setdefault('notices', [])
        warn = brief.get('agent_invocations_warn')
        if warn is not None and used >= warn and 'agent_warn' not in notes:
            notes.append('agent_warn')
            msg = f'agent calls used: {used} of {brief["agent_invocations_max"]}'
        else:
            msg = None
        ok = used < brief['agent_invocations_max']
        if not ok:
            for q in state['queue']:
                if q['id'] == tid:
                    first = 'agent_limit' not in q['steps']
                    q['steps']['agent_limit'] = True
                    q.update(status='pending', claimed_by=None, lease_expires=None)
    if msg:
        notify(cdir, brief, msg)
    if not ok and first:
        notify(cdir, brief, f'{tid}: agent call limit reached; task waits (monitoring and evaluation continue)')
    return ok


def runner_argv(brief, prompt):
    kind = brief['runner']
    if kind == 'simulated':
        if not brief.get('runner_command'):
            raise GateError('simulated runner needs runner_command')
        return 'simulated', list(brief['runner_command'])
    if kind == 'claude':
        return 'claude-cli', ['claude', '-p', prompt, '--output-format', 'json',
                              '--permission-mode', 'acceptEdits',
                              '--allowedTools', 'Read,Edit,Write,Glob,Grep']
    if kind == 'codex':
        argv = [brief.get('codex_bin') or 'codex', 'exec']
        if brief.get('codex_model'):
            argv += ['-m', brief['codex_model']]
        argv += ['--sandbox', 'workspace-write', '--json']
        if brief.get('_workspace_is_git') is False:
            argv += ['--skip-git-repo-check']
        return 'codex-cli', argv + ['-']          # prompt on stdin
    raise GateError(f'unknown runner {kind}')


def task_prompt(cdir, task):
    ev = Path(cdir) / EVIDENCE / task['id']
    return (f"You are repairing a failed task in this directory. Read {ev}/failure.json and "
            f"{ev}/pod.log for the failure evidence. Find the cause and make the smallest fix. "
            f"You may change only files matching: {', '.join(load_brief(cdir)['repair_paths'])}. "
            "Do not change the question, the evaluation, or any existing test. You may read files "
            "and run the workspace's tests; do not start training, submit jobs, or use the network. "
            "End with one paragraph: diagnosis, change made, remaining uncertainty.")


def _record_evaluation(cdir, key, result):
    with locked_state(cdir) as state:
        state.setdefault('evaluations', {})[key] = dict(result, at=iso(now_utc()))


def stage_of(state, key):
    """A Job's stage: its label when present, else the stage it was submitted under."""
    obs = state['observations'].get(key, {})
    return obs.get('stage') or state['resources']['jobs'].get(obs.get('job') or key.split('#')[0],
                                                              {}).get('stage')


def stage_required(state, stage):
    """Keys whose results a stage's interpretation needs: every index of every tracked training
    Job of that stage that has not been replaced by a relaunch. None while a Job has no record."""
    keys = []
    for job, e in state['resources']['jobs'].items():
        if not e.get('tracked') or e.get('stage') != stage or e.get('superseded_by'):
            continue
        mine = [k for k, o in state['observations'].items()
                if o.get('job') == job and o.get('role', 'train') == 'train']
        if not mine:
            return None
        keys += mine
    return sorted(keys) or None


def maybe_queue_interpret(cdir, stage):
    """Queue one interpretation when every required result of the stage exists."""
    brief = load_brief(cdir)
    if not brief.get('interpret_paths') or not stage:
        return None
    with locked_state(cdir) as state:
        keys = stage_required(state, stage)
        ev = state.get('evaluations', {})
        if not keys or any(k not in ev for k in keys):
            return None
        snap = {k: {kk: ev[k].get(kk) for kk in ('valid', 'value', 'reason')} for k in keys}
        iid = f"interpret-{stage}-{sha_text(canon(snap))[:12]}"
        if any(q['id'] == iid for q in state['queue']):
            return iid
        state['queue'].append({'id': iid, 'task': 'interpret', 'key': stage, 'event': iid,
                               'detail': {'stage': stage, 'results': snap}, 'status': 'pending',
                               'steps': {}, 'claimed_by': None, 'lease_expires': None})
        return iid


def dispatch_plan(cdir, brief, tid):
    """Carry out plan/next.json once: only permitted action types, within the campaign's limits.
    Every outcome, including refusals, is recorded."""
    cdir = Path(cdir)
    path = cdir / 'plan' / 'next.json'
    if not path.is_file():
        record(cdir, {'type': 'decision', 'decision': 'no plan written', 'task': tid})
        notify(cdir, brief, f'{tid}: interpretation wrote no plan/next.json')
        return {'status': 'no plan'}
    try:
        plan = json.loads(path.read_text())
        pid = str(plan['plan_id'])
    except (ValueError, KeyError, TypeError) as e:
        record(cdir, {'type': 'decision', 'decision': 'plan refused: unreadable', 'task': tid,
                      'error': str(e)[:300]})
        notify(cdir, brief, f'{tid}: plan/next.json unreadable; nothing dispatched')
        return {'status': 'unreadable'}
    with locked_state(cdir) as state:
        if pid in state.setdefault('dispatched', {}):
            return {'status': 'already dispatched', 'plan_id': pid}
    results = []
    for a in plan.get('actions', []):
        kind = a.get('type')
        if kind not in brief.get('dispatch_actions', []):
            results.append({'action': a, 'outcome': 'refused: action type not permitted'})
            continue
        if kind == 'implement':
            ideas = json.loads((cdir / 'ideas.json').read_text())
            node = next((n for n in ideas.get('nodes', []) if n.get('id') == a.get('node')), None)
            spec = (cdir / str(a.get('spec', ''))).resolve()
            with locked_state(cdir) as state:
                n_impl = sum(1 for q in state['queue'] if q['task'] == 'implement')
                exists = any(q['id'] == f"implement-{a.get('node')}" for q in state['queue'])
                if node is None:
                    out = 'refused: unknown idea node'
                elif not spec.is_file() or (cdir / 'plan') not in spec.parents:
                    out = 'refused: spec must be an existing file under plan/'
                elif exists:
                    out = 'already queued'
                elif n_impl >= brief.get('candidate_attempts_max', 5):
                    out = 'refused: candidate attempt limit reached'
                else:
                    state['queue'].append({'id': f"implement-{a['node']}", 'task': 'implement',
                                           'key': a['node'], 'event': pid,
                                           'detail': {'node': a['node'], 'parent': node.get('parent'),
                                                      'spec': str(spec.relative_to(cdir))},
                                           'status': 'pending', 'steps': {}, 'claimed_by': None,
                                           'lease_expires': None})
                    out = 'queued'
            results.append({'action': a, 'outcome': out})
        elif kind == 'submit':
            handoff = (cdir / str(a.get('handoff', ''))).resolve()
            stage = a.get('stage')
            if (cdir / 'handoffs') not in handoff.parents or stage not in brief['stage_order'][1:]:
                results.append({'action': a, 'outcome': 'refused: handoff outside handoffs/ or stage not permitted'})
                continue
            try:
                results.append({'action': a, 'outcome': submit(cdir, handoff, stage=stage)})
            except GateError as e:
                results.append({'action': a, 'outcome': f'refused: {e}'})
        elif kind == 'stop':
            if a.get('scope') == 'campaign':
                with locked_state(cdir) as state:
                    state['stopped'] = True
            results.append({'action': a, 'outcome': 'recorded'})
        elif kind == 'escalate':
            notify(cdir, brief, f"NEEDS KAI ({pid}): {str(a.get('reason', ''))[:400]}")
            results.append({'action': a, 'outcome': 'notified'})
    with locked_state(cdir) as state:
        state['dispatched'][pid] = {'at': iso(now_utc()), 'decision': plan.get('decision'),
                                    'results': results, 'task': tid}
    record(cdir, {'type': 'decision', 'decision': plan.get('decision'), 'plan_id': pid,
                  'reasoning': str(plan.get('reasoning', ''))[:3000], 'results': results,
                  'task': tid})
    notify(cdir, brief, f"decision {pid}: {plan.get('decision')}; " + '; '.join(
        f"{r['action'].get('type')} {r['action'].get('node') or r['action'].get('handoff') or ''}: "
        f"{r['outcome'] if isinstance(r['outcome'], str) else r['outcome'].get('status')}" for r in results))
    return {'status': 'dispatched', 'plan_id': pid, 'results': results}


def interpret_prompt(cdir, task):
    d = task.get('detail') or {}
    return (
        f"You are the research agent for the campaign in {cdir}. Read PROPOSAL.md (the approved "
        "protocol: §4 metric, §5 progression rules and INVALID classes, §6 candidates, §8 limits), "
        "BRIEF.md, ideas.json, LEDGER.jsonl and HANDOFF.md. The results of stage "
        f"{d.get('stage')!r} are complete: {json.dumps(d.get('results'))}. Score files are under "
        "evidence/scores/ (the *.result.json files hold the secondary measurements). Submission status is "
        "recorded in LEDGER.jsonl (type submission); campaign files such as attempts/*.json describe "
        "preparation only. Apply the protocol exactly. Keep measured values separate from your "
        "interpretation; never turn an INVALID into a number; describe any recovery after epoch 500 "
        "as recovery under continued training with the existing schedule. Then: (1) update "
        "ideas.json for each evaluated node: status, score (number or the INVALID reason, exactly as "
        "recorded), outcome (supporting / against / inconclusive / does not qualify at this horizon / "
        "diverged / not evaluated), and a short lesson; (2) if the protocol's next step is a candidate, "
        "write its self-contained implementation specification to plan/specs/<node id>.md "
        "(hypothesis, rationale, files that may change, required behaviour, tests, protected "
        "components, acceptance criteria); (3) write plan/next.json as JSON: {\"plan_id\": a new "
        "unique string, \"decision\": one of PROCEED, INVESTIGATE FURTHER, STOP THIS BRANCH, "
        "VALIDITY CHECK FAILED, NEEDS KAI, \"reasoning\": the evidence and the rule applied, "
        "\"actions\": a list of {\"type\": \"implement\", \"node\": id, \"spec\": "
        "\"plan/specs/<id>.md\"} | {\"type\": \"stop\", \"scope\": \"branch\" or \"campaign\", "
        "\"reason\": text} | {\"type\": \"escalate\", \"reason\": text}}. Write only ideas.json, "
        "plan/ and notes/. Do not run commands, submit jobs, edit code or change the protocol.")


NEW_COMPUTE_TASKS = ('repair', 'investigate', 'relaunch', 'implement')


INTEGRATION_PASS = 'evidence/candidate-integration-PASS.json'


def _git(ws, *args, check=True):
    return subprocess.run(['git', '-C', str(ws), '-c', 'user.name=BNJetTag harness',
                           '-c', 'user.email=harness@bnjettag.local', *args],
                          capture_output=True, text=True, check=check).stdout


def _changed_vs(ws, base):
    tracked = _git(ws, 'diff', '--name-only', base).split()
    untracked = _git(ws, 'ls-files', '--others', '--exclude-standard').split()
    return sorted(set(tracked) | set(untracked))


def implement_prompt(cdir, task, spec_text, brief):
    return (f"Implement this candidate in the current directory (a git checkout on branch "
            f"cand-{task['detail']['node']}). Follow the specification exactly.\n\n{spec_text}\n\n"
            f"Files you may change or add: {', '.join(brief['candidate_paths'])}. Never change: "
            f"{', '.join(brief['candidate_protected'])}, any existing test file, the evaluator or data code. "
            "You may run the tests. Do not start training, submit jobs or use the network. Do not commit. "
            "End with one paragraph: what you changed and why, and anything you could not do.")


def review_prompt(cdir, task, spec_rel, diff_rel, verdict_rel):
    return (f"Campaign directory: {cdir}. Review a candidate implementation. Read the specification "
            f"{spec_rel}, the diff {diff_rel}, PROPOSAL.md §3, §4, §6 and BRIEF.md. Check: the change "
            "implements the specification and nothing else; binary weights, N=64 and the 350k target are "
            "kept; no evaluation, data, split or EBOPs code or existing test is changed; no leakage of "
            "validation or test data into training; no hardcoded results; any added inference operation has a "
            "certification test that compares the traced EBOPs with certify_ebops. Write only the file "
            f"{verdict_rel} as JSON: {{\"verdict\": \"PASS\" or \"FAIL\", \"findings\": [strings]}}. "
            "Do not change any other file and do not run commands.")


def run_implement(cdir, brief, task, holder, ev, ws, crash_after):
    """Candidate task: branch from the parent's commit, implementation, path check, review, check,
    commit, versioned handoff, budget-checked submission. Each finished step is saved."""
    tid, node = task['id'], task['detail']['node']
    branch = f'cand-{node.lower()}'          # campaign tools key branches and configs on the lower-case id
    stepsof = lambda: next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']
    steps = stepsof()

    def stop(step):
        return crash_after == step

    def refuse(step, why, detail=None):
        _git(ws, 'reset', '-q', '--hard', check=False)      # index and working tree back to HEAD
        _git(ws, 'clean', '-fdq', check=False)
        _set_step(cdir, tid, step, dict(detail or {}, refused=why), 'failed')
        record(cdir, {'type': 'decision', 'decision': f'candidate {node} not submitted: {why}',
                      'task': tid, 'outcome': 'implementation failure (not a scientific result)'})
        notify(cdir, brief, f'{tid}: {why}; nothing submitted')
        return 'failed'

    if 'branch' not in steps:
        ideas = json.loads((cdir / 'ideas.json').read_text())
        parent = next((n for n in ideas['nodes'] if n['id'] == task['detail'].get('parent')), None)
        base = (parent or {}).get('code_revision')
        if not base:
            return refuse('branch', 'parent node has no recorded code revision')
        if _git(ws, 'status', '--porcelain').strip():
            return refuse('branch', 'workspace not clean')
        _git(ws, 'checkout', '-q', '-B', branch, base)
        _set_step(cdir, tid, 'branch', {'branch': branch, 'base': base})
        if stop('branch'):
            return 'interrupted'
    base = stepsof()['branch']['base']

    if 'implement' not in steps:
        if 'implement_started' in steps:      # a process died mid-run: discard partial edits
            _git(ws, 'checkout', '-q', '-f', '-B', branch, base)
            _git(ws, 'reset', '-q', '--hard', check=False)
            _git(ws, 'clean', '-fdq', check=False)
        spec_text = (cdir / task['detail']['spec']).read_text()
        prompt = implement_prompt(cdir, task, spec_text, brief)
        r = brief['implement_runner']
        kind, argv = ((('simulated', list(brief['runner_command'])) if r == 'simulated'
                       else runner_argv(dict(brief, runner=r, _workspace_is_git=True), prompt)))
        if shutil.which(argv[0]) is None:
            with locked_state(cdir) as state:
                for q in state['queue']:
                    if q['id'] == tid:
                        q.update(status='pending', claimed_by=None, lease_expires=None)
            notify(cdir, brief, f'{tid}: implementation runner {kind} unavailable; task waits')
            return 'runner-unavailable'
        if not agent_call_allowed(cdir, brief, tid):
            return 'agent-limit'
        with locked_state(cdir) as state:
            state['counters']['agent_invocations'] += 1
        _set_step(cdir, tid, 'implement_started', {'kind': kind, 'at': iso(now_utc())})
        if stop('implement_started'):
            return 'interrupted'
        res = subprocess.run(argv, cwd=ws, capture_output=True, text=True,
                             input=prompt if kind == 'codex-cli' else None,
                             env=dict(os.environ, HARNESS_TASK=tid, HARNESS_EVIDENCE=str(ev),
                                      HARNESS_SPEC=str(cdir / task['detail']['spec'])))
        (ev / 'implement-output.txt').write_text(res.stdout + res.stderr)
        if res.returncode != 0:
            return refuse('implement', f'implementation runner exit {res.returncode}')
        changed = _changed_vs(ws, base)
        existing = set(_git(ws, 'ls-tree', '-r', '--name-only', base).split())
        bad = [c for c in changed if not any(fnmatch.fnmatch(c, g) for g in brief['candidate_paths'])
               or any(fnmatch.fnmatch(c, g) for g in brief['candidate_protected'])
               or (c.startswith('tests/') and c in existing)]
        (ev / 'candidate.diff').write_text(_git(ws, 'diff', base) + ''.join(
            f'\n=== new file {u} ===\n' + (ws / u).read_text(errors='replace')
            for u in _git(ws, 'ls-files', '--others', '--exclude-standard').split()))
        if not changed:
            return refuse('implement', 'implementation made no change', {'kind': kind})
        if bad:
            return refuse('implement', f'changes outside the permitted candidate paths: {bad}', {'kind': kind, 'changed': changed})
        _git(ws, 'add', '-A')
        _set_step(cdir, tid, 'implement', {'kind': kind, 'changed': changed,
                                           'tree': _git(ws, 'write-tree').strip()})
        if stop('implement'):
            return 'interrupted'
    tree = stepsof()['implement']['tree']

    if 'review' not in stepsof():
        if _git(ws, 'write-tree').strip() != tree:
            return refuse('review', 'workspace differs from the implemented tree')
        verdict_rel = f'{EVIDENCE}/{tid}/review.json'
        (cdir / verdict_rel).unlink(missing_ok=True)
        r = brief['review_runner']
        prompt = review_prompt(cdir, task, task['detail']['spec'], f'{EVIDENCE}/{tid}/candidate.diff', verdict_rel)
        kind, argv = ((('simulated', list(brief['interpret_command'])) if r == 'simulated'
                       else runner_argv(dict(brief, runner=r, _workspace_is_git=False), prompt)))
        if not agent_call_allowed(cdir, brief, tid):
            return 'agent-limit'
        with locked_state(cdir) as state:
            state['counters']['agent_invocations'] += 1
        before = _tree(cdir)
        res = subprocess.run(argv, cwd=cdir, capture_output=True, text=True,
                             input=prompt if kind == 'codex-cli' else None,
                             env=dict(os.environ, HARNESS_TASK=tid, HARNESS_EVIDENCE=str(ev),
                                      HARNESS_VERDICT=str(cdir / verdict_rel)))
        (ev / 'review-output.txt').write_text(res.stdout + res.stderr)
        after = _tree(cdir)
        stray = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)
                       and k != verdict_rel and not k.startswith(('STATE.json', '.state.lock', 'LEDGER.jsonl',
                                                                  'NOTIFY.log', f'{EVIDENCE}/{tid}/', 'code/')))
        try:
            verdict = json.loads((cdir / verdict_rel).read_text())
        except (OSError, ValueError):
            verdict = {'verdict': 'MISSING', 'findings': ['no readable verdict file']}
        if stray:
            return refuse('review', f'reviewer wrote outside its verdict file: {stray[:5]}')
        if verdict.get('verdict') != 'PASS':
            return refuse('review', f"review verdict {verdict.get('verdict')}", {'findings': verdict.get('findings')})
        _set_step(cdir, tid, 'review', {'kind': kind, 'verdict': 'PASS', 'findings': verdict.get('findings', [])})
        if stop('review'):
            return 'interrupted'

    if 'check' not in stepsof():
        if _git(ws, 'write-tree').strip() != tree:
            return refuse('check', 'workspace differs from the reviewed tree')
        t = subprocess.run(_fmt(brief['candidate_check_command'], cdir=str(Path(cdir).resolve()), node=node),
                           cwd=ws, capture_output=True, text=True)
        (ev / 'check-output.txt').write_text(t.stdout + t.stderr)
        passed = re.search(rf'^CANDIDATE_CHECK_PASS {re.escape(node)}(\s|$)', t.stdout, re.M | re.I)
        if t.returncode != 0 or not passed:
            first = next((l for l in t.stdout.splitlines() if re.match(r'^[A-Z_]{6,}', l)), f'exit {t.returncode}')
            return refuse('check', f'candidate check failed: {first[:300]}')
        _git(ws, 'add', '-A')                      # the check may freeze the candidate fingerprint
        if _git(ws, 'write-tree').strip() != tree:
            return refuse('check', 'candidate check changed the code tree')
        _set_step(cdir, tid, 'check', {'exit': 0})
        if stop('check'):
            return 'interrupted'

    if 'commit' not in stepsof():
        if _git(ws, 'write-tree').strip() != tree:
            return refuse('commit', 'workspace differs from the reviewed and checked tree')
        _git(ws, 'commit', '-qm', f'candidate {node} ({tid}); reviewed tree {tree[:12]}')
        commit = _git(ws, 'rev-parse', 'HEAD').strip()
        if _git(ws, 'rev-parse', 'HEAD^{tree}').strip() != tree:
            return refuse('commit', 'committed tree differs from the reviewed tree')
        _set_step(cdir, tid, 'commit', {'commit': commit, 'tree': tree})
        if stop('commit'):
            return 'interrupted'
    commit = stepsof()['commit']['commit']

    if 'prepare' not in stepsof():
        with locked_state(cdir) as state:
            state['counters']['attempt'] += 1
            attempt = state['counters']['attempt']
        p = subprocess.run(_fmt(brief['candidate_prepare_command'], cdir=str(Path(cdir).resolve()), node=node,
                                attempt=attempt), cwd=ws, capture_output=True, text=True)
        (ev / 'prepare-output.txt').write_text(p.stdout + p.stderr)
        if p.returncode != 0:
            return refuse('prepare', f'candidate preparation failed (exit {p.returncode})')
        handoff = p.stdout.strip().splitlines()[-1]
        job = json.loads((Path(handoff) / 'job.json').read_text())
        packaged = job['metadata'].get('annotations', {}).get('bnjettag.io/code-commit')
        if packaged != commit:
            return refuse('prepare', f'handoff packages {packaged}, not the reviewed commit {commit}')
        _set_step(cdir, tid, 'prepare', {'handoff': handoff, 'attempt': attempt, 'commit': commit,
                                         'job': job['metadata']['name']})
        if stop('prepare'):
            return 'interrupted'

    if 'submit' not in stepsof():
        if not (Path(cdir) / INTEGRATION_PASS).is_file():
            with locked_state(cdir) as state:
                for q in state['queue']:
                    if q['id'] == tid:
                        q.update(status='pending', claimed_by=None, lease_expires=None)
            notify(cdir, brief, f'{tid}: prepared, but the candidate integration has not passed; not submitted')
            return 'waiting-integration'
        result = submit(cdir, stepsof()['prepare']['handoff'], stage='search')
        if result.get('status') == 'deferred':
            with locked_state(cdir) as state:
                for q in state['queue']:
                    if q['id'] == tid:
                        q.update(status='pending', claimed_by=None, lease_expires=None)
            return 'deferred'
        _set_step(cdir, tid, 'submit', result)
        if stop('submit'):
            return 'interrupted'
    st = stepsof()
    record(cdir, {'type': 'decision', 'decision': f'candidate {node} submitted', 'task': tid,
                  'commit': st['commit']['commit'], 'job': st['submit']['job'], 'review': st['review']})
    _set_step(cdir, tid, 'done', True, 'done')
    notify(cdir, brief, f"{tid}: candidate {node} at commit {st['commit']['commit'][:12]} submitted as {st['submit']['job']}")
    return 'done'


def claim_task(cdir, holder, now=None):
    """Claim the next runnable task. A submission stop holds back tasks that lead to new compute;
    an invalid brief allows only evaluation. Monitoring is never held back here."""
    now = now or now_utc()
    brief = load_brief(cdir)
    config_ok = not validate_brief(cdir)
    with locked_state(cdir) as state:
        for q in state['queue']:
            if state['stopped'] and q['task'] in NEW_COMPUTE_TASKS:
                continue
            if not config_ok and q['task'] != 'evaluate':
                continue
            free = q['status'] == 'pending' or (q['status'] == 'claimed' and
                                                parse_iso(q['lease_expires']) <= now)
            if free:
                q.update(status='claimed', claimed_by=holder,
                         lease_expires=iso(now + timedelta(seconds=brief['lease_s'])))
                return dict(q)
    return None


def _set_step(cdir, tid, step, value, status=None):
    with locked_state(cdir) as state:
        for q in state['queue']:
            if q['id'] == tid:
                q['steps'][step] = value
                if status:
                    q['status'] = status
                return q
    raise KeyError(tid)


def _fmt(argv, **kw):
    """Fill {job}, {attempt}, {cls}, {node} and {cdir} (the campaign directory) in a command."""
    return [a.format(**kw) for a in argv]


def run_task(cdir, holder, records_doc=None, crash_after=None, run_handoff=None, runner=None,
             now=None):
    """Claim one task and carry it through its steps; each finished step is saved so a resumed
    process continues after it. `crash_after` (tests only) stops after the named step."""
    cdir = Path(cdir)
    brief = load_brief(cdir)
    task = claim_task(cdir, holder, now)
    if not task:
        return None
    tid, steps = task['id'], task['steps']
    ev = cdir / EVIDENCE / tid
    ev.mkdir(parents=True, exist_ok=True)
    ws = cdir / brief['workspace'] if brief.get('workspace') else None

    def stop(step):
        return crash_after == step

    if task['task'] == 'evaluate':
        if 'evaluate' not in steps:
            job = task['key'].split('#')[0]
            out = subprocess.run(_fmt(brief['evaluate_command'], cdir=str(Path(cdir).resolve()), job=job), cwd=ws,
                                 capture_output=True, text=True)
            (ev / 'evaluate-output.txt').write_text(out.stdout + out.stderr)
            last = (out.stdout.strip().splitlines() or [''])[-1].strip()
            if last == 'PENDING' and out.returncode == 0:
                # Scoring runs elsewhere (a CPU Job); release the task for the next monitor pass.
                with locked_state(cdir) as state:
                    for q in state['queue']:
                        if q['id'] == tid:
                            q['steps']['evaluate_polls'] = q['steps'].get('evaluate_polls', 0) + 1
                            q.update(status='pending', claimed_by=None, lease_expires=None)
                return 'pending'
            if last.startswith('INVALID'):
                # No score exists for this run; record that, never a number.
                record(cdir, {'type': 'evaluation', 'key': task['key'], 'valid': False,
                              'reason': last, 'evidence': str(ev / 'evaluate-output.txt')})
                _set_step(cdir, tid, 'evaluate', {'valid': False, 'reason': last})
                notify(cdir, brief, f"{task['key']} evaluated: {last}")
            elif out.returncode != 0:
                _set_step(cdir, tid, 'evaluate', {'exit': out.returncode}, 'failed')
                notify(cdir, brief, f'evaluation of {task["key"]} failed (exit {out.returncode}); '
                                    'no score recorded')
                return 'failed'
            else:
                metrics_path = Path(last)
                m = json.loads(metrics_path.read_text())
                record_measurement(cdir, m['metric'], m['value'], m['split'], m['n'], m['status'],
                                   metrics_path, by=f'{holder}/evaluate')
                _set_step(cdir, tid, 'evaluate', {'valid': True, 'metrics': str(metrics_path)})
                notify(cdir, brief, f"{task['key']} evaluated: {m['metric']} = {m['value']} "
                                    f"({m['split']}, n={m['n']}, {m['status']})")
            if stop('evaluate'):
                return 'interrupted'
        st_eval = next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']['evaluate']
        result = {'valid': st_eval.get('valid', False), 'reason': st_eval.get('reason')}
        if st_eval.get('valid'):
            result['value'] = json.loads(Path(st_eval['metrics']).read_text())['value']
        _record_evaluation(cdir, task['key'], result)
        record(cdir, {'type': 'decision', 'decision': 'task completed and evaluated',
                      'key': task['key'], 'task': tid})
        _set_step(cdir, tid, 'done', True, 'done')
        maybe_queue_interpret(cdir, stage_of(load_state(cdir), task['key']))
        return 'done'

    if task['task'] == 'interpret':
        # An agent reads the evidence and updates the idea record and plan files only.
        if 'interpret' not in steps:
            before = _tree(cdir)
            prompt = interpret_prompt(cdir, task)
            r = runner or brief['runner']
            if r == 'simulated':
                kind, argv = 'simulated', list(brief['interpret_command'])
            else:
                kind, argv = runner_argv(dict(brief, runner=r, _workspace_is_git=False), prompt)
            if shutil.which(argv[0]) is None:
                with locked_state(cdir) as state:
                    for q in state['queue']:
                        if q['id'] == tid:
                            q.update(status='pending', claimed_by=None, lease_expires=None)
                notify(cdir, brief, f'runner {kind} unavailable; {tid} left pending')
                return 'runner-unavailable'
            if not agent_call_allowed(cdir, brief, tid):
                return 'agent-limit'
            with locked_state(cdir) as state:
                state['counters']['agent_invocations'] += 1
            res = subprocess.run(argv, cwd=cdir, capture_output=True, text=True,
                                 input=prompt if kind == 'codex-cli' else None,
                                 env=dict(os.environ, HARNESS_TASK=tid, HARNESS_EVIDENCE=str(ev)))
            (ev / 'interpret-output.txt').write_text(res.stdout + res.stderr)
            after = _tree(cdir)
            changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)
                             and not k.startswith(('STATE.json', '.state.lock', 'LEDGER.jsonl',
                                                   'NOTIFY.log', EVIDENCE + '/')))
            bad = [c for c in changed if not any(fnmatch.fnmatch(c, g)
                                                 for g in brief['interpret_paths'])]
            if res.returncode != 0 or bad:
                _set_step(cdir, tid, 'interpret', {'kind': kind, 'changed': changed,
                                                   'refused': bad or f'exit {res.returncode}'},
                          'failed')
                notify(cdir, brief, f'{tid}: interpretation refused '
                                    f'({bad or "runner exit " + str(res.returncode)})')
                return 'failed'
            _set_step(cdir, tid, 'interpret', {'kind': kind, 'changed': changed})
        record(cdir, {'type': 'decision', 'decision': 'interpretation recorded', 'task': tid,
                      'changed': next(q for q in load_state(cdir)['queue']
                                      if q['id'] == tid)['steps']['interpret']['changed']})
        steps = next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']
        if 'dispatch' not in steps:
            _set_step(cdir, tid, 'dispatch', dispatch_plan(cdir, brief, tid))
        _set_step(cdir, tid, 'done', True, 'done')
        return 'done'

    if task['task'] == 'implement':
        return run_implement(cdir, brief, task, holder, ev, ws, crash_after)

    # repair / investigate / relaunch
    if 'evidence' not in steps:
        obs = load_state(cdir)['observations'].get(task['key'], {})
        (ev / 'failure.json').write_text(json.dumps({'task': task, 'observation': obs},
                                                    indent=2) + '\n')
        doc = records_doc if records_doc is not None else (
            fetch_records(brief) if brief.get('selector') else None)
        pod = ((observe(doc).get(task['key'], {}).get('attempts') or [{}])[-1].get('pod')
               if doc else None)
        log = ''
        if pod:
            r = kubectl(brief, 'logs', pod, '--tail=200', check=False)
            log = r.stdout if r.returncode == 0 else f'(logs unavailable: exit {r.returncode})'
        (ev / 'pod.log').write_text(log or '(no pod log available)\n')
        if brief.get('workspace_command'):
            w = subprocess.run(_fmt(brief['workspace_command'], cdir=str(Path(cdir).resolve()), job=task['key'].split('#')[0]),
                               cwd=ws, capture_output=True, text=True)
            (ev / 'workspace-command.txt').write_text(w.stdout + w.stderr)
            if w.returncode != 0:
                _set_step(cdir, tid, 'evidence', {'workspace_command_exit': w.returncode}, 'failed')
                notify(cdir, brief, f'{tid}: could not set the workspace to the failed run\'s code')
                return 'failed'
        if ws:
            _snapshot(ws, ev / 'workspace-before')
        _set_step(cdir, tid, 'evidence', {'dir': str(ev), 'pod': pod})
        if stop('evidence'):
            return 'interrupted'

    if task['task'] in ('repair', 'investigate') and 'agent' not in steps:
        if 'agent_started' in steps:
            # An earlier process died during the agent run: discard its partial edits.
            _restore(ev / 'workspace-before', ws)
        before = _tree(ws)
        prompt = task_prompt(cdir, task)
        kind, argv = runner_argv(dict(brief, runner=runner or brief['runner'],
                                      _workspace_is_git=(ws / '.git').exists()), prompt)
        if shutil.which(argv[0]) is None:
            _set_step(cdir, tid, 'runner', {'kind': kind, 'status': 'unavailable'}, 'pending')
            with locked_state(cdir) as state:
                for q in state['queue']:
                    if q['id'] == tid:
                        q.update(claimed_by=None, lease_expires=None)
            notify(cdir, brief, f'runner {kind} unavailable; {tid} left pending')
            return 'runner-unavailable'
        if not agent_call_allowed(cdir, brief, tid):
            return 'agent-limit'
        with locked_state(cdir) as state:
            state['counters']['agent_invocations'] += 1
        _set_step(cdir, tid, 'agent_started', {'kind': kind, 'at': iso(now_utc())})
        if stop('agent_started'):
            return 'interrupted'
        res = subprocess.run(argv, cwd=ws, capture_output=True, text=True,
                             input=prompt if kind == 'codex-cli' else None,
                             env=dict(os.environ, HARNESS_TASK=tid, HARNESS_EVIDENCE=str(ev)))
        (ev / 'agent-output.txt').write_text(res.stdout + res.stderr)
        after = _tree(ws)
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        bad = [c for c in changed if not any(fnmatch.fnmatch(c, g) for g in brief['repair_paths'])]
        sci = []
        for rel, keys in (brief.get('scientific_settings') or {}).items():
            if rel in changed:
                old = json.loads((ev / 'workspace-before' / rel).read_text())
                new = json.loads((ws / rel).read_text()) if (ws / rel).exists() else {}
                sci += [f'{rel}:{k} {old.get(k)!r} -> {new.get(k)!r}' for k in keys
                        if old.get(k) != new.get(k)]
        if sci and res.returncode == 0 and not bad:
            _restore(ev / 'workspace-before', ws)
            _set_step(cdir, tid, 'agent', {'kind': kind, 'changed': changed,
                                           'refused': 'scientific setting changed', 'settings': sci},
                      'failed')
            record(cdir, {'type': 'decision', 'decision': 'repair refused: it changes a scientific '
                          'setting, which is a new experiment, not a restart', 'task': tid,
                          'settings': sci})
            notify(cdir, brief, f'{tid}: proposed repair changes {sci}; not relaunched as a repair')
            return 'failed'
        if res.returncode != 0 or bad:
            _restore(ev / 'workspace-before', ws)
            why = f'runner exit {res.returncode}' if res.returncode else f'edited outside allowed paths: {bad}'
            _set_step(cdir, tid, 'agent', {'kind': kind, 'changed': changed, 'refused': why}, 'failed')
            notify(cdir, brief, f'{tid}: agent change refused ({why}); workspace restored')
            return 'failed'
        _set_step(cdir, tid, 'agent', {'kind': kind, 'changed': changed, 'exit': res.returncode})
        if stop('agent'):
            return 'interrupted'

    steps = next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']
    if task['task'] in ('repair', 'investigate') and 'test' not in steps:
        if not steps['agent']['changed']:
            _set_step(cdir, tid, 'test', {'skipped': 'no change made'}, 'failed')
            notify(cdir, brief, f'{tid}: agent made no change; not relaunched')
            return 'failed'
        t = subprocess.run(_fmt(brief['repair_test_command'], cdir=str(Path(cdir).resolve()), job=task['key'].split('#')[0]),
                           cwd=ws, capture_output=True, text=True)
        (ev / 'test-output.txt').write_text(t.stdout + t.stderr)
        sci = [l for l in t.stdout.splitlines() if l.startswith('SCIENTIFIC_SETTING_CHANGED')]
        if sci or t.returncode != 0:
            # Keep the refused change as evidence, then put the workspace back.
            if (ws / '.git').exists():
                d = subprocess.run(['git', '-C', str(ws), 'diff'], capture_output=True, text=True)
                (ev / 'refused-change.diff').write_text(d.stdout)
            _restore(ev / 'workspace-before', ws)
        if sci:
            _set_step(cdir, tid, 'test', {'exit': t.returncode, 'refused': sci[0][:500]}, 'failed')
            record(cdir, {'type': 'decision', 'decision': 'repair refused: it changes a scientific '
                          'setting, which is a new experiment, not a restart', 'task': tid,
                          'settings': sci[0][:1000]})
            notify(cdir, brief, f'{tid}: repair refused, scientific setting changed ({sci[0][:200]})')
            return 'failed'
        if t.returncode != 0:
            _set_step(cdir, tid, 'test', {'exit': t.returncode}, 'failed')
            notify(cdir, brief, f'{tid}: repair test failed (exit {t.returncode}); not relaunched')
            record(cdir, {'type': 'decision', 'decision': 'repair rejected by test', 'task': tid})
            return 'failed'
        _set_step(cdir, tid, 'test', {'exit': 0})
        if stop('test'):
            return 'interrupted'

    steps = next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']
    if 'prepare' not in steps:
        with locked_state(cdir) as state:
            state['counters']['attempt'] += 1
            attempt = state['counters']['attempt']
        p = subprocess.run(_fmt(brief['prepare_command'], cdir=str(Path(cdir).resolve()), attempt=attempt,
                                job=task['key'].split('#')[0],
                                cls=(task.get('detail') or {}).get('class') or task['task']), cwd=ws,
                           capture_output=True, text=True)
        if p.returncode != 0:
            _set_step(cdir, tid, 'prepare', {'exit': p.returncode, 'out': p.stderr[-500:]}, 'failed')
            return 'failed'
        _set_step(cdir, tid, 'prepare', {'handoff': p.stdout.strip().splitlines()[-1],
                                         'attempt': attempt})
        if stop('prepare'):
            return 'interrupted'

    steps = next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']
    if 'submit' not in steps:
        result = submit(cdir, steps['prepare']['handoff'], run_handoff)
        if result.get('status') == 'deferred':
            with locked_state(cdir) as state:
                for q in state['queue']:
                    if q['id'] == tid:
                        first = q['steps'].get('deferred_why') != result.get('why')
                        q['steps']['deferred_why'] = result.get('why')
                        q.update(status='pending', claimed_by=None, lease_expires=None)
            if first:
                notify(cdir, brief, f"{tid}: submission deferred ({result.get('why')}); retried on a later pass")
            return 'deferred'
        _set_step(cdir, tid, 'submit', result)
        with locked_state(cdir) as state:
            state['resources']['jobs'].setdefault(task['key'].split('#')[0], {})['superseded_by'] = result['job']
        if stop('submit'):
            return 'interrupted'
    steps = next(q for q in load_state(cdir)['queue'] if q['id'] == tid)['steps']
    record(cdir, {'type': 'decision', 'decision': f"{task['task']} done; relaunched",
                  'task': tid, 'key': task['key'], 'class': task['detail'].get('class'),
                  'changed': steps.get('agent', {}).get('changed'),
                  'runner': steps.get('agent', {}).get('kind'),
                  'job': steps['submit']['job']})
    _set_step(cdir, tid, 'done', True, 'done')
    notify(cdir, brief, f"{tid}: relaunched as {steps['submit']['job']}")
    return 'done'


# ---------------------------------------------------------------- scheduled pass

CREDENTIAL_HINTS = ('unauthorized', 'oidc', 'token', 'login', 'credential', 'forbidden',
                    'you must be logged in', 'refresh')
NETWORK_HINTS = ('unable to connect', 'timeout', 'timed out', 'no route', 'connection refused',
                 'tls handshake', 'eof', 'i/o timeout', 'name resolution')


def kubectl_error_kind(text):
    t = (text or '').lower()
    if any(h in t for h in CREDENTIAL_HINTS):
        return 'credentials'
    if any(h in t for h in NETWORK_HINTS):
        return 'network'
    return 'kubectl'


def tick(cdir, holder, runner=None, records=None, now=None):
    """One scheduled pass (cron): monitor, then at most one task. Overlapping passes are skipped.
    A cluster read failure is reported once per change of state; Jobs keep running on NRP."""
    cdir = Path(cdir)
    with open(cdir / '.tick.lock', 'a+') as lk:
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 'busy'
        brief = load_brief(cdir)
        stamp = iso(now or now_utc())
        try:
            watch_once(cdir, records, now)
        except (subprocess.CalledProcessError, OSError, json.JSONDecodeError) as e:
            text = (getattr(e, 'stderr', None) or str(e)).strip()
            kind = kubectl_error_kind(text)
            first = text.splitlines()[0][:300] if text else type(e).__name__
            with locked_state(cdir) as state:
                mon = state.setdefault('monitor', {})
                changed = mon.get('error_kind') != kind
                mon.update(error_kind=kind, last_error=first, last_error_at=stamp,
                           failures=mon.get('failures', 0) + 1)
                if changed:
                    mon['error_since'] = stamp
            if changed:
                hint = (' An interactive `kubectl oidc-login` on the home PC may be needed.'
                        if kind == 'credentials' else '')
                notify(cdir, brief, f'monitor cannot read the cluster ({kind}): {first}. Jobs keep '
                                    f'running on NRP; monitoring resumes when access returns.{hint}')
            return f'monitor-error:{kind}'
        with locked_state(cdir) as state:
            mon = state.setdefault('monitor', {})
            recovered = mon.get('error_kind')
            mon.update(error_kind=None, last_ok=stamp)
            days = elapsed_days(state)
            notes = state.setdefault('notices', [])
            elapsed_msgs = []
            for key, limit in (('elapsed_warn', brief.get('elapsed_days_warn')),
                               ('elapsed_max', brief.get('elapsed_days_max'))):
                if limit is not None and days is not None and days > limit and key not in notes:
                    notes.append(key)
                    elapsed_msgs.append(f'campaign elapsed {days:.1f} d > {limit} d ({key}; behaviour: '
                                        f"{brief.get('elapsed_behavior') if key == 'elapsed_max' else 'warning'})")
        for m in elapsed_msgs:
            notify(cdir, brief, m)
        if recovered:
            notify(cdir, brief, f'monitor reads the cluster again (was: {recovered}).')
        try:
            return run_task(cdir, holder, runner=runner, now=now) or 'idle'
        except (subprocess.CalledProcessError, GateError, OSError) as e:
            with locked_state(cdir) as state:          # let the next pass retry from the saved steps
                for q in state['queue']:
                    if q['status'] == 'claimed' and q.get('claimed_by') == holder:
                        q.update(status='pending', claimed_by=None, lease_expires=None)
            msg = (getattr(e, 'stderr', None) or str(e)).strip().splitlines()
            notify(cdir, brief, f'task step stopped: {type(e).__name__}: {(msg or [""])[0][:300]}; '
                                'its saved steps resume after the lease expires')
            return 'task-error'


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init'); p.add_argument('campaign_dir'); p.add_argument('--id', required=True)
    p = sub.add_parser('approve', help='Kai only; needs a terminal')
    p.add_argument('campaign_dir'); p.add_argument('--by', required=True)
    p = sub.add_parser('watch', help='one monitor pass')
    p.add_argument('campaign_dir'); p.add_argument('--records', help='saved kubectl List JSON')
    p = sub.add_parser('step', help='claim and run one queued task')
    p.add_argument('campaign_dir'); p.add_argument('--holder', required=True)
    p.add_argument('--runner', choices=['simulated', 'claude', 'codex'])
    p = sub.add_parser('submit'); p.add_argument('campaign_dir'); p.add_argument('handoff_dir')
    p.add_argument('--stage')
    p = sub.add_parser('validate', help='check BRIEF.md policy blocks and the approval')
    p.add_argument('campaign_dir')
    p = sub.add_parser('tick', help='scheduled pass: monitor, then at most one task')
    p.add_argument('campaign_dir'); p.add_argument('--holder', required=True)
    p.add_argument('--runner', choices=['simulated', 'claude', 'codex'])
    a = ap.parse_args(argv)
    if a.cmd == 'init':
        print(' '.join(init_campaign(a.campaign_dir, a.id)) or 'nothing to create')
    elif a.cmd == 'approve':
        print(json.dumps(write_approval(a.campaign_dir, a.by), indent=2))
    elif a.cmd == 'watch':
        doc = json.loads(Path(a.records).read_text()) if a.records else None
        for act in watch_once(a.campaign_dir, doc):
            print(canon(act))
    elif a.cmd == 'step':
        print(run_task(a.campaign_dir, a.holder, runner=a.runner))
    elif a.cmd == 'submit':
        print(canon(submit(a.campaign_dir, a.handoff_dir, stage=a.stage)))
    elif a.cmd == 'validate':
        errs = validate_brief(a.campaign_dir)
        appr = current_approval(a.campaign_dir)
        print(f'authority sha256 {brief_sha(a.campaign_dir)}')
        print(f'operations sha256 {operations_sha(a.campaign_dir)}')
        print('approval: ' + ('matches the authority block (' + appr['approved_by'] + ', ' + appr['approved_at'] + ')'
                              if appr else 'none matching the authority block: submissions refused'))
        for e in errs:
            print('ERROR', e)
        print('VALID' if not errs else f'INVALID ({len(errs)} errors): submissions and agent work refused')
        return 1 if errs else 0
    elif a.cmd == 'tick':
        print(f'{iso(now_utc())} {tick(a.campaign_dir, a.holder, runner=a.runner)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
