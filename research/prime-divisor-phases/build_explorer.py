"""Build an offline explorer by embedding the reviewed finite analysis."""
import argparse
import json
from pathlib import Path

base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
template=(base/'explorer.template.html').read_text(encoding='utf-8')
assert template.count('__ANALYSIS_JSON__')==1
data=json.loads((base/'evidence/analysis.json').read_text(encoding='utf-8'))
payload=json.dumps(data,separators=(',',':')).replace('</','<\\/')
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(template.replace('__ANALYSIS_JSON__',payload),encoding='utf-8')
print(args.output)
