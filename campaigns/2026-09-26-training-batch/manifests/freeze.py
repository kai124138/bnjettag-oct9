#!/usr/bin/env python3
"""Freeze code/tree (+ code/analysis) into the ConfigMap payload and generate the regime-B pilot
and epoch-500 readout Job manifests.

REGIME B (Kai [D15] decision, 2026-09-27; plan.md "ml-engineer, regime B"). The regime-A pilot
`kai-chang0926-pilot-77f1ca` runs on bundle 77f1ca4e (ConfigMap kai-chang0926-code-77f1ca4e9f,
manifest f7d4003f). This script no longer writes `pilot-job.json`, `readout-job.json` or
`cache-job.json`: those files describe the 77f1ca4e bundle and stay as they are (the running pod's
manifest; the cache must not be rebuilt). The 77f1ca4e ConfigMap payload and bundle manifest are
kept as `configmap-77f1ca4e.json` and `bundle-manifest-77f1ca4e.json`. It writes:
    chang0926-code.tar.gz, configmap.json, bundle-manifest.json   the new (regime-B) bundle,
    configmap-<sha8>.json, bundle-manifest-<sha8>.json            sha-named copies of the same
    pilot-b-k5-job.json     GPU, 1 pod, K=5: A-s1, A-s2, D-s1, C'-s1, E1-s1, BNJ_STAGE=pilot-b
    pilot-b-k3-job.json     GPU, 1 pod, K=3: A07-350-s1, C-s1, F-s1 (STUDY arbiter v8 fix 2)
    readout-b5-job.json     CPU readout of the K=5 pod's epoch-500 snapshots (new bundle)
    readout-b3-job.json     CPU readout of the K=3 pod's epoch-500 snapshots (new bundle)
    readout-a-job.json      CPU readout of the regime-A pilot on the 77f1ca4e ConfigMap: the code
                            that trained it; five runs (A07-350-s1 has no snapshot, it OOMed on all
                            three attempts), so `readout-job.json` (six runs) would stop at its gate
Both pilot-b pods use the run root /data/chang-n64-20260926/pilot-b and W&B stage pilot-b.
Re-frozen after the stall incident (2026-09-28): patches 0030 (run_pack.py: fresh heartbeat per
attempt, pod-wide stall not charged, POD_MEM every poll, exit 5 not retried) and 0031
(ablation.py: one validation model per run via load_weights; the RSS canary gate, env
BNJ_RSS_GATE_LIMIT_MB / BNJ_RSS_GATE_WINDOW, projection form, set on the pilot-b pods only).

Earlier scope, kept for the record:

Never submits anything. Scope (PREFLIGHT build half, 2026-09-27; re-freeze after PREFLIGHT gate
v1): the gated N=64 cache job, the one-pod pilot (canary epochs 1-10, then the same pod to epoch
500) and the CPU readout of the pilot's epoch-500 snapshots ([D20] certification + [A26]
entropy). Wave-1 production and wave 2 are not generated here; a production generator must
follow docs/infrastructure/gpu-selection-policy.md, pin one measured GPU product and its
resource key, and set BNJ_STAGE=production. This script regenerates the already-launched pilot
manifests for audit only; it does not select the future production GPU.

    python3 campaigns/2026-09-26-training-batch/manifests/freeze.py

Writes, beside this file:
    chang0926-code.tar.gz     deterministic tarball of code/tree (arcname code/, no __pycache__)
                              plus code/analysis/ (arcname code/analysis/; offline, not training)
    configmap.json            immutable ConfigMap kai-chang0926-code-<bundle sha[:10]>
    cache-job.json            CPU Job: prepare_cache -> data_info readout -> threshold -> df
    pilot-job.json            GPU Indexed Job, 1 pod, K=6, pilot_packs.json, --stop-after 500, BNJ_STAGE=pilot
    readout-job.json          CPU Job: certify_ebops.py --snapshot 500 and analysis/attn_entropy.py on
                              the six pilot runs' snapshots/epoch-0500 (after the pilot pauses)
    bundle-manifest.json      bundle sha, manifest sha, ConfigMap name, per-file sha256

Checks made here (fail loudly):
    - every config in campaigns/chang0926/index.json hashes to its config_sha256 (58 rows);
    - index count, packs.json (10 packs) and pilot_packs.json == [[0, 1, 24, 48, 56, 57]];
    - run_study.manifest() sha, re-derived from the file hashes and the pinned versions in
      requirements-training.txt, equals the recorded EXPECTED_MANIFEST (the pods assert it again
      after pip install, so a version drift fails the pod before training);
    - the tarball is small enough for a ConfigMap (base64 < 1 MiB).
"""
import base64
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
CODE = HERE.parent / 'code' / 'tree'
# [A26] offline analysis, shipped as non-training files under code/analysis/: not *.py at the
# top level or in bnhgq2/, so outside run_study.manifest() and the trainer's code_sha256.
ANALYSIS = HERE.parent / 'code' / 'analysis'
CAMPAIGN_REL = 'campaigns/chang0926'
CAMP = CODE / CAMPAIGN_REL

