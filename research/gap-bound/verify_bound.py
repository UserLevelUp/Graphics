"""Exact finite-polynomial controls for the backward-heat minimum-gap bound.

Default: python -B verify_bound.py
Custom:  python -B verify_bound.py --roots=-3,-1,1,3
Optional: --output report.json

Inputs, heat coefficients, Sturm counts, and enclosure arithmetic use Fraction.
The finite examples check the implementation, not the general bound theorem.
This CLI requires at least three distinct real roots; the quadratic case is
outside its domain and is handled separately in the human theorem.
"""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import json
from math import factorial
from pathlib import Path
import sys

# defines: graph.riemann.gap.verify
# consumer: graph.riemann.gap.proof


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def display(value):
    with localcontext() as context:
        context.prec = 24
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def trim(poly):
    result = list(poly)
    while result and result[-1] == 0:
        result.pop()
    return result


def derivative(poly):
    return trim([index * coefficient for index, coefficient in enumerate(poly)][1:])


def remainder(a, b):
    require(bool(b), 'division by zero polynomial')
    result = trim(a)
    while len(result) >= len(b):
        offset = len(result) - len(b)
        coefficient = result[-1] / b[-1]
        for index, value in enumerate(b):
            result[index + offset] -= coefficient * value
        result = trim(result)
    return result


def positive_normalize(poly):
    return [value / abs(poly[-1]) for value in poly] if poly else []


def variations(signs):
    return sum(a != b for a, b in zip(signs, signs[1:]))


def sturm(poly):
    """Count distinct real roots using exact signs at +/- infinity."""
    poly = trim(poly)
    require(len(poly) >= 2, 'Sturm input must be nonconstant')
    chain = [positive_normalize(poly), positive_normalize(derivative(poly))]
    while chain[-1]:
        next_poly = positive_normalize([-value for value in remainder(chain[-2], chain[-1])])
        if not next_poly:
            break
        chain.append(next_poly)
    plus = [1 if item[-1] > 0 else -1 for item in chain]
    minus = [sign * (-1) ** (len(item) - 1) for sign, item in zip(plus, chain)]
    before, after = variations(minus), variations(plus)
    return {'distinctRealRoots': before - after, 'variationAtMinusInfinity': before,
            'variationAtPlusInfinity': after, 'gcdDegreeWithDerivative': len(chain[-1]) - 1,
            'chainDegrees': [len(item) - 1 for item in chain]}


def normalized_roots(values):
    roots = sorted(Q(value) for value in values)
    require(len(roots) >= 3, 'at least three distinct real roots are required')
    require(len(set(roots)) == len(roots), 'duplicate roots are not admissible')
    return roots


def initial_polynomial(roots):
    poly = [Q(1)]
    for root in roots:
        product = [Q(0)] * (len(poly) + 1)
        for index, coefficient in enumerate(poly):
            product[index] -= root * coefficient
            product[index + 1] += coefficient
        poly = product
    return poly


