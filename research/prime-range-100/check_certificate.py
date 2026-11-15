"""Independent exhaustive-definition cross-check and adversarial certificate checks."""
import copy
import hashlib
import json
from pathlib import Path
from prime_certificate import verify, evaluate_predictions

base = Path(__file__).resolve().parent
path = base/'certificate.json'
certificate = json.loads(path.read_text(encoding='utf-8'))
summary = verify(certificate)
# Cross-check using EVERY proper divisor, not the generator's four-prime sieve.
definition_primes = [n for n in range(2, 101) if all(n % d for d in range(2, n))]
assert summary['primes'] == definition_primes
assert summary['counts'] == dict(prime=25, composite=74, neither=2)
mutations = []
for name, mutation in [
    ('missing_integer', lambda c: c['records'].pop(49)),
    ('one_called_prime', lambda c: c['records'].__setitem__(1, dict(n=1, classification='prime', remainders=[]))),
    ('square49_called_prime', lambda c: c['records'].__setitem__(49, dict(n=49, classification='prime', remainders=[dict(divisor=p,remainder=49%p) for p in (2,3,5,7)]))),
    ('omit_square_boundary_divisor', lambda c: c['records'].__setitem__(49, dict(n=49, classification='prime', remainders=[dict(divisor=p,remainder=49%p) for p in (2,3,5)]))),
    ('false_factor_for97', lambda c: c['records'].__setitem__(97, dict(n=97, classification='composite', divisor=7, cofactor=13))),
    ('incorrect_prime_remainder', lambda c: c['records'][97]['remainders'][0].__setitem__('remainder',0)),
]:
    damaged=copy.deepcopy(certificate);mutation(damaged)
    try:verify(damaged)
    except ValueError:mutations.append(dict(case=name,rejected=True))
    else:raise AssertionError('Accepted invalid certificate: '+name)
fixture={'predictions':[dict(n=n,isPrime=n in definition_primes) for n in range(101)]}
assert evaluate_predictions(certificate,fixture)['exactMatch']
fixture['predictions'][49]['isPrime']=True
result=evaluate_predictions(certificate,fixture)
assert not result['exactMatch'] and result['errors']==[dict(n=49,predictedPrime=True,actualPrime=False)]
report=dict(traceId='graph.primes.range100.validation',status='passed',certificateSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            exhaustiveDefinitionCrosscheck=True,integersCovered=101,summary=summary,tamperChecks=mutations,
            evaluatorChecks=['Oracle fixture scores exactly; this is an evaluator test, not a proposed predictor.','Changing49 to prime yields exactly one false positive.'],
            limits='Replayable elementary certificate and independent finite cross-check; no proof assistant or new RH result.')
(base/'evidence/validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],counts=summary['counts'],rejectedTamperCases=len(mutations)),indent=2))