# c5d6f02a bundle: ac5a5c86...; 77f1ca4e bundle (patches 0025-0026): f7d4003f...;
# regime B (patches 0027-0029, 2026-09-27): 12c76954... (bundle f2107a04, superseded before
# any pod); regime B + stall-incident fixes (patches 0030-0031, 2026-09-28): 33e9bf7b... (bundle
# ceb174db, slope-form gate, superseded before any pod), then the projection-form gate:
EXPECTED_MANIFEST = '041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42'
PILOT_PACK = [[0, 1, 24, 48, 56, 57]]                   # regime-A pilot (77f1ca4e), record only
PILOT_B = {'k5': ('pilot_b_k5_packs.json', [[0, 1, 24, 56, 57]]),
           'k3': ('pilot_b_k3_packs.json', [[48, 16, 32]])}
N_PACKS = 13                                            # packs.json, plan.md DECISION R-B3
DATA_ROOT = '/data/chang-n64-20260926'
RUN_ROOT = DATA_ROOT + '/pilot-b'        # regime-B pilot runs, apart from the regime-A pilot and production
STAGE = 'pilot-b'                        # BNJ_STAGE: W&B id and group (bnhgq2.wandb_util, patch 0028)
TAGS = 'chang0926,pilot,pilot-b,regime-b,validation-only'
# Incident 2026-09-28 (review/INCIDENT_stall_20260928.md): memory canary gate on every pilot-b
# arm (bnhgq2.ablation.rss_gate_from_env, patch 0031), projection form (coordinator, 2026-09-28):
# fit host RSS over this process's epochs 5-104; baseline + slope x train.epochs (7,000; R 1,000)
# must be <= the per-arm limit below, else the arm stops with exit 5 (run_pack: not retried).
# Per-arm memory: measured start-of-run RSS 2,106-2,160 MB per arm (incident §2, W&B rssMB at
# 20:56Z, ~5 min after launch). Resized 6 -> 8 GiB (coordinator, 2026-09-28; decisions.md): the
# 6 GiB came from rule PACK's "about 6 Gi per arm" guidance, not a measurement. The only GPU RSS
# telemetry on this code, Delta canary v2 (campaigns/2026-09-27-delta-screen/RUN.md, commit
# a3a3362; Delta's patches on top of 42abed4b; not a result), fitted 0.45-0.63 MB/epoch over epochs
# 5-100 at a 2,288-2,303 MB baseline, which projects to about 5.3-6.6 GB at epoch 7,000 (gate
# form), one arm in four over 6,144, all under 8,192. At 8 GiB and a 2.1-2.2 GB baseline the
# gate admits about 0.85-0.87 MB/epoch.
PER_ARM_MEMORY_GI = 8
RSS_GATE_LIMIT_MB = str(PER_ARM_MEMORY_GI * 1024)
RSS_GATE_WINDOW = '5:105'
# The regime-A pilot (running) and its readout: the 77f1ca4e ConfigMap, never rebuilt.
REGIME_A = {'bundle': '77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94',
            'manifest': 'f7d4003f49584c701aec1cfefb4c0c9a3591c41d7d2fda94dd5a293d00eaaa36',
            'configmap': 'kai-chang0926-code-77f1ca4e9f', 'run_root': DATA_ROOT + '/pilot', 'stage': 'pilot',
            'indices': [0, 1, 24, 56, 57]}
READOUT_EPOCH = 500
CAMPAIGN_DIR = '/work/code/' + CAMPAIGN_REL
RAW = '/data/hls4ml_lhc_jet/train/train'
KEY = 'hgq2.tar.gz'
SKIP = ('__pycache__', '.pytest_cache', '.DS_Store')
BAD_NODES = ['k8s-chase-ci-07.calit2.optiputer.net', 'nautilus-ext-gpu01.fullerton.edu',
             'ren-gp-argo-01.madren.org']   # cache job and readout-a (unchanged manifests)
# Historical regime-B pilot requirement (PREFLIGHT gate v3 A1). Kai's later GPU-policy amendment
# supersedes the A10-only rule for future production. Keep this value to reproduce the manifests
# of the running pilots; do not copy it into a new production generator.
PILOT_B_GPU_REQUIRED = ['NVIDIA-A10']
REPO = HERE.parents[2]
# Delta REGRESSION_TICKET (campaigns/2026-09-27-delta-screen/REGRESSION_TICKET.md): epoch-0 NaN,
# initial_ebops off the reference, on this node.
C6017 = 'hcc-nrp-shor-c6017.unl.edu'


