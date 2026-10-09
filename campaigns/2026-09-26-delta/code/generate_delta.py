#!/usr/bin/env python3
"""Generate every Delta config from delta.json and the anchor's own arm configs. Never submits.

    python3 generate_delta.py                       # screen tier on the anchor bundle in anchor_arms.json (42abed4b), strict
    python3 generate_delta.py --skip-invalid        # write what is valid, record the rest in index.json
    python3 generate_delta.py --tier confirm        # confirm tier (seeds_confirm, targets_confirm) -> configs/confirm
    python3 generate_delta.py --standin --out configs-standin   # tarball stand-in, for tests_patches only

Pipeline (WIRING.md): generate_delta.py -> apply_anchor.sh -> trace_floors_delta.py (writes
floors_delta.json) -> generate_delta.py again (floors set) -> classify_series.py -> gate_cpu.py
-> annotate_index.py -> manifest_wave2.py.

Base (anchor_arms.json). Each cell (entry x target x seed) starts from the anchor's generated
config for its base arm AT THAT SEED (code/campaigns/chang0926/configs/chang0926-<arm>-n64-s<seed>.json
inside the sha-checked anchor pilot bundle 77f1ca4e), so experiment.seed and train.order_seed are
the anchor's ([D9] order_seed = 20260926 * 100 + s, generate.py:37; asserted). Seeds with no
anchor config (the teachers' seed 101) start from the seed-1 file with seed and order_seed set by
that formula (flag seed_outside_anchor_configs). The anchor's `campaign` block is removed (it
describes a training-batch run, production true); identity is replaced: name
delta0926-<wave>-<run_id>, experiment.arm = name, experiment.group delta-20260926-<wave>,
train.wandb_project BNJetTag-Delta, engram_study.question the cell, and a `delta_study`
provenance block (validator PROVENANCE; it enters digest_json, so it is part of the resume identity).
Then the entry's config_delta (value_map applied: pt_gate 0 -> null, optimizer adam -> adam_ours),
target -> train.ebops.pid.target_ebops, H -> train.epochs, '=horizon' -> H, and the always-on keys.

Zero floor. experiment.nondegenerate.zero_floor_ebops is read at run time (ablation.py, the
[ND] feasibility rule), so a cell whose arch or quant section differs from its arm must carry its
own traced 0-bit floor. The floor depends on arch + quant only (the anchor's floor_signature);
generate_delta.py looks the signature up in floors_delta.json (static_floor.floors on the
apply_anchor.sh tree, CPU, synthetic sample, the anchor's own procedure). Unchanged signature:
the anchor's value. No trace: the base value stays in the file, the row is flagged
floor_untraced and manifest_wave2.py does not pack it.

Cache. Each row carries cache_key (anchor_arms.json cache.identity_keys) and data_root: the
anchor's gated 90/10 cache /data/chang-n64-20260926 (split_seed 1) when the key equals arm A's,
else /data/delta-20260927/caches/<key8> (flag cache_not_built: the wave-2 STUDY's Z10 caches).

Wave-2 lists (wave2_amendments.json, from the frozen wave-2 STUDY 24c3c90): placebo cells P-350 / P-5M
and replica seeds 1-8; rows flagged study_frozen_list.

Checks: a delta key absent from the base must be registered by a slug in the entry's own
code_changes (register() lines of patches-anchor/, or key_registry.json) or be runner-live; null
values and placeholder strings are refused except key_registry.json null_whitelist; extra_delta
must equal config_delta. The applied tree's own strict validator (classify_series.py) is the ground truth.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
LAB = CAMPAIGN.parents[1]
DELTA = CAMPAIGN / 'delta.json'
REGISTRY = HERE / 'key_registry.json'
ARMS = HERE / 'anchor_arms.json'
FLOORS = HERE / 'floors_delta.json'
AMEND = HERE / 'wave2_amendments.json'
LEDGER = HERE / 'README.md'
TARBALL = LAB / 'campaigns/2026-09-22-constituent-screen/study-code.tar.gz'
TARBALL_SHA = '26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45'
STANDIN_MEMBER = 'code/configs/const0922-a07-n64-s1-fast50-fp32.json'
CONFIRM_H_DEFAULT = 7000   # DELTA.md §5.1: the full recipe; used only if an entry has no confirm horizon
NAME_PREFIX = 'delta0926'
GROUP_PREFIX = 'delta-20260926'
WANDB_PROJECT = 'BNJetTag-Delta'
CONFIRM_WAVE = 'w4'        # STUDY.md: delta-20260926-w4 (confirm)
IDENTITY_KEYS = {'name', 'experiment.arm', 'experiment.group', 'engram_study.question', 'train.epochs'}
VALUE_MAP, ALWAYS_ON = {}, {}   # filled in main() from key_registry.json


class GenError(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ bases
def load_anchor_bundle(spec, path_override=None, sha_override=None):
    """(bytes, path) of the anchor bundle, sha256-checked; tries the tarball, then the ConfigMap payload.
    --anchor-bundle / --anchor-sha replace both (the regime-B production bundle, next rebase)."""
    want = sha_override or spec['anchor_bundle']['sha256']
    seen = []
    for rel in ([str(path_override)] if path_override else spec['anchor_bundle']['paths_tried_in_order']):
        path = LAB / rel
        if not path.exists():
            seen.append(f'{rel}: missing')
            continue
        raw = path.read_bytes()
        if rel.endswith('.json'):
            raw = base64.b64decode(json.loads(raw)['binaryData']['hgq2.tar.gz'])
        got = sha256_bytes(raw)
        if got == want:
            return raw, rel
        seen.append(f'{rel}: sha256 {got[:12]}')
    raise GenError(f'no anchor bundle with sha256 {want[:12]} ({"; ".join(seen)})')


class AnchorBase:
    def __init__(self, spec, path_override=None, sha_override=None):
        raw, self.source = load_anchor_bundle(spec, path_override, sha_override)
        self.sha = sha_override or spec['anchor_bundle']['sha256']
        self.spec = spec
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tar:
            self.members = {m.name: tar.extractfile(m).read() for m in tar.getmembers()
                            if m.isfile() and m.name.startswith('code/campaigns/chang0926/configs/')}
        rule = spec['order_seed_rule']
        self.order_seed = lambda s: int(rule['base']) * 100 + int(s)

    def config(self, arm, seed):
        """(cfg, member, sha256, flags) for arm at seed."""
        flags = []
        pattern = self.spec['config_member']
        file_arm = self.spec['arms'][arm]['file_arm']
        member = pattern.format(file_arm=file_arm, seed=seed)
        if member not in self.members:
            member = pattern.format(file_arm=file_arm, seed=1)
            flags.append('seed_outside_anchor_configs')
        data = self.members[member]
        cfg = json.loads(data)
        if 'seed_outside_anchor_configs' in flags:
            cfg['experiment']['seed'] = int(seed)
            cfg['train']['order_seed'] = self.order_seed(seed)
        if cfg['experiment']['seed'] != int(seed) or cfg['train']['order_seed'] != self.order_seed(seed):
            raise GenError(f'{member}: seed/order_seed {cfg["experiment"]["seed"]}/{cfg["train"]["order_seed"]} '
                           f'!= {seed}/{self.order_seed(seed)} ([D9] rule)')
        return cfg, member, sha256_bytes(data), flags

    def label(self):
        return f'anchor bundle {self.sha[:8]} ({self.source}), per-seed arm configs'


class StandinBase:
    """Screen-tarball stand-in (configs-standin/ for the tarball series' tests only)."""

    def __init__(self, spec):
        raw = TARBALL.read_bytes()
        if sha256_bytes(raw) != TARBALL_SHA:
            raise GenError('screen tarball sha256 mismatch')
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tar:
            self.data = tar.extractfile(STANDIN_MEMBER).read()
        self.sha = TARBALL_SHA
        self.arms = spec['standin']['arms']

    def config(self, arm, seed):
        cfg = json.loads(self.data)
        for k, v in self.arms[arm]['delta'].items():
            set_path(cfg, k, copy.deepcopy(v))
        cfg['experiment']['seed'] = int(seed)
        return cfg, STANDIN_MEMBER, sha256_bytes(self.data), ['stand_in_base', 'order_seed_standin']

    def label(self):
        return f'STAND-IN {STANDIN_MEMBER} from study-code.tar.gz {TARBALL_SHA[:12]} (tests only, never packed)'


def load_standin():
    """Stand-in base config (tests/conftest.py fixture)."""
    b = StandinBase(json.loads(ARMS.read_text()))
    return json.loads(b.data), sha256_bytes(b.data)


# ------------------------------------------------------------------ helpers
def flat(d, prefix=''):
    """{dotted leaf path: value}; an empty dict is a leaf."""
    out = {}
    for k, v in d.items():
        key = prefix + k
        if isinstance(v, dict) and v:
            out.update(flat(v, key + '.'))
        else:
            out[key] = v
    return out


def flat_keys(d, prefix=''):
    out = set()
    for k, v in d.items():
        key = prefix + k
        out.add(key)
        if isinstance(v, dict):
            out |= flat_keys(v, key + '.')
    return out


def set_path(cfg, dotted, value):
    parts = dotted.split('.')
    node = cfg
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict):
            node[p] = {}
        node = node[p]
    node[parts[-1]] = value


