# Zero motion and point-to-point phase results

defines: graph.zeros.motion.results
consumer: graph.zeros.motion
consumer: graph.zeros.motion.model
consumer: graph.zeros.motion.color
consumer: graph.zeros.motion.ui
consumer: graph.zeros.motion.verify
consumer: graph.zeros.motion.path
consumer: graph.zeros.motion.path.verify

The Zero motion lab is available from the main Graphics window, from the Prime color lab, and through --zero-lab. Three panels display the phase quadrant of z-A, z-B, and F(z,lambda)=z^2-2lambda. Cyan and amber markers identify the two roots of F, with the other root labeled as a reference on each local-factor panel. A white combined marker identifies the collision. Each simple factor retains winding one; their product has winding two at the double zero. Branch identity through collision is a stated convention.

The parameter slider and numeric field move the roots from the real axis through their collision onto the imaginary axis. Playback decreases lambda, pauses at zero, and stops at -1. Presets select before, collision and after. Hovering shows full local coordinates and raw phases. Palette rotation recolors the same numerical data. The three raw phases obey argument addition modulo 2pi; adding already rotated sector labels is not the computation.

The two-point probe accepts a start and end in any panel and displays their common straight segment in all three panels. It compares Im(F'(start)/F(start)*(end-start)) with Im integral F'/F dz. The evaluator solves the real and imaginary scalar quadratics along the path to distinguish crossings, tangencies, endpoints, unresolved events and whole-boundary coincidence. A real-component boundary means Re(exp(-i*palette)*F)=0, geometrically the rotated imaginary axis. Full angles are retained independently of quadrant colors.

For lambda=0.5 and the path (-1.6+0.7i) to (1.6+0.7i), the local derivative forecast is -2.944259634888437 radians. The continued phase is -4.032855734483295 radians, whereas the principal endpoint change is +2.250329572696291 radians. The difference is one negative full turn. There are three interior color-boundary crossings, no tangencies and no zeros on this segment. Simpson refinement uses 2048 intervals; comparison with independent sampled phase gives approximately 1.62e-13 error. This is a useful demonstration of local prediction error and angle wrapping, not a new identity.

Numerical validation covers root residuals, factorization, phase addition, signed discriminants, the backward heat equation, near-collision parameters +/-1e-6, enclosing and isolating winding counts, traversal reversal, and palette changes. The path suite has twelve named cases, including simple/double zero encounters, endpoint zeros, near-root guards, zero-length paths, tangency, coincident boundaries, rotated boundaries, and additional full turns. Independent Python checks use 70-digit Decimal reference roots and separately sampled contour/path phases. Eight corrupted model exports and eight corrupted path exports are rejected. Directed-rounding certification is not claimed; boundary tolerances and integration convergence are empirical. Paths through or too near a root skip phase integration explicitly.

The Release build passes with the existing net5.0 support and unused-field warnings. Existing prime mesh and unwrapping PNG exports remain byte-identical to the pre-change baseline; all three earlier zeta PNG exports match their preserved hashes. Native verification observed the layout, hover values, custom start/end clicks across different panels, playback reaching -1 and stopping, the zero preset, palette rotation to 22.5 degrees, the example path, and successful Save PNG + data output including the path overlay and JSON/text sidecars. The final app remains open with the example path and rotated palette.

Durable evidence is under research/zero-motion/evidence. The independent validator is research/zero-motion/verify_exports.py. The input/evidence manifest records source hashes, regression hashes and UI observations. To reproduce on this host, set DOTNET_ROLL_FORWARD=Major, then run the Release Graphics.dll with --zero-motion output.png [lambda] [paletteDegrees], or --zero-path output.json lambda startReal startImag endReal endImag paletteDegrees. The latter also writes the corresponding PNG with its path overlay and data sidecars. UI export and CLI path export share the same export routine.

This is an exact polynomial calibration, not an implementation of the Riemann xi heat deformation. Its frozen quadratic collision prediction Delta_lambda=-lambda is exact and reproduces the known spacing baseline. No new RH inequality or prime generator is established; graph.riemann stays open. Future work must test a measurement or correction on higher-degree controls against existing spacing/derivative predictors before transferring it to xi.

Sources: Rodgers and Tao, https://arxiv.org/abs/1801.05914 (de Bruijn-Newman context and heat-flow direction); NIST DLMF https://dlmf.nist.gov/1.10.E9 (phase/argument principle). The project's open RH proof obligations remain in graph.riemann.proof.current.md.
