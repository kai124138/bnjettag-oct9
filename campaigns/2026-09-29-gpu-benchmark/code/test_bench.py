#!/usr/bin/env python3
"""Unit tests for the benchmark tooling (stdlib only; `python3 test_bench.py` or pytest).

Formula checks (owner protocol, formula verification): substitution of known values and one
limiting case for the steady-state epoch time, the throughput, the CPU-core estimate and K_rule.
Synthetic inputs only; nothing here is a result. A test returning 'skip' prints SKIP with its reason.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bench_summary as bs   # noqa: E402
import gen_bench as gb       # noqa: E402
import bench_driver as bd    # noqa: E402  (last: it drops its own directory from sys.path on import)


def epoch_line(e, traced, seconds, rss=2300):
    ebops = '9605779' if traced else 'untraced in_training_ebops=9681043'
    tr = '100.00' if traced else '0.01'
    return (f'[epoch {e}/7000] EBOPs={ebops} target=350000 beta=1e-07 val_AUC=0.5 val_accuracy=0.2 '
            f'seconds={seconds:.1f} checkpoint=- ebops_trace_seconds={tr} ebops_trace_over_epoch=0.4 loss=2.5 host_rss_mb={rss}')


def write_log(path, name, u, t, first=200.0, resume_block=True, last=25):
    lines = ['==== ARM_ATTEMPT 0 2026-09-29T00:00:00Z', 'RUN_STAGE pilot-b',
             f'[train] {name} params=31735 resume_epoch=0 initial_ebops=11559681']
    for e in range(1, last + 1):
        traced = e in (1, 10, 20)
        lines.append(epoch_line(e, traced, first if e == 1 else t if traced else u))
    if resume_block:   # a later attempt that resumed at 25 must be ignored
        lines += ['==== ARM_ATTEMPT 0 2026-09-29T02:00:00Z', f'[train] {name} params=31735 resume_epoch=25 initial_ebops=1',
                  epoch_line(26, False, 999.0)]
    Path(path).write_text('\n'.join(lines) + '\n')


def test_steady_formula():
    assert bs.steady(130.0, 130.0) == 130.0                       # limiting case: no trace cost
    assert abs(bs.steady(130.0, 245.0) - 141.5) < 1e-12            # (9 x 130 + 245) / 10
    assert bs.steady(None, 1.0) is None


def test_parse_fresh_block_and_pool():
    with tempfile.TemporaryDirectory() as d:
        write_log(Path(d) / 'a.log', 'chang0926-a-n64-s1', 130.0, 245.0)
        write_log(Path(d) / 'b.log', 'chang0926-a-n64-s2', 130.0, 245.0)
        arms = [bs.arm_metrics(bs.fresh_block(Path(d) / n), 21) for n in ('a.log', 'b.log')]
    a = arms[0]
    assert a['epochs_done'] == 21 and a['traced_epochs'] == [1, 10, 20] and a['traced_as_expected']
    assert len(a['untraced_s']) == 18 and len(a['traced_s']) == 2 and a['epoch1_s'] == 200.0
    assert 999.0 not in a['untraced_s']                              # the resumed attempt is not read
    p = bs.pool(arms, 2, 21)
    assert p['untraced_median_s'] == 130.0 and p['traced_median_s'] == 245.0
    assert abs(p['steady_s_per_epoch'] - 141.5) < 1e-12
    assert abs(p['run_epochs_per_gpu_hour'] - 2 * 3600 / 141.5) < 1e-9
    assert abs(p['steady_s_slowest_arm'] - 141.5) < 1e-12 and p['all_arms_completed']
    assert abs(p['R_d1'] - 2 * 3600 / 141.5) < 1e-9
    assert p['n_untraced'] == 36 and p['n_traced'] == 4 and p['completed_run_epochs'] == 42


def test_pool_completion_against_stop_after():
    """B2: every arm stopped at epoch 15 (deadline, SIGTERM): same epoch count everywhere, but not stop_after, so no R."""
    with tempfile.TemporaryDirectory() as d:
        for n in ('a', 'b'):
            write_log(Path(d) / f'{n}.log', f'chang0926-a-n64-s{n}', 130.0, 245.0, resume_block=False, last=15)
        arms = [bs.arm_metrics(bs.fresh_block(Path(d) / f'{n}.log'), 21) for n in ('a', 'b')]
    p = bs.pool(arms, 2, 21)
    assert [a['epochs_done'] for a in arms] == [15, 15]
    assert p['arms_completed'] == 0 and not p['all_arms_completed'] and p['R_d1'] is None
    assert p['s_d1'] is not None                                     # s is still reported, R is not


def test_cpu_cores_from_usage():
    rows = [{'phase': 'p1-E-k2', 'kind': 'gpu', 'unix_s': str(t), 'cgroup_cpu_usage_usec': str(u),
             'gpu_util_pct': '50', 'gpu_mem_used_mib': '9000', 'gpu_mem_total_mib': '23028', 'live_arms': '2',
             'epochs_done_min': '3', 'epochs_done_max': '4', 'cgroup_mem_current_bytes': str(2 ** 30)}
            for t, u in ((0, 0), (60, 120_000_000), (120, 240_000_000))]
    s = bs.samples_for(rows, 'p1-E-k2', 2, 21)
    assert abs(s['cpu_cores_mean_all'] - 2.0) < 1e-12 and abs(s['cpu_cores_mean_steady'] - 2.0) < 1e-12
    assert abs(s['cpu_cores_per_arm_steady'] - 1.0) < 1e-12 and s['cpu_pinned_cores_expected'] == 4
    assert abs(s['gpu_mem_peak_fraction'] - 9000 / 23028) < 1e-12 and s['gpu_util_mean_steady'] == 50.0
    assert s['cgroup_mem_peak_mib'] == 1024.0
    # the driver's own PHASE_DONE figure uses the same window and the same pairs
    tuples = [(float(r['unix_s']), float(r['cgroup_cpu_usage_usec']), 2, 3, 4) for r in rows]
    assert bd.steady_cores(tuples, 2, 21) == (2.0, 2)
    # rule 5: 4.5 cores for 2 arms is 2.25 per arm > 2.1
    over = [dict(r, cgroup_cpu_usage_usec=str(int(u))) for r, u in zip(rows, (0, 270e6, 540e6))]
    s2 = bs.samples_for(over, 'p1-E-k2', 2, 21)
    assert abs(s2['cpu_cores_per_arm_steady'] - 2.25) < 1e-12
    assert any(w.startswith('rule 5: above the CPU budget') for w in bs.exclusion({**s2, 'cpu_pin': 'pinned'}))
    assert not any(w.startswith('rule 5') for w in bs.exclusion({**s, 'cpu_pin': 'pinned'}))


def test_plan_validation():
    with tempfile.TemporaryDirectory() as d:
        rows = [{'name': n} for names in bd.CLASS_NAMES.values() for n in names]
        Path(d, 'index.json').write_text(json.dumps({'runs': rows}))
        good = {'stop_after': 21, 'phases': [{'phase': 'p1-E-k2', 'class': 'E', 'k': 2, 'names': bd.CLASS_NAMES['E'][:2]}]}
        assert bd.validate_plan(good, Path(d)) == []
        for bad_names in (bd.CLASS_NAMES['E'][1:3], [bd.CLASS_NAMES['E'][0]] * 2, bd.CLASS_NAMES['A07'][:2]):
            bad = {'stop_after': 21, 'phases': [{'phase': 'p1-E-k2', 'class': 'E', 'k': 2, 'names': bad_names}]}
            assert bd.validate_plan(bad, Path(d)), bad_names
        assert bd.validate_plan({'stop_after': 0, 'phases': []}, Path(d))


def node(cpu, mem, gpus=4, ok=True):
    return {'node': f'n{cpu}-{mem}', 'alloc_cpu': float(cpu), 'alloc_mem_gi': float(mem),
            'gpu_resources': {'nvidia.com/gpu': gpus}, 'schedulable_for_us': ok}


def survey(card, nodes):
    return {'resource_keys': ['nvidia.com/gpu'], 'card_mib_labels': [card], 'nodes': len(nodes),
            'schedulable_gpus_allocatable': sum(n['gpu_resources']['nvidia.com/gpu'] for n in nodes if n['schedulable_for_us']),
            'per_node': nodes}


def shapes(p):
    return {j['shape']: ([ph['phase'] for ph in j['phases']], j['pod_request']) for j in p['jobs']}


def test_k_rule_and_caps():
    # 46,068 MiB: E floor(0.9 x 46068 / 4350) = 9 (9 x 4350 = 39,150 = 85.0 %), A07 floor(... / 8446) = 4
    p = gb.plan_product('NVIDIA-L40', survey(46068, [node(20, 503)]))
    assert (p['classes']['E']['k_rule'], p['classes']['E']['k_run'], p['classes']['E']['k_low']) == (9, 9, 4)
    assert (p['classes']['A07']['k_rule'], p['classes']['A07']['k_run'], p['classes']['A07']['k_low']) == (4, 4, 2)
    # Amendment 1 (A2): two Jobs, each pod sized for its own largest K
    assert shapes(p) == {'krule': (['p1-E-k9', 'p2-A07-k4'], {'cpu': 18, 'memory_gi': 72}),
                         'klow': (['p3-E-k4', 'p4-A07-k2'], {'cpu': 8, 'memory_gi': 32})}
    assert p['classes']['E']['predicted_peak_fraction_at_k_run'] <= 0.9 and p['run_epochs'] == (9 + 4 + 4 + 2) * 21
    # A6000 49,140 MiB on 20-CPU nodes: E rule 10 needs 20 CPU; node cap (20 - 2) // 2 = 9 binds
    q = gb.plan_product('NVIDIA-RTX-A6000', survey(49140, [node(20, 251.5)]))
    assert (q['classes']['E']['k_rule'], q['classes']['E']['k_run'], q['classes']['E']['k_low']) == (10, 9, 4)
    assert q['classes']['E']['binding_caps'] and not q['classes']['A07']['binding_caps']
    # 80 GB: E 16 (the whole 16-name pool, not capped), A07 8
    r = gb.plan_product('NVIDIA-A100-SXM4-80GB', survey(81920, [node(252, 1007.3)]))
    assert (r['classes']['E']['k_run'], r['classes']['A07']['k_run']) == (16, 8)
    assert shapes(r)['krule'][1] == {'cpu': 32, 'memory_gi': 128} and shapes(r)['klow'][1] == {'cpu': 8, 'memory_gi': 32}
    # a hypothetical 200 GB card: the name pool binds
    s = gb.plan_product('X', survey(200000, [node(252, 1007.3)]))
    assert s['classes']['E']['k_rule'] == 41 and s['classes']['E']['k_run'] == 16 and s['classes']['E']['binding_caps']
    # memory reserve: a 31.2 Gi node cannot hold a 5-arm pod (40 Gi + 16 Gi reserve)
    held, pods = gb.holding([node(12, 31.2, 2), node(12, 62.6, 2)], 5)
    assert held == ['n12-62.6'] and pods == 1


def test_a10_baseline_jobs():
    """Amendment 1 (A1): the A10 in the same harness, K_rule E 4 / A07 2 = floor(0.9 x 23,028 / m), K_low = K_rule - 1,
    through the generator's own [D2] rule, not a special case; the yield-to-anchor rule rides on both Jobs."""
    p = gb.plan_product('NVIDIA-A10', survey(23028, [node(124, 503.6, 8)]))
    assert p['role'] == 'baseline'
    assert (p['classes']['E']['k_rule'], p['classes']['E']['k_run'], p['classes']['E']['k_low']) == (4, 4, 3)
    assert (p['classes']['A07']['k_rule'], p['classes']['A07']['k_run'], p['classes']['A07']['k_low']) == (2, 2, 1)
    assert shapes(p) == {'krule': (['p1-E-k4', 'p2-A07-k2'], {'cpu': 8, 'memory_gi': 32}),
                         'klow': (['p3-E-k3', 'p4-A07-k1'], {'cpu': 6, 'memory_gi': 24})}
    for j in p['jobs']:
        m = gb.job(p, j, 'cm', 'x' * 64, ['hcc-nrp-shor-c6017.unl.edu'], 'survey')
        ann = m['metadata']['annotations']
        assert 'bnjettag.io/yield-to-anchor' in ann and 'pilot-b' in ann['bnjettag.io/yield-to-anchor']
        assert 'bnjettag.io/baseline' in ann
        expr = m['spec']['template']['spec']['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][
            'nodeSelectorTerms'][0]['matchExpressions']
        assert {'key': 'nvidia.com/gpu.product', 'operator': 'In', 'values': ['NVIDIA-A10']} in expr
        assert 'hcc-nrp-shor-c6017.unl.edu' in expr[1]['values']
        # critical v2 C5: the pilot-b nodes too, in the same NotIn, the existing exclusions kept
        assert expr[1]['values'] == sorted({'hcc-nrp-shor-c6017.unl.edu', *gb.PILOT_NODES})
        assert 'bnjettag.io/pilot-nodes-excluded' in ann
    assert gb.PRODUCTS[-1] == 'NVIDIA-A10' and len(gb.PRODUCTS) == 8


