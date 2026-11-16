"""Capture the recorded development of the finite collision certificate.

defines: graph.riemann.collision_guide.discovery
consumer: graph.zeros.motion
consumer: graph.riemann.collision.next
consumer: graph.riemann.gap.proof
Trace occurrences establish links to inspect, not mathematical truth or priority.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
EVIDENCE = BASE / 'evidence'
RECUR = Path('C:/Users/marcn/.cargo/bin/recur.exe')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    EVIDENCE.mkdir(exist_ok=True)
    stages = [
        dict(commit='170993c', traceId='graph.zeros.motion',
             claim='Local-origin color and phase probes motivated examining root motion. The quadratic was an exact calibration, not a new inequality.',
             sources=['warps/graph.zeros.motion.results.complete.md']),
        dict(commit='73518fc', traceId='graph.riemann.collision',
             claim='An exact quartic exposed failure of frozen local collision forecasts. The surviving gap inequality supplied the baseline m^2/8; the next obligation explicitly retained the exterior interaction S.',
             sources=['warps/graph.riemann.collision.baseline.complete.md',
                      'warps/graph.riemann.collision.results.complete.md',
                      'warps/graph.riemann.collision.next.current.md',
                      'research/collision-proof/exact-quartic-proof.md']),
        dict(commit='cf51254', traceId='graph.riemann.gap',
             claim='Static and contracting diameter bounds strengthened the finite baseline. Both proposed formulas were supplied in the review contract before reviewer responses; those responses are audits, not invention records.',
             sources=['research/gap-bound/graph.riemann.gap.contract.current.md',
                      'research/gap-bound/interaction-bound-proof.md',
                      'warps/graph.riemann.gap.results.complete.md',
                      'warps/graph.riemann.gap.next.current.md']),
    ]
    for stage in stages:
        raw = subprocess.check_output(['git','show','--no-patch','--format=%H%n%cI%n%s',stage['commit']],cwd=REPO,text=True,encoding='utf-8').splitlines()
        stage['git'] = dict(hash=raw[0],committedAt=raw[1],subject=raw[2])
    sources = sorted(set(p for stage in stages for p in stage['sources']) | {
        'research/gap-bound/carbon/review.md',
        'research/gap-bound/codex/review.md',
        'research/gap-bound/evidence/review-audit.json',
        'research/gap-bound/carbon/runs/20261115T072203Z-fe1b6967/steering-after-01.json',
        'research/gap-bound/codex/runs/20261115T072501Z-7f5a0c47/steering-after-01.json',
    })
    queries=[]
    for name, pattern, root in [
        ('motion','graph.zeros.motion.**','warps'),
        ('collision','graph.riemann.collision.**','research/collision-proof'),
        ('gap','graph.riemann.gap.**','research/gap-bound'),
    ]:
        argv=[str(RECUR),'trace-id',pattern,'--scope','**','-e','md,json,py','-d',str(REPO/root),'--list-ids','--json']
        result=subprocess.run(argv,cwd=REPO,capture_output=True,text=True,encoding='utf-8',check=True)
        parsed=json.loads(result.stdout)
        assert parsed.get('complete') and parsed['coverage']['complete'] and parsed['output']['complete'], 'Incomplete trace inventory requires a narrower query'
        destination=EVIDENCE/f'discovery-trace-{name}.json'
        destination.write_text(json.dumps(parsed,indent=2)+'\n',encoding='utf-8')
        queries.append(dict(argv=argv,returnCode=result.returncode,report=destination.name,sha256=digest(destination)))
    receipt=dict(schema='graph-collision-discovery-v1',traceId='graph.riemann.collision_guide.discovery',
        observedAtUtc=datetime.now(timezone.utc).isoformat(),stages=stages,
        correction=dict(traceId='graph.riemann.gap.review.audit',
            observation='Carbon initially used a false product inequality. Coordinator steering identified the error, and the final review explicitly retracted it and used reciprocal distances with x(D-x) <= D^2/4.',
            implication='Review needed checking and correction. Agreement, response timing and Eventness completion do not establish proof.'),
        eventness=dict(completedScope='The finite-polynomial proof and recorded exact checks.',
            stillOpen='Infinite-system transfer remains current in graph.riemann.gap.next, and graph.riemann remains open.'),
        limits=['This reconstructs the documented development, not private thought or historical priority.',
                'The proposal predates the attached reviewer reports; exact origin before the recorded contract is not established here.',
                'No claim of mathematical novelty, new prime algorithm or RH advance follows from these records.'],
        queries=queries,sources=[dict(path=p,sha256=digest(REPO/p)) for p in sources])
    target=EVIDENCE/'discovery-provenance.json'
    target.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(report=str(target),sources=len(sources),queries=len(queries)),indent=2))


if __name__=='__main__':
    main()
