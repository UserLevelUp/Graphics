"""Insert two 28-second scenes before the accepted video's repository card."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import textwrap

import imageio_ffmpeg

FPS, INSERT, ADDED, TOTAL = 24, 252, 56, 320
VOICE_OFFSET = 0.15


def seconds(value):
    h, m, s, ms = map(int, re.fullmatch(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", value).groups())
    return h * 3600 + m * 60 + s + ms / 1000


def timestamp(value):
    ms = round(value * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def captions(old, scenes, voices):
    blocks = []
    for block in re.split(r"\n\s*\n", old.strip()):
        lines = block.splitlines()
        start, end = map(seconds, lines[1].split(" --> "))
        if not 0 <= start < end <= 264:
            raise ValueError("Baseline caption lies outside the accepted 264-second video")
        text = "\n".join(lines[2:])
        if start < INSERT:
            blocks.append((start, min(end, INSERT), text))
        if end > INSERT:
            blocks.append((max(start, INSERT) + ADDED, end + ADDED, text))
    for index, scene in enumerate(scenes):
        voice = voices[scene["id"]]
        duration = float(voice["durationSeconds"])
        if not math.isfinite(duration) or not 0 < duration <= 28 - VOICE_OFFSET:
            raise ValueError(f"Narration does not fit scene: {scene['id']}")
        if "prompt" in voice and voice["prompt"] != scene["narration"]:
            raise ValueError(f"Narration text mismatch: {scene['id']}")
        start = INSERT + index * 28 + VOICE_OFFSET
        blocks.append((start, start + duration, textwrap.fill(scene["narration"], 64)))
    return "\n\n".join(f"{i}\n{timestamp(lo)} --> {timestamp(hi)}\n{text}"
                         for i, (lo, hi, text) in enumerate(sorted(blocks), 1)) + "\n"


def transcript(old, scenes):
    pattern = r"^\d{2}:\d{2}:\d{2},\d{3}"
    entries = list(re.finditer(pattern, old, re.M))
    if not entries or not any(seconds(m[0]) == INSERT for m in entries):
        raise ValueError("Baseline transcript lacks the expected repository card at 252 seconds")
    shifted = re.sub(pattern, lambda m: timestamp(seconds(m[0]) + (ADDED if seconds(m[0]) >= INSERT else 0)), old, flags=re.M)
    boundary = re.search(r"^" + re.escape(timestamp(INSERT + ADDED)), shifted, re.M).start()
    new = "".join(f"{timestamp(INSERT + index * 28)}  {scene['title']}\n{scene['narration']}\n\n"
                  for index, scene in enumerate(scenes))
    return shifted[:boundary] + new + shifted[boundary:]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    base = Path(__file__).resolve().parent
    contract = json.loads((base / "presentation.json").read_text(encoding="utf-8-sig"))
    if (contract["baselineSeconds"], contract["insertAtSeconds"], contract["insertSeconds"], contract["totalSeconds"]) != (264, INSERT, ADDED, TOTAL):
        raise ValueError("Unexpected assembly timing contract")
    scenes = contract["scenes"]
    if [(s["id"], s["duration"]) for s in scenes] != [("finite_prime", 28), ("phase_proof", 28)]:
        raise ValueError("Expected finite-prime then phase-proof scenes, each 28 seconds")
    old = Path(contract["baselineVideo"])
    inputs = [old, output / "finite-prime-scene.mp4", output / "phase-proof-scene.mp4", output / "updated-repository-card.mp4"]
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)
    if sha256(old) != contract["baselineVideoSha256"]:
        raise ValueError("Accepted baseline video fingerprint changed")
    rows = json.loads((base / "evidence/voice-production.json").read_text(encoding="utf-8-sig"))["clips"]
    voices = {row["id"]: row for row in rows}
    if len(voices) != len(rows) or not {"finite_prime", "phase_proof"} <= voices.keys():
        raise ValueError("Voice report has duplicate or missing scene IDs")
    new_captions = captions((old.parent / "captions.srt").read_text(encoding="utf-8-sig"), scenes, voices)
    new_transcript = transcript((old.parent / "transcript.txt").read_text(encoding="utf-8-sig"), scenes)

    graph = (
        "[0:v]fps=24,trim=end_frame=6048,setpts=PTS-STARTPTS,setsar=1[v0];"
        "[1:v]fps=24,trim=end_frame=672,setpts=PTS-STARTPTS,setsar=1[v1];"
        "[2:v]fps=24,trim=end_frame=672,setpts=PTS-STARTPTS,setsar=1[v2];"
        "[3:v]fps=24,trim=end_frame=288,setpts=PTS-STARTPTS,setsar=1[v3];"
        "[0:a]asplit=2[oldprefix][oldrepo];"
        "[oldprefix]atrim=end=252,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a0];"
        "[1:a]apad,atrim=duration=28,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a1];"
        "[2:a]apad,atrim=duration=28,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a2];"
        "[oldrepo]atrim=start=252:end=264,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a3];"
        "[v0][a0][v1][a1][v2][a2][v3][a3]concat=n=4:v=1:a=1[v][a]"
    )
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    encoding = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                "-r", "24", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    dest = output / "presentation-with-finite-proof.mp4"
    command = [ffmpeg, "-hide_banner", "-y"]
    for path in inputs:
        command += ["-i", str(path)]
    command += ["-filter_complex", graph, "-map", "[v]", "-map", "[a]"] + encoding + ["-frames:v", "7680", "-t", "320", str(dest)]
    preview = [ffmpeg, "-hide_banner", "-y", "-i", str(dest), "-filter_complex",
               "[0:v]trim=start_frame=6048:end_frame=7392,setpts=PTS-STARTPTS[v];[0:a]atrim=start=252:end=308,asetpts=PTS-STARTPTS[a]",
               "-map", "[v]", "-map", "[a]"] + encoding + ["-frames:v", "1344", "-t", "56", str(output / "proof-demonstration.mp4")]
    (base / "evidence").mkdir(exist_ok=True)
    with (base / "evidence/assembly.log").open("w", encoding="utf-8") as log:
        for argv in (command, preview):
            log.write(json.dumps({"argv": argv}) + "\n")
            log.flush()
            subprocess.run(argv, stdout=log, stderr=log, check=True)
    (output / "captions.srt").write_text(new_captions, encoding="utf-8")
    (output / "transcript.txt").write_text(new_transcript, encoding="utf-8")
    print(json.dumps({"video": str(dest), "expectedSeconds": TOTAL, "expectedFrames": TOTAL * FPS,
                      "proofPreviewSeconds": 56, "repositoryCard": [308, 320],
                      "preservation": "Accepted source unchanged; derived video and audio re-encoded."}))


if __name__ == "__main__":
    main()
