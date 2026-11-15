"""Verify the scoped 264-second origin-trail revision after media is assembled.

Requires imageio-ffmpeg, NumPy and Pillow. Produces technical evidence, not a
speech transcription, mathematical certificate, or final visual acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

FPS, WIDTH, HEIGHT, RATE = 24, 1920, 1080, 16000
EXPECTED_SECONDS, EXPECTED_FRAMES = 264, 6336
ORIGINAL_SECONDS, ORIGINAL_FRAMES = 252, 6048
RGB_DISTANCE_LIMIT = 8.0
PIXEL_RMSE_LIMIT = 3.0
AUDIO_CORRELATION_MIN = 0.995
AUDIO_NORMALIZED_RMSE_MAX = 0.12
AUDIO_ABSOLUTE_RMSE_MAX = 0.01
AUDIO_MAX_LAG_SECONDS = 0.020
COLORS = {"TL": (136, 102, 39), "BL": (101, 60, 133),
          "TR": (27, 115, 94), "BR": (39, 77, 136)}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command):
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): "
                           + result.stderr.decode("utf-8", "replace")[-6000:])
    return result


def decode_and_probe(ffmpeg, path, evidence, label):
    probe = run([ffmpeg, "-hide_banner", "-i", str(path), "-t", "0",
                 "-f", "null", "-"])
    header = probe.stderr.decode("utf-8", "replace")
    (evidence / f"probe-{label}.log").write_text(header, encoding="utf-8")
    video_lines = [line for line in header.splitlines()
                   if "Stream #0:" in line and "Video:" in line]
    if not video_lines:
        raise AssertionError(f"No input video stream: {path}")
    dimensions = re.search(r"\b(\d{3,5})x(\d{3,5})\b", video_lines[0])
    rate = re.search(r"\b([0-9.]+) fps\b", video_lines[0])
    duration = re.search(r"Duration: (\d+):(\d+):([0-9.]+)", header)
    if not (dimensions and rate and duration):
        raise AssertionError(f"Cannot establish dimensions, frame rate and duration: {path}")
    seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3])
    result = run([ffmpeg, "-v", "error", "-nostats", "-progress", "pipe:1",
                  "-i", str(path), "-map", "0:v:0", "-map", "0:a:0",
                  "-f", "null", "-"])
    stdout = result.stdout.decode("utf-8", "replace")
    stderr = result.stderr.decode("utf-8", "replace")
    (evidence / f"full-decode-{label}.log").write_text(stdout + stderr, encoding="utf-8")
    if stderr.strip():
        raise AssertionError(f"Decode reported errors: {stderr[-4000:]}")
    counts = re.findall(r"^frame=(\d+)\s*$", stdout, re.M)
    if not counts or "progress=end" not in stdout:
        raise AssertionError(f"Full decode did not report completion: {path}")
    return {"path": str(path), "seconds": seconds, "frames": int(counts[-1]),
            "size": [int(dimensions[1]), int(dimensions[2])],
            "fps": float(rate[1]), "fullVideoAndAudioDecodePassed": True}


def frame(ffmpeg, path, seconds, size=(WIDTH, HEIGHT)):
    command = [ffmpeg, "-v", "error", "-ss", f"{seconds:.6f}", "-i", str(path),
               "-frames:v", "1", "-vf", f"scale={size[0]}:{size[1]}",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    raw = run(command).stdout
    expected = size[0] * size[1] * 3
    if len(raw) != expected:
        raise AssertionError(f"Expected one frame at {seconds}; got {len(raw)} bytes")
    return np.frombuffer(raw, dtype=np.uint8).reshape(size[1], size[0], 3)


def audio(ffmpeg, path):
    result = run([ffmpeg, "-v", "error", "-i", str(path), "-map", "0:a:0",
                  "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"])
    samples = np.frombuffer(result.stdout, dtype="<f4")
    if not np.isfinite(samples).all():
        raise AssertionError(f"Nonfinite decoded audio: {path}")
    return samples


def audio_comparison(reference, candidate, sample_rate=RATE):
    """Estimate only a small fixed lag; compare the full aligned range afterward.

    The lag comes from the loudest two-second reference window. It cannot fix a
    time stretch, omitted narration, an inserted section, or local misalignment.
    """
    if len(reference) != len(candidate):
        raise AssertionError("Preserved audio ranges have different lengths")
    x, y = reference.astype(np.float64), candidate.astype(np.float64)
    margin = round(AUDIO_MAX_LAG_SECONDS * sample_rate)
    width = 2 * sample_rate
    if len(x) < width + 2 * margin:
        raise AssertionError("Audio preservation range is too short")
    starts = range(margin, len(x) - width - margin + 1, sample_rate)
    start = max(starts, key=lambda i: float(np.mean(x[i:i + width] ** 2)))
    anchor = x[start:start + width]
    anchor = anchor - anchor.mean()
    expanded = y[start - margin:start + width + margin]
    scores = np.correlate(expanded, anchor, mode="valid")
    lag = int(np.argmax(scores)) - margin
    if lag > 0:
        xa, ya = x[:-lag], y[lag:]
    elif lag < 0:
        xa, ya = x[-lag:], y[:lag]
    else:
        xa, ya = x, y
    signal_rms = float(np.sqrt(np.mean(xa ** 2)))
    if signal_rms <= 0.001:
        raise AssertionError("Reference audio is effectively silent")
    rmse = float(np.sqrt(np.mean((xa - ya) ** 2)))
    xc, yc = xa - xa.mean(), ya - ya.mean()
    denominator = float(np.sqrt(np.dot(xc, xc) * np.dot(yc, yc)))
    correlation = float(np.dot(xc, yc) / denominator) if denominator else 0.0
    return {"comparedSamples": len(xa), "referenceRms": signal_rms,
            "lagSamples": lag, "lagSeconds": lag / sample_rate,
            "unalignedRmse": float(np.sqrt(np.mean((x - y) ** 2))),
            "rmse": rmse, "normalizedRmse": rmse / signal_rms,
            "correlation": correlation,
            "passed": (abs(lag) < margin and correlation >= AUDIO_CORRELATION_MIN
                       and rmse <= AUDIO_ABSOLUTE_RMSE_MAX
                       and rmse / signal_rms <= AUDIO_NORMALIZED_RMSE_MAX)}


def pixel_probe(pixels, x, y, expected, radius=2):
    x, y = round(x), round(y)
    patch = pixels[y - radius:y + radius + 1, x - radius:x + radius + 1]
    if patch.shape != (radius * 2 + 1, radius * 2 + 1, 3):
        raise AssertionError("Color probe outside frame")
    median = np.median(patch.reshape(-1, 3), axis=0)
    distance = float(np.linalg.norm(median - np.array(expected)))
    return {"pixel": [x, y], "patchSize": radius * 2 + 1,
            "expectedRgb": list(expected), "medianRgb": median.tolist(),
            "rgbDistance": distance, "passed": distance < RGB_DISTANCE_LIMIT}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    base = Path(__file__).resolve().parent
    contract = json.loads((base / "contract.json").read_text(encoding="utf-8-sig"))
    out = args.output.resolve()
    video = out / "presentation-with-trail.mp4"
    project = out / "presentation-with-trail.aep"
    original = Path(contract["originalVideo"])
    original_project = Path(contract["originalProject"])
    # Do not generate evidence or previews before the requested media exists.
    for required in (video, project, original, original_project):
        if not required.is_file() or required.stat().st_size == 0:
            parser.error(f"Required completed media/source is not available: {required}")
    evidence, preview = base / "evidence", out / "preview"
    evidence.mkdir(parents=True, exist_ok=True)
    preview.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    report = {"traceId": "graph.riemann.origin_trail.media.verify",
              "status": "running", "startedAtUtc": datetime.now(timezone.utc).isoformat(),
              "contractSha256": sha256(base / "contract.json"), "checks": [],
              "thresholds": {"unchangedFrameRgbRmse": PIXEL_RMSE_LIMIT,
                             "paletteMedianRgbDistance": RGB_DISTANCE_LIMIT,
                             "audioCorrelationMin": AUDIO_CORRELATION_MIN,
                             "audioNormalizedRmseMax": AUDIO_NORMALIZED_RMSE_MAX,
                             "audioAbsoluteRmseMax": AUDIO_ABSOLUTE_RMSE_MAX,
                             "audioMaxLagSecondsExclusive": AUDIO_MAX_LAG_SECONDS},
              "limitations": [
                  "Technical verification is not final human visual review or mathematical certification.",
                  "Unchanged visual sections are sampled at listed times, not compared frame by frame.",
                  "PCM checks cover both preserved audio ranges, allowing only a reported fixed lag under20ms; AAC output is not expected to be byte-identical.",
                  "Audio correlation and signal presence do not perform speech transcription, ASR, or independent verification of spoken words.",
                  "Median color probes and palette coverage check specified rendering behavior, not all pixels or an analytic invariant.",
                  "The circle is a rendered brush demonstration, not new evidence about zeta zeros or RH."]}

    def check(name, passed, detail):
        report["checks"].append({"id": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise AssertionError(f"{name}: {detail}")

    def protected_sources(stage):
        values = {"videoSha256": sha256(original), "projectSha256": sha256(original_project)}
        check(f"protected_sources_{stage}",
              values["videoSha256"] == contract["originalVideoSha256"]
              and values["projectSha256"] == contract["originalProjectSha256"], values)
        return values

    try:
        check("contract_timing", contract["durationSeconds"] == EXPECTED_SECONDS
              and contract["sceneIntervalSeconds"] == [14, 28]
              and contract["circleScene"]["intervalSeconds"] == [28, 40], "264s; revised14-28s; inserted28-40s")
        report["protectedSourceHashes"] = protected_sources("before")
        print("Decoding original and revised video/audio...", flush=True)
        for label, path, seconds, count in (("original", original, ORIGINAL_SECONDS, ORIGINAL_FRAMES),
                                            ("revised", video, EXPECTED_SECONDS, EXPECTED_FRAMES)):
            metadata = decode_and_probe(ffmpeg, path, evidence, label)
            report[label + "Media"] = metadata
            check(label + "_media_contract", metadata["frames"] == count
                  and metadata["size"] == [WIDTH, HEIGHT] and abs(metadata["fps"] - FPS) < 1e-9
                  and abs(metadata["seconds"] - seconds) <= 0.05, metadata)

        screenshots, origin_frames, circle_frames = [], {}, {}
        for label, offset, times, target in (("origin", 14, [0.5, 6, 12.5], origin_frames),
                                            ("circle", 28, [0.5, 3, 5, 7, 9.5], circle_frames)):
            for local_time in times:
                pixels = frame(ffmpeg, video, offset + local_time)
                target[local_time] = pixels
                filename = f"{label}-{local_time:g}s.png"
                Image.fromarray(pixels).save(preview / filename)
                screenshots.append({"id": label, "localSeconds": local_time,
                                    "videoSeconds": offset + local_time,
                                    "path": str(preview / filename)})
        last_time = (EXPECTED_FRAMES - 1) / FPS
        last = frame(ffmpeg, video, last_time)
        last_path = preview / "last-frame.png"
        Image.fromarray(last).save(last_path)
        screenshots.append({"id": "last-frame", "videoSeconds": last_time, "path": str(last_path)})
        sheet = Image.new("RGB", (1440, 894), (16, 23, 36))
        draw = ImageDraw.Draw(sheet)
        for index, shot in enumerate(screenshots):
            x, y = (index % 3) * 480, (index // 3) * 298
            with Image.open(shot["path"]) as image:
                sheet.paste(image.convert("RGB").resize((480, 270)), (x, y + 28))
            draw.text((x + 8, y + 7), f"{shot['id']}  video {shot['videoSeconds']:.3f}s", fill="white")
        sheet.save(preview / "contact-sheet.png")
        report["previewFrames"] = screenshots
        report["contactSheet"] = str(preview / "contact-sheet.png")

        print("Checking unchanged samples, brush persistence and orientation...", flush=True)
        comparisons = []
        # The last repository card is intentionally refreshed and excluded.
        for old_time in [7, 13, 28.5, 35.5, 60, 84, 115.5, 130.5, 148, 167, 186, 206, 228, 239]:
            new_time = old_time if old_time < 14 else old_time + 12
            a = frame(ffmpeg, original, old_time, (480, 270)).astype(np.float64)
            b = frame(ffmpeg, video, new_time, (480, 270)).astype(np.float64)
            rmse = float(np.sqrt(np.mean((a - b) ** 2)))
            detail = {"originalSeconds": old_time, "revisedSeconds": new_time, "rgbRmse": rmse}
            check(f"unchanged_pixels_{old_time:g}", rmse < PIXEL_RMSE_LIMIT, detail)
            comparisons.append(detail)
        report["unchangedSectionFrameComparisons"] = comparisons

        geometry = contract["geometry"]
        check("palette_contract", all(tuple(geometry[key]) == COLORS[q] for key, q in
              [("topTrailColorRgb", "TL"), ("bottomTrailColorRgb", "BL"),
               ("topRightColorRgb", "TR"), ("bottomRightColorRgb", "BR")]), "Four contract RGB colors")
        # Use the protected accepted rendering as the color reference. AE's
        # export pipeline converts the raw construction RGB values consistently;
        # retain the tight 8-unit tolerance against the actual delivered palette.
        baseline = frame(ffmpeg, original, 14.5)
        reference_points = {"TL": (1260,500), "BL": (1260,630), "TR": (1380,500), "BR": (1380,630)}
        rendered_colors = {}
        calibration = {}
        for q, (x,y) in reference_points.items():
            measured = pixel_probe(baseline,x,y,COLORS[q])
            rendered_colors[q] = measured["medianRgb"]
            calibration[q] = {"referencePixel": [x,y], "rawConstructionRgb": list(COLORS[q]),
                              "acceptedRenderedRgb": measured["medianRgb"], "rawToRenderedRgbDistance": measured["rgbDistance"]}
        report["renderedPaletteCalibration"] = {"source": str(original), "timeSeconds": 14.5,
                                               "quadrants": calibration, "comparisonToleranceUnchanged": RGB_DISTANCE_LIMIT}
        for local_time, pixels in origin_frames.items():
            progress = min(1, max(0, (local_time - 1) / 11))
            origin_x = 1335 + 265 * progress
            probes = [("left_top", 1260, 500, "TL"), ("left_bottom", 1260, 630, "BL"),
                      ("moving_top_right", origin_x + 47.5, 522.5, "TR"),
                      ("moving_bottom_right", origin_x + 47.5, 617.5, "BR"),
                      ("overwrite_top", 1370, 500, "TR" if local_time < 1 else "TL"),
                      ("overwrite_bottom", 1370, 630, "BR" if local_time < 1 else "BL")]
            for label, x, y, q in probes:
                probe = pixel_probe(pixels, x, y, rendered_colors[q])
                check(f"origin_{local_time:g}_{label}", probe["passed"], probe)
            outside = pixel_probe(pixels, origin_x + 110, 500, rendered_colors["TR"])
            check(f"origin_{local_time:g}_right_tile_finite_width",
                  outside["rgbDistance"] > RGB_DISTANCE_LIMIT, outside)

        palette = np.array(list(rendered_colors.values()), dtype=np.float32)
        coverages = []
        for local_time, pixels in circle_frames.items():
            progress = min(1, max(0, (local_time - 1) / 8))
            angle = -math.pi / 2 + 2 * math.pi * progress
            cx, cy = 1165 + 210 * math.cos(angle), 600 + 210 * math.sin(angle)
            # Offsets32 avoid the current-center marker, outline, and fixed label.
            for q, dx, dy in [("TR", 32, -32), ("TL", -32, -32),
                              ("BL", -32, 32), ("BR", 32, 32)]:
                probe = pixel_probe(pixels, cx + dx, cy + dy, rendered_colors[q])
                check(f"circle_{local_time:g}_upright_{q}", probe["passed"], probe)
            if local_time in (0.5, 3, 5, 7):
                probe = pixel_probe(pixels, 1125, 350, rendered_colors["TL"])
                check(f"circle_{local_time:g}_retained_paint", probe["passed"], probe)
            crop = pixels[300:900, 900:1440].astype(np.float32)
            nearest = np.min(np.sum((crop[:, :, None, :] - palette) ** 2, axis=3), axis=2)
            coverages.append({"localSeconds": local_time,
                              "nearPalettePixels": int(np.count_nonzero(nearest < RGB_DISTANCE_LIMIT ** 2))})
        for index in range(1, len(coverages)):
            check(f"circle_coverage_grows_{index}",
                  coverages[index]["nearPalettePixels"] > coverages[index - 1]["nearPalettePixels"] + 1000,
                  {"before": coverages[index - 1], "after": coverages[index]})
        report["circlePaintCoverage"] = coverages
        for local_time, q in [(3, "BR"), (5, "TR")]:
            probe = pixel_probe(circle_frames[local_time], 1385, 610, rendered_colors[q])
            check(f"circle_{local_time:g}_newer_color_overwrites", probe["passed"], probe)

        print("Comparing complete preserved PCM ranges...", flush=True)
        old_audio, new_audio = audio(ffmpeg, original), audio(ffmpeg, video)
        check("audio_durations", abs(len(old_audio) / RATE - ORIGINAL_SECONDS) <= 0.05
              and abs(len(new_audio) / RATE - EXPECTED_SECONDS) <= 0.05,
              {"originalSeconds": len(old_audio) / RATE, "revisedSeconds": len(new_audio) / RATE})
        audio_checks = []
        for old_start, old_end, new_start, new_end in [(0, 28, 0, 28), (28, 252, 40, 264)]:
            a = old_audio[old_start * RATE:old_end * RATE]
            b = new_audio[new_start * RATE:new_end * RATE]
            result = audio_comparison(a, b)
            result.update(originalRange=[old_start, old_end], revisedRange=[new_start, new_end])
            check(f"preserved_audio_{old_start}_{old_end}", result["passed"], result)
            audio_checks.append(result)
        report["preservedAudioComparisons"] = audio_checks
        circle = new_audio[28 * RATE:40 * RATE].astype(np.float64)
        signal = {"rms": float(np.sqrt(np.mean(circle ** 2))),
                  "peak": float(np.max(np.abs(circle))), "rangeSeconds": [28, 40]}
        check("inserted_circle_audio_present", signal["rms"] > 0.001 and signal["peak"] < 1.05, signal)
        report["circleAudio"] = signal
        protected_sources("after")
        report["videoSha256"] = sha256(video)
        report["aepSha256"] = sha256(project)
        report["scope"] = {"revisedOrigin": [14, 28], "insertedCircle": [28, 40],
                           "old28to240Now": [40, 252], "refreshedRepositoryCard": [252, 264],
                           "existingAudioPreserved": "old0-28->new0-28; old28-252->new40-264",
                           "pixelComparisonExclusions": [[14, 40], [252, 264]]}
        report["status"] = "technical_pass_visual_review_pending"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    report["finishedAtUtc"] = datetime.now(timezone.utc).isoformat()
    report["passedChecks"] = sum(item["passed"] for item in report["checks"])
    (evidence / "media-qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "passedChecks": report["passedChecks"],
                      "report": str(evidence / "media-qa.json"), "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "technical_pass_visual_review_pending" else 1


if __name__ == "__main__":
    sys.exit(main())
