import cmath
import json
import math

def zeta_em(s, n):
    value = sum(k ** (-s) for k in range(1, n))
    value += n ** (1-s)/(s-1) + 0.5*n**(-s)
    bernoulli = [(1,6),(-1,30),(1,42),(-1,30),(5,66),(-691,2730),(7,6),(-3617,510)]
    for k, (numerator, denominator) in enumerate(bernoulli,1):
        rising = 1+0j
        for j in range(2*k-1):
            rising *= s+j
        value += numerator/denominator/math.factorial(2*k)*rising*n**(-s-2*k+1)
    return value

def primes(limit):
    sieve=[True]*(limit+1)
    sieve[0]=sieve[1]=False
    for p in range(2,math.isqrt(limit)+1):
        if sieve[p]:
            for multiple in range(p*p,limit+1,p):
                sieve[multiple]=False
    return [p for p in range(2,limit+1) if sieve[p]]

rows=[]
for s in [2+0j,2+14.134725141734694j,2+23.298320492762855j]:
    reference = zeta_em(s,64)
    reference_check = abs(reference-zeta_em(s,32))
    assert reference_check < 1e-12
    if not s.imag:
        assert abs(reference-math.pi**2/6)<1e-12
    for limit in [32,128,512,2048]:
        factors=[1/(1-p**(-s)) for p in primes(limit)]
        product=math.prod(factors)
        reversed_product=math.prod(reversed(factors))
        logarithm=-sum(cmath.log(1-p**(-s)) for p in primes(limit))
        bound=limit**(1-s.real)/((s.real-1)*(1-(limit+1)**(-s.real)))
        product_bound=abs(product)*math.expm1(bound)
        error=abs(product-reference)
        assert abs(product-reversed_product)<1e-12
        assert abs(product-cmath.exp(logarithm))<1e-12
        assert error <= product_bound+1e-12
        rows.append(dict(real=s.real,imag=s.imag,cutoff=limit,
            observed_error=error,truncation_bound=product_bound,
            reverse_difference=abs(product-reversed_product),reference_crosscheck=reference_check))
print(json.dumps(dict(status="passed",scope="double-precision spot checks; truncation bound excludes rounding",cases=rows),indent=2))
