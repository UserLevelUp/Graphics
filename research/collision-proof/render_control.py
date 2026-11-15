"""Plot the exact quartic control; this image is illustrative, not a proof.

defines: graph.riemann.collision.render
consumer: graph.riemann.collision.proof

Uses Pillow already present in the project environment; no numeric root solver.
Run: python research/collision-proof/render_control.py
"""

from __future__ import annotations

import cmath
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "evidence" / "quartic-control.png"
WIDTH, HEIGHT = 1720, 1260
LEFT, RIGHT = 150, 1620
TMIN, TMAX = -1.2, 0.0
COLORS = ("#007e90", "#d67800", "#3948be", "#bb3692")
INK, MUTED = "#1c2939", "#536273"
FONT_DIR = Path("C:/Windows/Fonts")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def roots(t: float) -> tuple[complex, complex, complex, complex]:
    discriminant = 96 * (t + 1) * (t + 2 / 3)
    # Clamp only rounding at the two explicitly sampled discriminant zeros.
    if t in (-1.0, -2 / 3):
        discriminant = 0.0
    dw = cmath.sqrt(discriminant)
    wp, wm = 5 + 6 * t + dw / 2, 5 + 6 * t - dw / 2
    a, b = cmath.sqrt(wp), cmath.sqrt(wm)
    return a, -a, b, -b


def main() -> None:
    im = Image.new("RGB", (WIDTH, HEIGHT), "#fbfcff")
    draw = ImageDraw.Draw(im)

    def text(x: float, y: float, label: str, size: int = 23,
             fill: str = INK, bold: bool = False, anchor: str = "la") -> None:
        draw.text((x, y), label, font=font(size, bold), fill=fill, anchor=anchor)

    def tx(t: float) -> float:
        return LEFT + (t - TMIN) / (TMAX - TMIN) * (RIGHT - LEFT)

    def dash(x: float, top: float, bottom: float, color: str,
             width: int = 2) -> None:
        y = top
        while y < bottom:
            draw.line((x, y, x, min(y + 9, bottom)), fill=color, width=width)
            y += 16

    text(80, 28, "Four zeros: exact collision versus local forecasts", 39, bold=True)
    text(80, 84, "Pτ(z) = z⁴ − (10 + 12τ)z² + 9 + 20τ + 12τ²", 29)
    text(80, 127, "Start at τ = 0 on the right; decrease τ toward the left.", 24, MUTED)
    text(80, 174, "Root branches", 22, bold=True)
    labels = ("+√w+", "−√w+", "+√w−", "−√w−")
    for j, (label, color) in enumerate(zip(labels, COLORS)):
        x = 255 + j * 142
        draw.line((x, 193, x + 35, 193), fill=color, width=5)
        text(x + 44, 174, label, 23, color)

    # A dedicated key keeps close forecast labels away from the plotted roots.
    estimates = ((-113 / 196, "#805e32", "Frozen at c = ±2: −113/196 ≈ −0.577"),
                 (-1 / 2, "#737b88", "Gap bound: −1/2 = −0.500"),
                 (-9 / 20, "#a35b72", "Frozen at c = 0: −9/20 = −0.450"))
    text(1040, 116, "Vertical dashed lines = forecasts / bound", 22, bold=True)
    for j, (_, color, label) in enumerate(estimates):
        y = 151 + 32 * j
        draw.line((1040, y + 15, 1073, y + 15), fill=color, width=3)
        text(1085, y, label, 21, color)

    ts = sorted({TMIN + i * (TMAX - TMIN) / 1800 for i in range(1801)}
                | {-1.0, -2 / 3, -113 / 196, -0.5, -0.45, 0.0})
    calculated = [roots(t) for t in ts]

    for which, top, bottom, limit, heading in (
        ("real", 290, 620, 3.3, "Real component of each zero"),
        ("imag", 765, 1095, 2.5, "Imaginary component of each zero"),
    ):
        text(LEFT, top - 43, heading, 26, bold=True)

        def py(value: float) -> float:
            return bottom - (value + limit) / (2 * limit) * (bottom - top)

        regimes = ((-1.2, -1, "#edf0f5"),
                   (-1, -2 / 3, "#fcf1e5"),
                   (-2 / 3, 0, "#eaf5ee"))
        for a, b, color in regimes:
            draw.rectangle((tx(a), top, tx(b), bottom), fill=color)
        for val in range(-int(limit), int(limit) + 1):
            y = py(val)
            draw.line((LEFT, y, RIGHT, y), fill="#cbd4df", width=1)
            text(LEFT - 22, y, str(val), 21, MUTED, anchor="rm")
        for tick in (-1.2, -1.0, -0.8, -0.6, -0.4, -0.2, 0.0):
            x = tx(tick)
            draw.line((x, top, x, bottom), fill="#d7dfe8", width=1)
            label = "0" if tick == 0 else f"{tick:.1f}"
            text(x, bottom + 11, label, 21, MUTED, anchor="ma")
        draw.line((LEFT, py(0), RIGHT, py(0)), fill="#9baabb", width=2)
        for tau, color, _ in estimates:
            dash(tx(tau), top, bottom, color)
        draw.line((tx(-1), top, tx(-1), bottom), fill="#788393", width=2)
        draw.line((tx(-2 / 3), top, tx(-2 / 3), bottom), fill="#111c2b", width=4)

        # Unequal dash spacing makes coinciding branch components visible.
        for branch, color in enumerate(COLORS):
            coords = [(tx(t), py(getattr(row[branch], which)))
                      for t, row in zip(ts, calculated)]
            if branch < 2:
                draw.line(coords, fill=color, width=5)
            else:
                for k in range(0, len(coords) - 1, 9):
                    draw.line(coords[k:k + 6], fill=color, width=3)
        if which == "real":
            for val in (-1, 1):
                x, y = tx(-2 / 3), py(val)
                draw.ellipse((x - 7, y - 7, x + 7, y + 7),
                             fill="white", outline="#111c2b", width=3)
        else:
            x, y = tx(-2 / 3), py(0)
            draw.ellipse((x - 7, y - 7, x + 7, y + 7),
                         fill="white", outline="#111c2b", width=3)
        draw.rectangle((LEFT, top, RIGHT, bottom), outline="#aab7c8", width=1)
        text(RIGHT + 22, bottom + 11, "τ", 23, MUTED)

    text(tx(-1.10), 670, "Purely imaginary", 21, MUTED, anchor="ma")
    text(tx(-5 / 6), 670, "Off-axis quartet", 21, "#895b2d", anchor="ma")
    text(tx(-0.32), 670, "All four zeros real", 23, "#27633a", True, "ma")
    text(tx(-2 / 3), 700, "Exact first collision: τ = −2/3; double roots at z = ±1",
         23, INK, True, "ma")

    text(80, 1160, "Polynomial control, not the Riemann xi function. Curves use the quadratic formula; the plot is not the proof.",
         22, MUTED)
    text(80, 1197, "Coincident components overlap. Colors follow ±√w±; branch identities at double roots are conventional.",
         22, MUTED)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUTPUT)
    residual = max(abs(z ** 4 - (10 + 12 * t) * z ** 2 + 9 + 20 * t + 12 * t ** 2)
                   for t, row in zip(ts, calculated) for z in row)
    print(json.dumps({"output": str(OUTPUT), "pixels": [WIDTH, HEIGHT],
                      "parameter_samples": len(ts),
                      "max_float_residual_for_plot_only": residual,
                      "proof": "exact-quartic-proof.md; verify_exact.py"}, indent=2))


if __name__ == "__main__":
    main()
