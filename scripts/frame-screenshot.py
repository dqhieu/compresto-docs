#!/usr/bin/env python3
"""Put a Compresto window screenshot on a blue gradient so it stands out on the docs page.

Adds padding, a soft drop shadow, and rounded outer corners. Works best with a
window captured with transparent corners and no macOS shadow:

    screencapture -o -l <window-id> window.png

Usage:
    python3 scripts/frame-screenshot.py window.png images/my-screenshot.png
    python3 scripts/frame-screenshot.py a.png b.png --out-dir images

Requires Pillow (pip3 install pillow).
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

# Docs primary blue (#2563EB) fading from a light tint in the top-left corner.
GRADIENT_START = (191, 219, 254)
GRADIENT_END = (37, 99, 235)
SHADOW_COLOR = (15, 23, 42)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size):
    tile = Image.new("RGB", (256, 256))
    px = tile.load()
    for y in range(256):
        for x in range(256):
            px[x, y] = lerp(GRADIENT_START, GRADIENT_END, (x + y) / 510)
    return tile.resize(size, Image.BICUBIC).convert("RGBA")


def frame(src: Path, dst: Path) -> None:
    window = Image.open(src).convert("RGBA")
    w, h = window.size
    pad = int(max(w, h) * 0.07)
    size = (w + pad * 2, h + pad * 2)

    canvas = gradient(size)

    # Shadow from the window's own alpha, so it follows the rounded corners.
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    silhouette = Image.new("RGBA", window.size, SHADOW_COLOR + (0,))
    silhouette.putalpha(window.split()[3].point(lambda a: int(a * 0.45)))
    shadow.paste(silhouette, (pad, pad + int(pad * 0.18)), silhouette)
    shadow = shadow.filter(ImageFilter.GaussianBlur(pad * 0.35))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.alpha_composite(window, (pad, pad))

    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), int(pad * 0.45), fill=255
    )
    canvas.putalpha(mask)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("inputs", nargs="+", type=Path, help="screenshot(s) to frame")
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="write each framed image here with the same file name "
        "(without it, pass exactly one input followed by one output path)",
    )
    args = parser.parse_args()

    if args.out_dir:
        pairs = [(src, args.out_dir / src.name) for src in args.inputs]
    elif len(args.inputs) == 2:
        pairs = [(args.inputs[0], args.inputs[1])]
    else:
        parser.error("pass INPUT OUTPUT, or several inputs with --out-dir")

    for src, dst in pairs:
        if src.resolve() == dst.resolve():
            parser.error(f"{src} would overwrite itself; keep the unframed original")
        frame(src, dst)
        print(f"{src} -> {dst}")


if __name__ == "__main__":
    main()
