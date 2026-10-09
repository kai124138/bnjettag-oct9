#!/usr/bin/env python3
"""Fill the A0 portrait poster with the complete content of the finished landscape poster.

The portrait file is the base, not a fresh template: its slide master, header band
(title / authors / affiliations) and its own visual language — 28.5 pt blue #0B5394
section headings, 17.25 pt body, dark-blue table headers, two 14.74" columns — are kept
exactly as they were set up. What changes is the content: the half-finished, paraphrased
draft is replaced by every block of the landscape poster
(``poster-final-version-revised.pptx``), re-flowed down the two columns.

Text is transferred, never retyped. Each source shape is deep-copied as XML so its runs,
bold/italic spans, bullets, sub/superscripts and footnote markers survive; only the point
sizes are rescaled to the portrait's scale (21 pt body -> 17.25 pt, i.e. x0.8214) and the
section headings restyled to the portrait's blue. Tables are copied cell-for-cell and
re-dressed in the portrait's header colour. All six figures are re-embedded from the
source's own media, which also fixes the 1x1 px placeholder standing in for the
architecture diagram and restores the missing AUC-vs-EBOPs plot.

Column breaks come from measured text heights, and headings, figure captions and table
footnotes are kept with the block they belong to.

Inputs:
  base    docs/reports/BNJetTag-FastML-poster-A0-portrait.pptx   (the portrait draft)
  source  ~/Downloads/poster-final-version-revised.pptx          (the finished landscape poster)
Usage:
  python3 build_poster_portrait.py [out.pptx]
"""
from __future__ import annotations

import copy
import functools
import os
import sys

from PIL import ImageFont
from pptx import Presentation
from pptx.util import Inches

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

SRC = os.path.expanduser("~/Downloads/poster-final-version-revised.pptx")
BASE = os.path.join(REPO, "docs/reports/BNJetTag-FastML-poster-A0-portrait.pptx")
DST = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1
                         else "~/Downloads/BNJetTag-FastML-poster-A0-portrait.pptx")
TMP = os.path.join(os.environ.get("TMPDIR", "/tmp"), "bnjettag_portrait_figs")
os.makedirs(TMP, exist_ok=True)

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def a(tag):
    return f"{{{A}}}{tag}"


def p_(tag):
    return f"{{{P}}}{tag}"


# ------------------------------------------------- the portrait's own style
INK = "1A1A1A"          # body text
ACCENT = "0B5394"       # section headings and table header fill

# ------------------------------------------------- page geometry
# The draft's panels sat 0.63 in from the page edge with a further 0.48 in of padding
# before the text; both are pulled in so the columns get the width back. The master's two
# rounded rectangles are moved to match (see `retile_master`), so the frame still fits
# the text exactly.
PAGE_W = 33.109
MARGIN = 0.32                   # page edge -> panel   (was 0.63)
GUTTER = 0.34                   # panel -> panel       (was 0.47)
PAD_LR = 0.26                   # panel -> text        (was 0.48)
PANEL_TOP, PANEL_BOT = 5.38, 45.05      # was 5.76 / 44.74
PAD_T, PAD_B = 0.26, 0.22

PANEL_W = (PAGE_W - 2 * MARGIN - GUTTER) / 2
PANEL_X = [MARGIN, MARGIN + PANEL_W + GUTTER]
COL_W = PANEL_W - 2 * PAD_LR
COL_X = [x + PAD_LR for x in PANEL_X]
TOP, BOTTOM = PANEL_TOP + PAD_T, PANEL_BOT - PAD_B
CAPACITY = BOTTOM - TOP

INS_LR, INS_TB = 0.10, 0.05     # PowerPoint text-box defaults, as in the draft's shapes
GAP, GAP_HDR = 0.06, 0.16

