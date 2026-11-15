"""Verify complete encoded chapter and assembled presentation independently.

defines: graph.riemann.lessons.media_review
Requires NumPy, Pillow and imageio-ffmpeg. Mathematical review is separate.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_chapter import Renderer

BASE = Path(__file__).resolve().parent
EXPECTED_BASE = "4dbd34ae6816c32301c017fd386202fa5e93c4e65cf5a8a225edceef3402e12e"
FPS = 24
RATE = 48000
INSERT = 308


def sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def run(command, **kwargs):
    return subprocess.run(command, check=True, capture_output=True, **kwargs)


def seconds(value):
    h, m, s = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def srt(path):
    cues = []
    for block in re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig").strip()):
        rows = block.splitlines()
        at = next(i for i, row in enumerate(rows) if " --> " in row)
        start, end = rows[at].split(" --> ")
        cues.append((seconds(start), seconds(end), " ".join(" ".join(rows[at + 1:]).split())))
    return cues


def cues_equal(actual, expected, tolerance=.003):
    assert len(actual) == len(expected), (len(actual), len(expected))
    for observed, wanted in zip(actual, expected):
        assert observed[2] == wanted[2], (observed, wanted)
        assert max(abs(observed[k] - wanted[k]) for k in (0, 1)) <= tolerance, (observed, wanted)


def validate_cues(cues, duration):
    assert cues
    for i, (a, b, text) in enumerate(cues):
        assert 0 <= a < b <= duration + .002 and text
        if i:
            assert cues[i - 1][1] <= a + .002, (i, cues[i - 1], cues[i])


def metadata(ff, path, width, height, duration, subtitles):
    probe = subprocess.run([ff, "-hide_banner", "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [line.strip() for line in probe.stderr.splitlines() if re.match(r"\s*Stream #\d+:\d+", line)]
    videos = [line for line in lines if "Video:" in line]
    audios = [line for line in lines if "Audio:" in line]
    subs = [line for line in lines if "Subtitle:" in line]
    assert len(videos) == 1 and "h264" in videos[0] and f"{width}x{height}" in videos[0] and "24 fps" in videos[0], lines
    assert len(audios) == 1 and "aac" in audios[0] and "48000 Hz" in audios[0] and "stereo" in audios[0], lines
    assert len(subs) == int(subtitles), lines
    if subtitles:
        assert "mov_text" in subs[0], lines
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    assert match
    actual = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    assert abs(actual - duration) <= .05, (actual, duration)
    return {"streamDescriptions": lines, "durationSeconds": actual}


def full_decode(ff, path, expected_frames, log_path):
    # Decode every video and audio frame under FFmpeg's strict error policy.
    result = run([ff, "-hide_banner", "-v", "error", "-xerror", "-err_detect", "explode", "-i", str(path),
                  "-map", "0:v:0", "-map", "0:a:0", "-fps_mode", "passthrough", "-progress", "pipe:1", "-nostats", "-f", "null", "NUL"])
    progress = result.stdout.decode("utf-8", errors="replace")
    errors = result.stderr.decode("utf-8", errors="replace")
    log_path.write_text(progress + "\nSTDERR:\n" + errors, encoding="utf-8")
    counts = re.findall(r"^frame=(\d+)$", progress, re.M)
    assert counts and int(counts[-1]) == expected_frames, (counts[-1:] if counts else [], expected_frames)
    assert "progress=end" in progress
    assert not errors.strip(), errors
    return {"frames": int(counts[-1]), "strictDecode": True, "stderr": errors, "logSha256": sha(log_path)}


def selected_frames(ff, path, numbers, width, height):
    numbers = sorted(set(numbers))
    selection = "+".join(f"eq(n\\,{n})" for n in numbers)
    process = subprocess.Popen([ff, "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0", "-vf", f"select={selection}",
                                "-fps_mode", "passthrough", "-an", "-sn", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    count = width * height * 3
    try:
        for number in numbers:
            data = process.stdout.read(count)
            assert len(data) == count, (path, number, len(data), count)
            yield number, np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
        extra = process.stdout.read()
        errors = process.stderr.read().decode("utf-8", errors="replace")
        assert not extra and process.wait() == 0 and not errors.strip(), errors
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def compare(actual, expected, context):
    diff = np.abs(actual.astype(np.int16) - expected.astype(np.int16))
    metrics = {"meanAbsolute": float(diff.mean()), "percentile99": float(np.percentile(diff, 99)), "fractionOver50": float(np.mean(diff > 50))}
    assert metrics["meanAbsolute"] < 4.5, (context, metrics)
    assert metrics["percentile99"] < 45, (context, metrics)
    assert metrics["fractionOver50"] < .015, (context, metrics)
    return metrics


def decode_audio(ff, path, output, duration):
    run([ff, "-v", "error", "-xerror", "-y", "-i", str(path), "-map", "0:a:0", "-vn", "-sn", "-ar", str(RATE), "-ac", "2", "-f", "f32le", str(output)])
    samples = output.stat().st_size // 8
    assert duration * RATE - 4 <= samples <= duration * RATE + 2048, (path, samples, duration * RATE)
    return np.memmap(output, dtype="<f4", mode="r").reshape(-1, 2)


def rms(signal):
    return float(np.sqrt(np.mean(np.square(signal.astype(np.float64)))))


def audio_similarity(actual, expected, context):
    assert len(actual) == len(expected)
    a = actual.astype(np.float64)
    b = expected.astype(np.float64)
    energy = float(np.sum(b * b))
    assert energy > .001
    correlation = float(np.sum(a * b) / np.sqrt(np.sum(a * a) * energy))
    ratio = rms(a) / rms(b)
    assert correlation > .97 and .90 < ratio < 1.10, (context, correlation, ratio)
    return {"correlation": correlation, "rmsRatio": ratio, "rms": rms(a), "peak": float(np.abs(a).max()), "fractionAtOrAboveFullScale": float(np.mean(np.abs(a) >= 1))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=BASE / "evidence/media-review.json")
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    decoded = args.output_dir / "review-frames"
    decoded.mkdir(parents=True, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    chapter_path = args.output_dir / "chapter.mp4"
    full_path = args.output_dir / "presentation-with-lessons.mp4"
    cm_path = args.output_dir / "chapter-manifest.json"
    am_path = args.output_dir / "assembly-manifest.json"
    cm, am = read(cm_path), read(am_path)
    base_path = Path(am["preservedSource"]["path"])
    checked_inputs = [Path(__file__), BASE / "render_chapter.py", BASE / "script.json", BASE / "evidence/explanation-review.json", cm_path, am_path, chapter_path, full_path, base_path]
    assert sha(base_path) == EXPECTED_BASE == am["preservedSource"]["sha256"]
    assert sha(BASE / "script.json") == read(BASE / "evidence/explanation-review.json")["reviewedScriptSha256"]
    for manifest, path in ((cm, chapter_path), (am, full_path)):
        assert sha(path) == manifest["video"]["sha256"]
        assert path.stat().st_size == manifest["video"]["bytes"]
        for item in manifest["inputs"]:
            source = Path(item["path"])
            assert source.is_file() and sha(source) == item["sha256"], item
            checked_inputs.append(source)
    assert (cm["width"], cm["height"], cm["fps"]) == (1280, 720, 24)
    assert cm["frames"] == round(cm["durationSeconds"] * FPS)
    assert (am["video"]["width"], am["video"]["height"], am["video"]["fps"]) == (1920, 1080, 24)
    assert am["video"]["frames"] == 320 * FPS + cm["frames"]
    assert am["chapter"]["insertAtSeconds"] == INSERT
    assert am["repositoryCard"]["startSeconds"] == INSERT + cm["durationSeconds"]
    assert am["repositoryCard"]["durationSeconds"] == 12
    initial_fingerprints = {str(p): sha(p) for p in set(checked_inputs)}
    print("Validating streams and decoding the complete chapter and presentation.", flush=True)
    streams = {
        "chapter": metadata(ff, chapter_path, 1280, 720, cm["durationSeconds"], False),
        "presentation": metadata(ff, full_path, 1920, 1080, am["video"]["durationSeconds"], True),
    }
    decodes = {
        "chapter": full_decode(ff, chapter_path, cm["frames"], args.work / "chapter-decode.txt"),
        "presentation": full_decode(ff, full_path, am["video"]["frames"], args.work / "presentation-decode.txt"),
    }
    print("Both complete streams decoded. Checking captions and scene frames.", flush=True)
    cc = srt(args.output_dir / "captions.srt")
    fc = srt(args.output_dir / "presentation-captions.srt")
    bc = srt(base_path.parent / "captions.srt")
    validate_cues(cc, cm["durationSeconds"])
    validate_cues(fc, am["video"]["durationSeconds"])
    expected = [(a + INSERT, b + INSERT, text) for a, b, text in cc]
    for a, b, text in bc:
        assert not (a < INSERT < b)
        shift = cm["durationSeconds"] if a >= INSERT else 0
        expected.append((a + shift, b + shift, text))
    cues_equal(fc, sorted(expected))
    embedded = args.work / "embedded-captions.srt"
    run([ff, "-v", "error", "-y", "-i", str(full_path), "-map", "0:s:0", "-c:s", "srt", str(embedded)])
    cues_equal(srt(embedded), fc)
    renderer = Renderer(BASE / "script.json")
    scenes = cm["scenes"]
    assert len(scenes) == len(renderer.scenes) == 12
    targets = {}
    cursor = 0
    for i, scene in enumerate(scenes):
        assert scene["id"] == renderer.scenes[i]["id"]
        assert scene["startFrame"] == cursor
        assert scene["endFrameExclusive"] - cursor == round(scene["durationSeconds"] * FPS)
        count = scene["endFrameExclusive"] - cursor
        for local in (0, count // 2, count - 1):
            targets[cursor + local] = (i, local, scene["durationSeconds"])
        cursor = scene["endFrameExclusive"]
    assert cursor == cm["frames"]
    comparisons = []
    scene_images = []
    for number, actual in selected_frames(ff, chapter_path, targets, 1280, 720):
        i, local, duration = targets[number]
        expected_image = renderer.frame(i, local / FPS, duration)
        metrics = compare(actual, np.asarray(expected_image), ("chapter", number))
        comparisons.append({"video": "chapter", "frame": number, "scene": scenes[i]["id"], "metrics": metrics})
        if local == round(duration * FPS) // 2:
            dest = decoded / f"{i + 1:02}-{scenes[i]['id']}.png"
            Image.fromarray(actual).save(dest)
            scene_images.append((i, dest))
    base_targets = [0, 321, 120 * FPS, 250 * FPS, INSERT * FPS - 1]
    base_frames = dict(selected_frames(ff, base_path, base_targets, 1920, 1080))
    card_path = args.output_dir / "repository-card.png"
    assert sha(card_path) == am["repositoryCard"]["imageSha256"]
    card = np.asarray(Image.open(card_path).convert("RGB"))
    card_start = INSERT * FPS + cm["frames"]
    full_targets = base_targets + [INSERT * FPS + n for n in targets] + [card_start, card_start + 144, am["video"]["frames"] - 1]
    for number, actual in selected_frames(ff, full_path, full_targets, 1920, 1080):
        if number < INSERT * FPS:
            expect, label = base_frames[number], "preserved_prefix"
        elif number < card_start:
            i, local, duration = targets[number - INSERT * FPS]
            expect = np.asarray(renderer.frame(i, local / FPS, duration).resize((1920, 1080), Image.Resampling.LANCZOS))
            label = scenes[i]["id"]
        else:
            expect, label = card, "repository_card"
            if number == card_start + 144:
                Image.fromarray(actual).save(decoded / "repository-card.png")
        metrics = compare(actual, expect, ("presentation", number))
        comparisons.append({"video": "presentation", "frame": number, "scene": label, "metrics": metrics})
    contact = Image.new("RGB", (1920, 1544), "#090e18")
    draw = ImageDraw.Draw(contact)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    for i, path in scene_images:
        x, y = (i % 3) * 640, (i // 3) * 386
        contact.paste(Image.open(path).resize((640, 360), Image.Resampling.LANCZOS), (x, y + 26))
        draw.text((x + 8, y), f"{i + 1:02}  {scenes[i]['id']}", font=font, fill="#eff5fc")
    contact_path = args.output_dir / "encoded-contact-sheet.png"
    contact.save(contact_path)
    print("Scene comparisons passed. Checking the complete audio timeline.", flush=True)
    audio_chapter = decode_audio(ff, chapter_path, args.work / "chapter.f32", cm["durationSeconds"])
    audio_full = decode_audio(ff, full_path, args.work / "presentation.f32", am["video"]["durationSeconds"])
    audio_base = decode_audio(ff, base_path, args.work / "base.f32", 320)
    with wave.open(str(args.output_dir / "narration.wav"), "rb") as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1, 2, RATE, round(cm["durationSeconds"] * RATE))
        combined = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    audio_checks = []
    for i, (scene, clip) in enumerate(zip(scenes, cm["voiceClips"])):
        assert clip["id"] == scene["id"] and clip["narration"] == renderer.scenes[i]["narration"]
        wav_path = Path(clip["wav"]["path"])
        assert sha(wav_path) == clip["wav"]["sha256"]
        with wave.open(str(wav_path), "rb") as w:
            assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, RATE)
            raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        assert rms(raw / 32768) > .005
        assert np.max(np.abs(raw.astype(np.int32))) < 32767, (scene["id"], "Source reaches full-scale clipping boundary")
        start = round(scene["voiceStartSeconds"] * RATE)
        end = start + len(raw)
        scene_start = round(scene["startFrame"] / FPS * RATE)
        scene_end = round(scene["endFrameExclusive"] / FPS * RATE)
        assert start - scene_start == round(.65 * RATE)
        assert scene_end - end >= round(.5 * RATE)
        assert np.array_equal(combined[start:end], raw), scene["id"]
        assert not np.any(combined[scene_start:start]) and not np.any(combined[end:scene_end])
        # FFmpeg's default mono-to-stereo rematrix uses -3 dB per channel.
        # Compare to that expected signal, not to the louder original mono channel.
        source = raw.astype(np.float64) / 32768 / np.sqrt(2)
        chapter_match = audio_similarity(audio_chapter[start:end, 0], source, (scene["id"], "chapter"))
        offset = INSERT * RATE
        presentation_match = audio_similarity(audio_full[start + offset:end + offset, 0], source, (scene["id"], "presentation"))
        assert chapter_match["fractionAtOrAboveFullScale"] < .0001 and presentation_match["fractionAtOrAboveFullScale"] < .0001
        scene_cues = [(a, b, t) for a, b, t in cc if scene["startFrame"] / FPS <= a < scene["endFrameExclusive"] / FPS]
        assert " ".join(t for a, b, t in scene_cues) == clip["narration"]
        assert abs(scene_cues[0][0] - start / RATE) < .002 and abs(scene_cues[-1][1] - end / RATE) < .002
        audio_checks.append({"scene": scene["id"], "sourceSamples": len(raw), "voiceSeconds": len(raw) / RATE, "sourcePeak": int(np.max(np.abs(raw.astype(np.int32)))), "leadSeconds": (start - scene_start) / RATE, "tailSeconds": (scene_end - end) / RATE, "sourceRetainedExactlyInNarrationWav": True, "expectedMonoToStereoGainPerChannel": float(1 / np.sqrt(2)), "chapterMatch": chapter_match, "presentationMatch": presentation_match})
    prefix_audio = []
    for at in (24, 122, 232, 310):
        a = round(at * RATE)
        shift = round(cm["durationSeconds"] * RATE) if at >= INSERT else 0
        match = audio_similarity(audio_full[a + shift:a + shift + RATE, 0], audio_base[a:a + RATE, 0], ("historical_audio", at))
        prefix_audio.append({"baseSeconds": at, "presentationSeconds": at + shift / RATE, "metrics": match})
    for p, digest in initial_fingerprints.items():
        assert sha(Path(p)) == digest, ("Input changed during review", p)
    assert sha(base_path) == EXPECTED_BASE
    report = {
        "schema": "graph-riemann-lessons-media-review-v1", "traceId": "graph.riemann.lessons.media_review", "status": "passed",
        "reviewedAtUtc": datetime.now(timezone.utc).isoformat(),
        "videos": {"chapter": {"path": str(chapter_path), "sha256": sha(chapter_path), **streams["chapter"], **decodes["chapter"]}, "presentation": {"path": str(full_path), "sha256": sha(full_path), **streams["presentation"], **decodes["presentation"]}},
        "coverage": {"completeStrictVideoAudioDecodes": 2, "chapterSceneComparisons": len(targets), "presentationSceneComparisons": len(full_targets), "sourcePrefixFrames": base_targets, "scenePositions": "first, middle, last", "voiceClips": len(audio_checks), "historicalAudioSamples": len(prefix_audio)},
        "captions": {"chapterCues": len(cc), "presentationCues": len(fc), "allHistoricalCuesPreservedAndRetimed": True, "embeddedTextAndTimingsMatchExternalSrt": True, "orderedAndNonOverlapping": True, "timingMethod": cm["captions"]["timing"]},
        "frameTolerance": {"meanAbsoluteBelow": 4.5, "percentile99Below": 45, "fractionOver50Below": .015, "reason": "H264 YUV420 encoding and intentional Lanczos upscale of the 1280 chapter inside the 1920 presentation."},
        "frameComparisons": comparisons,
        "voiceChecks": audio_checks, "historicalAudioChecks": prefix_audio,
        "preservedSource": {"path": str(base_path), "sha256": EXPECTED_BASE, "byteIdentical": True},
        "decodedContactSheet": {"path": str(contact_path), "sha256": sha(contact_path)},
        "inputs": [{"path": p, "sha256": digest} for p, digest in sorted(initial_fingerprints.items())],
        "limits": ["This verifies technical media integrity and consistency with the reviewed renderer; independent visual editorial inspection is recorded separately.", "Narration clips match the supplied script in the provider manifest. Waveform tests do not establish pronunciation or speech-recognition accuracy.", "Sentence caption timings are apportioned by word count, not forced-aligned; clip and scene boundaries are verified.", "The chapter is rendered at 1280x720 and intentionally upscaled within the 1920x1080 combined export.", "No new mathematical validation is inferred from video decoding, pixels, audio or subtitles."]
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "coverage": report["coverage"], "report": str(args.report), "contactSheet": str(contact_path)}, indent=2))


if __name__ == "__main__":
    main()
