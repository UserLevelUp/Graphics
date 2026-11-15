"""Deterministic opaque four-color brush moving clockwise around one circle.

The image is accumulated paint only. Pointer, outline, labels, and path guides
belong to native After Effects overlays and are deliberately absent here.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
import PIL

WIDTH, HEIGHT, FPS, COUNT = 1920, 1080, 24, 288
CX, CY, RADIUS = 1165, 600, 210
HALF = 48
COLORS = {
    "TR": (27, 115, 94, 255),
    "TL": (136, 102, 39, 255),
    "BL": (101, 60, 133, 255),
    "BR": (39, 77, 136, 255),
}
DEFAULT_OUTPUT = Path("C:/Users/marcn/Documents/Codex/2026-11-14/eu/outputs/riemann-origin-trail/assets/circle")


def location(frame):
    time = frame / FPS
    progress = min(1.0, max(0.0, (time - 1.0) / 8.0))
    angle = -math.pi / 2 + 2 * math.pi * progress
    return time, angle, CX + RADIUS * math.cos(angle), CY + RADIUS * math.sin(angle)


def stamp(draw, x, y):
    # Pixel cells use half-open quadrant bounds. ImageDraw's endpoints are
    # inclusive, hence the explicit -1. No blending or transparency is used.
    x, y = round(x), round(y)
    draw.rectangle((x, y - HALF, x + HALF - 1, y - 1), fill=COLORS["TR"])
    draw.rectangle((x - HALF, y - HALF, x - 1, y - 1), fill=COLORS["TL"])
    draw.rectangle((x - HALF, y, x - 1, y + HALF - 1), fill=COLORS["BL"])
    draw.rectangle((x, y, x + HALF - 1, y + HALF - 1), fill=COLORS["BR"])
    return x, y


def verify(snapshots, positions, output, max_arc_spacing, protected_paints):
    checks = []
    def check(name, condition, detail):
        if not condition:
            raise AssertionError(f"{name}: {detail}")
        checks.append({"id": name, "passed": True, "detail": detail})

    check("frame_count", len(positions) == COUNT and all((output / p["file"]).is_file() for p in positions), "288 full-frame PNG files")
    check("arc_spacing", max_arc_spacing <= 1.0, {"maximumPixelsAlongArc": max_arc_spacing})
    check("start_hold", len({p["sha256"] for p in positions[:25]}) == 1, "Frames 0..24 hold the top stamp through local time 1 second")
    check("end_hold", len({p["sha256"] for p in positions[216:]}) == 1, "Frames 216..287 hold the completed paint through the 12-second clip")
    check("clockwise_key_positions", all(abs(positions[f]["x"] - x) < 1e-9 and abs(positions[f]["y"] - y) < 1e-9 for f, x, y in [(0,1165,390),(72,1375,600),(120,1165,810),(168,955,600),(216,1165,390)]), "Top, right, bottom, left, top in increasing frame order")

    # The newest opaque stamp must have this same orientation everywhere.
    for frame in (0, 72, 120, 168, 216):
        p = positions[frame]
        expected = {"TR": (24,-24), "TL": (-24,-24), "BL": (-24,24), "BR": (24,24)}
        for quadrant, (dx,dy) in expected.items():
            check(f"orientation_{frame}_{quadrant}", snapshots[frame].getpixel((p["pixelX"]+dx,p["pixelY"]+dy)) == COLORS[quadrant], "Newest brush retains fixed screen orientation")

    probe = (1125,350)
    check("untouched_paint_persists", protected_paints == 0 and snapshots[72].getpixel(probe) == snapshots[120].getpixel(probe) == COLORS["TL"], {"pixel": probe, "stampsTouchingPixelBetweenFrames72And120": protected_paints})
    anchor = (1375,600)
    check("latest_color_overwrites", snapshots[72].getpixel(anchor) == COLORS["BR"] and snapshots[120].getpixel(anchor) == COLORS["TR"], {"pixel": anchor, "frame72": "BR blue", "frame120": "TR green"})
    last_alpha = None
    for frame in sorted(snapshots):
        image = snapshots[frame]
        alpha = image.getchannel("A")
        check(f"opaque_palette_{frame}", all(c in set(COLORS.values()) | {(0,0,0,0)} for _,c in image.getcolors(maxcolors=5) or [(1,None)]), "Only fully opaque palette paint or fully transparent background")
        if last_alpha is not None:
            check(f"paint_never_erased_{frame}", ImageChops.subtract(last_alpha, alpha).getbbox() is None, "Previously painted pixels retain full opacity")
        last_alpha = alpha
    check("center_unpainted", snapshots[287].getpixel((CX,CY)) == (0,0,0,0), "Circle interior has no raster path, marker, or outline")
    return checks


def render(output):
    output.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (WIDTH,HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    positions, snapshots = [], {}
    last_angle, png, digest = None, None, None
    max_arc_spacing, total_stamps, protected_paints = 0.0, 0, 0
    for frame in range(COUNT):
        time, angle, x, y = location(frame)
        changed = last_angle is None or angle != last_angle
        new_stamps = 0
        if last_angle is None:
            stamp(draw,x,y)
            new_stamps = 1
        elif changed:
            delta = angle - last_angle
            steps = max(1,math.ceil(RADIUS * delta))
            max_arc_spacing = max(max_arc_spacing,RADIUS * delta / steps)
            for index in range(1,steps+1):
                a = last_angle + delta * index / steps
                px,py = stamp(draw,CX+RADIUS*math.cos(a),CY+RADIUS*math.sin(a))
                if 72 < frame <= 120 and px-HALF <= 1125 < px+HALF and py-HALF <= 350 < py+HALF:
                    protected_paints += 1
            new_stamps = steps
        total_stamps += new_stamps
        if changed:
            encoded = io.BytesIO()
            image.save(encoded,format="PNG",compress_level=6,optimize=False)
            png = encoded.getvalue()
            digest = hashlib.sha256(png).hexdigest()
        filename = f"brush{frame:04}.png"
        (output / filename).write_bytes(png)
        positions.append({"frame":frame,"time":time,"x":x,"y":y,"angleRadians":angle,
                          "pixelX":round(x),"pixelY":round(y),"file":filename,"sha256":digest,"newStamps":new_stamps})
        if frame in (0,24,72,120,168,216,287):
            snapshots[frame] = image.copy()
        last_angle = angle
    checks = verify(snapshots,positions,output,max_arc_spacing,protected_paints)
    geometry = {
        "schema":"graph-four-color-circle-v1", "traceId":"graph.riemann.origin_trail.circle",
        "fps":FPS,"durationSeconds":12,"width":WIDTH,"height":HEIGHT,"offset":{"x":0,"y":0},
        "frameCount":COUNT,"firstFrame":"brush0000.png","lastFrame":"brush0287.png",
        "circle":{"center":{"x":CX,"y":CY},"radius":RADIUS,"startAngleRadians":-math.pi/2,"direction":"clockwise in screen coordinates","movementStartsSeconds":1,"movementEndsSeconds":9},
        "brush":{"width":96,"height":96,"quadrantSize":48,"orientation":"fixed screen axes","colorsRGBA":COLORS,"bounds":"half-open pixel rectangles around round(x),round(y)","composition":"opaque overwrite, latest stamp wins","accumulation":"paint persists; no fading or clearing","arcSubdivisionMaxPixels":1},
        "rasterIncludes":"Accumulated paint only; no marker, outline, guide path, or labels",
        "positions":positions,"totalStamps":total_stamps,"maximumActualArcSpacingPixels":max_arc_spacing,
        "frameSampling":"time=frame/24; frame287 begins at11.958333...s and displays until12s",
        "determinism":{"algorithm":"fixed integer rectangles and deterministic PNG encoding; no random input or timestamps","pillowVersion":PIL.__version__,"pngCompressionLevel":6},
        "validation":{"passed":True,"checkCount":len(checks),"checks":checks},
    }
    (output/"geometry.json").write_text(json.dumps(geometry,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(output),"frames":COUNT,"uniquePaintFrames":len({p['sha256'] for p in positions}),"stamps":total_stamps,"maxArcSpacing":max_arc_spacing,"checksPassed":len(checks),"finalFrameSha256":positions[-1]["sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    render(parser.parse_args().output)