# ------------------------------------------------- type scale
# Everything is tied to the body size: the draft's 17.25 pt body, 28.5 pt headings and
# 15.75 / 14.25 pt table type keep their proportions, and `fit_body_pt` below raises the
# whole scale as far as the two columns will take.
SRC_BODY_PT = 21.0              # the landscape poster's body size
DRAFT_BODY_PT = 17.25           # the draft's body size, and the base of every ratio
HEAD_RATIO = 28.5 / DRAFT_BODY_PT
TBL_RATIO = {20: 15.75 / DRAFT_BODY_PT, 24: 14.25 / DRAFT_BODY_PT,
             37: 15.75 / DRAFT_BODY_PT, 40: 14.25 / DRAFT_BODY_PT}

BODY_PT = DRAFT_BODY_PT         # rebound by set_body_pt()
SCALE = BODY_PT / SRC_BODY_PT
HEAD_PT = BODY_PT * HEAD_RATIO
DEFAULT_PT = BODY_PT
TBL_PT = {k: v * BODY_PT for k, v in TBL_RATIO.items()}


def quarter(pt):
    """Point sizes live on PowerPoint's 0.25 pt grid, as the draft's did."""
    return round(pt * 4.0) / 4.0


def set_body_pt(pt):
    global BODY_PT, SCALE, HEAD_PT, DEFAULT_PT, TBL_PT
    BODY_PT = pt
    SCALE = pt / SRC_BODY_PT
    HEAD_PT = quarter(pt * HEAD_RATIO)
    DEFAULT_PT = pt
    TBL_PT = {k: quarter(v * pt) for k, v in TBL_RATIO.items()}

# ------------------------------------------------- text metrics
FONTS = {
    (0, 0): "/System/Library/Fonts/Supplemental/Arial.ttf",
    (1, 0): "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    (0, 1): "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
    (1, 1): "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
}
# Calibrated on the two auto-fitted (spAutoFit) text boxes in the landscape deck: the author
# line gives 1.213 and the affiliation block 1.241, both on the reading that PowerPoint
# applies the 20% space-before to every paragraph except the first.
LINE_FACTOR = 1.22
SPC_BEFORE = 0.20
DEFAULT_PT = 17.25


@functools.lru_cache(maxsize=None)
def _font(bold, italic, size_pt):
    return ImageFont.truetype(FONTS[(int(bool(bold)), int(bool(italic)))], int(round(size_pt * 4)))


def _width(text, bold, italic, size_pt):
    return 0.0 if not text else _font(bold, italic, size_pt).getlength(text) / 4.0


def wrap_count(words, first_w, rest_w):
    lines, cur, limit = 1, 0.0, first_w
    for text, bold, ital, size in words:
        w = _width(text, bold, ital, size)
        if cur + w > limit and cur > 0:
            lines, cur, limit = lines + 1, w, rest_w
        else:
            cur += w
    return lines


def block_height(paras, box_w):
    """Rendered height, inches, of [(marL, indent, [(text, bold, italic, pt), ...]), ...]."""
    avail = (box_w - 2 * INS_LR) * 72.0
    total = 0.0
    for i, (mar_l, ind, runs) in enumerate(paras):
        size = max((r[3] or DEFAULT_PT) for r in runs)
        words = []
        for text, bold, ital, pt in runs:
            parts = text.split(" ")
            for j, part in enumerate(parts):
                words.append((part + (" " if j < len(parts) - 1 else ""),
                              bold, ital, pt or DEFAULT_PT))
        lines = wrap_count(words, avail - (mar_l + ind) * 72.0, avail - mar_l * 72.0)
        total += lines * size * LINE_FACTOR + (size * SPC_BEFORE if i else 0.0)
    return total / 72.0 + 2 * INS_TB


# ------------------------------------------------- the landscape poster
src = Presentation(SRC)
s_shapes = list(src.slides[0].shapes)

for sh in s_shapes:                                     # keep the figures byte-identical
    if sh.shape_type == 13:
        with open(os.path.join(TMP, f"{sh.image.sha1[:8]}.{sh.image.ext}"), "wb") as fh:
            fh.write(sh.image.blob)

HDRS = {1, 2, 3, 4, 5, 6, 7, 12, 14, 23, 26, 30, 34, 45}    # the fourteen section headings