def known_bad_nodes():
    spec = importlib.util.spec_from_file_location('nrp_doctor', REPO / 'nrp-lab' / 'nrp_doctor.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.KNOWN_BAD_NODES)


# pilot-b, fallback and readout-b Jobs: the old list, c6017, and every nrp_doctor KNOWN_BAD_NODES host
PILOT_B_BAD_NODES = sorted(set(BAD_NODES) | {C6017} | known_bad_nodes())
BUNDLE_42 = '42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0'   # frozen; --jobs-only asserts it
# GPU fingerprint gate (Delta REGRESSION_TICKET §3 item 2; Delta gate 15). Delta's script, byte-identical
# (campaigns/2026-09-26-delta/code/fingerprint_check.py at 2d86bc9), shipped in its own immutable
# ConfigMap so bundle 42abed4b is unchanged. Reference: anchor A-s1 initial_ebops on the anchor cache,
# CPU on the 42abed4b extraction (code/evidence/fingerprint_cpu_42abed4b.log) = anchor GPU c5825.
FP_FILE = HERE / 'fingerprint' / 'fingerprint_check.py'
FP_SHA = 'e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1'
FP_RUN, FP_EXPECT = 'chang0926-a-n64-s1', 11559681
FP_MOUNT = '/cmfp'
EXIT_EPOCH0_ALL_DIVERGED = 10
# PREFLIGHT gate v3 B4: registered fallback for an OOM in the K=3 pod (A07-350-s1, C-s1, F-s1)
# The K=3 Job is deleted when an arm fails on OOM, so the survivors are relaunched too:
# e.g. A07-350-s1 OOM -> fb48 + fb16-32; C-s1 OOM -> fb16 + fb48-32; F-s1 OOM -> fb32 + fb48-16.
FALLBACKS = ([48], [16], [32], [16, 32], [48, 16], [48, 32])
LABELS = {'user': 'kai', 'campaign': 'chang-n64-20260926'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def keep(path, root):
    return not any(part in SKIP for part in path.relative_to(root).parts)


def members():
    """(archive name relative to code/, path), sorted: code/tree/** then code/analysis/**."""
    out = [(p.relative_to(CODE).as_posix(), p) for p in CODE.rglob('*') if keep(p, CODE)]
    assert not (CODE / 'analysis').exists(), 'code/tree/analysis would collide with code/analysis'
    out += [('analysis', ANALYSIS)]
    out += [('analysis/' + p.relative_to(ANALYSIS).as_posix(), p) for p in ANALYSIS.rglob('*') if keep(p, ANALYSIS)]
    return sorted(out)


def build_tarball():
    entries = members()
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


def pinned_versions():
    pins = {}
    for line in (CODE / 'requirements-training.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split('==')
            pins[name.split('[')[0].strip()] = version.strip()
    return {k: pins[k] for k in ('tensorflow', 'keras', 'hgq2', 'quantizers', 'numpy', 'scikit-learn')}


def manifest_sha():
    # Same construction as run_study.manifest(); versions from the pins the pods install.
    paths = sorted(CODE.glob('*.py')) + sorted((CODE / 'bnhgq2').glob('*.py'))
    result = {'files': {str(p.relative_to(CODE)): sha(p.read_bytes()) for p in paths},
              'versions': pinned_versions()}
    return sha(json.dumps(result, sort_keys=True).encode())


def check_campaign():
    index = json.loads((CAMP / 'index.json').read_text())
    rows = index['runs']
    assert index['count'] == len(rows) == 58, index['count']
    for row in rows:
        got = sha((CAMP / 'configs' / row['file']).read_bytes())
        assert got == row['config_sha256'], (row['file'], got)
    assert len(list((CAMP / 'configs').glob('*.json'))) == 58
    assert json.loads((CAMP / 'pilot_packs.json').read_text()) == PILOT_PACK
    for packs_file, pack in PILOT_B.values():
        assert json.loads((CAMP / packs_file).read_text()) == pack, packs_file
    packs = json.loads((CAMP / 'packs.json').read_text())
    assert len(packs) == N_PACKS and sorted(i for p in packs for i in p) == list(range(56))
    assert [p.name for p in (CAMP / 'cache_configs').glob('*.json')] == ['n64.json']
    # The cache is built from cache_configs/n64.json but checked in-pod against each run config
    # (run_engram.load_cache, nondegenerate_threshold.py): the identity keys must agree for all 58.
    cache = json.loads((CAMP / 'cache_configs' / 'n64.json').read_text())
    assert cache['cache']['order_seed_in_cache'] is False
    for row in rows:
        cfg = json.loads((CAMP / 'configs' / row['file']).read_text())
        for part, key in (('arch', 'n_part'), ('arch', 'features'), ('arch', 'pt_gate_gev'),
                          ('train', 'validation_split'), ('train', 'split_seed')):
            assert cfg[part].get(key) == cache[part].get(key), (row['file'], key)
        # [D20] regime B: every config traces every 10 epochs
        assert cfg['train'].get('ebops_trace_every') == 10, row['file']
    return {r['index']: r['name'] for r in rows}


def header(bundle, msha, cpu, run_root=RUN_ROOT, stage=STAGE):
    lines = [
        'set -euo pipefail',
        'export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2',
        'export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1',
        'mkdir -p /work/code',
        f"echo '{bundle}  /cmcode/{KEY}' | sha256sum -c -",
        f'tar -xzf /cmcode/{KEY} -C /work/code --strip-components=1',
        'export PYTHONPATH=/work/code',
        f'export BNJ_DATA_ROOT={DATA_ROOT} BNJ_RUN_ROOT={run_root} BNJ_CAMPAIGN_DIR={CAMPAIGN_DIR}',
        f'export BNJ_STAGE={stage}',
    ]
    if cpu:
        lines += ['export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled',
                  'pip install -q --no-cache-dir -r /work/code/requirements-cpu.txt']
    else:
        lines += [
            'export TF_FORCE_GPU_ALLOW_GROWTH=true NVIDIA_TF32_OVERRIDE=0',
            # Project comes from the configs (BNJetTag-ChangRecipe); an env WANDB_PROJECT would
            # override it and validate_tracking_destination would refuse to start.
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
    # The code sha the trainer records and checks on resume is run_study.manifest(), which
    # includes the installed package versions: assert it here, before any work.
    lines += [
        'cd /work/code',
        'MSHA=$(python -c "import run_study; print(run_study.manifest()[\'sha256\'])")',
        f'test "$MSHA" = "{msha}" || {{ echo "MANIFEST_SHA_MISMATCH $MSHA"; exit 1; }}',
        'echo "MANIFEST_SHA_OK $MSHA"',
        'export BNHGQ2_CODE_SHA256="$MSHA"',
    ]
    return '\n'.join(lines) + '\n'


def cache_tail():
    data = f'{DATA_ROOT}/n64/data'
    readout = ("import json; d = json.load(open('" + data + "/data_info.json')); "
               "print('DATA_INFO', json.dumps({k: d.get(k) for k in ('n_train', 'n_val', 'pt_gate_gev', "
               "'validation_split', 'split_seed', 'order_seed', 'pt_gate_stats', 'sort_stats', "
               "'y_class_counts', 'code_sha256', 'array_sha256')}, sort_keys=True))")
    return '\n'.join([
        f'test "$(ls {RAW}/*.h5 | wc -l)" = 62',
        f'python -u /work/code/prepare_cache.py --configs {CAMPAIGN_DIR}/cache_configs --root {DATA_ROOT} '
        f'--raw {RAW} --n-parts 64',
        f'python -c "{readout}"',
        f'python -u {CAMPAIGN_DIR}/nondegenerate_threshold.py --cache {data} '
        f'--out {DATA_ROOT}/n64/nondegenerate_threshold.json',
        'df -h /data',
        'echo CACHE_JOB_DONE',
    ]) + '\n'


def fp_configmap_name():
    return 'kai-chang0926-fp-' + FP_SHA[:10]


def fp_configmap():
    data = FP_FILE.read_bytes()
    assert sha(data) == FP_SHA, sha(data)
    return {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
            'metadata': {'name': fp_configmap_name(), 'namespace': 'cms-ml', 'labels': LABELS,
                         'annotations': {'bnjettag.io/fingerprint-sha256': FP_SHA,
                                         'bnjettag.io/source': 'campaigns/2026-09-26-delta/code/fingerprint_check.py @ 2d86bc9',
                                         'bnjettag.io/expect': f'{FP_RUN} initial_ebops {FP_EXPECT}'}},
            'data': {'fingerprint_check.py': data.decode()}}


# After run_pack: every arm of this pack diverged at zero-based epoch 0 -> a pod-level failure
# (Delta REGRESSION_TICKET §3 item 2, wrapper side; run_pack itself treats them as K outcomes).
EPOCH0_CHECK = '''python - "$PACKS" <<'PY' || E0=$?
import json, os, sys
from pathlib import Path
camp = Path(os.environ['BNJ_CAMPAIGN_DIR'])
runs = Path(os.environ['BNJ_RUN_ROOT']) / 'runs'
pack = json.loads((camp / sys.argv[1]).read_text())[int(os.environ['JOB_COMPLETION_INDEX'])]
rows = json.loads((camp / 'index.json').read_text())['runs']
seen = []
for i in pack:
    marker = runs / rows[i]['name'] / 'DIVERGED.json'
    seen.append((rows[i]['name'], json.loads(marker.read_text()).get('divergence_epoch_zero_based') if marker.exists() else None))
print('PACK_EPOCH0_CHECK', ' '.join(f'{n}={e}' for n, e in seen), flush=True)
sys.exit(%d if seen and all(e == 0 for _, e in seen) else 0)
PY''' % EXIT_EPOCH0_ALL_DIVERGED


def pilot_tail(packs_file, pack_json=None, guard_names=()):
    lines = [
        'python -c "import tensorflow as tf; assert tf.config.list_physical_devices(\'GPU\'); print(\'GPU_GATE_PASS\')"',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true',
        'df -h /data',
    ]
    if pack_json is not None:
        # OOM fallback (gate v3 B4): the pack is written here, run_pack reads CAMPAIGN / <absolute path>.
        # Refuse while any target arm shows progress in the last 15 min (the K=3 Job must be deleted
        # first) or when it has history but no committed checkpoint (ablation.py:710 would raise).
        lines += [f"echo '{pack_json}' > /work/fallback_packs.json"]
        for name in guard_names:
            run = f'{RUN_ROOT}/runs/{name}'
            lines += [
                f'if test -n "$(find {run}/latest.json {run}/activation_widths.jsonl -mmin -15 2>/dev/null)"; '
                f'then echo "ARM_STILL_LIVE {name}"; exit 1; fi',
                f'if test -f {run}/activation_widths.jsonl && ! test -f {run}/latest.json; '
                f'then echo "ARM_NO_CHECKPOINT {name}: rename {run} aside (never delete), then re-apply"; exit 1; fi',
            ]
    lines += [
        # GPU fingerprint gate (Delta gate 15): before any arm starts; a mismatch starts no arm.
        f"echo '{FP_SHA}  {FP_MOUNT}/fingerprint_check.py' | sha256sum -c -",
        'FP=0',
        f'python -u {FP_MOUNT}/fingerprint_check.py --run {FP_RUN} --expect {FP_EXPECT} --data-root {DATA_ROOT} '
        f'--campaign-dir {CAMPAIGN_DIR} --env-report || FP=$?',
        'if [ "$FP" != 0 ]; then echo "FINGERPRINT_GATE_FAIL exit=$FP node=${NODE_NAME:-na}; no arm started"; exit "$FP"; fi',
        f'PACKS={packs_file}',
        # [A12] run_pack isolates arms (patch 0007): a diverged or crashed arm never stops the others.
        # --stop-after 500: canary readout from epochs 1-10, the same pod continues to epoch 500.
        'RP=0; E0=0',
        'python -u /work/code/run_pack.py "$PACKS" 500 || RP=$?',
        EPOCH0_CHECK,
        f'if [ "$E0" = {EXIT_EPOCH0_ALL_DIVERGED} ]; then echo "POD_EPOCH0_ALL_DIVERGED node=${{NODE_NAME:-na}} run_pack_exit=$RP"; exit {EXIT_EPOCH0_ALL_DIVERGED}; fi',
        'if [ "$E0" != 0 ]; then echo "PACK_EPOCH0_CHECK_ERROR $E0"; fi',
        'exit "$RP"',
    ]
    return '\n'.join(lines) + '\n'


def readout_tail_partial(names_by_index, indices, run_root, label):
    """Gate v3 B6: process the arms that are present, report the missing ones. An arm counts if it
    has the epoch-500 snapshot or DIVERGED.json (as before); an arm with neither (RSS_GATE_FAIL.json,
    ARM_FAILED_*, or still running) is reported as READOUT_MISSING with its marker and left out of
    --only / --indices. Stops only if no arm has a snapshot. A partial readout writes to a
    timestamped directory, so a later full readout does not meet attn_entropy's no-overwrite guard."""
    snap = f'snapshots/epoch-{READOUT_EPOCH:04d}/state.json'
    out = f'{run_root}/readout-epoch-{READOUT_EPOCH:04d}-$BUNDLE6-{label}'
    pairs = ' '.join(f'{i}:{names_by_index[i]}' for i in indices)
    return '\n'.join([
        'ONLY=""; IDX=""; NSNAP=0; MISSING=""',
        f'for pair in {pairs}; do',
        '  i=${pair%%:*}; n=${pair#*:}; d=' + f'{run_root}/runs/$n',
        f'  if test -f "$d/{snap}"; then ONLY="$ONLY${{ONLY:+,}}$n"; IDX="$IDX $i"; NSNAP=$((NSNAP + 1))',
        '  elif test -f "$d/DIVERGED.json"; then ONLY="$ONLY${ONLY:+,}$n"; IDX="$IDX $i"',
        '  else',
        '    why=NO_TERMINAL_MARKER',
        '    test -f "$d/RSS_GATE_FAIL.json" && why=RSS_GATE_FAIL',
        '    echo "READOUT_MISSING $n $why"; MISSING="$MISSING $n"',
        '  fi',
        'done',
        'test "$NSNAP" -gt 0 || { echo "READOUT_NOTHING_PRESENT"; exit 1; }',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        f'OUT={out}',
        'if [ -n "$MISSING" ]; then OUT="$OUT-partial-$(date -u +%Y%m%dT%H%M%SZ)"; fi',
        'echo "READOUT_ARMS only=$ONLY indices=$IDX missing=${MISSING:- none}"',
        'mkdir -p "$OUT"',
        'CERT=0; A26=0',
        f'python -u {CAMPAIGN_DIR}/certify_ebops.py --run-root {run_root}/runs --cache {DATA_ROOT}/n64/data '
        f'--out "$OUT/certify-snapshot-{READOUT_EPOCH:04d}.json" --snapshot {READOUT_EPOCH} '
        '--only "$ONLY" || CERT=$?',
        f'python -u /work/code/analysis/attn_entropy.py --indices $IDX '
        f'--epoch {READOUT_EPOCH} --out "$OUT/a26-entropy-epoch-{READOUT_EPOCH:04d}.json" || A26=$?',
        'sha256sum "$OUT"/*.json',
        'echo "READOUT_JOB_DONE certify_exit=$CERT a26_exit=$A26 missing=${MISSING:- none}"',
        'test "$CERT" = 0 && test "$A26" = 0',
    ]) + '\n'


def readout_tail(names_by_index, indices, run_root, label):
    names = [names_by_index[i] for i in indices]
    out = f'{run_root}/readout-epoch-{READOUT_EPOCH:04d}-$BUNDLE6-{label}'
    return '\n'.join([
        # every pilot run has paused at 500 (snapshot written) or recorded a divergence
        f'for n in {" ".join(names)}; do',
        f'  test -f {run_root}/runs/$n/snapshots/epoch-{READOUT_EPOCH:04d}/state.json '
        f'|| test -f {run_root}/runs/$n/DIVERGED.json || {{ echo "SNAPSHOTS_NOT_READY $n"; exit 1; }}',
        'done',
        f'test -f {DATA_ROOT}/n64/data/READY.json || {{ echo "CACHE_NOT_READY"; exit 1; }}',
        f'OUT={out}',
        'mkdir -p "$OUT"',
        'CERT=0; A26=0',
        # [D20] STUDY Budget/pilot "Certification check": full training split, same trace batch
        f'python -u {CAMPAIGN_DIR}/certify_ebops.py --run-root {run_root}/runs --cache {DATA_ROOT}/n64/data '
        f'--out "$OUT/certify-snapshot-{READOUT_EPOCH:04d}.json" --snapshot {READOUT_EPOCH} '
        f'--only {",".join(names)} || CERT=$?',
        # [A26] attention entropy (validation split only) and Q/K, V 0-bit fractions
        f'python -u /work/code/analysis/attn_entropy.py --indices {" ".join(map(str, indices))} '
        f'--epoch {READOUT_EPOCH} --out "$OUT/a26-entropy-epoch-{READOUT_EPOCH:04d}.json" || A26=$?',
        'sha256sum "$OUT"/*.json',
        'echo "READOUT_JOB_DONE certify_exit=$CERT a26_exit=$A26"',
        'test "$CERT" = 0 && test "$A26" = 0',
    ]) + '\n'


def volumes(cm, work='24Gi', fingerprint=False):
    # work: the emptyDir limit equals the container's ephemeral-storage limit (gate v2 flag 5:
    # the 77f1ca4e readout had 24Gi against 12Gi)
    out = [{'name': 'code', 'configMap': {'name': cm, 'defaultMode': 420}},
           {'name': 'work', 'emptyDir': {'sizeLimit': work}},
           {'name': 'persistent', 'persistentVolumeClaim': {'claimName': 'kai-data'}}]
    if fingerprint:
        out.append({'name': 'fingerprint', 'configMap': {'name': fp_configmap_name(), 'defaultMode': 420}})
    return out


MOUNTS = [{'mountPath': '/cmcode', 'name': 'code', 'readOnly': True},
          {'mountPath': '/work', 'name': 'work'},
          {'mountPath': '/data', 'name': 'persistent'}]


def res(**kw):
    return {'requests': dict(kw), 'limits': dict(kw)}


def cache_job(cm, bundle, msha):
    labels = {**LABELS, 'app': 'kai-chang0926-cache'}
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': f'kai-chang0926-cache-{bundle[:6]}', 'namespace': 'cms-ml', 'labels': labels},
            'spec': {'backoffLimit': 0, 'activeDeadlineSeconds': 7200, 'ttlSecondsAfterFinished': 604800,
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {
                             'nodeSelectorTerms': [{'matchExpressions': [
                                 {'key': 'kubernetes.io/hostname', 'operator': 'NotIn', 'values': BAD_NODES}]}]}}},
                         'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'prepare', 'image': 'python:3.12', 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'],
                                         'args': [header(bundle, msha, cpu=True) + cache_tail()],
                                         'resources': res(cpu='4', memory='16Gi', **{'ephemeral-storage': '12Gi'}),
                                         'volumeMounts': MOUNTS}],
                         'volumes': volumes(cm)}}}}


