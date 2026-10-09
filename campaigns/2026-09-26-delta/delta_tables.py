import json, sys
D = sys.argv[1] if len(sys.argv) > 1 else "."
O = sys.argv[2] if len(sys.argv) > 2 else D
A = json.load(open(f"{D}/delta.json"))
E = A["entries"]
def fmt_t(ts): return ", ".join({350000:"350k",5000000:"5M",1400000:"1.4M"}[t] for t in ts)
def delta(e):
    parts = []
    for k, v in e["config_delta"].items():
        vv = json.dumps(v, separators=(",", ":")) if not isinstance(v, str) else v
        parts.append(f"`{k}={vv}`")
    return "; ".join(parts) if parts else "—"
def cc(e): return ", ".join(f"`{p}`" for p in e["code_changes"]) or "—"
def num(v): return "n/a" if v is None else f"{v:,}"
def fl(e):
    f = e["floor_derived"]; h = f["headroom_by_target"].get("350000")
    if f["floor0"] is None: return "trace"
    s = f"{num(f['floor0'])} / {num(f['floor1_alive'])}"
    if e.get("floor_traced"): s += " (= trace)"
    if isinstance(h, float): s += f"; h={h:.3f}"
    oe = f.get("on_E")
    if oe: s += "; 350k on E: h=" + (f"{oe['headroom_350000']:.3f}" if isinstance(oe["headroom_350000"], float) else "n/a")
    return s
out = []
out.append("| ID | name | fam. | cards | mech. | delta from the base arm (`base[target]`) | code tier / patches | tried | targets (screen → confirm) | H | pairing | prediction | mechanism diagnostic | floor0 / floor1 (derived), h at 350k; 350k on E | note |")
out.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for e in E:
    if e["tier"] not in ("single", "baseline"): continue
    out.append(f"| {e['id']} | {e['name']} | {e['family']} | {', '.join(e['cards'])} | {', '.join(e['mechanisms'])} | {delta(e)} | {e['code_tier']}: {cc(e)} | {e['tried']} | {fmt_t(e['targets'])} → {fmt_t(e['targets_confirm'])} | {e['horizon_screen_epochs']} | {e['pairing']} | {e['prediction']} | {e['mechanism_diagnostic']} | {fl(e)} | {e['note'] or '—'} |")
open(f"{O}/singles.md","w").write("\n".join(out)+"\n")
out = []
out.append("| ID | package | fam. | = components | decomposition ladder | extra delta | code tier | targets (screen → confirm) | H | pairing | prediction | diagnostic | floor0 / floor1 (derived), h at 350k; 350k on E |")
out.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for e in E:
    if not (e["tier"] in ("package","factorial-cell")): continue
    comp = " + ".join(e["combo_of"]) or "—"
    # extra delta = keys not coming straight from components
    ed = "; ".join(f"`{k}={json.dumps(v, separators=(',', ':'))}`" for k, v in e["extra_delta"].items())
    extra = "; ".join(x for x in [ed, e["note"]] if x) or "—"
    out.append(f"| {e['id']} | {e['name']} | {e['family']} | {comp} | {', '.join(e['ladder'])} | {extra} | {e['code_tier']} | {fmt_t(e['targets'])} → {fmt_t(e['targets_confirm'])} | {e['horizon_screen_epochs']} | {e['pairing']} | {e['prediction']} | {e['mechanism_diagnostic']} | {fl(e)} |")
open(f"{O}/combos.md","w").write("\n".join(out)+"\n")
out = ["| architecture (entries) | 0-bit floor, derived | 1-bit-alive floor, derived | traced (0-bit / 1-bit-alive) | h at 350k | class at 350k |",
       "| --- | ---: | ---: | --- | ---: | --- |"]
for r in A["architecture_floors"]:
    tr = f"{num(r['floor0_traced'])} / {num(r['floor1_alive_traced'])}" if r["floor0_traced"] is not None else "–"
    hh = r["headroom_350000"]; hs = f"{hh:.3f}" if isinstance(hh, float) else "–"
    cls = "`STATIC_INFEASIBLE`" if r["class_350000"] == "STATIC_INFEASIBLE" else r["class_350000"]
    out.append(f"| {r['architecture']} | {num(r['floor0_derived'])} | {num(r['floor1_alive_derived'])} | {tr} | {hs} | {cls} |")
open(f"{O}/floors.md","w").write("\n".join(out)+"\n")
print(len(open(f"{O}/singles.md").read().splitlines()), len(open(f"{O}/combos.md").read().splitlines()), len(out))
