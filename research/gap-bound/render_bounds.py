"""Render finite-polynomial collision guarantees for the quartic control.

defines: graph.riemann.gap.render
consumer: graph.riemann.gap.proof

The image uses floating-point samples for display. The separate proof and exact
checker establish the bounds; samples and pixels do not prove inequalities.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "evidence" / "gap-bounds.png"
WIDTH, HEIGHT = 1800, 1320
LEFT, RIGHT = 170, 1650
UMAX = 0.70
OLD = 0.5
CONSTANT = 4.5 * math.log(9 / 8)
DYNAMIC = 0.9 * (1 - 3 ** (-5 / 6))
ACTUAL = 2 / 3
COLORS = {"true": "#7841b3", "old": "#6b7789",
          "constant": "#00869c", "dynamic": "#c77a0c"}
INK, MUTED = "#1b2a3c", "#536377"


def gap_squared(u: float) -> float:
    return 10 - 12 * u - 2 * math.sqrt(9 - 20 * u + 12 * u * u)


def old_lower(u: float) -> float:
    return 4 - 8 * u


def constant_lower(u: float) -> float:
    return 36 - 32 * math.exp(2 * u / 9)


def dynamic_lower(u: float) -> float:
    a = 1 - 40 * u / 36
    return a ** (-1 / 5) * (4 - 6 * (1 - a ** (6 / 5)))


def main() -> None:
    im = Image.new("RGB", (WIDTH, HEIGHT), "#fbfcff")
    draw = ImageDraw.Draw(im)

    def text(x, y, value, size=24, fill=INK, bold=False, anchor="la"):
        face = "segoeuib.ttf" if bold else "segoeui.ttf"
        f = ImageFont.truetype(str(Path("C:/Windows/Fonts") / face), size)
        draw.text((x, y), value, fill=fill, font=f, anchor=anchor)

    def px(u):
        return LEFT + u / UMAX * (RIGHT - LEFT)

    top, bottom = 270, 760

    def py(y):
        return bottom - (y + 0.12) / 4.38 * (bottom - top)

    text(80, 28, "Accounting for other zeros improves the collision guarantee", 37, bold=True)
    text(80, 83, "Quartic control: initial roots −3, −1, 1, 3; backward elapsed time u = −t ≥ 0", 27)
    text(80, 126, "P−u(z) = z⁴ − (10 − 12u)z² + 9 − 20u + 12u²", 27, MUTED)

    legends = ((80, "true", "Exact outer-pair gap"),
               (520, "old", "Gap-only lower bound"),
               (960, "constant", "Constant tail bound"),
               (1370, "dynamic", "Evolving tail bound"))
    for x, key, label in legends:
        draw.line((x, 190, x + 42, 190), fill=COLORS[key], width=5)
        text(x + 54, 172, label, 23, COLORS[key])

    text(LEFT, 222, "Squared separation of the adjacent outer zeros", 27, bold=True)
    draw.rectangle((LEFT, top, px(ACTUAL), bottom), fill="#f3edf9")
    draw.rectangle((px(ACTUAL), top, RIGHT, bottom), fill="#f2f4f7")
    for tick in range(5):
        y = py(tick)
        draw.line((LEFT, y, RIGHT, y), fill="#d0d8e3", width=1)
        text(LEFT - 23, y, str(tick), 23, MUTED, anchor="rm")
    for index in range(8):
        tick = index / 10
        x = px(tick)
        draw.line((x, top, x, bottom), fill="#dde3ec", width=1)
        text(x, bottom + 12, f"{tick:.1f}", 22, MUTED, anchor="ma")
    draw.line((LEFT, py(0), RIGHT, py(0)), fill="#8a99ac", width=2)

    curves = (("true", ACTUAL, gap_squared),
              ("old", OLD, old_lower),
              ("constant", CONSTANT, constant_lower),
              ("dynamic", DYNAMIC, dynamic_lower))
    max_reversal = 0.0
    for key, duration, fn in curves:
        samples = [duration * i / 1200 for i in range(1201)]
        # The endpoint is known symbolically to be zero; roundoff is display-only.
        values = [fn(u) for u in samples[:-1]] + [0.0]
        points = [(px(u), py(y)) for u, y in zip(samples, values)]
        draw.line(points, fill=COLORS[key], width=6 if key == "true" else 4)
        endx, endy = points[-1]
        draw.ellipse((endx - 6, endy - 6, endx + 6, endy + 6),
                     fill="white", outline=COLORS[key], width=3)
        if key != "true":
            max_reversal = max(max_reversal, max(fn(u) - gap_squared(u) for u in samples))

    for y in range(top, bottom, 17):
        draw.line((px(ACTUAL), y, px(ACTUAL), min(y + 9, bottom)),
                  fill=COLORS["true"], width=2)
    text(px(ACTUAL) - 18, top + 20, "Actual collision", 24, COLORS["true"], True, "ra")
    text(px(ACTUAL) - 18, top + 54, "u = 2/3", 24, COLORS["true"], False, "ra")
    draw.rectangle((LEFT, top, RIGHT, bottom), outline="#a7b5c8", width=1)
    text(RIGHT, bottom + 46, "Backward elapsed time u", 23, MUTED, anchor="ra")

    text(LEFT, 830, "Guaranteed collision-free duration: 0 ≤ u < T", 28, bold=True)
    improvement = (DYNAMIC / OLD - 1) * 100
    text(RIGHT, 832, f"{improvement:.2f}% longer than gap-only", 26,
         COLORS["dynamic"], True, "ra")
    rows = (("Gap-only", "old", OLD),
            ("Constant tail", "constant", CONSTANT),
            ("Evolving tail", "dynamic", DYNAMIC),
            ("Actual first collision", "true", ACTUAL))
    for index, (name, key, duration) in enumerate(rows):
        y = 910 + 75 * index
        text(LEFT, y - 33, name, 23, COLORS[key], True)
        draw.rounded_rectangle((LEFT, y, px(duration), y + 16),
                               radius=7, fill=COLORS[key])
        text(px(duration) + 16, y + 8, f"{duration:.9f}", 23,
             COLORS[key], True, "lm")

    text(80, 1200, "Finite polynomial with distinct real initial roots. Guarantees require the separate proof; plotted samples are approximate.",
         22, MUTED)
    text(80, 1238, "Lower-bound curves stop at their first zero. The exact curve stops at the actual collision. This is not an RH result or a novelty claim.",
         22, MUTED)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUTPUT)
    print(json.dumps({"output": str(OUTPUT), "pixels": [WIDTH, HEIGHT],
                      "durations": {"gap_only": OLD, "constant_tail": CONSTANT,
                                    "evolving_tail": DYNAMIC, "actual_collision": ACTUAL},
                      "improvement_percent": improvement,
                      "max_sampled_bound_minus_exact_for_plot_only": max_reversal,
                      "proof_status": "See separate proof and exact-checker evidence"}, indent=2))


if __name__ == "__main__":
    main()