def pilot_job(cm, bundle, msha, label, packs_file, pack, arms, fallback=False, names=()):
    """Regime-B pilot pod: same shape as the regime-A pilot (Indexed, 1 pod, podFailurePolicy
    Ignore on DisruptionTarget, no activeDeadlineSeconds); historical pilot A10 assignment,
    c6017 and nrp_doctor's
    KNOWN_BAD_NODES excluded (gate v3 A1); the GPU fingerprint gate before run_pack; K arms at about
    2 CPU and PER_ARM_MEMORY_GI (8 Gi since 2026-09-28) each (rule PACK sizes about 6 Gi). fallback=True: the K=3 OOM fallback (gate v3 B4), the pack
    written inline, same bundle, run root and stage."""
    labels = {**LABELS, 'app': f'kai-chang0926-pilot-{label}', 'bnjettag.io/arms-per-pod': str(arms)}
    gpu_expr = lambda values: {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': values}
    extra = {}
    if fallback and arms == 1:
        extra['bnjettag.io/single-arm-justified'] = (
            'registered OOM fallback for the K=3 pilot-b pod (PREFLIGHT gate v3 B4): the arm OOMed beside '
            'two others, so it runs alone')
    if fallback:
        extra['bnjettag.io/fallback-for'] = 'kai-chang0926-pilotb3-' + bundle[:6]
    tail = (pilot_tail('/work/fallback_packs.json', json.dumps(pack), names) if fallback
            else pilot_tail(packs_file))
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': f'kai-chang0926-pilot{label}-{bundle[:6]}', 'namespace': 'cms-ml', 'labels': labels,
                         'annotations': {**extra,
                                         'bnjettag.io/pack': f'{packs_file} {json.dumps(pack)}',
                                         'bnjettag.io/gpu-fingerprint': (
                                             f'{fp_configmap_name()} sha256 {FP_SHA[:16]}: {FP_RUN} initial_ebops == '
                                             f'{FP_EXPECT} before any arm, else exit 9 (Delta REGRESSION_TICKET)'),
                                         'bnjettag.io/regime': 'B: [D20] trace every 10 epochs (train.ebops_trace_every)',
                                         'bnjettag.io/active-deadline': 'unset on purpose (STUDY Resume)',
                                         'bnjettag.io/per-arm-memory': (
                                             f'{PER_ARM_MEMORY_GI}Gi: measured start RSS 2,106-2,160 MB; RSS gate requires '
                                             f'baseline + slope x train.epochs <= {RSS_GATE_LIMIT_MB} MiB (INCIDENT_stall_20260928)'),
                                         'bnjettag.io/rss-gate': f'projection <= {RSS_GATE_LIMIT_MB} MiB, fit over process epochs {RSS_GATE_WINDOW}'}},
            'spec': {'completionMode': 'Indexed', 'completions': 1, 'parallelism': 1,
                     'backoffLimitPerIndex': 2, 'podReplacementPolicy': 'Failed',
                     'ttlSecondsAfterFinished': 604800,
                     'podFailurePolicy': {'rules': [
                         {'action': 'Ignore', 'onPodConditions': [{'type': 'DisruptionTarget'}]},
                         # every arm diverged at epoch 0: a replacement pod would skip them all and "succeed"
                         {'action': 'FailJob', 'onExitCodes': {'containerName': 'train', 'operator': 'In',
                                                               'values': [EXIT_EPOCH0_ALL_DIVERGED]}}]},
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'affinity': {'nodeAffinity': {
                             'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{
                                 'matchExpressions': [gpu_expr(PILOT_B_GPU_REQUIRED),
                                                      {'key': 'kubernetes.io/hostname', 'operator': 'NotIn',
                                                       'values': PILOT_B_BAD_NODES}]}]}}},
                         'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'train', 'image': 'python:3.12', 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'],
                                         'args': [header(bundle, msha, cpu=False) + tail],
                                         # W&B key from the kai-wandb secret, as every past campaign.
                                         'env': [{'name': 'WANDB_API_KEY', 'valueFrom': {'secretKeyRef': {
                                             'name': 'kai-wandb', 'key': 'WANDB_API_KEY'}}},
                                                 {'name': 'NODE_NAME', 'valueFrom': {'fieldRef': {
                                                     'fieldPath': 'spec.nodeName'}}}],
                                         'resources': res(cpu=str(2 * arms), memory=f'{PER_ARM_MEMORY_GI * arms}Gi',
                                                          **{'ephemeral-storage': '24Gi', 'nvidia.com/gpu': '1'}),
                                         'volumeMounts': MOUNTS + [{'mountPath': FP_MOUNT, 'name': 'fingerprint',
                                                                    'readOnly': True}]}],
                         'volumes': volumes(cm, fingerprint=True)}}}}


