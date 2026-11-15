"""Exact certificate for primality on the inclusive integer range 0..100.

This is an elementary reference benchmark, not a brush prediction or RH proof.
"""
import argparse
import json
from pathlib import Path

SMALL_PRIMES = (2, 3, 5, 7)

def generate():
    rows = []
    for n in range(101):
        if n < 2:
            rows.append(dict(n=n, classification='neither', reason='zero' if n == 0 else 'unit'))
            continue
        tested = [p for p in SMALL_PRIMES if p*p <= n]
        divisor = next((p for p in tested if n % p == 0), None)
        if divisor is not None:
            rows.append(dict(n=n, classification='composite', divisor=divisor, cofactor=n//divisor))
        else:
            rows.append(dict(n=n, classification='prime', remainders=[dict(divisor=p, remainder=n % p) for p in tested]))
    return dict(schema='finite-prime-certificate-v1', traceId='graph.primes.range100.certificate',
                lower=0, upper=100, trialPrimes=list(SMALL_PRIMES), records=rows)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify(certificate):
    require(certificate.get('schema') == 'finite-prime-certificate-v1', 'Unsupported schema')
    require(type(certificate.get('lower')) is int and certificate['lower'] == 0, 'Lower bound must be0')
    require(type(certificate.get('upper')) is int and certificate['upper'] == 100, 'Upper bound must be100')
    require(certificate.get('trialPrimes') == list(SMALL_PRIMES), 'Wrong trial-prime basis')
    rows = certificate.get('records')
    require(isinstance(rows, list) and len(rows) == 101, 'Exactly101 records required')
    counts = dict(prime=0, composite=0, neither=0)
    primes = []
    for n, row in enumerate(rows):
        require(type(row.get('n')) is int and row['n'] == n, 'Missing, reordered or duplicate integer')
        kind = row.get('classification')
        require(kind in counts, f'Unknown classification at{n}')
        if kind == 'neither':
            require(n in (0, 1), f'Only0and1 are neither in this domain: {n}')
            require(row.get('reason') == ('zero' if n == 0 else 'unit'), 'Wrong boundary reason')
        elif kind == 'composite':
            d, q = row.get('divisor'), row.get('cofactor')
            require(type(d) is int and type(q) is int and 1 < d < n and 1 < q < n and d*q == n,
                    f'Invalid nontrivial factor witness at{n}')
        else:
            require(n >= 2, 'Prime domain begins at2')
            expected = [p for p in SMALL_PRIMES if p*p <= n]
            residues = row.get('remainders')
            require(isinstance(residues, list) and len(residues) == len(expected), f'Incomplete divisibility coverage at{n}')
            for p, record in zip(expected, residues):
                d, r = record.get('divisor'), record.get('remainder')
                require(type(d) is int and d == p and type(r) is int and 0 < r < p and r == n % p,
                        f'Invalid prime remainder at{n}, divisor{p}')
            primes.append(n)
        counts[kind] += 1
    return dict(status='verified', interval=[0, 100], counts=counts, primes=primes,
                limit='Finite integer classification only; not a new theorem, brush predictor, or result about zeta zeros.')

def evaluate_predictions(certificate, predictions):
    """Evaluate externally supplied labels; never derives predictions from colors."""
    truth = verify(certificate)
    rows = predictions.get('predictions')
    require(isinstance(rows, list) and len(rows) == 101, 'Exactly101 predictions required')
    expected = set(truth['primes'])
    matrix = dict(truePositive=0, falsePositive=0, trueNegative=0, falseNegative=0)
    errors = []
    for n, row in enumerate(rows):
        require(type(row.get('n')) is int and row['n'] == n and type(row.get('isPrime')) is bool,
                f'Invalid or reordered prediction at{n}')
        predicted, actual = row['isPrime'], n in expected
        key = ('truePositive' if actual else 'falsePositive') if predicted else ('falseNegative' if actual else 'trueNegative')
        matrix[key] += 1
        if predicted != actual:
            errors.append(dict(n=n, predictedPrime=predicted, actualPrime=actual))
    return dict(status='evaluated', interval=[0, 100], confusionMatrix=matrix, errors=errors,
                exactMatch=not errors, limit='This public finite test does not establish generalization, independence from supplied answers, or RH.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['generate', 'verify', 'evaluate'])
    parser.add_argument('certificate', type=Path)
    parser.add_argument('--predictions', type=Path)
    args = parser.parse_args()
    if args.action == 'generate':
        value = generate();verify(value)
        args.certificate.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    value = json.loads(args.certificate.read_text(encoding='utf-8'))
    result = evaluate_predictions(value, json.loads(args.predictions.read_text(encoding='utf-8'))) if args.action == 'evaluate' else verify(value)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
