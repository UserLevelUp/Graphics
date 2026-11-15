# Prime color laboratory results

defines: graph.primes.phase.results
consumer: graph.primes.phase.render
consumer: graph.primes.phase.unwrap
consumer: graph.primes.phase.acceptance
consumer: graph.primes.phase.reviews

Implemented the finite prime-product experiment in Graphics with an interactive Prime color lab button and a standalone --prime-lab entry point. The UI controls real part, prime cutoff, axis rotation, selected prime, factor order, and shared-height overlays. PNG export and an Unwrap factors dialog are available. The source lives in PrimePhaseExperiment.cs, PrimePhaseForm.cs, and PrimeUnwrap.cs. Existing zeta views remain available.

The left mesh colors the four quadrants of each local step d_p=-Log(1-p^(-s)). Its real component changes log magnitude and its imaginary component changes angle. Brightness is scaled separately per column to make small contributions visible; it does not compare raw contribution strengths across primes. The right mesh colors the cumulative finite product. Violet marks quadrant changes between consecutive nonempty partial products, excluding the initial unit on an axis. Exact axes use half-open intervals; gray applies an explicitly empirical 1e-12*max(1,|value|) display tolerance. This is not a rigorous roundoff enclosure.

The Euler product and the elementary tail bounds used here apply for real part greater than1. [NIST DLMF25.2.11](https://dlmf.nist.gov/25.2.E11). These finite-product colors are not presented as certified colors of the infinite zeta function. At sigma1.2 and cutoff512, the conservative analytic logarithm tail bound is about1.43668, excluding arithmetic error.

On the default grid there are97 prime factors and481 height rows from0 through40. Violet marks285 of46,657 cells. Rotating the axes by22.5 degrees changes425 marker cells. Reversing factor order changes the history; the maximum difference in the final product across the height grid is6.217e-15. Grid refinement at241/481/961 rows produces141/285/563 markers. Comparing inserted midpoint rows with the preceding coarse row changes155 marker decisions; this is not a count of previously hidden crossings. Independent NumPy calculations reproduced these measurements.

The overlay compares shared height coordinates. Lime lines mark prime integer heights2 through40, white dashed lines mark six pre-established zeta-zero heights, and amber marks the earlier derivative-critical-point height23.298320. The horizontal axis remains prime index. These reference lines do not superimpose different functions at identical complex inputs.

At default sigma1.2, ascending order, and zero axis rotation, prime integer rows have0 violet transitions out of1,152 eligible comparisons. Composite integer rows have15 out of2,592. At22.5 degrees the counts are2 and9. In descending order at zero rotation they are152 and368. Across eight independent settings using sigma1.2 or2, two rotations, and two orders, prime-row density did not exceed composite-row density. This is a descriptive test of an arbitrarily chosen height correspondence, not a primality criterion or statistical discovery.

The unwrapped view follows the individual factors n^(-sigma-it), for which continuous angle is exactly -t*log(n). A513-sample unwrap matches that expression within3.553e-15 radians across the selected controls; reconstructed label relative error is at most4.461e-16. A one-step control for n=13 misses three complete turns. Composite controls4 and12 behave the same way. These are supplied factor labels being reconstructed, not newly found primes. Unwrapping the full zeta function, especially through a zero, is a different problem.

Validation includes all12 contract points, direct/reverse/grouped/log evaluation agreement, decreasing log-tail bounds, domain rejection, exact and near-axis behavior, phase-wrap cases,970 predicted individual phase crossings, grid refinement, and overlay controls. Independent70-digit Decimal products and Euler-Maclaurin references agree with the exported doubles within1.57e-14. No directed-rounding certification is claimed. The Release build passes with the existing net5.0 support warning and existing unused-field warnings. All three previous PNG exports regenerate byte-for-byte. The main UI, rotation-and-render action, and unwrapped dialog were verified in the native app. Observed preview times were roughly9–48ms on this machine; no GPU acceleration was introduced. Parallel row evaluation, cached prime logarithms, and bulk bitmap writes keep rendering responsive.

Evidence and reproducible independent scripts are under research/prime-phase/evidence/render. JSON exports distinguish actual renderParameters from the fixed verificationParameters. Run an export with DOTNET_ROLL_FORWARD=Major on this host, for example `dotnet Graphics/bin/Release/net5.0-windows/Graphics.dll --prime-phase output.png` or `--prime-unwrap unwrapped.png`.

This completes the bounded visualization experiment. The parent graph.riemann proof remains open. Rescaling, unwrapping, or visually filtering does not establish zero exclusion off the critical line. A proof-relevant filter would need a rigorous guarantee for every excluded point and a global argument covering all remaining heights. [Clay's RH description](https://www.claymath.org/millennium/riemann-hypothesis/)