def readout_job(cm, bundle, msha, names_by_index, indices, run_root, stage, label, partial=False):
    labels = {**LABELS, 'app': 'kai-chang0926-readout'}
    tail = readout_tail_partial if partial else readout_tail
    bad = PILOT_B_BAD_NODES if partial else BAD_NODES
    script = (header(bundle, msha, cpu=True, run_root=run_root, stage=stage) + f'BUNDLE6={bundle[:6]}\n'
              + tail(names_by_index, indices, run_root, label))
    return {'apiVersion': 'batch/v1', 'kind': 'Job',
            'metadata': {'name': f'kai-chang0926-readout{label}-{bundle[:6]}', 'namespace': 'cms-ml', 'labels': labels,
                         'annotations': {'bnjettag.io/readout': f'epoch-{READOUT_EPOCH} snapshots under {run_root}: '
                                                                 'certify_ebops.py + analysis/attn_entropy.py',
                                         'bnjettag.io/runs': ','.join(names_by_index[i] for i in indices)}},
            'spec': {'backoffLimit': 0, 'activeDeadlineSeconds': 14400, 'ttlSecondsAfterFinished': 604800,
                     'template': {'metadata': {'labels': labels}, 'spec': {
                         'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {
                             'nodeSelectorTerms': [{'matchExpressions': [
                                 {'key': 'kubernetes.io/hostname', 'operator': 'NotIn', 'values': bad}]}]}}},
                         'automountServiceAccountToken': False,
                         'nodeSelector': {'kubernetes.io/arch': 'amd64'},
                         'restartPolicy': 'Never', 'terminationGracePeriodSeconds': 180,
                         'containers': [{'name': 'readout', 'image': 'python:3.12', 'imagePullPolicy': 'IfNotPresent',
                                         'command': ['bash', '-c'], 'args': [script],
                                         'resources': res(cpu='8', memory='24Gi', **{'ephemeral-storage': '12Gi'}),
                                         'volumeMounts': MOUNTS}],
                         'volumes': volumes(cm, work='12Gi')}}}}