def get_path(cfg, dotted, default=None):
    node = cfg
    for p in dotted.split('.'):
        if not isinstance(node, dict) or p not in node:
            return default
        node = node[p]
    return node


def floor_signature(cfg):
    """The anchor's floor_signature (generate.py:135): sha256 of the arch and quant sections."""
    return hashlib.sha256(json.dumps({k: cfg[k] for k in ('arch', 'quant')}, sort_keys=True).encode()).hexdigest()


def cache_key(cfg, keys):
    ident = {k: get_path(cfg, k) for k in keys}
    return hashlib.sha256(json.dumps(ident, sort_keys=True).encode()).hexdigest(), ident


def ledger_status():
    """slug -> status cell from code/README.md (the shared ledger), if present."""
    if not LEDGER.exists():
        return {}
    status = {}
    for line in LEDGER.read_text().splitlines():
        if not line.lstrip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 3:
            slug = cells[0].strip('`')
            if re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug) and slug != 'slug':
                status[slug] = cells[2]
    return status


def is_placeholder_string(v):
    return isinstance(v, str) and (v.startswith('per ') or 'ml-engineer' in v or 'TBD' in v)


def wave_dir(wave):
    """Filesystem- and W&B-safe wave label ('confirm-only (offered at K3)' -> 'confirm-only-offered-at-K3')."""
    return re.sub(r'[^A-Za-z0-9]+', '-', str(wave)).strip('-')


