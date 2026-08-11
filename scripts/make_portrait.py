#!/usr/bin/env python3
"""Turn a photo into ascii.svg — colored with phosphor green neon mapping for depth."""
import argparse
import sys
import cv2
import numpy as np
from PIL import Image
from rembg import remove

RAMP = " .`:-=+*cs#%@"     # bright/sparse -> dark/dense; leading space = blank
PALETTE = [
    "#66ff66", # 0 brightest highlight (pure light green)
    "#39ff14", # 1 pure neon green
    "#1fdf20", # 2
    "#18c919", # 3
    "#12b012", # 4
    "#0d930d", # 5
    "#097909", # 6
    "#066106", # 7
    "#044b04", # 8
    "#023502", # 9
    "#012001", # 10
    "#000c00", # 11
    "#000000"  # 12 darkest shadow
]

COLS = 90
CLAHE_CLIP = 3.0
GAMMA = 1.0
CURVE = 1.7
CROP_BOTTOM = 0.0          
ROW_RATIO = 0.48

FG_LIGHT = "#097909"       
FG_DARK = "#39ff14"        
CHAR_W = 7.74
FONT_SIZE = 12.9
LINE_H = 15
ROW_DELAY = 0.09
FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

def prep(path, crop=None):
    src = Image.open(path).convert("RGBA")
    if crop:
        src = src.crop(crop)

    cut = remove(src)
    alpha = np.array(cut.split()[-1])

    black = Image.new("RGBA", cut.size, (0, 0, 0, 255))
    gray = np.array(Image.alpha_composite(black, cut).convert("L"))

    gray = cv2.bilateralFilter(gray, 11, 50, 50)
    gray = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(8, 8)).apply(gray)
    gray = (255.0 * (gray / 255.0) ** CURVE).astype("uint8")
    gray[alpha < 20] = 255
    return Image.fromarray(gray)

def to_lines(img, cols=COLS, gamma=GAMMA):
    w, h = img.size
    if CROP_BOTTOM:
        trim_h = int(h * (1 - CROP_BOTTOM))
        img = img.crop((0, 0, w, trim_h))
        w, h = img.size

    rows = int(cols * (h / w) * ROW_RATIO)
    img = img.resize((cols, rows), Image.LANCZOS)
    px = list(img.getdata())
    n = len(RAMP)

    out = []
    for r in range(rows):
        row_spans = []
        
        # Determine chars first
        chars = []
        indices = []
        for c in range(cols):
            val = px[r * cols + c] / 255.0
            idx = min(n - 1, int((1 - val) ** gamma * n))
            chars.append(RAMP[idx])
            indices.append(idx)
            
        while chars and chars[-1] == " ":
            chars.pop()
            indices.pop()
            
        chars_len = len(chars)
        
        for c, char in enumerate(chars):
            if char == " ":
                row_spans.append(" ")
            else:
                hex_col = PALETTE[indices[c]]
                safe_char = char.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                row_spans.append(f'<tspan fill="{hex_col}">{safe_char}</tspan>')
        
        out.append(("".join(row_spans), chars_len))

    while out and out[0][1] == 0:
        out.pop(0)
    while out and out[-1][1] == 0:
        out.pop()
    return out

def build_svg(lines, cols=COLS):
    pad = 14
    width = int(cols * CHAR_W + pad * 2)
    height = len(lines) * LINE_H + pad * 2

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
         f'height="{height}" viewBox="0 0 {width} {height}" '
         f'font-family="{FAMILY}">',
         f'<style>.a{{fill:{FG_LIGHT}}}'
         f'@media(prefers-color-scheme:dark){{.a{{fill:{FG_DARK}}}}}</style>']

    for i, (xml_line, visible_len) in enumerate(lines):
        y = pad + i * LINE_H
        begin = f"{i * ROW_DELAY:.2f}s"
        end = f"{(i + 1) * ROW_DELAY:.2f}s"
        w = max(visible_len, 1) * CHAR_W

        p.append(f'<clipPath id="c{i}"><rect x="{pad}" y="{y}" '
                 f'height="{LINE_H}" width="0">'
                 f'<animate attributeName="width" from="0" to="{w:.1f}" '
                 f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
                 f'</rect></clipPath>')
        p.append(f'<g clip-path="url(#c{i})"><text xml:space="preserve" '
                 f'x="{pad}" y="{y + 11.2:.1f}" '
                 f'font-size="{FONT_SIZE}">{xml_line}</text></g>')
        
        p.append(f'<rect y="{y + 1}" width="6" height="12" class="a" '
                 f'opacity="0">'
                 f'<animate attributeName="x" from="{pad}" to="{pad + w:.1f}" '
                 f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0.8" begin="{begin}"/>'
                 f'<set attributeName="opacity" to="0" begin="{end}"/></rect>')

    p.append("</svg>")
    return "".join(p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("out", nargs="?", default="ascii.svg")
    ap.add_argument("--crop")
    ap.add_argument("--cols", type=int, default=COLS)
    args = ap.parse_args()

    crop = None
    if args.crop:
        crop = tuple(int(v) for v in args.crop.split(","))

    lines = to_lines(prep(args.photo, crop), cols=args.cols)
    
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_svg(lines, cols=args.cols))
    print(f"wrote {args.out} — {len(lines)} rows, {args.cols} columns")

if __name__ == "__main__":
    main()