def write_pilot_b_jobs(cm, bundle, msha, names):
    """The regime-B pilot, fallback and readout-b Jobs plus the fingerprint ConfigMap."""
    written = {}
    fp = fp_configmap()
    (HERE / f'configmap-fp-{FP_SHA[:8]}.json').write_text(json.dumps(fp, indent=2) + '\n')
    written[f'configmap-fp-{FP_SHA[:8]}.json'] = fp['metadata']['name']
    for label, arms in (('k5', 5), ('k3', 3)):
        packs_file, pack = PILOT_B[label]
        job = pilot_job(cm, bundle, msha, 'b' + label[1], packs_file, pack, arms)
        script = job['spec']['template']['spec']['containers'][0]['args'][0]
        assert f'export BNJ_STAGE={STAGE}' in script and f'BNJ_RUN_ROOT={RUN_ROOT} ' in script
        assert 'activeDeadlineSeconds' not in job['spec'] and job['spec']['podFailurePolicy']
        assert script.index('fingerprint_check.py --run') < script.index('run_pack.py')
        path = HERE / f'pilot-b-{label}-job.json'
        path.write_text(json.dumps(job, indent=2) + '\n')
        written[path.name] = job['metadata']['name']
        readout = readout_job(cm, bundle, msha, names, pack[0], RUN_ROOT, STAGE, 'b' + label[1], partial=True)
        path = HERE / f'readout-b{label[1]}-job.json'
        path.write_text(json.dumps(readout, indent=2) + '\n')
        written[path.name] = readout['metadata']['name']
    for idx in FALLBACKS:
        assert set(idx) <= set(PILOT_B['k3'][1][0]), idx
        tag = 'fb' + '-'.join(map(str, idx))
        job = pilot_job(cm, bundle, msha, 'b' + tag, 'fallback', [idx], len(idx), fallback=True,
                        names=[names[i] for i in idx])
        path = HERE / f'pilot-b-{tag}-job.json'
        path.write_text(json.dumps(job, indent=2) + '\n')
        written[path.name] = job['metadata']['name']
    return written