def test_k_low_rules():
    """Brief (half) against STUDY.md [D2] (A10 K, or K_run - 1 where K_run <= it)."""
    cases = {  # card: (E half, A07 half, E d2, A07 d2)
        23028: (2, 1, 3, 1), 24576: (2, 1, 4, 1), 46068: (4, 2, 4, 2), 81920: (8, 4, 4, 2)}
    for card, (eh, ah, ed, ad) in cases.items():
        h = gb.plan_product('X', survey(card, [node(252, 1007.3)]), 'half')
        d = gb.plan_product('X', survey(card, [node(252, 1007.3)]), 'study-d2')
        assert (h['classes']['E']['k_low'], h['classes']['A07']['k_low']) == (eh, ah), card
        assert (d['classes']['E']['k_low'], d['classes']['A07']['k_low']) == (ed, ad), card
        assert h['classes']['E']['k_run'] == d['classes']['E']['k_run']


def test_deadline_formula():
    p = gb.plan_product('NVIDIA-L40', survey(46068, [node(20, 503)]))
    krule, klow = p['jobs']
    raw_rule = 1800 + sum(k * 21 * c * 2.5 + 15 * k + 900 for k, c in ((9, 28), (4, 44)))
    raw_low = 1800 + sum(k * 21 * c * 2.5 + 15 * k + 900 for k, c in ((4, 28), (2, 44)))
    assert (raw_rule, raw_low) == (26265, 14190)
    assert (krule['pod_active_deadline_seconds'], klow['pod_active_deadline_seconds']) == (26400, 14400)
    assert (krule['job_active_deadline_seconds'], klow['job_active_deadline_seconds']) == (26400 + 21600, 14400 + 21600)
    # expected compute, both A10 bounds (arithmetic): aggregate 9 x 21 x 28 + 4 x 21 x 44; per-process 2 x 21 x 140
    assert krule['expected_compute']['a10_aggregate_bound_s'] == 9 * 21 * 28 + 4 * 21 * 44 == 8988
    assert krule['expected_compute']['a10_per_process_bound_s'] == 2 * 21 * 140 == 5880
    job = gb.job(p, krule, 'cm', 'x' * 64, ['bad-node'], 'survey')
    assert job['spec']['activeDeadlineSeconds'] == 48000 and job['spec']['backoffLimit'] == 0
    assert job['spec']['template']['spec']['activeDeadlineSeconds'] == 26400
    assert 'podFailurePolicy' not in job['spec']                            # never re-run automatically
    env = {e['name']: e.get('value') for e in job['spec']['template']['spec']['containers'][0]['env']}
    assert env['WANDB_MODE'] == 'disabled' and 'WANDB_API_KEY' not in env
    plan = json.loads(env['BENCH_PLAN'])
    assert plan['slug'] == 'l40-krule' and plan['pod_cpu_request'] == 18 and len(plan['phases']) == 2
    script = job['spec']['template']['spec']['containers'][0]['args'][0]
    assert script.rstrip().splitlines()[-1].startswith('exec python')
    assert 'BR=/data/chang-n64-20260926/gpu-bench/l40-krule' in script
    for tag in ('CPU_MODEL', 'CPU_COUNTS', 'LSCPU', 'HOST_MEM'):                # B4: node CPU and RAM in the header
        assert tag in script, tag
    res = job['spec']['template']['spec']['containers'][0]['resources']
    assert res['requests'] == res['limits'] and res['requests']['cpu'] == '18'   # Guaranteed QoS, integer CPUs
    anti = job['spec']['template']['spec']['affinity']['podAntiAffinity']['requiredDuringSchedulingIgnoredDuringExecution']
    assert anti == [{'labelSelector': {'matchLabels': {gb.PIN_LABEL: 'true'}}, 'topologyKey': 'kubernetes.io/hostname'}]
    assert job['spec']['template']['metadata']['labels'][gb.PIN_LABEL] == 'true'
    assert 'unused' not in job['metadata']['annotations']['bnjettag.io/per-arm-resources']
    assert 'bnjettag.io/yield-to-anchor' not in job['metadata']['annotations']   # A10 Jobs only
    hosts = job['spec']['template']['spec']['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][
        'nodeSelectorTerms'][0]['matchExpressions'][1]
    assert hosts == {'key': 'kubernetes.io/hostname', 'operator': 'NotIn', 'values': ['bad-node']}   # C5: A10 Jobs only
    assert 'bnjettag.io/pilot-nodes-excluded' not in job['metadata']['annotations']


