# Open mathematical obligation after the quartic control

defines: graph.riemann.collision.next
consumer: graph.riemann.collision.proof
consumer: graph.riemann

For a finite polynomial heat flow P_t with distinct simple real roots r_j(t), differentiating P_t(r_i(t))=0 gives

r_i'(t) = P_t''(r_i)/P_t'(r_i) = 2 sum_{j != i} 1/(r_i-r_j).

For adjacent roots a<b, set g=b-a. Subtracting their velocities gives the exact identity

g' = 4/g - 2*g*S,
S = sum_{r outside {a,b}} 1/((b-r)*(a-r)).

Every term in S is positive while the roots are real, simple and ordered and there are other roots. For a two-root polynomial S=0. The isolated-pair forecast discards this contribution.

One valid finite-polynomial bound does follow: (g^2)'=8-4*g^2*S <= 8. Integrating backward from t=0, before the first collision, gives g(t)^2 >= g(0)^2+8*t. Consequently a first backward collision cannot occur for -g_min(0)^2/8 < t <= 0. The isolated-gap estimate gives a safe interval under these assumptions; it does not give the exact collision time. Here that interval is (-1/2,0], while the actual real-rooted interval extends to -2/3. This elementary consequence of the root-motion equation is not claimed as a new theorem.

For the quartic at t=0, the velocities in root order -3,-1,1,3 are -11/6,-1/2,1/2,11/6. Thus the adjacent gap derivatives are 4/3,1,4/3, although the gaps all equal 2. The isolated-pair formula would give 2 for each. Equal gap sizes alone do not determine their rates of change.

Next candidate obligation: derive a stronger, non-circular interval bound on the external interaction term (or a better global quantity), retaining enough information to control collisions beyond the conservative nearest-gap interval. Test any proposed inequality against exact higher-degree controls before using it in the Riemann deformation. Selecting midpoint centers is a possible restriction to test; the current arbitrary-center counterexamples do not refute every restricted formulation.

Transfer to the infinite Riemann deformation requires its own analytic justification, convergence/regularization of any infinite root sums, and estimates valid for all relevant zeros and heights. The finite polynomial sum above is not such a justification. We have no inequality meeting this obligation, and the parent RH proof remains open.