def jobs_only():
    """PREFLIGHT gate v3 (2026-09-28): regenerate the pilot-b, fallback and readout-b Jobs and the
    fingerprint ConfigMap WITHOUT re-freezing: the tarball on disk and a rebuild must both be
    42abed4b; no tarball, configmap.json or bundle-manifest is written."""
    names = check_campaign()
    msha = manifest_sha()
    assert msha == EXPECTED_MANIFEST, msha
    on_disk = sha((HERE / 'chang0926-code.tar.gz').read_bytes())
    rebuilt = sha(build_tarball()[0])
    assert on_disk == rebuilt == BUNDLE_42, (on_disk, rebuilt)
    cm = 'kai-chang0926-code-' + BUNDLE_42[:10]
    assert json.loads((HERE / 'configmap.json').read_text())['metadata']['name'] == cm
    print('BUNDLE_SHA256', on_disk, '(unchanged, not rewritten)')
    print('MANIFEST_SHA256', msha)
    print('CONFIGMAP', cm, '(unchanged)')
    print('FINGERPRINT_CONFIGMAP', fp_configmap_name(), 'sha256', FP_SHA)
    print('PILOT_B_BAD_NODES', ' '.join(PILOT_B_BAD_NODES))
    for f, n in write_pilot_b_jobs(cm, BUNDLE_42, msha, names).items():
        print('JOB', f, n)