FIG = {                                    # sha, aspect, width as a fraction of the column
    "bitnet": ("245af4af", 2035 / 728, 0.692),
    "arch": ("042a9ecc", 6000 / 3170, 0.692),
    "auc": ("5a2be38b", 1650 / 1144, 0.489),
    "cms": ("9348c4f6", 2028 / 620, 0.692),
    "pareto": ("66ff9fb7", 1650 / 1144, 0.489),
    "lut": ("17a3bb14", 4493 / 1194, 0.719),
}


FIG_SCALE = 1.00                # rebound by the fitter; 1.0 = figure grows with the column
FIG_FLOOR = 0.85                # how much figure width the text is allowed to take


def fig_width(ref):
    return FIG[ref][2] * FIG_SCALE * COL_W

FLOW = [
    # --- landscape column 1
    ("hdr", 1), ("body", 0), ("pic", "bitnet"), ("cap", 11),
    ("hdr", 12), ("body", 13),
    ("hdr", 2), ("body", 8),
    ("hdr", 14), ("body", 15),
    # --- landscape column 2
    ("hdr", 3), ("body", 16), ("pic", "arch"), ("cap", 18),
    ("hdr", 4), ("pic", "auc"), ("tbl", 20), ("cap", 21), ("body", 22),
    # --- landscape column 3
    ("hdr", 23), ("tbl", 24), ("cap", 25),
    ("hdr", 26), ("pic", "cms"), ("cap", 28), ("body", 29),
    ("hdr", 30), ("body", 31), ("pic", "pareto"), ("cap", 33),
    ("hdr", 34), ("body", 35),
    # --- landscape column 4
    ("hdr", 5), ("body", 36), ("tbl", 37), ("body", 38),
    ("hdr", 6), ("body", 39), ("tbl", 40), ("pic", "lut"), ("cap", 42), ("body", 43),
    ("hdr", 7), ("body", 44),
    ("hdr", 45), ("body", 48),
]


def scaled_paragraphs(idx):
    """Source paragraphs carrying the portrait's point sizes."""
    out = []
    for para in s_shapes[idx].text_frame.paragraphs:
        ppr = para._pPr
        mar_l = ind = 0.0
        if ppr is not None:
            if ppr.get("marL"):
                mar_l = int(ppr.get("marL")) / 914400 * SCALE
            if ppr.get("indent"):
                ind = int(ppr.get("indent")) / 914400 * SCALE
        runs = []
        for r in para.runs:
            pt = (HEAD_PT if idx in HDRS else
                  quarter(r.font.size.pt * SCALE) if r.font.size else None)
            runs.append((r.text, bool(r.font.bold) or idx in HDRS, bool(r.font.italic), pt))
        out.append((mar_l, ind, runs or [("", False, False, None)]))
    return out


CELL_MAR_LR, CELL_MAR_TB = 0.10, 0.05


def table_geometry(idx, frame_w):
    """Column widths and row heights for a source table redrawn ``frame_w`` inches wide."""
    shape = s_shapes[idx]
    size = TBL_PT[idx]
    grid = shape._element.find(f".//{a('tblGrid')}")
    cols = [int(c.get("w")) for c in grid.findall(a("gridCol"))]
    total = sum(cols)
    widths = [c / total * frame_w for c in cols]
    rows = []
    for row in shape.table.rows:
        need = 0.0
        for cell, w in zip(row.cells, widths):
            avail = (w - 2 * CELL_MAR_LR) * 72.0
            h = 0.0
            for para in cell.text_frame.paragraphs:
                bold = any(r.font.bold for r in para.runs)
                words = [(t + " ", bold, False, size)
                         for t in "".join(r.text for r in para.runs).split(" ")]
                h += wrap_count(words, avail, avail) * size * LINE_FACTOR
            need = max(need, h / 72.0 + 2 * CELL_MAR_TB)
        rows.append(max(0.42, need))
    return widths, rows


# ------------------------------------------------- column packing
# Atomic units: a heading carries the block after it, a caption stays with what it follows.
units, i = [], 0
while i < len(FLOW):
    j = i + 1
    if FLOW[i][0] == "hdr" and j < len(FLOW):
        j += 1
    while j < len(FLOW) and FLOW[j][0] == "cap":
        j += 1
    units.append(list(range(i, j)))
    i = j


