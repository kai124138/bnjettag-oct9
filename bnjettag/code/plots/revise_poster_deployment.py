#!/usr/bin/env python3
"""Create a deployment-status-corrected copy of the FastML poster.

The original PowerPoint is never overwritten. Text is replaced paragraph-by-paragraph so
the existing layout and formatting are retained.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt


REPLACEMENTS = {
    "emits Verilog for the AMD/Xilinx Virtex": (
        "Quantization-aware training (Keras + HGQ2 [5]) → hls4ml [2] converts the trained "
        "network to C++ → Vitis HLS emits Verilog → Vivado performs out-of-context logic "
        "synthesis targeting a Zynq UltraScale+ ZU7EV. Counts are compared with the nominal "
        "Virtex UltraScale+ VU13P resource total; this is not a target-part fit result. The "
        "exported network reproduces the trained scores (correlation ≥ 0.997 on 4,096 jets; "
        "0.9988 at N = 8), and the hls4ml C++ test bench matches it bit-for-bit."
    ),
    "Resources, and the device-fit gap": "Resources and the deployment gap",
    "whether the design fits the VU13P's LUT budget": (
        "The zero-DSP result is established. VU13P fit is not: the counts below come from "
        "out-of-context ZU7EV synthesis before place-and-route and are compared only with "
        "the VU13P's nominal LUT count."
    ),
    "% of VU13P LUTs": "% of nominal VU13P LUT count*",
    "attribution of the fitting build": (
        "Where the logic goes (high-level-synthesis attribution of the resource-characterization "
        "build): binary layers 28%, β rescaling 26%, inter-layer buffering and control 24%, "
        "attention products 14%."
    ),
    "Both designs at the bit-widths learned in training": (
        "Both learned-precision zero-DSP designs exceed the nominal VU13P LUT count (122%, "
        "113%). A 4-bit softmax grid brings the cross-part count to 98%. At 2.5 ns every "
        "zero-DSP design fails timing; at 5 ns the retrained 4-bit design uses 1,583,565 LUTs "
        "(91.6% of the nominal count), zero DSPs, and has +0.65 ns pre-route slack. It accepts "
        "one jet every 240 ns with 1.7 µs latency and scores 0.8701 ± 0.0020 AUC. This is a "
        "ZU7EV out-of-context resource point, not demonstrated VU13P fit or Level-1 deployability."
    ),
    "LUT counts: Vivado logic synthesis": (
        "*LUT counts are from Vivado logic synthesis of the standalone module targeting a "
        "smaller Zynq UltraScale+ ZU7EV, before place-and-route, and are compared with the "
        "VU13P's nominal 1,728,000 LUTs. No VU13P placement, routing, bitstream, or board test "
        "has been performed. Zero-DSP rows are confirmed on the Vivado netlist."
    ),
    "Synthesize the network retrained with the 4-bit softmax grid": (
        "• Synthesize, place and route on the VU13P; then close target-part timing.   "
        "• Reduce LUT use, 333-cycle latency and II = 48; the timing-clean point is 1.7 µs "
        "and one jet per 240 ns.   • Integrate trigger I/O, generate a bitstream and test on "
        "a board.   • Synthesize N ≥ 16 and an FP32 baseline.   • W8A8 is now measured: in "
        "the same cross-part flow it demands 2,525,842 LUTs and 5,550 DSPs."
    ),
}


def replace_paragraph(paragraph, new_text: str) -> None:
    if not paragraph.runs:
        run = paragraph.add_run()
        run.text = new_text
        return
    paragraph.runs[0].text = new_text
    for run in paragraph.runs[1:]:
        run.text = ""


def iter_paragraphs(prs: Presentation):
    for slide in prs.slides:
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                yield from shape.text_frame.paragraphs
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    for cell in row.cells:
                        yield from cell.text_frame.paragraphs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    prs = Presentation(args.input)
    matched = {anchor: 0 for anchor in REPLACEMENTS}
    for paragraph in iter_paragraphs(prs):
        original = paragraph.text
        for anchor, replacement in REPLACEMENTS.items():
            if anchor in original:
                replace_paragraph(paragraph, replacement)
                matched[anchor] += 1
                break

    missing = [anchor for anchor, count in matched.items() if count != 1]
    if missing:
        details = ", ".join(f"{anchor!r} ({matched[anchor]} matches)" for anchor in missing)
        raise RuntimeError(f"Expected exactly one match for each replacement: {details}")

    # Define the evaluation term in the caption without discarding its uncertainty notes.
    for paragraph in iter_paragraphs(prs):
        if paragraph.text.startswith("Held-out macro one-vs-rest AUC"):
            for run in paragraph.runs:
                run.text = run.text.replace(
                    "Held-out macro one-vs-rest AUC",
                    "Held-out = a separate test set never used for training or model selection. "
                    "Macro one-vs-rest AUC",
                )

    # Russell's visual fixes: make the title dominant and normalize the poster typography.
    white = RGBColor(0xFF, 0xFF, 0xFF)
    for slide in prs.slides:
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                text = shape.text.strip()
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = "Arial"
                        if text.startswith("A Binary-Weight Transformer"):
                            run.font.size = Pt(96)
                            run.font.bold = True
                            run.font.color.rgb = white
                        elif text.startswith("Kai Yamaguchi"):
                            run.font.size = Pt(30)
                            run.font.color.rgb = white
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    for cell in row.cells:
                        for paragraph in cell.text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.font.name = "Arial"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
