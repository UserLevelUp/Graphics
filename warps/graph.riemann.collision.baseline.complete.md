# Exact collision control baseline

defines: graph.riemann.collision.baseline
consumer: graph.zeros.motion.model
consumer: graph.riemann.collision

Source baseline: 170993c; restore tag graph-zero-motion-lab-2026-11-14.

The existing F(z,lambda)=z^2-2*lambda example is solved exactly. Its collision occurs at lambda=0. A second-order local approximation is the complete function in that example, so its successful prediction does not test omitted higher-order terms.

The new quartic starts with four distinct real zeros -3,-1,1,3. All three adjacent gaps are 2. This supplies equal starting gaps while retaining interactions between more than two zeros. The model and heat sign are fixed before accepting any collision forecast.

Required final artifacts: research/collision-proof/exact-quartic-proof.md, research/collision-proof/verify_exact.py, exact checker output and a hashed evidence manifest. The optional figure must be labeled as a polynomial control. Scope and acceptance are in graph.riemann.collision.contract.complete.md.

The parent graph.riemann slice-final remains pending. This child does not inherit or satisfy its global all-heights mathematical obligation.