def test_generated_script_is_valid_bash():
    p = gb.plan_product('NVIDIA-L40', survey(46068, [node(20, 503)]))
    script = gb.script(p, p['jobs'][0], 'x' * 64)
    r = subprocess.run(['bash', '-n'], input=script, text=True, capture_output=True)
    assert r.returncode == 0, r.stderr
    # the header's CPU lines run under set -euo pipefail without aborting, whatever the platform lacks
    header = '\n'.join(['set -euo pipefail'] + [ln for ln in gb.setup_lines()
                                                if ln.startswith(('echo "CPU_', '(lscpu', 'echo "HOST_MEM'))] + ['echo HEADER_DONE'])
    r = subprocess.run(['bash', '-c', header], text=True, capture_output=True)
    assert r.returncode == 0 and 'HEADER_DONE' in r.stdout, (r.returncode, r.stdout, r.stderr)


def test_probe_job_shape():
    p = gb.plan_product('NVIDIA-L40', survey(46068, [node(20, 503)]))
    job = gb.probe_job(p, 9, 10, ['bad-node'], 'survey')
    spec = job['spec']
    assert (spec['completionMode'], spec['completions'], spec['parallelism'], spec['maxFailedIndexes']) == ('Indexed', 10, 10, 10)
    assert spec['backoffLimitPerIndex'] == 0 and spec['template']['spec']['activeDeadlineSeconds'] == 1800
    res = spec['template']['spec']['containers'][0]['resources']['requests']
    assert res == {'cpu': '18', 'memory': '72Gi', 'ephemeral-storage': '24Gi', 'nvidia.com/gpu': '1'}
    script = spec['template']['spec']['containers'][0]['args'][0]
    assert 'fingerprint_check.py --run chang0926-a-n64-s1 --expect 11559681' in script and 'bench_driver' not in script
    one = gb.probe_job(p, 1, 3, [], 'survey')
    assert 'bnjettag.io/single-arm-justified' in one['metadata']['annotations']


def test_offset_window_and_exclusions():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'a.log'
        lines = ['==== ARM_ATTEMPT 0 2026-09-29T00:00:00Z', '[train] x params=61951 resume_epoch=0 initial_ebops=1']
        lines += [epoch_line(e, e == 1 or e % 10 == 0, 100.0) for e in range(1, 28)]
        lines += ['==== ARM_ATTEMPT 0 2026-09-29T02:00:00Z', '[train] x params=61951 resume_epoch=25 initial_ebops=1']
        lines += [epoch_line(e, e % 10 == 0, 200.0 if e % 10 == 0 else 110.0) for e in range(26, 45)]
        path.write_text('\n'.join(lines) + '\n')
        m = bs.arm_metrics(bs.merged_block(path), 21, offset=20)          # window 22-41, traced 30 and 40
        assert m['window'] == [21, 41] and m['traced_epochs'] == [30, 40] and m['traced_as_expected']
        assert m['window_crosses_resume'] and len(m['untraced_s']) == 18
        assert 110.0 in m['untraced_s'] and m['traced_s'] == [200.0, 200.0]     # the resumed attempt replaces 26-27
        fresh = bs.arm_metrics(bs.fresh_block(path), 21)
        assert not fresh['window_crosses_resume'] and fresh['traced_epochs'] == [1, 10, 20]
    row = {'oom': True, 'nan': False, 'gpu_mem_over_90pct': True, 'fingerprint_ok': True}
    assert bs.exclusion(row) == ['rule 1: OOM', 'rule 1: pod peak above 90 % of memory.total']
    assert bs.exclusion({'fingerprint_ok': False}) == ['rule 2: fingerprint mismatch (product)']
    assert bs.exclusion({'verification': {'FAIL': 1}}) == ['rule 6: checkpoint verification FAIL (product)']


