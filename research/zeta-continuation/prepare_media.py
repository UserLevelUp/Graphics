"""Prepare a native After Effects script launcher from checked native data."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("kind", choices=["animation", "presentation"])
p.add_argument("--output", type=Path, required=True)
p.add_argument("--work", type=Path, required=True)
args = p.parse_args()
base = Path(__file__).resolve().parent
args.output.mkdir(parents=True, exist_ok=True)
args.work.mkdir(parents=True, exist_ok=True)
config = dict(output=args.output.as_posix())
if args.kind == "animation":
    config["phase"] = (args.output / "assets/phase").as_posix()
    source = base / "evidence/native/a1.values.json"
    config["data"] = json.loads(source.read_text(encoding="utf-8-sig"))
    assert len(list((args.output / "assets/phase").glob("phase*.png"))) == 121
else:
    config["story"] = json.loads((base / "storyboard.json").read_text(encoding="utf-8-sig"))
    assert config["story"]["productionGate"]["readyForProduction"]
    acceptance = json.loads((base / "evidence/animation-acceptance.json").read_text(encoding="utf-8-sig"))
    assert acceptance["status"] == "accepted"
    config["acceptedAnimation"] = True
    config["animationVideo"] = (args.output.parent / "animation/scientific-animation.mp4").as_posix()
    config["animationData"] = json.loads((base / "evidence/native/a1.values.json").read_text(encoding="utf-8-sig"))
    config["voice"] = {}
    for scene in config["story"]["scenes"]:
        candidates = [args.output / "assets/voice" / (scene["id"] + ext) for ext in (".mp3", ".wav")]
        existing = [f for f in candidates if f.is_file()]
        assert len(existing) == 1, (scene["id"], "expected one voice clip")
        config["voice"][scene["id"]] = existing[0].as_posix()
launcher = args.work / (args.kind + "-launch.jsx")
script = base / ("build_" + args.kind + ".jsx")
launcher.write_text("var CONFIG = " + json.dumps(config, ensure_ascii=True) + ";\n$.evalFile(new File(" + json.dumps(script.as_posix()) + "));\n", encoding="utf-8")
print(launcher)