def gap_before(prev_kind, kind):
    return GAP_HDR if kind == "hdr" and prev_kind is not None else GAP


MAX_EXTRA = 0.60                         # justify both columns to the same foot
SAFETY = 0.35                            # the line-height model is calibrated, not exact


def solve(body_pt):
    """Measure, split and justify the flow at ``body_pt``; None if it will not fit."""
    set_body_pt(body_pt)
    tables = {ref: table_geometry(ref, COL_W) for kind, ref in FLOW if kind == "tbl"}

    heights = []
    for kind, ref in FLOW:
        if kind == "pic":
            heights.append(fig_width(ref) / FIG[ref][1])
        elif kind == "tbl":
            heights.append(sum(tables[ref][1]))
        else:
            heights.append(block_height(scaled_paragraphs(ref), COL_W))

    def unit_height(unit, first_in_column):
        h, prev = 0.0, (None if first_in_column else "body")
        for b in unit:
            if prev is not None:
                h += gap_before(prev, FLOW[b][0])
            h += heights[b]
            prev = FLOW[b][0]
        return h

    n = len(units)
    head = [unit_height(u, True) for u in units]
    tail = [unit_height(u, False) for u in units]

    def span(p, q):
        return head[p] + sum(tail[k] for k in range(p + 1, q))

    # Prefer a break that starts column 2 on a section heading; fall back to the most
    # even split if no clean break fits.
    feasible = [(max(span(0, i), span(i, n)), FLOW[units[i][0]][0] == "hdr", i)
                for i in range(1, n)]
    fits = [f for f in feasible if f[0] <= CAPACITY - SAFETY]
    if not fits:
        return None
    clean = [f for f in fits if f[1]]
    _tallest, _is_hdr, cut = min(clean or fits)

    layout = []
    for p, q in ((0, cut), (cut, n)):
        blocks = [b for u in units[p:q] for b in u]
        gaps = [gap_before(FLOW[blocks[k - 1]][0], FLOW[blocks[k]][0])
                for k in range(1, len(blocks))]
        slack = CAPACITY - (sum(heights[b] for b in blocks) + sum(gaps))
        extra = min(MAX_EXTRA, slack / len(gaps)) if gaps and slack > 0 else 0.0
        column, y = [], TOP
        for k, b in enumerate(blocks):
            if k:
                y += gaps[k - 1] + extra
            column.append((b, y))
            y += heights[b]
        layout.append(column)
    return layout, heights, tables


def fit(lo=DRAFT_BODY_PT, hi=26.0, step=0.25):
    """Biggest type the poster will take.

    Type size comes first — that is what the two columns were re-cut for — and the
    figures give back width, but only down to ``FIG_FLOOR``. Among the settings that
    fit, the largest body size wins, and at that size the largest figures win.
    """
    global FIG_SCALE
    best = None
    pt = lo
    while pt <= hi + 1e-9:
        found = None
        for hundredths in range(100, int(FIG_FLOOR * 100) - 1, -1):
            FIG_SCALE = hundredths / 100.0
            got = solve(pt)
            if got is not None:
                found = (pt, FIG_SCALE, got)
                break
        if found is None:
            break
        best, pt = found, pt + step
    if best is None:
        raise SystemExit(f"nothing fits: even {lo} pt overflows {CAPACITY:.2f} in")
    FIG_SCALE = best[1]
    return best


BODY_PT, FIG_SCALE, (layout, heights, TABLES) = fit()
set_body_pt(BODY_PT)

# ------------------------------------------------- edit the portrait file
prs = Presentation(BASE)
slide = prs.slides[0]
tree = slide.shapes._spTree
KEEP = {"poster-title", "poster-authors", "poster-affiliations"}

for sh in list(slide.shapes):            # clear the draft body, keep the header band
    if sh.name not in KEEP:
        sh._element.getparent().remove(sh._element)