def test_benign_oom_line_is_not_an_oom():
    """A logged allocator failure that the arm survives must not trigger exclusion rule 1."""
    with tempfile.TemporaryDirectory() as d:
        ok, dead = Path(d) / 'ok.log', Path(d) / 'dead.log'
        write_log(ok, 'chang0926-a-n64-s1', 130.0, 245.0, resume_block=False)
        ok.write_text(ok.read_text().replace(
            '[epoch 5/', 'E external/xla/xla/stream_executor/cuda/cuda_driver.cc failed to allocate 2.00GiB: '
            'CUDA_ERROR_OUT_OF_MEMORY: out of memory\n[epoch 5/', 1) + 'ARM_DONE chang0926-a-n64-s1 exit 0\n')
        dead.write_text('\n'.join(['==== BENCH_ARM_ATTEMPT 0 2026-09-29T00:00:00Z', '[train] x params=61951 resume_epoch=0 initial_ebops=1',
                                   epoch_line(1, True, 100.0), 'tensorflow.python.framework.errors_impl.ResourceExhaustedError: '
                                   'RESOURCE_EXHAUSTED: failed to allocate memory', 'ARM_OOM x RESOURCE_EXHAUSTED']) + '\n')
        a = bs.arm_metrics(bs.fresh_block(ok), 21)
        b = bs.arm_metrics(bs.fresh_block(dead), 21)
    assert a['oom_lines_seen'] == 1 and a['oom'] is False and a['epochs_done'] == 21 and not a['arm_oom']
    assert b['oom'] is True and b['arm_oom'] is True
    assert bs.exclusion(bs.pool([a], 1, 21)) == [] and bs.exclusion(bs.pool([b], 1, 21)) == ['rule 1: OOM']


class _Child:
    pid = 4242


def _entry(d, text, stalled=False):
    log = Path(d) / 'arm.log'
    log.write_text(text)
    return {'name': 'chang0926-c-n64-s1', 'log': log, 'child': _Child(), 'run': Path(d) / 'run', 'stalled': stalled,
            'started_wall': 0.0, 'ended_wall': 60.0}


def test_classify_exit_codes_win():
    """B2: the exit code decides; OOM-looking text never turns exit 6 or a crash into an OOM."""
    oom_text = 'W tensorflow bfc_allocator: failed to allocate memory, retrying\n'
    fail = 'CHECKPOINT_VERIFICATION_FAIL {"run": "x", "error": "AssertionError(\'Max absolute difference: 3e-07\')"}\n'
    with tempfile.TemporaryDirectory() as d:
        c = bd.classify(_entry(d, oom_text + fail), bd.EXIT_VERIFY_FAIL)
        assert c['outcome'] == 'verify_fail' and c['oom_lines'] and 'Max absolute difference' in c['verification_error']
        assert bd.classify(_entry(d, oom_text + 'Traceback ...\n'), 1)['outcome'] == 'crash'
        assert bd.classify(_entry(d, 'ARM_OOM x RESOURCE_EXHAUSTED\n'), bd.EXIT_OOM)['outcome'] == 'oom'
        assert bd.classify(_entry(d, ''), 0)['outcome'] == 'ok'
        assert bd.classify(_entry(d, ''), bd.EXIT_DIVERGED)['outcome'] == 'diverged'
        assert bd.classify(_entry(d, ''), bd.EXIT_CPU_PIN)['outcome'] == 'cpu_pin_failed'
        assert bd.classify(_entry(d, ''), bd.EXIT_WANDB_IMPORTED)['outcome'] == 'wandb_imported'
        k = bd.classify(_entry(d, ''), -9, oom_kill_rose=True)
        assert k['outcome'] == 'host_oom_kill' and k['signal'] == 'SIGKILL'
        assert bd.classify(_entry(d, ''), -9)['outcome'] == 'killed'
        assert bd.classify(_entry(d, ''), -15)['signal'] == 'SIGTERM'
        assert bd.classify(_entry(d, oom_text, stalled=True), -9, oom_kill_rose=True)['outcome'] == 'stalled'


def test_cpu_list_and_phase_selection():
    """A2 plumbing, every platform: the kernel list format, and the first 2K CPUs of the allowed set."""
    assert bd.parse_cpu_list('0-3,8,10-11') == [0, 1, 2, 3, 8, 10, 11]
    assert bd.format_cpu_list([11, 10, 8, 3, 2, 1, 0]) == '0-3,8,10-11' and bd.format_cpu_list([5]) == '5'
    with tempfile.TemporaryDirectory() as d:
        status = Path(d) / 'status'
        status.write_text('Name:\tpython\nCpus_allowed:\tff\nCpus_allowed_list:\t2-5,8,10-11\n')
        allowed = bd.parse_cpu_list(status.read_text().split('Cpus_allowed_list:')[1].splitlines()[0])
        if not hasattr(os, 'sched_getaffinity'):   # the /proc fallback is what this platform would use
            assert bd.allowed_cpus(status) == allowed
    assert allowed == [2, 3, 4, 5, 8, 10, 11]
    assert bd.phase_cpus(allowed, 2) == [2, 3, 4, 5]           # a static-CPU-manager set does not start at 0
    assert bd.phase_cpus(list(range(18)), 1) == [0, 1] and bd.phase_cpus(list(range(18)), 9) == list(range(18))
    assert bd.phase_cpus([0, 1, 2], 2) == [0, 1, 2]            # short: run_phase labels it 'short', rule 5 flags it
    assert bd.phase_cpus(None, 2) is None


def _fake_campaign(d):
    camp = Path(d) / 'camp'
    camp.mkdir()
    (camp / 'index.json').write_text(json.dumps({'runs': [{'name': n} for ns in bd.CLASS_NAMES.values() for n in ns]}))
    return camp


