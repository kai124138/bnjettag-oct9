#!/usr/bin/env python3
"""Freeze the pilot-program round-1 tree and prepare (never submit) its Jobs and immutable handoffs.

python3 campaigns/2026-10-05-pilot-program/freeze_p.py            # scientific gate pending (default)
python3 campaigns/2026-10-05-pilot-program/freeze_p.py --only cpugate \
    --gate-cleared '<reviewed gate record>' --approval-ref '<exact Kai authorization>'   # action time only

Modelled on campaigns/2026-10-02-chang-option-c/freeze_c.py (read, never written). Writes under this
directory only:
  manifests/pilot1005-code.tar.gz, configmap.json, bundle-manifest.json
  manifests/cpugate-job.json        CPU gate: threshold, cpu_gate.py on the 23 configs, NB pairing s1-8, full pytest;
                                    fail-fast, last line GATE_RESULT PASS | GATE_RESULT FAIL <reason>
  manifests/r1-<tag>-job.json       23 single-arm GPU Jobs (RTX 3090), epoch-500 pause
  manifests/readout-job.json        CPU readout: a26 entropy, certification, controller audit, readout.json
  manifests/brief-<key>.json        factual handoff briefs (scientific gate pending)
  handoffs/rh-*                     tools/run_handoff.py prepare output (offline)
  PREPARED.json (or PREPARED-cleared-<keys>.json)   names, hashes and handoff IDs
Never calls kubectl. Checks the generated arm table against PROGRAM.json r1_launch (read only): the same
23 (arm, hypothesis, arch, budget, option_c, warmup, seed) rows, and each run's `config_extra` keys
(NB350-C quant.weight, A350-C-qkv1 quant.attn_bit_floor) equal to the generated config.
"""
import base64
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CODE = HERE / 'code' / 'tree'
CAMP_REL = 'campaigns/pilot1005'
CAMP = CODE / CAMP_REL
OUT = HERE / 'manifests'
HIST = REPO / 'campaigns' / '2026-09-26-training-batch' / 'manifests' / 'freeze.py'
EXPORT_INFO = REPO / 'campaigns/2026-10-01-recovery/captures/pvc-20261001T0555Z/chang-n64-20260926/n64/data/data_info.json'
DATA_ROOT = '/data/chang-n64-20260926'                  # the existing gated N64 cache, unchanged
DATA_INFO_PATH = DATA_ROOT + '/n64/data/data_info.json'
PROGRAM_ROOT = DATA_ROOT + '/pilot-program-20261005'      # new: no earlier campaign writes here
ROUND = 'R1'
RUN_ROOT = PROGRAM_ROOT + '/r1'                          # runs/<name>, readout-epoch-0500-<sha6>-r1/
STAGE = 'pilot-r1'                                       # W&B group chang-n64-20261005-pilot-r1 (patch 0038)
CAMPAIGN_DIR = '/work/code/' + CAMP_REL
FP_CAMPAIGN_DIR = '/work/code/campaigns/chang1002c'      # the reviewed fingerprint reference row
FP_RUN = 'chang1002c-a-n64-s1'
IMAGE = 'docker.io/library/python@sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7'
PYTEST = 'pytest==8.4.2'                                 # test runner only; not a training pin
KEY = 'hgq2.tar.gz'
SKIP = ('__pycache__', '.pytest_cache', '.DS_Store', '.git')
LABELS = {'user': 'kai', 'campaign': 'chang-n64-20261005-pilot'}
TAGS = 'pilot1005,pilot-program,r1,option-c-ladder,regime-b,validation-only'
GPU_PRODUCT = ['NVIDIA-GeForce-RTX-3090']                # STUDY §3: one product per round
PER_ARM_CPU = 2
N_ARMS = 23   # b3fb22c8; a tree with a later patch (0042+) carries its own count (index.json, checked vs PROGRAM.json)
PER_ARM_MEMORY_GI = 10      # RSS gate 8,192 MiB + about 2 GiB for pip, monitor and page cache (one arm)
EPHEMERAL_GI = 16
RSS_GATE_LIMIT_MB, RSS_GATE_WINDOW = str(8 * 1024), '5:105'
STOP_AFTER = 500
MONITOR_EVERY_S = 1800
GATE_DEADLINE_S, READOUT_DEADLINE_S = 14400, 28800
# --- Fixes after PREFLIGHT review v1 (opt-in; defaults reproduce the b3fb22 build-half manifests) ---
# A1: certify_ebops.py:120 imports evaluate_roc, which exists only in campaigns/chang0926.
READOUT_PYTHONPATH = '/work/code:/work/code/campaigns/chang0926'
# A2: bound R1 spend. Pod-level activeDeadlineSeconds (counts from pod start, not Job creation).
#   A07 K=1 RTX 3090 (gpu-benchmark VERIFY.md:109): 30.85 s/epoch -> 500 ep 15,425 s (4.3 h);
#   total elapsed 38.8 s per run-epoch -> 19,400 s (5.4 h), the pessimistic bound. Pre-arm (pip +
#   fingerprint) about 4-5 min (training-batch ONBOARDING.md:31). E at K=1 is unmeasured.
#   Worst case per arm: PREARM_RETRY_S (one early retry) + POD_DEADLINE_S + GRACE (backstop kill)
#   = 600 + 20,800 + 180 = 21,580 s; x 23 = 496,340 s = 137.87 GPU-h <= 138 (STUDY §11).
POD_DEADLINE_S = 20800
PREARM_RETRY_S = 600         # a failure before run_pack starts and within this many s of script start is retryable
RESERVE_S = 420              # run_pack's own timeout ends this long before the pod deadline
KILL_AFTER_S = 150           # timeout: SIGTERM, then SIGKILL after this (run_pack's child grace is 120 s)
BACKOFF_PER_INDEX_BOUNDED = 1
EXIT_RSS_GATE, EXIT_ARM_FINAL, EXIT_PREARM_RETRY, EXIT_ARM_DEADLINE = 5, 76, 75, 124
FINAL_EXIT_CODES = [EXIT_RSS_GATE, EXIT_ARM_FINAL, EXIT_ARM_DEADLINE, 137, 143]   # 137/143: pod-deadline kill of PID 1
OPTS = {'readout_pythonpath': False, 'bounded': False, 'diag': False}
# F5 (STUDY_arbiter_v1; constructive A2/A3): readout_diag.json, descriptive only, never a rule input and never
# read by readout_pilot.py or PROGRAM.json. Standard library; runs after readout.json is written; its exit
# status does not enter the Job's exit status.
DIAG_PY = r"""
import json, os, statistics, sys
from pathlib import Path
run_root, index_path, out_dir, epoch = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
rows = [r for r in json.loads(index_path.read_text())['runs'] if r['round'] == 'R1']
Q, K = '_attn_scores__in0', '_attn_scores__in1'

def zero(bits):
    flat = bits if isinstance(bits, list) else [bits]
    while flat and isinstance(flat[0], list):
        flat = [x for sub in flat for x in sub]
    return bool(flat) and all(float(x) == 0.0 for x in flat)

def mean(bits):
    flat = bits if isinstance(bits, list) else [bits]
    while flat and isinstance(flat[0], list):
        flat = [x for sub in flat for x in sub]
    return sum(map(float, flat)) / len(flat) if flat else None

def group(layer):
    if layer.endswith('_attn_softmax'):
        return 'softmax_tables'
    if '_attn_' in layer:
        return 'attention_nonsoftmax'
    if 'ffn' in layer:
        return 'ffn'
    if 'input_proj' in layer or 'embed' in layer:
        return 'input_proj'
    return 'head_and_other'

def a26_mean(path):
    if not path.is_file():
        return None, None
    d = json.loads(path.read_text())
    r = (d.get('runs') or [{}])[0]
    if r.get('status') != 'ok':
        return None, r.get('status')
    heads = [h['entropy_over_log_n'] for blk in r['entropy'].values() for h in blk['heads']]
    return (sum(heads) / len(heads) if heads else None), {'checkpoint': r.get('checkpoint'), 'heads': heads,
                                                         'checkpoint_sha256': r.get('checkpoint_sha256')}

arms = []
for row in rows:
    name, run = row['name'], run_root / row['name']
    entry = {'name': name, 'arm': row['program_arm'], 'seed': row['seed'], 'budget': row['budget']}
    recs = []
    path = run / 'activation_widths.jsonl'
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if int(r['epoch']) < epoch:
                    recs.append(r)
    entry['epochs_read'] = len(recs)
    t_uniform, first_zero = None, {}
    for r in recs:
        widths = r.get('widths') or {}
        blocks = {}
        for site, w in widths.items():
            if site.startswith('bit_block_') and (site.endswith(Q) or site.endswith(K)):
                blk = site[len('bit_block_'):-len(Q)]
                blocks.setdefault(blk, []).append(zero(w.get('bits')))
            m = mean(w.get('bits'))
            if m == 0.0 and site not in first_zero:
                first_zero[site] = r['epoch']
        if t_uniform is None and blocks and all(any(v) for v in blocks.values()):
            t_uniform = r['epoch']
    entry['t_uniform'] = t_uniform          # first epoch: in every block Q or K at 0 bits on all channels
    traced = [r for r in recs if r.get('ebops_traced', 1) == 1 and r.get('ebops') is not None]
    t_budget = next((r['epoch'] for r in traced if r['ebops'] <= row['budget']), None)
    entry['t_budget'] = t_budget            # first traced epoch meeting (a)
    sites = sorted({s for r in recs for s in (r.get('widths') or {})})
    entry['site_order'] = sorted([[s, first_zero.get(s)] for s in sites],
                                 key=lambda x: (x[1] is None, x[1] if x[1] is not None else 0, x[0]))
    state, sel, which = {}, None, None
    sp = run / 'snapshots' / f'epoch-{epoch:04d}' / 'state.json'
    if sp.is_file():
        state = json.loads(sp.read_text())
    if state.get('best_feasible'):
        sel, which = state['best_feasible']['epoch'], 'best_feasible'
    elif traced:
        sel, which = min(traced, key=lambda r: (r['ebops'], r['epoch']))['epoch'], 'min_traced_ebops'
    rec = next((r for r in recs if r['epoch'] == sel), None)
    split = {}
    if rec and rec.get('per_layer'):
        for layer, v in rec['per_layer'].items():
            split[group(layer)] = split.get(group(layer), 0.0) + float(v)
    total = sum(split.values())
    entry['cost_split'] = {'epoch': sel, 'checkpoint': which, 'ebops_total': total or None,
                           'share_of_budget': {g: v / row['budget'] for g, v in sorted(split.items())},
                           'share_of_total': {g: (v / total if total else None) for g, v in sorted(split.items())}}
    ratio = [r['ebops_in_training_over_traced'] for r in recs
             if r.get('ebops_in_training_over_traced') is not None and r.get('pid_stepped', 1) == 1]
    entry['controller_error'] = {'n': len(ratio), 'median': statistics.median(ratio) if ratio else None,
                                 'max': max(ratio) if ratio else None,
                                 'definition': 'ebops_in_training_over_traced over stepped traced epochs'}
    if row.get('variant') == 'nb':
        wb = {r['epoch']: r.get('weight_bits_mean') for r in recs}
        entry['nb_weight_bits_mean'] = {'at_t_budget': wb.get(t_budget), f'at_epoch_{epoch - 1}': wb.get(epoch - 1)}
    last = next((r for r in recs if r['epoch'] == epoch - 1), None)
    m, info = a26_mean(out_dir / f'a26-last-{name}.json')
    entry['last_epoch'] = {'epoch': epoch - 1, 'val_categorical_accuracy': last and last.get('val_categorical_accuracy'),
                           'val_macro_auc': last and last.get('val_macro_auc'), 'attn_entropy_norm_mean': m, 'a26': info}
    m, info = a26_mean(out_dir / f'a26-unc-{name}.json')
    if info is not None or (out_dir / f'a26-unc-{name}.json').exists():
        entry['unconstrained'] = {'best_auc_point': state.get('best_auc'), 'attn_entropy_norm_mean': m, 'a26': info}
    arms.append(entry)
out = {'descriptive_only': True, 'rule_input': False, 'epoch': epoch, 'split': 'validation (a26), training logs',
       'source': 'STUDY_arbiter_v1 F5; STUDY_constructive_v1 A2 items 1-6, A3', 'arms': arms}
tmp = out_dir / 'readout_diag.json.tmp'
tmp.write_text(json.dumps(out, indent=1, allow_nan=False) + '\n')
os.replace(tmp, out_dir.parent / 'readout_diag.json')
print('READOUT_DIAG_WROTE', out_dir.parent / 'readout_diag.json', 'arms', len(arms), flush=True)
"""
APPROVAL = ('PENDING launch authorization; program approval .claude/memory/decisions.md 2026-10-05 10:08 JST '
            '(PROGRAM.json not yet signed)')
