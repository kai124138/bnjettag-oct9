#!/usr/bin/env python3
"""Summarize the Delta memory canary into k_result.json (stdlib only; runs in the canary pod).

    python canary_k.py --samples <canary>/gpu_samples.csv --packs delta_canary_packs.json \
        --run-root <canary> --out <canary>/k_result.json

The canary pod (manifests/delta-canary-job.json) runs the phases of delta_canary_packs.json
(pack_meta: phase, class, k_tested, run_root) one after another, each to --stop-after 110, while a
background loop appends nvidia-smi samples:
  <unix>,<phase>,gpu,<name>,<memory.total MiB>,<memory.used MiB>[,<utilization.gpu %>]
  <unix>,<phase>,app,<pid>,<used_memory MiB>
and run_pack.py's stdout is kept as <run_root>/pack.log (ARM_STARTED <idx> <name> pid <pid> ...,
POD_MEM ... current_mib <x> ...). Per phase:
  card_mib, pod_peak_mib           max memory.total / memory.used over the phase's samples
  per_arm[name].gpu_peak_mib       max used_memory of the arm's pids (from ARM_STARTED)
  per_arm[name].rss_gate           the anchor's RSS_GATE line from the arm log (slope_mb_per_epoch,
                                   baseline_mb, projection_mb, limit_mb, PASS/FAIL), else null
  per_process_peak_mib             max used_memory over all processes (pid mapping not required)
  pod_host_peak_mib                max POD_MEM current_mib (cgroup, host memory)
  gpu_util_mean_pct                mean sampled GPU utilization during this phase, if available
  gpu_util_last_3h_pct             last-three-hour mean only when the phase covers three hours
  oom                              'RESOURCE_EXHAUSTED' / 'out of memory' in any arm log
Rule (wave-2 STUDY launch gate 7, [DK11]): accepted only if the pod peak stays <= 90 % of the card
and nothing runs out of memory:
  k_rule     = floor(0.90 * card_mib / per_process_peak_mib)
  k_accepted = min(k_rule, k_tested)       if no OOM and pod_peak <= 0.90 * card_mib
             = min(k_rule, k_tested - 1)   otherwise (never above what was measured)
Per class, K = the largest k_accepted over that class's phases. Gate 14 (host memory): every arm's
RSS_GATE must be PASS (rss_gate_all_pass per phase). One pod covers one GPU product; the packer
uses a phase only for that product's class. Nothing here is a result; it sizes packs.
"""
import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

RULE = 0.90
RSS_RE = re.compile(r'RSS_GATE (\S+) (PASS|FAIL) slope_mb_per_epoch (\S+) baseline_mb (\S+) projection_mb (\S+) '
                    r'at_epoch (\S+) limit_mb (\S+)')


