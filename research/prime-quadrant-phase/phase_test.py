"""Wilson-derived exact quadrant test, without input prime labels.

defines: graph.primes.quadrant_phase
consumer: graph.primes.function
"""
from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction


def quadrant(x: int, y: int) -> int:
    """Canonical open quadrant from exact integer signs; axes are undefined."""
    if type(x) is not int or type(y) is not int or x == 0 or y == 0:
        raise ValueError('Use nonzero exact integer coordinates.')
    return (1 if x > 0 else 2) if y > 0 else (4 if x > 0 else 3)


def phase_test(n: int) -> dict:
    """Compute F(n)=(1+i)*i**R(n), then decide from its quadrant.

    Coordinates are evaluated as exact quarter turns, never floating complex
    powers or huge factorials. Runtime still includes the Wilson computation.
    """
    if type(n) is not int or n < 0:
        raise ValueError('Use a nonnegative integer, excluding bool.')
    if n < 2:
        return dict(n=n, defined=False, classification='neither', indicator=0,
                    factorialMod=None, residue=None, x=None, y=None,
                    quadrant=None, angleDegrees=None, multiplications=0)
    accumulator = 1
    multiplications = 0
    for k in range(2, n):
        accumulator = (k * accumulator) % n
        multiplications += 1
        if accumulator == 0:
            break  # Multiplying by further integers cannot change zero mod n.
    residue = (accumulator + 1) % n
    # Algebraic multiplication by i cycles the signs. No primality branch here.
    x, y = ((1, 1), (-1, 1), (-1, -1), (1, -1))[residue % 4]
    q = quadrant(x, y)
    indicator = int(q == 1)
    return dict(n=n, defined=True,
                classification='prime' if indicator else 'composite',
                indicator=indicator, factorialMod=accumulator, residue=residue,
                x=x, y=y, quadrant=q, angleDegrees=45 + 90 * (residue % 4),
                multiplications=multiplications)


def observed_quadrant(angle_degrees: float, error_degrees: float) -> dict:
    """Resolve a supplied angular interval only if wholly inside one quadrant.

    This helper ASSUMES the caller's error bound is valid; it does not certify
    that an image measurement or floating calculation meets that bound.
    """
    if (not isinstance(angle_degrees, (int, float)) or isinstance(angle_degrees, bool)
            or not isinstance(error_degrees, (int, float)) or isinstance(error_degrees, bool)):
        raise ValueError('Use finite numeric angles and a nonnegative error bound.')
    if (isinstance(angle_degrees, float) and not math.isfinite(angle_degrees)
            or isinstance(error_degrees, float) and not math.isfinite(error_degrees)
            or error_degrees < 0):
        raise ValueError('Use finite angles and a nonnegative error bound.')
    # Exact rationals preserve large integer turns and the actual values of
    # supplied floats, including tiny negative angles next to an axis. Floating
    # modulo could round a negative remainder to 360 and invent quadrant 5.
    angle, error = Fraction(angle_degrees), Fraction(error_degrees)
    local = angle % 90
    margin = min(local, 90 - local)
    q = int((angle % 360) // 90) + 1 if error < margin else None
    return dict(quadrant=q, status='resolved' if q is not None else 'uncertain',
                marginDegrees=float(margin), suppliedErrorDegrees=error_degrees)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('n', type=int, nargs='+')
    parser.add_argument('--angle-error', type=float, default=0,
                        help='Assumed angular observation error in degrees, not a certified measurement.')
    args = parser.parse_args()
    rows = []
    try:
        observed_quadrant(45, args.angle_error)  # Validate even for domain controls.
        for n in args.n:
            row = phase_test(n)
            row['observation'] = (observed_quadrant(row['angleDegrees'], args.angle_error)
                                  if row['defined'] else None)
            rows.append(row)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(dict(traceId='graph.primes.quadrant_phase.evaluate', results=rows,
        formula='R=((n-1)!+1) mod n; F=(1+i)*i^R; prime iff canonical quadrant I, n>=2.',
        limits='Wilson-derived quadrant encoding. No speedup, independent zeta classifier, or RH result.'), indent=2))


if __name__ == '__main__':
    main()
