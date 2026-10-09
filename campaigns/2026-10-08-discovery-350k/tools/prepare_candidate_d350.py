#!/usr/bin/env python3
"""Prepare (never submit) the search-stage handoff of a candidate node (BRIEF candidate_prepare_command).

python3 tools/prepare_candidate_d350.py <node> <attempt> [--config NAME]

The code is the committed branch cand-<node> of code/ (prepare_attempt.py archives the commit,
never the working tree). The branch must exist and, when it is checked out, the working tree
must be clean. The candidate's config is the one config on that commit whose stem carries the
node id as a '-'-separated token (as in candidate_check_d350.py); --config picks one when
there are several. It must already be frozen in settings/candidate-<node>-fingerprint.json,
which candidate_check_d350.py writes only when every check passed.

The handoff is built by prepare_attempt.py with: --branch cand-<node> --stage search
--stop-epoch 1000 --runtime-factor F, F = the config's campaign.runtime_factor if present,
else 1.3 (PROPOSAL §8). Pod deadline 47 s x 1000 x F (1.3: 61,100 s), Job deadline twice that,
the Job shape and checks of prepare_attempt.py unchanged. The last stdout line is the absolute
handoff directory. Nothing calls kubectl.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d350_common as dc  # noqa: E402
import prepare_attempt  # noqa: E402

DEFAULT_FACTOR = dc.CANDIDATE_RUNTIME_FACTOR   # BRIEF operations candidate_runtime_factor
STOP_EPOCH = 1000
CFG_DIR = 'campaigns/d350/configs'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('node')
    ap.add_argument('attempt', type=int)
    ap.add_argument('--config')
    args = ap.parse_args(argv)
    node = args.node.lower()
    if not re.match(r'^[a-z0-9]+$', node):
        dc.fail(f'node id {args.node!r} must be lowercase letters and digits')
    branch = f'cand-{node}'
    if subprocess.run(['git', '-C', str(dc.CODE), 'rev-parse', '--verify', '-q', f'refs/heads/{branch}'],
                      capture_output=True).returncode != 0:
        dc.fail(f'branch {branch} does not exist in code/')
    commit = dc.resolve(f'refs/heads/{branch}')
    head = subprocess.run(['git', '-C', str(dc.CODE), 'symbolic-ref', '-q', '--short', 'HEAD'],
                          capture_output=True, text=True).stdout.strip()
    if head == branch and dc.git('status', '--porcelain', '--untracked-files=all'):
        dc.fail(f'{branch} is checked out with uncommitted changes; commit them first')
    token = re.compile(rf'(^|-){re.escape(node)}(-|$)')
    names = sorted(p[len(CFG_DIR) + 1:-5] for p in dc.git('ls-tree', '--name-only', commit, f'{CFG_DIR}/').splitlines()
                   if p.endswith('.json') and token.search(p[len(CFG_DIR) + 1:-5]))
    if args.config:
        if args.config not in names:
            dc.fail(f'{args.config} is not a config of node {node} on {branch} ({names})')
        names = [args.config]
    if len(names) != 1:
        dc.fail(f'expected one config of node {node} on {branch} at {commit[:12]}, found {names}; use --config')
    name = names[0]
    if not name.startswith('d350-'):
        dc.fail(f'config {name} does not start with d350-')
    fp_path = dc.CAMP / 'settings' / f'candidate-{node}-fingerprint.json'
    if not fp_path.is_file() or name not in {r['name'] for r in json.loads(fp_path.read_text())}:
        dc.fail(f'{name} has no frozen fingerprint in {fp_path.name}; run candidate_check_d350.py {node} first')
    cfg = json.loads(dc.git('show', f'{commit}:{CFG_DIR}/{name}.json'))
    factor = float((cfg.get('campaign') or {}).get('runtime_factor', DEFAULT_FACTOR))
    note = (f'config {name} added on branch {branch} (candidate node {node}, PROPOSAL.md §6), CPU-gate fingerprint '
            f'frozen in settings/{fp_path.name}; runtime factor {factor!r} '
            f'({"campaign.runtime_factor" if "runtime_factor" in (cfg.get("campaign") or {}) else "PROPOSAL §8 default"}).')
    camp = cfg.get('campaign') or {}
    extra = []
    if camp.get('runtime_justification') or camp.get('timing_evidence'):
        ev = Path(str(camp.get('timing_evidence', '')))
        extra = ['--runtime-justification', str(camp.get('runtime_justification', '')),
                 '--timing-evidence', str(ev if ev.is_absolute() else dc.CAMP / ev)]
    return prepare_attempt.main([name[len('d350-'):], str(args.attempt), '--branch', branch, '--stage', 'search',
                                 '--stop-epoch', str(STOP_EPOCH), '--runtime-factor', repr(factor),
                                 '--config-text', note] + extra)


if __name__ == '__main__':
    raise SystemExit(main())
