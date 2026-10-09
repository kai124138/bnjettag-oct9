#!/usr/bin/env python3
"""Build the BNJetTag study guide — a read-and-learn deck for presenting Round 14.

This is **personal preparation material, not part of the scientific record.** It is a
teaching document: it explains the physics, the method, the code and the measurements at
enough depth to be defended out loud, and it carries the caveats that must travel with
every number.

Every figure is either a committed TikZ schematic (rendered through the upmath MCP server
and cached under ``docs/figures/study-guide/``) or a matplotlib plot built from the stored
arrays and synthesis reports. Every number on a slide is transcribed from ``RESEARCH.md``,
``results/r14/*.md`` or ``roc-results/r14/*/roc_auc.md`` and carries its source in the
slide footer.

Usage:
    .venv-hgq2/bin/python bnjettag/code/plots/build_study_guide.py [out.pptx]
"""
from __future__ import annotations

import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FIGS = os.path.join(REPO, "docs", "figures", "study-guide")
R14 = os.path.join(REPO, "bnjettag", "results", "r14", "figures")

DST = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                      else os.path.join(REPO, "docs", "reports", "BNJetTag-study-guide.pptx"))

# ------------------------------------------------------------------ house style
INK = RGBColor(0x1A, 0x1A, 0x1A)
ACCENT = RGBColor(0x0B, 0x53, 0x94)       # the project blue, as on the poster
MUTED = RGBColor(0x55, 0x5F, 0x66)
FAINT = RGBColor(0x8A, 0x93, 0x99)
RULE = RGBColor(0xD8, 0xDD, 0xE0)
GOOD = RGBColor(0x1E, 0x7D, 0x4F)
WARN = RGBColor(0xB0, 0x3A, 0x2E)
PANEL = RGBColor(0xF4, 0xF6, 0xF8)
CODEBG = RGBColor(0xF7, 0xF7, 0xF4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

BODY = "Helvetica Neue"
MONO = "Menlo"

W, H = Inches(13.333), Inches(7.5)
M = Inches(0.62)                          # page margin
CONTENT_W = W - 2 * M


# ------------------------------------------------------------------ primitives
def _tf(shape, *, wrap=True, shrink=False):
    tf = shape.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if shrink:
        from pptx.enum.text import MSO_AUTO_SIZE
        tf.auto_size = MSO_AUTO_SIZE.NONE
    return tf


def textbox(slide, x, y, w, h, *, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = _tf(box)
    tf.vertical_anchor = anchor
    return box, tf


def para(tf, text, *, size=14, bold=False, italic=False, color=INK, font=BODY,
         space_before=0, space_after=4, align=PP_ALIGN.LEFT, line=1.18, first=False,
         indent=0, bullet=None):
    """Add a paragraph. `bullet` is a literal glyph we draw ourselves (python-pptx has no
    clean bullet API); indent is in inches."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    p.line_spacing = line
    if indent:
        p.left_indent = Inches(indent)
        p.first_line_indent = Inches(-0.22) if bullet else 0
    body = (bullet + "  " + text) if bullet else text
    _runs(p, body, size=size, bold=bold, italic=italic, color=color, font=font)
    return p


def _runs(p, text, *, size, bold, italic, color, font):
    """Split on **bold**, *italic*, `code` and @@accent@@ markers."""
    import re
    tokens = re.split(r"(\*\*.+?\*\*|(?<!\*)\*[^*]+?\*(?!\*)|`[^`]+?`|@@.+?@@)", text)
    for tok in tokens:
        if not tok:
            continue
        r = p.add_run()
        f = r.font
        f.size = Pt(size)
        f.name = font
        f.bold = bold
        f.italic = italic
        f.color.rgb = color
        if tok.startswith("**") and tok.endswith("**"):
            r.text = tok[2:-2]
            f.bold = True
        elif tok.startswith("@@") and tok.endswith("@@"):
            r.text = tok[2:-2]
            f.bold = True
            f.color.rgb = ACCENT
        elif tok.startswith("`") and tok.endswith("`"):
            r.text = tok[1:-1]
            f.name = MONO
            f.size = Pt(size - 1.2)
            f.color.rgb = RGBColor(0x33, 0x44, 0x55)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r.text = tok[1:-1]
            f.italic = True
        else:
            r.text = tok


def rect(slide, x, y, w, h, fill=None, line=None, line_w=1.0):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_w)
    sh.text_frame.word_wrap = True
    return sh


def hrule(slide, x, y, w, color=RULE, weight=1.0):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Pt(weight))
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


def picture_fit(slide, path, x, y, w, h):
    """Place an image centred inside the (x, y, w, h) box, preserving aspect."""
    from PIL import Image
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    return slide.shapes.add_picture(path, int(x + (w - pw) / 2), int(y + (h - ph) / 2),
                                    width=pw, height=ph)


# ------------------------------------------------------------------ slide chrome
class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.n = 0
        self.part = ""
        self.index = []          # (number, part, title) for the contents page

    # -- a bare slide with the running footer
    def _slide(self, *, footer=None, counted=True):
        s = self.prs.slides.add_slide(self.blank)
        if counted:
            self.n += 1
            _, tf = textbox(s, W - M - Inches(1.0), H - Inches(0.44),
                            Inches(1.0), Inches(0.26))
            para(tf, str(self.n), size=9.5, color=FAINT, align=PP_ALIGN.RIGHT, first=True)
        if footer:
            _, tf = textbox(s, M, H - Inches(0.46), CONTENT_W - Inches(1.1), Inches(0.3))
            para(tf, footer, size=8.5, color=FAINT, first=True, line=1.1)
        return s

    # -- title + optional standfirst, returns the y where content may start
    def _head(self, s, title, standfirst=None, kicker=None):
        y = M - Inches(0.06)
        if kicker is None:
            kicker = self.part
        if kicker:
            _, tf = textbox(s, M, y, CONTENT_W, Inches(0.24))
            para(tf, kicker.upper(), size=10, bold=True, color=ACCENT, first=True)
            y += Inches(0.28)
        _, tf = textbox(s, M, y, CONTENT_W, Inches(0.46))
        para(tf, title, size=25, bold=True, color=INK, first=True, line=1.05)
        y += Inches(0.16) + Inches(0.30) * (1 + title.count("\n"))
        if standfirst:
            _, tf = textbox(s, M, y, CONTENT_W, Inches(0.5))
            para(tf, standfirst, size=13.5, color=MUTED, first=True, line=1.28, italic=False)
            y += Inches(0.24) * (1 + len(standfirst) // 150)
        hrule(s, M, y + Inches(0.05), CONTENT_W)
        return y + Inches(0.26)

    # ============================================================ slide kinds
    def cover(self, title, subtitle, lines):
        s = self._slide(counted=False)
        rect(s, 0, 0, W, Inches(3.05), fill=RGBColor(0x0B, 0x53, 0x94))
        _, tf = textbox(s, M, Inches(1.02), CONTENT_W, Inches(1.4))
        para(tf, title, size=42, bold=True, color=WHITE, first=True, line=1.05)
        para(tf, subtitle, size=17, color=RGBColor(0xC6, 0xDA, 0xEE), space_before=10, line=1.3)
        _, tf = textbox(s, M, Inches(3.55), Inches(8.2), Inches(3.2))
        for i, ln in enumerate(lines):
            para(tf, ln, size=13.5, color=INK if i == 0 else MUTED,
                 bold=(i == 0), first=(i == 0), space_after=9, line=1.35)
        return s

    def divider(self, part, title, blurb, items):
        self.part = part
        s = self._slide()
        rect(s, 0, 0, Inches(0.26), H, fill=ACCENT)
        _, tf = textbox(s, Inches(0.95), Inches(1.5), Inches(11.6), Inches(1.2))
        para(tf, part.upper(), size=13, bold=True, color=ACCENT, first=True)
        para(tf, title, size=34, bold=True, color=INK, space_before=6, line=1.06)
        para(tf, blurb, size=14.5, color=MUTED, space_before=12, line=1.35)
        _, tf = textbox(s, Inches(0.95), Inches(4.15), Inches(11.6), Inches(2.4))
        for i, it in enumerate(items):
            para(tf, it, size=12.5, color=MUTED, bullet="—", first=(i == 0),
                 space_after=7, line=1.3)
        self.index.append((self.n, part, title))
        return s

    def text(self, title, blocks, *, standfirst=None, footer=None, cols=1, kicker=None):
        """blocks: list of (kind, payload). kind in {p, b, h, note, warn, good, code, kv}."""
        s = self._slide(footer=footer)
        y = self._head(s, title, standfirst, kicker)
        avail_h = H - y - Inches(0.62)
        if cols == 1:
            self._blocks(s, M, y, CONTENT_W, avail_h, blocks)
        else:
            gap = Inches(0.42)
            cw = (CONTENT_W - gap) / 2
            half = self._split(blocks)
            self._blocks(s, M, y, cw, avail_h, blocks[:half])
            self._blocks(s, M + cw + gap, y, cw, avail_h, blocks[half:])
        return s

    @staticmethod
    def _split(blocks):
        """Split a block list into two roughly equal columns by rendered weight."""
        def wt(b):
            k, v = b[0], b[1]
            if k == "h":
                return 34
            if k == "code":
                return 14 * (v.count("\n") + 1) + 16
            return 15 + len(str(v)) * 0.30
        tot = sum(wt(b) for b in blocks)
        run, i = 0, 0
        for i, b in enumerate(blocks):
            if run + wt(b) / 2 > tot / 2 and i > 0:
                return i
            run += wt(b)
        return len(blocks)

    def _blocks(self, s, x, y, w, h, blocks):
        cur = y
        for b in blocks:
            kind, payload = b[0], b[1]
            opt = b[2] if len(b) > 2 else {}
            cur = self._one_block(s, x, cur, w, kind, payload, opt)

    def _one_block(self, s, x, y, w, kind, payload, opt):
        size = opt.get("size", 12.5)
        if kind == "h":
            _, tf = textbox(s, x, y, w, Inches(0.3))
            para(tf, payload, size=opt.get("size", 13.5), bold=True, color=ACCENT, first=True)
            return y + Inches(0.30)
        if kind == "p":
            lines = _wrapped(payload, w, size)
            _, tf = textbox(s, x, y, w, Inches(0.24) * lines)
            para(tf, payload, size=size, color=INK, first=True, line=1.26)
            return y + Inches(0.192) * lines + Inches(0.085)
        if kind == "b":
            lines = _wrapped(payload, w - Inches(0.24), size)
            _, tf = textbox(s, x, y, w, Inches(0.24) * lines)
            para(tf, payload, size=size, color=INK, first=True, line=1.24,
                 indent=0.22, bullet=opt.get("glyph", "•"))
            return y + Inches(0.192) * lines + Inches(0.075)
        if kind == "kv":
            k, v = payload
            _, tf = textbox(s, x, y, Inches(2.0), Inches(0.26))
            para(tf, k, size=size, bold=True, color=ACCENT, first=True)
            lines = _wrapped(v, w - Inches(2.08), size)
            _, tf = textbox(s, x + Inches(2.08), y, w - Inches(2.08), Inches(0.24) * lines)
            para(tf, v, size=size, color=INK, first=True, line=1.24)
            return y + max(Inches(0.20), Inches(0.192) * lines) + Inches(0.075)
        if kind in ("note", "warn", "good"):
            col = {"note": ACCENT, "warn": WARN, "good": GOOD}[kind]
            bg = {"note": PANEL, "warn": RGBColor(0xFD, 0xF2, 0xF0),
                  "good": RGBColor(0xEF, 0xF7, 0xF2)}[kind]
            lines = _wrapped(payload, w - Inches(0.42), size)
            bh = Inches(0.192) * lines + Inches(0.22)
            rect(s, x, y, w, bh, fill=bg)
            rect(s, x, y, Pt(3), bh, fill=col)
            _, tf = textbox(s, x + Inches(0.17), y + Inches(0.10), w - Inches(0.30),
                            bh - Inches(0.18))
            para(tf, payload, size=size, color=INK, first=True, line=1.24)
            return y + bh + Inches(0.11)
        if kind == "code":
            src = payload.rstrip("\n")
            nl = src.count("\n") + 1
            csz = opt.get("size", 11.0)
            bh = Pt(csz * 1.42) * nl + Inches(0.20)
            rect(s, x, y, w, bh, fill=CODEBG, line=RGBColor(0xE2, 0xE2, 0xDC))
            _, tf = textbox(s, x + Inches(0.14), y + Inches(0.09), w - Inches(0.24),
                            bh - Inches(0.16))
            for i, ln in enumerate(src.split("\n")):
                para(tf, ln.replace("*", "∗") or " ", size=csz, font=MONO,
                     color=RGBColor(0x22, 0x33, 0x44), first=(i == 0), space_after=0,
                     line=1.18)
            return y + bh + Inches(0.11)
        if kind == "gap":
            return y + Inches(payload)
        raise ValueError(kind)

    def figure(self, title, image, caption, *, standfirst=None, footer=None,
               side=None, kicker=None, img_h=None):
        s = self._slide(footer=footer)
        y = self._head(s, title, standfirst, kicker)
        cap_h = Inches(0.19) * _wrapped(caption, CONTENT_W, 11) + Inches(0.10) if caption else 0
        box_h = (img_h or (H - y - Inches(0.66) - cap_h))
        if side:
            iw = CONTENT_W * 0.615
            picture_fit(s, image, M, y, iw, box_h)
            self._blocks(s, M + iw + Inches(0.34), y, CONTENT_W - iw - Inches(0.34),
                         box_h, side)
        else:
            picture_fit(s, image, M, y, CONTENT_W, box_h)
        if caption:
            _, tf = textbox(s, M, y + box_h + Inches(0.08), CONTENT_W, cap_h)
            para(tf, caption, size=11, color=MUTED, first=True, line=1.25)
        return s

    def table(self, title, header, rows, *, standfirst=None, footer=None, notes=None,
              widths=None, kicker=None, size=12.0, emph=None):
        s = self._slide(footer=footer)
        y = self._head(s, title, standfirst, kicker)
        ncol = len(header)
        widths = widths or [1.0 / ncol] * ncol
        xs, acc = [], M
        for fr in widths:
            xs.append(acc)
            acc += int(CONTENT_W * fr)
        rh = Inches(0.05) + Pt(size * 1.9)
        hh = Inches(0.05) + Pt(size * 1.9)
        rect(s, M, y, CONTENT_W, hh, fill=ACCENT)
        for i, htxt in enumerate(header):
            _, tf = textbox(s, xs[i] + Inches(0.10), y + Inches(0.055),
                            int(CONTENT_W * widths[i]) - Inches(0.16), hh)
            para(tf, htxt, size=size - 0.5, bold=True, color=WHITE, first=True, line=1.1)
        yy = y + hh
        for r_i, row in enumerate(rows):
            if row is None:                     # a rule between groups
                hrule(s, M, yy, CONTENT_W, color=ACCENT, weight=1.2)
                yy += Inches(0.05)
                continue
            if r_i % 2 == 1:
                rect(s, M, yy, CONTENT_W, rh, fill=RGBColor(0xF5, 0xF7, 0xF9))
            for i, cell in enumerate(row):
                _, tf = textbox(s, xs[i] + Inches(0.10), yy + Inches(0.055),
                                int(CONTENT_W * widths[i]) - Inches(0.16), rh)
                bold = bool(emph and r_i in emph)
                para(tf, str(cell), size=size - 0.5, color=INK, bold=bold, first=True, line=1.12)
            yy += rh
        if notes:
            yy += Inches(0.14)
            self._blocks(s, M, yy, CONTENT_W, H - yy - Inches(0.6), notes)
        return s

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.prs.save(path)
        return path


# rough line-count for a proportional font at a given box width
_CPI = {9: 22.5, 10: 20.2, 10.5: 19.3, 11: 18.4, 11.5: 17.6, 12: 16.9, 12.5: 16.2,
        13: 15.6, 13.5: 15.0, 14: 14.5, 15: 13.5, 16: 12.7}


def _wrapped(text, w_emu, size):
    cpi = _CPI.get(round(size * 2) / 2, 16.9 * 12 / max(size, 1))
    per_line = max(12, int(cpi * (w_emu / Inches(1))))
    n = 0
    for chunk in str(text).split("\n"):
        n += max(1, -(-len(chunk) // per_line))
    return n


# ==================================================================== the guide
RESEARCH = "RESEARCH.md"
FIT = "bnjettag/results/r14/hls_r14_fit.md"
HLS = "bnjettag/results/r14/hls_r14.md"
FOLD = "bnjettag/results/r14/hls_r14_folded.md"
ROC = "bnjettag/roc-results/r14/n<N>/roc_auc.md"
WP = "bnjettag/results/r14/working_points_r14.md"


def build():
    d = Deck()

    # ---------------------------------------------------------------- cover
    d.cover(
        "BNJetTag — the study guide",
        "Everything behind the poster: the physics, the method, the code, the measurements,\n"
        "and the answer to every question you are going to be asked.",
        [
            "A 1-bit BitNet transformer jet tagger for the CMS Level-1 trigger, taken through hls4ml to FPGA synthesis.",
            "Read it front to back once. Then read Part VIII — the questions — until the answers are automatic.",
            "Personal preparation material. Not part of the scientific record: the record is RESEARCH.md, and every "
            "number here is transcribed from it or from the results files named in the slide footers.",
            "Round 14 only. Nothing from _attic/ appears here and nothing from it may be quoted.",
        ])

    # ------------------------------------------------------------ how to use
    d.part = ""
    d.text(
        "How to use this guide",
        [
            ("h", "The five things you must be able to do without notes"),
            ("b", "Say what the project is in @@three sentences@@ — problem, idea, what was measured."),
            ("b", "Draw the BitLinear layer on a napkin and say where γ and β go on silicon."),
            ("b", "Quote the AUC cost of binarization at N = 16 (**0.017**) and say what that means at a working point."),
            ("b", "Explain why a zero-DSP count at C-synthesis is not a zero-DSP claim about silicon."),
            ("b", "State the fit result @@with its caveats in the same breath@@ — out-of-context, xczu7ev, pre-route."),
            ("gap", 0.10),
            ("h", "How the deck is built"),
            ("p", "Each slide is self-contained. **@@Say@@** boxes are what to say out loud; **@@Know@@** is the "
                  "supporting fact; **@@Careful@@** boxes are claims you must not make. Code slides quote the "
                  "actual repository file, with its path, so you can open it."),
            ("note", "Every number carries its source in the footer. If a number is not in this guide's footers, "
                     "it is not a project claim — read it from RESEARCH.md §7 or recompute it."),
            ("gap", 0.06),
            ("h", "Two words that are never interchangeable"),
            ("warn", "**Validation AUC** is the training-time monitor computed on a 20% carve-out of the training "
                     "split. **ROC-test AUC** is measured on the dataset's own held-out 260,000-jet split. Every "
                     "number quoted in public is ROC-test. Saying the wrong one in a poster session is the easiest "
                     "way to lose a referee's trust."),
        ],
        standfirst="This is a teaching document, not a slide deck to present from. It is dense on purpose.",
        cols=2, kicker="Front matter")

    # ------------------------------------------------------- 60-second version
    d.text(
        "The whole project in sixty seconds",
        [
            ("h", "1 · The problem"),
            ("p", "The LHC produces a proton–proton collision every 25 ns. The **Level-1 trigger** must decide, "
                  "in FPGAs, within a few microseconds, which collisions to keep — and it throws away about "
                  "99.75% of them. Anything that runs there must be small, fast and fixed-latency, and it must "
                  "share one FPGA with everything else in the trigger."),
            ("h", "2 · The idea"),
            ("p", "A transformer jet tagger whose weights are all **±1** (BitNet-style, 1-bit). A multiply by ±1 "
                  "is a sign flip — an add or a subtract — so a matrix multiply becomes an adder tree in **LUT "
                  "logic** instead of a **DSP** multiplier. DSPs are the scarce resource; the trigger needs them "
                  "for everything else."),
            ("h", "3 · What was measured"),
            ("b", "**Accuracy.** Binarization costs a resolved **0.015–0.017** macro-AUC at N ≤ 16 and "
                  "**0.032–0.036** at N ≥ 32, against FP32, on a held-out set of 260,000 jets."),
            ("b", "**Zero DSP.** The whole model synthesizes at **0 DSP** — verified at the Vivado netlist, not "
                  "only at C-synthesis — once the β rescales and softmax are bound to fabric."),
            ("b", "**Device fit.** The first fitting zero-DSP operating point with an accuracy attached: "
                  "**1,689,320 CLB LUT = 97.8%** of the VU13P's nominal LUT count at **0 DSP**, "
                  "AUC 0.8701 ± 0.0020."),
            ("b", "**The gap.** It is not Level-1 deployable yet: II = 48 and 1.67 µs latency at a 5 ns clock, "
                  "against a goal of sub-microsecond at II = 1."),
            ("gap", 0.05),
            ("good", "**The one-sentence claim.** Binary weights buy a DSP-free mapping of a transformer jet "
                     "tagger onto FPGA logic, at a measured cost of about 1.7 AUC points at the sweet spot — "
                     "and the zero-DSP result survives all the way to a synthesized netlist."),
        ],
        standfirst="If you remember nothing else, remember this slide.",
        cols=2, kicker="Front matter",
        footer=f"Sources: {RESEARCH} §1, §5, §6.3, §6.5 · {FIT} rows 7–8")

    # ------------------------------------------------------------- part I
    d.divider(
        "Part I", "The problem",
        "Why anyone needs a jet tagger that fits in a trigger — and why that is a hardware problem "
        "before it is a machine-learning problem.",
        ["What the LHC produces, and what the Level-1 trigger has to do about it",
         "What a jet is, why tagging it is hard, and what the five classes mean",
         "The dataset, its splits, and what 'held-out' means here",
         "The two hardware numbers that are not accuracy: latency and initiation interval",
         "Why DSP multipliers, not LUTs, are the resource that runs out first"])

    d.figure(
        "The Level-1 trigger, and what it demands",
        os.path.join(FIGS, "trigger.png"),
        "The rates are the public Run-2/3 figures read off M. Pierini's data-flow figure. The Phase-2 "
        "Level-1 latency budget is 12.5 µs, and the VU13P is Phase-2 hardware — if you are asked which era "
        "a number belongs to, say so rather than blending them.",
        standfirst="Protons collide 40 million times a second. The first decision is made in silicon.",
        img_h=Inches(4.35))

    d.text(
        "Latency and initiation interval — say these correctly",
        [
            ("h", "Latency"),
            ("p", "The number of **clock cycles** from a jet entering the design to its class coming out. "
                  "Multiply by the clock period to get nanoseconds. Our shipped point: **333 cycles**, which at "
                  "a 5 ns clock is **1.67 µs**."),
            ("h", "Initiation interval (II)"),
            ("p", "How many cycles must pass before the **next** jet may enter the pipeline. II = 1 means one "
                  "jet per clock. Our shipped point has **II = 48**: one jet every 240 ns at 5 ns."),
            ("note", "These are independent. A design can have a long latency and still accept a new jet every "
                     "clock — that is what pipelining buys. Folding a design shortens nothing and lengthens the "
                     "interval; it trades throughput for area."),
            ("gap", 0.06),
            ("h", "Why II = 48 is not automatically fatal"),
            ("p", "One collision every 25 ns does not mean one *jet* every 25 ns through one copy of the tagger. "
                  "A trigger time-multiplexes: several jets share one engine, or several copies run in parallel. "
                  "The honest statement is that **we have not shown the integration**, not that the number is "
                  "unusable."),
            ("h", "What we did not meet"),
            ("warn", "**Goal 4 — sub-microsecond latency at II = 1 — is not met.** The only timing-clean result is "
                     "1.67 µs at one jet per 240 ns (II = 48, 5 ns clock). The II = 1 zero-DSP design is 122.0% of "
                     "the VU13P's nominal LUT count and fails the 2.5 ns constraint before place-and-route. Say "
                     "this plainly; it is on the poster as an open problem."),
        ],
        standfirst="Two numbers, constantly confused by people who have not built firmware. Do not be one of them.",
        cols=2,
        footer=f"Sources: {RESEARCH} §6.2, §6.3 · {FIT} rows 2, 7, 8")

    d.figure(
        "What a jet is, and why some classes are harder",
        os.path.join(FIGS, "jets.png"),
        "The prong structure is the intuition behind the per-class results in Part VI: top jets lose the least "
        "to binarization, gluon and light quark lose the most at short sequences, and the W/Z pair is where the "
        "long-sequence instability shows up.",
        standfirst="A quark or gluon cannot exist alone. What the detector sees is the spray it turns into.",
        img_h=Inches(4.3))

    d.table(
        "The dataset, and the split discipline that protects every number",
        ["", "What it is", "Why you must say it this way"],
        [
            ["Source", "Public HLS4ML LHC Jet dataset, Zenodo record 3602260",
             "Public, so our numbers are checkable and comparable"],
            ["Physics", "Simulated 13 TeV jets, up to 150 constituents each",
             "For cone size / generator / pile-up, cite the dataset papers — do not improvise"],
            ["Classes", "5, balanced: g, q, W, Z, t", "No reweighting — matches published baselines"],
            ["Input we use", "top-N by p_T × 3 features (p_T, η_rel, φ_rel), N ∈ {8,16,32,64}",
             "The L1-realistic set (Odagiu, arXiv:2402.01876) — 13 of the 16 stored features are thrown away on purpose"],
            ["Total jets", "880,000", ""],
            ["Train split", "620,000, of which 20% (124,000) is carved off per seed as **validation**",
             "This is the training monitor. It is never quoted."],
            ["Held-out split", "**260,000** — the dataset's own `val/` directory",
             "Never trained on, never model-selected on. **Every AUC on the poster is this set.**"],
        ],
        standfirst="The dataset's own held-out partition is named `val/`. Our usage makes it a test set. Say so explicitly.",
        widths=[0.16, 0.44, 0.40], size=11.5,
        notes=[
            ("warn", "**The trap.** A referee hears 'val split' and assumes you tested on your validation data. "
                     "Pre-empt it: *\"the 20% validation carve comes out of the training file and differs per seed — "
                     "it only picks the checkpoint. Every number I show you is the dataset's own 260,000-jet "
                     "partition, which the training process never touched.\"*"),
            ("note", "**Why 260,000 and not 270,000?** One chunk (`jetImage_9_150p_40000_50000.h5`) is absent from "
                     "the Zenodo tarball itself — verified with `tar -tzf`. It is also the test-set size the closest "
                     "published system uses, so the comparison is size-matched."),
        ],
        footer=f"Sources: {RESEARCH} §4 · DATASET.md · docs/reports/poster-2026-08-23-speaker-notes.md")

    d.text(
        "Why DSPs, not LUTs, are the resource that runs out",
        [
            ("h", "The two things an FPGA is made of"),
            ("kv", ("LUT", "A look-up table — the generic logic cell. It can be wired into anything: an adder, "
                            "a comparator, a multiplexer. The VU13P has **1,728,000** of them.")),
            ("kv", ("DSP", "A hard multiply–accumulate slice, built into the silicon. Fast and dense for real "
                            "multiplies — and there are only **12,288** on the VU13P.")),
            ("p", "That ratio is the whole argument. A conventional quantized network spends a DSP on every "
                  "multiply, and on a trigger FPGA the DSPs are gone long before the LUTs are."),
            ("gap", 0.05),
            ("h", "What binary weights do to that"),
            ("p", "A multiply by +1 or −1 is not a multiply. It is an add or a subtract. So a dot product of "
                  "binary weights against activations becomes an **adder tree** — pure logic, no multiplier. "
                  "The core moves off the scarce resource and onto the abundant one, and leaves the DSPs for "
                  "everything else the trigger has to do on the same device."),
            ("good", "**The measured version of that claim.** At C-synthesis, all 13 binary matmul modules and "
                     "both head layers come out at **0 DSP with no directive at all**. The thesis holds on the "
                     "first whole-model synthesis, for free."),
            ("warn", "**And the honest half.** The design is not free of multipliers. The β rescales (3,621 DSP) "
                     "and softmax (512 DSP) are, and beating those to zero cost a directive and a measured "
                     "+1.20M csynth LUT. Part VII is that story."),
        ],
        standfirst="This slide is why the project exists. If you can only defend one idea, defend this one.",
        cols=2,
        footer=f"Sources: {RESEARCH} §6.2 · {HLS} DSP attribution (106 instances, sums exactly to 4,133)")

    # ------------------------------------------------------------- part II
    d.divider(
        "Part II", "The idea",
        "BitNet, the straight-through estimator, and exactly what binarization does and does not touch.",
        ["What a BitLinear layer computes, and where γ and β live on silicon",
         "The absmean quantizer: why centre first, why β = mean|W − α|",
         "The straight-through estimator, and the second stop_gradient nobody notices",
         "What is NOT binary — and why attention cannot be helped by binarization",
         "Norm-free, and why it forces every β into the graph"])

    d.figure(
        "The BitLinear layer — the whole mechanism on one slide",
        os.path.join(FIGS, "bitlinear.png"),
        "Say it in this order: quantize the activations to the trained grid (γ), multiply by ±1 (which is an "
        "add or a subtract), rescale by β. The output is the quantize → multiply → dequantize of the same number.",
        standfirst="Draw this on a napkin. If you can, you can answer most of the questions you will get.",
        img_h=Inches(4.5))

    d.text(
        "The absmean quantizer, defended line by line",
        [
            ("code", "def absmean_binarize(w: np.ndarray):\n"
                     "    w = np.asarray(w, dtype=np.float64)\n"
                     "    alpha = w.mean()\n"
                     "    wc = w - alpha\n"
                     "    beta = np.abs(wc).mean() + 1e-6\n"
                     "    q = np.sign(wc)\n"
                     "    return q.astype(np.int8), float(beta), float(alpha), n_zero",
             {"size": 10.5}),
            ("kv", ("Why centre first?", "Binarization keeps only the sign, so the sign carries the entire signal. "
                                          "A trained kernel routinely has a nonzero mean; thresholding at zero would "
                                          "push most weights to the same sign and destroy the layer. Subtracting α "
                                          "re-centres so the split is balanced and informative.")),
            ("kv", ("Why β = mean|W − α|?", "It is the L1-optimal single scalar: for a fixed sign pattern q, the β "
                                             "minimising ‖W − βq‖₁ is the mean absolute deviation. The layer's output "
                                             "magnitude is preserved as well as one scalar can preserve it.")),
            ("kv", ("Why is α discarded?", "It is a rank-one perturbation — subtracting a constant from every entry "
                                            "adds a constant times the input sum. The network trained with the "
                                            "forward value q·β, so nothing is lost at export.")),
            ("kv", ("Per-tensor, not per-channel", "Deliberate. It makes the export re-binarization reproduce "
                                                    "bit-identical ±β on the same latents, and it costs one scale "
                                                    "constant per layer in hardware rather than d_model of them.")),
            ("kv", ("The +1e-6", "A division guard so β is never exactly zero on a degenerate kernel. Not a tuning knob.")),
        ],
        standfirst="This is the BitNet recipe (Wang et al., arXiv:2310.11453), implemented verbatim.",
        footer="Source: bnjettag/code/hgq2/bnhgq2/binarize.py:37-45")

    d.text(
        "The straight-through estimator — and the second stop_gradient",
        [
            ("h", "The forward pass IS the hardware"),
            ("code", "w = ops.cast(w, \"float32\")\n"
                     "alpha = ops.mean(w)\n"
                     "wc = w - alpha\n"
                     "beta = ops.mean(ops.abs(wc)) + eps\n"
                     "ws = wc / ops.stop_gradient(beta)      # bounded backward\n"
                     "q = ops.where(wc >= 0.0, 1.0, -1.0)    # strict bipolar, never 0\n"
                     "wq = ws + ops.stop_gradient(q - ws)    # STE: forward = q\n"
                     "return wq * beta                       # in {-beta, +beta}",
             {"size": 10.0}),
            ("p", "**The obvious stop_gradient.** Forward, `q - ws` evaluates as written, so `wq = q` exactly. "
                  "Backward, it contributes nothing, so the gradient flows through `ws` — the continuous "
                  "normalized weight — and never touches the sign. `sign()` has zero derivative almost "
                  "everywhere; without this, no gradient reaches the latents at all."),
            ("h", "The one nobody notices"),
            ("p", "`ws = wc / ops.stop_gradient(beta)` detaches β in the **denominator** but not in the final "
                  "`return wq * beta`. Work the derivative: the β cancels, and what is left is "
                  "(I − 1/n) + q·dβ/dw — bounded no matter how small β gets."),
            ("warn", "**The failure this fixed.** The upstream QKeras version divided by a live β, leaving a "
                     "1/β factor in the backward pass. When a kernel's centred weights collapse (β → 1e-6) the "
                     "gradient explodes by six orders of magnitude. That is what produced the A4 training NaN "
                     "(verified 2026-07-07). The rewrite removes it and leaves the forward value byte-identical."),
            ("note", "**Say it out loud as:** \"forward is the hardware; backward is a bounded surrogate; the "
                     "forward value did not change when we hardened the backward.\""),
        ],
        standfirst="Two stop_gradient calls. Only one of them is the STE. Know which is which.",
        cols=2,
        footer="Source: bnjettag/code/hgq2/bnhgq2/qat.py:43-65")

    d.text(
        "sign(0) = 0 would void the whole claim — so it is gated twice",
        [
            ("h", "Why zero is not allowed"),
            ("p", "Hardware binary has no zero state. A `{−1,+1}` weight is one bit and maps to an add or a "
                  "subtract in an adder tree. A three-valued `{−1,0,+1}` weight is **ternary** — it needs a "
                  "second bit, and it is a different thesis. One latent landing exactly on the mean would, if "
                  "`sign` returned 0, break the binary claim."),
            ("h", "Two code paths, two different rules — on purpose"),
            ("b", "**Training forward:** `ops.where(wc >= 0.0, 1.0, -1.0)` — strict bipolar, ties go to +1, can "
                  "never emit 0. The trained model is binary by construction."),
            ("b", "**Export:** `np.sign(wc)`, which *can* return 0, and counts every occurrence into "
                  "`total_sign_zeros`."),
            ("p", "That asymmetry is a trip-wire, not an inconsistency. If a latent ever sat exactly on the "
                  "mean the two paths would disagree, and the export gate fires instead of silently shipping "
                  "a ternary weight."),
            ("h", "The two independent gates"),
            ("code", "if cfg[\"quant\"][\"weight\"] == \"binary_absmean\":\n"
                     "    effs = qat.effective_weight_values(model)\n"
                     "    ok = all(len(v) == 2 and not (v == 0).any() for v in effs.values())\n"
                     "    assert ok, \"BINARY GATE FAILED at build\"",
             {"size": 10.0}),
            ("b", "**At training build**, before the first epoch: every bit-layer must have exactly two distinct "
                  "effective values, neither of them zero."),
            ("b", "**At export**: `convert_final.py` raises `SystemExit(\"STOP: … binary {-1,+1} claim would be void\")` "
                  "on any sign-zero. Same guard in `run_stage.py`."),
            ("good", "The rhetorical value: \"the weights are binary\" is not a description in this project. It is "
                     "an **enforced invariant**, checked by two separate mechanisms reading two separate "
                     "representations of the same tensors."),
        ],
        standfirst="A referee's fastest attack on a 1-bit paper is 'are you sure it isn't ternary?'. Have this ready.",
        cols=2,
        footer="Sources: bnhgq2/binarize.py:44,79-82 · bnhgq2/qat.py:63 · bnhgq2/train.py:336-340 · convert_final.py:434-437")

    d.text(
        "What is NOT binary — and why it matters more than it sounds",
        [
            ("h", "Binarization applies to kernels. Full stop."),
            ("p", "Anything that multiplies two **activations** has no weight in it, so binarization is not even "
                  "a question there. In this graph that is exactly two operations per encoder block:"),
            ("b", "the **scores**, `\"bthe,bshe->bhts\"` on [q, k] — that is Q·Kᵀ"),
            ("b", "the **context**, `\"bhts,bshe->bthe\"` on [attn, v] — that is softmax·V"),
            ("p", "They are built with `QEinsum`, take activation-quantizer configs on *both* operands, and carry "
                  "no weight-quantizer config at all. At N = 8 they are 8,192 multiplies per jet."),
            ("h", "Also not binary, each for a stated reason"),
            ("b", "**Biases** are float in every arm (matching the QKeras reference)."),
            ("b", "**The positional table** is a learned additive constant that folds exactly into `input_proj`'s "
                  "bias table at export — it costs nothing at inference."),
            ("b", "**β** is a per-layer fixed-point scale constant, implemented as a shift-add affine."),
            ("b", "**ReLU, the residual adds, mean pooling** carry no weights at all."),
            ("note", "**The honest sentence for the poster:** \"17,664 kernel weights are binary. Nothing else in "
                     "the model is a weight.\""),
            ("warn", "**This is also why the EBOPs advantage shrinks with N** — 5.28× at N = 8 down to 2.14× at "
                     "N = 64. The act×act attention terms cost b_a·b_a regardless of weight precision and grow "
                     "as N². It looks like a weakening result until you say why. Volunteer the explanation."),
        ],
        standfirst="\"Do you binarize the attention too?\" — No. There is nothing there to binarize.",
        cols=2,
        footer=f"Sources: bnhgq2/qat.py:516-529 · bnjettag/results/ebops.md:15-17 · {RESEARCH} §5")

    d.text(
        "Norm-free — the decision that cost the most and taught the most",
        [
            ("h", "What LayerNorm would have bought"),
            ("p", "A LayerNorm is scale-invariant: normalising destroys any positive scalar multiplying its input. "
                  "β is exactly such a scalar. In a normed graph most β values can be disposed of for free — "
                  "`binarize.py` encodes four ways: `score_fold` (β_q·β_k rides into the softmax scale), "
                  "`ln_killed` (β_v is eaten by the next LayerNorm), `bias_fold` (fc1's β becomes b/β), and "
                  "`explicit` (the sites that reach a residual add or the logits). That is 2L+2 = 6 affines."),
            ("h", "What Round 14 chose instead"),
            ("p", "`arch.norm: \"none\"` in all 20 configs. `norm()` becomes an identity passthrough — "
                  "parameter-free, DSP-free, and the whole SubLN HLS kernel disappears. But now nothing absorbs "
                  "**any** β, so `fold_class` short-circuits to `\"explicit\"` for every layer: **6L+3 = 15 affines** "
                  "at L = 2, each a shift-add placed directly after its own matmul."),
            ("good", "**Why the exactness argument holds.** β > 0 by construction (a mean of absolute values plus "
                     "1e-6), and ReLU is positively homogeneous — so pulling a positive scalar through a ReLU is "
                     "exact, not approximate. The einsums are linear, so pulling it through them is exact too."),
            ("h", "And this is what made the export faithful"),
            ("p", "With β restored at source, every downstream stream sits at its true trained scale — which is "
                  "what lets the trained activation grids be copied in **verbatim**, saturation included. "
                  "The previous exporter tried to carry β downstream and re-derive those grids. Part V tells "
                  "that story; it scored GATE1 0.839."),
            ("note", "**The defensible one-liner:** \"We removed the norms, which means we pay for every scale "
                     "explicitly — and paying for them explicitly is what made the exported FPGA model provably "
                     "the same network we trained.\""),
        ],
        standfirst="Removing LayerNorm is why every β has to be implemented — and why the export can be verified.",
        cols=2,
        footer=f"Sources: bnhgq2/binarize.py:16-34 · bnhgq2/qat.py:406-409 · bnhgq2/build.py:185-191 · {RESEARCH} §6.1")

    # ------------------------------------------------------------ part III
    d.divider(
        "Part III", "The model",
        "A small transformer, deliberately. Two encoder layers, width 32, and every linear layer binary.",
        ["The architecture, block by block, and what each colour on the schematic means",
         "17,664 binary weights — counted by hand so you can reproduce the number live",
         "The five arms, and the fact that they differ by one JSON key",
         "The training recipe, and why every hyperparameter is frozen rather than tuned"])

    d.figure(
        "The architecture",
        os.path.join(FIGS, "architecture.png"),
        "Two encoder blocks, model width 32, four heads, feed-forward width 64, no normalization layers, "
        "learned positional encoding, mean pooling over constituents (which is what makes the tagger "
        "permutation-invariant), five-class head. Blue = ±1 weights; orange = activation-only arithmetic; "
        "grey = no weights.",
        standfirst="Read from the config, not from memory: d_model 32, 2 layers, 4 heads, FFN 64, norm none.",
        img_h=Inches(4.3),
        footer="Source: docs/figures/bnjettag-architecture.tex, drawn from bnhgq2/qat.py build_qat_model and configs/r14-l1x3-n8-w1a8.json")

    d.text(
        "17,664 binary weights, counted by hand",
        [
            ("h", "The arithmetic — reproduce this live if asked"),
            ("kv", ("input_proj", "(F, D) = 3 · 32 = **96**")),
            ("kv", ("per block", "W_q, W_k, W_v each (D, H, E) = 32·4·8 = 1,024;  W_O (H, E, D) = 4·8·32 = 1,024;\n"
                                  "fc1 (D, FFN) = 32·64 = 2,048;  fc2 (FFN, D) = 64·32 = 2,048  →  **8,192 per block**")),
            ("kv", ("two blocks", "**16,384**")),
            ("kv", ("head", "head_fc1 (D, D) = 32·32 = 1,024;  head_fc2 (D, C) = 32·5 = **160**")),
            ("kv", ("total", "96 + 16,384 + 1,024 + 160 = **17,664**, in 15 layers (13 einsum + 2 head dense)")),
            ("good", "That 13 + 2 split is exactly the `einsum_dense` ×13 plus 2 head `dense_latency` split the "
                     "C-synthesis instance table reports — the count is checkable in the firmware."),
            ("h", "The fact people miss"),
            ("warn", "**T never appears in any kernel shape.** 17,664 is the same at N = 8 and at N = 64. What N "
                     "changes is how many times each weight is *applied*. At N = 8 the 16,480 token-wise weights "
                     "fire once per particle (16,480 × 8 = 131,840) and the 1,184 head weights fire once after "
                     "pooling: **133,024 weight multiplies per jet**."),
            ("note", "**Why so small?** It has to share a trigger FPGA with everything else, and the "
                     "sub-microsecond transformer literature works at the same scale. The point of the work is "
                     "the binary mapping, not model size. Total trainable parameters of the N = 16 W1A8 model: "
                     "**19,169** (from the pre-launch smoke test)."),
        ],
        standfirst="A number you should be able to derive on a whiteboard, not just recite.",
        cols=2,
        footer="Sources: bnhgq2/qat.py:483-553 · configs/r14-l1x3-n8-w1a8.json:4-19 · experiment-log 2026-08-01")

    d.table(
        "The five arms — and the diff that proves they are controlled",
        ["Arm", "`quant.weight`", "`quant.act_bits`", "What it is"],
        [
            ["FP32", "`\"none\"`", "32 (inert)", "Float weights, float activations — the accuracy ceiling"],
            ["W8A8", "`\"int8_absmax\"`", "8", "8-bit weights and activations — the conventional baseline the field would deploy"],
            ["**W1A8**", "`\"binary_absmean\"`", "8", "**THE THESIS POINT** — {−1,+1} weights, 8-bit activations"],
            ["W1A6", "`\"binary_absmean\"`", "6", "Same binary weights, activations narrowed to 6 bits"],
            ["W1A4", "`\"binary_absmean\"`", "4", "Same binary weights, activations narrowed to 4 bits"],
        ],
        standfirst="Two orthogonal axes crossing at W1A8: weight precision going up, activation precision going down.",
        widths=[0.13, 0.24, 0.15, 0.48], size=12.5, emph=[2],
        notes=[
            ("good", "**The strongest experimental-control statement in the project, and it is verifiable with "
                     "`diff`.** `r14-l1x3-n8-w8a8.json` and `r14-l1x3-n8-w1a8.json` differ in `name` plus "
                     "**exactly one scientific key**: `quant.weight`. Not a re-tuned learning rate, not a "
                     "different depth, not a different early-stopping budget. Same for w1a8 vs w1a6 (`act_bits` "
                     "alone) and n8 vs n64 (`n_part` alone). Say the diff out loud — it lands harder than any "
                     "prose about experimental control."),
            ("note", "All 20 configs come out of one generator function, `gen_r14.py:make(n_part, variant)`, which "
                     "substitutes exactly three things into one dictionary literal. Cross 5 arms × 4 values of N "
                     "and you have the twenty configs, and the 60 runs at 3 seeds each."),
        ],
        footer="Sources: configs/gen_r14.py:15,28-30 · verified by diff of the shipped config files")

    d.text(
        "The training recipe — and why you defend the policy, not the values",
        [
            ("h", "What the code actually builds"),
            ("kv", ("Optimizer", "Adam, β₁ = 0.9 (hardcoded), **β₂ = 0.98**, weight_decay 0.01")),
            ("kv", ("Gradient clip", "**clipvalue = 1.0**, per-element (`clip_mode: \"value\"`)")),
            ("kv", ("Schedule", "peak LR **2e-05**, 1 warmup epoch + 100 epochs of **linear** decay (power 1.0)")),
            ("kv", ("Length", "101 epochs, batch 256, early stop patience **15** on `val_macro_auc`")),
            ("kv", ("Loss", "CategoricalCrossentropy(from_logits=True) — the model emits logits, so the AUC "
                            "callback softmaxes them itself")),
            ("h", "The three choices worth explaining"),
            ("b", "**β₂ = 0.98, not Keras's 0.999.** The latent weight moves smoothly but the *effective* weight "
                  "flips sign discontinuously, so gradient statistics are far less stationary than in a float "
                  "network. A 0.999 window averages ~1000 steps and lags the flips; 0.98 is ~50 steps and tracks them."),
            ("b", "**LR 2e-05 — an order of magnitude below normal for a model this small.** The effective weight "
                  "is a sign, and signs move discontinuously. A large step flips many latents past zero at once, "
                  "and the STE gradient that motivated the step was computed for the pre-flip network. Small LR "
                  "keeps the flip rate low enough that the gradient stays informative. The recipe compensates "
                  "with length, not step size."),
            ("b", "**clipvalue, not global_clipnorm — a real failure, not a preference.** A global norm must sum "
                  "squared gradients over every tensor before rescaling, and that sum overflows float32 on this "
                  "stack; the clip that was meant to save you produces inf, then NaN. The W1A4 arm was the "
                  "canary. Per-element clipping never forms the sum. The config still carries `clipnorm: 1.0` "
                  "next to it so the losing option stays visible and hashed."),
            ("warn", "**If asked \"why 2e-05?\", do not defend the value — defend the policy.** It was not tuned "
                     "for Round 14. Every arm uses the byte-identical `train` block, inherited verbatim from the "
                     "earlier r8-small recipe. Per-arm tuning would have made each arm slightly better and every "
                     "comparison uninterpretable. The honest caveat to volunteer: this makes FP32 a "
                     "**matched-recipe** baseline, not a best-possible float model, so the measured gap is an "
                     "upper bound on what binarization costs under this recipe."),
            ("note", "**One detail to get right:** with `warmup_epochs: 1`, epoch 0 returns `lr · (0+1)/1` — the "
                     "full peak LR. The single warmup epoch is a structural placeholder and warms nothing up. "
                     "Describe the schedule as \"peak from step one, then 100 epochs of linear decay to 1%\"."),
        ],
        standfirst="Every knob is frozen. That is the experimental design, not laziness.",
        cols=2,
        footer="Sources: bnhgq2/train.py:211-219,342-352 · configs/r14-l1x3-n16-w1a8.json:34-46 · train.py module docstring (which is stale — the config wins)")

    # ------------------------------------------------------------- part IV
    d.divider(
        "Part IV", "The code",
        "How the implementation actually works — the files, the functions, and the design decisions "
        "you would have to defend if someone opened the repository during your talk.",
        ["The repository map, and the one rule that governs it",
         "bnhgq2/: the QAT library — binarize, qat, train, data, config, store",
         "The export path — extract, build, port, convert, verify, gold",
         "The evaluation path — roc_final, export_roc_eval, uncertainty, working points",
         "The hardware path — convert_final, fold_r14n8, mulder_csynth, parse_csynth, parse_families"])

    d.table(
        "The repository, in the order you would read it",
        ["Path", "What lives there"],
        [
            ["`RESEARCH.md`", "**The living record.** Verified numbers only. §7 maps every claim to its source file."],
            ["`DATASET.md`", "The dataset, its splits, and how to fetch it."],
            ["`bnjettag/code/hgq2/bnhgq2/`", "The QAT library: binarization, the model builder, training, data, export."],
            ["`bnjettag/code/hgq2/`", "The drivers: `run_stage.py`, `roc_final.py`, `convert_final.py`, `fold_r14n8.py`, the parsers."],
            ["`bnjettag/code/hgq2/configs/`", "The 20 Round-14 config JSONs and their generator."],
            ["`bnjettag/code/jobs/training/variants/`", "The 60 Nautilus job YAMLs, their generators, the launcher, the ConfigMap builder."],
            ["`bnjettag/code/plots/`", "Figure generation — including this deck's builder."],
            ["`bnjettag/results/r14/`", "The parsed tables of record: AUC, EBOPs, uncertainty, HLS, the fit ladder."],
            ["`bnjettag/results/synthesis/runs/`", "Per-article export / C-sim / synthesis stores, keyed by config hash."],
            ["`bnjettag/roc-results/r14/`", "The raw `.npz` ROC arrays every AUC is recomputed from."],
            ["`docs/infrastructure/`", "How to run things: Nautilus, mulder, the W&B layout, the round runbook."],
            ["`_attic/`", "Everything pre-Round-14, moved intact 2026-08-13. **Out of scope — never quote it.**"],
        ],
        standfirst="Start at RESEARCH.md. Everything else exists to make its numbers checkable.",
        widths=[0.30, 0.70], size=11.5,
        notes=[("warn", "**The rule that governs all of it:** never quote a number from memory. Read it from "
                        "RESEARCH.md §7, or recompute it from the `.npz` or the raw csynth report. "
                        "RESEARCH.md §7 ends: *\"Anything not traceable to this table is not a project claim.\"*")],
        footer="Source: README.md · RESEARCH.md §7")

    d.text(
        "bnhgq2/qat.py — how a BitLinear layer is actually built",
        [
            ("h", "There is no from-scratch BitLinear class"),
            ("p", "`BitQEinsumDense` subclasses HGQ2's `QEinsumDense`; `BitQDense` subclasses `QDense`. Each "
                  "overrides **exactly one method**: `call()`. Everything else — the input activation quantizer, "
                  "the bias quantizer, the EBOPs bookkeeping, serialization, the hls4ml handler that recognises "
                  "the parent class — is inherited untouched."),
            ("code", "def call(self, inputs, training=None):\n"
                     "    qkernel = bitnet_binary_ste(self._kernel)\n"
                     "    if self.enable_iq:\n"
                     "        inputs = self.iq(inputs, training=training)\n"
                     "    x = ops.einsum(self.equation, inputs, qkernel)\n"
                     "    if self.bias is not None:\n"
                     "        x = x + self.bq(self.bias, training=training)",
             {"size": 10.0}),
            ("good", "**Why that matters under pushback.** The binary claim is a change to ONE tensor in the "
                     "forward pass, not a bespoke re-implementation of a transformer that might quietly differ "
                     "from the baseline. FP32, W8A8 and the W1A* arms are the same graph builder with a "
                     "different class and a different weight-quantizer config. That is what makes the accuracy "
                     "deltas attributable to quantization rather than to architecture."),
            ("h", "One consequence to state out loud"),
            ("p", "The layer stores **latent float32 kernels** as its trainable variables. The ±1 values are "
                  "never a stored parameter during training — they are recomputed from the latents on every "
                  "single forward pass."),
            ("warn", "**The trap in this file.** `_binary_kq()` attaches a 1-bit KBI weight quantizer to every "
                     "binary layer — and it quantizes nothing, because the forward already returned ±β before "
                     "that quantizer would see it. Its only job is declarative: to make EBOPs and hls4ml "
                     "*report* 1 bit. Reading it as the operative quantizer leads to the opposite of the truth, "
                     "since a stock 1-bit KBI actually produces the ternary grid {−1,0,+1}."),
        ],
        standfirst="The whole binary path is one substitution inside one method.",
        cols=2,
        footer="Sources: bnhgq2/qat.py:71-89, 92-108, 422-455, 483")

    d.text(
        "What HGQ2 gives us, and what this repo had to write",
        [
            ("h", "HGQ2 supplies"),
            ("b", "Quantized layer classes: `QEinsumDense`, `QDense`, `QSoftmax`, `QGlobalAveragePooling1D`, `QEinsum`."),
            ("b", "The `QuantizerConfig` system with KBI (signed / total bits / integer bits) and KIF parametrizations."),
            ("b", "**Trainable** quantizer parameters with gradient surrogates."),
            ("b", "**EBOPs** as a synthesis-free cost proxy, computed inside the graph."),
            ("b", "The hls4ml frontend that turns all of it into HLS C++."),
            ("h", "What HGQ2 does NOT supply — and the probe that proved it"),
            ("warn", "A stock HGQ2 fixed-point weight quantizer configured at 1 bit rounds latent floats onto the "
                     "grid **{−1, 0, +1}**. Probe T1 found it collapsed **4096/4096** latents to zero. That is "
                     "ternary — and at the observed collapse it is worse than ternary, it is a dead layer. "
                     "This is recorded as a measured probe, not an opinion."),
            ("p", "So this repository wrote: `bitnet_binary_ste` (the binary STE), `BitQEinsumDense` / `BitQDense`, "
                  "`binarize.py` (the export-side re-binarization and the β fold bookkeeping), `PSubLN` plus its "
                  "full hls4ml extension stack in `subln.py`, `calibrate_activations`, and all the gates."),
            ("note", "**Useful framing for a question about novelty:** we did not re-implement a quantization "
                     "framework. We added the one path a general framework could not give us, and measured why "
                     "the general path fails."),
        ],
        standfirst="Know the boundary. It is exactly where the interesting engineering is.",
        cols=2,
        footer="Sources: bnhgq2/qat.py:7-16, 30-33, 228-232")

    d.text(
        "The activation side — MSE calibration, then a grid that trains with the model",
        [
            ("h", "Step 1: calibrate"),
            ("p", "Every quantized layer gets a signed fixed-point input quantizer. `calibrate_activations` runs "
                  "one forward pass over a real batch (`calib_n: 8192`) and, for every tap site, picks the "
                  "integer-bit count *i* that **minimises the MSE** of the static grid against the true "
                  "activations, sweeping *i* over 0 … act_bits−2 so at least one fractional bit always survives."),
            ("kv", ("Why MSE, not max+margin?", "The docstring records the counterexample: max+margin over-ranges "
                                                 "low-bit grids, and at A4 it leaves f = 0 — an integer-only grid. "
                                                 "MSE trades dynamic range for fractional resolution, which is the "
                                                 "right trade when you have 16 levels.")),
            ("h", "Step 2: let it move"),
            ("p", "A grid calibrated once and frozen goes stale, because activation distributions drift during "
                  "training. All 20 configs set `quant.act_calib: \"trainable\"`: the total width is **pinned** by "
                  "a `Constant(act_bits − 1)` constraint while the integer/fractional split is left "
                  "gradient-trainable under `MinMax(0, act_bits − 2)`. The width stays exactly act_bits — so \"A4\" "
                  "still means 4 bits — while the grid slides to follow the distribution."),
            ("code", "QuantizerConfig(\"kbi\", \"datalane\", k0=1, b0=act_bits - 1, i0=int(i0),\n"
                     "                round_mode=\"RND_CONV\", overflow_mode=\"SAT\",\n"
                     "                trainable=True, heterogeneous_axis=(),\n"
                     "                bc=Constant(act_bits - 1),          # pin width -> fixed act_bits\n"
                     "                ic=MinMax(0, max(0, act_bits - 2)))  # f = b - i >= 1",
             {"size": 9.6}),
            ("h", "Two choices to defend"),
            ("b", "**KBI rather than KIF**, because KIF carries independent i and f with no fixed total, so the "
                  "width could drift and \"A4\" would stop meaning 4 bits."),
            ("b", "**SAT rather than HGQ2's WRAP default**, because SAT clips exactly the way the exported "
                  "hardware grid clips. The checkpoint IS the deployable model: **train == deploy**."),
        ],
        standfirst="This is the second axis of the thesis — how far activations can be pushed.",
        cols=2,
        footer="Sources: bnhgq2/qat.py:244-263, 411-417, 569-602 · configs/r14-l1x3-n16-w1a8.json:30")

    d.text(
        "The data pipeline — four steps, and the order is load-bearing",
        [
            ("h", "What `load_train_data` does, in this order"),
            ("b", "**1.** Find the p_T column by name suffix `_pt`."),
            ("b", "**2.** `np.argsort(-pT, axis=1, kind=\"stable\")` — sort constituents by *descending* p_T, stably."),
            ("b", "**3.** Truncate to `const[:, :n_part, :]`."),
            ("b", "**4.** *Only then* slice the feature subset."),
            ("code", "pt_col = next((i for i, n in enumerate(pnames) if n.endswith(\"_pt\")), None)\n"
                     "if pt_col is not None:\n"
                     "    order = np.argsort(-const[:, :, pt_col], axis=1, kind=\"stable\")\n"
                     "    const = np.take_along_axis(const, order[:, :, None], axis=1)\n"
                     "const = const[:, :n_part, :]",
             {"size": 10.0}),
            ("kv", ("Why sort by p_T?", "The model has no notion of which constituent is which except a learned "
                                         "positional encoding, and a trigger reads out the hardest constituents "
                                         "first. Top-N by p_T is the physically meaningful truncation — you keep "
                                         "the energy and drop the soft junk.")),
            ("kv", ("Why *stable*?", "Ties in p_T (common in quantized detector readout) resolve to the original "
                                      "file order, so the ordering reproduces across machines and NumPy versions.")),
            ("kv", ("Why slice features last?", "So the particle ordering is identical regardless of the feature "
                                                 "subset. A 3-feature run sees the same particles in the same slots "
                                                 "as a 16-feature run would. That kills the confound where changing "
                                                 "the inputs also silently changes which constituents are present.")),
            ("warn", "**`feature_indices` matches by EXACT suffix and raises unless each resolves uniquely.** The "
                     "docstring names the hazard: `pt` ≠ `ptrel`, `etarel` ≠ `etarot`. A sloppy substring match "
                     "would train on the wrong three columns, every AUC in the campaign would be quietly wrong, "
                     "and nothing would crash."),
        ],
        standfirst="The 3-feature cut and the N sweep are genuinely independent knobs — by construction.",
        cols=2,
        footer="Sources: bnhgq2/data.py:20-32, 35-66 · bnhgq2/train.py:32-69")

    d.text(
        "Input standardization — and the honest scoping of it",
        [
            ("h", "What happens"),
            ("code", "def input_std_stats(X, eps=1e-6):\n"
                     "    mu = X.mean(axis=(0, 1))\n"
                     "    sigma = X.std(axis=(0, 1))\n"
                     "    sigma = np.where(sigma < eps, 1.0, sigma)\n"
                     "    return mu.astype(\"float32\"), sigma.astype(\"float32\")",
             {"size": 10.5}),
            ("p", "One mu and one sigma **per feature** — three of each — taken over (jets, constituents). "
                  "Computed on `Xtr` **after** the validation carve, never on the full array; the validation set "
                  "is then standardized with the training set's statistics. Textbook leakage hygiene."),
            ("h", "The question you will get"),
            ("warn", "*\"The FPGA can't z-score its inputs at 40 MHz. Isn't that free accuracy the hardware can't "
                     "deliver?\"*"),
            ("good", "**The answer is scoped, and the scope is written into the artifact.** `input_std.json` "
                     "carries the literal strings `\"computed_from\": \"train split only\"` and `\"contract\": "
                     "\"hardware receives standardized inputs (offline preprocessing)\"`. Standardization is "
                     "*declared* to be upstream of the synthesized block. The mu/sigma travel with the checkpoint "
                     "so evaluation and hls4ml conversion apply identical numbers. What the resource counts cover "
                     "is the network **after** that transform, and we do not claim the subtract-and-scale is "
                     "inside the DSP/LUT figures."),
            ("h", "Why standardize at all"),
            ("b", "The three L1 features have wildly different natural scales — p_T in GeV against dimensionless "
                  "η_rel/φ_rel of order 0.1 (the range of per-feature standard deviations across the 16 stored "
                  "features is about **2,979×**)."),
            ("b", "The architecture is **norm-free**, so nothing downstream rescues an unbalanced input."),
            ("b", "The activation quantizers use a **static per-tensor** grid. If input scales differ by orders "
                  "of magnitude, one fixed grid cannot cover both and you burn bits on dynamic range instead "
                  "of resolution."),
        ],
        standfirst="Say the contract, not the cost estimate. The contract is what is written in the file.",
        cols=2,
        footer="Sources: bnhgq2/train.py:304-320 · bnhgq2/data.py:77-88 · DATASET.md:67-69")

    d.text(
        "run_stage.py — the driver, and why `train` sits outside the chain",
        [
            ("code", "STAGES = {\n"
                     "    \"train\": stage_train,\n"
                     "    \"extract\": stage_extract,\n"
                     "    \"calibrate\": stage_calibrate,\n"
                     "    \"build\": stage_build,\n"
                     "    \"verify\": stage_verify,\n"
                     "    \"ebops\": stage_ebops,\n"
                     "    \"convert\": stage_convert,\n"
                     "}\n"
                     "ORDER = [\"extract\", \"calibrate\", \"build\", \"verify\", \"ebops\", \"convert\"]",
             {"size": 10.0}),
            ("p", "`train` is deliberately **not** in `ORDER`. `main` short-circuits on it — *\"TRAIN is a "
                  "standalone from-scratch stage (no extract/calibrate/build preamble)\"* — runs it, and returns."),
            ("h", "Why, and what it explains"),
            ("p", "The six-stage chain was written for the QKeras era: take a trained *float* checkpoint, extract "
                  "its weights, binarize them, calibrate activation grids against a numpy gold reference, rebuild "
                  "an equivalent HGQ2 model, verify it through two gates, convert. Round 14 changed the premise: "
                  "training happens **natively in HGQ2**, so — as `train.py`'s docstring says — *\"the trained "
                  "model IS (essentially) the hardware model\"*. There is nothing to extract and re-port. That is "
                  "why `train` is a peer of the chain rather than its first link."),
            ("h", "Two behaviours worth being able to explain"),
            ("b", "**Single-stage entry rebuilds context.** Asking for `verify` alone replays `extract`, "
                  "`calibrate` and `build` first, because those are cheap and idempotent and populate the "
                  "in-memory context later stages read."),
            ("b", "**The store write for `train` is non-fatal.** `model_best.keras` plus `train_meta.json` plus "
                  "W&B are the source of truth; the local store JSON is an analysis convenience and *must never "
                  "fail the training run*. A GPU-hour-expensive run must not die because a JSON write hit a "
                  "read-only path."),
        ],
        standfirst="Seven stages, six in the chain, and one that stands alone for a reason worth knowing.",
        cols=2,
        footer="Sources: run_stage.py:229-269 · bnhgq2/train.py:5")

    d.text(
        "Why the knobs live in a JSON config — the answer is auditability",
        [
            ("code", "def cfg_hash(cfg: dict) -> str:\n"
                     "    \"\"\"Stable 8-hex-char key of the scientific content.\"\"\"\n"
                     "    clean = {k: v for k, v in cfg.items() if not k.startswith(\"_\")}\n"
                     "    blob = json.dumps(clean, sort_keys=True, separators=(\",\", \":\")).encode()\n"
                     "    return hashlib.sha256(blob).hexdigest()[:8]",
             {"size": 10.0}),
            ("p", "`store.write_stage` files every stage's result under "
                  "`results/hgq2/runs/<cfg_hash>/<stage>.json`. So a resource number, an EBOPs number and a "
                  "verification gate all sit in a directory **named after the exact bytes of the config that "
                  "produced them**. Change `act_bits` from 8 to 6 and you get a different directory — you cannot "
                  "silently overwrite a result with a different model."),
            ("good", "**The one-line answer:** a config is the model's identity, and identity has to be hashable. "
                     "An environment variable is invisible to `json.dumps`, so it could change the science "
                     "without changing the hash."),
            ("h", "The symmetry the code preserves"),
            ("p", "The env vars that do exist — `BNHGQ2_TRAIN_DATA`, `BNHGQ2_OUT_ROOT`, `BNHGQ2_STORE` — override "
                  "only *where things live on a given machine*, never what the model is. `config.py:3` states the "
                  "rule outright: *\"The pipeline never reads architecture or precision from anywhere else.\"*"),
            ("note", "**A related discipline worth knowing.** Every optional knob is read as "
                     "`cfg[\"quant\"].get(key, default)` where the default reproduces the prior behaviour exactly — "
                     "\"a config WITHOUT this key is byte/hash-unchanged.\" That is why the Round-15 gamma arms "
                     "needed no control *run*: with the knob absent, the code path is bit-for-bit the one that "
                     "produced the published R14 checkpoints, so those checkpoints **are** the control."),
        ],
        standfirst="\"What does a config file buy you over command-line flags?\" — This.",
        cols=2,
        footer="Sources: bnhgq2/config.py:1-54 · bnhgq2/store.py:33-47 · configs/gen_r15_gamma.py:13-18")

    d.text(
        "roc_final.py — how every AUC is produced",
        [
            ("h", "Macro one-vs-rest, spelled out"),
            ("code", "def macro_ovr_auc(y_onehot, scores):\n"
                     "    from sklearn.metrics import roc_auc_score\n"
                     "    per = [float(roc_auc_score(y_onehot[:, c], scores[:, c]))\n"
                     "           for c in range(y_onehot.shape[1])]\n"
                     "    return float(np.mean(per)), per",
             {"size": 10.5}),
            ("p", "Five binary problems — \"is this jet class c?\" — each an ordinary AUC, then an **unweighted** "
                  "mean. Unweighted matters: the dataset is balanced, so weighting would change nothing, but "
                  "saying it removes an ambiguity a referee would probe."),
            ("h", "The `.npz` arrays are the artifact — not the AUC"),
            ("code", "def runs_from_npz(files):\n"
                     "    \"\"\"Load npz's and RECOMPUTE AUC from the stored arrays.\"\"\"\n"
                     "    ...\n"
                     "    macro, per = macro_ovr_auc(d[\"y\"], d[\"score\"])\n"
                     "    m[\"auc\"] = macro          # overwrites the stored scalar",
             {"size": 10.0}),
            ("p", "Each file holds exactly three keys: `y` (260000, 5) one-hot float32, `score` (260000, 5) "
                  "softmax float32, and a JSON `meta` string. The AUC inside `meta` is **never** the number "
                  "quoted — every consumer recomputes from the arrays. That is what makes the numbers "
                  "falsifiable by anyone holding the file: there is no path by which a stale scalar propagates "
                  "into a report."),
            ("good", "**A guard worth mentioning.** The heads emit logits, so `eval_one` applies softmax exactly "
                     "once, in float64. If a checkpoint ever already emitted a probability simplex, "
                     "re-softmaxing would compress the scores — so there is an explicit check on row sums and "
                     "minimum value that uses the raw output and warns."),
            ("warn", "**The size gate.** `load_data_checked` raises unless the loaded set has exactly "
                     "`expect_n = 260000` rows: *\"refuse to evaluate a wrong/partial split.\"*"),
        ],
        standfirst="The scalar is never the artifact. The arrays are.",
        cols=2,
        footer="Sources: roc_final.py:148-167, 230-266 · verified live: n8 W1A8-s3 claimed 0.8724, recomputed 0.872410 ✓")

    d.text(
        "uncertainty_r14.py — how a difference becomes a claim",
        [
            ("h", "Two independent noise sources, added in quadrature"),
            ("kv", ("σ_seed", "Training variance. For a difference of two seed means over 3 seeds each, "
                              "Var(A)/3 + Var(B)/3, each a ddof=1 sample variance.")),
            ("kv", ("σ_boot", "Finite-test-set uncertainty at fixed weights: draw 260,000 indices with "
                              "replacement, **score both models on the same resampled indices**, 200 times.")),
            ("code", "def paired_boot_gap(yA, sA, sB, n_boot, rng, block=None):\n"
                     "    for b in range(n_boot):\n"
                     "        idx = rng.integers(0, n, n)\n"
                     "        gaps[b] = (macro_auc_fast(yA[idx], sA[idx], None)\n"
                     "                 - macro_auc_fast(yA[idx], sB[idx], None))\n"
                     "    return float(gaps.mean()), float(gaps.std(ddof=1))",
             {"size": 9.8}),
            ("p", "**Paired** is the load-bearing word. A resample that happens to contain unusually easy jets "
                  "makes *both* models look better, so jet-level difficulty cancels in the difference and the "
                  "bootstrap measures only how much the **gap** wobbles. An unpaired bootstrap would report a "
                  "far larger and mostly irrelevant σ."),
            ("h", "The verdict rule"),
            ("p", "σ_total = √(σ_seed² + σ_boot²), then a plain sigma count: **RESOLVED** above 2σ, TENTATIVE "
                  "between 1σ and 2σ, UNRESOLVED below 1σ. The RNG is seeded (`default_rng(20260802)`) so the "
                  "pass reproduces."),
            ("note", "**A shortcut to concede if challenged.** The bootstrap runs on the seed-1 pair only, not "
                     "all three. Justification: test-set noise is model-pair specific but stable across seeds. "
                     "The numbers bear it out — σ_boot lands in 0.00012–0.00027 across all 16 comparisons, so it "
                     "never changes a verdict, because σ_seed is 3× to 60× larger."),
        ],
        standfirst="This file decides which differences you are allowed to claim out loud.",
        cols=2,
        footer="Sources: uncertainty_r14.py:70-133 · bnjettag/results/r14/uncertainty_r14.md")

    d.text(
        "convert_final.py — the export driver, and its flags",
        [
            ("h", "What export means, and why it is fallible"),
            ("p", "The trained model and the firmware model are the same function computed by different "
                  "machinery; export is the re-factoring between them. hls4ml cannot convert the training graph "
                  "as-is — the training layers hold latent FP32 kernels and apply β as a fused in-layer scale, "
                  "while hls4ml's HGQ2 frontend reads only (k, i, f) plus SAT/RND off each quantizer. So export "
                  "rebuilds the graph out of primitives hls4ml handles: `QEinsumDense` with pure ±1 kernels, "
                  "`QEinsum` for the two act×act contractions, `QSoftmax`, and frozen `QBatchNormalization` "
                  "affines for β."),
            ("warn", "**Every one of those substitutions is a chance to change the function, and nothing in the "
                     "toolchain tells you if you got it wrong.** The graph still converts, still synthesizes, "
                     "still produces plausible logits. That is why the pipeline has two numeric gates rather "
                     "than a code review."),
            ("good", "**The framing for a skeptic:** *\"we do not assert the export is faithful, we measure it, "
                     "per article, and store the measurement next to the synthesis project.\"*"),
            ("h", "The proof that the exported weights are the trained weights"),
            ("p", "`weight_export_exactness` recomputes the QAT forward's own `bitnet_binary_ste(latent)` and "
                  "compares it to β·q element-wise. Measured **2.98e-08** on both shipped articles — one float32 "
                  "ULP at that magnitude."),
            ("h", "The flag that looks like a hack"),
            ("p", "`--force-softmax-out-bits` exists because `quant.softmax_out_bits` is **inert for an "
                  "already-trained checkpoint**: HGQ2 quantizer k/i/f values are Keras variables loaded from the "
                  "file, so a config-driven study would have synthesized the 10-bit grid and silently reported "
                  "\"narrowing does nothing.\" Applying it to the **export only** leaves the QAT model as an "
                  "untouched reference, which turns GATE1 into a free post-training-quantization probe of "
                  "exactly what the narrowing costs, while GATE2 stays bit-exact."),
            ("warn", "**Builds made with that flag are characterization builds.** They carry no fidelity claim "
                     "and never enter an accuracy table. That is why fit-ladder row 5 is labelled structure-only."),
        ],
        standfirst="943 lines. The three things to know are: what it rebuilds, what it measures, and one flag.",
        cols=2,
        footer="Sources: convert_final.py:2-38, 541-553, 659-684 · runs/38a20c62/w1a8-s3-r14n8/export_verify.json")

    d.text(
        "fold_r14n8.py — the fold that works, and the one that did not",
        [
            ("h", "Why the reuse factor was inert"),
            ("p", "The obvious question is \"the design is 184% of the device — just raise the reuse factor.\" "
                  "The measured answer: RF did nothing. hls4ml's `io_parallel` emit puts a bare "
                  "`#pragma HLS PIPELINE` on the whole top-level function, and Vitis **fully unrolls every loop "
                  "inside a pipelined region**, overriding any unroll factor or allocation limit beneath it."),
            ("warn", "The proof is brutal: an n16 build with parallelization factor 8 came back with instruction "
                     "counts identical to the unfolded baseline (21,295,573 then 7,416,592) and was killed at 32 "
                     "minutes."),
            ("h", "The lever that works"),
            ("p", "Replace the region rather than fight it: model-level `PipelineStyle: 'dataflow'` swaps the "
                  "whole-model PIPELINE for `#pragma HLS DATAFLOW`, so each layer becomes its own process and a "
                  "per-layer `parallelization_factor` survives. At pf = 1 the token axis stays **rolled** — one "
                  "physical dense core reused across tokens."),
            ("h", "The timing trap that took a probe to find"),
            ("code", "if l0 % pf:\n"
                     "    raise ValueError(f\"pf={pf} does not divide token axis\")\n"
                     "node.attributes[\"parallelization_factor\"] = pf\n"
                     "tmpl.transform(hm, node)     # <- apply_templates already fired at graph creation",
             {"size": 9.8}),
            ("p", "hls4ml bakes `parallelization_factor` into each layer's generated config at **ModelGraph "
                  "creation**, and `write()` never re-applies it. Setting the attribute alone is silently "
                  "discarded. So the code sets it **and** re-runs the config template on that node."),
            ("h", "Two gates on a scheduling-only change"),
            ("b", "**GATE A** reads back the *emitted firmware*: top-level PIPELINE == 0, DATAFLOW ≥ 1, and a pf "
                  "histogram accounting for all 15 pf lines with nothing left over — a leftover softmax pf **is** "
                  "the wedge that hung the Vitis front end for 24 hours."),
            ("b", "**GATE B** says a scheduling change must move nothing: GATE1 must reproduce the stored "
                  "baseline correlation to **1e-9** — not merely clear the 0.997 policy bar — and GATE2 must "
                  "stay bit-exact. The pf1 build reproduced GATE1 at 0.9988158043665978 with Δ = 0.0."),
        ],
        standfirst="Folding is a schedule change. Its gate is that nothing about the arithmetic moves.",
        cols=2,
        footer="Sources: fold_r14n8.py:10-27, 102-178, 264-266, 457-492 · probe_pf_dataflow.py:19-23 · results/r14/hls_r14_folded.md:129-132")

    d.text(
        "parse_csynth.py and parse_families.py — reading what comes back",
        [
            ("h", "parse_csynth.py — the whole-model row"),
            ("p", "Stdlib-only, so it runs on mulder's system python3. Pulls part, top module, target and "
                  "estimated clock, LUT/FF/DSP/BRAM_18K/URAM, the available-resources block, and best/worst "
                  "latency plus min/max interval."),
            ("code", "for k in (\"LatencyBest\", \"LatencyWorst\", \"IntervalMin\", \"IntervalMax\"):\n"
                     "    try:\n"
                     "        out[k] = int(out[k])\n"
                     "    except (TypeError, ValueError):\n"
                     "        out[k + \"_raw\"] = out[k]   # a DATAFLOW design can report '?'\n"
                     "        out[k] = None",
             {"size": 9.8}),
            ("h", "parse_families.py — the attribution tool"),
            ("p", "Sums the **flat per-instance** Utilization table of `myproject_csynth.rpt`, keying families off "
                  "the module name. Because that table is already per-instance, summing it needs no hierarchy "
                  "walk and **cannot double-count parents** — the `csynth.xml` fallback (module area × instance "
                  "count) can, and is reported as untrusted."),
            ("good", "**`--diff` mechanises the single-lever check**: per-family ΔLUT / ΔDSP plus an explicit "
                     "*unchanged-families* list. For the global fabric flag it showed `normalize` +705,472 LUT / "
                     "−3,621 DSP, `softmax_stable` +188,928 / −512, `einsum(act×act)` +303,104 / **0 DSP**, and "
                     "`einsum_dense`, `thresholded_relu`, `add` and `pool` **byte-identical**. Byte-identical "
                     "unchanged families is what makes an attribution airtight."),
            ("note", "It ships with `--self-test` against the stored r14n8 RF=1 baseline: 8/8 families, "
                     "cell-for-cell, over 25,811 instance rows — and it was validated *before* the run it was "
                     "built to judge, deliberately."),
        ],
        standfirst="\"How do you know a directive changed only the thing you think it changed?\" — with this.",
        cols=2,
        footer="Sources: parse_csynth.py:35-47 · parse_families.py:9-14, 40-62, 101-127")

    d.text(
        "The commands, end to end — be able to name them",
        [
            ("h", "Export + convert + both gates (local, CPU)"),
            ("code", "convert_final.py --variant w1a8 --seed 3 --tag r15gamma-sm4i0 \\\n"
                     "  --checkpoint models/cache/r15-gamma-sm4i0-n8-w1a8-s3/model_best.keras \\\n"
                     "  --config configs/r15-gamma-sm4i0-n8-w1a8.json \\\n"
                     "  --rf 1 --strategy Latency --beta-mode fx8 --input-std ... \\\n"
                     "  --fix-relu-parse --no-exact-char --data-dir data/val",
             {"size": 9.2}),
            ("p", "Note the **absence** of `--force-softmax-out-bits`: on the shipped arm the narrow grid is "
                  "trained, not forced."),
            ("h", "Fold"),
            ("code", "KERAS_BACKEND=tensorflow ../../../.venv-hgq2/bin/python fold_r14n8.py --article n8\n"
                     "  --pf 1 --pf-softmax 1 --n-gate 4096 --n-csim 128 --gate1-tol 1e-9",
             {"size": 9.2}),
            ("warn", "`--n-gate` **must** stay 4096 to match the baseline: `Xg[:2048]` sizes the export's stream "
                     "ranges, so changing it means GATE B is comparing unlike builds."),
            ("h", "Ship and synthesize"),
            ("code", "scp <tarball> mulder:~/bnjet_r14/\n"
                     "ssh mulder 'cd ~/bnjet_r14 && ./mulder_csynth.sh <tarball>.tar.gz'\n"
                     "# launched under setsid nohup ... < /dev/null — runs take hours",
             {"size": 9.2}),
            ("h", "Parse"),
            ("code", "parse_csynth.py <csynth.xml> > csynth_report.json\n"
                     "parse_families.py <myproject_csynth.rpt>\n"
                     "parse_families.py --diff <baseline.rpt> <variant.rpt>   # single-lever check\n"
                     "parse_families.py --self-test",
             {"size": 9.2}),
            ("h", "W8A8 baseline — a different driver"),
            ("code", "KERAS_BACKEND=tensorflow CUDA_VISIBLE_DEVICES=-1 \\\n"
                     "  python convert_w8a8.py --seed 3 --tag r14n8",
             {"size": 9.2}),
            ("note", "**Provenance:** every run leaf is `results/synthesis/runs/<cfg_hash>/<article>/`, with the "
                     "raw report always stored beside the parsed JSON."),
        ],
        standfirst="Naming the commands is what separates \"I ran a pipeline\" from \"I drove this.\"",
        cols=2,
        footer="Sources: .claude/skills/hls-mulder/SKILL.md:42-59 · experiment-log 2026-08-23 · fold_r14n8.py:519-521")

    # -------------------------------------------------------------- part V
    d.divider(
        "Part V", "The process",
        "Where it ran, how a run is proven to be the run you think it is, and the gates that stand "
        "between a number and a claim.",
        ["The pipeline end to end, and what each stage is allowed to say",
         "NRP Nautilus, mulder, and W&B — and why W&B is never the number of record",
         "Pre-registration: what was written down before any GPU started",
         "The two export gates, and the verify-roc gate",
         "The stage discipline: csynth, post-synthesis, post-opt_design are three different quantities"])

    d.figure(
        "The pipeline, end to end",
        os.path.join(FIGS, "pipeline.png"),
        "The accuracy axis and the silicon axis diverge at the checkpoint and never rejoin. Two gates stand "
        "between the trained model and any statement about silicon; three synthesis stages stand between the "
        "firmware and a claim about device fit, and they never share a table.",
        standfirst="If someone asks 'how does a trained model become an FPGA number?', this is the answer.",
        img_h=Inches(4.35))

    d.text(
        "Where it ran — and the PVC-free design that makes it reproducible",
        [
            ("h", "Training: NRP Nautilus"),
            ("p", "The National Research Platform's Kubernetes GPU cluster, in namespace `cms-ml` — the whole "
                  "Duarte group's **shared** namespace, not a personal one, which is why every resource is "
                  "prefixed `kai-`. Round 14 was 60 batch Jobs: stage 1 (36) launched in waves of 6 at ~08:19 UTC "
                  "on 2026-08-01 and finished the same day; stage 2 (24) went out immediately after; the round "
                  "was complete and ROC-verified on **2026-08-04**."),
            ("h", "The design choice worth defending"),
            ("p", "Pods are **emptyDir-only** — no persistent disk. Code arrives as a ~240 KB Kubernetes "
                  "ConfigMap, not a git clone and not a mounted volume. The ~2.7 GB dataset is re-downloaded "
                  "from Zenodo **inside every pod**. The only thing that survives the pod is a versioned W&B "
                  "artifact."),
            ("good", "**Why pay 2.7 GB per pod?** Because a PVC is shared mutable state on a shared cluster: "
                     "anyone can overwrite it, it silently accumulates stale code, and it makes \"which code "
                     "produced this checkpoint?\" unanswerable. Trading it for a frozen per-round ConfigMap plus "
                     "a public dataset URL plus immutable artifacts turns every run into something a third party "
                     "can re-derive from public inputs."),
            ("h", "Synthesis: mulder"),
            ("p", "Nautilus has no Xilinx backend, so hls4ml's build stage — the only stage that yields real "
                  "LUT/FF/DSP and latency in cycles — runs on `mulder.t2.ucsd.edu`, a shared UCSD Tier-2 box: "
                  "Vitis HLS 2023.2, target `xcvu13p-flga2577-2-e`, 2.5 ns."),
            ("warn", "**The counter-intuitive part.** Vitis HLS C-synthesis is **single-threaded**, so a run pegs "
                     "one core of 64 and leaves the rest idle. Mulder is not fast per synthesis — what it gives "
                     "is 125 GB of RAM. Memory is the binding constraint: three concurrent syntheses OOM-killed "
                     "a run at 54 GB RSS, and the n16 run was SIGKILLed at 112.5 GB after 17.7 hours."),
        ],
        standfirst="Two machines, two very different cost profiles. Know both answers to \"how long did it take?\"",
        cols=2,
        footer="Sources: docs/infrastructure/{nrp-nautilus-setup,mulder-setup,manual-round-runbook}.md · experiment-log 2026-08-01/04")

    d.text(
        "The md5 chain — proving which code produced a checkpoint",
        [
            ("h", "The mechanism"),
            ("code", "MD5=$(md5sum \"$TAR\" | awk '{print $1}' || md5 -q \"$TAR\")\n"
                     "SZ=$(wc -c < \"$TAR\")\n"
                     "echo \"[cm] packed $SRC -> hgq2.tar.gz  md5=$MD5  bytes=$SZ\"\n"
                     "[ \"$SZ\" -lt 1048576 ] || { echo \"[fatal] tar exceeds the 1 MB ConfigMap limit\"; exit 1; }",
             {"size": 9.6}),
            ("p", "`make_code_configmap_r14.sh` tars `code/hgq2/`, prints the md5, refuses to publish over the "
                  "1 MB ConfigMap limit, and applies it as ConfigMap `kai-bn14-code`. **Every training pod then "
                  "echoes the same md5 back** as `[code] configmap tar md5: …`. Round 14's is "
                  "`994813949ee8da13315206bc6633f100`."),
            ("good", "So \"did this pod run the code I think it ran?\" has an **answer**, not an assumption. And "
                     "ConfigMaps are frozen one per round — `kai-bnf`, `kai-bn11`, `kai-bn12`, `kai-bn13` are "
                     "untouched — so re-running an old round is still reproducible."),
            ("h", "The gates on both ends, and why they are scientific"),
            ("p", "The builder refuses to publish a tree lacking `feature_indices` in `bnhgq2/data.py`, lacking "
                  "the `wandb_util` layout in `train.py`, or holding anything other than exactly 20 "
                  "`configs/r14-*.json`. The pod repeats those greps at runtime and exits 1 on any of them."),
            ("warn", "**The reason is specific.** A pre-r14 tree would silently train the r14 config on all 16 "
                     "features instead of the L1-realistic 3 — which is exactly the confound Round 14 exists to "
                     "remove. A crash is recoverable; a silently wrong input set is not."),
        ],
        standfirst="\"Nothing is version-controlled inside the cluster. How do you know?\" — this is the answer.",
        cols=2,
        footer="Source: bnjettag/code/jobs/training/variants/make_code_configmap_r14.sh:1-34 · experiment-log 2026-08-01")

    d.text(
        "Pre-registration — what was written down before any GPU started",
        [
            ("h", "Fixed in `decisions.md` on 2026-08-01, before the first pod"),
            ("b", "**The arms:** stage 1 = {fp32, w8a8, w1a8} × N × seeds {1,2,3} = 36 jobs; stage 2 = "
                  "{w1a6, w1a4} × N × seeds = 24 jobs."),
            ("b", "**The selection rule:** best validation macro-OvR AUC per run."),
            ("b", "**The reporting metric:** ROC-test macro-OvR on the 260,000-jet held-out split, seed mean ± "
                  "sample std."),
            ("b", "**A requirement:** an uncertainty interval before any cross-arm claim."),
            ("b", "**The falsifier**, verbatim: *\"w1a8 within noise of fp32/w8a8 at some N with 0 DSP "
                  "downstream; if the binary gap blows up on 3-feature inputs, that is a result, not a failure.\"*"),
            ("good", "**Why it matters, in one sentence:** a campaign whose success criterion is written after "
                     "the numbers land cannot distinguish a discovery from a choice of framing."),
            ("h", "The same discipline, later"),
            ("p", "The Round-15 gamma selection rule was fixed on **19 August**, before any of those arms "
                  "existed: *ship the narrowest arm whose one-sided 95% upper bound on ΔAUC against the control "
                  "is ≤ 0.005; three seeds for screening, escalate to five only if the point estimate lands in "
                  "[0.002, 0.008]*. Both widths passed. So the result is not \"we found the one width that "
                  "worked\" — it is \"the 10-bit grid was over-provisioned and we shipped the narrower of two "
                  "passing arms, by rule.\""),
            ("note", "A **new W&B project** (`BNJetTagAug`) was created for the same reason: so a 3-feature "
                     "number can never silently sit in a 16-feature table."),
        ],
        standfirst="This is the slide that answers \"isn't this fitting the answer to the target?\"",
        cols=2,
        footer="Sources: .claude/memory/decisions.md 2026-08-01, 2026-08-19 · experiment-log 2026-08-01, 2026-08-23")

    d.text(
        "The three gates that stand between a number and a claim",
        [
            ("h", "GATE 1 — is the exported graph the trained network?"),
            ("p", "Correlate the exported Keras graph's scores against the trained QAT model's, on 4,096 real "
                  "jets drawn by `np.linspace` across the held-out split (evenly spaced, not the first 4,096 — "
                  "that avoids ordering bias). Bar: **0.997** norm-free, 0.9999 normed, stored per run with the "
                  "policy string so nobody can quietly relax it."),
            ("kv", ("Measured", "**0.9988** (n8-s3), **0.9974** (n16-s1); argmax agreement 0.980 / 0.976")),
            ("warn", "**Not an AUC.** A score correlation is a per-jet criterion; an AUC is a ranking metric. "
                     "Never call one the other."),
            ("h", "GATE 2 — is the firmware the exported graph?"),
            ("p", "hls4ml writes its own C++ test bench and runs the firmware model on real jets. The reference "
                  "is the **exported** graph, not the trained one — GATE 1 owns \"did the re-factoring preserve "
                  "the trained function\", GATE 2 owns \"did hls4ml's C++ reproduce the graph we handed it\"."),
            ("kv", ("Measured", "`max_abs_diff` **0.0**, `corr` **1.0**, bit_exact **true**, n = 128 — on both "
                                "probe articles")),
            ("h", "The verify-roc gate — rule zero"),
            ("p", "*\"Recompute, don't trust. A number may be written into a report only if it was recomputed "
                  "from the underlying `.npz` in the current session, or is quoted with its source file.\"* "
                  "Six steps: locate the arrays → inspect shapes before computing → compute macro-OvR → compare "
                  "against every place the number is claimed → report verbatim (\"claimed 0.7986, recomputed "
                  "0.7986 ✓\") → log the outcome."),
            ("good", "**The Round-14 pass: 60/60 models, 60 ✓ / 0 ✗** — and it caught a real defect. A table of "
                     "seed means that had survived a session compaction did not match the `.npz` recomputes and "
                     "was discarded. The disk tables had always been right. Volunteer this story; it is the gate "
                     "doing its job."),
        ],
        standfirst="Three gates, three different questions. Being able to separate them is most of the credibility.",
        cols=2,
        footer=f"Sources: convert_final.py:556-599, 686-709 · bnhgq2/convert.py:96-103 · .claude/skills/verify-roc/SKILL.md · {RESEARCH} §6.1")

    d.text(
        "Stage discipline — the vocabulary you must speak correctly",
        [
            ("h", "Five stages, five different truths"),
            ("kv", ("1. Convert", "Codegen only — but it yields exact **structural** facts. The C types in "
                                   "`defines.h` say what arithmetic the hardware can even express.")),
            ("kv", ("2. C-simulation", "A bit-accurate g++ emulation. Gives **fidelity** (GATE 2), never resources.")),
            ("kv", ("3. C-synthesis", "Vitis HLS **estimates** of LUT/FF/DSP/BRAM plus latency in cycles.")),
            ("kv", ("4. Vivado post-synthesis", "The RTL mapped to **real primitives**.")),
            ("kv", ("5. Post-`opt_design`", "After logic optimisation. **This is the fit result of record.**")),
            ("warn", "**They disagree by large, design-dependent factors.** Measured post-opt ÷ csynth: "
                     "**0.482** (RF=1 fabric), **0.462** (pf1fab), **0.442** (the narrowed build). The record "
                     "explicitly forbids pooling them, or applying a whole-design ratio to a delta."),
            ("warn", "**And csynth systematically understates DSP demand.** The binary DSP-carrying build reads "
                     "4,133 at csynth and demands **8,229** at Vivado (2.0×). The W8A8 baseline reads 1,384 and "
                     "demands **5,550** (4.0×)."),
            ("h", "Three separate meanings of \"zero DSP\""),
            ("b", "**(a)** C-synthesis reports DSP 0 in its rollup."),
            ("b", "**(b)** The Vivado *utilisation report* shows DSP used = 0."),
            ("b", "**(c)** The Vivado *synthesis log* has no `[Synth 8-3323]` line — i.e. DSP **demand** = 0."),
            ("good", "**Only (c) is the thesis claim.** The fit ladder's \"DSP used / demanded\" column exists "
                     "precisely to keep them apart — note that the W8A8 row's \"used\" is 1,721 only because the "
                     "part caps at 1,728 while the real demand is 5,550."),
        ],
        standfirst="Quoting a C-synthesis LUT count as silicon is the fastest way to lose an FPGA person.",
        cols=2,
        footer=f"Sources: {RESEARCH} §6 preamble · {FIT} §1 header and reading rules")

    # ------------------------------------------------------------- part VI
    d.divider(
        "Part VI", "What binarization costs",
        "The accuracy axis. Sixty runs, three seeds per arm, one held-out set of 260,000 jets — "
        "and a careful account of what is and is not resolved.",
        ["The AUC table, and the resolved binary deficit at every N",
         "What you are NOT allowed to claim at three seeds",
         "Which jets pay — per-class, and at trigger working points",
         "The N = 64 instability, and why it is a seed range and not a mean",
         "EBOPs, the Pareto front, and the two caveats that go with them"])

    d.table(
        "ROC-test macro one-vs-rest AUC — the table",
        ["N", "FP32", "W8A8", "W1A8 (binary)", "W1A6", "W1A4"],
        [
            ["8",  "0.8864 ± 0.0005", "0.8862 ± 0.0009", "**0.8712 ± 0.0016**", "0.8689 ± 0.0020", "0.8534 ± 0.0012"],
            ["16", "0.9128 ± 0.0013", "0.9124 ± 0.0014", "**0.8956 ± 0.0002**", "0.8910 ± 0.0009", "0.8693 ± 0.0021"],
            ["32", "0.9374 ± 0.0017", "0.9358 ± 0.0011", "**0.9052 ± 0.0079**", "0.9022 ± 0.0009", "0.8833 ± 0.0013"],
            ["64", "0.9486 ± 0.0012", "0.9448 ± 0.0011", "**0.9121 ± 0.0116** †", "0.9136 ± 0.0061", "0.9073 ± 0.0009"],
        ],
        standfirst="Held-out split, n = 260,000. Seed mean ± sample std over 3 seeds. Verified 2026-08-04, 60/60 exact.",
        widths=[0.08, 0.184, 0.184, 0.196, 0.178, 0.178], size=12.5,
        notes=[
            ("good", "**The headline, said correctly.** The binary deficit against FP32 is **RESOLVED at every N**: "
                     "+0.0152 (N=8), +0.0172 (16), +0.0322 (32), +0.0365 (64). Phrase it as *\"the deficit is "
                     "0.015–0.017 at N ≤ 16 and 0.032–0.036 at N ≥ 32\"* — never as a per-step growth."),
            ("warn", "**† N = 64 W1A8 is a seed RANGE, not a mean:** 0.9028 / 0.9084 / 0.9251. The seed-pair "
                     "bootstrap intervals all exclude zero — real training instability, not evaluation noise. "
                     "Reporting 0.9121 ± 0.0116 would imply a well-defined arm with modest scatter. Do not."),
            ("note", "**Finding 1, worth saying:** the three L1 features carry the task. FP32 reaches 0.9128 at "
                     "N = 16 and 0.9374–0.9486 at N = 32–64 on p_T, η_rel, φ_rel alone."),
        ],
        footer=f"Sources: {RESEARCH} §5 · {ROC} · recomputable from bnjettag/roc-results/r14/n<N>/*.npz")

    d.text(
        "What you are NOT allowed to claim — and why that is a strength",
        [
            ("h", "The forbidden list"),
            ("warn", "**Do not say the gap grows with N, step by step.** The steps are +0.0020 / +0.0150 / "
                     "+0.0043 in the FP32 − W1A8 convention — consistent in sign, **not individually resolved** "
                     "at three seeds."),
            ("warn", "**Do not say W8A8 is worse than FP32.** At N = 64 the seed-mean gap is +0.0038 and the "
                     "σ_total table calls it RESOLVED — but the three-seed t-interval is [−0.0018, +0.0095], so "
                     "it is not claimed. Conventional 8-bit quantization is **free** on this task at N = 8 and "
                     "16 (UNRESOLVED), and binarization is not. That is the honest framing, and it also makes "
                     "W8A8 the right comparator: it is statistically indistinguishable from FP32 where it matters."),
            ("warn", "**Do not claim an activation-width ordering at N = 64.** W1A8 − W1A6 is −0.00151 ± 0.00758 "
                     "— the sign even flips."),
            ("h", "The one documented disagreement between the two passes"),
            ("p", "The A8 → A4 step at N = 32: the σ_total table calls it RESOLVED (+0.0220 ± 0.0047), but the "
                  "three-seed t-interval [−0.0008, +0.0447] marginally includes zero. **Where the two passes "
                  "differ, the conservative verdict is adopted.** RESEARCH.md flags it explicitly as \"the one "
                  "disagreement.\""),
            ("h", "Why three seeds, and what it would take"),
            ("p", "With n = 3 the sample std has 2 degrees of freedom, so the two-sided 95% t-multiplier is "
                  "**4.303**, not 1.96 — a three-seed interval is more than twice as wide as a naive Gaussian "
                  "one. The flagship claim survives with enormous margin anyway (N = 8: +0.01520 against "
                  "σ_total 0.00099, over 15σ). The cost of settling the rest is on record: about **10 seeds** "
                  "for W8A8 at N = 64, about **30** for the gap-growth steps."),
            ("good", "**Say this, and mean it:** we claim less than the raw numbers would let us. Volunteering "
                     "the not-claimed list before a referee finds it is the single highest-value thing you can "
                     "do at the poster."),
        ],
        standfirst="Knowing what you cannot claim is worth more at a poster than any number you can.",
        cols=2,
        footer=f"Sources: {RESEARCH} §5 · bnjettag/results/r14/uncertainty_r14.md · experiment-log 2026-08-03")

    d.text(
        "Why test-set noise is negligible — and what that tells a reviewer",
        [
            ("h", "The two numbers"),
            ("kv", ("σ_boot", "**0.00012 – 0.00027** across all 16 comparisons (≈0.0004 as quoted)")),
            ("kv", ("σ_seed", "**0.00055 – 0.00757** — up to roughly 30× larger")),
            ("p", "Because they add in quadrature, σ_boot never moves a verdict."),
            ("h", "The reading, and why it is a design argument"),
            ("good", "260,000 held-out jets is **plenty** to pin an AUC. What we do not know precisely is what a "
                     "retrain would give. So the honest error bar on any comparison here is a training-variance "
                     "bar, and collecting more test data would buy nothing."),
            ("p", "That also tells the reviewer what the fix is — **more seeds, not more jets** — and closes the "
                  "obvious \"is your test set big enough?\" line of attack in one move."),
            ("h", "The N = 64 instability, quantified"),
            ("p", "Mean per-N binary seed variance, (n32, n64) / (n8, n16): **×75.8**. The weakest N = 32/64 "
                  "seeds peak **mid-training** and degrade afterwards — best epochs 57, 49 and 40 for n32-s1, "
                  "n32-s3, n64-s1 (n64-s3 at 99). Diagnostics point at optimization, not evaluation."),
            ("warn", "**A correction to know before someone reruns the script.** `uncertainty_r14.py` prints a "
                     "pooled variance ratio of **0.5×**, which is invalid — pooling across N mixes different arm "
                     "means, so the between-N mean shift (which is signal) inflates the pooled variance. The "
                     "corrected per-N statistic is 75.8×, recorded as a dated correction in `uncertainty_r14.md` "
                     "and as `corrected_per_n_variance_ratio` in the JSON. A statistician in the audience will "
                     "ask why pooling was wrong; that is the answer."),
        ],
        standfirst="\"Is your test set big enough?\" — Yes, and here is the number that proves it is not the limit.",
        cols=2,
        footer="Sources: bnjettag/results/r14/uncertainty_r14.{md,json} · RESEARCH.md §5 · train_meta.json of the checkpoints")

    d.text(
        "Which jets pay — per class, and at a trigger working point",
        [
            ("h", "Per-class one-vs-rest AUC, FP32 → W1A8"),
            ("kv", ("N = 8 and 16", "**gluon** pays the most (−0.023 / −0.025), **top** the least (−0.007 / −0.010)")),
            ("kv", ("N = 32 and 64", "**W and Z** pay the most (−0.046 / −0.048 and −0.063 / −0.070) and carry the "
                                      "seed instability; top stays within −0.014 at every N")),
            ("p", "N = 16 values: FP32 g 0.8784 / q 0.8930 / W 0.9358 / Z 0.9202 / t 0.9364 against W1A8 "
                  "g 0.8531 / q 0.8793 / W 0.9179 / Z 0.9015 / t 0.9263."),
            ("good", "**The physics predicts this, and that is the strongest sentence in the section.** g-vs-q is "
                     "a soft radiation-pattern discriminant with no hard structure to fall back on — "
                     "binarization damages it first. Top is three-prong and heaviest, the loudest signature — "
                     "damaged last. W and Z are near-degenerate two-prong objects separated mainly by ~11 GeV of "
                     "mass, so once there are enough constituents to resolve prongs, they are what destabilizes."),
            ("h", "And AUC hides some of it — working points"),
            ("p", "Nobody builds a trigger menu out of macro AUC. At a **1% mistag rate**, N = 16: Z efficiency "
                  "0.480 ± 0.003 → 0.390 ± 0.004; top 0.469 ± 0.012 → 0.365 ± 0.003. That is 3–10 efficiency "
                  "points — manageable."),
            ("warn", "**At N = 64 the W/Z working points collapse.** W efficiency at 1% mistag "
                     "0.660 ± 0.011 → **0.209 ± 0.105**; Z rejection at 50% efficiency 519 ± 60 → **32 ± 26**. "
                     "The seed scatter is half the value. **No single-seed number may be quoted there.**"),
            ("note", "**The framing that turns this into a characterized limit rather than a weakness:** *\"binary "
                     "holds at short sequences, which is where the L1 latency budget puts us anyway; at long "
                     "sequences binary QAT becomes unstable, and we say so.\"*"),
        ],
        standfirst="This slide is where a physicist decides whether you understand your own result.",
        cols=2,
        footer=f"Sources: {RESEARCH} §5 · {WP} (gate-verified 2026-08-24, 66 files, AUCs matched to 1e-4)")

    d.figure(
        "Accuracy against constituent count",
        os.path.join(R14, "fig_r14_auc_vs_n.png"),
        "Held-out macro one-vs-rest AUC against N, all five arms, seed mean with sample std. FP32 and W8A8 sit "
        "on top of each other; the binary arms sit below by a resolved margin, and the binary spread widens "
        "visibly at N of 32 and above.",
        standfirst="Recomputed from the stored .npz arrays; this is the figure that goes on the poster.",
        img_h=Inches(4.3),
        footer="Source: bnjettag/results/r14/figures/fig_r14_auc_vs_n.png, built from bnjettag/roc-results/r14/n<N>/*.npz")

    d.figure(
        "The cost axis — accuracy against bit-operations",
        os.path.join(R14, "fig_r14_pareto.png"),
        "EBOPs (HGQ's synthesis-free estimate from the trained quantizers) against AUC. Binary needs 5.28× "
        "(N = 8), 4.08× (16), 2.97× (32) and 2.14× (64) fewer checkpoint EBOPs than W8A8 at matched N.",
        standfirst="A proxy, not silicon. Say the two caveats before you are asked for them.",
        side=[
            ("h", "The two caveats"),
            ("warn", "Checkpoint EBOPs **omit the 15 β-restore affines** the silicon actually carries. The n8 "
                     "W1A8 export graph traces to **3,025,884** EBOPs against the checkpoint's **1,739,182** — "
                     "+74%, and the reconciliation is exact (+1,280,302 from the affines, +6,400 from "
                     "input_proj bias bookkeeping)."),
            ("warn", "EBOPs carries **no accumulator term** — it counts multiplies only, so the adder trees that "
                     "binary weights turn into are invisible to it. That is why the measured csynth and Vivado "
                     "numbers, not EBOPs, are the resource claim of record."),
            ("note", "FP32 has no EBOPs point at all — it is not quantized."),
            ("note", "Why the ratio falls with N: the act×act attention terms are identical across arms and grow "
                     "as N². Volunteer this; it looks like a weakening result until you explain it."),
        ],
        img_h=Inches(4.3),
        footer=f"Sources: {RESEARCH} §5 · bnjettag/results/r14/ebops_r14.json · bnjettag/results/ebops.md")
