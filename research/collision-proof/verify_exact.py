"""Exact rational algebra certificates for a quartic backward-heat example.

Run with Python 3: python -B verify_exact.py
All arithmetic is Fraction/integer arithmetic. JSON goes to stdout; failure
exits nonzero. This checks finite identities and counterexamples, not a machine
formal proof of the human sign argument characterizing all-real roots.
"""
from fractions import Fraction as Q
from functools import lru_cache
from math import comb
import json
import sys

# defines: graph.riemann.collision.verify
# consumer: graph.riemann.collision.proof
# Polynomials are sparse maps (z exponent, tau exponent) -> Fraction.


def clean(p):
    return {power: Q(coefficient) for power, coefficient in p.items() if coefficient}


def constant(value):
    return clean({(0, 0): Q(value)})


def add(*polynomials):
    result = {}
    for polynomial in polynomials:
        for power, coefficient in polynomial.items():
            result[power] = result.get(power, Q(0)) + coefficient
    return clean(result)


def scale(p, coefficient):
    return clean({power: value * coefficient for power, value in p.items()})


def multiply(a, b):
    result = {}
    for (az, at), ac in a.items():
        for (bz, bt), bc in b.items():
            power = az + bz, at + bt
            result[power] = result.get(power, Q(0)) + ac * bc
    return clean(result)


def power(p, exponent):
    result = constant(1)
    for _ in range(exponent):
        result = multiply(result, p)
    return result


def derivative(p, variable):
    result = {}
    for exponents, coefficient in p.items():
        degree = exponents[variable]
        if degree:
            reduced = list(exponents)
            reduced[variable] -= 1
            result[tuple(reduced)] = coefficient * degree
    return clean(result)


def substitute(p, variable, value):
    result = {}
    for exponents, coefficient in p.items():
        reduced = list(exponents)
        reduced[variable] = 0
        term = coefficient * Q(value) ** exponents[variable]
        key = tuple(reduced)
        result[key] = result.get(key, Q(0)) + term
    return clean(result)


def evaluate(p, z=Q(0), tau=Q(0)):
    return sum((c * Q(z) ** iz * Q(tau) ** it for (iz, it), c in p.items()), Q(0))


def terms(p):
    return [{'zPower': iz, 'tauPower': it, 'coefficient': str(coefficient)}
            for (iz, it), coefficient in sorted(p.items(), reverse=True)]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def identity(name, left, right):
    residual = add(left, scale(right, -1))
    require(not residual, name + ': nonzero exact residual ' + repr(residual))
    return {'name': name, 'passed': True, 'residualTerms': []}


def sylvester_resultant(p, q):
    """Determinant over Q[tau], computed independently of a closed formula."""
    n, m = max(iz for iz, _ in p), max(iz for iz, _ in q)
    def coefficient(polynomial, degree):
        return clean({(0, it): c for (iz, it), c in polynomial.items() if iz == degree})
    pc = [coefficient(p, i) for i in range(n, -1, -1)]
    qc = [coefficient(q, i) for i in range(m, -1, -1)]
    rows = [[{}] * shift + pc + [{}] * (m - shift - 1) for shift in range(m)]
    rows += [[{}] * shift + qc + [{}] * (n - shift - 1) for shift in range(n)]
    @lru_cache(None)
    def determinant(columns):
        if not columns:
            return constant(1)
        row = n + m - len(columns)
        result = {}
        for position, column in enumerate(columns):
            if rows[row][column]:
                minor = determinant(columns[:position] + columns[position + 1:])
                result = add(result, scale(multiply(rows[row][column], minor), (-1) ** position))
        return result
    return determinant(tuple(range(n + m)))


def z_divmod(a, b):
    require(b and all(it == 0 for _, it in a) and all(it == 0 for _, it in b),
            'univariate division domain')
    quotient, remainder = {}, dict(a)
    divisor_degree = max(iz for iz, _ in b)
    leading = b[(divisor_degree, 0)]
    while remainder and max(iz for iz, _ in remainder) >= divisor_degree:
        degree = max(iz for iz, _ in remainder)
        term = {(degree - divisor_degree, 0): remainder[(degree, 0)] / leading}
        quotient = add(quotient, term)
        remainder = add(remainder, scale(multiply(term, b), -1))
    return quotient, remainder


