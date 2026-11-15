"""Seal stage-specific evidence; integrity is not a mathematical certificate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent

def digest(path, mode="raw"):
    data = path.read_bytes()
    if mode == "text-lf":
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=["animation", "presentation"])
    p.add_argument("--seal", action="store_true")
    p.add_argument("--outputs", type=Path)
    args = p.parse_args()
    manifest_path = BASE / "evidence" / (args.stage + "-manifest.json")
    if args.seal:
        if not args.outputs:
            p.error("--outputs is required with --seal")
        if manifest_path.exists():
            p.error("A sealed manifest already exists; preserve it and assess changes before creating a new version")
        names = ["Graphics/ZetaContinuationExperiment.cs", "Graphics/ZetaContinuationForm.cs", "Graphics/ZetaSwitchExperiment.cs", "Graphics/Program.cs", "Graphics/GraphForm.cs", ".recur/config.toml", ".gitattributes"]
        names += ["research/zeta-continuation/" + s for s in ("seal_evidence.py", "prepare_media.py", "build_"+args.stage+".jsx")]
        if args.stage == "animation":
            names += ["research/zeta-continuation/" + s for s in ("track_roots.py", "verify_native.py", "requirements.txt")]
            folders = [BASE / "animation", BASE / "evidence/native"]
            names += [str(f.relative_to(ROOT)) for f in (BASE / "evidence").glob("*.json") if "manifest" not in f.name and f.name != "story-review.json"]
            names += [str(f.relative_to(ROOT)) for f in (BASE / "evidence").glob("animation-*.log")]
        else:
            names += ["research/zeta-continuation/" + s for s in ("storyboard.json", "math-scope.md", "evidence/story-review.json", "evidence/presentation-qa.json", "evidence/animation-manifest.json")]
            folders = []
        files = {ROOT / s for s in names}
        for folder in folders:
            files.update(f for f in folder.rglob("*") if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc")
        rows = []
        for f in sorted(files):
            mode = "text-lf" if f.suffix in (".cs", ".py", ".jsx", ".toml") or f.parent == BASE or f.parent == ROOT else "raw"
            rows.append(dict(path=f.relative_to(ROOT).as_posix(), sha256=digest(f,mode), mode=mode))
        media=[]
        for f in sorted(args.outputs.rglob("*")):
            if f.is_file() and f.name != "failed-build.aep":
                media.append(dict(path=f.relative_to(args.outputs).as_posix(),sha256=digest(f),bytes=f.stat().st_size))
        value=dict(schema="graph-continuation-manifest-v1",traceId="graph.riemann.continuation."+args.stage+".integrity",createdUtc=datetime.now(timezone.utc).isoformat(),baseline="f24b64c97916eb12aae25f5844458c687365fb2f",files=rows,mediaRoot=args.outputs.as_posix(),media=media,limit="Byte integrity of a finite numerical experiment and its presentation; not a proof certificate.")
        manifest_path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
    value=json.loads(manifest_path.read_text(encoding="utf-8"))
    failures=[]
    for row in value["files"]:
        f=(ROOT/row["path"]).resolve()
        if not f.is_relative_to(ROOT.resolve()) or not f.is_file() or digest(f,row["mode"]) != row["sha256"]:
            failures.append(row["path"])
    media_root=args.outputs or Path(value["mediaRoot"])
    for row in value["media"]:
        f=(media_root/row["path"]).resolve()
        if not f.is_relative_to(media_root.resolve()) or not f.is_file() or digest(f) != row["sha256"]:
            failures.append("media:"+row["path"])
    print(json.dumps(dict(status="passed" if not failures else "failed",stage=args.stage,files=len(value["files"]),media=len(value["media"]),manifestSha256=digest(manifest_path),failures=failures),indent=2))
    return bool(failures)

if __name__ == "__main__":
    raise SystemExit(main())
