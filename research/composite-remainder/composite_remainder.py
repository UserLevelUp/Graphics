"""Exact odd-composite coefficients from nontrivial factor pairs.

defines: graph.primes.composite_remainder.model
No prime list or prime oracle is an input to these functions.
"""
from math import isqrt


def natural(value):
    if type(value) is not int:
        raise TypeError('Expected an exact nonnegative integer (not bool).')
    if value < 0:
        raise ValueError('Expected a nonnegative integer.')
    return value


def odd_coefficient(n):
    """[z^n] U(z), U=sum_{odd d>=3} z^(d*d)/(1-z^(2*d))."""
    natural(n)
    if n < 3 or n % 2 == 0:
        return 0
    return sum(n // d - (n - 1) // d for d in range(3, isqrt(n) + 1, 2))


def factor_pairs(n):
    """All unordered odd factor pairs with both factors at least 3."""
    natural(n)
    if n < 3 or n % 2 == 0:
        return []
    return [(d, n // d) for d in range(3, isqrt(n) + 1, 2) if n % d == 0]


def classify(n):
    """Classify a candidate; the coefficient alone applies only to odd n>1."""
    natural(n)
    if n < 2:
        return 'neither'
    if n == 2:
        return 'prime'
    if n % 2 == 0:
        return 'composite'
    return 'composite' if odd_coefficient(n) else 'prime'


def finite_unordered(limit):
    """Coefficients through limit, computed by the finite geometric expansions."""
    natural(limit)
    coefficients = [0] * (limit + 1)
    for d in range(3, isqrt(limit) + 1, 2):
        for n in range(d*d, limit + 1, 2*d):
            coefficients[n] += 1
    return coefficients


def finite_ordered(limit):
    """Count ordered odd factor pairs with both factors >=3."""
    natural(limit)
    coefficients = [0] * (limit + 1)
    for d in range(3, limit // 3 + 1, 2):
        for n in range(3*d, limit + 1, 2*d):
            coefficients[n] += 1
    return coefficients


def finite_subtraction(limit):
    """All odd factor pairs minus both unit-factor families, plus their overlap."""
    natural(limit)
    all_pairs = [0] * (limit + 1)
    for d in range(1, limit + 1, 2):
        for n in range(d, limit + 1, 2*d):
            all_pairs[n] += 1
    for n in range(1, limit + 1, 2):
        all_pairs[n] -= 2
    if limit >= 1:
        all_pairs[1] += 1  # (1,1) belongs to both removed families.
    return all_pairs


def batch_classification(limit):
    counts = finite_unordered(limit)
    return [n == 2 or (n > 2 and n % 2 == 1 and counts[n] == 0)
            for n in range(limit + 1)]


def geometric_terms(limit):
    """The exact finite polynomial expansion, grouped by its smaller factor."""
    natural(limit)
    return [dict(factor=d, exponents=list(range(d*d, limit+1, 2*d)))
            for d in range(3, isqrt(limit)+1, 2)]
