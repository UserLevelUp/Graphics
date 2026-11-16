"""Apply the finite-polynomial bound to exact rational roots and elapsed time.

defines: graph.riemann.collision_guide.application
consumer: graph.riemann.gap.verify
This wrapper keeps an interval guarantee separate from an exact pointwise root
count. Leaving the guaranteed interval is not evidence that roots collided.
"""
import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent


def load_checker(path):
    spec=importlib.util.spec_from_file_location('finite_gap_checker',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate(root_strings, duration_string, checker):
    roots=checker.normalized_roots([Fraction(s) for s in root_strings])
    duration=Fraction(duration_string)
    if duration<0:
        raise ValueError('elapsed duration u must be nonnegative; the flow parameter is t=-u')
    bounds=checker.bound_data(roots)
    certified=duration<bounds['dynamic_lower']
    family=checker.heat_family(checker.initial_polynomial(roots))
    checker.check_heat_pde(family)
    polynomial=checker.heat_at(family,-duration)
    count=checker.sturm(polynomial)
    point_simple=count['distinctRealRoots']==len(roots) and count['gcdDegreeWithDerivative']==0
    return dict(traceId='graph.riemann.collision_guide.application',
        inputs=dict(roots=list(map(str,roots)),degree=len(roots),elapsedDuration=str(duration),flowParameter=str(-duration)),
        parameters=dict(minimumGap=str(bounds['minimum_gap']),diameter=str(bounds['diameter']),kappa=str(bounds['kappa'])),
        guaranteedInterval=dict(status='certified' if certified else 'outside_available_guarantee',
            condition='0 <= u < exact rational lower enclosure of T_dynamic',
            lowerEnclosure=str(bounds['dynamic_lower']),upperEnclosure=str(bounds['dynamic_upper']),
            decimalLowerForDisplay=checker.display(bounds['dynamic_lower']),
            interpretation='The analytic theorem guarantees real simple roots throughout 0 <= v <= u.' if certified
            else 'The interval bound makes no collision claim at this time. This status is not a failure of real-rootedness.'),
        exactPointCheck=dict(status='all_roots_real_and_simple' if point_simple else 'not_all_roots_real_and_simple',
            counts=count,coefficientsAscending=list(map(str,polynomial)),
            interpretation='Exact Sturm/gcd check of this single rational-time polynomial; not a time-integrator error bound.'),
        assumptions=['Fixed finite polynomial degree at least three.', 'Distinct real initial roots supplied as exact rationals.',
            'Specific heat evolution P_t = -P_zz and elapsed duration u=-t.', 'No interval certification of noisy or approximate root inputs is implemented.'],
        limits=['A conservative interval bound is not an exact collision predictor.',
            'Floating-point decimals are for display; decisions compare exact fractions.',
            'No novelty, improvement over the research literature, or RH conclusion is claimed.'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--roots',required=True,help='Exact rational list, e.g. --roots=-3,-1,1,3')
    p.add_argument('--duration',required=True,help='Nonnegative elapsed time, e.g. 17/32')
    default=BASE.parent/'gap-bound/verify_bound.py'
    if not default.exists(): default=BASE/'verify_bound.py'
    p.add_argument('--checker',type=Path,default=default)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    result=evaluate([s.strip() for s in args.roots.split(',')],args.duration,load_checker(args.checker))
    text=json.dumps(result,indent=2)+'\n'
    if args.output: args.output.write_text(text,encoding='utf-8')
    print(text,end='')


if __name__=='__main__':
    try:main()
    except (ValueError,ArithmeticError,AssertionError,OSError) as e:
        raise SystemExit(str(e))
