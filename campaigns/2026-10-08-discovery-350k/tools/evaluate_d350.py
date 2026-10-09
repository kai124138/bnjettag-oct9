#!/usr/bin/env python3
"""Harness evaluate step for one finished training Job of this campaign.

python3 tools/evaluate_d350.py <training job name>

First call: prepares the frozen score Job (tools/prepare_score.py) and submits it through
tools/harness.py submit; prints PENDING. Later calls: PENDING while the score Job runs. When it
has ended (Complete or Failed), its log is saved under evidence/scores/ and its last line read:
- a finite number: writes a metrics file and prints its path (exit 0);
- `INVALID[<class>]: <reason>`: the class comes from the line, else from eval/INVALID_REASONS.json
  by prefix (unmatched reasons count as "evaluator"). A "scientific" or "diverged" INVALID is
  printed (exit 3).
  An "evaluator" or "infrastructure" INVALID gets exactly one more score attempt (PENDING); if
  that is INVALID too, it is printed with its class (exit 3);
- anything else from a Failed score Job (a killed pod): treated as infrastructure, same single
  retry; then exit 2 (evaluation failure, not a result).
"""
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

CDIR = Path(__file__).resolve().parents[1]
ROOT = CDIR.parents[1]
spec = importlib.util.spec_from_file_location('harness', ROOT / 'tools/harness.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
VAL_N = 62000          # frozen validation split (PROPOSAL §3)
MAX_SCORE_ATTEMPTS = 2
INVALID_LINE = re.compile(r'^INVALID(?:\[(?P<cls>[a-z]+)\])?:\s*(?P<reason>.*)$')


def attempt_record(job):
    for p in sorted((CDIR / 'attempts').glob('*.json')):
        rec = json.loads(p.read_text())
        if rec.get('job') == job:
            return rec
    sys.exit(f'no attempt record for job {job}')


def reason_class(reason):
    table = json.loads((CDIR / 'eval' / 'INVALID_REASONS.json').read_text())
    for cls, prefixes in table['classes'].items():
        if any(reason.startswith(p) for p in prefixes):
            return cls
    return 'evaluator'


def submit_score(rec, k):
    out = subprocess.run([sys.executable, str(CDIR / 'tools/prepare_score.py'), rec['run_name'],
                          '--expect-target', str(rec['target_ebops']), '--score-attempt', str(k)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stdout + out.stderr, file=sys.stderr)
        sys.exit(2)
    handoff = Path(out.stdout.strip().splitlines()[-1])
    if not handoff.is_absolute():
        handoff = (ROOT / handoff) if (ROOT / handoff).exists() else (CDIR / handoff)
    score_job = json.loads((handoff / 'job.json').read_text())['metadata']['name']
    r = h.submit(CDIR, handoff, stage='score')
    if r.get('status') == 'deferred':
        print('PENDING')            # e.g. cluster node list unreadable; nothing was created
        sys.exit(0)
    return {'k': k, 'handoff': str(handoff), 'score_job': score_job}


def main():
    job = sys.argv[1]
    rec = attempt_record(job)
    run = rec['run_name']
    sdir = CDIR / 'evidence' / 'scores'
    sdir.mkdir(parents=True, exist_ok=True)
    state_path = sdir / f'{run}.json'
    st = json.loads(state_path.read_text()) if state_path.exists() else {'attempts': []}
    brief = h.load_brief(CDIR)
    if not st['attempts']:
        st['attempts'].append(submit_score(rec, 1))
        h.write_json(state_path, st)
        print('PENDING')
        return
    cur = st['attempts'][-1]
    r = h.kubectl(brief, 'get', 'job', cur['score_job'], '-o', 'json')
    conds = {c['type'] for c in json.loads(r.stdout).get('status', {}).get('conditions', [])
             if c.get('status') == 'True'}
    if not conds & {'Complete', 'Failed'}:
        print('PENDING')
        return
    log = h.kubectl(brief, 'logs', f"job/{cur['score_job']}", '--tail=400', check=False).stdout
    log_path = sdir / f"{run}.s{cur['k']}.log"
    log_path.write_text(log)
    secondary = None
    blk = re.search(r'^SCORE_JSON_BEGIN\n(.*?)\nSCORE_JSON_END$', log, re.S | re.M)
    if blk:
        secondary = sdir / f"{run}.s{cur['k']}.result.json"
        secondary.write_text(blk.group(1).strip() + '\n')
    cur['result_file'] = str(secondary) if secondary else None
    last = next((l.strip() for l in reversed(log.splitlines()) if l.strip()), '')
    m = INVALID_LINE.match(last)
    if m:
        reason = m.group('reason').strip()
        cls = m.group('cls') or reason_class(reason)
    elif 'Complete' in conds:
        try:
            value = float(last)
        except ValueError:
            value = None
        if value is not None and math.isfinite(value):
            metrics = sdir / f'{run}.metrics.json'
            h.write_json(metrics, {'metric': 'best_feasible_val_top1_acc', 'value': value,
                                   'split': 'validation', 'n': VAL_N, 'status': 'unverified',
                                   'run': run, 'job': job, 'score_job': cur['score_job'],
                                   'score_attempt': cur['k'], 'score_log': str(log_path),
                                   'result_file': str(secondary) if secondary else None,
                                   'score_log_sha256': h.sha256_file(log_path)})
            print(metrics)
            return
        cls, reason = 'evaluator', f'score log does not end with a score or INVALID line: {last[:200]!r}'
    else:
        cls, reason = 'infrastructure', f"score job {cur['score_job']} failed without an INVALID line"
    cur.update(result='INVALID', cls=cls, reason=reason)
    if cls in ('evaluator', 'infrastructure') and cur['k'] < MAX_SCORE_ATTEMPTS:
        st['attempts'].append(submit_score(rec, cur['k'] + 1))
        h.write_json(state_path, st)
        print('PENDING')
        return
    h.write_json(state_path, st)
    if not m and 'Failed' in conds and cls == 'infrastructure':
        print(reason, file=sys.stderr)
        sys.exit(2)
    print(f'INVALID[{cls}]: {reason}')
    sys.exit(3)


if __name__ == '__main__':
    main()
