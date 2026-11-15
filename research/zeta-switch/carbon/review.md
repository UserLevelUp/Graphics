publish: graph.riemann.switch.carbon.response

STATUS: COMPLETE
ACK: e554d7facabf4f33a475143e66db2191
CLOCK: 2026-11-15T01:10:49.2879368-08:00

VERDICT
ACCEPT

REASONING
This review accepts the mathematical contract and validation plan only; it does not certify implementation code or executed tests, and global RH remains open.

- **Two-state & product identities**: On $\mathbb{C} \setminus \{1\}$, $Z_b(s) = \zeta(s) - 1 + b$ ($b \in \{0,1\}$) continues the $n=1$ Dirichlet-term switch analytically with $Z_0' = Z_1' = \zeta'$, $\operatorname{Im}(Z_0) = \operatorname{Im}(Z_1)$, and zero sets $\zeta^{-1}(0)$ ($b=1$) and $\zeta^{-1}(1)$ ($b=0$). $G(s) = \zeta(s)(\zeta(s)-1)$ is holomorphic away from $s=1$ and shares the exact zero union $\zeta^{-1}(\{0,1\})$ without switching jumps. Local differences cancel $-1+b$ on fixed branches and add $b(s)-b(c)$ across branches.
- **Selector equivalence**: Because $|z|^2 - |z-1|^2 = 2\operatorname{Re}(z) - 1$, $\operatorname{Re}(z) \le 1/2$ (tie to $b=1$) equals $|z| \le |z-1|$, giving $W^{-1}(0) = \zeta^{-1}(0) \cup \zeta^{-1}(1)$ with no spurious zeros.
- **Seam discontinuity (including $\zeta'(s_0)=0$)**: On $\operatorname{Re}(\zeta(s)) = 1/2$ (distinct from $\operatorname{Re}(s)=1/2$), $|W(s)| = \sqrt{1/4 + \operatorname{Im}(\zeta(s))^2} \ge 1/2$ is continuous, while $W$ jumps by $-1$ from $b=1$ to $b=0$. Even if $\zeta'(s_0)=0$ at a seam point $s_0 \neq 1$, $\zeta$ is non-constant holomorphic (open mapping theorem): $\zeta(s) - \zeta(s_0) = c_m(s-s_0)^m + O(|s-s_0|^{m+1})$ ($m \ge 2, c_m \neq 0$) creates $m$ alternating sectors of $\operatorname{Re}(\zeta) \le 1/2$ and $\operatorname{Re}(\zeta) > 1/2$ meeting at $s_0$. Approaching $s_0$ from any $b=0$ sector yields limit $\zeta(s_0)-1 \neq \zeta(s_0) = W(s_0)$, so the $-1$ discontinuity persists at every seam point, prohibiting cross-seam linear interpolation and ordinary argument-principle counting.
- **No off-line zero constraint**: $W(s)$ and $G(s)$ post-compose $\zeta(s)$ with fixed maps on $\mathbb{C}$ independent of $\operatorname{Re}(s)$. Any hypothetical off-critical-line zero ($\zeta(s_*)=0, \operatorname{Re}(s_*) \neq 1/2$) maps to $z=0 \implies b=1, W(s_*)=0, G(s_*)=0$ identically to an on-line zero. The switch leaves Euler's product intact and adds zero constraint excluding off-line $\zeta$ zeros.

TESTS
No tests were executed in this text-only audit. The validation plan appropriately specifies independent `mpmath` checks of $Z_b, W, G$, derivatives, selector/tie boundaries, seam/non-analytic metadata, removable $\eta$-quotient singularities near $1 + 2\pi i k/\log 2$, UI/export invariance, corrupted-export negative controls, and non-circular distinction of the approximate 1-point candidate near $1.40778804065+23.32798775456i$ from $\zeta$ zeros.