def sub(parent, tag):
    found = parent.find(a(tag))
    if found is None:
        found = parent.makeelement(a(tag), {})
        parent.append(found)
    return found


def solid_fill(rpr, hexcolor):
    for old in rpr.findall(a("solidFill")):
        rpr.remove(old)
    fill = rpr.makeelement(a("solidFill"), {})
    fill.append(fill.makeelement(a("srgbClr"), {"val": hexcolor}))
    rpr.insert(0, fill)


def adopt(element):
    tree.append(element)
    return next(sh for sh in slide.shapes if sh._element is element)


def place(shape, left, top, width, height=None):
    shape.left, shape.top, shape.width = Inches(left), Inches(top), Inches(width)
    if height is not None:
        shape.height = Inches(height)


def text_shape(idx, is_head):
    """Copy a source text shape and re-dress it in the portrait's style."""
    el = copy.deepcopy(s_shapes[idx]._element)

    nv_pr = el.find(f".//{p_('nvPr')}")               # a plain text box, not a placeholder
    for child in list(nv_pr):
        nv_pr.remove(child)

    sp_pr = el.find(p_("spPr"))
    for child in list(sp_pr):
        if child.tag != a("xfrm"):
            sp_pr.remove(child)
    geom = sp_pr.makeelement(a("prstGeom"), {"prst": "rect"})
    geom.append(geom.makeelement(a("avLst"), {}))
    sp_pr.append(geom)
    sp_pr.append(sp_pr.makeelement(a("noFill"), {}))
    line = sp_pr.makeelement(a("ln"), {"w": "0"})
    line.append(line.makeelement(a("noFill"), {}))
    sp_pr.append(line)

    tx = el.find(p_("txBody"))
    body_pr = tx.find(a("bodyPr"))
    for key in ("lIns", "rIns", "tIns", "bIns"):
        body_pr.attrib.pop(key, None)
    body_pr.set("wrap", "square")
    body_pr.set("anchor", "t")
    for lst in tx.findall(a("lstStyle")):
        for child in list(lst):
            lst.remove(child)

    for para in tx.findall(a("p")):
        ppr = para.find(a("pPr"))
        if ppr is None:
            ppr = para.makeelement(a("pPr"), {})
            para.insert(0, ppr)
        ppr.set("algn", "l")
        for key in ("marL", "indent"):                # bullets: scale the hanging indent
            if ppr.get(key):
                ppr.set(key, str(int(int(ppr.get(key)) * SCALE)))
        for run in para.findall(a("r")):
            rpr = sub(run, "rPr")
            run.remove(rpr)
            run.insert(0, rpr)
            if is_head:
                rpr.set("sz", str(int(round(HEAD_PT * 100))))
                rpr.set("b", "1")
                rpr.attrib.pop("u", None)
                solid_fill(rpr, ACCENT)
            elif rpr.get("sz"):
                rpr.set("sz", str(int(round(int(rpr.get("sz")) * SCALE / 25.0) * 25)))
            else:
                rpr.set("sz", str(int(DEFAULT_PT * 100)))
            if not is_head and rpr.find(a("solidFill")) is None:
                solid_fill(rpr, INK)
            if rpr.find(a("latin")) is None:
                rpr.append(rpr.makeelement(a("latin"), {"typeface": "Arial"}))
        end = para.find(a("endParaRPr"))
        if end is not None:
            para.remove(end)
    return adopt(el)


