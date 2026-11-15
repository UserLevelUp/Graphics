# Exact quartic collision control: resolved bounded result

defines: graph.riemann.collision.results
consumer: graph.riemann.collision
consumer: graph.riemann.collision.proof
consumer: graph.riemann.collision.verify
consumer: graph.riemann.collision.render

The four-root polynomial in the contract has all its zeros real if and only if tau >= -2/3. At the boundary it is (z^2-1)^2. Between -1 and -2/3 it has an off-axis quartet; at and below -1 all its zeros are nonzero and purely imaginary. The proof covers the entire real parameter line, rather than inferring the result from sampled root positions.

The frozen local quadratic at centers 0 and +/-2 forecasts -9/20 and -113/196 respectively. The nearest-gap estimate is -1/2. All differ from the exact first collision -2/3. The frozen forecast at center 0 predicts a collision there, but P_tau(0)=12(tau+5/6)^2+2/3 is strictly positive for every real tau.

The arbitrary-center frozen formula has no universal one-sided ordering relative to the first collision: center 0 gives a parameter above -2/3, center 4/3 gives -28277/324 below it, and center 4 gives a positive increment 643/7396. This refutes unrestricted versions of the predictor. It does not disprove every possible midpoint-restricted or otherwise constrained inequality.

One useful bound survives. For a finite polynomial flow starting with simple real roots, adjacent gaps obey (g^2)' <= 8 while the roots remain real and simple. Integrating backward proves a safe interval -g_min(0)^2/8 < t <= 0. For this quartic that is (-1/2,0]. The gap estimate is therefore a valid conservative bound under these assumptions, even though it is not the exact threshold. This elementary root-dynamics consequence is not claimed as novel.

Validation: an independently implemented standard-library Python Fraction checker verifies seven polynomial identities, a Sylvester-determinant resultant, specialized Euclidean gcds, exact frozen predictions and residuals, and initial root/gap velocities. It rejects four deliberate corruptions: reversed heat sign, altered coefficient, shifted threshold, and canceled non-univariate division inputs. The all-real equivalence and safe-interval theorem also require the human sign/continuity arguments in the proof; the checker is not a formal proof assistant.

Evidence:

- research/collision-proof/exact-quartic-proof.md: full proof and scope of the counterexamples.
- research/collision-proof/verify_exact.py: reproducible exact algebra checker.
- research/collision-proof/evidence/exact-certificates.json: canonical successful output.
- research/collision-proof/render_control.py and evidence/quartic-control.png: illustrative root-component plot, visually inspected. Float residuals concern the plot only.
- research/collision-proof/evidence/manifest.json: content hashes tying this result to its source and evidence.

No application source changed, so the completed application build/UI checks from 170993c were not repeated. This slice adds mathematical research artifacts, an exact checker and a standalone plot. A local Git commit and tag provide the restore point; Recur checkpoint metadata records provenance but is not itself a code backup.

The child graph.riemann.collision can close on this bounded obligation. The parent graph.riemann remains open: there is no proved transfer to the Riemann deformation, no all-heights control, and no RH proof or novelty claim. The concrete unfinished direction is recorded in graph.riemann.collision.next.current.md.
