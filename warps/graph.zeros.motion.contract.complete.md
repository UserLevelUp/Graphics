# Zero motion and local color coordinates: completed calibration contract

defines: graph.zeros.motion
consumer: graph.zeros.motion.model
consumer: graph.zeros.motion.color
consumer: graph.zeros.motion.ui
consumer: graph.zeros.motion.verify
consumer: graph.zeros.motion.path
consumer: graph.zeros.motion.path.verify

The authorized experiment replaces static prime coloring with controlled motion of zeros. Baseline is commit b5dff2b on graph/riemann-local-origins, with its preserved graph-prime-color-lab-2026-11-14 tag. The parent graph.riemann remains open.

Use the exact calibration family F(z,lambda)=z^2-2lambda, which satisfies the backward heat equation partial_lambda F=-partial_z^2 F. Decrease lambda through zero: two real zeros collide into a double zero, then split onto the imaginary axis. This is a polynomial example, not a numerical implementation of the Riemann xi deformation.

Each zero supplies a local complex coordinate z-r. Separate panels display the phase quadrant of each coordinate, and a third displays the phase of their product. The product phase is the sum of the two factor phases modulo a full turn. Color classification is a display convention; numerical phases, zero locations and multiplicity are retained independently. No prime labels, winner-takes-all overwriting, or RH classifications enter the model. Palette rotation is explicit. Branch A/B identities through the double zero are conventional.

Acceptance contract: render positive, collision, negative and near-collision snapshots; verify root residuals and factorization; independently check exported values and winding multiplicities; inspect native controls, animation, palette rotation and PNG/data export; preserve evidence and a local Git snapshot. Compare the frozen quadratic collision prediction with the exact parameter; in this family it reproduces the known gap predictor and supplies no novel inequality. Observed results are in graph.zeros.motion.results.complete.md.

Future research, outside this bounded calibration: higher-degree flow controls and independently validated collision forecasts compared with gap and derivative baselines, then the actual xi flow if the measurement adds information.

User steering adds a point-to-point probe within the same exact model. The local phase forecast is Im(F'(a)/F(a)*(b-a)). The accumulated phase is Im integral F'(z)/F(z) dz along a straight segment, provided the path avoids zeros. Independent factor-angle continuation checks integration; solving the real and imaginary rotated quadratic restrictions enumerates crossings and tangencies. Color labels themselves are discontinuous and are not differentiated. Singular and near-root paths must be explicit; empirical Simpson convergence is not a rigorous enclosure. UI selects two points, shows the common segment across panels, and saves the associated path data.

The de Bruijn-Newman context and sign convention follow Rodgers and Tao, https://arxiv.org/abs/1801.05914. This experiment does not establish a global zero exclusion or an RH result.