def z_gcd(a, b):
    while b:
        _, remainder = z_divmod(a, b)
        a, b = b, remainder
    return scale(a, 1 / a[(max(iz for iz, _ in a), 0)])


Z = {(1, 0): Q(1)}
T = {(0, 1): Q(1)}
B = add(constant(10), scale(T, 12))
C = add(constant(9), scale(T, 20), scale(power(T, 2), 12))
P = add(power(Z, 4), scale(multiply(B, power(Z, 2)), -1), C)
THRESHOLD = Q(-2, 3)


def frozen_prediction(p, center):
    first = derivative(p, 0)
    second = derivative(first, 0)
    f, fz, fzz = (evaluate(poly, center, 0) for poly in (p, first, second))
    require(fzz != 0, 'frozen predictor denominator is zero')
    discriminant = fz * fz - 2 * f * fzz
    prediction = -discriminant / (2 * fzz * fzz)
    local_offset = -fz / fzz
    location = center + local_offset
    frozen_value = f + fz * local_offset + fzz * local_offset ** 2 / 2 - fzz * prediction
    frozen_derivative = fz + fzz * local_offset
    require(frozen_value == 0 and frozen_derivative == 0, 'frozen double-root location')
    return {'center': str(center), 'P': str(f), 'Pz': str(fz), 'Pzz': str(fzz),
            'localDiscriminant': str(discriminant), 'prediction': str(prediction),
            'frozenCollisionLocation': str(location), 'frozenValueAtPrediction': str(frozen_value),
            'frozenDerivativeAtPrediction': str(frozen_derivative),
            'actualPolynomialValueAtPrediction': str(evaluate(p, location, prediction))}, prediction


def omitted_remainder(p):
    # Three-variable coefficient check; powers are (center c, displacement u, tau).
    shifted, frozen = {}, {}
    def insert(target, exponents, coefficient):
        target[exponents] = target.get(exponents, Q(0)) + coefficient
    for (iz, it), coefficient in p.items():
        for iu in range(iz + 1):
            insert(shifted, (iz - iu, iu, it), coefficient * comb(iz, iu))
        if it == 0:
            insert(frozen, (iz, 0, 0), coefficient)
            if iz >= 1:
                insert(frozen, (iz - 1, 1, 0), coefficient * iz)
            if iz >= 2:
                second = coefficient * iz * (iz - 1)
                insert(frozen, (iz - 2, 2, 0), second / 2)
                insert(frozen, (iz - 2, 0, 1), -second)
    actual = add(shifted, scale(frozen, -1))
    expected = clean({(1, 3, 0): 4, (0, 4, 0): 1, (1, 1, 1): -24,
                      (0, 2, 1): -12, (0, 0, 2): 12})
    certificate = identity('P_tau(c+u)-Q=4*c*u^3+u^4-24*c*tau*u-12*tau*u^2+12*tau^2',
                           actual, expected)
    return certificate, [{'centerPower': ic, 'uPower': iu, 'tauPower': it, 'coefficient': str(value)}
                         for (ic, iu, it), value in sorted(actual.items(), reverse=True)]


