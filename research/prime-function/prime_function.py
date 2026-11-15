"""Exact primality functions of a nonnegative integer, with no input prime list.

Wilson supplies the equation; trial division supplies a cheaper equivalent
baseline. Phase values are illustrations and never determine the answer.
defines: graph.primes.function
"""
from __future__ import annotations

import argparse
import json
import math


def integer_domain(n: int) -> None:
    if type(n) is not int or n < 0:
        raise ValueError('Use a nonnegative integer, excluding bool.')


def trial(n: int) -> dict:
    """Exact integer trial division, skipping even divisors after checking 2."""
    integer_domain(n)
    if n < 2:
        return dict(indicator=0, classification='neither', divisor=None, checks=0)
    if n == 2:
        return dict(indicator=1, classification='prime', divisor=None, checks=0)
    checks = 1
    if n % 2 == 0:
        return dict(indicator=0, classification='composite', divisor=2, checks=checks)
    for d in range(3, math.isqrt(n) + 1, 2):
        checks += 1
        if n % d == 0:
            return dict(indicator=0, classification='composite', divisor=d, checks=checks)
    return dict(indicator=1, classification='prime', divisor=None, checks=checks)


def wilson(n: int) -> dict:
    """R(n)=((n-1)!+1) mod n; use exact modular products and safe early exit."""
    integer_domain(n)
    if n < 2:
        return dict(indicator=0, classification='neither', factorialMod=None,
                    residue=None, multiplications=0, phaseDegrees=None)
    accumulator = 1
    multiplications = 0
    for k in range(2, n):
        accumulator = (accumulator * k) % n
        multiplications += 1
        if accumulator == 0:
            break
    residue = (accumulator + 1) % n
    indicator = 1 // (1 + residue)
    return dict(indicator=indicator, classification='prime' if indicator else 'composite',
                factorialMod=accumulator, residue=residue, multiplications=multiplications,
                phaseDegrees=360 * (residue / n))


def f(n: int, method: str = 'trial') -> int:
    """The exact 0/1 prime indicator, evaluated by either established method."""
    if method == 'trial': return trial(n)['indicator']
    if method == 'wilson': return wilson(n)['indicator']
    raise ValueError('method must be trial or wilson')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('n', type=int, nargs='+')
    parser.add_argument('--method', choices=('trial','wilson','both'), default='trial')
    args = parser.parse_args()
    rows = []
    for n in args.n:
        try:
            integer_domain(n)
        except ValueError as exc:
            parser.error(str(exc))
        row = dict(n=n)
        if args.method in ('trial','both'): row['trial'] = trial(n)
        if args.method in ('wilson','both'): row['wilson'] = wilson(n)
        if args.method == 'both':
            assert row['trial']['indicator'] == row['wilson']['indicator']
        rows.append(row)
    print(json.dumps(dict(traceId='graph.primes.function.evaluate', results=rows,
        limit='Exact integer tests using established mathematics. No input prime list, phase-based shortcut, or RH result.'), indent=2))


if __name__ == '__main__': main()