SINGLE_ARM = ('campaigns/2026-09-29-gpu-benchmark/VERIFY.md:109: RTX 3090 A07 K=1 GPU util 61.6 % all / 74.3 % '
              'steady (1 arm x 20 epochs), peak 8,484 / 24,576 MiB; one arm per GPU is the approved pilot shape '
              '(decisions.md 2026-10-05 10:08 item 2). E at K=1 is unmeasured: utilization is checked 30 min '
              'after launch (PILOT_PROGRAM.md §4).')

# Patches after 0041 in patches/PATCHES.json (e.g. 0042, the F2 24-arm configs). Appended to the provenance strings;
# empty for b3fb22c8, whose manifests are then reproduced byte for byte.
_ORDER = [o['file'][:4] for o in json.loads((HERE / 'patches' / 'PATCHES.json').read_text())['order']]
EXTRA_PATCHES = _ORDER[_ORDER.index('0041') + 1:]
EXTRA_TXT = ''.join(f' + {x}' for x in EXTRA_PATCHES)

sys.dont_write_bytecode = True   # importing the historical freeze.py must not write into its campaign


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)       # module level only defines constants; main() is not run
    return module


H = load(HIST, 'chang0926_freeze')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def build_tarball():
    entries = sorted((p.relative_to(CODE).as_posix(), p) for p in CODE.rglob('*')
                     if not any(part in SKIP for part in p.relative_to(CODE).parts))
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for rel, path in entries:
            info = tarfile.TarInfo('code/' + rel)
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, '', ''
            if path.is_dir():
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                archive.addfile(info)
            else:
                data = path.read_bytes()
                info.size, info.mode = len(data), 0o755 if path.stat().st_mode & 0o111 else 0o644
                archive.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0, compresslevel=9) as gz:
        gz.write(raw.getvalue())
    return out.getvalue(), [(rel, p) for rel, p in entries if p.is_file()]