def subst_horizon(value, horizon):
    if value == '=horizon':
        return horizon
    if isinstance(value, dict):
        return {k: subst_horizon(v, horizon) for k, v in value.items()}
    if isinstance(value, list):
        return [subst_horizon(v, horizon) for v in value]
    return value


def base_arm(entry, target, spec, no_cell_arm=None):
    """Config arm for a cell, from the free-text entry.base[str(target)] via spec['base_text_rules']."""
    arms = spec['arms']
    text = (entry.get('base') or {}).get(str(int(target)))
    if text is None:
        raise GenError(f"{entry['id']}: no base named for target {target}")
    for rule in spec['base_text_rules']:
        m = re.match(rule['regex'], text.strip())
        if not m:
            continue
        if rule['arm'] is None:
            if no_cell_arm is not None:
                return no_cell_arm
            raise GenError(f"{entry['id']}: target {target} is listed but its base says {text!r}")
        arm = m.expand(rule['arm'])
        if arm not in arms:
            raise GenError(f"{entry['id']}: base arm {arm!r} not in anchor_arms.json")
        return arm
    raise GenError(f"{entry['id']}: no base_text_rules match {text!r} (add a rule to anchor_arms.json)")


def load_patch_registry(patch_dir):
    """{key: slug} from every `register('<key>', '<slug>', ...)` line the series adds to
    bnhgq2/delta_keys.py. Read as text; nothing is applied or imported."""
    out = {}
    for p in sorted(Path(patch_dir).glob('[0-9][0-9][0-9][0-9]-*.patch')):
        for line in p.read_text().splitlines():
            m = re.match(r"^\+register\('([^']+)',\s*'([^']+)'", line)
            if m:
                for slug in m.group(2).split(' / '):
                    out.setdefault(m.group(1), set()).add(slug.strip())
    return out


def check_delta(delta, slugs, base_keys, registry, where):
    errors, refusals = [], []
    keys = registry['keys']
    for key, value in delta.items():
        if value is None and key not in registry['null_whitelist']:
            refusals.append(f'{key}=null (to be filled by the wave STUDY)')
        elif is_placeholder_string(value):
            refusals.append(f'{key}={value!r} (placeholder string)')
        if key in base_keys:
            if key == 'quant.weight':
                known = registry['values']['quant.weight']
                if value not in known:
                    errors.append(f'{where}quant.weight={value!r} not registered')
                elif known[value]['slugs'] and not set(known[value]['slugs']) & slugs:
                    errors.append(f'{where}quant.weight={value!r} needs one of {known[value]["slugs"]}; '
                                  f'code_changes {sorted(slugs)}')
            continue
        if registry['patch_keys'].get(key, set()) & slugs:
            continue                       # registered in bnhgq2/delta_keys.py by one of the entry's slugs
        reg = keys.get(key)
        if reg is None:
            errors.append(f'{where}{key}: absent from base and not registered by any patch')
            continue
        if reg.get('runner_live') or set(reg['slugs']) & slugs:
            continue
        errors.append(f'{where}{key}: registered by {reg["slugs"]} but code_changes={sorted(slugs)}')
    return errors, refusals


