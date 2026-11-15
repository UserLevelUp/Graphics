"""Independent Decimal Euler products and Euler–Maclaurin zeta references."""
from decimal import Decimal as D, getcontext
from fractions import Fraction
import cmath
import json
import math
from pathlib import Path

getcontext().prec = 70
PI = D("3.141592653589793238462643383279502884197169399375105820974944592307816406286")
TAU = 2 * PI
ZERO = (D(0), D(0))
ONE = (D(1), D(0))


def add(a, b):
    return a[0] + b[0], a[1] + b[1]


def sub(a, b):
    return a[0] - b[0], a[1] - b[1]


def mul(a, b):
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def scale(a, b):
    return a[0] * b, a[1] * b


def div(a, b):
    denominator = b[0] ** 2 + b[1] ** 2
    return ((a[0] * b[0] + a[1] * b[1]) / denominator,
            (a[1] * b[0] - a[0] * b[1]) / denominator)


def abs_complex(a):
    return (a[0] ** 2 + a[1] ** 2).sqrt()


def sin_cos(angle):
    if angle == 0:
        return D(0), D(1)
    angle = (angle + PI) % TAU
    if angle < 0:
        angle += TAU
    angle -= PI
    cosine = cosine_term = D(1)
    sine = sine_term = angle
    square = angle * angle
    for n in range(1, 140):
        sine_term *= -square / D((2 * n) * (2 * n + 1))
        cosine_term *= -square / D((2 * n - 1) * (2 * n))
        cosine += cosine_term
        sine += sine_term
        if max(abs(sine_term), abs(cosine_term)) < D("1e-75"):
            break
    else:
        raise AssertionError("Decimal trig failed to converge")
    return sine, cosine


def power_real(base, exponent):
    logarithm = D(base).ln()
    magnitude = (exponent[0] * logarithm).exp()
    sine, cosine = sin_cos(exponent[1] * logarithm)
    return magnitude * cosine, magnitude * sine


def bernoulli_numbers(count):
    work = []
    result = []
    for m in range(count + 1):
        work.append(Fraction(1, m + 1))
        for j in range(m, 0, -1):
            work[j - 1] = j * (work[j - 1] - work[j])
        result.append(work[0])
    return result


BERNOULLI = bernoulli_numbers(48)


def zeta_em(s, cutoff, corrections=24):
    negative_s = scale(s, D(-1))
    result = ZERO
    for n in range(1, cutoff):
        result = add(result, power_real(n, negative_s))
    result = add(result, div(power_real(cutoff, sub(ONE, s)), sub(s, ONE)))
    result = add(result, scale(power_real(cutoff, negative_s), D("0.5")))
    rising = ONE
    next_factor = 0
    for k in range(1, corrections + 1):
        while next_factor < 2 * k - 1:
            rising = mul(rising, add(s, (D(next_factor), D(0))))
            next_factor += 1
        coefficient = BERNOULLI[2 * k] / math.factorial(2 * k)
        decimal_coefficient = D(coefficient.numerator) / D(coefficient.denominator)
        power = power_real(cutoff, sub(negative_s, (D(2 * k - 1), D(0))))
        result = add(result, scale(mul(rising, power), decimal_coefficient))
    return result


def primes_up_to(limit):
    sieve = [True] * (limit + 1)
    sieve[0:2] = [False, False]
    for n in range(2, math.isqrt(limit) + 1):
        if sieve[n]:
            for composite in range(n * n, limit + 1, n):
                sieve[composite] = False
    return [n for n, is_prime in enumerate(sieve) if is_prime]


def complex_record(value):
    return {"real": format(value[0], ".42g"), "imaginary": format(value[1], ".42g")}


points = ["0", "14.134725141734694", "23.298320492762855"]
cutoffs = [32, 128, 512, 2048]
primes = primes_up_to(max(cutoffs))
records = []
max_reference_difference = D(0)
for text_t in points:
    s = D(2), D(text_t)
    reference96 = zeta_em(s, 96)
    reference192 = zeta_em(s, 192)
    reference_difference = abs_complex(sub(reference96, reference192))
    max_reference_difference = max(max_reference_difference, reference_difference)
    assert reference_difference < D("1e-43"), reference_difference
    if s[1] == 0:
        assert abs(reference192[0] - PI ** 2 / 6) < D("1e-60")
    for cutoff in cutoffs:
        product = ONE
        for prime in primes:
            if prime > cutoff:
                break
            product = div(product, sub(ONE, power_real(prime, scale(s, D(-1)))))
        bound = D(cutoff) ** (1 - s[0]) / ((s[0] - 1) * (1 - D(cutoff + 1) ** -s[0]))
        product_bound = abs_complex(product) * (bound.exp() - 1)
        error = abs_complex(sub(reference192, product))
        assert error <= product_bound
        phase = math.atan2(float(product[1]), float(product[0]))
        records.append({
            "sigma": "2",
            "t": text_t,
            "prime_cutoff": cutoff,
            "prime_count": sum(p <= cutoff for p in primes),
            "partial_product": complex_record(product),
            "zeta_reference": complex_record(reference192),
            "absolute_error": format(error, ".30g"),
            "log_tail_bound": format(bound, ".30g"),
            "absolute_product_tail_bound": format(product_bound, ".30g"),
            "phase_radians_double": phase,
            "em_96_192_difference": format(reference_difference, ".10g")
        })

report = {
    "method": "70-digit Decimal finite Euler products; independent Euler–Maclaurin zeta with 24 Bernoulli corrections and cutoffs 96 and 192",
    "scope": "sigma=2 at the three exact decimal contract ordinates",
    "accuracy_note": "Reference agreement is numerical cross-checking. No directed-rounding or rigorous Euler–Maclaurin remainder certificate was used.",
    "max_reference_difference": format(max_reference_difference, ".12g"),
    "records": records
}
path = Path(__file__).with_name("numeric-references.json")
path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(path)
print("Maximum EM reference difference:", max_reference_difference)
for record in records:
    print(record["t"], record["prime_cutoff"], record["partial_product"], "error", record["absolute_error"])