def manifest_sha():
    """run_study.manifest() construction over this tree and the pinned training versions."""
    pins = {}
    for line in (CODE / 'requirements-training.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split('==')
            pins[name.split('[')[0].strip()] = version.strip()
    versions = {k: pins[k] for k in ('tensorflow', 'keras', 'hgq2', 'quantizers', 'numpy', 'scikit-learn')}
    paths = sorted(CODE.glob('*.py')) + sorted((CODE / 'bnhgq2').glob('*.py'))
    result = {'files': {str(p.relative_to(CODE)): sha(p.read_bytes()) for p in paths}, 'versions': versions}
    return sha(json.dumps(result, sort_keys=True).encode())


def check_campaign():
    index = json.loads((CAMP / 'index.json').read_text())
    rows = index['runs']
    assert index['count'] == len(rows) and (len(rows) == N_ARMS or EXTRA_PATCHES) and index['round'] == ROUND
    for row in rows:
        data = (CAMP / 'configs' / row['file']).read_bytes()
        assert sha(data) == row['config_sha256'], row['file']
        cfg = json.loads(data)
        eb = cfg['train']['ebops']
        assert ('pid_input' in eb) == row['option_c'] and eb['pid']['warmup'] == row['warmup']
        assert eb['pid']['target_ebops'] == row['budget'] and cfg['train']['ebops_trace_every'] == 10
        assert cfg['experiment']['group'] == 'chang-n64-20261005'
        assert json.loads((CAMP / row['pack']).read_text()) == [[row['index']]]
    # the arm table must equal the draft PROGRAM.json r1_launch runs (read only)
    program = json.loads((HERE / 'PROGRAM.json').read_text())
    launch = next(s for s in program['steps'] if s['id'] == 'r1_launch')
    keys = ('arm', 'hypothesis', 'arch', 'budget', 'option_c', 'warmup', 'seed')
    want = sorted(tuple(r[k] for k in keys) for r in launch['runs'])
    got = sorted((r['program_arm'], r['hypothesis'], r['arch_name'], r['budget'], r['option_c'], r['warmup'], r['seed'])
                 for r in rows)
    assert got == want, ('arm table differs from PROGRAM.json r1_launch', set(got) ^ set(want))
    by_key = {(r['program_arm'], r['seed']): r for r in rows}
    for run in launch['runs']:
        cfg = json.loads((CAMP / 'configs' / by_key[(run['arm'], run['seed'])]['file']).read_text())
        for dotted, value in run.get('config_extra', {}).items():
            block, key = dotted.split('.')
            assert cfg[block].get(key) == value, (run['arm'], run['seed'], dotted)
    return rows


def header(bundle, msha, cpu, trap=None):
    lines = ['set -euo pipefail']
    if trap:
        lines.append(trap)
    lines += [
        'export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2',
        'export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1',
        'mkdir -p /work/code',
        f"echo '{bundle}  /cmcode/{KEY}' | sha256sum -c -",
        f'tar -xzf /cmcode/{KEY} -C /work/code --strip-components=1',
        'export PYTHONPATH=/work/code',
        f'export BNJ_DATA_ROOT={DATA_ROOT} BNJ_RUN_ROOT={RUN_ROOT} BNJ_CAMPAIGN_DIR={CAMPAIGN_DIR}',
        f'export BNJ_STAGE={STAGE}',
    ]
    if cpu:
        lines += ['export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled',
                  'pip install -q --no-cache-dir -r /work/code/requirements-cpu.txt']
    else:
        lines += [
            'export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0',
            'unset WANDB_PROJECT',
            'export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_MODE=online',
            f'export WANDB_TAGS={TAGS}',
            f'export BNJ_RSS_GATE_LIMIT_MB={RSS_GATE_LIMIT_MB} BNJ_RSS_GATE_WINDOW={RSS_GATE_WINDOW}',
            'export WANDB_DIR=/work WANDB_CACHE_DIR=/work/wandb-cache WANDB_DATA_DIR=/work/wandb-data '
            'WANDB_DISABLE_CODE=true WANDB_QUIET=true',
            'pip install -q --no-cache-dir -r /work/code/requirements-training.txt',
            'NVLIBS=$(python -c "import glob; print(\':\'.join(sorted(glob.glob(\'/usr/local/lib/python*/'
            'site-packages/nvidia/*/lib\'))))")',
            'export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        ]
    lines += [
        'cd /work/code',
        'MSHA=$(python -c "import run_study; print(run_study.manifest()[\'sha256\'])")',
        f'test "$MSHA" = "{msha}" || {{ echo "MANIFEST_SHA_MISMATCH $MSHA"; exit 1; }}',
        'echo "MANIFEST_SHA_OK $MSHA"',
        'export BNHGQ2_CODE_SHA256="$MSHA"',
    ]
    return '\n'.join(lines) + '\n'


# CPU gate: any nonzero exit before the PASS line prints `GATE_RESULT FAIL exit=<rc> line=<n>` last.
GATE_TRAP = ("trap 'rc=$?; if [ -z \"${GATE_RESULT_PRINTED:-}\" ]; then echo \"GATE_RESULT FAIL exit=$rc "
             "line=${LINENO}\"; fi' EXIT")


def cpugate_tail(bundle):
    out = f'{PROGRAM_ROOT}/cpu-gate-{bundle[:6]}-r1'
    check = f'python -u {CAMPAIGN_DIR}/gate_check.py'
    return '\n'.join([
        'gate_fail() { GATE_RESULT_PRINTED=1; echo "GATE_RESULT FAIL $*"; exit 1; }',
        f'OUT={out}',
        'test ! -e "$OUT" || gate_fail "output_exists $OUT"',
        f'mkdir -p {PROGRAM_ROOT} && mkdir "$OUT"',
        f'test -f {DATA_ROOT}/n64/data/READY.json || gate_fail "cache_not_ready"',
        f'pip install -q --no-cache-dir {PYTEST}',
        'pip freeze > "$OUT/pip-freeze.txt"',
        # 1. threshold (c) and the validation labels sha, re-derived from the cache (seconds)
        f'TH=0; python -u {CAMPAIGN_DIR}/nondegenerate_threshold.py --cache {DATA_ROOT}/n64/data '
        '--out "$OUT/threshold.json" > "$OUT/threshold.log" 2>&1 || TH=$?',
        'test "$TH" = 0 || gate_fail "threshold_script exit=$TH"',
        f'{check} threshold --json "$OUT/threshold.json" || gate_fail "threshold_mismatch"',
        # 2. build / one step / reload / floors / PID schedule / matched init on the 23 configs
        f'GATE=0; python -u {CAMPAIGN_DIR}/cpu_gate.py --out "$OUT/cpu_gate.json" > "$OUT/cpu_gate.log" 2>&1 || GATE=$?',
        'grep -E "PID_TRACED_ONLY_OK|PID_HISTORICAL_INPUT_OK|PAIRED_INIT_OK|PREFLIGHT_ALL_PASS|Error|assert" '
        '"$OUT/cpu_gate.log" | tail -n 60 || true',
        f'{check} cpu-gate --log "$OUT/cpu_gate.log" --exit-code "$GATE" || gate_fail "cpu_gate exit=$GATE"',
        # 3. [A22] NB initial kernels equal A's at seeds 1-8
        f'NBP=0; python -u {CAMPAIGN_DIR}/pair_nb.py --out "$OUT/nb_pairing.json" > "$OUT/nb_pairing.log" 2>&1 || NBP=$?',
        'grep -E "^NB_" "$OUT/nb_pairing.log" || true',
        f'{check} nb-pairing --log "$OUT/nb_pairing.log" --exit-code "$NBP" || gate_fail "nb_pairing exit=$NBP"',
        # 4. full unit suite: exactly the 2 known skips, everything else passed, exact count
        'PT=0; python -m pytest -q -p no:cacheprovider -rs --junitxml "$OUT/pytest.xml" tests analysis '
        '> "$OUT/pytest.log" 2>&1 || PT=$?',
        'tail -n 30 "$OUT/pytest.log"',
        f'{check} pytest --junit "$OUT/pytest.xml" --exit-code "$PT" || gate_fail "pytest exit=$PT"',
        'sha256sum "$OUT"/*',
        'echo "CPU_GATE_DONE threshold_exit=$TH cpu_gate_exit=$GATE nb_pairing_exit=$NBP pytest_exit=$PT"',
        'GATE_RESULT_PRINTED=1',
        'echo "GATE_RESULT PASS"',
    ]) + '\n'


def pod_exit_trap():
    """A2: classify every nonzero pod exit into final (FailIndex) or retryable, in the EXIT trap.
    0 and the epoch-0 FailJob code pass through. ARM_FINAL_RC (deadline 124, RSS gate 5) is final.
    A failure before run_pack starts, within PREARM_RETRY_S of script start, exits 75 (retryable,
    counts against backoffLimitPerIndex). Anything else exits 76 (final)."""
    return '\n'.join([
        'T0=$(date +%s); ARM_PHASE=pre; ARM_FINAL_RC=""',
        'pod_exit() { rc=$?; trap - EXIT; el=$(( $(date +%s) - T0 )); '
        f'if [ "$rc" = 0 ] || [ "$rc" = {H.EXIT_EPOCH0_ALL_DIVERGED} ]; then exit "$rc"; fi; '
        'if [ -n "$ARM_FINAL_RC" ]; then echo "POD_EXIT_FINAL rc=$rc exit=$ARM_FINAL_RC elapsed_s=$el"; exit "$ARM_FINAL_RC"; fi; '
        f'if [ "$ARM_PHASE" = pre ] && [ "$el" -lt {PREARM_RETRY_S} ]; then '
        f'echo "POD_EXIT_RETRYABLE rc=$rc phase=pre elapsed_s=$el exit={EXIT_PREARM_RETRY}"; exit {EXIT_PREARM_RETRY}; fi; '
        f'echo "POD_EXIT_FINAL rc=$rc phase=$ARM_PHASE elapsed_s=$el exit={EXIT_ARM_FINAL}"; exit {EXIT_ARM_FINAL}; }}',
        'trap pod_exit EXIT',
    ])


def run_pack_line(name):
    if not OPTS['bounded']:
        return [f'python -u /work/code/run_pack.py "$PACKS" {STOP_AFTER} || RP=$?']
    return [
        'ARM_PHASE=train',
        f'ARM_BUDGET_S=$(( {POD_DEADLINE_S} - ($(date +%s) - T0) - {RESERVE_S} ))',
        f'echo "ARM_DEADLINE pod_deadline_s={POD_DEADLINE_S} run_pack_budget_s=$ARM_BUDGET_S"',
        f'if [ "$ARM_BUDGET_S" -le 0 ]; then ARM_FINAL_RC={EXIT_ARM_DEADLINE}; echo "ARM_DEADLINE_EXCEEDED {name} before_start"; '
        f'exit {EXIT_ARM_DEADLINE}; fi',
        'TS=$(date +%s)',
        f'timeout --signal=TERM --kill-after={KILL_AFTER_S} "$ARM_BUDGET_S" python -u /work/code/run_pack.py "$PACKS" '
        f'{STOP_AFTER} || RP=$?',
        'if [ "$RP" = 124 ] || { [ "$RP" = 137 ] && [ $(( $(date +%s) - TS )) -ge "$ARM_BUDGET_S" ]; }; then '
        f'ARM_FINAL_RC={EXIT_ARM_DEADLINE}; echo "ARM_DEADLINE_EXCEEDED {name} run_pack_exit=$RP budget_s=$ARM_BUDGET_S"; fi',
        f'if [ "$RP" != 0 ] && [ -z "$ARM_FINAL_RC" ] && test -f {RUN_ROOT}/runs/{name}/RSS_GATE_FAIL.json; then '
        f'ARM_FINAL_RC={EXIT_RSS_GATE}; echo "ARM_RSS_GATE_FINAL {name} run_pack_exit=$RP"; fi',
    ]


def monitor_loop(name):
    """Notify-only, standard library: every MONITOR_EVERY_S the warmup-aware canary/controller reader
    runs on the arm's telemetry and prints into the pod log. Never kills."""
    t = f'{RUN_ROOT}/runs/{name}/pid_telemetry.jsonl'
    return (f'( while sleep {MONITOR_EVERY_S}; do test -s {t} || continue; '
            f'python -u {CAMPAIGN_DIR}/monitor_p.py --config {CAMPAIGN_DIR}/configs/{name}.json --telemetry {t} '
            f'| sed "s/^/MONITOR /" || echo "MONITOR_ERROR {name}"; done ) &\nMON=$!\n')


def pilot_tail(row):
    name = row['name']
    t = f'{RUN_ROOT}/runs/{name}/pid_telemetry.jsonl'
    lines = [
        'python -c "import tensorflow as tf; assert tf.config.list_physical_devices(\'GPU\'); print(\'GPU_GATE_PASS\')"',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true',
        'df -h /data',
        f"echo '{H.FP_SHA}  {H.FP_MOUNT}/fingerprint_check.py' | sha256sum -c -",
        'FP=0',
        f'python -u {H.FP_MOUNT}/fingerprint_check.py --run {FP_RUN} --expect {H.FP_EXPECT} --data-root {DATA_ROOT} '
        f'--campaign-dir {FP_CAMPAIGN_DIR} --env-report || FP=$?',
        'if [ "$FP" != 0 ]; then echo "FINGERPRINT_GATE_FAIL exit=$FP node=${NODE_NAME:-na}; no arm started"; exit "$FP"; fi',
        '( while sleep 60; do echo "GPU_SAMPLE $(date -u +%FT%TZ) $(nvidia-smi --query-gpu=utilization.gpu,'
        'memory.used,memory.total --format=csv,noheader,nounits | tr -d \' \')"; done ) &',
        'SMI=$!',
    ]
    lines.append(monitor_loop(name).rstrip('\n') if row['option_c'] else 'MON=""   # no option (c): no controller telemetry')
    lines += [
        f'PACKS={row["pack"]}',
        'RP=0; E0=0',
    ]
    lines += run_pack_line(name)
    lines += [
        'kill "$SMI" $MON 2>/dev/null || true',
        H.EPOCH0_CHECK,
        f'if [ "$E0" = {H.EXIT_EPOCH0_ALL_DIVERGED} ]; then echo "POD_EPOCH0_ALL_DIVERGED node=${{NODE_NAME:-na}} '
        f'run_pack_exit=$RP"; exit {H.EXIT_EPOCH0_ALL_DIVERGED}; fi',
        'if [ "$E0" != 0 ]; then echo "PACK_EPOCH0_CHECK_ERROR $E0"; fi',
    ]
    if row['option_c']:
        lines.append(f'test -s {t} && python -u {CAMPAIGN_DIR}/monitor_p.py --config {CAMPAIGN_DIR}/configs/{name}.json '
                     f'--telemetry {t} | sed "s/^/FINAL /" || echo "FINAL_MONITOR_MISSING {name}"')
    lines += [f'echo "PILOT_ARM_DONE {name} run_pack_exit=$RP"', 'exit "$RP"']
    return '\n'.join(lines) + '\n'


def readout_tail(rows, bundle):
    snap = f'snapshots/epoch-{STOP_AFTER:04d}'
    out = f'{RUN_ROOT}/readout-epoch-{STOP_AFTER:04d}-{bundle[:6]}-r1'
    names = ' '.join(r['name'] for r in rows)
    c_names = ' '.join(r['name'] for r in rows if r['option_c'])
    indices = ' '.join(str(r['index']) for r in rows)
    pre = ([f'export PYTHONPATH={READOUT_PYTHONPATH}   # A1: certify_ebops.py:120 imports evaluate_roc (chang0926)',
            'python -c "import evaluate_roc; print(\'READOUT_IMPORT_OK evaluate_roc\', evaluate_roc.__file__)"']
           if OPTS['readout_pythonpath'] else [])
    return '\n'.join(pre + [
        f'OUT={out}',
        'test ! -e "$OUT" || { echo "READOUT_OUTPUT_EXISTS $OUT"; exit 1; }',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        'mkdir "$OUT" "$OUT/controller"',
        f'for n in {names}; do d={RUN_ROOT}/runs/$n; if test -f "$d/{snap}/state.json"; then echo "READOUT_PRESENT $n"; '
        'elif test -f "$d/DIVERGED.json"; then echo "READOUT_DIVERGED $n"; else echo "READOUT_MISSING $n"; fi; done',
        'A26=0; CERT=0; MONC=0; RO=0',
        f'python -u /work/code/analysis/attn_entropy.py --indices {indices} --epoch {STOP_AFTER} '
        f'--out "$OUT/a26-entropy-epoch-{STOP_AFTER:04d}.json" || A26=$?',
        f'python -u {CAMPAIGN_DIR}/certify_ebops.py --run-root {RUN_ROOT}/runs --cache {DATA_ROOT}/n64/data '
        f'--out "$OUT/certify-snapshot-{STOP_AFTER:04d}.json" --snapshot {STOP_AFTER} || CERT=$?',
        f'for n in {c_names}; do t={RUN_ROOT}/runs/$n/{snap}/pid_telemetry.jsonl; '
        f'if test -s "$t"; then python -u {CAMPAIGN_DIR}/monitor_p.py --config {CAMPAIGN_DIR}/configs/$n.json '
        '--telemetry "$t" --json "$OUT/controller/controller-$n.json" || MONC=1; else echo "TELEMETRY_MISSING $n"; MONC=1; fi; done',
        f'python -u {CAMPAIGN_DIR}/readout_pilot.py --run-root {RUN_ROOT}/runs --round {ROUND} --bundle-sha256 {bundle} '
        f'--a26 "$OUT/a26-entropy-epoch-{STOP_AFTER:04d}.json" --cert "$OUT/certify-snapshot-{STOP_AFTER:04d}.json" '
        f'--controller-dir "$OUT/controller" --epoch {STOP_AFTER} --out "$OUT/readout.json" || RO=$?',
    ] + (diag_lines(rows) if OPTS['diag'] else []) + [
        'sha256sum "$OUT"/*.json "$OUT"/controller/*.json 2>/dev/null || true',
        'echo "READOUT_JOB_DONE a26_exit=$A26 certify_exit=$CERT controller_exit=$MONC readout_exit=$RO out=$OUT/readout.json"',
        'test "$RO" = 0 && test "$A26" = 0 && test "$CERT" = 0 && test "$MONC" = 0',
    ]) + '\n'


def diag_lines(rows):
    """F5: a26 on checkpoints/epoch-0500/model.keras for every row, and on the snapshot's
    model_unconstrained.keras for every E row and A07-5000k-C; then DIAG_PY. Never fails the Job."""
    snap = f'snapshots/epoch-{STOP_AFTER:04d}'
    last = f'checkpoints/epoch-{STOP_AFTER:04d}/model.keras'
    a26 = '/work/code/analysis/attn_entropy.py'
    lines = ['DIAG=0; mkdir -p "$OUT/diag"']
    for r in rows:
        d = f"{RUN_ROOT}/runs/{r['name']}"
        lines.append(f'test -f {d}/{last} && {{ python -u {a26} --indices {r["index"]} --checkpoint {d}/{last} '
                     f'--out "$OUT/diag/a26-last-{r["name"]}.json" > "$OUT/diag/a26-last-{r["name"]}.log" 2>&1 || DIAG=1; }} '
                     f'|| echo "DIAG_LAST_MISSING {r["name"]}"')
        if r['arch_name'] == 'E' or r['program_arm'] == 'A07-5000k-C':
            lines.append(f'test -f {d}/{snap}/model_unconstrained.keras && {{ python -u {a26} --indices {r["index"]} '
                         f'--checkpoint {d}/{snap}/model_unconstrained.keras --out "$OUT/diag/a26-unc-{r["name"]}.json" '
                         f'> "$OUT/diag/a26-unc-{r["name"]}.log" 2>&1 || DIAG=1; }} || echo "DIAG_UNC_MISSING {r["name"]}"')
    lines += [f"python - {RUN_ROOT}/runs {CAMPAIGN_DIR}/index.json \"$OUT/diag\" {STOP_AFTER} <<'DIAGPY' || DIAG=1",
              DIAG_PY.strip('\n'), 'DIAGPY',
              'echo "READOUT_DIAG_DONE diag_exit=$DIAG (descriptive only; not part of the Job exit status)"']
    return lines


MOUNTS = [{'mountPath': '/cmcode', 'name': 'code', 'readOnly': True},
          {'mountPath': '/work', 'name': 'work'},
          {'mountPath': '/data', 'name': 'persistent'}]


def volumes(cm, work, fingerprint=False):
    out = [{'name': 'code', 'configMap': {'name': cm, 'defaultMode': 420}},
           {'name': 'work', 'emptyDir': {'sizeLimit': work}},
           {'name': 'persistent', 'persistentVolumeClaim': {'claimName': 'kai-data'}}]
    if fingerprint:
        out.append({'name': 'fingerprint', 'configMap': {'name': H.fp_configmap_name(), 'defaultMode': 420}})
    return out


def res(**kw):
    return {'requests': dict(kw), 'limits': dict(kw)}


def affinity(extra=()):
    return {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{
        'matchExpressions': list(extra) + [{'key': 'kubernetes.io/hostname', 'operator': 'NotIn',
                                            'values': H.PILOT_B_BAD_NODES}]}]}}}