def main():
    if '--jobs-only' in sys.argv[1:]:
        return jobs_only()
    names = check_campaign()
    msha = manifest_sha()
    assert msha == EXPECTED_MANIFEST, msha
    payload, files = build_tarball()
    bundle = sha(payload)
    assert bundle != REGIME_A['bundle']
    assert len(base64.b64encode(payload)) < 1_000_000, len(payload)
    cm = 'kai-chang0926-code-' + bundle[:10]
    (HERE / 'chang0926-code.tar.gz').write_bytes(payload)
    configmap = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
                 'metadata': {'name': cm, 'namespace': 'cms-ml',
                              'labels': LABELS, 'annotations': {'bnjettag.io/bundle-sha256': bundle,
                                                                'bnjettag.io/manifest-sha256': msha}},
                 'binaryData': {KEY: base64.b64encode(payload).decode()}}
    (HERE / 'configmap.json').write_text(json.dumps(configmap) + '\n')
    # sha-named copy, kept beside the 77f1ca4e one so a later re-freeze cannot overwrite it
    (HERE / f'configmap-{bundle[:8]}.json').write_text(json.dumps(configmap) + '\n')
    written = write_pilot_b_jobs(cm, bundle, msha, names)
    # regime-A readout: the 77f1ca4e ConfigMap and manifest (the code that trained the pilot)
    ra = readout_job(REGIME_A['configmap'], REGIME_A['bundle'], REGIME_A['manifest'], names,
                     REGIME_A['indices'], REGIME_A['run_root'], REGIME_A['stage'], 'a')
    (HERE / 'readout-a-job.json').write_text(json.dumps(ra, indent=2) + '\n')
    written['readout-a-job.json'] = ra['metadata']['name']
    (HERE / 'bundle-manifest.json').write_text(json.dumps({
        'bundle_sha256': bundle, 'manifest_sha256': msha, 'configmap': cm, 'key': KEY,
        'bytes': len(payload), 'regime': 'B ([D20] trace every 10 epochs)',
        'pilot_b': {k: {'packs_file': v[0], 'pack': v[1], 'runs': [names[i] for i in v[1][0]]} for k, v in PILOT_B.items()},
        'data_root': DATA_ROOT, 'run_root': RUN_ROOT, 'stage': STAGE, 'campaign_dir': CAMPAIGN_DIR,
        'jobs': written, 'regime_a_record': {**REGIME_A, 'files': ['configmap-77f1ca4e.json',
                                                                   'bundle-manifest-77f1ca4e.json',
                                                                   'pilot-job.json', 'readout-job.json',
                                                                   'readout-a-job.json']},
        'analysis_files_outside_manifest': sorted(rel for rel, _ in files if rel.startswith('analysis/')),
        'files': {rel: sha(p.read_bytes()) for rel, p in files}}, indent=2) + '\n')
    (HERE / f'bundle-manifest-{bundle[:8]}.json').write_bytes((HERE / 'bundle-manifest.json').read_bytes())
    print('BUNDLE_SHA256', bundle)
    print('MANIFEST_SHA256', msha)
    print('CONFIGMAP', cm, 'bytes', len(payload), 'files', len(files))
    for f, n in written.items():
        print('JOB', f, n)


if __name__ == '__main__':
    main()
