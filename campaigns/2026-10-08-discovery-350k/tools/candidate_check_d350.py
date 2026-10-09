#!/usr/bin/env python3
"""Candidate check for this campaign (BRIEF candidate_check_command). Run in code/ on the
candidate branch, with the candidate's change in the working tree (before it is committed).

python3 tools/candidate_check_d350.py <node> [--base REV]

The change is the working tree (tracked edits and untracked, non-ignored files) against REV
(default HEAD, the parent node's commit the branch was created from). Checks, cheapest first:

1. CONFIG_RULE_VIOLATED. The candidate's configs are the files added under
   campaigns/d350/configs/ whose stem contains the node id as a '-'-separated token (node c1:
   d350-c1-...). There must be at least one; no other config may be added, modified or removed;
   every index.json row present at REV must be unchanged. Each candidate config needs an
   index.json row (same name and file, matching config_sha256, unique index) and a pack
   [[index]]; it must keep N=64 (arch.n_part, row n_part), the 350,000 EBOPs target
   (train.ebops.pid.target_ebops, campaign.pilot.budget, row budget and target_ebops), binary
   weights (quant.weight 'binary*', not NB) and the baseline's data split (train.data,
   validation_split, split_seed, arch.pt_gate_gev, arch.n_classes).
2. CERTIFICATION_COVERAGE_MISSING. If the change adds an inference operation (rule in
   detect_inference_ops), tests/test_d350_<node>_certification.py must exist, mention
   certify_ebops and model_ebops (the traced value the PID controller reads), and name every
   detected named operation.
3. GATE_FAILED / SCIENTIFIC_SETTING_CHANGED. campaigns/d350/cpu_gate.py --only <arms> for the
   wave-1 arm and the candidate's arms, run once (the gate filters by index arm, and the
   candidate rows usually share arm 'A'). The gate must pass (its binary gate, EBOPs, reload
   and PID-input assertions included). Every field it reports for d350-baseline-e-350k-s1 and
   d350-reference-e-5m-s1 must equal settings/wave1-fingerprint.json (repair_check_d350.py's
   comparison). If settings/candidate-<node>-fingerprint.json exists and an attempt of the
   candidate config was already prepared, the candidate rows must equal it too.
4. TESTS_FAILED. The certification test, if present, then the copied suite (pytest -q -x tests),
   preflight venv, PYTHONPATH=code, D350_EVAL_DIR=<campaign>/eval (a certification test loads
   eval/certify_ebops.py from there by file path and restores sys.path afterwards).
On success the candidate rows of the gate output are written to
settings/candidate-<node>-fingerprint.json (the same format as wave1-fingerprint.json, so
repair_check_d350.py freezes the candidate against it) and the last line is
CANDIDATE_CHECK_PASS <node> <config>[,<config>...].
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

CDIR = Path(__file__).resolve().parents[1]
PY = '/home/kaimoe/lab/.venvs/preflight-20261001/bin/python'
D350 = 'campaigns/d350'
WAVE1 = ('d350-baseline-e-350k-s1', 'd350-reference-e-5m-s1')
BASELINE = WAVE1[0]
TARGET = 350_000
N_PART = 64
NODE = re.compile(r'^[a-z0-9]+$')
SPLIT_KEYS = (('train', 'data'), ('train', 'validation_split'), ('train', 'split_seed'),
              ('arch', 'pt_gate_gev'), ('arch', 'n_classes'))
EXIT = {'SCIENTIFIC_SETTING_CHANGED': 4, 'GATE_FAILED': 1, 'TESTS_FAILED': 1,
        'CONFIG_RULE_VIOLATED': 5, 'CERTIFICATION_COVERAGE_MISSING': 6}

# --- "new inference operation" detection ---------------------------------------------------
# Applied to the lines the change adds to Python files under bnhgq2/ and campaigns/d350/
# (an untracked file counts as wholly added). Comment lines are ignored except for the marker.
MODEL_FILES = {'bnhgq2/build.py', 'bnhgq2/monolith.py', 'bnhgq2/binarize.py', 'bnhgq2/qat.py',
               'bnhgq2/subln.py', 'bnhgq2/wrap_overflow.py', 'bnhgq2/engram.py'}
R_CLASS = re.compile(r'^\s*class\s+(\w+)\s*\(([^)]*)\)')
R_CLASS_BASE = re.compile(r'Layer|Quantizer|\bQ[A-Z]\w*|keras|Model|Module')
R_WEIGHT = re.compile(r'(?:(\w+)\s*=\s*)?[\w.]*\b(add_weight|add_variable|keras\.Variable|tf\.Variable)\s*\(')
R_QLAYER = re.compile(r'\b(Q[A-Z]\w*)\s*\(')
R_KLAYER = re.compile(r'\b(?:keras\.)?layers\.([A-Z]\w*)\s*\(')
R_OP = re.compile(r'\b(?:keras\.ops|ops|tf\.math|tf|K)\.(\w+)\s*\(')
R_NAME = re.compile(r'\bname\s*=\s*[\'"]([\w./-]+)[\'"]')
R_MARK = re.compile(r'd350-inference-op:\s*([\w./-]+)')


def detect_inference_ops(added, declared=(), new_files=()):
    """added: {repo-relative path: [(line number, text), ...]} of added lines; new_files: paths
    that did not exist at the base.
    Returns a list of {'rule', 'path', 'line', 'what', 'name'}; 'name' is the identifier the
    certification test must mention, or None when the operation has no natural name.

    R1 a new class whose bases mention a Layer, Quantizer, HGQ Q-layer, keras, Model or Module;
    R2 a new trainable/stored variable (add_weight, add_variable, keras.Variable, tf.Variable);
    R3 a new HGQ quantized layer or quantizer instantiation (QDense(, QEinsumDense(, Quantizer( ...);
    R4 a new Keras layer instantiation (layers.Multiply(, keras.layers.Dense( ...);
    R5 a new tensor operation (ops.*, keras.ops.*, tf.*, K.*) in a model-definition file
       (MODEL_FILES or a new file under bnhgq2/);
    R6 an explicit declaration: a 'd350-inference-op: <name>' marker in a changed file, or a
       name listed in a candidate config's campaign.candidate.inference_ops.
    The rule over-reports on purpose: a training-only component it flags (a teacher model)
    still needs the coverage test, which then shows the component is absent at inference."""
    found = []
    for path, lines in sorted(added.items()):
        if not path.endswith('.py') or not (path.startswith('bnhgq2/') or path.startswith(f'{D350}/')):
            continue
        model_file = path in MODEL_FILES or (path.startswith('bnhgq2/') and path in new_files)
        for no, text in lines:
            m = R_MARK.search(text)
            if m:
                found.append({'rule': 'R6', 'path': path, 'line': no, 'what': 'marker', 'name': m.group(1)})
            code = text.split('#', 1)[0]
            if not code.strip():
                continue
            m = R_CLASS.match(code)
            if m and R_CLASS_BASE.search(m.group(2)):
                found.append({'rule': 'R1', 'path': path, 'line': no, 'what': f'class {m.group(1)}', 'name': m.group(1)})
            nm = R_NAME.search(code)
            for m in R_WEIGHT.finditer(code):
                found.append({'rule': 'R2', 'path': path, 'line': no, 'what': m.group(2),
                              'name': nm.group(1) if nm else m.group(1)})
            for m in R_QLAYER.finditer(code):
                found.append({'rule': 'R3', 'path': path, 'line': no, 'what': m.group(1),
                              'name': nm.group(1) if nm else None})
            for m in R_KLAYER.finditer(code):
                found.append({'rule': 'R4', 'path': path, 'line': no, 'what': f'layers.{m.group(1)}',
                              'name': nm.group(1) if nm else None})
            if model_file:
                for m in R_OP.finditer(code):
                    found.append({'rule': 'R5', 'path': path, 'line': no, 'what': m.group(0).rstrip('( '),
                                  'name': None})
    for name in declared:
        found.append({'rule': 'R6', 'path': 'config', 'line': 0, 'what': 'campaign.candidate.inference_ops',
                      'name': str(name)})
    return found


def coverage_problems(test_text, ops):
    """What the certification test fails to mention (static floor; the review judges substance)."""
    missing = [w for w in ('certify_ebops', 'model_ebops') if w not in test_text]
    missing += sorted({o['name'] for o in ops if o['name'] and o['name'] not in test_text})
    return missing


# --- helpers ---------------------------------------------------------------------------------
def stop(prefix, message):
    print(f'{prefix} {message}')
    sys.exit(EXIT[prefix])


def git(code, *args):
    r = subprocess.run(['git', '-C', str(code), *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'git {" ".join(args)}: {r.stderr.strip()}')
    return r.stdout


def at_base(code, base, rel):
    r = subprocess.run(['git', '-C', str(code), 'show', f'{base}:{rel}'], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def changes(code, base):
    """{path: status} for the working tree against base, untracked files as 'A'."""
    out = {}
    for line in git(code, 'diff', '--name-status', '--no-renames', base).splitlines():
        status, path = line.split('\t', 1)
        out[path] = status[0]
    for path in git(code, 'ls-files', '--others', '--exclude-standard').splitlines():
        out[path] = 'A'
    return out


def added_lines(code, base, status):
    added = {}
    tracked = [p for p, s in status.items() if s != 'D' and p.endswith('.py') and at_base(code, base, p) is not None]
    if tracked:
        cur, no = None, 0
        for line in git(code, 'diff', '-U0', '--no-renames', base, '--', *tracked).splitlines():
            if line.startswith('+++ '):
                cur = line[6:] if line.startswith('+++ b/') else None
            elif line.startswith('@@'):
                no = int(re.search(r'\+(\d+)', line).group(1))
            elif line.startswith('+') and cur:
                added.setdefault(cur, []).append((no, line[1:]))
                no += 1
    new = [p for p, s in status.items() if s == 'A' and p.endswith('.py') and at_base(code, base, p) is None]
    for p in new:
        f = code / p
        if f.is_file():
            added[p] = list(enumerate(f.read_text(errors='replace').splitlines(), 1))
    return added, set(new)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def get(cfg, *keys):
    for k in keys:
        if not isinstance(cfg, dict) or k not in cfg:
            return None
        cfg = cfg[k]
    return cfg


def config_rules(code, base, node, status):
    """Returns (candidate index rows, their configs) or stops with CONFIG_RULE_VIOLATED."""
    token = re.compile(rf'(^|-){re.escape(node)}(-|$)')
    cfg_dir = f'{D350}/configs/'
    new_cfgs, bad = [], []
    for path, s in sorted(status.items()):
        if not path.startswith(cfg_dir):
            continue
        name = path[len(cfg_dir):]
        if s == 'A' and at_base(code, base, path) is None and name.endswith('.json') and '/' not in name \
                and token.search(name[:-5]):
            new_cfgs.append(name[:-5])
        else:
            bad.append(f'{path} ({"added outside the node" if s == "A" else {"M": "modified", "D": "removed"}.get(s, s)})')
    if bad:
        stop('CONFIG_RULE_VIOLATED', 'only new configs of node %s may change: %s' % (node, ', '.join(bad)))
    if not new_cfgs:
        stop('CONFIG_RULE_VIOLATED', f'no new config named d350-...{node}... under {cfg_dir}')
    base_index = json.loads(at_base(code, base, f'{D350}/index.json'))['runs']
    index = json.loads((code / D350 / 'index.json').read_text())['runs']
    by_name = {r['name']: r for r in index}
    for r in base_index:
        if by_name.get(r['name']) != r:
            stop('CONFIG_RULE_VIOLATED', f'index.json row {r["name"]} changed or removed')
    for p, s in status.items():
        if p.startswith(f'{D350}/packs/') and s != 'A':
            stop('CONFIG_RULE_VIOLATED', f'{p} {"modified" if s == "M" else "removed"}')
    if len({r['index'] for r in index}) != len(index) or len(by_name) != len(index):
        stop('CONFIG_RULE_VIOLATED', 'index.json has duplicate index or name values')
    extra = sorted(set(by_name) - {r['name'] for r in base_index} - set(new_cfgs))
    if extra:
        stop('CONFIG_RULE_VIOLATED', f'index.json rows without a new config of node {node}: {extra}')
    baseline = json.loads((code / D350 / 'configs' / f'{BASELINE}.json').read_text())
    rows, cfgs = [], {}
    for name in new_cfgs:
        row = by_name.get(name)
        if row is None:
            stop('CONFIG_RULE_VIOLATED', f'{name} has no index.json row')
        data = (code / D350 / 'configs' / f'{name}.json').read_bytes()
        cfg = json.loads(data)
        problems = []
        if row.get('file') != f'{name}.json' or cfg.get('name') != name:
            problems.append('row file / config name do not match the file name')
        if row.get('config_sha256') != sha(data):
            problems.append('config_sha256 differs from the file')
        pack = code / D350 / str(row.get('pack', ''))
        if not pack.is_file() or json.loads(pack.read_text()) != [[row['index']]]:
            problems.append(f'pack {row.get("pack")} missing or not [[{row["index"]}]]')
        if get(cfg, 'arch', 'n_part') != N_PART or row.get('n_part') != N_PART:
            problems.append(f'N must be {N_PART}')
        targets = (get(cfg, 'train', 'ebops', 'pid', 'target_ebops'), get(cfg, 'campaign', 'pilot', 'budget'),
                   row.get('budget'), row.get('target_ebops'))
        if any(t != TARGET for t in targets):
            problems.append(f'EBOPs target must be {TARGET} (config pid, campaign.pilot.budget, row budget, '
                            f'row target_ebops: {targets})')
        weight = str(get(cfg, 'quant', 'weight'))
        if not weight.startswith('binary'):
            problems.append(f'quant.weight {weight!r} is not binary')
        for keys in SPLIT_KEYS:
            if get(cfg, *keys) != get(baseline, *keys):
                problems.append(f'{".".join(keys)} {get(cfg, *keys)!r} differs from the baseline '
                                f'{get(baseline, *keys)!r} (data split is reserved to Kai)')
        if problems:
            stop('CONFIG_RULE_VIOLATED', f'{name}: ' + '; '.join(problems))
        rows.append(row)
        cfgs[name] = cfg
    return rows, cfgs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('node')
    ap.add_argument('--base', default='HEAD')
    args = ap.parse_args()
    node = args.node.lower()
    if not NODE.match(node):
        sys.exit(f'node id {args.node!r} must be lowercase letters and digits')
    cwd = Path.cwd()
    code = cwd if (cwd / D350 / 'cpu_gate.py').is_file() else CDIR / 'code'
    base = git(code, 'rev-parse', '--verify', f'{args.base}^{{commit}}').strip()
    status = changes(code, base)

    rows, cfgs = config_rules(code, base, node, status)
    names = [r['name'] for r in rows]

    declared = [n for c in cfgs.values() for n in (get(c, 'campaign', 'candidate', 'inference_ops') or [])]
    added, new_files = added_lines(code, base, status)
    ops = detect_inference_ops(added, declared, new_files)
    cert_rel = f'tests/test_d350_{node}_certification.py'
    cert = code / cert_rel
    if ops:
        print('INFERENCE_OPS ' + '; '.join(f"{o['rule']} {o['path']}:{o['line']} {o['what']}"
                                           + (f" [{o['name']}]" if o['name'] else '') for o in ops[:20]))
        if not cert.is_file():
            stop('CERTIFICATION_COVERAGE_MISSING', f'{cert_rel} missing; the change adds inference operations '
                 '(see INFERENCE_OPS)')
        missing = coverage_problems(cert.read_text(), ops)
        if missing:
            stop('CERTIFICATION_COVERAGE_MISSING', f'{cert_rel} does not mention: {", ".join(missing)}')

    env = dict(os.environ, PYTHONPATH=str(code), KERAS_BACKEND='tensorflow', D350_EVAL_DIR=str(CDIR / 'eval'))
    wave1 = {r['name']: r for r in json.loads((CDIR / 'settings' / 'wave1-fingerprint.json').read_text())}
    arms = sorted({wave1[n]['arm'] for n in WAVE1} | {r['arm'] for r in rows})
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'gate.json'
        g = subprocess.run([PY, f'{D350}/cpu_gate.py', '--only', ','.join(arms), '--out', str(out)],
                           cwd=code, env=env, capture_output=True, text=True)
        if g.returncode != 0 or not out.exists():
            print(g.stdout[-2000:] + g.stderr[-2000:])
            stop('GATE_FAILED', f'exit={g.returncode} arms={",".join(arms)}')
        now = {r['name']: r for r in json.loads(out.read_text())}

    for name in WAVE1:          # repair_check_d350.py's comparison, per wave-1 config
        if name not in now:
            stop('SCIENTIFIC_SETTING_CHANGED', f'{name}: config no longer produced by the gate')
        diff = sorted(k for k in set(wave1[name]) | set(now[name]) if wave1[name].get(k) != now[name].get(k))
        if diff:
            stop('SCIENTIFIC_SETTING_CHANGED', f'{name}: ' + ', '.join(
                f'{k}: {wave1[name].get(k)!r} -> {now[name].get(k)!r}' for k in diff[:12]))
    for name in names:
        if name not in now or now[name].get('status') != 'PASS':
            stop('GATE_FAILED', f'{name}: no PASS row in the gate output')

    fp_path = CDIR / 'settings' / f'candidate-{node}-fingerprint.json'
    mine = [now[n] for n in names]
    data = (json.dumps(mine, indent=2) + '\n').encode()
    prepared = [p.name for p in (CDIR / 'attempts').glob('*.json')
                if json.loads(p.read_text()).get('config_name') in names]
    if fp_path.exists() and prepared and fp_path.read_bytes() != data:
        frozen = {r['name']: r for r in json.loads(fp_path.read_text())}
        diff = sorted({f'{n}.{k}' for n in names for k in set(frozen.get(n, {})) | set(now[n])
                       if frozen.get(n, {}).get(k) != now[n].get(k)})
        stop('SCIENTIFIC_SETTING_CHANGED', f'{fp_path.name} is frozen (attempts {prepared}); differs in: '
             + ', '.join(diff[:12]))

    if cert.is_file():
        t = subprocess.run([PY, '-m', 'pytest', '-q', '-x', cert_rel], cwd=code, env=env)
        if t.returncode != 0:
            stop('TESTS_FAILED', f'{cert_rel} exit={t.returncode}')
    t = subprocess.run([PY, '-m', 'pytest', '-q', '-x', 'tests'], cwd=code, env=env)
    if t.returncode != 0:
        stop('TESTS_FAILED', f'exit={t.returncode}')

    fp_path.parent.mkdir(exist_ok=True)
    fp_path.write_bytes(data)
    print(f'CANDIDATE_FINGERPRINT {fp_path}')
    print(f'CANDIDATE_CHECK_PASS {node} {",".join(names)}')


if __name__ == '__main__':
    main()