def cpu_job(name, app, cm, script, annotations, deadline):
    labels = {**LABELS, 'app': app}
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': annotations},
            'spec': {'backoffLimit': 0, 'activeDeadlineSeconds': deadline, 'ttlSecondsAfterFinished': 604800,
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'affinity': affinity(), 'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'main', 'image': IMAGE, 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [script],
                                         'resources': res(cpu='8', memory='24Gi', **{'ephemeral-storage': '12Gi'}),
                                         'volumeMounts': MOUNTS}],
                         'volumes': volumes(cm, '12Gi')}}}}


def tag_of(name):
    return name[len('pilot1005-'):]


def pilot_job(name, row, cm, script):
    labels = {**LABELS, 'app': 'kai-pilot1005-r1', 'bnjettag.io/arms-per-pod': '1',
              'bnjettag.io/round': 'r1'}
    gpu = {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': GPU_PRODUCT}
    controller = ('option (c): train.ebops.pid_input traced_only, pid_traced_integral per_epoch'
                  if row['option_c'] else 'historical: PID reads in-training EBOPs on untraced epochs (keys absent)')
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': name, 'namespace': 'cms-ml', 'labels': labels, 'annotations': {
                'bnjettag.io/pack': f"{row['pack']} {row['name']}",
                'bnjettag.io/arm': f"{row['program_arm']} s{row['seed']} {row['hypothesis']} {row['arch_name']} "
                                   f"budget {row['budget']} warmup {row['warmup']}",
                'bnjettag.io/controller': controller,
                'bnjettag.io/single-arm-justified': SINGLE_ARM,
                'bnjettag.io/gpu-fingerprint': f'{H.fp_configmap_name()} sha256 {H.FP_SHA[:16]}: '
                                               f'{FP_RUN} initial_ebops == {H.FP_EXPECT} before the arm',
                'bnjettag.io/regime': 'B: [D20] trace every 10 epochs',
                'bnjettag.io/active-deadline': (
                    f'pod {POD_DEADLINE_S} s; run_pack timeout = deadline - elapsed - {RESERVE_S} s; deadline (124), '
                    f'RSS gate (5), training-phase failure (76) and PID-1 kill (137/143) are FailIndex; a pre-arm failure '
                    f'within {PREARM_RETRY_S} s exits 75 and is retried once (PREFLIGHT fixes after review v1, A2)'
                    if OPTS['bounded'] else
                    'unset in the build half; cluster-ops sets it at the launch half (STUDY §11)'),
                'bnjettag.io/per-arm-memory': f'{PER_ARM_MEMORY_GI}Gi host RAM, {PER_ARM_CPU} CPU, one arm',
                'bnjettag.io/rss-gate': f'projection <= {RSS_GATE_LIMIT_MB} MiB, fit over process epochs {RSS_GATE_WINDOW}'}},
            'spec': {'completionMode': 'Indexed', 'completions': 1, 'parallelism': 1,
                     'backoffLimitPerIndex': BACKOFF_PER_INDEX_BOUNDED if OPTS['bounded'] else 2,
                     'podReplacementPolicy': 'Failed', 'ttlSecondsAfterFinished': 604800,
                     'podFailurePolicy': {'rules': [
                         {'action': 'Ignore', 'onPodConditions': [{'type': 'DisruptionTarget'}]},
                         {'action': 'FailJob', 'onExitCodes': {'containerName': 'train', 'operator': 'In',
                                                               'values': [H.EXIT_EPOCH0_ALL_DIVERGED]}}]
                         + ([{'action': 'FailIndex', 'onExitCodes': {'containerName': 'train', 'operator': 'In',
                                                                     'values': FINAL_EXIT_CODES}}]
                            if OPTS['bounded'] else [])},
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         **({'activeDeadlineSeconds': POD_DEADLINE_S} if OPTS['bounded'] else {}),
                         'affinity': affinity([gpu]), 'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'train', 'image': IMAGE, 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [script],
                                         'env': [{'name': 'WANDB_API_KEY', 'valueFrom': {'secretKeyRef': {
                                             'name': 'kai-wandb', 'key': 'WANDB_API_KEY'}}},
                                                 {'name': 'NODE_NAME', 'valueFrom': {'fieldRef': {
                                                     'fieldPath': 'spec.nodeName'}}}],
                                         'resources': res(cpu=str(PER_ARM_CPU), memory=f'{PER_ARM_MEMORY_GI}Gi',
                                                          **{'ephemeral-storage': f'{EPHEMERAL_GI}Gi',
                                                             'nvidia.com/gpu': '1'}),
                                         'volumeMounts': MOUNTS + [{'mountPath': H.FP_MOUNT, 'name': 'fingerprint',
                                                                    'readOnly': True}]}],
                         'volumes': volumes(cm, f'{EPHEMERAL_GI}Gi', fingerprint=True)}}}}