def heat_family(poly, sign=-1):
    # exp(-tau*d_z^2) P0, a finite sum for a polynomial.
    family = {}
    for degree, coefficient in enumerate(poly):
        for order in range(degree // 2 + 1):
            value = coefficient * Q(factorial(degree), factorial(degree - 2 * order) * factorial(order)) * sign ** order
            if value:
                family[(degree - 2 * order, order)] = value
    return family


def check_heat_pde(family):
    residual = {}
    for (z_degree, tau_degree), coefficient in family.items():
        if tau_degree:
            key = z_degree, tau_degree - 1
            residual[key] = residual.get(key, Q(0)) + coefficient * tau_degree
        if z_degree >= 2:
            key = z_degree - 2, tau_degree
            residual[key] = residual.get(key, Q(0)) + coefficient * z_degree * (z_degree - 1)
    require(all(value == 0 for value in residual.values()), 'P_tau + P_zz is not identically zero')


def heat_at(family, tau):
    poly = [Q(0)] * (max(degree for degree, _ in family) + 1)
    for (degree, order), coefficient in family.items():
        poly[degree] += coefficient * tau ** order
    return trim(poly)


def logarithm_enclosure(x, order=32):
    require(0 < x < 1, 'logarithm-series argument must be between zero and one')
    lower = sum((x ** k / k for k in range(1, order + 1)), Q(0))
    remainder_bound = x ** (order + 1) / ((order + 1) * (1 - x))
    upper = lower + remainder_bound
    require(lower > x and upper > lower, 'invalid logarithm enclosure')
    return lower, upper, remainder_bound


def rational_power_enclosure(base, exponent, steps=80):
    require(0 < base < 1 and exponent > 0, 'invalid rational power')
    numerator, denominator = exponent.numerator, exponent.denominator
    target = base ** numerator
    lower, upper = Q(0), Q(1)
    for _ in range(steps):
        middle = (lower + upper) / 2
        value = middle ** denominator
        if value == target:
            lower = upper = middle
            break
        if value < target:
            lower = middle
        else:
            upper = middle
    require(lower ** denominator <= target <= upper ** denominator, 'rational power enclosure failed')
    return lower, upper


def interior_dyadic(lower, upper):
    require(0 <= lower < upper, 'empty rational sampling interval')
    denominator = 1
    for _ in range(8192):
        numerator = lower.numerator * denominator // lower.denominator + 1
        candidate = Q(numerator, denominator)
        if candidate < upper:
            require(lower < candidate < upper, 'rational sample is not interior')
            return candidate
        denominator *= 2
    raise AssertionError('rational sample requires more than 8192 binary digits')


def bound_data(roots):
    n = len(roots)
    diameter = roots[-1] - roots[0]
    minimum_gap = min(right - left for left, right in zip(roots, roots[1:]))
    kappa = Q(n - 2) / diameter ** 2
    x = kappa * minimum_gap ** 2 / 2
    require(minimum_gap * (n - 1) <= diameter and 0 < x < 1, 'packing/domain condition')
    log_lower, log_upper, log_remainder = logarithm_enclosure(x)
    lower, upper = log_lower / (4 * kappa), log_upper / (4 * kappa)
    baseline = minimum_gap ** 2 / 8
    require(lower > baseline, 'constant-kappa lower bound is not strictly stronger than baseline')
    # Optional dynamic-diameter bound, independently enclosed by integer powers.
    a, b = Q(4 * (n - 2)), Q(16 * n - 24)
    eta = (a + b) * minimum_gap ** 2 / (8 * diameter ** 2)
    require(0 < eta < 1, 'dynamic-bound rational-power domain')
    exponent = b / (a + b)
    root_lower, root_upper = rational_power_enclosure(1 - eta, exponent)
    dynamic_lower = diameter ** 2 / b * (1 - root_upper)
    dynamic_upper = diameter ** 2 / b * (1 - root_lower)
    return {'n': n, 'diameter': diameter, 'minimum_gap': minimum_gap, 'kappa': kappa,
            'x': x, 'log_lower': log_lower, 'log_upper': log_upper, 'log_remainder': log_remainder,
            'lower': lower, 'upper': upper, 'baseline': baseline, 'eta': eta,
            'power_exponent': exponent, 'root_lower': root_lower, 'root_upper': root_upper,
            'dynamic_lower': dynamic_lower, 'dynamic_upper': dynamic_upper}


def certify_case(name, values):
    roots = normalized_roots(values)
    poly = initial_polynomial(roots)
    family = heat_family(poly)
    check_heat_pde(family)
    initial_count = sturm(poly)
    require(initial_count['distinctRealRoots'] == len(roots)
            and initial_count['gcdDegreeWithDerivative'] == 0, 'initial Sturm count')
    bounds = bound_data(roots)
    baseline, lower, upper = (bounds[key] for key in ('baseline', 'lower', 'upper'))
    intervals = [('early_constant_bound', Q(0), baseline / 2),
                 ('middle_constant_bound', baseline / 2, baseline),
                 ('strictly_beyond_old_baseline', baseline, lower)]
    dynamic_improvement = bounds['dynamic_lower'] > upper
    if dynamic_improvement:
        intervals.append(('strictly_beyond_constant_bound', upper, bounds['dynamic_lower']))
    samples = []
    for label, left, right in intervals:
        duration = interior_dyadic(left, right)
        count = sturm(heat_at(family, -duration))
        require(count['distinctRealRoots'] == len(roots) and count['gcdDegreeWithDerivative'] == 0,
                name + ': exact Sturm count refutes the claimed safe sample ' + label)
        samples.append({'name': label, 'backwardDuration': str(duration), 'tau': str(-duration),
                        'strictSamplingInterval': [str(left), str(right)], 'sturm': count})
    serial = {key: str(value) for key, value in bounds.items() if key != 'n'}
    return {'name': name, 'degree': len(roots), 'rootsSorted': list(map(str, roots)),
            'initialCoefficientsAscending': list(map(str, poly)), 'initialSturm': initial_count,
            'heatEquationCheckedCoefficientwise': True,
            'heatFamilyTerms': [{'zPower': iz, 'tauPower': it, 'coefficient': str(value)}
                                for (iz, it), value in sorted(family.items())],
            'exactBounds': serial,
            'logEnclosure': {'seriesTerms': 32, 'formula': 'L_N=sum(x^k/k); R<=x^(N+1)/((N+1)*(1-x))'},
            'dynamicEnclosure': {'bisectionSteps': 80, 'strictImprovementProvedByEnclosures': dynamic_improvement,
                                 'formula': 'Tdyn=D^2/B*(1-(1-eta)^(B/(A+B)))'},
            'decimalDisplayOnly': {'oldBaseline': display(baseline), 'constantLower': display(lower),
                                   'constantUpper': display(upper),
                                   'dynamicLower': display(bounds['dynamic_lower']),
                                   'dynamicUpper': display(bounds['dynamic_upper'])},
            'samples': samples}


def default_cases():
    cases = []
    clustered = [Q(0), Q(1, 20), Q(1), Q(3), Q(6), Q(10), Q(15), Q(21)]
    uneven = list(map(Q, [-9, -4, -1, 2, 6, 13, 23, 38]))
    for n in range(3, 9):
        uniform = [Q(index) - Q(n - 1, 2) for index in range(n)]
        cases.extend([(f'degree_{n}_uniform', uniform), (f'degree_{n}_clustered', clustered[:n]),
                      (f'degree_{n}_uneven', uneven[:n]),
                      (f'degree_{n}_translated_scaled', [Q(3, 2) * root + Q(7, 3) for root in uniform])])
    cases.append(('quartic_reference', list(map(Q, [-3, -1, 1, 3]))))
    return cases


def controls():
    roots = list(map(Q, [-3, -1, 1, 3]))
    poly = initial_polynomial(roots)
    family = heat_family(poly)
    collision = heat_at(family, Q(-2, 3))
    require(collision == list(map(Q, [1, 0, -2, 0, 1])), 'quartic exact collision factorization')
    collision_sturm = sturm(collision)
    require(collision_sturm['distinctRealRoots'] == 2
            and collision_sturm['gcdDegreeWithDerivative'] == 2, 'quartic double-root gcd degree')
    inflated_sturm = sturm(heat_at(family, Q(-7, 10)))
    def inflated_bound():
        require(inflated_sturm['distinctRealRoots'] == 4,
                'inflated duration 7/10 extends beyond the quartic collision')
    negative = [
        ('heat sign reversed', lambda: check_heat_pde(heat_family(poly, sign=1))),
        ('inflated safe duration 7/10', inflated_bound),
        ('duplicate roots', lambda: normalized_roots([Q(0), Q(0), Q(1)])),
        ('degree two outside theorem', lambda: normalized_roots([Q(-1), Q(1)])),
    ]
    for label, test in negative:
        try:
            test()
        except AssertionError:
            continue
        raise AssertionError('negative control accepted: ' + label)
    require(normalized_roots([Q(3), Q(-1), Q(-3), Q(1)]) == roots, 'unsorted input normalization')
    original = bound_data(roots)
    scale, shift = Q(3, 2), Q(7, 3)
    transformed = bound_data([scale * root + shift for root in roots])
    for key in ('lower', 'upper', 'baseline', 'dynamic_lower', 'dynamic_upper'):
        require(transformed[key] == scale ** 2 * original[key], 'translation/scaling covariance ' + key)
    return {'rejectedNegativeControls': [label for label, _ in negative],
            'unsortedInputAcceptedBySorting': True, 'boundTranslationAndScalingCheckedExactly': True,
            'quarticExactCollision': {'tau': '-2/3', 'polynomial': '(z^2-1)^2', 'sturm': collision_sturm},
            'inflatedDurationCounterexample': {'tau': '-7/10', 'sturm': inflated_sturm}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roots', help='comma-separated exact rationals; e.g. --roots=-3,-1,1,3')
    parser.add_argument('--output', type=Path, help='optional path for the same JSON printed to stdout')
    args = parser.parse_args()
    cases = default_cases() if args.roots is None else [
        ('custom', [Q(value.strip()) for value in args.roots.split(',')])]
    result = {'status': 'passed', 'traceId': 'graph.riemann.gap.verify',
              'arithmetic': 'Fraction exact rational arithmetic; Decimal values are display-only',
              'timeConvention': 'backward duration u>0 corresponds to tau=-u',
              'cases': [certify_case(name, roots) for name, roots in cases], 'controls': controls(),
              'limitations': [
                  'The general gap bound requires the separate analytic proof; examples do not establish it.',
                  'Sturm counts certify only the listed rational sample times; the theorem supplies the interval claim.',
                  'Logarithm and rational-power enclosures are exact rational interval calculations.',
                  'An 80-step dynamic enclosure may be too broad to show improvement for extreme gap-to-diameter ratios.',
                  'No novelty, Riemann-zeta, or Riemann Hypothesis conclusion is claimed.']}
    result['caseCount'] = len(result['cases'])
    result['sampleCount'] = sum(len(case['samples']) for case in result['cases'])
    encoded = json.dumps(result, indent=2) + '\n'
    if args.output is not None:
        args.output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ArithmeticError, ValueError, OSError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        sys.exit(1)
