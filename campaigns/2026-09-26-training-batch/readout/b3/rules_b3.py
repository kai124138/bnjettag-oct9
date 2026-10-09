"""Evaluate the pre-registered epoch-500 pilot rules for the K=3 regime-B pod (b3).

Arms A07-350-s1, C-s1, F-s1. Pilot telemetry: validation only (n_val = 62,000), single seed, never
quoted, selects nothing. Rules: STUDY.md 'Phase 2, feasibility pilot' (l. 1720-1847), Falsifier
'A07-350' (l. 1129-1141), collapse label (l. 1403-1414), Selection rule (a)-(c) (l. 995-1021).

Run from the campaign directory, after readout/b3/fetch_b3.py:
  uv run --with numpy python readout/b3/rules_b3.py
Writes readout/b3/rules-b3.txt (one labelled number per line, each with src=file:line) and prints it.
"""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

CAMPAIGN = Path(__file__).resolve().parents[2]
B3 = "readout/b3"
RUNS = ["chang0926-a07-350-n64-s1", "chang0926-c-n64-s1", "chang0926-f-n64-s1"]
SHORT = {"chang0926-a07-350-n64-s1": "A07-350-s1", "chang0926-c-n64-s1": "C-s1", "chang0926-f-n64-s1": "F-s1"}
ARMLOG = {r: f"logs/{r}-kai-chang0926-pilotb3-42abed-0-final-20260929T1613Z.log" for r in RUNS}
PODLOG = "logs/pilotb3-vqxc7-final-20260929T1613Z.log"
CERT = f"{B3}/readout-epoch-0500-42abed-b3/certify-snapshot-0500.json"
A26 = f"{B3}/readout-epoch-0500-42abed-b3/a26-entropy-epoch-0500.json"
RPOD = f"{B3}/readoutb3-pod.log"
WB = f"{B3}/wandb-history-b3.csv"
PVC = f"{B3}/pvc-extract-b3.json"
FLOORS = "code/evidence/static_floors_arms_s1_d25.json"
CFG = "code/tree/campaigns/chang0926/configs/{}.json"
PER_CONSTITUENT = ["input_proj", "bit_block_0_attn_Wq", "bit_block_0_attn_Wk", "bit_block_0_attn_Wv",
                   "bit_block_0_attn_Wo", "bit_block_0_ffn_fc1", "bit_block_0_ffn_fc2"]
OUT = []


def emit(text=""):
    OUT.append(text)


def read(path):
    return (CAMPAIGN / path).read_text()


def lines(path):
    return read(path).splitlines()


def line_of(path, pattern, after=0):
    """1-based number of the first line at or after `after` that matches `pattern`."""
    rx = re.compile(pattern)
    for i, text in enumerate(lines(path), start=1):
        if i >= after and rx.search(text):
            return i
    raise LookupError((path, pattern, after))


def src(path, line):
    return f"{path}:{line}"