def read_text(p):
    try:
        return p.read_text(errors='replace')
    except OSError:
        return ''


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--samples', type=Path, required=True)
    ap.add_argument('--packs', type=Path, required=True)
    ap.add_argument('--run-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    packs = json.loads(args.packs.read_text())
    gpu, app = {}, {}
    for row in csv.reader(read_text(args.samples).splitlines()):
        if len(row) < 5:
            continue
        phase, kind = row[1].strip(), row[2].strip()
        try:
            if kind == 'gpu' and len(row) >= 6:
                util = float(row[6]) if len(row) >= 7 and row[6].strip() not in ('', 'N/A', '[N/A]') else None
                gpu.setdefault(phase, []).append((row[3].strip(), float(row[4]), float(row[5]),
                                                   util, int(row[0])))
            elif kind == 'app':
                app.setdefault(phase, []).append((row[0].strip(), row[3].strip(), float(row[4])))
        except ValueError:
            continue
    phases, classes = {}, {}
    for meta, names in zip(packs['pack_meta'], packs['packs']):
        phase = meta['phase']
        root = Path(meta.get('run_root') or args.run_root / phase)
        g, a = gpu.get(phase, []), app.get(phase, [])
        pack_log = read_text(root / 'pack.log')
        pid_arm = {m.group(2): m.group(1) for m in re.finditer(r'ARM_STARTED \S+ (\S+) pid (\d+)', pack_log)}
        host = [float(x) for x in re.findall(r'POD_MEM .*?current_mib (\d+(?:\.\d+)?)', pack_log)]
        logs = sorted((root / 'logs').glob('*.log'))
        texts = {p.name: read_text(p) for p in logs}
        oom = any('RESOURCE_EXHAUSTED' in t or 'out of memory' in t for t in texts.values())
        per_arm = {}
        for name in names:
            peaks = [x[2] for x in a if pid_arm.get(x[1]) == name]
            gate = None
            for t in texts.values():
                for m in RSS_RE.finditer(t):
                    if m.group(1) == name:
                        gate = {'verdict': m.group(2), 'slope_mb_per_epoch': float(m.group(3)),
                                'baseline_mb': float(m.group(4)), 'projection_mb': float(m.group(5)),
                                'at_epoch': int(m.group(6)), 'limit_mb': float(m.group(7))}
            per_arm[name] = {'gpu_peak_mib': max(peaks) if peaks else None, 'rss_gate': gate}
        rec = {'class': meta['class'], 'k_tested': meta['k_tested'], 'n_samples': len(g), 'oom': oom,
               'per_arm': per_arm, 'pod_host_peak_mib': max(host) if host else None,
               'rss_gate_all_pass': all((v['rss_gate'] or {}).get('verdict') == 'PASS' for v in per_arm.values()),
               'arm_logs': sorted(texts)}
        if g and a:
            card = max(x[1] for x in g)
            per_proc = max(x[2] for x in a)
            pod_peak = max(x[2] for x in g)
            util_samples = [(x[4], x[3]) for x in g if x[3] is not None]
            util_mean = (round(sum(v for _, v in util_samples) / len(util_samples), 2)
                         if util_samples else None)
            span = max((t for t, _ in util_samples), default=0) - min((t for t, _ in util_samples), default=0)
            last_3h = [v for t, v in util_samples if t >= max((s for s, _ in util_samples), default=0) - 10800]
            util_3h = (round(sum(last_3h) / len(last_3h), 2)
                       if util_samples and span >= 10800 else None)
            k_rule = math.floor(RULE * card / per_proc)
            within = pod_peak <= RULE * card
            rec.update(gpu_product=sorted({x[0] for x in g}), card_mib=card, per_process_peak_mib=per_proc,
                       pod_peak_mib=pod_peak, pod_peak_over_card=round(pod_peak / card, 4), k_rule=k_rule,
                       pod_within_90=within, gpu_util_mean_pct=util_mean,
                       gpu_util_last_3h_pct=util_3h, gpu_util_samples=len(util_samples),
                       k_accepted=min(k_rule, meta['k_tested']) if (within and not oom)
                       else max(0, min(k_rule, meta['k_tested'] - 1)))
        else:
            rec.update(k_accepted=None, error='no nvidia-smi samples for this phase')
        phases[phase] = rec
        if rec.get('k_accepted'):
            classes[meta['class']] = max(classes.get(meta['class'], 0), rec['k_accepted'])
        print('CANARY_PHASE', phase, json.dumps({k: v for k, v in rec.items() if k != 'per_arm'}, sort_keys=True), flush=True)
        for name, v in per_arm.items():
            print('CANARY_ARM', phase, name, json.dumps(v, sort_keys=True), flush=True)
    args.out.write_text(json.dumps({'rule_fraction': RULE, 'k_by_class': classes, 'phases': phases,
                                    'note': 'memory canary; sizes packs, not a result'}, indent=1) + '\n')
    ok = all(p.get('k_accepted') for p in phases.values()) and all(p['rss_gate_all_pass'] for p in phases.values())
    print('CANARY_K_DONE' if ok else 'CANARY_K_INCOMPLETE', json.dumps(classes), args.out, flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