def _run_stub_pod(d, extra, phases):
    plan = {'product': 'TEST', 'slug': 'test-krule', 'shape': 'krule', 'stop_after': 21, 'pod_cpu_request': 4,
            'phases': phases}
    env = {k: v for k, v in os.environ.items() if k != 'KUBERNETES_SERVICE_HOST'}
    env.update(BNJ_CAMPAIGN_DIR=str(_fake_campaign(d)), BENCH_STAGGER_SECONDS='0', BENCH_POLL_SECONDS='0.2',
               BENCH_SAMPLE_SECONDS='1', BENCH_CGROUP_DIR=str(Path(d) / 'no-cgroup'))
    bench = Path(d) / 'bench'
    r = subprocess.run([sys.executable, str(HERE / 'bench_driver.py'), 'pod', '--bench-root', str(bench),
                        '--plan-json', json.dumps(plan), '--test-arm-stub', *extra],
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (r.returncode, r.stdout[-2000:], r.stderr[-2000:])
    return bench, r.stdout


PHASES_K2_K1 = [{'phase': 'p1-E-k2', 'class': 'E', 'k': 2, 'names': bd.CLASS_NAMES['E'][:2]},
                {'phase': 'p2-A07-k1', 'class': 'A07', 'k': 1, 'names': bd.CLASS_NAMES['A07'][:1]}]


def test_pod_mode_gives_each_arm_2k_cpus():
    """A2 plumbing through the real pod path, every platform: the K=2 phase's two arms are each launched with exactly
    the first 4 CPUs of the (injected) allowed set, the K=1 phase's arm with the first 2; the phase record carries the
    pinned list. On Linux the injected set is this process's own allowed set, so the arms' real pinning succeeds in any
    cpuset. The kernel's own view is the next test (Linux only)."""
    if hasattr(os, 'sched_getaffinity'):   # Linux: the arms really pin, so inject CPUs this process may use
        real = sorted(os.sched_getaffinity(0))
        if len(real) < 4:
            return f'skip: only {len(real)} allowed CPUs here'
        inject = real[:10]
    else:                                  # no affinity API: the arms print ARM_CPUS unavailable (--test-cpu)
        inject = list(range(6, 16))
    four, two, inj = bd.format_cpu_list(inject[:4]), bd.format_cpu_list(inject[:2]), bd.format_cpu_list(inject)
    with tempfile.TemporaryDirectory() as d:
        bench, out = _run_stub_pod(d, ['--test-cpu', '--test-allowed-cpus', inj], PHASES_K2_K1)
        started = [ln for ln in out.splitlines() if ln.startswith('ARM_STARTED')]
        assert len(started) == 3, out
        assert all(f' cpus {four} ' in ln for ln in started[:2]) and f' cpus {two} ' in started[2], started
        r1 = json.loads((bench / 'p1-E-k2' / 'phase_result.json').read_text())
        r2 = json.loads((bench / 'p2-A07-k1' / 'phase_result.json').read_text())
        assert (r1['cpus_pinned'], r1['cpus_pinned_n'], r1['cpu_pin'], r1['cpus_allowed_n']) == (four, 4, 'pinned', len(inject))
        assert (r2['cpus_pinned'], r2['cpus_pinned_n']) == (two, 2)
        assert r1['outcomes'] == {'ok': 2} and r2['outcomes'] == {'ok': 1}
        for name in bd.CLASS_NAMES['E'][:2]:
            log = (bench / 'p1-E-k2' / 'logs' / f'{name}.log').read_text()
            assert f'requested {four}' in log and 'ARM_STUB_DONE' in log, log
        assert f'POD_CPUS allowed_n {len(inject)} allowed {inj} pod_cpu_request 4' in out


def test_pinning_k2_phase_arms_see_4_cpus():
    """A2, the kernel's view (Linux only): every arm of a K=2 phase reports exactly 4 CPUs from os.sched_getaffinity
    after pinning itself, and they are the first 4 of the pod's allowed set."""
    if not hasattr(os, 'sched_setaffinity'):
        return (f'skip: no os.sched_setaffinity on {sys.platform}; runs unmodified on Linux (an authorized Linux host, '
                'or the first pod: ARM_CPUS lines in every arm log, checked by bench_summary)')
    allowed = sorted(os.sched_getaffinity(0))
    if len(allowed) < 4:
        return f'skip: only {len(allowed)} allowed CPUs here'
    with tempfile.TemporaryDirectory() as d:
        bench, out = _run_stub_pod(d, [], PHASES_K2_K1)
        want = bd.format_cpu_list(allowed[:4])
        for name in bd.CLASS_NAMES['E'][:2]:
            log = (bench / 'p1-E-k2' / 'logs' / f'{name}.log').read_text()
            assert f'ARM_CPUS n=4 requested {want} seen {want} OK' in log, log
        log = (bench / 'p2-A07-k1' / 'logs' / f'{bd.CLASS_NAMES["A07"][0]}.log').read_text()
        assert f'ARM_CPUS n=2 requested {bd.format_cpu_list(allowed[:2])}' in log, log


def test_arm_refuses_unpinnable_outside_the_cpu_gate():
    """Without --test-cpu an arm that cannot pin as asked exits 14 before importing anything."""
    env = {k: v for k, v in os.environ.items() if k != 'KUBERNETES_SERVICE_HOST'}
    with tempfile.TemporaryDirectory() as d:
        bad = '100000' if hasattr(os, 'sched_setaffinity') else '0-3'   # Linux: a CPU that does not exist
        r = subprocess.run([sys.executable, str(HERE / 'bench_driver.py'), 'arm', '--name', 'x', '--run-root', d,
                            '--cpus', bad], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == bd.EXIT_CPU_PIN and 'ARM_CPUS' in r.stdout, (r.returncode, r.stdout, r.stderr)
    r = subprocess.run([sys.executable, str(HERE / 'bench_driver.py'), 'arm', '--name', 'x', '--run-root', '/tmp/x',
                        '--test-arm-stub'], env={**env, 'KUBERNETES_SERVICE_HOST': '10.0.0.1'},
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == bd.EXIT_BAD_PLAN and 'BENCH_TEST_FLAGS_REFUSED' in r.stdout


# A real finished pod (campaigns/2026-09-20-status/cluster.json, kai-batch0917-screen-e100-r3-0-94g6w): Ready is False
# (PodCompleted) and the container kept its startedAt. The Job's creationTimestamp is synthetic.
COMPLETED_POD = {
    'metadata': {'name': 'kai-batch0917-screen-e100-r3-0-94g6w', 'creationTimestamp': '2026-09-17T21:56:03Z'},
    'spec': {'nodeName': 'n1'},
    'status': {'phase': 'Succeeded', 'conditions': [
        {'lastTransitionTime': '2026-09-18T00:25:17Z', 'status': 'False', 'type': 'PodReadyToStartContainers'},
        {'lastTransitionTime': '2026-09-17T21:56:03Z', 'reason': 'PodCompleted', 'status': 'True', 'type': 'Initialized'},
        {'lastTransitionTime': '2026-09-18T00:25:14Z', 'reason': 'PodCompleted', 'status': 'False', 'type': 'Ready'},
        {'lastTransitionTime': '2026-09-18T00:25:14Z', 'reason': 'PodCompleted', 'status': 'False', 'type': 'ContainersReady'},
        {'lastTransitionTime': '2026-09-17T21:56:03Z', 'status': 'True', 'type': 'PodScheduled'}],
        'containerStatuses': [{'state': {'terminated': {'exitCode': 0, 'finishedAt': '2026-09-18T00:25:13Z',
                                                        'reason': 'Completed', 'startedAt': '2026-09-17T21:56:25Z'}}}]}}


def test_pod_facts_completed_pod():
    """B1: a finished pod (Ready False, PodCompleted) still gives Q from apply, through the container's startedAt."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, 'pod.json').write_text(json.dumps(COMPLETED_POD))
        Path(d, 'job.json').write_text(json.dumps({'metadata': {'name': 'j', 'creationTimestamp': '2026-09-17T21:55:00Z'}}))
        facts = bs.pod_facts([], Path(d, 'pod.json'))
    assert facts['queue_seconds'] == 0.0                          # created -> PodScheduled
    assert facts['pod_created_to_running_seconds'] == 22.0        # 21:56:03 -> startedAt 21:56:25
    assert facts['job_created_to_running_seconds'] == 85.0        # Job 21:55:00 -> 21:56:25
    assert facts['running_source'] == 'containerStatuses.startedAt'
    running = json.loads(json.dumps(COMPLETED_POD))
    running['status']['conditions'][2] = {'lastTransitionTime': '2026-09-17T21:56:30Z', 'status': 'True', 'type': 'Ready'}
    assert bs.running_time(running) == (bs.parse_ts('2026-09-17T21:56:30Z'), 'Ready')


def _pod_log(path, stamp, fp_value, ok, product='NVIDIA-L40', slug='l40-krule'):
    lines = [f'BENCH_POD kai-gpubench-{slug}-x product {product} slug {slug} shape krule {stamp}', 'HOSTNAME_NODE n1',
             'CPU_MODEL AMD EPYC 7302 16-Core Processor', 'CPU_COUNTS node_logical 64 allowed 18 cpus_allowed_list 0-17',
             f'FINGERPRINT {fp_value} expected 11559681 chang0926-a-n64-s1',
             'FINGERPRINT_OK chang0926-a-n64-s1' if ok else f'GPU_FINGERPRINT_MISMATCH {fp_value}']
    Path(path).write_text('\n'.join(lines) + '\n')


def _job_dir(root, slug, shape, phases, results, samples, pod_logs, confirm=True, product='NVIDIA-L40', dirname=None,
             timing=None):
    """One Job directory as copied from the PVC. dirname: a moved-aside attempt; timing: {phase: (u, t, last epoch)}."""
    d = Path(root) / (dirname or slug)
    d.mkdir(parents=True)
    Path(d, 'plan.json').write_text(json.dumps({'product': product, 'slug': slug, 'product_slug': slug.rsplit('-', 1)[0],
                                                'shape': shape, 'stop_after': 21, 'pod_cpu_request': 8, 'phases': phases}))
    for ph, res in zip(phases, results):
        (d / ph['phase'] / 'logs').mkdir(parents=True)
        Path(d, ph['phase'], 'phase_result.json').write_text(json.dumps(res))
        u, t, last = (timing or {}).get(ph['phase'], (130.0, 245.0, 21))
        for i, name in enumerate(ph['names']):
            write_log(d / ph['phase'] / 'logs' / f'{name}.log', name, u, t, resume_block=False, last=last)
            if confirm:   # what a pinned arm prints first, right after the driver's attempt header
                head, rest = (d / ph['phase'] / 'logs' / f'{name}.log').read_text().split('\n', 1)
                pin = res['cpus_pinned']
                (d / ph['phase'] / 'logs' / f'{name}.log').write_text(
                    f'{head}\nARM_CPUS n={len(bs.cpu_list(pin))} requested {pin} seen {pin} OK\n{rest}')
            if res['arms'][i]['outcome'] == 'verify_fail':
                with open(d / ph['phase'] / 'logs' / f'{name}.log', 'a') as fh:
                    fh.write('CHECKPOINT_VERIFICATION_FAIL {"error": "Max absolute difference: 2e-07"}\n')
    fields = list(bd.CSV_FIELDS)
    with open(d / 'samples.csv', 'w') as fh:
        fh.write(','.join(fields) + '\n')
        for row in samples:
            fh.write(','.join(str(row.get(k, '')) for k in fields) + '\n')
    for name, (stamp, value, ok) in pod_logs.items():
        _pod_log(d / name, stamp, value, ok, product=product, slug=slug)
    return d


def _result(ph, outcomes, pinned):
    return {'phase': ph['phase'], 'k': ph['k'], 'wall_seconds': 3000.0, 'cpu_pin': 'pinned', 'cpus_pinned': pinned,
            'cpus_pinned_n': 2 * ph['k'], 'cpus_allowed_n': 2 * ph['k'],
            'arms': [{'name': n, 'outcome': o, 'exit_code': {'ok': 0, 'verify_fail': 6, 'crash': 1}[o], 'epochs_done': 21,
                      'verification': 'FAIL' if o == 'verify_fail' else 'PASS'} for n, o in zip(ph['names'], outcomes)],
            'outcomes': {o: outcomes.count(o) for o in set(outcomes)}}


def _samples(phase, k, per_arm_cores, cpus):
    rows = []
    for i, t in enumerate(range(0, 300, 60)):
        rows.append({'phase': phase, 'kind': 'gpu', 'unix_s': t, 'cgroup_cpu_usage_usec': int(t * 1e6 * per_arm_cores * k),
                     'gpu_util_pct': 30, 'gpu_mem_used_mib': 20000, 'gpu_mem_total_mib': 46068, 'live_arms': k,
                     'epochs_done_min': 2 + i, 'epochs_done_max': 3 + i})
        rows.append({'phase': phase, 'kind': 'proc', 'unix_s': t, 'arm': 'a', 'pid': 1, 'proc_epochs_done': 2 + i,
                     'proc_cpus_allowed': cpus})
    return rows


def test_summary_rules_2_5_6_across_both_job_dirs():
    """A2 rule 5 per phase; B3 rule 6 and rule 2 product-wide across the K_rule and K_low Job directories; C3 a mismatch
    that repeats; C6 chronological pod logs (an old mismatch is not hidden by a later, alphabetically-last OK log);
    B2 non-ok arms listed; B5 low utilization is a finding, not an exclusion."""
    e2 = {'phase': 'p1-E-k2', 'class': 'E', 'k': 2, 'names': bd.CLASS_NAMES['E'][:2]}
    a1 = {'phase': 'p2-A07-k1', 'class': 'A07', 'k': 1, 'names': bd.CLASS_NAMES['A07'][:1]}
    e1 = {'phase': 'p3-E-k1', 'class': 'E', 'k': 1, 'names': bd.CLASS_NAMES['E'][:1]}
    with tempfile.TemporaryDirectory() as root:
        _job_dir(root, 'l40-krule', 'krule', [e2, a1], [_result(e2, ['ok', 'ok'], '0-3'), _result(a1, ['ok'], '0-1')],
                 _samples('p1-E-k2', 2, 2.5, '0-3') + _samples('p2-A07-k1', 1, 1.9, '0-1'),
                 # zz sorts last by name but is the OLDER pod: its mismatch must still count
                 {'pod-zz.log': ('2026-09-29T09:00:00Z', 11559680, False), 'pod-aa.log': ('2026-09-29T10:00:00Z', 11559681, True)})
        _job_dir(root, 'l40-klow', 'klow', [e1], [_result(e1, ['verify_fail'], '0-1')], _samples('p3-E-k1', 1, 1.8, '0-1'),
                 {'pod-bb.log': ('2026-09-29T09:30:00Z', 11559680, False)}, confirm=False)
        rows = bs.summarize_bench(root, None)
    by_phase = {r['phase']: r for r in rows}
    p1, p2, p3 = by_phase['p1-E-k2'], by_phase['p2-A07-k1'], by_phase['p3-E-k1']
    assert abs(p1['cpu_cores_per_arm_steady'] - 2.5) < 1e-9 and any(w.startswith('rule 5: above') for w in p1['excluded'])
    assert not any(w.startswith('rule 5') for w in p2['excluded'])
    assert any('did not confirm the pin' in w for w in p3['excluded']) and p3['arm_cpus_unconfirmed']
    for r in (p1, p2, p3):   # product-wide: the klow FAIL and the mismatches exclude every row of the product
        assert 'rule 6: checkpoint verification FAIL (product)' in r['excluded'], r['excluded']
        assert 'rule 2: fingerprint mismatch (product)' in r['excluded'], r['excluded']
        assert r['product_fingerprint_mismatch_pods'] == 2 and r['product_fingerprint_mismatch_repeats'] is True
    assert p1['fingerprint'].startswith('FINGERPRINT 11559681')    # the chronologically last pod log
    assert p3['non_ok_arms'][0]['outcome'] == 'verify_fail' and 'Max absolute' in (p3['arms'][0]['verification_error'] or '')
    assert p1['threads_within_pinned'] is True and p1['cpu_model'].startswith('AMD EPYC')
    assert any('GPU utilization mean 30.0 %' in x for x in p1['findings'])
    assert not any('utilization' in w for w in p1['excluded'])
    # C6, discriminating: the OLDER mismatch sorts FIRST by name, the newer OK log last; "last log wins" would say OK
    with tempfile.TemporaryDirectory() as d:
        _pod_log(Path(d, 'pod-aa.log'), '2026-09-29T09:00:00Z', 11559680, False)
        _pod_log(Path(d, 'pod-zz.log'), '2026-09-29T10:00:00Z', 11559681, True)
        _pod_log(Path(d, 'pod-mm.log'), '2026-09-29T11:00:00Z', 11559681, True)
        facts = bs.pod_facts(sorted(Path(d).glob('pod-*.log')), None)
    assert facts['fingerprint_ok'] is False and [g['log'] for g in facts['pod_logs']] == ['pod-aa.log', 'pod-zz.log', 'pod-mm.log']
    assert facts['fingerprint'] == 'FINGERPRINT 11559681 expected 11559681 chang0926-a-n64-s1'   # the 11:00Z pod's


def test_rule5_thread_mask_skips_pre_pin_rows():
    """PREFLIGHT critical v2 B1: a sampler row taken between Popen and the arm's own pin (proc_epochs_done 0, the pod's
    whole allowed set) must not exclude the phase; a row past epoch 1 outside the pinned CPUs still does."""
    a2 = {'phase': 'p4-A07-k2', 'class': 'A07', 'k': 2, 'names': bd.CLASS_NAMES['A07'][:2]}
    pre_pin = {'phase': 'p4-A07-k2', 'kind': 'proc', 'unix_s': 0, 'arm': bd.CLASS_NAMES['A07'][1], 'pid': 2,
               'proc_epochs_done': 0, 'proc_cpus_allowed': '0-7'}
    rows = {}
    for case, extra in (('pre_pin', pre_pin), ('escaped', dict(pre_pin, proc_epochs_done=3))):
        with tempfile.TemporaryDirectory() as root:
            _job_dir(root, 'l40-klow', 'klow', [a2], [_result(a2, ['ok', 'ok'], '0-3')],
                     _samples('p4-A07-k2', 2, 1.9, '0-3') + [extra], {})
            rows[case] = next(r for r in bs.summarize_bench(root, None) if r['phase'] == 'p4-A07-k2')
    ok, bad = rows['pre_pin'], rows['escaped']
    assert ok['threads_within_pinned'] is True and ok['thread_cpus_union'] == '0,1,2,3' and ok['thread_mask_rows'] == 5
    assert ok['excluded'] == [] and ok['R_d1'] is not None, ok['excluded']
    assert bad['threads_within_pinned'] is False and bad['thread_mask_rows'] == 6
    assert 'rule 5: an arm thread ran outside the pinned CPUs; out of T' in bad['excluded']


def test_phase_without_phase_result():
    """PREFLIGHT critical v2 C1 and B3 (STUDY Amendment 1): a deletion during the last arm's verify_selected leaves every
    arm at 21 epochs with no CHECKPOINT_VERIFICATION line and no phase_result.json. If every arm printed ARM_CPUS OK on
    one list of 2K CPUs, the pin checks run from the logs and R stands; otherwise the phase keeps no R, and no pin
    failure is asserted. The arms are verify_interrupted, never a rule-6 FAIL."""
    e2 = {'phase': 'p1-E-k2', 'class': 'E', 'k': 2, 'names': bd.CLASS_NAMES['E'][:2]}
    rows = {}
    for confirm in (True, False):
        with tempfile.TemporaryDirectory() as root:
            d = _job_dir(root, 'l40-krule', 'krule', [e2], [_result(e2, ['ok', 'ok'], '0-3')],
                         _samples('p1-E-k2', 2, 1.9, '0-3'), {}, confirm=confirm)
            (d / 'p1-E-k2' / 'phase_result.json').unlink()
            rows[confirm] = next(r for r in bs.summarize_bench(root, None) if r['phase'] == 'p1-E-k2')
    good, bad = rows[True], rows[False]
    assert (good['cpu_pin'], good['cpus_pinned'], good['cpus_pinned_n']) == ('pinned', '0-3', 4)
    assert 'arm logs' in good['cpu_pin_source'] and good['threads_within_pinned'] is True
    assert good['R_d1'] is not None and good['excluded'] == [], good['excluded']
    assert bad['R_d1'] is None and bad['run_epochs_per_gpu_hour'] is None and bad['s_d1'] is not None
    assert 'C1 (critical v2)' in bad['no_R_reason'] and bad['cpu_pin'] is None and bad['excluded'] == [], bad['excluded']
    for r in (good, bad):
        assert r['verify_interrupted_arms'] == bd.CLASS_NAMES['E'][:2] and r['verification']['FAIL'] == 0
        assert any('verify_interrupted' in x for x in r['findings'])
    # an arm that ended ok with phase_result.json is never verify_interrupted (the rules 2/5/6 fixture: no PASS line)
    with tempfile.TemporaryDirectory() as root:
        _job_dir(root, 'l40-krule', 'krule', [e2], [_result(e2, ['ok', 'ok'], '0-3')], _samples('p1-E-k2', 2, 1.9, '0-3'), {})
        assert next(r for r in bs.summarize_bench(root, None) if r['phase'] == 'p1-E-k2')['verify_interrupted_arms'] == []


def test_a10_attempts_and_baseline_check():
    """STUDY Amendment 1, critical v2 B3 and B6. B3: an A10 Job's first complete attempt counts (every phase with all K arms at 21
    epochs), ordered by the BENCH_POD stamp, not the directory name; every other attempt is listed and kept out of T.
    B6: the counted A10 s at E K=4 and A07 K=2 against Delta's slowest pure-pack canary arm, one-sided, 10 %."""
    e4 = {'phase': 'p1-E-k4', 'class': 'E', 'k': 4, 'names': bd.CLASS_NAMES['E'][:4]}
    a2 = {'phase': 'p2-A07-k2', 'class': 'A07', 'k': 2, 'names': bd.CLASS_NAMES['A07'][:2]}
    res = [_result(e4, ['ok'] * 4, '0-7'), _result(a2, ['ok'] * 2, '0-3')]
    smp = _samples('p1-E-k4', 4, 1.9, '0-7') + _samples('p2-A07-k2', 2, 1.9, '0-3')

    def summarize(attempts):
        """attempts: (directory, BENCH_POD stamp, last A07 epoch); the re-run uses the original directory name."""
        with tempfile.TemporaryDirectory() as root:
            for dirname, stamp, last in attempts:
                _job_dir(root, 'a10-krule', 'krule', [e4, a2], res, smp, {'pod-x.log': (stamp, 11559681, True)},
                         product='NVIDIA-A10', dirname=dirname, timing={'p2-A07-k2': (85.0, 150.0, last)})
            rows = bs.summarize_bench(root, None)
        a10 = {(r['job_dir'], r['phase']): r for r in rows if r['product'] == 'NVIDIA-A10' and r['phase'] != 'none'}
        status = [x for r in rows if r['class'] == 'A10 baseline (STUDY Amendment 1, critical v2 B3 and B6)' for x in r['findings']]
        return a10, status

    # (a) attempt 1 yielded during its A07 phase (epoch 15); the re-run completed: only the re-run counts
    a10, status = summarize([('a10-krule-moved-1', '2026-09-29T12:00:00Z', 15), ('a10-krule', '2026-09-29T18:00:00Z', 21)])
    for ph in ('p1-E-k4', 'p2-A07-k2'):
        first, rerun = a10[('a10-krule-moved-1', ph)], a10[('a10-krule', ph)]
        assert first['attempt'] == '1 of 2' and not first['attempt_counted'] and 'baseline_check' not in first
        assert any(w.startswith('B3: A10 krule attempt 1 of 2') for w in first['excluded']), first['excluded']
        assert rerun['attempt'] == '2 of 2' and rerun['attempt_counted'] and rerun['excluded'] == [], rerun['excluded']
    e, a = a10[('a10-krule', 'p1-E-k4')], a10[('a10-krule', 'p2-A07-k2')]
    assert abs(e['s_d1'] - 141.5) < 1e-9 and e['baseline_check']['flag'] is True          # 141.5 > 1.10 x 114.455
    assert any(x.startswith('B6: A10 s 141.50') and 'goes to Kai' in x for x in e['findings'])
    assert abs(a['s_d1'] - 91.5) < 1e-9 and a['baseline_check']['flag'] is False          # 91.5 <= 1.10 x 90.73
    assert a['baseline_check']['limit_s'] == 99.803 and not any(x.startswith('B6') for x in a['findings'])
    assert status == []                                                                   # both classes measured
    # (b) both attempts complete: the earlier stamp counts, although its directory name sorts last
    a10, _ = summarize([('a10-krule-moved-1', '2026-09-29T12:00:00Z', 21), ('a10-krule', '2026-09-29T18:00:00Z', 21)])
    assert a10[('a10-krule-moved-1', 'p1-E-k4')]['attempt_counted'] and not a10[('a10-krule', 'p1-E-k4')]['attempt_counted']
    # (c) one attempt, cut short: nothing counts, both classes read "A10 baseline not measured", B6 does not run
    a10, status = summarize([('a10-krule', '2026-09-29T12:00:00Z', 15)])
    assert not any(r['attempt_counted'] for r in a10.values())
    assert sum('A10 baseline not measured' in x for x in status) == 2 and sum('check not run' in x for x in status) == 2


def test_probe_summary():
    with tempfile.TemporaryDirectory() as d:
        Path(d, 'job.json').write_text(json.dumps({'metadata': {'name': 'kai-gpuprobe-l40-k9', 'creationTimestamp': '2026-09-29T10:00:00Z'}}))
        def pod(name, ready):
            conds = [{'type': 'PodScheduled', 'status': 'True', 'lastTransitionTime': '2026-09-29T10:01:00Z'}]
            if ready:
                conds.append({'type': 'Ready', 'status': 'True', 'lastTransitionTime': ready})
            return {'metadata': {'name': name}, 'spec': {'nodeName': 'n1'}, 'status': {'phase': 'Running', 'conditions': conds}}
        pods = [pod('p0', '2026-09-29T10:05:00Z'), pod('p1', '2026-09-29T10:15:00Z'), pod('p2', '2026-09-29T10:45:00Z'), pod('p3', None)]
        Path(d, 'pods.json').write_text(json.dumps({'items': pods}))
        r = bs.summarize_probe(Path(d, 'job.json'), Path(d, 'pods.json'), 30)
    assert r['G_obs'] == 2 and r['Q_p_median_s'] == 600.0 and r['pods'] == 4       # 300 s and 900 s inside 30 min


def test_sampler_row_with_fake_nvidia_smi_and_cgroup():
    """The pod sampler's GPU and cgroup path, with canned nvidia-smi output (a pilot-like A10 reading)."""
    import csv
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        smi = d / 'bin' / 'nvidia-smi'
        smi.parent.mkdir()
        smi.write_text('#!/bin/sh\ncase "$1" in\n'
                       '  --query-gpu=*) echo "NVIDIA A10, 23028, 21249, 100, 1695, 148.52, 67" ;;\n'
                       '  --query-compute-apps=*) echo "4242, 8446"; echo "999, 12" ;;\nesac\n')
        smi.chmod(0o755)
        cg = d / 'cg'
        cg.mkdir()
        (cg / 'cpu.stat').write_text('usage_usec 123456789\nuser_usec 1\n')
        (cg / 'memory.current').write_text(str(10 * 2 ** 30) + '\n')
        (cg / 'memory.max').write_text('max\n')
        (cg / 'memory.events').write_text('low 0\nhigh 0\nmax 0\noom 1\noom_kill 1\n')
        root = d / 'p1-E-k1'
        (root / 'runs' / 'chang0926-a-n64-s1').mkdir(parents=True)
        (root / 'runs' / 'chang0926-a-n64-s1' / 'activation_widths.jsonl').write_text('{}\n{}\n{}\n')
        old_path, old_cg = os.environ['PATH'], os.environ.get('BENCH_CGROUP_DIR')
        os.environ['PATH'] = f"{smi.parent}:{old_path}"
        os.environ['BENCH_CGROUP_DIR'] = str(cg)
        child = subprocess.Popen(['sleep', '30'])
        try:
            sampler = bd.Sampler(d / 'samples.csv', 60)
            entry = {'child': child, 'name': 'chang0926-a-n64-s1'}
            sampler.set_phase('p1-E-k1', 1, root, [entry])
            real = child.pid
            apps = bd.query_compute_apps()
            assert apps == {4242: '8446', 999: '12'}
            sampler.sample()
            sampler.handle.close()
            assert sampler.cpu_rows['p1-E-k1'][0][1:] == (123456789, 1, 3, 3)
            assert bd.cgroup_oom_kills(cg) == 1
        finally:
            child.kill()
            os.environ['PATH'] = old_path
            if old_cg is None:
                os.environ.pop('BENCH_CGROUP_DIR', None)
            else:
                os.environ['BENCH_CGROUP_DIR'] = old_cg
        rows = list(csv.DictReader((d / 'samples.csv').open()))
    gpu = [r for r in rows if r['kind'] == 'gpu'][0]
    assert (gpu['gpu_name'], gpu['gpu_mem_total_mib'], gpu['gpu_mem_used_mib'], gpu['gpu_util_pct']) == ('NVIDIA A10', '23028', '21249', '100')
    assert gpu['cgroup_cpu_usage_usec'] == '123456789' and gpu['cgroup_mem_current_bytes'] == str(10 * 2 ** 30)
    assert gpu['cgroup_mem_max_bytes'] == '' and gpu['live_arms'] == '1' and gpu['epochs_done_min'] == '3'
    procs = {r['arm']: r for r in rows if r['kind'] == 'proc'}
    assert procs['chang0926-a-n64-s1']['pid'] == str(real) and procs['chang0926-a-n64-s1']['proc_epochs_done'] == '3'
    if Path('/proc/self/task').exists():   # Linux: the arm's threads report their CPU mask
        assert procs['chang0926-a-n64-s1']['proc_cpus_allowed']
    # canned pids 4242 and 999 are not our child: both are recorded as "other"
    assert sorted(r['pid'] for r in rows if r['arm'] == 'other') == ['4242', '999']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    passed, skipped = 0, []
    for t in tests:
        result = t()
        if isinstance(result, str) and result.startswith('skip'):
            skipped.append(t.__name__)
            print('SKIP', t.__name__, '--', result)
        else:
            passed += 1
            print('PASS', t.__name__)
    print(f'ALL_PASS {passed}' + (f' SKIPPED {len(skipped)} ({", ".join(skipped)})' if skipped else ''))