def initial_root_motion(p):
    roots = [Q(-3), Q(-1), Q(1), Q(3)]
    expected_velocities = [Q(-11, 6), Q(-1, 2), Q(1, 2), Q(11, 6)]
    pz, pzz = derivative(p, 0), derivative(derivative(p, 0), 0)
    velocities, root_certificates = [], []
    for root, expected in zip(roots, expected_velocities):
        require(evaluate(p, root, 0) == 0, 'initial root position')
        slope = evaluate(pz, root, 0)
        require(slope != 0, 'initial root is not simple')
        velocity = evaluate(pzz, root, 0) / slope
        interaction = 2 * sum((1 / (root - other) for other in roots if other != root), Q(0))
        require(velocity == interaction == expected, 'initial root-velocity identity')
        velocities.append(velocity)
        root_certificates.append({'root': str(root), 'PzzOverPz': str(velocity),
                                  'twiceOtherRootReciprocalSum': str(interaction)})
    gaps = []
    for index, expected in enumerate([Q(4, 3), Q(1), Q(4, 3)]):
        left, right = roots[index:index + 2]
        gap = right - left
        external_sum = sum((1 / ((right - other) * (left - other))
                            for other in roots if other not in (left, right)), Q(0))
        velocity_difference = velocities[index + 1] - velocities[index]
        formula = 4 / gap - 2 * gap * external_sum
        require(external_sum > 0 and velocity_difference == formula == expected,
                'adjacent-gap derivative identity')
        gaps.append({'leftRoot': str(left), 'rightRoot': str(right), 'gap': str(gap),
                     'externalRootSumS': str(external_sum),
                     'velocityDifference': str(velocity_difference),
                     'fourOverGapMinusTwoGapS': str(formula)})
    minimum_gap = min(right - left for left, right in zip(roots, roots[1:]))
    return {'tau': '0', 'rootVelocityFormula': 'Pzz/Pz = 2*sum_other(1/(r-other))',
            'gapDerivativeFormula': "g'=4/g-2*g*S", 'roots': root_certificates, 'adjacentGaps': gaps,
            'minimumInitialGap': str(minimum_gap),
            'negativeMinimumGapSquaredOverEight': str(-minimum_gap ** 2 / 8),
            'scope': 'Exact identities at tau=0 only; the sufficient finite-gap interval requires the separate human proof.'}


