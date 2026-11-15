"""Prepare an isolated native project revision and copied footage assets."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
base=Path(__file__).resolve().parent
contract=json.loads((base/'contract.json').read_text(encoding='utf-8'))
for key,hashkey in [('originalVideo','originalVideoSha256'),('originalProject','originalProjectSha256')]:
    assert hashlib.sha256(Path(contract[key]).read_bytes()).hexdigest()==contract[hashkey]
old=Path(contract['originalProject']).parent
a.output.mkdir(parents=True,exist_ok=True);a.work.mkdir(parents=True,exist_ok=True)
shutil.copytree(old/'assets',a.output/'assets',dirs_exist_ok=True)
for name in ['sources.txt']:
    shutil.copy2(old/name,a.output/name)
geometry=json.loads((a.output/'assets/circle/geometry.json').read_text(encoding='utf-8'))
assert len(geometry['positions'])==288 and (a.output/'assets/voice/circle.mp3').is_file()
checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=base,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=base,text=True).strip()
upstream=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=base,text=True).split()[0]
assert checkpoint==upstream
config=dict(output=a.output.as_posix(),baseProject=Path(contract['originalProject']).as_posix(),baseOutput=old.as_posix(),sourceCheckpoint=checkpoint,circlePositions=geometry['positions'])
launcher=a.work/'revision-launch.jsx'
launcher.write_text('var CONFIG = '+json.dumps(config,ensure_ascii=True)+';\n$.evalFile(new File('+json.dumps((base/'build_revision.jsx').as_posix())+'));\n',encoding='utf-8')
record=dict(traceId='graph.riemann.origin_trail.source',sourceCheckpoint=checkpoint,branch=branch,pushed=True,commands={'git remote -v':subprocess.check_output(['git','remote','-v'],cwd=base,text=True).strip()})
(base/'evidence/source-checkpoint.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(launcher)
