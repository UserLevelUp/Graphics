"""Independent finite-product overlay statistics; no repository dependencies."""
import json
import math
from pathlib import Path
import random

import numpy as np


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def quadrant(z, basis, epsilon):
    rotated = z * np.exp(-1j * basis)
    phase = np.mod(np.angle(z) - basis, 2 * np.pi)
    q = np.minimum(3, (phase / (np.pi / 2)).astype(np.int64))
    uncertain = ((np.abs(z) <= epsilon) | (np.abs(rotated.real) <= epsilon)
                 | (np.abs(rotated.imag) <= epsilon))
    return np.where(uncertain, -1, q)


heights = np.arange(2, 41, dtype=np.int64)
primes = np.array([p for p in range(2, 513) if is_prime(p)], dtype=np.int64)
prime_labels = np.array([is_prime(int(t)) for t in heights], dtype=bool)
prime_rows = int(prime_labels.sum())
composite_rows = len(heights) - prime_rows
eligible_columns = len(primes) - 1
assert prime_rows == 12 and composite_rows == 27 and eligible_columns == 96

seed = 20261114
samples = 10000
rng = random.Random(seed)
permutations = np.array([rng.sample(range(len(heights)), prime_rows)
                         for _ in range(samples)], dtype=np.int64)
scenarios = []
for sigma in [1.2, 2.0]:
    for basis_degrees in [0.0, 22.5]:
        for reverse in [False, True]:
            ordered = primes[::-1] if reverse else primes
            s = sigma + 1j * heights[:, None]
            steps = -np.log(1 - np.exp(-s * np.log(ordered)[None, :]))
            cumulative = np.cumsum(steps, axis=1)
            after = np.exp(cumulative)
            before = np.concatenate([np.ones((len(heights), 1), dtype=complex),
                                     after[:, :-1]], axis=1)
            epsilon = 1e-12 * np.maximum(1, np.abs(after))
            basis = math.radians(basis_degrees)
            q_before = quadrant(before, basis, epsilon)
            q_after = quadrant(after, basis, epsilon)
            markers = (q_before != q_after) & (q_before >= 0) & (q_after >= 0)
            markers[:, 0] = False
            counts = markers.sum(axis=1)
            prime_count = int(counts[prime_labels].sum())
            composite_count = int(counts[~prime_labels].sum())
            total = prime_count + composite_count
            # Integer numerator of prime-row mean count minus composite-row
            # mean count. The common positive denominator cancels for ranking.
            observed_numerator = len(heights) * prime_count - prime_rows * total
            sampled_prime_counts = counts[permutations].sum(axis=1)
            sampled_numerators = len(heights) * sampled_prime_counts - prime_rows * total
            two_sided_exceedances = int(np.count_nonzero(
                np.abs(sampled_numerators) >= abs(observed_numerator)))
            upper_exceedances = int(np.count_nonzero(
                sampled_numerators >= observed_numerator))
            prime_density = prime_count / (prime_rows * eligible_columns)
            composite_density = composite_count / (composite_rows * eligible_columns)
            scenarios.append({
                'sigma': sigma,
                'palette_basis_degrees': basis_degrees,
                'prime_order': 'descending' if reverse else 'ascending',
                'prime_height_marker_count': prime_count,
                'composite_height_marker_count': composite_count,
                'prime_height_marker_density': prime_density,
                'composite_height_marker_density': composite_density,
                'prime_minus_composite_density': prime_density - composite_density,
                'density_ratio': prime_density / composite_density if composite_density else None,
                'uncertain_eligible_comparisons': int(np.count_nonzero(
                    (q_before[:, 1:] < 0) | (q_after[:, 1:] < 0))),
                'permutation': {
                    'two_sided_exceedances': two_sided_exceedances,
                    'two_sided_descriptive_p': (two_sided_exceedances + 1) / (samples + 1),
                    'positive_enrichment_descriptive_p': (upper_exceedances + 1) / (samples + 1),
                },
                'row_counts': [{'t': int(t), 'prime_height': bool(label), 'markers': int(count)}
                               for t, label, count in zip(heights, prime_labels, counts)],
            })

result = {
    'traceId': 'graph.primes.phase.overlay.independent',
    'method': 'NumPy complex exponentials/logs; independent trial-division primality; same quadrant tolerance as C#',
    'cutoff': 512,
    'prime_factor_count': len(primes),
    'eligible_noninitial_transitions_per_row': eligible_columns,
    'heights': list(map(int, heights)),
    'prime_heights': list(map(int, heights[prime_labels])),
    'composite_heights': list(map(int, heights[~prime_labels])),
    'permutation_samples': samples,
    'permutation_seed': seed,
    'permutation_scheme': 'Uniform random subsets of 12 of 39 integer-height rows; one shared deterministic sample set across all scenarios.',
    'uncertainty': 'Empirical 1e-12*max(1,abs(after)); not a directed-rounding certification.',
    'scenarios': scenarios,
    'limitations': [
        'Integer prime height is an external label on the imaginary coordinate t, not prime factor membership on x.',
        'Height units and origin select which horizontal lines receive integer-prime labels.',
        'Permutation results describe this selected finite frame. Row-label exchangeability is not established; these are not calibrated inferential p-values.',
        'Eight scenarios share rows and labels; no multiple-comparison correction or pre-registered test is claimed.',
        'Palette rotation and prime order alter intermediate quadrant changes even though the endpoint product is order invariant.',
        'Finite Euler products at sigma>1 and finite resolution do not test or prove the Riemann Hypothesis.',
    ],
}
output = Path(__file__).with_name('overlay-analysis.json')
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
for row in scenarios:
    print(f"sigma={row['sigma']}, basis={row['palette_basis_degrees']}, {row['prime_order']}: "
          f"prime={row['prime_height_marker_count']}/{prime_rows*eligible_columns} "
          f"({row['prime_height_marker_density']:.4%}), "
          f"composite={row['composite_height_marker_count']}/{composite_rows*eligible_columns} "
          f"({row['composite_height_marker_density']:.4%}), "
          f"two-sided descriptive p={row['permutation']['two_sided_descriptive_p']:.4f}")
print(output)