BASE_OWNED = ('train.ebops_trace_every', 'train.split_seed', 'train.validation_split', 'train.order_seed')


def check_entry(entry, base_keys, registry):
    slugs = set(entry['code_changes'])
    delta = entry['config_delta']
    errors, refusals = check_delta(delta, slugs, base_keys, registry, '')
    for k in BASE_OWNED:     # carried from the anchor base config, never overridden (pairing, [D15] cadence)
        if k in delta:
            errors.append(f'{k} is owned by the anchor base config and may not be set by a Delta entry')
    for k, v in (entry.get('extra_delta') or {}).items():
        if delta.get(k) != v:
            errors.append(f'extra_delta key {k} differs from config_delta')
    return errors, refusals


# ------------------------------------------------------------------ one config
def make_cfg(base_cfg, deltas, *, run_id, wave, target, seed, horizon, entry_id, kind, tier, base_label,
             base_member, base_sha, arm, flags, floors, question, extra_provenance=None):
    cfg = copy.deepcopy(base_cfg)
    base_signature = floor_signature({k: base_cfg[k] for k in ('arch', 'quant')})
    base_floor = get_path(base_cfg, 'experiment.nondegenerate.zero_floor_ebops')
    cfg.pop('campaign', None)                      # the anchor generator's provenance (training-batch run)
    set_keys = []
    for delta in deltas:
        for key, value in delta.items():
            set_path(cfg, key, copy.deepcopy(subst_horizon(value, horizon)))
            set_keys.append(key)
    for key, vm in (VALUE_MAP or {}).items():
        if key in set_keys and get_path(cfg, key, object()) == vm['from']:
            set_path(cfg, key, vm['to'])
            flags.append(vm['flag'])
    if tier == 'screen' and kind != 'prerequisite_teacher':
        for slug, spec in (ALWAYS_ON or {}).items():
            if spec.get('key'):
                set_path(cfg, spec['key'], copy.deepcopy(spec['value']))
    set_path(cfg, 'train.ebops.pid.target_ebops', int(target) if float(target).is_integer() else target)
    set_path(cfg, 'experiment.seed', int(seed))
    set_path(cfg, 'train.epochs', int(horizon))
    wtoken = CONFIRM_WAVE if tier == 'confirm' else wave_dir(wave).lower()
    name = f'{NAME_PREFIX}-{"standin-" if "stand_in_base" in flags else ""}{wtoken}-{run_id.lower()}'
    cfg['name'] = name
    set_path(cfg, 'experiment.arm', name)
    set_path(cfg, 'experiment.group', f'{GROUP_PREFIX}-{wtoken}' + ('-standin' if 'stand_in_base' in flags else ''))
    set_path(cfg, 'train.wandb_project', WANDB_PROJECT)
    if 'engram_study' in cfg:
        cfg['engram_study']['question'] = question
    # zero floor: arch/quant signature after the delta
    floor = {'value': base_floor, 'source': 'anchor arm config (signature unchanged)'}
    if 'nondegenerate' in cfg.get('experiment', {}):
        sig = floor_signature(cfg)
        if sig != base_signature:
            hit = (floors or {}).get(sig)
            if hit is not None and hit.get('zero') is not None:
                cfg['experiment']['nondegenerate']['zero_floor_ebops'] = int(hit['zero'])
                floor = {'value': int(hit['zero']), 'source': f'floors_delta.json (traced on {hit.get("config")})'}
                if int(hit['zero']) != base_floor:
                    flags.append('zero_floor_retraced')
            else:
                floor = {'value': base_floor, 'source': 'UNTRACED: inherited from the arm; not packable',
                         'trace_error': (hit or {}).get('error')}
                flags.append('floor_untraced')
        floor['signature'] = sig
    cfg['delta_study'] = {
        'campaign': 'campaigns/2026-09-26-delta', 'entry': entry_id, 'kind': kind, 'wave': wave,
        'tier': tier, 'base_arm': arm, 'target_ebops': target, 'seed': int(seed), 'horizon_epochs': int(horizon),
        'base': base_label, 'base_config': base_member, 'base_config_sha256': base_sha,
        'stand_in_base': 'stand_in_base' in flags, 'flags': sorted(set(flags)),
        **(extra_provenance or {}),
    }
    return cfg, floor