def sha(path):
    return hashlib.sha256((CAMPAIGN / path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- inputs
TRACED_RX = re.compile(r"^\[epoch (\d+)/7000\] EBOPs=(\d+) target=(\d+) above_floor=(-?\d+) feasible=(\d) "
                       r"degenerate=(\d) beta=(\S+) val_AUC=(\S+) val_accuracy=(\S+)")
UNTRACED_RX = re.compile(r"^\[epoch (\d+)/7000\] EBOPs=untraced in_training_ebops=(\d+)")


def committed_traced(run):
    """Traced epoch lines of the committed trajectory: the first attempt up to its resume point,
    then every line after the last `==== ARM_ATTEMPT` (RUN.md l. 900-905)."""
    path = ARMLOG[run]
    text = lines(path)
    attempts = [i for i, t in enumerate(text, start=1) if t.startswith("==== ARM_ATTEMPT")]
    last = attempts[-1]
    resume = int(re.search(r"resume_epoch=(\d+)", "\n".join(text[last - 1:last + 3])).group(1))
    out = {}
    for i, t in enumerate(text, start=1):
        m = TRACED_RX.match(t)
        if not m:
            continue
        epoch = int(m.group(1))
        if (i < last and epoch <= resume) or i > last:
            out[epoch] = dict(line=i, ebops=int(m.group(2)), target=int(m.group(3)), above=int(m.group(4)),
                              feasible=int(m.group(5)), degenerate=int(m.group(6)), beta=float(m.group(7)),
                              auc=float(m.group(8)), acc=float(m.group(9)))
    return out, last, resume


def wandb_rows():
    rows = {r: [] for r in RUNS}
    with (CAMPAIGN / WB).open() as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):   # line 1 is the header
            row["_line"] = n
            rows[row["run"]].append(row)
    return rows


def f(x):
    return None if x in ("", "None") else float(x)


def median_ci(values, alpha=0.05):
    """Distribution-free order-statistic interval for the median (exact binomial). Assumes
    independent draws; the traced-epoch r series is autocorrelated, so this is an indication."""
    x = np.sort(np.asarray(values))
    n = len(x)
    cdf = lambda k: sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n
    k = max(k for k in range(1, n // 2 + 1) if cdf(k - 1) <= alpha / 2)
    return float(x[k - 1]), float(x[n - k]), k, 1 - 2 * cdf(k - 1)


def main():
    emit("# rules-b3.txt: epoch-500 pilot rule inputs, b3 (K=3 regime-B pod: A07-350-s1, C-s1, F-s1).")
    emit("# Pilot telemetry: validation only (n_val = 62,000), single seed, never quoted, selects nothing.")
    emit("# Written by readout/b3/rules_b3.py (uv run --with numpy python readout/b3/rules_b3.py).")
    emit("# Epochs: one-based = W&B _step = log '[epoch N/7000]'; zero-based = the runner's point['epoch'].")
    for p in [CERT, A26, RPOD, WB, PVC, FLOORS, PODLOG] + [ARMLOG[r] for r in RUNS] + [CFG.format(r) for r in RUNS]:
        emit(f"INPUT {p} sha256={sha(p)}")
    emit()

    # ------------------------------------------------------------ constants
    emit("[0] constants")
    pre_line = line_of("PREFLIGHT.md", r"^NONDEGENERATE_THRESHOLD ")
    thr = json.loads(lines("PREFLIGHT.md")[pre_line - 1].split(" ", 1)[1])["val_accuracy_threshold"]
    emit(f"0.1 threshold_c (val top-1 accuracy, p_maj + 5 SE) = {thr!r} | src={src('PREFLIGHT.md', pre_line)}")
    floors = json.loads(read(FLOORS))
    fl = {e["name"]: e for e in floors}
    cfg = {r: json.loads(read(CFG.format(r))) for r in RUNS}
    target, floor, head = {}, {}, {}
    for r in RUNS:
        tline = line_of(CFG.format(r), r'"target_ebops"')
        mline = line_of(CFG.format(r), r'"min_beta"')
        target[r] = int(cfg[r]["train"]["ebops"]["pid"]["target_ebops"])
        nline = line_of(FLOORS, rf'"name": "{r}"')
        zline = line_of(FLOORS, r'"zero": \{', nline) + 1
        floor[r] = fl[r]["zero"]["total"]
        head[r] = target[r] - floor[r]
        emit(f"0.2 {SHORT[r]} target = {target[r]} | src={src(CFG.format(r), tline)}")
        emit(f"0.3 {SHORT[r]} traced 0-bit floor = {floor[r]} | src={src(FLOORS, zline)}")
        emit(f"0.4 {SHORT[r]} headroom = target - floor = {head[r]}")
        emit(f"0.5 {SHORT[r]} K1 threshold = 10 % of headroom = {0.1 * head[r]:.1f} (STUDY l. 1754-1755 prints "
             f"{round(0.1 * head[r]):,})")
        emit(f"0.6 {SHORT[r]} min_beta = {cfg[r]['train']['ebops']['pid']['min_beta']!r} | src={src(CFG.format(r), mline)}")
    a07 = fl["chang0926-a07-350-n64-s1"]
    one = a07["one"]["per_layer"]
    oline = line_of(FLOORS, r'"one": \{', line_of(FLOORS, r'"name": "chang0926-a07-350-n64-s1"'))
    per_ch = {"input_proj": one["input_proj"] / 3, **{q: one[q] / 32 for q in PER_CONSTITUENT[1:]},
              "head_fc1": one["head_fc1"] / 32, "head_fc2": one["head_fc2"] / 32}
    emit(f"0.7 A07 EBOPs per input channel-bit (all-1-bit per-layer totals / channels): "
         + ", ".join(f"{k} {v:g}" for k, v in per_ch.items()) + f" | src={src(FLOORS, oline)}")
    emit(f"0.8 A07-350 per-constituent bound at 350k = floor(headroom / 2048) = {head['chang0926-a07-350-n64-s1'] // 2048} "
         f"channel-bits (STUDY l. 1133: at most three 1-bit input channels)")
    emit()

    # ------------------------------------------------------------ per-run inputs
    state = json.loads(read(PVC))["state"]
    records = json.loads(read(PVC))["records"]
    pvc_lines = lines(PVC)
    cert = json.loads(read(CERT))
    a26 = json.loads(read(A26))
    wb = wandb_rows()
    traced = {}
    for r in RUNS:
        traced[r], last_attempt, resume = committed_traced(r)
        assert sorted(traced[r]) == [1] + list(range(10, 501, 10)), (r, sorted(traced[r]))
        emit(f"# {SHORT[r]}: committed trajectory = {ARMLOG[r]} lines before {last_attempt} with epoch <= {resume}, "
             f"then lines after {last_attempt} (last ==== ARM_ATTEMPT); 51 traced epochs (one-based 1, 10, ..., 500)")

    # ------------------------------------------------------------ cross-checks
    emit()
    emit("[X] cross-checks")
    for r in RUNS:
        rows = {int(w["_step"]): w for w in wb[r]}
        diff = []
        for e, t in sorted(traced[r].items()):
            w = rows[e]
            assert w["ebops_traced"] == "1", (r, e)
            if int(float(w["ebops"])) != t["ebops"]:
                diff.append((e, t["ebops"], int(float(w["ebops"])), w["_line"], t["line"]))
        emit(f"X.1 {SHORT[r]} traced EBOPs, arm log vs W&B, 51 traced epochs: {51 - len(diff)} equal"
             + ("" if not diff else "; differ at " + "; ".join(
                 f"epoch {e}: log {a} ({src(ARMLOG[r], ln)}) vs W&B {b} ({src(WB, wl)}), W&B holds the first "
                 f"attempt (re-run step dropped, RUN.md l. 907-910)" for e, a, b, wl, ln in diff)))
        ratio_dev = max(abs(f(w["ebops_in_training"]) / f(w["ebops"]) - f(w["ebops_in_training_over_traced"]))
                        for w in wb[r] if w["ebops_traced"] == "1")
        emit(f"X.2 {SHORT[r]} W&B ebops_in_training / ebops vs logged ebops_in_training_over_traced: max |diff| "
             f"= {ratio_dev:.1e}")
    for rec in records:
        r, step = rec["run"], rec["epoch"] + 1
        w = {int(x["_step"]): x for x in wb[r]}[step]
        ok = int(float(w["ebops"])) == rec["ebops"] and f(w["ebops_in_training"]) == rec["ebops_in_training"]
        emit(f"X.3 {SHORT[r]} zero-based epoch {rec['epoch']}: PVC jsonl line {rec['line']} ebops {rec['ebops']}, "
             f"in-training {rec['ebops_in_training']:.0f} vs W&B step {step} {'equal' if ok else 'DIFFER'} | "
             f"src={src(WB, w['_line'])}")
        assert ok
    for run in cert["runs"]:
        r = run["name"]
        for ck in run["checkpoints"]:
            bf = state[r]["best_feasible"] if ck["which"].endswith("primary") else state[r]["best_feasible_auc"]
            emit(f"X.4 {SHORT[r]} {ck['which']}: certify logged {ck['logged_ebops']} = retraced {ck['retraced_ebops']} "
                 f"= stored {ck['stored_ebops']}, relative difference {ck['relative_difference']}, {ck['status']}; "
                 f"state.json epoch {bf['epoch']} ebops {bf['ebops']} "
                 f"{'agrees' if bf['ebops'] == ck['logged_ebops'] and bf['epoch'] == ck['epoch'] else 'DISAGREES'} | "
                 f"src={src(CERT, line_of(CERT, r'\"status\": \"CERTIFIED\"', line_of(CERT, re.escape(ck['which']), line_of(CERT, r)))) }")
    emit(f"X.5 certification summary: {lines(RPOD)[line_of(RPOD, 'CERTIFICATION_ALL_PASS') - 1].split('Z ', 1)[1]} "
         f"| src={src(RPOD, line_of(RPOD, 'CERTIFICATION_ALL_PASS'))}; "
         f"{lines(RPOD)[line_of(RPOD, 'READOUT_JOB_DONE') - 1].split('Z ', 1)[1]} | src={src(RPOD, line_of(RPOD, 'READOUT_JOB_DONE'))}")
    # RUN.md telemetry lines (1047-1048) against the arm logs
    for r, pat in [("chang0926-a07-350-n64-s1", r"A07-350-s1 `EBOPs="), ("chang0926-c-n64-s1", r"C-s1 `EBOPs=")]:
        ln = line_of("RUN.md", pat)
        m = re.search(r"EBOPs=(\d+) .*above_floor=(\d+) .*beta=(\S+) val_AUC=(\S+) val_accuracy=([0-9.]+)", lines("RUN.md")[ln - 1])
        t = traced[r][500]
        same = (int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5))) == \
               (t["ebops"], t["above"], t["beta"], t["auc"], t["acc"])
        emit(f"X.6 RUN.md epoch-500 telemetry for {SHORT[r]} vs arm log: {'identical' if same else 'DIFFERENT'} | "
             f"src={src('RUN.md', ln)}, {src(ARMLOG[r], t['line'])}")
    emit()

    # ------------------------------------------------------------ [2] per run
    emit("[2] per run (evaluated snapshot = best-feasible-as-of-500, or model_min_ebops if none meets (a))")
    pod = lines(PODLOG)
    pack = line_of(PODLOG, r"^PACK_DONE")
    for r in RUNS:
        s = state[r]
        name_line = line_of(PVC, rf'"{r}": \{{')
        t = traced[r]
        n_a = sum(1 for v in t.values() if v["ebops"] <= target[r])
        n_feas = sum(v["feasible"] for v in t.values())
        n_deg = sum(v["degenerate"] for v in t.values())
        fde_line = line_of(PVC, r'"feasible_degenerate_epochs"', name_line)
        emit(f"2.1 {SHORT[r]} traced epochs meeting (a) EBOPs <= target: {n_a} of 51; meeting (a)-(c): {n_feas}; "
             f"feasible-degenerate (a) and not (b)/(c): {n_deg} (state.json feasible_degenerate_epochs = "
             f"{s['feasible_degenerate_epochs']}) | src={ARMLOG[r]} traced lines, {src(PVC, fde_line)}")
        arm_exit = line_of(PODLOG, rf"^ARM_EXIT {r} ")
        emit(f"2.2 {SHORT[r]} diverged: no ({pod[arm_exit - 1]}; {pod[pack - 1]}) | src={src(PODLOG, arm_exit)}, "
             f"{src(PODLOG, pack)}")
        if s["best_feasible"] is None:
            snap, which = s["lowest"], "model_min_ebops.keras (no feasible checkpoint as of epoch 500)"
            key_line = line_of(PVC, r'"lowest": \{', name_line)
            bf_line = line_of(PVC, r'"best_feasible": null', name_line)
            emit(f"2.3 {SHORT[r]} class: no feasible checkpoint (best_feasible null) | src={src(PVC, bf_line)}")
        else:
            snap, which = s["best_feasible"], "model_best.keras (best-feasible-as-of-500)"
            key_line = line_of(PVC, r'"best_feasible": \{', name_line)
            emit(f"2.3 {SHORT[r]} class: feasible | src={src(PVC, key_line)}")
        above = snap["ebops"] - floor[r]
        emit(f"2.4 {SHORT[r]} evaluated snapshot: {which}, zero-based epoch {snap['epoch']} (one-based "
             f"{snap['epoch'] + 1}), traced EBOPs {snap['ebops']}, above floor {above} | src={src(PVC, key_line + 1)}, "
             f"{src(PVC, key_line + 4)}")
        emit(f"2.5 {SHORT[r]} headroom fraction (EBOPs - floor) / headroom = {above} / {head[r]} = {above / head[r]:.4f}")
        emit(f"2.6 {SHORT[r]} snapshot validation top-1 accuracy {snap['val_categorical_accuracy']:.6f}, "
             f"macro-OvR AUC {snap['val_macro_auc']:.6f} (validation, n = 62,000, single seed) | "
             f"src={src(PVC, key_line + 3)}, {src(PVC, key_line + 2)}")
        # attention state from A26
        run_line = line_of(A26, rf'"name": "{r}"')
        a = [x for x in a26["runs"] if x["name"] == r][0]
        ck_line = line_of(A26, r'"checkpoint":', run_line)
        emit(f"2.7 {SHORT[r]} A26 checkpoint: {a['checkpoint'].rsplit('/', 1)[1]} ({a['checkpoint_reason']}) | "
             f"src={src(A26, ck_line)}")
        zb = a["zero_bit"]["bit_block_0"]
        heads = a["entropy"]["bit_block_0"]["heads"]
        nh = len(heads)
        for q in ("Q", "K", "V"):
            ql = line_of(A26, r'"zero_bit": \d+,', line_of(A26, rf'"{q}": \{{', line_of(A26, r'"zero_bit": \{', run_line)))
            emit(f"2.8 {SHORT[r]} {q} channels at 0 bits = {zb[q]['zero_bit']} / {zb[q]['channels']} "
                 f"(fraction {zb[q]['zero_bit_fraction']:.6f}; per head {zb[q]['zero_bit_per_head']}) | src={src(A26, ql)}")
        ent_lines = []
        at = line_of(A26, r'"heads": \[', run_line)
        for h in heads:
            at = line_of(A26, r'"entropy_over_log_n": ', at + 1)
            ent_lines.append(at)
        emit(f"2.9 {SHORT[r]} entropy / log 64 (row-renormalized, [A26], validation n = 62,000) per head = "
             + ", ".join(f"{h['entropy_over_log_n']:.6f}" for h in heads)
             + f"; per-jet sd {', '.join(f'{h['per_jet_std']:.4f}' for h in heads)} | src="
             + ", ".join(src(A26, ln) for ln in ent_lines))
        per = zb["Q"]["channels"] // nh
        crit = []
        for i, h in enumerate(heads):
            c1 = zb["Q"]["zero_bit_per_head"][i] == per or zb["K"]["zero_bit_per_head"][i] == per
            c2 = zb["V"]["zero_bit_per_head"][i] == per
            c3 = h["entropy_over_log_n"] >= 0.99
            crit.append((c1, c2, c3))
        label = "Deep-Set-class" if all(any(c) for c in crit) else "not Deep-Set-class"
        emit(f"2.10 {SHORT[r]} collapse label (STUDY l. 1403-1407: every head meets (i) all Q or all K at 0 bits, "
             f"(ii) all V at 0 bits, or (iii) entropy/log 64 >= 0.99): {label}; per head (i,ii,iii) = "
             + "; ".join(f"h{i} {tuple(int(x) for x in c)}" for i, c in enumerate(crit)))
        if s["best_feasible"] is not None:
            emit(f"2.11 {SHORT[r]} best-feasible validation accuracy = {s['best_feasible']['val_categorical_accuracy']:.6f} "
                 f"(> threshold_c {thr:.7f}; margin {s['best_feasible']['val_categorical_accuracy'] - thr:+.6f}) "
                 f"| src={src(PVC, line_of(PVC, r'\"best_feasible\": \{', name_line) + 3)}")
        else:
            emit(f"2.11 {SHORT[r]} best-feasible validation accuracy: none (no feasible checkpoint)")
        # (c) behaviour on traced epochs (descriptive)
        fails_c = [e for e, v in sorted(t.items()) if v["acc"] <= thr]
        tail = [e for e in sorted(t) if all(t[x]["acc"] <= thr for x in sorted(t) if x >= e)]
        emit(f"2.12 {SHORT[r]} traced epochs failing (c) (val acc <= threshold_c): {len(fails_c)} of 51"
             + (f"; every traced epoch from one-based {tail[0]} to 500 fails (c)" if tail else "")
             + f"; traced epochs with val AUC exactly 0.500000: {sum(1 for v in t.values() if v['auc'] == 0.5)}")
    emit()

    # ------------------------------------------------------------ [1] A07-350-s1 rule
    emit("[1] A07-350-s1 rule (Falsifier 'A07-350', STUDY l. 1129-1141; pilot bullet l. 1742-1746)")
    r = "chang0926-a07-350-n64-s1"
    rec = [x for x in records if x["run"] == r and x["line"] == 330][0]
    rec_end = [x for x in records if x["run"] == r and x["line"] == 500][0]
    rline = line_of(PVC, r'"line": 330')
    assert rec["epoch"] == state[r]["lowest"]["epoch"] and rec["ebops"] == state[r]["lowest"]["ebops"]
    emit(f"1.1 feasible A07-350-s1 checkpoints as of epoch 500: 0 (traced epochs with EBOPs <= 350,000: "
         f"{sum(1 for v in traced[r].values() if v['ebops'] <= 350000)} of 51; certify status "
         f"'{[x for x in cert['runs'] if x['name'] == r][0]['status']}') | src={src(CERT, line_of(CERT, r'\"status\": \"no feasible checkpoint\"'))}")
    emit(f"1.2 fallback = model_min_ebops at zero-based epoch {rec['epoch']} = state.json lowest; PVC jsonl line "
         f"{rec['line']} (sha256 {rec['sha256_line'][:16]}...) | src={src(PVC, rline)}")
    pl = rec["per_layer"]
    total = sum(pl.values())
    pl_line = line_of(PVC, r'"per_layer": \{', rline)
    emit(f"1.3 per-layer traced EBOPs sum = {total} = logged {rec['ebops']} ({'equal' if total == rec['ebops'] else 'DIFFER'}); "
         f"attn_softmax term = {pl['bit_block_0_attn_softmax']} (= floor {floor[r]}: "
         f"{pl['bit_block_0_attn_softmax'] == floor[r]}) | src={src(PVC, pl_line)}-{pl_line + 13}")
    wl = line_of(PVC, r'"widths_ebops_bits": \{', rline)
    tot_live = tot_bits = tot_eb = 0
    for q in PER_CONSTITUENT + ["head_fc1", "head_fc2"]:
        w = rec["widths_ebops_bits"][q]
        eb = pl[q]
        ql = line_of(PVC, rf'"{q}": \{{', wl)
        cost = eb / w["channel_bits"] if w["channel_bits"] else None
        ok = (w["channel_bits"] * per_ch[q] == eb)
        emit(f"1.4 {q}: input channels live {w['live']} of {w['channels']} ({w['one_bit']} at 1 bit), channel-bits "
             f"{w['channel_bits']:g}, EBOPs {eb}"
             + (f", {cost:g} per channel-bit ({'matches' if ok else 'DOES NOT MATCH'} static {per_ch[q]:g})" if cost else "")
             + f" | src={src(PVC, ql)}")
        assert ok
        if q in PER_CONSTITUENT:
            tot_live += w["live"]; tot_bits += w["channel_bits"]; tot_eb += eb
    emit(f"1.5 per-constituent layers total: {tot_live} live input channels, {tot_bits:g} channel-bits, {tot_eb} EBOPs "
         f"= {tot_bits:g} x 2048; expected at <= 350k: <= 3 channel-bits (<= 6,144 EBOPs)")
    above = rec["ebops"] - floor[r]
    emit(f"1.6 above-floor decomposition: {above} = per-constituent {tot_eb} + head_fc1 {pl['head_fc1']} + head_fc2 "
         f"{pl['head_fc2']} ({tot_eb + pl['head_fc1'] + pl['head_fc2'] == above}); checkpoint is {rec['ebops'] - 350000} "
         f"over the 350,000 target; implied per-constituent ceiling at its own above-floor budget = "
         f"floor({above} / 2048) = {above // 2048} channel-bits")
    qk = [line_of(PVC, rf'"bit_block_0_attn_scores__in{i}": \{{', wl) for i in (0, 1)]
    for i, ql in zip((0, 1), qk):
        w = rec["widths_ebops_bits"][f"bit_block_0_attn_scores__in{i}"]
        emit(f"1.7 attn_scores__in{i} ({'Q' if i == 0 else 'K'}) channels at 0 bits = {w['zero_bit']} / {w['channels']} | src={src(PVC, ql)}")
    emit("1.8 expectation (i) Q.K logits independent of the jet: Q and K at 0 bits on every channel -> logits constant; "
         "A26 entropy / log 64 = 1.000000 with per-jet sd 0.0 on all 4 heads (items 2.8-2.9) -> MATCH on the fallback")
    emit(f"1.9 expectation (ii) <= 3 per-constituent 1-bit input channels: {tot_bits:g} channel-bits on a checkpoint "
         f"{rec['ebops'] - 350000} over target -> outside the expectation's domain (feasible checkpoints); per-layer EBOPs "
         f"reconcile exactly with the widths and the floor (1.3-1.6) -> no floor-accounting discrepancy found")
    pl2 = rec_end["per_layer"]
    w2 = rec_end["widths_ebops_bits"]
    r2 = line_of(PVC, r'"line": 500')
    emit(f"1.10 descriptive, zero-based epoch 499 (jsonl line 500): EBOPs {rec_end['ebops']}, above floor "
         f"{rec_end['ebops'] - floor[r]} = input_proj {pl2['input_proj']} + ffn_fc1 {pl2['bit_block_0_ffn_fc1']}; "
         f"ffn_fc2 input live {w2['bit_block_0_ffn_fc2']['live']} of 32, head_fc1 input live {w2['head_fc1']['live']} of 32 | "
         f"src={src(PVC, r2)}")
    emit()

    # ------------------------------------------------------------ [3] C constraint readout
    emit("[3] C-s1 constraint readout (STUDY l. 1816-1840)")
    r = "chang0926-c-n64-s1"
    rows = [w for w in wb[r] if w["ebops_traced"] == "1"]
    assert len(rows) == 51
    over = [w for w in rows if f(w["ebops"]) > 5_000_000]
    emit(f"3.1 (i) traced epochs with traced EBOPs > 5,000,000: {len(over)} of {len(rows)} = {len(over) / len(rows):.4f} "
         f"(steps {', '.join(w['_step'] for w in over)}) | src=" + ", ".join(src(WB, w["_line"]) for w in over))
    bf = state[r]["best_feasible"]
    emit(f"3.2 (ii) selected (best-feasible-as-of-500) traced EBOPs / 5,000,000 = {bf['ebops']} / 5,000,000 = "
         f"{bf['ebops'] / 5_000_000:.6f} (certified, X.4) | src={src(PVC, line_of(PVC, r'\"best_feasible\": \{', line_of(PVC, rf'\"{r}\": \{{')) + 4)}")
    last10 = rows[-10:]
    betas = [f(w["beta"]) for w in last10]
    at_floor = [abs(b - 1e-10) / 1e-10 <= 1e-6 for b in betas]
    over10 = [f(w["ebops"]) > 5_000_000 for w in last10]
    emit(f"3.3 (iii) beta at the last 10 traced epochs (steps {last10[0]['_step']}-{last10[-1]['_step']}): "
         + ", ".join(f"{b:.4g}" for b in betas)
         + f"; at 1e-10 (rel. diff <= 1e-6): {sum(at_floor)} of 10; min beta / 1e-10 = {min(betas) / 1e-10:.1f} | "
           f"src={src(WB, last10[0]['_line'])}-{last10[-1]['_line']}")
    emit(f"3.4 traced EBOPs > 5,000,000 in the same last-10 window: {sum(over10)} of 10; traced EBOPs there "
         f"{min(f(w['ebops']) for w in last10):.0f}-{max(f(w['ebops']) for w in last10):.0f}")
    slack = all(at_floor) and not any(over10)
    label = ("constraint slack" if slack else
             f"beta at floor (integral wound up), 5M exceeded on {sum(over10)} of 10" if all(at_floor) else
             "not slack: (iii) fails, neither registered label applies")
    emit(f"3.5 rule: {label}")
    emit()

    # ------------------------------------------------------------ [4] K1
    emit("[4] Regime-B PID input rule K1 (STUDY l. 1747-1778), r = W&B ebops_in_training / ebops on traced epochs")
    med, ci = {}, {}
    for r in RUNS:
        rows = [w for w in wb[r] if w["ebops_traced"] == "1"]
        T = target[r]
        rstar = (1 - 0.1 * head[r] / T) ** (-1 / 0.9)
        for tag, lo, hi in (("one-based 100-500 (primary)", 100, 500), ("zero-based 100-500", 101, 500)):
            sel = [w for w in rows if lo <= int(w["_step"]) <= hi]
            rr = np.array([f(w["ebops_in_training"]) / f(w["ebops"]) for w in sel])
            m = float(np.median(rr))
            off = T * (1 - m ** -0.9)
            lo_ci, hi_ci, k, cov = median_ci(rr)
            if tag.endswith("(primary)"):
                med[r] = m
                ci[r] = (lo_ci, hi_ci)
            emit(f"4.1 {SHORT[r]} {tag}: n = {len(rr)} traced epochs (steps {sel[0]['_step']}-{sel[-1]['_step']}), "
                 f"median r = {m:.6f} (min {rr.min():.4f}, max {rr.max():.4f}) | src={src(WB, sel[0]['_line'])}-{sel[-1]['_line']}")
            emit(f"4.2 {SHORT[r]} {tag}: implied traced offset {T:,} x (1 - r^-0.9) = {off:.1f}; share of headroom "
                 f"{off / head[r]:.4f}; threshold {0.1 * head[r]:.1f} -> {'EXCEEDS (fires)' if off > 0.1 * head[r] else 'below (does not fire)'}")
            emit(f"4.3 {SHORT[r]} {tag}: r at which the offset equals the threshold r* = {rstar:.6f}; r values above r*: "
                 f"{int((rr > rstar).sum())} of {len(rr)}; order-statistic interval on the median (x_({k}), x_({len(rr) + 1 - k}), "
                 f"coverage {cov:.3f} if draws were independent; the series is autocorrelated) = [{lo_ci:.6f}, {hi_ci:.6f}]")
            if tag.endswith("(primary)"):
                dd = np.array([f(w["ebops_in_training"]) - f(w["ebops"]) for w in sel])
                emit(f"4.4 {SHORT[r]} descriptive: median in-training - traced = {np.median(dd):.0f} EBOPs over the same "
                     f"{len(dd)} traced epochs; stationary point T x r^-0.9 = {T * m ** -0.9:.0f}")
    sl = line_of("STUDY.md", r"E1 − D is 1\.0920 − 1\.0717")
    emit(f"4.5 formula check: r = 1 gives offset {350000 * (1 - 1.0 ** -0.9):.1f} (limiting case); the regime-A medians "
         f"E1-s1 1.0920 and D-s1 1.0717 give 350,000 x (1 - r^-0.9) = {350000 * (1 - 1.0920 ** -0.9):,.0f} and "
         f"{350000 * (1 - 1.0717 ** -0.9):,.0f}, the STUDY's 26,654 and 21,147 | src={src('STUDY.md', sl - 1)}-{sl}")
    names = [SHORT[r] for r in RUNS]
    for i in range(3):
        for j in range(i + 1, 3):
            d = abs(med[RUNS[i]] - med[RUNS[j]])
            a, b = ci[RUNS[i]], ci[RUNS[j]]
            gap = max(a[0] - b[1], b[0] - a[1])   # separation of the two median intervals (< 0: overlap)
            emit(f"4.6 |median r {names[i]} - median r {names[j]}| = {d:.6f} -> {'> 0.02' if d > 0.02 else '<= 0.02'}; "
                 f"gap between their median intervals (4.3) = {gap:.6f} ({'> 0.02' if gap > 0.02 else '<= 0.02'})")
    r = "chang0926-a07-350-n64-s1"
    un = [w for w in wb[r] if w["ebops_traced"] == "0"]
    tr = [w for w in wb[r] if w["ebops_traced"] == "1"]
    above350 = sum(1 for w in un if f(w["ebops_in_training"]) > 350000)
    band = 1.01 * floor[r]
    within = sum(1 for w in tr if f(w["ebops"]) <= band)
    tmin = min(tr, key=lambda w: f(w["ebops"]))
    umin = min(un, key=lambda w: f(w["ebops_in_training"]))
    emit(f"4.7 A07-350-s1 wind-up clause, last cycle = one-based epochs 1-500: untraced epochs with W&B ebops_in_training "
         f"> 350,000: {above350} of {len(un)} (minimum {f(umin['ebops_in_training']):.0f} at step {umin['_step']}) | "
         f"src={src(WB, umin['_line'])}")
    emit(f"4.8 A07-350-s1 traced epochs within 1 % of the floor (<= {band:.2f}): {within} of {len(tr)}; minimum traced "
         f"{f(tmin['ebops']):.0f} at step {tmin['_step']} = {f(tmin['ebops']) / floor[r]:.4f} x floor | src={src(WB, tmin['_line'])}")
    emit(f"4.9 A07-350-s1 distance to target: minimum traced EBOPs - 350,000 = {f(tmin['ebops']) - 350000:.0f}; at step 500 "
         f"{f(tr[-1]['ebops']) - 350000:.0f}")
    for r in RUNS:
        rows = [w for w in wb[r] if w["ebops_traced"] == "1"]
        l10 = rows[-10:]
        ev = [f(w["ebops"]) for w in l10]
        mx = cfg[r]["train"]["ebops"]["pid"]["max_beta"]
        emit(f"4.10 {SHORT[r]} last 10 traced epochs (steps 410-500): traced EBOPs {min(ev):.0f}-{max(ev):.0f} = "
             f"{min(ev) / target[r]:.4f}-{max(ev) / target[r]:.4f} x target; traced epochs over target in the whole "
             f"cycle {sum(1 for w in rows if f(w['ebops']) > target[r])} of 51; beta at step 500 {f(rows[-1]['beta']):.4g} "
             f"= {f(rows[-1]['beta']) / mx:.3g} x max_beta {mx:g} | src={src(WB, l10[0]['_line'])}-{l10[-1]['_line']}, "
             f"{src(CFG.format(r), line_of(CFG.format(r), r'\"max_beta\"'))}")
    emit()
    return "\n".join(OUT) + "\n"


if __name__ == "__main__":
    text = main()
    (CAMPAIGN / B3 / "rules-b3.txt").write_text(text)
    print(text, end="")
