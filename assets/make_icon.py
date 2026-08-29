#!/usr/bin/env python3
"""
Generate the Natural Gas Prop Main application icon.

Creates a themed icon: a rounded-square navy->teal gradient badge with a
pressure-gauge bezel, gauge tick marks, molecule accents and a stylized
natural-gas flame. Outputs:
    assets/NaturalGasProp.png        (1024px master)
    assets/NaturalGasProp.icns       (macOS)
    assets/NaturalGasProp.ico        (Windows, multi-size)

Usage:
    python assets/make_icon.py
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent
SIZE = 1024


def gradient_background(size: int) -> Image.Image:
    """Vertical navy -> teal gradient (each row a solid colour)."""
    top = np.array([8, 20, 50], dtype=float)
    bottom = np.array([0, 120, 140], dtype=float)
    ramp = np.linspace(0.0, 1.0, size, dtype=float)
    # (size, 1, 3) row colours broadcast across the width
    grad = ramp[:, None, None] * bottom + (1.0 - ramp)[:, None, None] * top
    grad = np.repeat(grad, size, axis=1)
    return Image.fromarray(grad.astype(np.uint8), "RGB")


def draw_flame(d: ImageDraw.ImageDraw, cx: float, cy_base: float, scale: float) -> None:
    """Layered teardrop natural-gas flame anchored near (cx, cy_base)."""
    # outer (red)
    d.ellipse([cx - 210 * scale, cy_base - 120 * scale, cx + 210 * scale, cy_base + 240 * scale],
              fill=(235, 64, 52, 255))
    d.polygon(
        [(cx - 150 * scale, cy_base - 10 * scale),
         (cx + 150 * scale, cy_base - 10 * scale),
         (cx, cy_base - 360 * scale)],
        fill=(235, 64, 52, 255),
    )
    # middle (orange)
    d.ellipse([cx - 150 * scale, cy_base - 80 * scale, cx + 150 * scale, cy_base + 180 * scale],
              fill=(255, 140, 20, 255))
    d.polygon(
        [(cx - 105 * scale, cy_base - 30 * scale),
         (cx + 105 * scale, cy_base - 30 * scale),
         (cx, cy_base - 320 * scale)],
        fill=(255, 140, 20, 255),
    )
    # inner (yellow)
    d.ellipse([cx - 95 * scale, cy_base - 50 * scale, cx + 95 * scale, cy_base + 120 * scale],
              fill=(255, 214, 0, 255))
    d.polygon(
        [(cx - 65 * scale, cy_base - 10 * scale),
         (cx + 65 * scale, cy_base - 10 * scale),
         (cx, cy_base - 250 * scale)],
        fill=(255, 214, 0, 255),
    )
    # core (white)
    d.ellipse([cx - 48 * scale, cy_base - 25 * scale, cx + 48 * scale, cy_base + 70 * scale],
              fill=(255, 255, 255, 255))


def render_icon(size: int) -> Image.Image:
    s = size
    scale = s / 1024.0
    img = gradient_background(s).convert("RGBA")

    # rounded-rectangle mask
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.21), fill=255)
    img.putalpha(mask)

    d = ImageDraw.Draw(img)
    cx, cy = s / 2.0, s / 2.0

    # gauge bezel (dark ring) + dial face
    bezel_r = 0.44 * s
    d.ellipse([cx - bezel_r, cy - bezel_r, cx + bezel_r, cy + bezel_r], fill=(10, 30, 60, 255))

    face = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    fd = ImageDraw.Draw(face)
    face_r = 0.40 * s
    fd.ellipse([cx - face_r, cy - face_r, cx + face_r, cy + face_r], fill=(238, 248, 252, 255))
    fd.ellipse([cx - face_r * 0.92, cy - face_r * 0.92, cx + face_r * 0.92, cy + face_r * 0.92],
               outline=(180, 215, 230, 255), width=max(1, int(s * 0.012)))
    img.alpha_composite(face)

    # gauge ticks along the upper arc (-135deg .. -45deg)
    tick_inner, tick_outer = face_r * 0.82, face_r * 0.94
    for i in range(11):
        ang = math.radians(-135 + i * 9)
        x1 = cx + tick_inner * math.cos(ang)
        y1 = cy + tick_inner * math.sin(ang)
        x2 = cx + tick_outer * math.cos(ang)
        y2 = cy + tick_outer * math.sin(ang)
        d.line([x1, y1, x2, y2], fill=(10, 30, 60, 255), width=max(1, int(s * (0.008 if i in (0, 5, 10) else 0.005))))

    # molecule accents at the top of the dial
    ax, ay = cx, cy - face_r * 0.62
    d.line([ax - s * 0.06, ay, ax + s * 0.06, ay], fill=(0, 120, 140, 255), width=max(1, int(s * 0.05)))
    for ox in (-s * 0.06, s * 0.06):
        d.ellipse([ax + ox - s * 0.035, ay - s * 0.035, ax + ox + s * 0.035, ay + s * 0.035],
                  fill=(0, 150, 170, 255))

    # natural-gas flame (lower-centre of the dial)
    draw_flame(d, cx, cy + face_r * 0.30, scale)

    return img


def make_ico(img: Image.Image, path: Path) -> None:
    img.save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def make_icns(img: Image.Image, path: Path) -> None:
    iconset = ASSETS / "NaturalGasProp.iconset"
    iconset.mkdir(exist_ok=True)
    spec = {
        "icon_16x16.png": 16, "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32, "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128, "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256, "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512, "icon_512x512@2x.png": 1024,
    }
    for name, sz in spec.items():
        img.resize((sz, sz), Image.LANCZOS).save(iconset / name)
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(path)], check=True)
    for f in iconset.glob("*.png"):
        f.unlink()
    iconset.rmdir()


def main() -> None:
    master = render_icon(SIZE)
    master.save(ASSETS / "NaturalGasProp.png")
    make_ico(master, ASSETS / "NaturalGasProp.ico")
    make_icns(master, ASSETS / "NaturalGasProp.icns")
    print("Icons written to assets/")


if __name__ == "__main__":
    main()