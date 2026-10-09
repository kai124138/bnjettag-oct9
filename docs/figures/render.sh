#!/usr/bin/env bash
# Render docs/figures/<name>.tex (a standalone TikZ document) to <name>.svg and <name>.png,
# entirely on this machine: tectonic compiles, PyMuPDF converts. No third party sees the source,
# and there is no size limit, unlike the upmath GET API (which also fails when any TikZ library
# is passed in `packages`).
#   ./render.sh harness-layout
set -euo pipefail
cd "$(dirname "$0")"
name="${1:?usage: render.sh <name>   (renders <name>.tex)}"
name="${name%.tex}"
tectonic -X compile "$name.tex" >/dev/null
uv run --quiet --with pymupdf python - "$name" <<'PY'
import sys, pymupdf
name = sys.argv[1]
page = pymupdf.open(f"{name}.pdf")[0]
open(f"{name}.svg", "w").write(page.get_svg_image(text_as_path=True))
page.get_pixmap(dpi=180).save(f"{name}.png")
PY
rm -f "$name.pdf"
echo "wrote $name.svg $name.png"