GATE_REF = ('campaigns/2026-10-05-pilot-program/PREFLIGHT.md (build half, not reviewed); STUDY.md and PROGRAM.json '
            'drafts, not reviewed or signed')
COMMON_LIMITS = ['Pilots are directional (STUDY.md): no pilot number is a result, enters verify.json or appears in '
                 'outward text.',
                 'No historical checkpoint may initialize or resume these runs (config and code SHA guards).',
                 'The epoch-500 pause does not observe the first LR restart after epoch 500.']
GATE = {'status': 'pending', 'reference': GATE_REF, 'approval_ref': APPROVAL}


def brief(purpose, changes, runs, metrics, stops, outputs):
    return {'purpose': purpose, 'changes': changes, 'approval_ref': GATE['approval_ref'],
            'scientific_gate': {'status': GATE['status'], 'reference': GATE['reference']},
            'production_gate': {'status': 'pending', 'reference': 'STUDY.md §9 production trigger; PROGRAM.json unsigned'},
            'runs': [{'name': n, 'config_path': f'code/{CAMP_REL}/configs/{n}.json'} for n in runs],
            'expected_metrics': metrics, 'stop_rules': stops, 'outputs': outputs, 'limitations': COMMON_LIMITS,
            'decision_ref': '.claude/memory/decisions.md 2026-10-05 10:08 JST',
            'study_ref': 'campaigns/2026-10-05-pilot-program/STUDY.md'}


