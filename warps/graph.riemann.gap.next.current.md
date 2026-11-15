# Infinite-system transfer remains open

defines: graph.riemann.gap.next
consumer: graph.riemann.gap.proof
consumer: graph.riemann

The new finite-polynomial certificates improve on the nearest-gap interval. They do not prove RH or produce a prime-identification algorithm. A root list is an explicit input to this control; an RH argument must not assume that all Riemann zeros are already real in the centered xi coordinate.

There is a concrete limit to passing these particular bounds directly to a growing root set. Write x=(n-2)m^2/(2D^2) and eta=(5n-8)m^2/(2D^2). Packing gives x <= (n-2)/(2(n-1)^2) and eta <= (5n-8)/(2(n-1)^2). Both tend to zero as n tends to infinity.

The constant bound divided by m^2/8 is -log(1-x)/x, which tends to one. For the dynamic bound, put beta=(16n-24)/(20n-32). Its ratio to m^2/8 is [1-(1-eta)^beta]/(beta*eta), which also tends to one, with beta tending to 4/5. This follows, for example, by writing the numerator as the integral of beta*(1-v)^(beta-1) from zero to eta. Thus if the minimum gaps m tend to zero, both guaranteed durations tend to zero. This is an analytic limit of the formulas, not a numerical extrapolation.

Conditionally assuming real simple zeros in the xi coordinate, height truncations have O(T) diameter and order T*log(T) zeros. Packing then forces m=O(1/log(T)). The established zero-count asymptotic therefore illustrates the vanishing-bound obstruction; the real/simplicity premise is not supplied by the zero-count theorem. Primary source for the count: Hasanalizade, Shen and Wong, https://arxiv.org/abs/2107.06506 .

Next mathematical obligation: replace the global diameter/minimum-gap estimate with justified local interaction and tail control for the actual entire-function flow. Any proposed transfer must state its starting real-root assumption, convergence of the relevant sums, behavior of omitted zeros, and how its estimates cover every height without assuming RH. A local point or color state cannot discharge those obligations on its own.

The completed bubble is a stronger finite tool with an explicitly identified transfer gap. No positive uniform backward interval for the full Riemann flow has been established.
