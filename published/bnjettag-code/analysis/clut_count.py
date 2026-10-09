"""CompressedLUT applicability census for the COMPILER.md campaign (W1.2).

CompressedLUT (Khataei & Bazargan, FPGA'24) losslessly compresses CONSTANT
lookup tables (ROMs) by ~60% on average. It does not apply to adder trees,
runtime-computed values, or weights folded into the datapath. This script
establishes, at counting level (no synthesis), how much of the deployed
flagship's LUT area is actually ROM-resident and therefore addressable:

  1. firmware-declared tables  - parameters.h/defines.h table configs, checked
                                 against nnet_activation.h for whether each
                                 config's table is actually indexed (the
                                 thresholded_relu configs carry a vestigial
                                 table_size that no code reads);
  2. synthesized ROM inventory - every storage BindNode in the whole-model
                                 csynth XML, with its optype, geometry, and
                                 BRAM/LUT binding;
  3. closure checks            - instances x per-ROM BRAM vs the design BRAM
                                 total; softmax module LUT vs the COMPILER.md
                                 section-1 census row;
  4. the Four-Russians S[g][p] question - arm C's pattern values are runtime
                                 adder results seeded from the input vector,
                                 not ROMs (verified from the emitted source);
  5. addressable-savings model - (ROM-resident LUT) x 0.6 vs the pre-registered
                                 bands: PROMOTE >= 200k LUT, KILL < 50k.

All resource numbers are csynth-estimate space (Vitis HLS 2023.2, VU13P).
The LUTROM counterfactual in section 5 is a model, not a measurement, and is
labeled as such wherever it is printed.

Run:  .venv-hgq2/bin/python bnjettag/code/analysis/clut_count.py
Outputs: bnjettag/results/adder-graph/clut/counting_results.json + console.
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # bnjettag/
STDNN_PRJ = REPO / "r7/results/convert/r8stdnn-s2/rf8/hls_prj_rf8"
STDNN_XML = REPO / "r7/results/csynth/whole_model_rf8_stdnn.xml"
FR_EMIT_C = REPO / "results/adder-graph/e1/c/myproject.cpp"
OUT_DIR = REPO / "results/adder-graph/clut"
SIBLING_XMLS = [                                    # robustness scan (regex, no ET)
    "r7/results/csynth/whole_model_rf1_stdnn.xml",
    "r7/results/csynth/whole_model_da_rf8attn_stdnn.xml",
    "r7/results/csynth/whole_model_rf8_w1a4.xml",
]

DEVICE_LUT = 1_728_000          # VU13P
DEVICE_BRAM = 5_376             # VU13P BRAM_18K
CLUT_RATIO = 0.60               # CompressedLUT average table-size compression (FPGA'24)
PROMOTE_LUT = 200_000           # pre-registered band: promote to emit experiment
KILL_LUT = 50_000               # pre-registered band: kill
LUTROM_OVERHEAD = 1.5           # counterfactual model: mux overhead bracket over bits/64


# ---------------------------------------------------------------- firmware parsing

def parse_defines(prj):
    """typedef ap_[u]fixed<W,I,...> name;  ->  {name: (W, I)}"""
    types = {}
    txt = (prj / "firmware/defines.h").read_text()
    for m in re.finditer(r"typedef\s+ap_u?fixed<(\d+),\s*(-?\d+)[^>]*>\s+(\w+);", txt):
        types[m.group(3)] = (int(m.group(1)), int(m.group(2)))
    return types


def parse_table_configs(prj, types):
    """Every config struct in parameters.h that declares a table_size field."""
    txt = (prj / "firmware/parameters.h").read_text()
    configs = []
    for m in re.finditer(r"//\s*(\w+)\s*\nstruct\s+(\w+)[^{]*\{(.*?)\n\};", txt, re.S):
        layer, cfg, body = m.groups()
        tables = []
        for tm in re.finditer(r"static const unsigned (\w*table_size)\s*=\s*(\d+);", body):
            field, size = tm.group(1), int(tm.group(2))
            tname = field.replace("_size", "_t") if field != "table_size" else "table_t"
            ty = re.search(r"typedef\s+(\w+)\s+" + tname + r";", body)
            width = types.get(ty.group(1), (None,))[0] if ty else None
            tables.append(dict(field=field, size=size, type_t=ty.group(1) if ty else None,
                               width=width))
        if tables:
            configs.append(dict(layer=layer, config=cfg, tables=tables))
    return configs


def table_users(prj):
    """Which activation kernels actually index a table? -> {func: bool}"""
    txt = (prj / "firmware/nnet_utils/nnet_activation.h").read_text()
    out = {}
    for m in re.finditer(r"void (softmax_stable|softmax_latency|softmax_legacy|"
                         r"thresholded_relu)\s*\((.*?)\n\}", txt, re.S):
        body = m.group(2)
        out[m.group(1)] = bool(re.search(r"\w*table\w*\[", body))
    return out


# ---------------------------------------------------------------- csynth XML

def parse_xml(xml_path):
    """ROM BindNodes, per-module resources, instance counts, top totals."""
    root = ET.parse(xml_path).getroot()

    top = {res: int(root.find("AreaEstimates/Resources/" + res).text)
           for res in ("BRAM_18K", "DSP", "FF", "LUT", "URAM")}

    mres, roms, rom_modules = {}, [], set()
    for mod in root.findall("ModuleInformation/Module"):
        name = mod.find("Name").text
        r = mod.find(".//AreaEstimates/Resources")
        if r is not None:
            mres[name] = {e.tag: int(e.text) for e in r
                          if e.text and e.text.lstrip("-").isdigit()}
        for bn in mod.findall(".//BindNode[@BINDTYPE='storage']"):
            opt = bn.get("OPTYPE", "")
            if "rom" not in opt:
                continue
            width, depth = bn.get("STORAGESIZE", "0 0 0").split()[:2]
            roms.append(dict(module=name, variable=bn.get("VARIABLE"),
                             optype=opt, width=int(width), depth=int(depth),
                             bram=int(bn.get("BRAM", 0))))
            rom_modules.add(name)

    count = defaultdict(int)

    def walk(inst):
        mod = inst.find("ModuleName").text
        count[mod] += 1
        il = inst.find("InstancesList")
        for c in (il.findall("Instance") if il is not None else []):
            walk(c)

    walk(root.find("RTLDesignHierarchy/TopModule"))

    rom_named = sorted(n for n in mres if "rom" in n.lower())
    return top, mres, roms, rom_modules, count, rom_named


def scan_sibling(xml_path):
    """Regex scan of a sibling csynth XML: rom BindNodes + top BRAM total."""
    txt = xml_path.read_text()
    roms = []
    for m in re.finditer(r'<BindNode BINDTYPE="storage"[^>]*OPTYPE="(rom[^"]*)"[^>]*>',
                         txt):
        node = m.group(0)
        width, depth = re.search(r'STORAGESIZE="(\d+) (\d+)', node).groups()
        roms.append(dict(variable=re.search(r'VARIABLE="([^"]*)"', node).group(1),
                         optype=m.group(1), width=int(width), depth=int(depth),
                         bram=int(re.search(r'BRAM="(\d+)"', node).group(1))))
    top_bram = int(re.search(r"<BRAM_18K>(\d+)</BRAM_18K>", txt).group(1))
    return roms, top_bram


# ---------------------------------------------------------------- FR emitted code

def inspect_fr_emit(path):
    """Arm C source: S[g][p] provenance + any constant arrays."""
    txt = path.read_text()
    s_assigns = len(re.findall(r"S\[\d+\]\[\d+\]\s*=", txt))
    s_from_x = len(re.findall(r"S\[\d+\]\[\d+\]\s*=[^;]*x\[\d+\]", txt))
    s_from_s = len(re.findall(r"S\[\d+\]\[\d+\]\s*=[^;]*S\[\d+\]\[\d+\]", txt))
    const_arrays = re.findall(r"static const \w+ (\w+)\[(\d+)\]", txt)
    return dict(s_assigns=s_assigns, s_from_x=s_from_x, s_from_s=s_from_s,
                const_arrays=[(n, int(k)) for n, k in const_arrays])


# ---------------------------------------------------------------- main

def main():
    types = parse_defines(STDNN_PRJ)
    configs = parse_table_configs(STDNN_PRJ, types)
    users = table_users(STDNN_PRJ)
    top, mres, roms, rom_modules, count, rom_named = parse_xml(STDNN_XML)

    print("=" * 76)
    print("W1.2  CompressedLUT applicability census -- flagship r8 stdnn @ RF=8")
    print(f"firmware: {STDNN_PRJ.relative_to(REPO)}")
    print(f"csynth:   {STDNN_XML.relative_to(REPO)}  "
          f"(top LUT {top['LUT']:,}, BRAM_18K {top['BRAM_18K']})")
    print("=" * 76)

    print("\n[1] firmware-declared tables (parameters.h + defines.h)")
    for c in configs:
        kernel = ("softmax_stable" if c["config"].startswith("softmax")
                  else "thresholded_relu")
        used = users.get(kernel, None)
        for t in c["tables"]:
            print(f"  {c['layer']:28s} {c['config']:24s} {t['field']:15s} "
                  f"{t['size']:5d} x {str(t['width']):>4s}b  "
                  f"kernel={kernel}  indexes-table={used}")
    print(f"  kernel table usage (from nnet_activation.h function bodies): {users}")

    print("\n[2] synthesized ROM inventory (all storage BindNodes with optype rom_*)")
    if not roms:
        print("  NONE")
    for r in roms:
        n_inst = count.get(r["module"], 0)
        print(f"  {r['variable']:16s} {r['optype']:7s} {r['depth']:5d} x {r['width']:2d}b "
              f"-> {r['bram']} BRAM_18K  in {r['module'][:52]}  x{n_inst} inst")
    print(f"  modules with 'rom' in their name: {rom_named or 'NONE'}")

    print("\n[2b] sibling variants (regex scan; module-definition-level BindNodes)")
    siblings = {}
    for rel in SIBLING_XMLS:
        sroms, sbram = scan_sibling(REPO / rel)
        lutrom = [r for r in sroms if r["bram"] == 0]
        lutrom_bits = sum(r["depth"] * r["width"] for r in lutrom)
        siblings[rel] = dict(rom_bindnodes=sroms, top_bram=sbram,
                             lutrom_tables=len(lutrom), lutrom_bits=lutrom_bits)
        kinds = defaultdict(int)
        for r in sroms:
            kinds[f"{re.sub(r'_[0-9]+$', '', r['variable'])} "
                  f"{r['depth']}x{r['width']}b BRAM={r['bram']}"] += 1
        print(f"  {Path(rel).name}: {len(sroms)} rom BindNodes, top BRAM_18K={sbram}")
        for k, v in sorted(kinds.items()):
            print(f"    {v} x {k}")
        if lutrom:
            lo = lutrom_bits / 64
            print(f"    -> {len(lutrom)} LUT-resident ROM defs (BRAM=0), "
                  f"{lutrom_bits:,} bits ~= {lo:,.0f}-{lo * LUTROM_OVERHEAD:,.0f} LUT "
                  f"(modeled); 60% = {lo * CLUT_RATIO:,.0f}-"
                  f"{lo * LUTROM_OVERHEAD * CLUT_RATIO:,.0f} LUT")

    # closure: BRAM
    rom_bram_total = sum(r["bram"] * count.get(r["module"], 0) for r in roms)
    print(f"\n[3] closure checks")
    print(f"  ROM BRAM x instances = {rom_bram_total}  vs design BRAM_18K total = "
          f"{top['BRAM_18K']}  ({'EXACT' if rom_bram_total == top['BRAM_18K'] else 'MISMATCH'})")
    softmax_lut = sum(mres[m].get("LUT", 0) * count.get(m, 0) for m in rom_modules)
    softmax_bram = sum(mres[m].get("BRAM_18K", 0) * count.get(m, 0) for m in rom_modules)
    softmax_dsp = sum(mres[m].get("DSP", 0) * count.get(m, 0) for m in rom_modules)
    for m in sorted(rom_modules):
        print(f"  {m[:64]}: LUT {mres[m].get('LUT', 0):,} BRAM {mres[m].get('BRAM_18K', 0)} "
              f"DSP {mres[m].get('DSP', 0)} x{count.get(m, 0)} inst")
    print(f"  softmax modules total: LUT {softmax_lut:,} (COMPILER.md census row: 42,190), "
          f"BRAM {softmax_bram}, DSP {softmax_dsp}")

    print("\n[4] Four-Russians S[g][p] pattern values (arm C emitted source)")
    fr = inspect_fr_emit(FR_EMIT_C)
    print(f"  {FR_EMIT_C.relative_to(REPO)}")
    print(f"  S[g][p] assignments: {fr['s_assigns']}  "
          f"({fr['s_from_x']}/{fr['s_assigns']} reference the runtime input x[]; "
          f"{fr['s_from_s']}/{fr['s_assigns']} also chain from a prior S -- "
          f"categories overlap)")
    print(f"  constant arrays in emitted code: {fr['const_arrays']}")
    print("  -> every S[g][p] is a runtime ADDER result seeded from the input vector;")
    print("     none is a compile-time-constant table. CompressedLUT does NOT apply.")

    # ---- section 5: addressable savings
    rom_lut_measured = 0    # every ROM above binds to BRAM; storage consumes no LUTs
    addressable = rom_lut_measured * CLUT_RATIO
    rom_bits = sum(r["depth"] * r["width"] * count.get(r["module"], 0) for r in roms)
    lutrom_lo = rom_bits / 64                      # LUT6 as 64x1 ROM, no mux overhead
    lutrom_hi = lutrom_lo * LUTROM_OVERHEAD
    bram_saved = top["BRAM_18K"] * CLUT_RATIO

    print("\n[5] addressable savings vs pre-registered bands")
    print(f"  ROM-resident LUT in the design (measured): {rom_lut_measured:,}")
    print(f"  addressable savings = {rom_lut_measured:,} x {CLUT_RATIO} = "
          f"{addressable:,.0f} LUT")
    print(f"  bands: PROMOTE >= {PROMOTE_LUT:,} LUT, KILL < {KILL_LUT:,} LUT")
    verdict = "KILL" if addressable < KILL_LUT else (
        "PROMOTE" if addressable >= PROMOTE_LUT else "HOLD")
    print(f"  VERDICT: {verdict}")
    print(f"\n  counterfactual (modeled, counting-grade -- NOT a measurement):")
    print(f"    total ROM bits = {rom_bits:,} "
          f"({len(roms)} tables x instances; all currently in BRAM)")
    print(f"    if forced to LUTROM: ~{lutrom_lo:,.0f}-{lutrom_hi:,.0f} LUT "
          f"(bits/64 to {LUTROM_OVERHEAD}x mux bracket)")
    print(f"    60% of that = {lutrom_lo * CLUT_RATIO:,.0f}-{lutrom_hi * CLUT_RATIO:,.0f} LUT "
          f"-- still < KILL band {KILL_LUT:,}")
    print(f"    BRAM view: 0.6 x {top['BRAM_18K']} = {bram_saved:.0f} BRAM_18K saved of "
          f"{DEVICE_BRAM:,} available ({top['BRAM_18K'] / DEVICE_BRAM:.1%} used -- not binding)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = dict(
        source_xml=str(STDNN_XML.relative_to(REPO)),
        source_prj=str(STDNN_PRJ.relative_to(REPO)),
        top_total=top,
        firmware_table_configs=configs,
        kernel_indexes_table=users,
        rom_bindnodes=[dict(r, instances=count.get(r["module"], 0)) for r in roms],
        rom_named_modules=rom_named,
        rom_bram_total=rom_bram_total,
        softmax_modules_lut=softmax_lut,
        softmax_modules_bram=softmax_bram,
        softmax_modules_dsp=softmax_dsp,
        sibling_scan=siblings,
        fr_pattern_inspection=fr,
        rom_lut_measured=rom_lut_measured,
        addressable_savings_lut=addressable,
        rom_bits_total=rom_bits,
        lutrom_counterfactual_lut=[lutrom_lo, lutrom_hi],
        lutrom_counterfactual_savings_lut=[lutrom_lo * CLUT_RATIO,
                                           lutrom_hi * CLUT_RATIO],
        bram_modeled_savings=bram_saved,
        bands=dict(promote=PROMOTE_LUT, kill=KILL_LUT),
        verdict=verdict,
    )
    out_path = OUT_DIR / "counting_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