def main():
    global POD_DEADLINE_S, READOUT_DEADLINE_S, OUT
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='', help='comma list of cpugate, readout, r1-<tag> (default all)')
    ap.add_argument('--gate-cleared', metavar='REFERENCE',
                    help='only after Kai clears the gate: reviewed document that records it')
    ap.add_argument('--approval-ref', help='exact dated Kai authorization (required with --gate-cleared)')
    ap.add_argument('--readout-pythonpath', action='store_true',
                    help=f'review v1 A1: readout Job exports PYTHONPATH={READOUT_PYTHONPATH}')
    ap.add_argument('--bounded', action='store_true',
                    help='review v1 A2: pod deadline, final exits (FailIndex), one pre-arm retry on the R1 GPU Jobs')
    ap.add_argument('--diag', action='store_true', help='F5: readout_diag.json step in the readout Job')
    ap.add_argument('--pod-deadline-s', type=int, help=f'pod activeDeadlineSeconds with --bounded (default {POD_DEADLINE_S})')
    ap.add_argument('--readout-deadline-s', type=int, help=f'readout Job activeDeadlineSeconds (default {READOUT_DEADLINE_S})')
    ap.add_argument('--manifests-dir', help='write manifests here (relative to the campaign) instead of manifests/; '
                                            'a new bundle never overwrites the frozen files of an earlier one')
    ap.add_argument('--expect-bundle', help='refuse unless the rebuilt bundle sha256 starts with this')
    args = ap.parse_args()
    OPTS.update(readout_pythonpath=args.readout_pythonpath, bounded=args.bounded, diag=args.diag)
    if args.manifests_dir:
        OUT = HERE / args.manifests_dir
    if args.pod_deadline_s:
        assert args.bounded, '--pod-deadline-s needs --bounded'
        POD_DEADLINE_S = args.pod_deadline_s
        OPTS['pod_deadline_s'] = POD_DEADLINE_S
    if args.readout_deadline_s:
        READOUT_DEADLINE_S = args.readout_deadline_s
        OPTS['readout_deadline_s'] = READOUT_DEADLINE_S
    if args.gate_cleared:
        assert args.approval_ref and not args.approval_ref.startswith('PENDING'), 'explicit approval reference required'
        GATE.update(status='cleared', reference=args.gate_cleared, approval_ref=args.approval_ref)
    only = set(filter(None, args.only.split(',')))
    rows = check_campaign()
    msha = manifest_sha()
    payload, files = build_tarball()
    bundle = sha(payload)
    assert len(base64.b64encode(payload)) < 1_000_000, len(payload)
    assert bundle not in (H.BUNDLE_42, '6919462cf050c5dca664baec694f36081f05d8c4075a0d299b28af8ce4eb9da3')
    assert not args.expect_bundle or bundle.startswith(args.expect_bundle), ('bundle changed', bundle)
    cm = 'kai-pilot1005-code-' + bundle[:10]
    OUT.mkdir(exist_ok=True)

    def write_same(path, data):     # never rewrite a frozen artifact with different bytes
        if path.exists():
            assert path.read_bytes() == data, (path, 'differs from the frozen file')
            return
        path.write_bytes(data)
    write_same(OUT / 'pilot1005-code.tar.gz', payload)
    configmap = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
                 'metadata': {'name': cm, 'namespace': 'cms-ml', 'labels': LABELS,
                              'annotations': {'bnjettag.io/bundle-sha256': bundle, 'bnjettag.io/manifest-sha256': msha,
                                              'bnjettag.io/base': '42abed4b + 0032 + 0033 + 0034 + 0036 + 0037 + 0035 + 0038 + 0039 + '
                                                                  '0040 + 0041' + EXTRA_TXT + ' (build_tree.py)'}},
                 'binaryData': {KEY: base64.b64encode(payload).decode()}}
    write_same(OUT / 'configmap.json', enc(configmap))
    b6 = bundle[:6]
    names = [r['name'] for r in rows]
    jobs = {}
    gate = cpu_job(f'kai-pilot1005-cpugate-{b6}', 'kai-pilot1005-cpugate', cm,
                   header(bundle, msha, cpu=True, trap=GATE_TRAP) + cpugate_tail(bundle),
                   {'bnjettag.io/purpose': f'pilot-program CPU gate: threshold, cpu_gate.py on {len(rows)} configs, NB pairing, full pytest; '
                                           'fail-fast, last line GATE_RESULT'}, GATE_DEADLINE_S)
    jobs['cpugate'] = (gate, brief(
        'CPU gate for the pilot-program round-1 bundle before any pilot: threshold (c) from the cache, per-config '
        'build/step/reload/floor/PID-schedule gate with matched initialization, NB [A22] pairing at seeds 1-8, '
        'and the full unit suite.',
        'Tree 42abed4b + 0032 + 0033 (option c) + 0034 (test env fix) + 0036 (NB arm) + 0037 (attention bit floor) + '
        f'0035 ({len(rows) if not EXTRA_PATCHES else 23} pilot configs) + 0038 (W&B stages pilot-r1/2/3) + 0039 (readout) + 0040 (gate checks, NB pairing) + '
        '0041 (validate_cfg accepts NB)' + (EXTRA_TXT + f' ({len(rows)}-arm R1 configs, STUDY [A3])' if EXTRA_PATCHES else '')
        + '. No GPU, no training, no checkpoint read.',
        names,
        [{'name': 'threshold', 'split': 'validation labels, n=62000', 'expectation': 'val_accuracy_threshold '
          '0.2109624456315518 and labels sha e593f51f...7617'},
         {'name': 'cpu_gate.py', 'split': 'synthetic inputs, n=4096 rows', 'expectation': f'PREFLIGHT_ALL_PASS {len(rows)}; '
          f'{len(rows)} PID lines; PAIRED_INIT_OK E and A07'},
         {'name': 'pair_nb.py', 'split': 'synthetic inputs, n=4096 rows', 'expectation': 'NB_PAIRING_ALL_OK 8'},
         {'name': 'pytest suite', 'split': 'synthetic fixtures only', 'expectation': 'exactly 2 known skips '
          '(analysis/test_attn_entropy.py:142), all other tests passed, exact collected count'}],
        [{'condition': 'any check FAIL, nonzero exit or deadline', 'action': 'existing-runner-guard',
          'approval_ref': 'Job script: fail fast, last line GATE_RESULT FAIL <reason>; activeDeadlineSeconds '
                          f'{GATE_DEADLINE_S}'}],
        [f'{PROGRAM_ROOT}/cpu-gate-{b6}-r1']))
    for row in rows:
        tag = tag_of(row['name'])
        trap = pod_exit_trap() if OPTS['bounded'] else None
        job = pilot_job(f'kai-p1005r1-{tag}-{b6}', row, cm, header(bundle, msha, cpu=False, trap=trap) + pilot_tail(row))
        assert len(job['metadata']['name']) <= 52, job['metadata']['name']
        script = job['spec']['template']['spec']['containers'][0]['args'][0]
        assert script.index('fingerprint_check.py --run') < script.index('run_pack.py')
        jobs[f'r1-{tag}'] = (job, brief(
            f"Pilot-program R1 arm {row['program_arm']} seed {row['seed']} ({row['hypothesis']}): from initialization "
            'to the epoch-500 pause, one arm per RTX 3090.',
            f"Config {row['name']} ({row['arch_name']}, budget {row['budget']}, option (c) {row['option_c']}, "
            f"warmup {row['warmup']}, variant {row['variant']}); generated by campaigns/pilot1005/generate.py from the byte-checked "
            'chang0926/chang1002c config; only target, warmup, the NB/H3 quant key and its floor, and identity '
            'differ (config_map.json).',
            [row['name']],
            [{'name': 'readout fields', 'split': 'validation n=62000, traced epochs < 500',
              'expectation': 'reported, not predicted (STUDY.md §5)'}],
            [{'condition': 'divergence, nonfinite metrics, RSS projection gate, epoch-0 divergence, fingerprint mismatch',
              'action': 'existing-runner-guard', 'approval_ref': 'run_pack/ablation guards in the frozen bundle'},
             {'condition': 'CANARY_* FAIL or CONTROLLER_AUDIT FAIL in a MONITOR line', 'action': 'notify-only',
              'approval_ref': 'option-(c) amendment canary; monitor_p.py (warmup-aware)'},
             {'condition': 'GPU utilization < 40 % at 30 min', 'action': 'notify-only',
              'approval_ref': 'PILOT_PROGRAM.md §4; STUDY.md §10'}]
            + ([{'condition': f'pod activeDeadlineSeconds {POD_DEADLINE_S} / run_pack timeout, RSS gate, or a '
                              'training-phase failure', 'action': 'existing-runner-guard',
                 'approval_ref': 'final for the arm (podFailurePolicy FailIndex on exit 5, 76, 124, 137, 143); '
                                 f'backoffLimitPerIndex {BACKOFF_PER_INDEX_BOUNDED} only for a pre-arm failure '
                                 f'(exit 75, within {PREARM_RETRY_S} s); PREFLIGHT.md fixes after review v1 A2'}]
               if OPTS['bounded'] else []),
            [f"{RUN_ROOT}/runs/{row['name']}",
             f'wandb://kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe/chang-n64-20261005-{STAGE}']))
    readout = cpu_job(f'kai-pilot1005-r1ro-{b6}', 'kai-pilot1005-readout', cm,
                      header(bundle, msha, cpu=True) + readout_tail(rows, bundle),
                      {'bnjettag.io/readout': f'R1 epoch-{STOP_AFTER} snapshots under {RUN_ROOT}: attn_entropy.py, '
                                              'certify_ebops.py, monitor_p.py, readout_pilot.py -> readout.json',
                       'bnjettag.io/runs': ','.join(names)}, READOUT_DEADLINE_S)
    jobs['readout'] = (readout, brief(
        'Round-1 readout: one readout.json row per arm with the STUDY.md §5 fields, for the autopilot decision rule.',
        'CPU only, TF32 off, no training. a26 entropy and certification scripts as in readout-c; monitor_p.py on each '
        'option-(c) snapshot telemetry; readout_pilot.py (patch 0039) assembles readout.json. New output directory.',
        names,
        [{'name': 'readout.json', 'split': 'validation n=62000; traced epochs < 500', 'expectation':
          f'{len(rows)} rows, exact field set; status per row; integrity fields threshold_c, labels_sha256'}],
        [{'condition': 'any script exit nonzero or deadline', 'action': 'existing-runner-guard',
          'approval_ref': f'Job script exit status; activeDeadlineSeconds {READOUT_DEADLINE_S}'}],
        [f'{RUN_ROOT}/readout-epoch-{STOP_AFTER:04d}-{b6}-r1/readout.json']))
    prepared = {}
    for key, (job, br) in jobs.items():
        if only and key not in only:
            continue
        (OUT / f'{key}-job.json').write_bytes(enc(job))
        (OUT / f'brief-{key}.json').write_bytes(enc(br))
        result = subprocess.run([sys.executable, str(REPO / 'tools/run_handoff.py'), 'prepare',
                                 '--job', str(OUT / f'{key}-job.json'), '--configmap', str(OUT / 'configmap.json'),
                                 '--brief', str(OUT / f'brief-{key}.json'), '--data-info', str(EXPORT_INFO),
                                 '--data-path', DATA_INFO_PATH, '--out', str(HERE / 'handoffs')],
                                capture_output=True, text=True)
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        assert result.returncode == 0, key
        handoff = Path(result.stdout.strip())
        prepared[key] = {'job': job['metadata']['name'], 'handoff': str(handoff.relative_to(HERE)),
                         'record_sha256': sha((handoff / 'record.json').read_bytes()),
                         'job_json_sha256': sha((handoff / 'job.json').read_bytes())}
    write_same(OUT / 'bundle-manifest.json', enc({
        'bundle_sha256': bundle, 'manifest_sha256': msha, 'configmap': cm, 'bytes': len(payload),
        'base': '42abed4b + 0032 (f475c69e) + 0033 (23536dfe) + 0034 + 0036 + 0037 + 0035 + 0038 + 0039 + 0040 + 0041' + EXTRA_TXT + ' '
                '(patches/PATCHES.json)',
        'run_root': RUN_ROOT, 'stage': STAGE, 'data_root': DATA_ROOT,
        'files': {rel: sha(p.read_bytes()) for rel, p in files}}))
    if GATE['status'] == 'cleared':     # one record per invocation, never overwritten (option-(c) review C6)
        target = HERE / f"PREPARED-cleared-{'-'.join(sorted(prepared))[:80]}.json"
        assert not target.exists(), target
        target.write_bytes(enc({'gate': GATE, 'jobs': prepared}))
        return
    if only and (HERE / 'PREPARED.json').exists():   # --only: replace those keys, keep every other entry
        old = json.loads((HERE / 'PREPARED.json').read_text())
        assert old['bundle_sha256'] == bundle and old['manifest_sha256'] == msha, 'PREPARED.json is for another bundle'
        merged = {**old['jobs'], **prepared}
        superseded = {k: old['jobs'][k] for k in prepared if k in old['jobs'] and old['jobs'][k] != prepared[k]}
        prepared_all = merged
        extra = {'superseded': {**old.get('superseded', {}), **{f'{k}@{v["handoff"].split("/")[-1]}': v
                                                                for k, v in superseded.items()}},
                 'options': {**old.get('options', {}), **{k: dict(OPTS) for k in prepared}}}
    else:
        prepared_all, extra = prepared, {'options': {k: dict(OPTS) for k in prepared}}
        if (HERE / 'PREPARED.json').exists():      # keep the earlier bundle's record beside the new one
            old = json.loads((HERE / 'PREPARED.json').read_text())
            if old['bundle_sha256'] != bundle:
                keep = HERE / f"PREPARED-{old['bundle_sha256'][:8]}.json"
                assert not keep.exists() or keep.read_bytes() == (HERE / 'PREPARED.json').read_bytes(), keep
                keep.write_bytes((HERE / 'PREPARED.json').read_bytes())
                extra['previous_bundle_record'] = keep.name
        extra['manifests_dir'] = str(OUT.relative_to(HERE))
    (HERE / 'PREPARED.json').write_bytes(enc({'status': 'offline_prepared_not_submitted', 'bundle_sha256': bundle,
                                              'manifest_sha256': msha, 'configmap': cm, 'image': IMAGE,
                                              'gpu_product': GPU_PRODUCT, 'run_root': RUN_ROOT, 'jobs': prepared_all,
                                              **extra}))
    print('BUNDLE_SHA256', bundle)
    print('MANIFEST_SHA256', msha)
    print('CONFIGMAP', cm, 'bytes', len(payload), 'files', len(files))
    for key, value in prepared.items():
        print('PREPARED', key, value['job'], value['handoff'])


if __name__ == '__main__':
    main()
