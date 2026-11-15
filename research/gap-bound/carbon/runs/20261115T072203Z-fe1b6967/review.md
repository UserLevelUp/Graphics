publish: graph.riemann.gap.carbon.response

STATUS: COMPLETE
ACK: 0a819139fbe249599fe0f5a23cc80b7a
CLOCK: 2026-11-14T23:25:24.2207554-08:00

VERDICT
ACCEPT (supplied mathematical derivation only; software tests remain separate and unexecuted).

REASONING
- **Retraction & Correction**: I explicitly retract my Turn 1 claim `2 sum (r_n-r_j)(r_j-r_1) >= (n-3/2)D^2`; AM-GM gives `x(D-x) <= D^2/4`, reversing that inequality. What I corrected is applying AM-GM to the reciprocal interior terms in `D'`.
- **Dynamic Bound**: From `r_i' = 2 sum_{j!=i}(r_i-r_j)^{-1}`, `D' = 4/D + 2 sum_{1<j<n}[(r_n-r_j)^{-1}+(r_j-r_1)^{-1}]`. With `x = r_j-r_1 in (0,D)`, each of the `n-2` interior terms equals `2D/[x(D-x)] >= 8/D`, yielding `D' >= (8n-12)/D` and `(D^2)' = 2DD' >= 8+16(n-2) = 16n-24 = B > 0`. Integrating over `[t,0]` (`t<=0`) gives `D(t)^2 <= d+Bt` (`d=D_0^2`). With `y=g^2` and `A=4(n-2)`, `4S >= A/(d+Bt)` while `d+Bt>0`, so `y' + A/(d+Bt)y <= 8`. Multiplying by `(d+Bt)^{A/B} > 0`, integrating over `[t,0]`, and using `y(0)>=m^2` gives `y(t) >= (1+Bt/d)^{-A/B}[m^2 - 8d/(A+B)(1-(1+Bt/d)^{1+A/B})]` uniformly across adjacent gaps. Setting `eta = (A+B)m^2/(8d) = (5n-8)m^2/(2d)`, packing `d >= (n-1)^2 m^2` gives `2(n-1)^2-(5n-8) = (2n-5)(n-2) >= 1` for `n>=3`, so `0 < eta <= 7/8 < 1`. Solving for the first bracket zero gives `T_dynamic = (d/B)[1-(1-eta)^{B/(A+B)}]`, strictly below `d/B` since `(1-eta)^{B/(A+B)} > 0`; thus `d+Bt > 0` holds throughout `[-T_dynamic,0]`.
- **Main Theorem, Bootstrap & RH Boundary**: Static integration (`g(t)^2 >= 2/kappa + (m^2-2/kappa)e^{-4kappa t}`, `0<x<=1/8<1`, `T>m^2/8`), quartic control, and separate `n=2` (`m^2/8`) / `m=0` handling hold. On a maximal simple-real-root interval `(t_*,0]`, assuming `t_* > -T` (or `-T_dynamic`): continuous polynomial coefficients bound `|r_i(t)|`; uniform gap positivity `g(t) >= delta > 0` bounds velocities `|r_i'(t)| <= 2(n-1)/delta`; Lipschitz continuity gives `n` real limits at `t_*` separated by `>= delta`; `deg P = n` forces simple roots (`P_z != 0`); real IFT extends all `n` real roots past `t_*`, contradicting maximality. Strictly finite-degree ODE result; implies nothing for `n -> infinity` or RH/`Xi`.

TESTS
Unexecuted here; implementation acceptance requires exact `Fraction` polynomial heat flow, rational-time Sturm root counts inside `(-T,0]` beyond `-m^2/8`, proved Taylor-log enclosures, degree 3-8 invariance/cluster suites, and invalid-input rejections (`n<2`, repeated/non-real roots).
