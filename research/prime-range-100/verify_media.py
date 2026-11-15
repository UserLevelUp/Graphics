"""Bounded technical QA for the 320-second finite-prime/phase-model video.

Requires NumPy, Pillow, imageio-ffmpeg and the accepted origin-trail QA helpers.
Run only after assembly: python verify_media.py --output PATH
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
HELPER = BASE.parent / "zeta-origin-trail" / "verify_revision.py"
# Compile without importing a bytecode cache or running the prior verifier.
_helpers = {"__name__": "accepted_media_helpers", "__file__": str(HELPER)}
exec(compile(HELPER.read_text(encoding="utf-8"), str(HELPER), "exec"), _helpers)
sha256, decode, frame, audio, compare_audio, probe = (
    _helpers[k] for k in ("sha256", "decode_and_probe", "frame", "audio",
                         "audio_comparison", "pixel_probe"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    out = parser.parse_args(argv).output.resolve()
    contract = json.loads((BASE / "presentation.json").read_text(encoding="utf-8-sig"))
    old, old_aep = Path(contract["baselineVideo"]), Path(contract["baselineProject"])
    video, aep = out / "presentation-with-finite-proof.mp4", out / "presentation-with-finite-proof.aep"
    for path in (old, old_aep, video, aep):
        if not path.is_file() or not path.stat().st_size:
            parser.error(f"Completed media/source required before QA: {path}")
    evidence, preview = BASE / "evidence", out / "preview"
    evidence.mkdir(exist_ok=True); preview.mkdir(exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    report = dict(traceId="graph.primes.range100.media.verify", status="running", checks=[],
                  startedAtUtc=datetime.now(timezone.utc).isoformat(),
                  presentationSha256=sha256(BASE / "presentation.json"), helperSha256=sha256(HELPER),
                  thresholds=dict(pixelRmseExclusive=3, paletteRgbDistanceExclusive=8,
                                  audioCorrelationMin=.995, audioNormalizedRmseMax=.12,
                                  audioAbsoluteRmseMax=.01, audioFixedLagSecondsExclusive=.020),
                  limits=["Technical QA; final visual/content review remains separate.",
                          "101 indexed tile fills are checked; digit glyphs and prose are not OCR-verified.",
                          "Unchanged video is sampled; audio comparisons cover both complete preserved ranges.",
                          "Audio presence/correlation is not speech transcription or a narration-content certificate.",
                          "The exact mathematical certificate is accepted separately; animation is not an RH proof."])

    def check(name, passed, detail):
        report["checks"].append(dict(id=name, passed=bool(passed), detail=detail))
        if not passed:
            raise AssertionError(f"{name}: {detail}")

    def protected(stage):
        hashes = dict(video=sha256(old), project=sha256(old_aep))
        check("baseline_hashes_" + stage, hashes == dict(video=contract["baselineVideoSha256"],
              project=contract["baselineProjectSha256"]), hashes)

    try:
        check("timing_contract", [contract[k] for k in ("baselineSeconds", "insertAtSeconds", "insertSeconds", "totalSeconds")]
              == [264, 252, 56, 320] and contract["sourceCardInterval"] == [308, 320], "264 + 56 = 320 seconds")
        protected("before")
        print("Decoding both complete videos and audio streams...", flush=True)
        for label, path, seconds, count in (("baseline", old, 264, 6336), ("revised", video, 320, 7680)):
            data = decode(ff, path, evidence, label)
            check(label + "_media", data["frames"] == count and data["size"] == [1920, 1080]
                  and abs(data["fps"] - 24) < 1e-9 and abs(data["seconds"] - seconds) <= .05, data)
            report[label + "Media"] = data
        shots, phase = [], {}
        for label, time in [("prime-10s", 262)] + [(f"phase-{t}s", 280 + t) for t in (2, 6, 10, 14, 18)] + [("final-card", 319)]:
            pixels = frame(ff, video, time)
            Image.fromarray(pixels).save(preview / (label + ".png"))
            shots.append(dict(label=label, seconds=time, path=str(preview / (label + ".png"))))
            if label.startswith("phase-"): phase[time - 280] = pixels
            if label == "prime-10s": prime = pixels
        sheet = Image.new("RGB", (1440, 894), (16, 23, 36)); draw = ImageDraw.Draw(sheet)
        for i, shot in enumerate(shots):
            x, y = i % 3 * 480, i // 3 * 298
            with Image.open(shot["path"]) as image: sheet.paste(image.resize((480, 270)), (x, y + 28))
            draw.text((x + 8, y + 7), f"{shot['label']}  {shot['seconds']}s", fill="white")
        sheet.save(preview / "contact-sheet.png")
        report.update(previewFrames=shots, contactSheet=str(preview / "contact-sheet.png"))
        for time in (7, 14.5, 20, 28.5, 35, 40.5, 60, 96, 130, 148, 167, 186, 206, 228, 248, 251.5):
            a, b = (frame(ff, path, time, (480, 270)).astype(float) for path in (old, video))
            rmse = float(np.sqrt(np.mean((a - b) ** 2)))
            check(f"preserved_pixels_{time:g}", rmse < 3, dict(seconds=time, rgbRmse=rmse))
        certificate = json.loads((BASE / "certificate.json").read_text(encoding="utf-8"))
        accepted = json.loads((evidence / "validation.json").read_text(encoding="utf-8-sig"))
        check("accepted_certificate_binding", accepted["status"] == "passed" and
              accepted["certificateSha256"] == sha256(BASE / "certificate.json"), accepted["certificateSha256"])
        rows = certificate["records"]
        check("certificate_domain", [r["n"] for r in rows] == list(range(101)), "Each integer 0 through 100 once, in order")
        def tile(n, expected=(0, 0, 0)):
            return probe(prime, 550 + n % 11 * 57 + 3, 410 + n // 11 * 43 + 18, expected, radius=1)
        colors = {kind: tile(n)["medianRgb"] for kind, n in (("prime", 2), ("composite", 4), ("neither", 0))}
        pairs = [(a, b) for a in colors for b in colors if a < b]
        separation = {a + "/" + b: float(np.linalg.norm(np.array(colors[a]) - colors[b])) for a, b in pairs}
        check("tile_classes_visually_distinct", min(separation.values()) > 16, separation)
        report["tileCalibration"] = dict(referenceIntegers=dict(prime=2, composite=4, neither=0), measuredRgb=colors)
        for row in rows:
            data = tile(row["n"], colors[row["classification"]])
            check(f"integer_{row['n']}_{row['classification']}", data["passed"], data)
        report["tileScope"] = "101 position-indexed classification fills; native number labels require visual review."
        positions = [(980, 600), (850, 470), (720, 600), (850, 730)]
        amber = probe(phase[2], *positions[0], (0, 0, 0), radius=1)["medianRgb"]
        report["phaseMarkerCalibration"] = dict(timeSeconds=282, pixel=list(positions[0]), measuredRgb=amber)
        for t, index in ((2, 0), (6, 1), (10, 2), (14, 3), (18, 0)):
            for other, pos in enumerate(positions):
                data = probe(phase[t], *pos, amber, radius=1)
                check(f"phase_{t}_cardinal_{other}", data["passed"] if other == index else data["rgbDistance"] > 16, data)
        print("Checking complete preserved PCM ranges and inserted signals...", flush=True)
        oa, na = audio(ff, old), audio(ff, video)
        check("audio_durations", abs(len(oa) / 16000 - 264) <= .05 and abs(len(na) / 16000 - 320) <= .05,
              dict(baseline=len(oa) / 16000, revised=len(na) / 16000))
        for start, end, newstart in ((0, 252, 0), (252, 264, 308)):
            data = compare_audio(oa[start * 16000:end * 16000], na[newstart * 16000:(newstart + end - start) * 16000])
            data.update(baselineRange=[start, end], revisedRange=[newstart, newstart + end - start])
            check(f"preserved_audio_{start}_{end}", data["passed"], data)
        for label, start in (("finite_prime", 252), ("phase_model", 280)):
            segment = na[start * 16000:(start + 28) * 16000].astype(float)
            rms, peak = float(np.sqrt(np.mean(segment ** 2))), float(np.max(np.abs(segment)))
            check(label + "_audio_signal", rms > .001 and peak < 1.05, dict(rms=rms, peak=peak))
        protected("after")
        report.update(status="technical_pass_visual_review_pending", videoSha256=sha256(video), projectSha256=sha256(aep),
                      scope=dict(preservedVisuals=[0, 252], finitePrime=[252, 280], phaseModel=[280, 308],
                                 refreshedRepository=[308, 320], preservedAudio="old0-252->new0-252; old252-264->new308-320"))
    except Exception as exc:
        report.update(status="failed", error=dict(type=type(exc).__name__, message=str(exc)))
    report.update(finishedAtUtc=datetime.now(timezone.utc).isoformat(), passedChecks=sum(c["passed"] for c in report["checks"]))
    (evidence / "media-qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report.get(k) for k in ("status", "passedChecks", "error")}, indent=2))
    return 0 if report["status"] == "technical_pass_visual_review_pending" else 1


if __name__ == "__main__":
    raise SystemExit(main())
