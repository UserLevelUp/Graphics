"""Verify reviewed sources and prepare a separately saved After Effects revision."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from prime_certificate import verify

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
base=Path(__file__).resolve().parent;repo=base.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
story=json.loads((base/'presentation.json').read_text(encoding='utf-8'))
for name in ['review.json','content-review.json']:
    report=json.loads((base/'evidence'/name).read_text(encoding='utf-8'));assert report['status']=='passed'
    for row in report['inputs']:
        assert sha(repo/row['path'])==row['sha256'],row['path']
certificate=json.loads((base/'certificate.json').read_text(encoding='utf-8'));verify(certificate)
assert sha(Path(story['baselineVideo']))==story['baselineVideoSha256']
assert sha(Path(story['baselineProject']))==story['baselineProjectSha256']
old=Path(story['baselineProject']).parent;a.output.mkdir(parents=True,exist_ok=True);a.work.mkdir(parents=True,exist_ok=True)
shutil.copytree(old/'assets',a.output/'assets',dirs_exist_ok=True)
for s in story['scenes']:assert (a.output/'assets/voice'/f"{s['id']}.mp3").is_file()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=base,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=base,text=True).strip()
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=base,text=True).split()[0];assert head==remote
config=dict(output=a.output.as_posix(),baseProject=Path(story['baselineProject']).as_posix(),baseOutput=old.as_posix(),sourceCheckpoint=head,reviewAccepted=True,scenes=story['scenes'],records=certificate['records'])
launcher=a.work/'proof-launch.jsx';launcher.write_text('var CONFIG = '+json.dumps(config,ensure_ascii=True)+';\n$.evalFile(new File('+json.dumps((base/'build_presentation.jsx').as_posix())+'));\n',encoding='utf-8')
(base/'evidence/source-checkpoint.json').write_text(json.dumps(dict(traceId='graph.primes.range100.source',sourceCheckpoint=head,pushed=True,branch=branch,remoteVerification=subprocess.check_output(['git','remote','-v'],cwd=base,text=True).strip()),indent=2)+'\n',encoding='utf-8')
sources=(old/'sources.txt').read_text(encoding='utf-8')+'\n\nFINITE CERTIFICATE AND PHASE MODEL\n'+(base/'proof.md').read_text(encoding='utf-8')
(a.output/'sources.txt').write_text(sources,encoding='utf-8')
print(launcher)
