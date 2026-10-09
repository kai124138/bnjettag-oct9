#!/usr/bin/env python3
"""One read-only snapshot of Kai's NRP runs, as JSON on stdout, for the `runs` pane mod.

Reads: `kubectl get pods` and `kubectl get jobs` in cms-ml (names starting `kai-`), NRP's public
Prometheus for per-pod GPU utilization and memory (DCGM), the campaign config JSON each job names,
and each campaign's STATE.json evaluations. Writes nothing. Four requests to the cluster side per call.

Epochs and the validation-accuracy trace come from W&B (one runs query, plus one history read per
unfinished run; finished runs are cached in local/runs-cache/history). ROC curves are read from
local/runs-cache/roc/<arm>.json, which tools/runs_roc.py writes. A score shown here comes from the
lab pod or the home PC and is validation-only and unverified.

~/venv-hgq2/bin/python tools/runs_snapshot.py [--hours 48] [--namespace cms-ml]
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROM = 'https://prometheus.nrp-nautilus.io/api/v1/query'
CACHE = ROOT / 'local' / 'runs-cache'
ENTITY = 'kayamaguchi-uc-san-diego'
TRACE = ('epoch', 'val_categorical_accuracy', 'val_macro_auc', 'ebops')
AUTH_HINTS = ('device', 'verification', 'unauthorized', 'oidc', 'login', 'token', 'forbidden')


def now():
    return dt.datetime.now(dt.timezone.utc)


def parse_time(text):
    return dt.datetime.fromisoformat(text.replace('Z', '+00:00')) if text else None


def kubectl(args, timeout=25):
    """Run kubectl read-only; a stuck device-code login is killed by the timeout."""
    try:
        out = subprocess.run(['kubectl', *args, '--request-timeout=20s', '-o', 'json'], capture_output=True,
                             text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as error:
        stderr = (error.stderr or b'').decode() if isinstance(error.stderr, bytes) else (error.stderr or '')
        return None, 'login_needed' if any(h in stderr.lower() for h in AUTH_HINTS) or not stderr else 'error', \
            f'kubectl timed out after {timeout} s' + (f': {stderr.strip()[:200]}' if stderr else '')
    if out.returncode != 0:
        err = out.stderr.strip()
        return None, 'login_needed' if any(h in err.lower() for h in AUTH_HINTS) else 'error', err[:300]
    return json.loads(out.stdout), 'ok', None


def prometheus(query):
    url = PROM + '?' + urllib.parse.urlencode({'query': query})
    try:
        with urllib.request.urlopen(url, timeout=15) as reply:
            data = json.load(reply)
        return {r['metric'].get('pod'): r for r in data['data']['result']}, None
    except Exception as error:  # metrics are optional; the pane says they are missing
        return {}, f'prometheus: {error}'


def find_config(arm):
    """The campaign config JSON whose stem is the arm name (newest campaign first)."""
    for path in sorted(ROOT.glob(f'campaigns/*/configs/{arm}.json'), reverse=True):
        return path
    return None


def flatten(value, prefix=''):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out.update(flatten(item, f'{prefix}{key}.'))
        return out
    return {prefix[:-1]: value}


IGNORED = ('name', 'experiment.arm', 'campaign.pilot.arm', 'campaign.arm', 'campaign.revision_of')


def describe(cfg):
    """What the pane draws for one run: inputs, model blocks and quantization, from the config."""
    arch, quant, train = cfg.get('arch', {}), cfg.get('quant', {}), cfg.get('train', {})
    ebops = train.get('ebops', {})
    return {
        'inputs': {'constituents': arch.get('n_part'), 'features': arch.get('features', []),
                   'pt_gate_gev': arch.get('pt_gate_gev'), 'standardized': arch.get('input_std'),
                   'data': train.get('data'), 'validation_split': train.get('validation_split')},
        'model': {'d_model': arch.get('d_model'), 'heads': arch.get('n_heads'), 'layers': arch.get('n_layers'),
                  'ffn_dim': arch.get('ffn_dim'), 'ffn_act': arch.get('ffn_act'), 'norm': arch.get('norm'),
                  'pool': arch.get('pool'), 'classes': arch.get('n_classes'), 'pos_enc': arch.get('pos_enc'),
                  'softmax': quant.get('softmax_quant')},
        'quant': {'weight': quant.get('weight'), 'act_bits': quant.get('act_bits'),
                  'act_policy': quant.get('act_policy'),
                  'target_ebops': (ebops.get('pid') or {}).get('target_ebops'),
                  'controller': ebops.get('controller')},
        'train': {'epochs': train.get('epochs'), 'batch': train.get('batch'), 'lr': train.get('lr'),
                  'seed': cfg.get('experiment', {}).get('seed')},
    }


def differences(configs):
    """Per arm, the settings whose value is not shared by every arm of its campaign."""
    flat = {arm: flatten(cfg) for arm, cfg in configs.items()}
    keys = set().union(*flat.values()) if flat else set()
    varying = sorted(k for k in keys if k not in IGNORED and len({json.dumps(f.get(k)) for f in flat.values()}) > 1)
    return {arm: {k: f.get(k) for k in varying} for arm, f in flat.items()}


def scores():
    """Evaluations the harness recorded, by job name (lab pod, validation, unverified)."""
    out = {}
    for path in ROOT.glob('campaigns/*/STATE.json'):
        try:
            evaluations = json.loads(path.read_text()).get('evaluations', {})
        except (OSError, ValueError):
            continue
        for key, item in evaluations.items():
            out[key.split('#')[0]] = {'valid': item.get('valid'), 'value': item.get('value'),
                                      'reason': item.get('reason'), 'at': item.get('at')}
    return out


def wandb_info(arms_by_project):
    """Per arm: W&B state, epochs done, seconds per epoch and a sampled accuracy trace."""
    try:
        import wandb
    except ImportError:
        return {}, 'wandb not importable (run with ~/venv-hgq2/bin/python)'
    out, history_dir = {}, CACHE / 'history'
    history_dir.mkdir(parents=True, exist_ok=True)
    try:
        api = wandb.Api(timeout=20)
        for project, arms in arms_by_project.items():
            newest = {}
            for run in api.runs(f'{ENTITY}/{project}', filters={'display_name': {'$in': sorted(arms)}}, per_page=50):
                if run.name not in newest or run.created_at > newest[run.name].created_at:
                    newest[run.name] = run
            for arm, run in newest.items():
                summary = run.summary
                done = summary.get('completed_epochs')
                if done is None and summary.get('epoch') is not None:
                    done = int(summary.get('epoch')) + 1
                cached = history_dir / f'{arm}-{run.id}.json'
                if cached.is_file():
                    trace = json.loads(cached.read_text())
                else:
                    rows = run.history(keys=list(TRACE), samples=80, pandas=False)
                    trace = [{k: r.get(k) for k in TRACE} for r in rows]
                    if run.state == 'finished':
                        cached.write_text(json.dumps(trace))
                out[arm] = {'state': run.state, 'run_id': run.id, 'epochs_done': done,
                            'epoch_seconds': summary.get('epoch_seconds'),
                            'best_feasible_val_accuracy': summary.get('best_feasible_val_accuracy'),
                            'best_feasible_epoch': summary.get('best_feasible_epoch'),
                            'trace': trace}
    except Exception as error:  # W&B is optional; the pane says what is missing
        return out, f'wandb: {str(error)[:200]}'
    return out, None


def roc_for(arm):
    path = CACHE / 'roc' / f'{arm}.json'
    try:
        return json.loads(path.read_text()) if path.is_file() else None
    except ValueError:
        return None


def pod_row(pod, jobs, util, mem, evaluations):
    meta, spec, status = pod['metadata'], pod['spec'], pod.get('status', {})
    job_name = meta.get('labels', {}).get('job-name', '')
    job = jobs.get(job_name, {})
    notes = job.get('metadata', {}).get('annotations', {}) or {}
    state = ((status.get('containerStatuses') or [{}])[0].get('state') or {})
    detail = next(iter(state.values()), {}) if state else {}
    started = parse_time(status.get('startTime'))
    finished = parse_time(detail.get('finishedAt'))
    pack = notes.get('bnjettag.io/pack', '').split()
    arm = pack[1] if len(pack) > 1 else None
    u, m = util.get(meta['name']), mem.get(meta['name'])
    return {
        'pod': meta['name'], 'job': job_name, 'campaign': meta.get('labels', {}).get('campaign'),
        'role': meta.get('labels', {}).get('bnjettag.io/role'),
        'phase': status.get('phase'), 'reason': detail.get('reason') or status.get('reason'),
        'exit_code': detail.get('exitCode'), 'node': spec.get('nodeName'),
        'gpu_model': u['metric'].get('modelName') if u else None,
        'gpu_util_pct': float(u['value'][1]) if u else None,
        'gpu_mem_mib': float(m['value'][1]) if m else None,
        'started': status.get('startTime'),
        'runtime_s': int(((finished or now()) - started).total_seconds()) if started else None,
        'arm': arm, 'stop_epoch': notes.get('bnjettag.io/stop-epoch'),
        'attempt': meta.get('labels', {}).get('bnjettag.io/attempt'),
        'epoch': None,
        'score': evaluations.get(job_name),
    }


def snapshot(namespace, hours):
    result = {'at': now().isoformat(timespec='seconds'), 'auth': 'ok', 'errors': [], 'pods': [], 'runs': {},
              'missing': {}}
    pods, auth, error = kubectl(['get', 'pods', '-n', namespace])
    if pods is None:
        result.update(auth=auth)
        result['errors'].append(error)
        return result
    jobs, _, error = kubectl(['get', 'jobs', '-n', namespace])
    if error:
        result['errors'].append(error)
    jobs = {j['metadata']['name']: j for j in (jobs or {}).get('items', []) if j['metadata']['name'].startswith('kai-')}
    util, e1 = prometheus(f'DCGM_FI_DEV_GPU_UTIL{{namespace="{namespace}",pod=~"kai-.*"}}')
    mem, e2 = prometheus(f'DCGM_FI_DEV_FB_USED{{namespace="{namespace}",pod=~"kai-.*"}}')
    result['errors'] += [e for e in (e1, e2) if e]
    evaluations = scores()
    cutoff = now() - dt.timedelta(hours=hours)
    for pod in pods.get('items', []):
        if not pod['metadata']['name'].startswith('kai-'):
            continue
        row = pod_row(pod, jobs, util, mem, evaluations)
        started = parse_time(row['started'])
        if row['phase'] in ('Running', 'Pending') or (started and started >= cutoff):
            result['pods'].append(row)
    order = {'Running': 0, 'Pending': 1}
    result['pods'].sort(key=lambda r: (order.get(r['phase'], 2), -(parse_time(r['started']) or cutoff).timestamp()))

    by_campaign, by_project = {}, {}
    for row in result['pods']:
        path = find_config(row['arm']) if row['arm'] else None
        if path and row['arm'] not in result['runs']:
            cfg = json.loads(path.read_text())
            result['runs'][row['arm']] = {'config': str(path.relative_to(ROOT)), **describe(cfg),
                                          'roc': roc_for(row['arm'])}
            by_campaign.setdefault(path.parent, {})[row['arm']] = cfg
            by_project.setdefault(cfg['train'].get('wandb_project'), set()).add(row['arm'])
    by_project.pop(None, None)
    tracked, error = wandb_info(by_project) if by_project else ({}, None)
    if error:
        result['errors'].append(error)
        result['missing']['epoch'] = error
    for arm, info in tracked.items():
        result['runs'][arm]['wandb'] = info
    for row in result['pods']:
        info = tracked.get(row['arm'] or '')
        if info:
            row['epoch'] = info['epochs_done']
    for folder in by_campaign:  # compare against every arm config of that campaign, not just those on screen
        siblings = {p.stem: json.loads(p.read_text()) for p in folder.glob('*.json')}
        for arm, diff in differences(siblings).items():
            if arm in result['runs']:
                result['runs'][arm]['differs'] = diff
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--namespace', default='cms-ml')
    parser.add_argument('--hours', type=float, default=48, help='also list pods started within this many hours')
    args = parser.parse_args()
    json.dump(snapshot(args.namespace, args.hours), sys.stdout)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
