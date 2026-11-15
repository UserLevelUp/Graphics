# Local origins and the Riemann proof attempt

defines: graph.riemann
consumer: graph.zeta.overwrite
consumer: graph.zeta.contours
consumer: graph.zeta.origins
consumer: graph.riemann.collision

The proof remains open. This parent tracks the attempt to derive a global statement from the user's local-origin quadrant geometry. The completed children record finite experiments.

At each center c consider F_c(u) = zeta(c+u) - zeta(c). Write its first nonzero Taylor term as a_m u^m. For all sufficiently small radii r, the leading term dominates the higher terms on |u|=r, so F_c winds m times around zero. Therefore the limiting winding is one exactly when zeta'(c) is nonzero. A simple zero of the derivative gives two turns. This is a consequence of the Taylor expansion and the argument principle. [NIST DLMF](https://dlmf.nist.gov/1.10)

Speiser's theorem states that RH is equivalent to zeta' having no zeros in 0 < Re(s) < 1/2. Thus a precise target for this project is to establish that every center c in that entire open half-strip has an epsilon(c) > 0 for which every circle of radius 0 < r < epsilon(c) has local winding one. The local Taylor reasoning establishes the equivalence to a nonzero derivative. It supplies no global derivative exclusion. That exclusion is the unfinished mathematical step. [Levinson and Montgomery, corollary to Theorem 1](https://archive.ymsc.tsinghua.edu.cn/pacm_download/117/6174-11511_2006_Article_BF02392141.pdf)

Arias-de-Reyna's X-Ray of Riemann zeta-function studies the real and imaginary zero contours, critical points, and the Speiser connection. Its graphical arguments provide a relevant starting point for comparing this tool with established work. [Primary paper](https://arxiv.org/abs/math/0309433)

There are two exact limits to the graphical inference.

Adding a constant C preserves every local difference, since (f(s)+C)-(f(c)+C)=f(s)-f(c), while changing the absolute zero set. This prevents local differences alone from locating zeros of f. Derivative zeros survive the constant shift, which makes Speiser's criterion relevant to precisely this limitation.

A finite circle can enclose another preimage of f(c). For f(s)=(s-rho)^2 and c=rho+d, the centered map is u(u+2d). Its winding is two when r>2|d| and one when r<2|d|. Consequently a two-turn observation at a finite radius does not by itself establish that c is a derivative zero.

An alternate established target is positivity of Re(xi'/xi) throughout Re(s)>1/2. This is the horizontal derivative of log|xi| and expresses a local direction. A proof would need an unconditional global sign bound. [Sondow and Dumitrescu](https://arxiv.org/abs/1005.1104) · [Matiyasevich, Saidak and Zvengrowski](https://arxiv.org/abs/1205.2773)

A possible next bounded bubble would certify derivative counts within specified rectangles using ball arithmetic and boundary enclosures. Extending a finite verified result to all heights would still require a mathematical argument.

Resume with recur warp show graph.riemann, recur trace-id graph.riemann --scope "**" --format full, and recur lang report warps/graph.zeta.origins.recur, all rooted at C:/src/graph.

The completed graph.primes.phase experiment now includes local prime-contribution colors, shared-height prime/zeta overlays, and sampled factor-phase unwrapping. Its controlled comparisons did not show prime-height enrichment. See warps/graph.primes.phase.results.complete.md. These finite numerical findings supply no global zero exclusion; the RH proof remains open.

The completed graph.riemann.collision child now proves an exact quartic heat-flow threshold and supplies rational counterexamples to unrestricted frozen local forecasts. It also derives a conservative finite-polynomial safe interval from adjacent-root dynamics. See warps/graph.riemann.collision.results.complete.md and graph.riemann.collision.next.current.md. These distinguish a valid bound from an exact prediction and identify the missing interaction control. They do not supply a global theorem for the Riemann deformation.

For context, the de Bruijn-Newman deformation H_t has all zeros real exactly when t >= Lambda. RH is equivalent to Lambda <= 0; Rodgers and Tao proved Lambda >= 0. Thus an argument on this route still needs the complementary bound. Our quartic threshold is a different parameter for a different function. [Rodgers and Tao](https://arxiv.org/abs/1801.05914)