def table_shape(idx, widths, rows):
    """Copy a source table and re-dress it with the portrait's dark-blue header row."""
    el = copy.deepcopy(s_shapes[idx]._element)
    size = str(int(round(TBL_PT[idx] * 100)))
    tbl = el.find(f".//{a('tbl')}")

    tbl_pr = tbl.find(a("tblPr"))                     # the draft's tables carry no style flags
    for key in ("firstRow", "bandRow", "firstCol", "lastRow", "lastCol", "bandCol"):
        tbl_pr.attrib.pop(key, None)

    for col, w in zip(tbl.find(a("tblGrid")).findall(a("gridCol")), widths):
        col.set("w", str(int(Inches(w))))

    for ri, tr in enumerate(tbl.findall(a("tr"))):
        tr.set("h", str(int(Inches(rows[ri]))))
        for tc in tr.findall(a("tc")):
            for run in tc.iter(a("r")):
                rpr = sub(run, "rPr")
                run.remove(rpr)
                run.insert(0, rpr)
                rpr.set("sz", size)
                if ri == 0:
                    rpr.set("b", "1")
                    solid_fill(rpr, "FFFFFF")
            tc_pr = tc.find(a("tcPr"))
            if tc_pr is None:
                tc_pr = tc.makeelement(a("tcPr"), {})
                tc.append(tc_pr)
            for key, val in (("marL", "91440"), ("marR", "91440"),
                             ("marT", "45720"), ("marB", "45720")):
                tc_pr.set(key, val)
            for old in tc_pr.findall(a("solidFill")):
                tc_pr.remove(old)
            if ri == 0:
                fill = tc_pr.makeelement(a("solidFill"), {})
                fill.append(fill.makeelement(a("srgbClr"), {"val": ACCENT}))
                tc_pr.insert(0, fill)
    return adopt(el)


for c, column in enumerate(layout):
    x = COL_X[c]
    for block, y in column:
        kind, ref = FLOW[block]
        if kind == "pic":
            sha, _aspect, _frac = FIG[ref]
            width = fig_width(ref)
            path = next(os.path.join(TMP, f) for f in os.listdir(TMP) if f.startswith(sha))
            slide.shapes.add_picture(path, Inches(x + (COL_W - width) / 2), Inches(y),
                                     width=Inches(width))
        elif kind == "tbl":
            widths, rows = TABLES[ref]
            place(table_shape(ref, widths, rows), x, y, COL_W, sum(rows))
        else:
            place(text_shape(ref, kind == "hdr"), x, y, COL_W, heights[block])

def retile_master():
    """Pull the master's two rounded panels out to the tighter margins."""
    master = slide.slide_layout.slide_master
    panels = [sh for sh in master.shapes if sh.name.startswith("Rounded Rectangle")]
    if len(panels) != 2:                       # leave the frame alone if it isn't the pair
        return 0
    for sh, left in zip(sorted(panels, key=lambda s: s.left), PANEL_X):
        sh.left, sh.top = Inches(left), Inches(PANEL_TOP)
        sh.width, sh.height = Inches(PANEL_W), Inches(PANEL_BOT - PANEL_TOP)
    return len(panels)


panels_moved = retile_master()

for k, cnv in enumerate(tree.iter(p_("cNvPr")), start=2):   # ids must be unique
    cnv.set("id", str(k))

prs.save(DST)

print(f"wrote {DST}")
print(f"  figures at {FIG_SCALE:.2f} of the column "
      f"({', '.join(f'{fig_width(r):.1f}\u2033' for r in FIG)})")
print(f"  body {BODY_PT:.2f} pt, headings {HEAD_PT:.2f} pt, "
      f"tables {'/'.join(f'{v:g}' for v in sorted(set(TBL_PT.values()), reverse=True))} pt")
print(f"  columns {COL_W:.2f} in wide at x = {COL_X[0]:.2f} / {COL_X[1]:.2f}; "
      f"page margin {MARGIN:.2f} in, gutter {GUTTER:.2f} in")
print(f"  panels {PANEL_X[0]:.2f}-{PANEL_X[0] + PANEL_W:.2f} and "
      f"{PANEL_X[1]:.2f}-{PANEL_X[1] + PANEL_W:.2f} in, {PANEL_TOP:.2f}-{PANEL_BOT:.2f} in "
      f"({panels_moved} moved on the master)")
for c, column in enumerate(layout):
    last, y = column[-1]
    print(f"  column {c + 1}: {len(column)} blocks, {TOP:.2f} -> {y + heights[last]:.2f} in "
          f"(panel bottom {PANEL_BOT:.2f})")
print(f"  blocks placed: {sum(len(c) for c in layout)} / {len(FLOW)}")
