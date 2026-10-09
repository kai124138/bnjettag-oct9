#!/usr/bin/env python3
"""Pre-launch checks and cluster status for NRP Nautilus jobs (namespace cms-ml).

Two modes:

    nrp_doctor.py status              quota, our jobs, hung Running pods, why pods are Pending
    nrp_doctor.py lint <job.yaml>...  check a manifest before kubectl apply
    nrp_doctor.py mulder              ssh reachability, disks, Vitis, running synthesis
    nrp_doctor.py all                 status + mulder, one call

The rules behind the checks are documented once, in
docs/infrastructure/nrp-nautilus-setup.md -> "Scheduling, GPU pools and job shape".
This script is the executable form of that section; if they disagree, the doc is right
and this file is a bug.

Node facts are read live from the cluster, never hardcoded, so the resource-name check
stays true as Nautilus changes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

NS = "cms-ml"
MINE = "kai-"
DOC = "docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape'"

# Nodes advertise GPUs under a class-specific resource name. Anything not in this set
# is assumed to live under generic nvidia.com/gpu; the map is confirmed live in
# gpu_resource_map() below, which is what the checks actually use.
NARROW_HINT = ("a100", "a40", "h100", "h200", "gh200")

# Nodes that advertise GPUs their driver can no longer see. They accept pods and reject
# them at admission in seconds ("UnexpectedAdmissionError ... GPU is lost"), burning a
# retry each time. Kept in step with the table in .claude/memory/cluster-inventory.md,
# which the cluster-ops agent maintains. Add a node here the moment it is diagnosed.
KNOWN_BAD_NODES = {
    "nautilus-ext-gpu01.fullerton.edu": "2026-09-17 UnexpectedAdmissionError: GPU is lost",
    "hcc-nrp-shor-c6017.unl.edu": "2026-09-28 epoch-0 NaN with 4-5 processes per A10 (delta-screen REGRESSION_TICKET.md); excluded as a precaution",
}

# A Running pod whose newest log line is older than this is treated as hung. Our trainers
# print one line per epoch (about a minute), so hours of silence is never normal. Added
# after 2026-09-19: an ablation pod sat Running on an idle GPU for 3d18h (inventory).
STALE_LOG_HOURS = 2.0

# A Failed Job with no active pods is only worth a fresh WARN for this long after its
# Failed condition transitioned; otherwise every already-handled Failed Job (there are
# several sitting around from past campaigns) re-fires the WARN on every call, and a real
# new failure gets lost in the noise. Added after 2026-09-26 (see cluster-inventory.md):
# a Failed Job's W&B run can sit "running" for days with nobody noticing.
STALE_FAILED_JOB_HOURS = 72.0


def kube(*args: str) -> str:
    """Run kubectl, returning stdout. Raises with stderr on failure."""
    r = subprocess.run(("kubectl",) + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"kubectl {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


def kube_json(*args: str) -> dict:
    return json.loads(kube(*args, "-o", "json"))


# ---------------------------------------------------------------- cluster facts


def gpu_resource_map() -> tuple[dict[str, str], Counter]:
    """Map GPU product label -> the resource name you must REQUEST to get one.

    Returns (product -> resource, product -> count of schedulable nodes).
    """
    nodes = kube_json("get", "nodes")["items"]
    product_res: dict[str, str] = {}
    counts: Counter = Counter()
    for n in nodes:
        product = n["metadata"].get("labels", {}).get("nvidia.com/gpu.product")
        if not product:
            continue
        alloc = n.get("status", {}).get("allocatable", {})
        # Pick the nvidia.com/* resource this node actually offers a nonzero amount of.
        offered = [
            k for k, v in alloc.items()
            if k.startswith("nvidia.com/") and k != "nvidia.com/gpu.shared"
            and str(v) not in ("0", "")
        ]
        if not offered:
            continue
        res = sorted(offered, key=lambda k: (k == "nvidia.com/gpu", k))[0]
        product_res.setdefault(product, res)
        counts[product] += 1
    return product_res, counts


def our_pending_pods() -> list[tuple[str, str]]:
    pods = kube_json("-n", NS, "get", "pods")["items"]
    out = []
    for p in pods:
        name = p["metadata"]["name"]
        if not name.startswith(MINE) or p.get("status", {}).get("phase") != "Pending":
            continue
        msg = ""
        for c in p["status"].get("conditions", []):
            if c.get("type") == "PodScheduled" and c.get("status") == "False":
                msg = c.get("message", "")
        out.append((name, msg))
    return out


def _parse_ts(ts: str) -> datetime:
    """Parse a k8s / `kubectl logs --timestamps` RFC3339 stamp (nanoseconds dropped)."""
    return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def our_running_pods() -> list[tuple[str, str, float, float | None]]:
    """(name, node, hours running, hours since newest log line or None if unreadable)."""
    pods = kube_json("-n", NS, "get", "pods")["items"]
    now = datetime.now(timezone.utc)
    out = []
    for p in pods:
        name, st = p["metadata"]["name"], p.get("status", {})
        if not name.startswith(MINE) or st.get("phase") != "Running" or not st.get("startTime"):
            continue
        age = (now - _parse_ts(st["startTime"])).total_seconds() / 3600
        try:
            lines = kube("-n", NS, "logs", name, "--timestamps", "--tail=1").strip().splitlines()
            quiet = (now - _parse_ts(lines[-1])).total_seconds() / 3600 if lines else None
        except (RuntimeError, ValueError):
            quiet = None
        out.append((name, p.get("spec", {}).get("nodeName") or "<unknown>", age, quiet))
    return out


def bucket_scheduling_message(msg: str) -> list[tuple[int, str]]:
    """Collapse a scheduler message into its large buckets, dropping per-node taints."""
    buckets: list[tuple[int, str]] = []
    # The message starts "0/532 nodes are available: <reason>, <reason>, ..." — strip the
    # preamble first, or the FIRST reason gets glued to it and silently dropped. That
    # matters: the affinity bucket is often first, and it is the one we most need to see.
    msg = msg.split("available:", 1)[-1]
    for part in msg.split(","):
        part = part.strip().rstrip(".")
        if not part or "untolerated taint" in part:
            continue
        head = part.split(" ", 1)
        if head[0].isdigit() and len(head) == 2:
            n = int(head[0])
            if n > 1:
                buckets.append((n, head[1]))
    return sorted(buckets, reverse=True)


# ---------------------------------------------------------------- status


def cmd_status() -> int:
    rc = 0
    print("== quota ==")
    try:
        rq = kube_json("-n", NS, "get", "resourcequota")["items"]
    except RuntimeError as e:
        print(f"  ! {e}")
        return 2
    for q in rq:
        qname = q["metadata"]["name"]
        hard = q["status"].get("hard", {})
        used = q["status"].get("used", {})
        for k in sorted(hard):
            if not (k.startswith("requests.nvidia") or k == "pods"):
                continue
            h, u = hard[k], used.get(k, "0")
            # A "pods 0/0" quota is a priority-class ban, not a pod cap; label it as such.
            if k == "pods" and h == "0":
                print(f"  {qname:32s} {'(priority class blocked)':>17s}")
                continue
            flag = "  <-- BANNED (0)" if h == "0" else ""
            print(f"  {k:32s} {u:>5s} / {h:<5s}{flag}")

    print("\n== our jobs ==")
    jobs = kube_json("-n", NS, "get", "jobs")["items"]
    ours = [j for j in jobs if j["metadata"]["name"].startswith(MINE)]
    if not ours:
        print("  (none)")
    now = datetime.now(timezone.utc)
    for j in ours:
        s, st = j["spec"], j.get("status", {})
        cond = ""
        failed_since: datetime | None = None
        for c in st.get("conditions", []):
            if c.get("status") == "True" and c.get("type") in ("Failed", "Complete"):
                cond = f"  [{c['type']}: {c.get('reason','')}]"
                if c["type"] == "Failed":
                    ts = c.get("lastTransitionTime")
                    failed_since = _parse_ts(ts) if ts else now
        print(
            f"  {j['metadata']['name']:42s} par={s.get('parallelism')} "
            f"comp={s.get('completions')} active={st.get('active',0)} "
            f"succeeded={st.get('succeeded',0)} failed={st.get('failed',0)}{cond}"
        )
        # A Failed Job with active=0 is a dead job — most dangerously, its W&B run(s) can
        # still show "running" for days because nothing inside a killed pod ever tells W&B
        # the run is done (2026-09-26, cluster-inventory.md). Only WARN inside a recency
        # window: this cluster accumulates old, already-handled Failed Jobs, and a WARN on
        # every one of them every time is how a new failure hides in the noise again.
        if failed_since is not None and st.get("active", 0) == 0:
            age_h = (now - failed_since).total_seconds() / 3600.0
            if age_h <= STALE_FAILED_JOB_HOURS:
                rc = 1
                print(f"    WARN  FAILED JOB ({age_h:.1f}h ago), no active pods: check its W&B")
                print("          run(s) for a stuck 'running' state (nothing inside a killed pod")
                print("          marks it finished). Capture pod logs/state before GC; see")
                print("          cluster-inventory.md 2026-09-26.")

    print("\n== our running pods (newest log line) ==")
    running = our_running_pods()
    if not running:
        print("  (none running)")
    for name, node, age, quiet in running:
        shown = "no log line readable" if quiet is None else f"last log {quiet:.1f}h ago"
        print(f"  {name}  on {node}  up {age:.1f}h  {shown}")
        # A pod younger than the threshold may still be installing; silence there is normal.
        if age > STALE_LOG_HOURS and (quiet is None or quiet > STALE_LOG_HOURS):
            rc = 1
            print(f"    WARN  HUNG/IDLE POD: Running but silent for > {STALE_LOG_HOURS:g}h. An idle GPU")
            print("          pod violates Nautilus policy. Capture /proc/1 wchan + logs, then delete")
            print("          the POD (not the Job); see cluster-inventory.md 2026-09-19.")

    print("\n== our pending pods ==")
    pend = our_pending_pods()
    if not pend:
        print("  (none pending)")
    for name, msg in pend:
        print(f"  {name}")
        buckets = bucket_scheduling_message(msg)
        if not buckets:
            print("    (no scheduling message yet)")
            continue
        for n, reason in buckets[:5]:
            print(f"    {n:>4d}  {reason}")
        top = buckets[0][1]
        if "affinity" in top or "selector" in top:
            print("    => OUR manifest is the problem: the required list is too narrow.")
            print("       Waiting will not help. Widen it and resubmit.")
        elif "Insufficient" in top:
            print("    => genuine saturation for that resource class. Waiting may help;")
            print("       widening the pool helps faster.")

    print("\n== admission errors on our pods ==")
    try:
        pods = kube_json("-n", NS, "get", "pods")["items"]
    except RuntimeError:
        pods = []
    offenders: Counter = Counter()
    for p in pods:
        if not p["metadata"]["name"].startswith(MINE):
            continue
        if p.get("status", {}).get("reason") == "UnexpectedAdmissionError":
            offenders[p.get("spec", {}).get("nodeName") or "<unknown>"] += 1
    if not offenders:
        print("  (none)")
    for node, n in offenders.most_common():
        flag = "  <-- already in KNOWN_BAD_NODES" if node in KNOWN_BAD_NODES else ""
        print(f"  {n:>3d} rejected on {node}{flag}")
        if node not in KNOWN_BAD_NODES and n >= 2:
            print("       => likely a BAD NODE (GPUs advertised but gone). Exclude it by")
            print("          hostname, add it to KNOWN_BAD_NODES and to cluster-inventory.md.")

    print(f"\n(rules: {DOC})")
    return rc


# ---------------------------------------------------------------- lint


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []
        self.notes: list[str] = []

    def error(self, m: str) -> None:
        self.errors.append(m)

    def warn(self, m: str) -> None:
        self.warns.append(m)

    def note(self, m: str) -> None:
        self.notes.append(m)


def load_manifests(path: str) -> list[dict]:
    """Load Job manifests from YAML or JSON, including a kubectl-dumped live object."""
    docs: list[dict] = []
    if path.endswith((".yaml", ".yml")):
        # kubectl is already a hard requirement, so use it to parse YAML rather than
        # depending on PyYAML (which is not installed on this laptop). --dry-run=client
        # is local-only: it contacts no cluster and creates nothing.
        try:
            out = kube("create", "--dry-run=client", "-o", "json", "-f", path)
        except RuntimeError as e:
            print(f"! cannot parse {path}: {e}", file=sys.stderr)
            return []
        obj = json.loads(out)
        docs = obj.get("items", [obj]) if obj.get("kind") == "List" else [obj]
    else:
        obj = json.loads(open(path).read())
        docs = obj.get("items", [obj]) if isinstance(obj, dict) else list(obj)
    jobs = [d for d in docs if d.get("kind") == "Job"]
    # A live dump may carry the original manifest in an annotation; prefer the spec we see.
    return jobs


def required_products(pod_spec: dict) -> list[str]:
    aff = (pod_spec.get("affinity") or {}).get("nodeAffinity") or {}
    req = aff.get("requiredDuringSchedulingIgnoredDuringExecution") or {}
    prods: list[str] = []
    for term in req.get("nodeSelectorTerms", []) or []:
        for expr in term.get("matchExpressions", []) or []:
            if expr.get("key") == "nvidia.com/gpu.product" and expr.get("operator") == "In":
                prods.extend(expr.get("values", []))
    return prods


def lint_job(job: dict, product_res: dict[str, str], counts: Counter) -> Report:
    r = Report()
    spec = job["spec"]
    pod = spec["template"]["spec"]
    containers = pod.get("containers", [])

    requested = set()
    for c in containers:
        for bucket in ("requests", "limits"):
            for k in (c.get("resources", {}).get(bucket, {}) or {}):
                if k.startswith("nvidia.com/"):
                    requested.add(k)

    prods = required_products(pod)

    # --- the bug that cost us today: product pinned but resource name doesn't match
    if prods and requested:
        unreachable = []
        for p in prods:
            need = product_res.get(p)
            if need is not None and need not in requested:
                unreachable.append((p, need))
        unknown = [p for p in prods if p not in product_res]
        if unknown:
            r.warn(
                "required-list product(s) match no node in the cluster (typo, or the "
                "hardware is gone): " + ", ".join(unknown)
            )
        reachable = [p for p in prods if product_res.get(p) in requested]
        if not reachable:
            r.error(
                f"NO product in the required list is reachable: the pod requests "
                f"{'/'.join(sorted(requested))} but every listed product needs a "
                f"different resource name. This job can never schedule."
            )
        elif unreachable:
            # Dead entries in an otherwise-workable list: harmless to the scheduler,
            # but they make the pool look wider than it is. Say so once, compactly.
            dead = ", ".join(f"{p} (needs {need})" for p, need in unreachable)
            r.warn(
                f"{len(unreachable)} required-list product(s) unreachable with "
                f"{'/'.join(sorted(requested))} and silently ignored: {dead}"
            )
        if reachable:
            n = sum(counts.get(p, 0) for p in reachable)
            msg = f"required pool = {len(reachable)} products / {n} nodes cluster-wide"
            (r.warn if n < 30 else r.note)(
                msg + ("  <-- narrow; expect queueing" if n < 30 else "")
            )
    elif not prods:
        r.note("no required GPU product list — widest possible pool (good)")

    # --- known-bad nodes must be excluded by hostname
    excluded = set()
    aff = (pod.get("affinity") or {}).get("nodeAffinity") or {}
    req = aff.get("requiredDuringSchedulingIgnoredDuringExecution") or {}
    for term in req.get("nodeSelectorTerms", []) or []:
        for expr in term.get("matchExpressions", []) or []:
            if expr.get("key") == "kubernetes.io/hostname" and expr.get("operator") == "NotIn":
                excluded.update(expr.get("values", []))
    missing = [n for n in KNOWN_BAD_NODES if n not in excluded]
    if missing:
        for n in missing:
            r.warn(
                f"does not exclude known-bad node {n} ({KNOWN_BAD_NODES[n]}). It will "
                f"accept pods and fail them at admission, spending a retry each time. "
                f"Add a kubernetes.io/hostname NotIn rule."
            )

    # --- concurrency
    comp = spec.get("completions")
    par = spec.get("parallelism")
    indexed = spec.get("completionMode") == "Indexed"
    if indexed and comp and par and par < comp:
        r.warn(
            f"parallelism={par} but completions={comp}: at most {par} run at once. "
            f"This is a self-imposed ceiling, not a cluster limit."
        )

    # --- failure limits (only meaningful for Indexed campaigns)
    if indexed:
        bpi = spec.get("backoffLimitPerIndex")
        mfi = spec.get("maxFailedIndexes")
        if bpi is not None and bpi <= 1:
            r.warn(f"backoffLimitPerIndex={bpi}: one blip kills an index. Suggest 3.")
        if mfi is not None and comp and comp >= 6 and mfi <= 2:
            r.error(
                f"maxFailedIndexes={mfi} with completions={comp}: {mfi} bad indexes kill "
                f"ALL {comp} runs, including ones that never started. "
                f"This is what failed kai-batch0917-screen-e100. Suggest {max(3, comp // 2)}."
            )
        pfp = spec.get("podFailurePolicy")
        ignores_disruption = False
        for rule in (pfp or {}).get("rules", []) or []:
            if rule.get("action") == "Ignore":
                for c in rule.get("onPodConditions", []) or []:
                    if c.get("type") == "DisruptionTarget":
                        ignores_disruption = True
        if not ignores_disruption:
            r.warn(
                "no podFailurePolicy ignoring DisruptionTarget: a Nautilus preemption "
                "spends one of this index's retries, so evictions can fail a healthy run."
            )
    else:
        r.note("single (non-Indexed) Job — per-index limits N/A; "
               "backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here")

    if spec.get("activeDeadlineSeconds") is None:
        r.note("no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)")

    # --- [rule PACK] GPU utilization floor: small arms share a pod.
    # Doctrine: docs/infrastructure/nrp-nautilus-setup.md, "GPU utilization floor".
    # NRP alerts below 40 % average utilization over 3 h; one ~19k-parameter arm sits at
    # 27-39 %, so a GPU Job must say how many arms share each pod and size cpu/memory for it.
    gpus = 0
    cpu_req = mem_req_gi = None
    for c in containers:
        res = c.get("resources", {}) or {}
        for bucket in ("requests", "limits"):
            for k, v in (res.get(bucket, {}) or {}).items():
                if k.startswith("nvidia.com/"):
                    try:
                        gpus = max(gpus, int(v))
                    except (TypeError, ValueError):
                        pass
        req = res.get("requests", {}) or {}
        if cpu_req is None and "cpu" in req:
            cpu_req = _parse_cpu(req["cpu"])
        if mem_req_gi is None and "memory" in req:
            mem_req_gi = _parse_mem_gi(req["memory"])
    if gpus:
        meta = job.get("metadata", {}) or {}
        tmeta = (spec.get("template", {}) or {}).get("metadata", {}) or {}
        tags = {}
        for src in (meta.get("labels"), meta.get("annotations"), tmeta.get("labels"), tmeta.get("annotations")):
            tags.update(src or {})
        declared = tags.get("bnjettag.io/arms-per-pod")
        justified = tags.get("bnjettag.io/single-arm-justified")
        if declared is None:
            r.warn(
                "[rule PACK] GPU Job does not declare bnjettag.io/arms-per-pod. NRP alerts below "
                "40% average GPU utilization and one small arm sits at 27-39%; pack about 3 arms "
                "per pod (setup doc, 'GPU utilization floor'). Add the label, or "
                "bnjettag.io/single-arm-justified: '<why>' if this model saturates a GPU alone."
            )
        else:
            try:
                k = int(declared)
            except ValueError:
                k = 0
                r.error(f"[rule PACK] bnjettag.io/arms-per-pod={declared!r} is not an integer.")
            if k == 1 and not justified:
                r.warn(
                    "[rule PACK] one arm per pod with no bnjettag.io/single-arm-justified "
                    "annotation: this shape averaged 24-39% GPU utilization and drew an NRP warning "
                    "(cluster-inventory 2026-09-20)."
                )
            if k >= 2:
                if cpu_req is not None and cpu_req < 2 * k - 0.5:
                    r.warn(f"[rule PACK] cpu={cpu_req:g} for {k} arms per pod; the packing recipe "
                           f"sizes about 2 cores per arm (arms are one-core launch-bound).")
                if mem_req_gi is not None and mem_req_gi < 6 * k - 1:
                    r.warn(f"[rule PACK] memory={mem_req_gi:g}Gi for {k} arms per pod; the packing "
                           f"recipe sizes about 6 Gi per arm.")
                r.note(f"[rule PACK] {k} arms per pod declared.")

    return r


def _parse_cpu(v) -> float | None:
    """'6' -> 6.0, '1500m' -> 1.5."""
    s = str(v).strip()
    try:
        return int(s[:-1]) / 1000 if s.endswith("m") else float(s)
    except ValueError:
        return None


def _parse_mem_gi(v) -> float | None:
    """'18Gi' -> 18.0, '512Mi' -> 0.5, '2G' -> ~1.86."""
    s = str(v).strip()
    units = {"Ki": 1 / 1024 ** 2, "Mi": 1 / 1024, "Gi": 1.0, "Ti": 1024.0,
             "K": 1e3 / 1024 ** 3, "M": 1e6 / 1024 ** 3, "G": 1e9 / 1024 ** 3, "T": 1e12 / 1024 ** 3}
    for u, f in sorted(units.items(), key=lambda kv: -len(kv[0])):
        if s.endswith(u):
            try:
                return float(s[:-len(u)]) * f
            except ValueError:
                return None
    try:
        return float(s) / 1024 ** 3
    except ValueError:
        return None


def cmd_lint(paths: list[str]) -> int:
    try:
        product_res, counts = gpu_resource_map()
    except RuntimeError as e:
        print(f"! cannot read nodes, resource-name check disabled: {e}", file=sys.stderr)
        product_res, counts = {}, Counter()

    worst = 0
    for path in paths:
        jobs = load_manifests(path)
        if not jobs:
            print(f"-- {path}: no Job manifest found")
            continue
        for job in jobs:
            name = job.get("metadata", {}).get("name", "<unnamed>")
            print(f"\n== {path} :: {name} ==")
            r = lint_job(job, product_res, counts)
            for m in r.errors:
                print(f"  ERROR  {m}")
            for m in r.warns:
                print(f"  WARN   {m}")
            for m in r.notes:
                print(f"  note   {m}")
            if not (r.errors or r.warns):
                print("  OK")
            worst = max(worst, 2 if r.errors else (1 if r.warns else 0))
    print(f"\n(rules: {DOC})")
    return worst


# ---------------------------------------------------------------- mulder

MULDER = "mulder"  # ssh alias from ~/.ssh/config (see .claude/skills/vitis-mulder)
VITIS_SETTINGS = "/data/software/xilinx/Vitis/2023.2/settings64.sh"

# One remote script, key=value lines out. Every fact below is read live on the box.
MULDER_PROBE = r"""
echo host=$(hostname)
echo load=$(cut -d' ' -f1 /proc/loadavg)
echo uptime_days=$(awk '{printf "%d", $1/86400}' /proc/uptime)
echo home_pct=$(df -P ~ | awk 'NR==2{gsub("%","",$5); print $5}')
echo home_free=$(df -h ~ | awk 'NR==2{print $4}')
echo root_pct=$(df -P / | awk 'NR==2{gsub("%","",$5); print $5}')
echo root_free=$(df -h / | awk 'NR==2{print $4}')
echo mem_avail_gb=$(free -g | awk '/^Mem:/{print $7}')
echo vitis_settings=$([ -f __VITIS__ ] && echo present || echo MISSING)
echo vitis_procs=$(pgrep -c -f 'vitis_hls|vitis-run' 2>/dev/null)
echo vitis_procs_mine=$(pgrep -c -u "$USER" -f 'vitis_hls|vitis-run' 2>/dev/null)
echo tmpdir=${TMPDIR:-unset}
""".replace("__VITIS__", VITIS_SETTINGS)


def cmd_mulder() -> int:
    print("== mulder ==")
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", MULDER, "bash", "-s"],
        input=MULDER_PROBE, capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"  ! ssh {MULDER} failed (rc={r.returncode}): {r.stderr.strip()[:300]}")
        print("    check: ~/.ssh/config has Host mulder; key loaded; VPN/campus network")
        return 2
    f: dict[str, str] = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            f[k.strip()] = v.strip()

    worst = 0
    def flag(level: str, msg: str) -> None:
        nonlocal worst
        worst = max(worst, 2 if level == "ERROR" else 1)
        print(f"  {level:5s}  {msg}")

    print(f"  host {f.get('host')}  up {f.get('uptime_days')}d  load {f.get('load')}  "
          f"mem avail {f.get('mem_avail_gb')} GiB")
    print(f"  home (NFS) {f.get('home_pct')}% used, {f.get('home_free')} free   "
          f"root / {f.get('root_pct')}% used, {f.get('root_free')} free")
    print(f"  Vitis settings64.sh: {f.get('vitis_settings')}   "
          f"vitis procs: {f.get('vitis_procs')} total / {f.get('vitis_procs_mine')} mine")

    try:
        if int(f.get("root_pct", "0")) >= 98:
            flag("ERROR", "root / is full. Anything writing to /tmp or /var will fail; "
                 "export TMPDIR to a directory under $HOME before running Vitis.")
        elif int(f.get("root_pct", "0")) >= 90:
            flag("WARN", "root / nearly full; set TMPDIR under $HOME.")
        if int(f.get("home_pct", "0")) >= 97:
            flag("WARN", "shared NFS home is nearly full cluster-wide; check free GB "
                 "before shipping a large project.")
    except ValueError:
        flag("WARN", "could not parse disk figures")
    if f.get("vitis_settings") != "present":
        flag("ERROR", f"{VITIS_SETTINGS} not found - Vitis install moved?")
    if f.get("vitis_procs_mine", "0") == "0":
        print("  note   no synthesis of ours running right now")
    if f.get("tmpdir") == "unset":
        print("  note   TMPDIR unset in login shell (runner scripts must set it themselves)")

    print("\n(machine facts: .claude/skills/vitis-mulder; incidents: "
          ".claude/memory/cluster-inventory.md)")
    return worst


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[1] == "status":
        return cmd_status()
    if argv[1] == "mulder":
        return cmd_mulder()
    if argv[1] == "all":
        a = cmd_status()
        print()
        b = cmd_mulder()
        return max(a, b)
    if argv[1] == "lint":
        if len(argv) < 3:
            print("usage: nrp_doctor.py lint <job.yaml> [...]", file=sys.stderr)
            return 2
        return cmd_lint(argv[2:])
    print(f"unknown command {argv[1]!r}; try status | lint | mulder | all", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
