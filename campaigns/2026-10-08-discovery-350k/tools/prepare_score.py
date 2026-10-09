#!/usr/bin/env python3
"""Prepare (never submit) the CPU-only readout Job that scores one discovery-350k run.

python3 campaigns/2026-10-08-discovery-350k/tools/prepare_score.py RUN_NAME [--score-attempt 1]
    [--expect-target 350000] [--stop-epoch STOP] [--allow-protected-change REASON]

RUN_NAME is an attempt record name (attempts/<arm>-a<attempt>.json, written by prepare_attempt.py).
The Job runs the frozen eval/score.py (this campaign's eval/, checked against eval/MANIFEST.json,
shipped as /work/code/d350_eval/) on that run's PVC record directory, and writes score-s<k>.json there.
The checkpoint is loaded with the code of the commit that trained the run (its layers must
deserialize); the scoring logic never comes from a candidate branch. Files the proposal protects
from candidate edits (PROPOSAL §6: EBOPs computation and tracing, data and split code, the copied
pilot readout scripts) must be byte-identical to the base commit, or the preparation is refused
unless --allow-protected-change gives a reviewed reason (recorded in the brief and the record).

Job: one pod, no GPU, 8 CPU / 24 GiB (the pilot readout shape, freeze_p.cpu_job), pod and Job
activeDeadlineSeconds 3600, backoffLimit 0. Labels: user=kai, campaign=discovery-350k-20261008,
app=kai-d350-score, bnjettag.io/role=score, bnjettag.io/run=<RUN_NAME>. The pod log ends with the
score line or an `INVALID[<class>]: ...` line (a setup failure before score.py starts prints
`INVALID[infrastructure]: score job setup failed ...`). Writes manifests/score-<RUN_NAME>-s<k>/, handoffs/rh-*,
attempts/score-<RUN_NAME>-s<k>.json; the last stdout line is the absolute handoff directory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d350_common as dc  # noqa: E402

DEADLINE_S = dc.SCORE_DEADLINE_S       # BRIEF operations score_deadline_s
EXPECT_TARGET = 350_000
# PROPOSAL §6 "protected from candidate edits", as files of the code tree (whole files; a candidate that
# must touch one of them needs --allow-protected-change after review)
PROTECTED = ['run_engram.py', 'run_study.py', 'run_pack.py', 'bnhgq2/ebops_calc.py', 'bnhgq2/ebops_target.py',
             'bnhgq2/data.py', 'bnhgq2/compat.py', 'analysis/attn_entropy.py', 'prepare_cache.py',
             'campaigns/pilot1005/readout_pilot.py', 'campaigns/pilot1005/certify_ebops.py',
             'campaigns/pilot1005/nondegenerate_threshold.py', 'campaigns/chang0926/evaluate_roc.py']
# functions of bnhgq2/ablation.py the score depends on (the training loop in the same file is editable)
PROTECTED_FUNCS = ['majority_rule', 'nondegenerate_rule', 'validation_metrics', 'ebops_trace_sample',
                   'ebops_trace_batch', 'ebops_trace_every', 'is_traced_epoch', 'model_ebops', 'stored_state_ebops',
                   'saved_ebops', 'selected_checkpoint_ebops', 'checkpoint_selection_key', 'checkpoint_selection_metric',
                   'prepare_arrays', 'array_hash', 'digest_json']
SETUP_TRAP = ("trap 'rc=$?; echo \"INVALID[infrastructure]: score job setup failed exit=$rc line=${LINENO}\"' EXIT")


def function_sources(path):
    import ast
    text = Path(path).read_text()
    tree = ast.parse(text)
    return {n.name: ast.get_source_segment(text, n) for n in tree.body if isinstance(n, ast.FunctionDef)}


def protected_changes(commit):
    base = dc.base_commit()
    changed = []
    if commit == base:
        return changed
    for rel in PROTECTED:
        a = dc.git('rev-parse', f'{base}:{rel}', check=False)
        b = dc.git('rev-parse', f'{commit}:{rel}', check=False)
        if a != b:
            changed.append(rel)
    with dc.tmpdir() as tmp:
        for ref, name in ((base, 'base.py'), (commit, 'run.py')):
            data = dc.git('show', f'{ref}:bnhgq2/ablation.py')
            (Path(tmp) / name).write_text(data + '\n')
        fa, fb = function_sources(Path(tmp) / 'base.py'), function_sources(Path(tmp) / 'run.py')
        changed += [f'bnhgq2/ablation.py:{f}' for f in PROTECTED_FUNCS if fa.get(f) != fb.get(f)]
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('run_name')
    ap.add_argument('--score-attempt', type=int, default=1)
    ap.add_argument('--expect-target', type=int, default=EXPECT_TARGET,
                    help='the frozen 350,000; the reference arm is scored with 5000000')
    ap.add_argument('--stop-epoch', type=int, help="default the attempt's stop epoch")
    ap.add_argument('--allow-protected-change', metavar='REASON')
    args = ap.parse_args(argv)
    src_path = dc.CAMP / 'attempts' / f'{args.run_name}.json'
    if not src_path.is_file():
        dc.fail(f'no attempt record attempts/{args.run_name}.json')
    src = json.loads(src_path.read_text())
    stop = args.stop_epoch or src['stop_epoch']
    if stop > src['stop_epoch']:
        dc.fail(f'stop epoch {stop} is later than the attempt stop epoch {src["stop_epoch"]}')
    if src['target_ebops'] != args.expect_target:
        dc.fail(f"{args.run_name} target {src['target_ebops']} != --expect-target {args.expect_target}")
    if not src['run_dir'].startswith(dc.PVC_ROOT + '/'):
        dc.fail(f"run dir {src['run_dir']} outside {dc.PVC_ROOT}")
    commit = dc.resolve(src['commit'])
    changed = protected_changes(commit)
    if changed and not args.allow_protected_change:
        dc.fail(f'protected files differ from the base commit: {changed}; review the diff, then pass '
                '--allow-protected-change "<reason>"')
    fp = dc.load_freeze_p()
    manifest = json.loads((dc.EVAL / 'MANIFEST.json').read_text())
    for name, want in manifest['files'].items():
        if dc.sha((dc.EVAL / name).read_bytes()) != want:
            dc.fail(f'eval/{name} differs from eval/MANIFEST.json')
    with dc.tmpdir() as tmp:
        tree = dc.export_tree(commit, Path(tmp) / 'tree')
        if (tree / 'd350_eval').exists():
            dc.fail('the run commit already has a d350_eval/ directory')
        (tree / 'd350_eval').mkdir()
        for name in [*manifest['files'], 'MANIFEST.json']:
            shutil.copyfile(dc.EVAL / name, tree / 'd350_eval' / name)
        payload, files, msha = dc.bundle(fp, tree)
    if msha != src['manifest_sha256']:
        dc.fail('code manifest sha differs from the training attempt (the score would load other code)')
    bundle_sha = dc.sha(payload)
    run_root = src['run_root']
    dc.point_fp(fp, run_root, stop, DEADLINE_S, 'd350,discovery-350k,score')
    name = f"kai-d350-sc-{args.run_name}-s{args.score_attempt}"
    key = f"score-{args.run_name}-s{args.score_attempt}"
    if len(name) > 52:
        dc.fail(f'job name {name} longer than 52 characters')
    dc.check_label(name, 'job name')
    dc.check_label(args.run_name, 'run name')
    cm_name = 'kai-d350-score-' + bundle_sha[:10]
    cm = dc.configmap(fp, cm_name, payload, msha, f"code/ commit {commit} + eval/ MANIFEST "
                                                  f"{dc.sha((dc.EVAL / 'MANIFEST.json').read_bytes())[:12]}")
    cache = f'{fp.DATA_ROOT}/n64/data'
    tail = '\n'.join([
        f'test -f {cache}/READY.json || {{ echo "cache not ready: {cache}"; exit 1; }}',
        f'test -d {src["run_dir"]} || {{ echo "run dir missing: {src["run_dir"]}"; exit 1; }}',
        'trap - EXIT',
        'RC=0',
        f'python -u {dc.EVAL_DIR}/score.py {src["run_dir"]} --stop-epoch {stop} --expect-target {args.expect_target} '
        f'--cache {cache} --code /work/code'
        + (f' --score-attempt {args.score_attempt}' if args.score_attempt > 1 else '')
        + ' > /work/score.out 2>&1 || RC=$?',
        'cat /work/score.out',
        # The result file (secondary measurements) goes to the log between markers, then the score
        # or INVALID line is repeated so it stays the last line.
        f'F={src["run_dir"]}/score-s{args.score_attempt}.json',
        'if [ -f "$F" ]; then echo SCORE_JSON_BEGIN; cat "$F"; echo; echo SCORE_JSON_END; fi',
        'tail -n 1 /work/score.out',
        'exit $RC',
    ]) + '\n'
    script = fp.header(bundle_sha, msha, cpu=True, trap=SETUP_TRAP) + tail
    job = fp.cpu_job(name, 'kai-d350-score', cm_name, script,
                     {'bnjettag.io/purpose': f'discovery-350k score: eval/score.py on {src["run_dir"]} (stop epoch {stop})',
                      'bnjettag.io/run-dir': src['run_dir'], 'bnjettag.io/code-commit': commit,
                      'bnjettag.io/eval-manifest-sha256': dc.sha((dc.EVAL / 'MANIFEST.json').read_bytes())},
                     DEADLINE_S)
    labels = {'user': 'kai', 'campaign': dc.CAMPAIGN_LABEL, 'app': 'kai-d350-score', 'bnjettag.io/role': 'score',
              'bnjettag.io/run': args.run_name}
    job['metadata']['labels'] = dict(labels)
    job['spec']['template']['metadata']['labels'] = dict(labels)
    pod = job['spec']['template']['spec']
    pod['activeDeadlineSeconds'] = DEADLINE_S
    res = pod['containers'][0]['resources']
    assert 'nvidia.com/gpu' not in res['limits'] and 'nvidia.com/gpu' not in res['requests']
    assert job['spec']['backoffLimit'] == 0 and job['spec']['activeDeadlineSeconds'] == DEADLINE_S
    text = pod['containers'][0]['args'][0]
    lines = text.rstrip().splitlines()
    assert ('CUDA_VISIBLE_DEVICES=-1' in text and lines[-1] == 'exit $RC'
            and any(l.startswith('python -u ') and '/score.py ' in l for l in lines))
    brief = {
        'purpose': f'Score run {args.run_name} ({src["config_name"]}) with the frozen discovery-350k evaluator '
                   f'(PROPOSAL.md §4), epochs < {stop}; CPU only.',
        'changes': f'eval/ (MANIFEST.json sha256 {dc.sha((dc.EVAL / "MANIFEST.json").read_bytes())[:12]}) shipped as '
                   f'd350_eval/ beside code/ commit {commit[:12]} (the training commit, needed to load the checkpoint). '
                   'No training; reads the run record and the cache; writes score-s<k>.json into the run directory.'
                   + (f' Protected-file change allowed: {args.allow_protected_change} ({changed}).' if changed else ''),
        'approval_ref': dc.APPROVAL_REF,
        'scientific_gate': {'status': 'cleared', 'reference': dc.GATE_REFERENCE},
        'production_gate': {'status': 'pending', 'reference': 'not a production readout'},
        'runs': [{'name': src['config_name'], 'config_path': f"code/campaigns/d350/configs/{src['config_name']}.json"}],
        'expected_metrics': [{'name': 'score', 'split': f'validation n=62000, epochs < {stop}',
                              'expectation': 'one finite number or INVALID[<class>]: <reason> as the last log line'}],
        'stop_rules': [{'condition': 'any failure, nonzero exit or deadline', 'action': 'existing-runner-guard',
                        'approval_ref': f'score.py exit status; activeDeadlineSeconds {DEADLINE_S}; backoffLimit 0'}],
        'outputs': [f"{src['run_dir']}/score-s{args.score_attempt}.json"],
        'limitations': ['Certification and replay run on CPU (as the pilot readout did); the score is not a result before '
                        'a VERIFY.md.'],
        'decision_ref': 'campaigns/2026-10-08-discovery-350k/PROPOSAL.md §4, §9',
        'study_ref': 'campaigns/2026-10-08-discovery-350k/PROPOSAL.md',
    }
    out = dc.CAMP / 'manifests' / key
    for fname, value in (('configmap.json', cm), ('job.json', job), ('brief.json', brief)):
        dc.write_same(out / fname, dc.enc(value))
    handoff, record_sha, job_sha = dc.run_handoff_prepare(fp, out / 'job.json', out / 'configmap.json', out / 'brief.json')
    record = {'schema': 1, 'key': key, 'run_name': args.run_name, 'score_attempt': args.score_attempt, 'commit': commit,
              'bundle_sha256': bundle_sha, 'manifest_sha256': msha, 'configmap': cm_name,
              'eval_manifest_sha256': dc.sha((dc.EVAL / 'MANIFEST.json').read_bytes()), 'stop_epoch': stop,
              'expect_target': args.expect_target, 'run_dir': src['run_dir'], 'job': name,
              'protected_changes': changed, 'protected_change_reason': args.allow_protected_change,
              'handoff': str(handoff.relative_to(dc.CAMP)), 'record_sha256': record_sha, 'job_json_sha256': job_sha,
              'status': 'prepared_not_submitted'}
    dc.write_same(dc.CAMP / 'attempts' / f'{key}.json', dc.enc(record))
    print('PREPARED_SCORE', args.run_name, name, 'commit', commit[:12], 'bundle', bundle_sha[:12], 'deadline_s', DEADLINE_S)
    print(handoff)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