def diff_keys(a, b, ignore=()):
    fa, fb = flat(a), flat(b)
    return sorted(k for k in set(fa) | set(fb)
                  if fa.get(k, '<absent>') != fb.get(k, '<absent>') and not any(
                      k == i or k.startswith(i + '.') for i in ignore))


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tier', choices=('screen', 'confirm'), default='screen')
    ap.add_argument('--standin', action='store_true', help='tarball stand-in base (configs-standin/, tests only)')
    ap.add_argument('--delta', type=Path, default=DELTA)
    ap.add_argument('--out', type=Path, default=None, help='default configs/ (configs-standin/ with --standin)')
    ap.add_argument('--floors', type=Path, default=FLOORS)
    ap.add_argument('--amendments', type=Path, default=AMEND, help='wave2_amendments.json ("none" to skip)')
    ap.add_argument('--skip-invalid', action='store_true',
                    help='write valid entries and record invalid ones in index.json instead of aborting')
    ap.add_argument('--confirm-350k-base', default='A',
                    help="confirm tier: arm for targets whose screen base says 'no ... screen cell' (default A)")
    ap.add_argument('--no-prereq', action='store_true', help='skip teacher configs (P-T1, P-T2)')
    ap.add_argument('--anchor-bundle', type=Path, default=None,
                    help='anchor bundle tar.gz (or ConfigMap JSON); default anchor_arms.json paths (77f1ca4e)')
    ap.add_argument('--anchor-sha', default=None, help='expected sha256 of --anchor-bundle')
    args = ap.parse_args(argv)
    if bool(args.anchor_bundle) != bool(args.anchor_sha):
        ap.error('--anchor-bundle and --anchor-sha go together')

    delta_bytes = args.delta.read_bytes()
    delta = json.loads(delta_bytes)
    registry = json.loads(REGISTRY.read_text())
    registry['patch_keys'] = load_patch_registry(HERE / ('patches' if args.standin else 'patches-anchor'))
    global VALUE_MAP, ALWAYS_ON
    VALUE_MAP = {k: v for k, v in registry.get('value_map', {}).items() if not k.startswith('_')}
    ALWAYS_ON = {k: v for k, v in registry.get('always_on', {}).items()
                 if not k.startswith('_') and k in (delta.get('always_on_diagnostics') or [])}
    spec = json.loads(ARMS.read_text())
    base = StandinBase(spec) if args.standin else AnchorBase(spec, args.anchor_bundle, args.anchor_sha)
    stand_in = args.standin
    out_default = HERE / ('configs-standin' if stand_in else 'configs')
    out_root = (args.out or out_default) if args.tier == 'screen' else (args.out or out_default) / 'confirm'
    floors = {} if stand_in or not args.floors.exists() else json.loads(args.floors.read_text())['signatures']
    amend = None
    if args.tier == 'screen' and str(args.amendments) != 'none' and Path(args.amendments).exists():
        amend = json.loads(Path(args.amendments).read_text())
    cache_spec = spec['cache']
    ledger = ledger_status()
    tier = args.tier

    a_cfg = base.config('A', 1)[0]
    anchor_cache_key, anchor_cache_ident = cache_key(a_cfg, cache_spec['identity_keys'])
    base_keys = flat_keys(a_cfg)

    def cells(entry):
        seeds = entry['seeds_screen'] if tier == 'screen' else entry['seeds_confirm']
        targets = entry['targets'] if tier == 'screen' else entry['targets_confirm']
        horizon = (entry['horizon_screen_epochs'] if tier == 'screen'
                   else entry.get('horizon_confirm_epochs', CONFIRM_H_DEFAULT))
        for target in targets:
            arm = base_arm(entry, target, spec, None if tier == 'screen' else args.confirm_350k_base)
            for seed in seeds:
                yield target, seed, horizon, arm

    def entry_base_keys(e):
        keys = set(base_keys)
        for target in (e['targets'] if tier == 'screen' else e['targets_confirm']):
            arm = base_arm(e, target, spec, None if tier == 'screen' else args.confirm_350k_base)
            keys |= flat_keys(base.config(arm, 1)[0])
        return keys

    checked = {e['id']: check_entry(e, entry_base_keys(e), registry) for e in delta['entries']}
    problems = {i: c[0] for i, c in checked.items() if c[0]}
    if problems and not args.skip_invalid:
        for i, errs in problems.items():
            for e in errs:
                print(f'ERROR {i}: {e}', file=sys.stderr)
        print(f'FAILED: {len(problems)} entries with unregistered keys; nothing written', file=sys.stderr)
        return 2

    rows, counts = [], {}
    replica_cfgs = {}          # (wave, arm, seed) -> cfg (for the diff-vs-replica column)

    def emit(cfg, rel, row, floor):
        path = out_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(cfg, indent=2) + '\n'
        path.write_text(text)
        ck, ident = cache_key(cfg, cache_spec['identity_keys'])
        on_anchor = ck == anchor_cache_key
        row.update(file=str(path.relative_to(out_root)), name=cfg['name'], config_sha256=sha256_bytes(text.encode()),
                   n_part=cfg['arch']['n_part'], floor=floor, cache_key=ck[:12], cache_identity=ident,
                   data_root=(cache_spec['anchor_data_root'] if on_anchor
                              else f"{cache_spec['delta_cache_root']}/{ck[:8]}"),
                   cache_status='anchor cache (built, PREFLIGHT l. 512)' if on_anchor
                   else 'NOT BUILT (wave-2 STUDY Z10 cache; build with split_seed 1 before packing)')
        if not on_anchor:
            row['flags'].append('cache_not_built')
        if 'floor_untraced' in cfg['delta_study']['flags']:
            row['flags'].append('floor_untraced')
        if cfg['arch'].get('pos_enc') == 'none' and not cfg['arch'].get('pos_enc_none_consume_rng'):
            row['flags'].append('pos_enc_none_without_consume_rng')
        assert cfg['train']['split_seed'] == a_cfg['train']['split_seed'] and \
            cfg['train']['validation_split'] == a_cfg['train']['validation_split'], row['run_id']
        rows.append(row)
        return cfg

    def base_row(**kw):
        row = {'errors': [], 'refusals': [], 'placeholders': [], 'stand_in_base': stand_in,
               'covered_by_anchor_study': None, 'hw_labels': [], 'launchable': False if stand_in else None}
        row.update(kw)
        return row

    # replicas first (the diff column of every cell needs them)
    replicas = (delta.get('drift_replicas') or {}) if tier == 'screen' else {}
    rep_seed_override = (amend or {}).get('replica_seeds', {})
    wave_seeds = {}
    for entry in delta['entries']:
        if tier != 'screen':
            break
        for target, seed, _, _ in cells(entry):
            wave_seeds.setdefault((entry['wave'], target), set()).add(seed)
    for wave in sorted(k for k in replicas if isinstance(replicas[k], list)):
        for rep in replicas[wave]:
            arm, target, horizon = rep['arm'], rep['target'], int(rep['horizon_epochs'])
            if spec['arms'][arm]['target'] != target:
                raise GenError(f'drift replica {arm} target {target} != anchor arm target')
            override = rep_seed_override.get(wave, {}).get(arm)
            seeds = sorted(override['seeds'] if override else wave_seeds.get((wave, target), set()))
            rep_horizon = horizon
            for seed in seeds:
                run_id = f'REP-{arm}-t{target}-s{seed}'
                bcfg, member, bsha, bflags = base.config(arm, seed)
                pending = bool(override) and seed not in wave_seeds.get((wave, target), set())
                flags = bflags + (['study_frozen_list', 'amended_replica_seed'] if pending else [])
                # frozen STUDY (Drift replicas): seeds above n stop at 500. Config-level stop: train.epochs = 500
                # (the Sun et al. schedule and the PID read epochs 1..H identically at H 500 and 1,000/2,000;
                # launch gate 5), so the runner, the RSS projection and the pack all see 500.
                horizon = int(override.get('extension_seed_horizon', rep_horizon)) if pending else rep_horizon
                if pending and horizon != rep_horizon:
                    flags = flags + ['extension_seed_stops_at_500']
                row = base_row(run_id=run_id, id=f'REP-{arm}', kind='drift_replica', wave=wave, code_tier='T0',
                               base_arm=arm, target=target, seed=seed, horizon=horizon, code_changes=[],
                               patch_status={}, anchor_patches_required=[], status='ready_on_base',
                               flags=flags, serves=rep.get('serves'), gate_eligible=True,
                               anchor_config=member, anchor_config_sha256=bsha)
                cfg, floor = make_cfg(bcfg, [], run_id=run_id, wave=wave, target=target, seed=seed,
                                      horizon=horizon, entry_id=f'REP-{arm}', kind='drift_replica', tier=tier,
                                      base_label=base.label(), base_member=member, base_sha=bsha, arm=arm,
                                      flags=list(flags), floors=floors,
                                      question=f'delta0926 {wave} drift replica of arm {arm} at {target}, seed {seed}')
                counts[wave] = counts.get(wave, 0) + 1
                replica_cfgs[(wave, arm, seed)] = emit(cfg, f'{wave_dir(wave)}/{run_id}.json', row, floor)

    def replica_diff(row, cfg, entry_keys):
        rep = replica_cfgs.get((row['wave'], row['base_arm'], row['seed']))
        if rep is None:
            row['replica'] = None
            return
        d = diff_keys(cfg, rep, ignore=('delta_study',))
        declared = set(entry_keys) | IDENTITY_KEYS | {'train.ebops.pid.target_ebops',
                                                      'experiment.nondegenerate.zero_floor_ebops'}
        row['replica'] = rep['name']
        row['diff_vs_replica'] = d
        row['diff_outside_declared'] = [k for k in d if not any(k == x or k.startswith(x + '.') for x in declared)]
        if row['diff_outside_declared']:
            row['flags'].append('diff_outside_declared')

    for entry in delta['entries']:
        errors = problems.get(entry['id'], [])
        _, refusals = checked[entry['id']]
        wave = entry['wave']
        patch_status = {s: ledger.get(s, 'not started') for s in entry['code_changes']}
        covered = entry.get('covered_by_anchor_study') or {}
        status = ('error' if errors else 'refused_unfilled' if refusals
                  else 'needs_patches' if entry['code_changes'] else 'ready_on_base')
        for target, seed, horizon, arm in cells(entry):
            run_id = f"{entry['id']}-t{target}-s{seed}"
            counts[wave] = counts.get(wave, 0) + 1
            bcfg, member, bsha, bflags = base.config(arm, seed)
            flags = list(bflags) + (['covered_by_anchor_study'] if str(covered.get(str(target), '')).startswith('covered') else [])
            row = base_row(run_id=run_id, id=entry['id'], kind=entry['tier'], wave=wave, code_tier=entry['code_tier'],
                           base_arm=arm, target=target, seed=seed, horizon=horizon,
                           code_changes=entry['code_changes'], patch_status=patch_status,
                           anchor_patches_required=entry['anchor_patches_required'], status=status,
                           errors=errors, refusals=refusals, flags=flags, covered_by_anchor_study=covered or None,
                           hw_labels=entry.get('hw_labels', []), gate_eligible=status == 'ready_on_base',
                           anchor_config=member, anchor_config_sha256=bsha)
            if errors or refusals:
                row.update(file=None, name=None)
                rows.append(row)
                continue
            cfg, floor = make_cfg(bcfg, [entry['config_delta']], run_id=run_id, wave=wave, target=target, seed=seed,
                                  horizon=horizon, entry_id=entry['id'], kind=entry['tier'], tier=tier,
                                  base_label=base.label(), base_member=member, base_sha=bsha, arm=arm,
                                  flags=list(flags), floors=floors,
                                  question=f"delta0926 {entry['id']} ({entry['name']}) on arm {arm} at {target}, "
                                           f"seed {seed}, H {horizon}")
            emit(cfg, f'{wave_dir(wave) if tier == "screen" else wave_dir(wave)}/{run_id}.json', row, floor)
            replica_diff(row, cfg, list(entry['config_delta']) + [s['key'] for s in ALWAYS_ON.values() if s.get('key')])

    # wave-2 lists from the frozen STUDY: placebo cells
    for p in ((amend or {}).get('placebos') or []) if tier == 'screen' else []:
        arm, target, horizon = p['arm'], p['target'], int(p['horizon_epochs'])
        for seed in p['seeds']:
            run_id = f"{p['id']}-t{target}-s{seed}"
            bcfg, member, bsha, bflags = base.config(arm, seed)
            flags = list(bflags) + ['study_frozen_list', 'placebo']
            row = base_row(run_id=run_id, id=p['id'], kind='placebo', wave=p['wave'], code_tier='T0', base_arm=arm,
                           target=target, seed=seed, horizon=horizon, code_changes=[], patch_status={},
                           anchor_patches_required=[], status='ready_on_base', flags=flags, gate_eligible=True,
                           anchor_config=member, anchor_config_sha256=bsha)
            cfg, floor = make_cfg(bcfg, [], run_id=run_id, wave=p['wave'], target=target, seed=seed, horizon=horizon,
                                  entry_id=p['id'], kind='placebo', tier=tier, base_label=base.label(),
                                  base_member=member, base_sha=bsha, arm=arm, flags=list(flags), floors=floors,
                                  question=f"delta0926 {p['wave']} placebo {p['id']} (arm {arm} config, no-op) at {target}, seed {seed}",
                                  extra_provenance={'placebo': p['no_op'], 'amendment_status': amend['status']})
            counts[p['wave']] = counts.get(p['wave'], 0) + 1
            emit(cfg, f"{wave_dir(p['wave'])}/{run_id}.json", row, floor)
            replica_diff(row, cfg, [s['key'] for s in ALWAYS_ON.values() if s.get('key')])

    # prerequisite teachers (DELTA.md §3.4): never gated here (no config-level teacher gate)
    weight_for = {'P-T1': 'none', 'P-T2': 'int8_absmax'}
    if tier == 'screen' and not args.no_prereq:
        for tid, job in (delta.get('prerequisite_jobs') or {}).items():
            if tid not in weight_for:
                continue
            for seed in job['seeds']:
                bcfg, member, bsha, bflags = base.config('A07-350', seed)
                pid_min = get_path(bcfg, 'train.ebops.pid.min_beta')
                tdelta = {'quant.weight': weight_for[tid], 'train.ebops.pid.init_beta': pid_min,
                          'train.ebops.pid.max_beta': pid_min}
                run_id = f'{tid}-s{seed}'
                flags = list(bflags) + ['teacher_definition_provisional']
                row = base_row(run_id=run_id, id=tid, kind='prerequisite_teacher', wave='prereq', code_tier='T1',
                               base_arm='A07-350', target=1e12, seed=seed, horizon=job['epochs'],
                               code_changes=job['patches'],
                               patch_status={s: ledger.get(s, 'not started') for s in job['patches']},
                               anchor_patches_required=[], status='needs_patches',
                               placeholders=['"beta bounds at their minimum" read as init_beta = max_beta = min_beta '
                                             'of the anchor arm (flagged)'],
                               flags=flags, gate_eligible=False, anchor_config=member, anchor_config_sha256=bsha)
                cfg, floor = make_cfg(bcfg, [tdelta], run_id=run_id, wave='prereq', target=1e12, seed=seed,
                                      horizon=job['epochs'], entry_id=tid, kind='prerequisite_teacher', tier=tier,
                                      base_label=base.label(), base_member=member, base_sha=bsha, arm='A07-350',
                                      flags=list(flags), floors=floors,
                                      question=f'delta0926 prerequisite teacher {tid} ({job["what"][:60]}), seed {seed}')
                emit(cfg, f'prereq/{run_id}.json', row, floor)

    names = [r['name'] for r in rows if r.get('name')]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise GenError(f'{len(dupes)} duplicate run names (run directories would collide): {dupes[:5]}')
    files = [r['file'] for r in rows if r.get('file')]
    assert len(files) == len(set(files)), 'duplicate config files'
    for r in rows:
        r['flags'] = sorted(set(r['flags']))
    index = {'generator': 'code/generate_delta.py', 'delta': str(args.delta.relative_to(LAB)) if args.delta.is_absolute() else str(args.delta),
             'run_names_unique': True, 'n_run_names': len(names),
             'series_classification': None,   # filled by classify_series.py (the applied tree's validator)
             'delta_sha256': sha256_bytes(delta_bytes),
             'key_registry_sha256': sha256_bytes(REGISTRY.read_bytes()),
             'anchor_arms_sha256': sha256_bytes(ARMS.read_bytes()),
             'floors_sha256': sha256_bytes(args.floors.read_bytes()) if floors else None,
             'amendments': ({'file': Path(args.amendments).name, 'status': amend['status'],
                             'sha256': sha256_bytes(Path(args.amendments).read_bytes())} if amend else None),
             'tier': tier, 'base': base.label(), 'base_bundle_sha256': base.sha, 'stand_in_base': stand_in,
             'anchor_cache': {'key': anchor_cache_key[:12], 'identity': anchor_cache_ident,
                              'data_root': cache_spec['anchor_data_root']},
             'counts_by_wave_incl_replicas': counts,
             'status_counts': {s: sum(r['status'] == s for r in rows) for s in sorted({r['status'] for r in rows})},
             'written': sum(r['file'] is not None for r in rows),
             'errors': problems, 'runs': rows}
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / 'index.json').write_text(json.dumps(index, indent=1) + '\n')
    nflag = {}
    for r in rows:
        for f in r['flags']:
            nflag[f] = nflag.get(f, 0) + 1
    print(f'tier={tier} base={base.label()} delta_sha256={index["delta_sha256"][:12]}')
    print('cells by wave (incl. drift replicas, placebos):', counts)
    print('status:', index['status_counts'], 'configs written:', index['written'])
    print('flags:', dict(sorted(nflag.items())))
    for i, errs in problems.items():
        for e in errs:
            print(f'ERROR {i}: {e} (recorded, no config written)', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