def certificates(p=P, heat_sign=1, threshold=THRESHOLD):
    pz = derivative(p, 0)
    pzz = derivative(pz, 0)
    discriminant = add(power(B, 2), scale(C, -4))
    factored_discriminant = scale(multiply(add(T, constant(1)), add(T, constant(Q(2, 3)))), 96)
    completion = add(scale(power(add(T, constant(Q(5, 6))), 2), 12), constant(Q(2, 3)))
    identities = [
        identity('backward heat: P_tau + P_zz = 0', add(derivative(p, 1), scale(pzz, heat_sign)), {}),
        identity('tau=0: P=(z^2-1)(z^2-9)', substitute(p, 1, 0),
                 multiply(add(power(Z, 2), constant(-1)), add(power(Z, 2), constant(-9)))),
        identity('tau=-2/3: P=(z^2-1)^2', substitute(p, 1, threshold),
                 power(add(power(Z, 2), constant(-1)), 2)),
        identity('w-discriminant: B^2-4C=96(tau+1)(tau+2/3)', discriminant, factored_discriminant),
        identity('C=12(tau+5/6)^2+2/3', C, completion),
    ]
    remainder_certificate, remainder_terms = omitted_remainder(p)
    identities.append(remainder_certificate)
    resultant = sylvester_resultant(p, pz)
    identities.append(identity('Res_z(P,Pz)=16*C*(B^2-4C)^2', resultant,
                               scale(multiply(C, power(discriminant, 2)), 16)))
    gcd_certificates = []
    for tau, expected in [(Q(0), constant(1)), (THRESHOLD, add(power(Z, 2), constant(-1))),
                          (Q(-1), add(power(Z, 2), constant(1)))]:
        at_tau = substitute(p, 1, tau)
        gcd = z_gcd(at_tau, derivative(at_tau, 0))
        identity('specialized gcd at tau=' + str(tau), gcd, expected)
        quotient, remainder = z_divmod(at_tau, gcd)
        require(not remainder, 'gcd does not divide P')
        gcd_certificates.append({'tau': str(tau), 'monicGcdTerms': terms(gcd),
                                 'quotientTerms': terms(quotient)})
    predictions = []
    for center, expected in [(Q(0), Q(-9, 20)), (Q(2), Q(-113, 196)), (Q(-2), Q(-113, 196))]:
        entry, prediction = frozen_prediction(p, center)
        require(prediction == expected, 'unexpected frozen prediction at ' + str(center))
        require(prediction != THRESHOLD, 'claimed predictor equality unexpectedly holds')
        entry.update(actualCollisionParameter=str(THRESHOLD), equalsActual=False,
                     predictionMinusActual=str(prediction - THRESHOLD))
        if center == 0:
            require(evaluate(p, 0, prediction) == Q(243, 100) > 0,
                    'positive actual residual at the frozen center-zero collision')
        else:
            require(Q(entry['frozenCollisionLocation']) == (Q(16, 7) if center > 0 else Q(-16, 7)),
                    'frozen off-center collision location')
        predictions.append(entry)
    gap = Q(2)
    equal_gap = -gap * gap / 8
    require(equal_gap == Q(-1, 2) and equal_gap != THRESHOLD, 'equal-gap baseline')
    # These refute only bounds asserted for EVERY real center with Pzz != 0.
    upper_entry, upper = frozen_prediction(p, Q(0))
    lower_entry, lower = frozen_prediction(p, Q(4, 3))
    positive_entry, positive = frozen_prediction(p, Q(4))
    require(upper > THRESHOLD and lower < THRESHOLD and positive > 0, 'counterexample inequalities')
    return {'identities': identities, 'polynomialTerms': terms(p),
            'initialRootMotion': initial_root_motion(p),
            'omittedRemainderTerms': remainder_terms,
            'resultantTerms': terms(resultant), 'specializedGcds': gcd_certificates,
            'frozenLocalQuadraticPredictors': predictions,
            'equalSpacingGapBaseline': {'gap': str(gap), 'prediction': str(equal_gap),
                'equalsActual': False, 'predictionMinusActual': str(equal_gap - THRESHOLD)},
            'counterexamples': [
                {'candidate': 'c(center) <= -2/3 for every admissible real center',
                 'refuted': True, 'witness': upper_entry, 'difference': str(upper - THRESHOLD)},
                {'candidate': 'c(center) >= -2/3 for every admissible real center',
                 'refuted': True, 'witness': lower_entry, 'difference': str(lower - THRESHOLD)},
                {'candidate': 'the frozen prediction is always a negative parameter increment',
                 'refuted': True, 'witness': positive_entry}],
            'humanSignArgumentInputs': {'constantTermStrictLowerBound': '2/3',
                'wDiscriminantRoots': ['-1', '-2/3'], 'wRootSum': '10+12*tau',
                'sumAtMinusOne': str(evaluate(B, tau=-1)),
                'sumAtMinusTwoThirds': str(evaluate(B, tau=THRESHOLD))}}


def main():
    result = certificates()
    mutations = [
        ('heat sign reversed', lambda: certificates(heat_sign=-1)),
        ('constant coefficient corrupted', lambda: certificates(p=add(P, constant(1)))),
        ('threshold shifted by 1/100', lambda: certificates(threshold=THRESHOLD + Q(1, 100))),
        ('non-univariate division terms cancel', lambda: z_divmod(add(T, Z), add(scale(T, -1), constant(1)))),
    ]
    for label, test in mutations:
        try:
            test()
        except AssertionError:
            continue
        raise AssertionError('negative control was accepted: ' + label)
    result.update(status='passed', arithmetic='exact Python Fraction; no floating-point arithmetic',
                  traceId='graph.riemann.collision.verify',
                  rejectedNegativeControls=[label for label, _ in mutations],
                  limitations=[
                      'Finite algebraic identities and counterexamples are checked exactly.',
                      'The iff characterization of all-real roots still uses a separate human sign-case argument.',
                      'This is not a proof-assistant formalization or a result about Riemann zeta.',
                      'Counterexamples to bounds concern unrestricted centers; no stronger hypothesis is presumed.'])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ArithmeticError, ValueError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        sys.exit(1)
