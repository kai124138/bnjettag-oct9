#!/usr/bin/env python3
"""Python >=3.6 stdlib-only bounded serialized HLS -> Vivado OOC supervisor.

No remote connections. Only the assigned work directory and its children are
written. Every termination signal targets the process group started by this
runner, never another user's Vitis/Vivado process. A final status is mechanical
success only, not a claim of FPGA device fit, timing closure, or full-jet II=1.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback
import xml.etree.ElementTree as ET

GIB = 1024 ** 3
MAX_GROUP_RSS = 64 * GIB
MIN_START_AVAILABLE = 80 * GIB
MIN_AVAILABLE = 8 * GIB
MAX_DIRECTORY = 50 * GIB
MIN_DISK_FREE = 20 * GIB
WALL_LIMITS = {'linux_csim_build': 600, 'linux_csim': 600, 'hls': 6 * 3600, 'vivado': 8 * 3600}
HLS_PART = 'xcvu13p-flga2577-2-e'
OOC_PART = 'xczu7ev-ffvc1156-2-e'
ACTIVE_TOOLS = {'vitis_hls', 'vitis-run', 'vivado', 'vivado_lab'}


def utc_now():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(temp), str(path))


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def process_table():
    rows = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            text = (entry / 'stat').read_text()
            tail = text[text.rfind(')') + 2:].split()
            comm = (entry / 'comm').read_text().strip()
            rss = max(0, int(tail[21])) * os.sysconf('SC_PAGE_SIZE')
            rows.append({'pid': int(entry.name), 'pgrp': int(tail[2]),
                         'session': int(tail[3]), 'state': tail[0], 'comm': comm,
                         'rss_bytes': rss})
        except (OSError, ValueError, IndexError):
            continue
    return rows


def mem_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise RuntimeError('Cannot read Linux MemAvailable; fail closed')


def directory_size(root):
    total = 0
    for base, directories, files in os.walk(str(root), followlinks=False):
        directories[:] = [d for d in directories if not Path(base, d).is_symlink()]
        for name in files:
            try:
                total += Path(base, name).lstat().st_size
            except FileNotFoundError:
                pass
    return total


def other_tools(exclude_group=None):
    return [{'pid': p['pid'], 'comm': p['comm']} for p in process_table()
            if p['state'] != 'Z' and p['pgrp'] != exclude_group
            and (p['comm'] in ACTIVE_TOOLS or p['comm'].startswith('vitis_hls'))]


def validate_gate(verification):
    if verification.get('gate1', {}).get('pass') is not True:
        raise RuntimeError('Gate 1 did not pass')
    if verification.get('gate2_pass') is not True:
        raise RuntimeError('Gate 2 did not pass: refusing synthesis')
    if verification.get('rf') != 1 or verification.get('clock_ns') != 2.5:
        raise RuntimeError('Expected unchanged RF=1 and 2.5 ns HLS clock')
    if verification.get('hls_part') != HLS_PART:
        raise RuntimeError('Unexpected HLS target part')


def extract_fresh(archive, root):
    project = root / 'hls_prj_rf1'
    if project.exists():
        raise RuntimeError('Refusing to reuse existing hls_prj_rf1; choose fresh work directory or archive it explicitly')
    with tarfile.open(str(archive), 'r:gz') as tar:
        members = tar.getmembers()
        if len(members) > 100000 or sum(m.size for m in members) > 10 * GIB:
            raise RuntimeError('Unexpected archive size/member count')
        for member in members:
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'hls_prj_rf1':
                raise RuntimeError('Unsafe/unexpected archive path: ' + member.name)
            if not (member.isfile() or member.isdir()):
                raise RuntimeError('Links/devices are forbidden in input archive')
        tar.extractall(str(root), members=members)
    return project


def hls_summary(report):
    tree = ET.parse(str(report))
    root = tree.getroot()
    wanted = ('Best-caseLatency', 'Worst-caseLatency', 'Interval-min', 'Interval-max',
              'EstimatedClockPeriod', 'TargetClockPeriod', 'Part', 'LUT', 'FF',
              'DSP', 'BRAM_18K', 'URAM')
    values = {}
    for element in root.iter():
        key = element.tag.rsplit('}', 1)[-1]
        if key in wanted and element.text:
            values.setdefault(key, []).append(element.text.strip())
    return {'report': str(report), 'raw_xml_fields': values,
            'interpretation': 'HLS estimates only. Inspect achieved top-level interval and timing; RF=1 alone does not establish full-jet II=1.'}


class Supervisor:
    def __init__(self, root):
        self.root = root
        self.runner = Path(__file__).resolve().parent
        self.child = None
        self.group = None
        self.state = {'runner_pid': os.getpid(), 'started_utc': utc_now(),
                      'phase': 'initializing', 'hls_part': HLS_PART, 'ooc_part': OOC_PART,
                      'clock_ns': 2.5, 'reuse_factor': 1, 'vivado_threads': 4,
                      'limits': {'group_rss_bytes': MAX_GROUP_RSS, 'minimum_start_mem_available_bytes': MIN_START_AVAILABLE,
                                 'minimum_mem_available_bytes': MIN_AVAILABLE, 'directory_bytes': MAX_DIRECTORY,
                                 'minimum_disk_free_bytes': MIN_DISK_FREE, 'stage_wall_seconds': WALL_LIMITS},
                      'stages': {}}

    def save(self, **changes):
        self.state.update(changes)
        self.state['updated_utc'] = utc_now()
        atomic_json(self.root / 'status.json', self.state)

    def start_guard(self):
        active = other_tools()
        if active:
            raise RuntimeError('Other Vitis/Vivado processes active: ' + json.dumps(active))
        if mem_available() < MIN_START_AVAILABLE:
            raise RuntimeError('Start guard requires at least 80 GiB MemAvailable')
        if shutil.disk_usage(str(self.root)).free < MIN_DISK_FREE:
            raise RuntimeError('Start guard requires at least 20 GiB disk free')
        if directory_size(self.root) > MAX_DIRECTORY:
            raise RuntimeError('Work directory already exceeds 50 GiB')

    def group_members(self):
        return [p for p in process_table() if p['pgrp'] == self.group and p['session'] == self.group and p['state'] != 'Z']

    def stop_child(self):
        if self.group is None or self.group == os.getpgrp():
            return
        # New session/group was created by this runner; only its live members count.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            if not self.group_members():
                break
            try:
                os.killpg(self.group, sig)
            except ProcessLookupError:
                break
            deadline = time.monotonic() + (20 if sig == signal.SIGTERM else 5)
            while self.group_members() and time.monotonic() < deadline:
                time.sleep(0.5)
        if self.child is not None:
            try:
                self.child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass

    def run_stage(self, stage, command, cwd):
        self.start_guard()
        started = time.monotonic()
        log_path = self.root / 'logs' / (stage + '.log')
        with log_path.open('wb') as log, (self.root / 'samples.jsonl').open('a') as samples:
            self.child = subprocess.Popen(command, cwd=str(cwd), stdout=log,
                                          stderr=subprocess.STDOUT, start_new_session=True)
            self.group = self.child.pid
            self.state['stages'][stage] = {'started_utc': utc_now(), 'command': command,
                                           'cwd': str(cwd), 'pid': self.child.pid, 'process_group': self.group,
                                           'stdout_log': str(log_path), 'wall_limit_seconds': WALL_LIMITS[stage]}
            self.save(phase=stage + '_running', child_pid=self.child.pid, child_process_group=self.group)
            size = directory_size(self.root)
            next_size_check = time.monotonic() + 30
            try:
                while True:
                    elapsed = time.monotonic() - started
                    if time.monotonic() >= next_size_check:
                        size = directory_size(self.root)
                        next_size_check = time.monotonic() + 30
                    sample = {'utc': utc_now(), 'stage': stage, 'elapsed_seconds': elapsed,
                              'process_group': self.group, 'rss_bytes': sum(p['rss_bytes'] for p in self.group_members()),
                              'mem_available_bytes': mem_available(), 'directory_bytes': size,
                              'disk_free_bytes': shutil.disk_usage(str(self.root)).free}
                    samples.write(json.dumps(sample, allow_nan=False) + '\n')
                    samples.flush()
                    self.save(last_sample=sample)
                    breaches = []
                    if sample['rss_bytes'] > MAX_GROUP_RSS: breaches.append('group RSS exceeds 64 GiB')
                    if sample['mem_available_bytes'] < MIN_AVAILABLE: breaches.append('MemAvailable below 8 GiB')
                    if size > MAX_DIRECTORY: breaches.append('directory exceeds 50 GiB')
                    if sample['disk_free_bytes'] < MIN_DISK_FREE: breaches.append('disk free below 20 GiB')
                    if elapsed > WALL_LIMITS[stage]: breaches.append(stage + ' wall limit exceeded')
                    if breaches:
                        raise RuntimeError('; '.join(breaches))
                    code = self.child.poll()
                    if code is not None:
                        if code:
                            raise RuntimeError(stage + ' exited with code ' + str(code))
                        if self.group_members():
                            raise RuntimeError(stage + ' exited but child processes remain')
                        break
                    time.sleep(10)
            except BaseException:
                self.stop_child()
                raise
            self.state['stages'][stage].update(completed_utc=utc_now(), elapsed_seconds=time.monotonic() - started, exit_code=0)
            self.child = None
            self.group = None
            self.save(phase=stage + '_complete', child_pid=None, child_process_group=None)

    def run(self):
        verification_path = self.root / 'export' / 'verification.json'
        archive = self.root / 'export' / 'hls_prj_rf1.tar.gz'
        verification = json.loads(verification_path.read_text())
        validate_gate(verification)
        self.start_guard()
        archive_sha = sha256(archive)
        if verification.get('hls_archive_sha256') and verification['hls_archive_sha256'] != archive_sha:
            raise RuntimeError('Archive SHA does not match verified export')
        self.save(input_archive_sha256=archive_sha, verification_sha256=sha256(verification_path),
                  checkpoint_sha256=verification.get('checkpoint_sha256'), gate1_pass=True, gate2_pass=True)
        tools = {}
        for name in ('vitis_hls', 'vivado'):
            resolved = shutil.which(name)
            if not resolved or '2023.2' not in str(Path(resolved).resolve()):
                raise RuntimeError(name + ' must resolve to the 2023.2 toolchain')
            tools[name] = resolved
        self.save(tools=tools)
        project = extract_fresh(archive, self.root)
        project_tcl = (project / 'project.tcl').read_text()
        part_match = re.search(r'set\s+part\s+"?([^"\s]+)', project_tcl)
        clock_match = re.search(r'set\s+clock_period\s+([0-9.]+)', project_tcl)
        top_match = re.search(r'set\s+project_name\s+"?([A-Za-z_][A-Za-z_0-9]*)', project_tcl)
        if not part_match or part_match.group(1) != HLS_PART or not clock_match or float(clock_match.group(1)) != 2.5 or not top_match:
            raise RuntimeError('Export project target/clock/top does not match gated settings')
        top = top_match.group(1)
        reuse = re.findall(r'ReuseFactor:\s*(\d+)', (project / 'hls4ml_config.yml').read_text())
        if not reuse or any(int(value) != 1 for value in reuse):
            raise RuntimeError('Export must preserve RF=1 at every configured layer')
        original_options = (project / 'build_opt.tcl').read_text()
        (self.root / 'reports' / 'original_build_opt.tcl').write_text(original_options)
        (project / 'build_opt.tcl').write_text('array set opt {\n reset 0\n csim 0\n synth 1\n cosim 0\n validation 0\n export 0\n vsynth 0\n fifo_opt 0\n}\n')
        # Fresh archive must not contain stale synthesis products that could masquerade as new output.
        solution = project / (top + '_prj') / 'solution1'
        if (solution / 'syn').exists():
            raise RuntimeError('Archive contains stale HLS synthesis output; require clean export')
        self.run_stage('linux_csim_build', ['bash', 'build_lib.sh'], project)
        csim_python = '/home/users/kayamaguchi/micromamba/envs/bnjet/bin/python'
        self.run_stage('linux_csim', [csim_python, str(self.root / 'remote_csim.py'),
                       '--project', str(project), '--inputs', str(self.root / 'export' / 'csim_inputs.npy'),
                       '--reference', str(self.root / 'export' / 'csim_reference.npy')], project)
        linux_gate = json.loads((self.root / 'linux_csim_verification.json').read_text())
        if linux_gate.get('bit_exact') is not True or linux_gate.get('n') != 4096 or linux_gate.get('max_abs_diff') != 0:
            raise RuntimeError('Linux C simulation is not strictly bit-exact on all 4096 samples')
        self.save(linux_csim_pass=True, linux_csim_verification=linux_gate)
        self.run_stage('hls', [tools['vitis_hls'], '-f', 'build_prj.tcl'], project)
        report = solution / 'syn' / 'report' / (top + '_csynth.xml')
        rtl = solution / 'syn' / 'verilog'
        if not report.is_file() or report.stat().st_size == 0:
            raise RuntimeError('Successful HLS exit did not produce top-level csynth XML')
        sources = sorted(list(rtl.glob('*.v')) + list(rtl.glob('*.sv')))
        if not sources or any(p.stat().st_size == 0 for p in sources):
            raise RuntimeError('Successful HLS exit did not produce nonempty RTL')
        atomic_json(self.root / 'reports' / 'hls_summary.json', hls_summary(report))
        shutil.copyfile(str(report), str(self.root / 'reports' / 'hls_csynth.xml'))
        atomic_json(self.root / 'reports' / 'rtl_manifest.json', [{'name': p.name, 'sha256': sha256(p)} for p in sources])
        ooc_reports = self.root / 'reports' / 'ooc_xczu7ev'
        ooc_reports.mkdir()
        self.run_stage('vivado', [tools['vivado'], '-mode', 'batch', '-notrace',
                       '-source', str(self.runner / 'ooc.tcl'), '-log', str(self.root / 'logs' / 'vivado_tool.log'),
                       '-journal', str(self.root / 'logs' / 'vivado.jou'), '-tclargs', str(rtl),
                       str(ooc_reports), top, str(self.runner / 'clock.xdc')], rtl)
        required = ['post_synth_utilization.rpt', 'post_synth_timing.rpt', 'post_synth.dcp',
                    'post_opt_utilization.rpt', 'post_opt_timing.rpt', 'post_opt.dcp']
        if any(not (ooc_reports / name).is_file() or (ooc_reports / name).stat().st_size == 0 for name in required):
            raise RuntimeError('Vivado exited without every required report/checkpoint')
        self.save(phase='complete', completed_utc=utc_now(), reports=str(self.root / 'reports'),
                  interpretation='HLS VU13P estimates and Vivado xczu7ev OOC synthesis/optimization are distinct targets. No place/route timing closure or full-jet II=1 claim.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', type=Path, default=Path.home() / 'bnjet_ebops_r4_20260917')
    args = parser.parse_args()
    root = args.workdir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = (root / 'runner.lock').open('a+')
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('Another runner owns runner.lock; active status was not modified', file=sys.stderr)
        return 2
    for name in ('tmp', 'logs', 'reports'):
        (root / name).mkdir(exist_ok=True)
    os.environ.update(TMPDIR=str(root / 'tmp'), TMP=str(root / 'tmp'), TEMP=str(root / 'tmp'))
    runner = Supervisor(root)
    (root / 'runner.pid').write_text(str(os.getpid()) + '\n')
    def interrupt(signum, frame):
        raise InterruptedError('Runner received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        runner.save()
        runner.run()
        return 0
    except BaseException as exc:
        runner.stop_child()
        error = {'type': type(exc).__name__, 'message': str(exc)}
        try:
            (root / 'logs' / 'runner_error.log').write_text(traceback.format_exc())
            runner.save(phase='terminated' if isinstance(exc, (InterruptedError, KeyboardInterrupt)) else 'failed', error=error,
                        completed_utc=utc_now(), child_pid=None, child_process_group=None)
        except BaseException:
            traceback.print_exc()
        print(json.dumps(error), file=sys.stderr)
        return 1
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()

if __name__ == '__main__':
    sys.exit(main())
