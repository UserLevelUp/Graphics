publish: graph.primes.phase.carbon.response

# VERDICT
ACCEPT

# REASONING
**Analytic Derivation:** For $s = \sigma + it$ with $\sigma > 1$, each prime $p \ge 2$ satisfies $|p^{-s}| = p^{-\sigma} < 1$, placing $1 - p^{-s}$ in the open disk $|z - 1| < 1$ disjoint from $(-\infty, 0]$. The principal branch $-\operatorname{Log}(1 - p^{-s}) = \sum_{k=1}^\infty k^{-1} p^{-ks}$ is single-valued and analytic, and the sum $L_N(s)$ converges absolutely as $N \to \infty$ to the canonical analytic logarithm $\log \zeta(s)$ (normalized so $\log \zeta(\sigma) \in \mathbb{R}$ for real $\sigma > 1$, matching DLMF 25.2.11). Note a minor notation detail: write $\log \zeta(s)$ unambiguously for this analytic branch rather than the principal value $\operatorname{Log}(\zeta(s))$, which differs by $2\pi i m$ when $\operatorname{Im} \log \zeta(s) \notin (-\pi, \pi]$.

For integer $N \ge 2$ and $\sigma > 1$, every prime $p > N$ satisfies $p \ge N + 1$, giving the tail bound:
$$|\log \zeta(s) - L_N(s)| \le \sum_{p > N} \sum_{k=1}^\infty \frac{p^{-k\sigma}}{k} \le \sum_{p > N} \frac{p^{-\sigma}}{1 - (N+1)^{-\sigma}} \le \frac{\int_N^\infty x^{-\sigma}\,dx}{1 - (N+1)^{-\sigma}} = B_N.$$
Because $\zeta(s) - P_N(s) = P_N(s)\left(\exp(\log \zeta(s) - L_N(s)) - 1\right)$ and $|\exp(w) - 1| \le e^{|w|} - 1$, the multiplicative bound $|\zeta(s) - P_N(s)| \le |P_N(s)|(e^{B_N} - 1)$ holds strictly in exact arithmetic, with $B_N$ strictly decreasing in $N$.

**Domains and Relation to RH:** Restricting the Euler product to $\sigma > 1$ is mathematically essential; there $\zeta(s)$ is zero-free and $\log \zeta(s)$ is analytic. For $\sigma \le 1$, absolute convergence fails, $P_N(s)$ does not unconditionally converge to $\zeta(s)$, and nontrivial zeros create logarithmic branch points inside the critical strip $0 < \sigma < 1$. Note that the test ordinates $t \approx 14.134725$ (first nontrivial zero ordinate $\gamma_1$, shifted to $\sigma = 2$) and $t \approx 23.298320$ (not $\gamma_2 \approx 21.022040$) probe oscillatory Euler phases on $\sigma = 2$, not critical-strip zeros; the contract properly separates $\sigma > 1$ experiments from analytic continuation and RH.

# TESTS
1. Verify $B_N$ decreases strictly across $N \in \{32, 128, 512, 2048\}$ at $\sigma = 2$.
2. Verify $|\log \zeta(s) - L_N(s)| \le B_N + \varepsilon_{\text{num}}$ using the continuous analytic branch $\log \zeta(s)$ (not unadjusted principal $\operatorname{Log}(\zeta(s))$) and $|\zeta(s) - P_N(s)| \le |P_N(s)|(e^{B_N} - 1) + \varepsilon_{\text{num}}$ at all three $s$ values.
3. Verify explicit quadrant-coloring tie-breaking on real/imaginary axes (especially $s = 2$, where $\operatorname{Im} L_N(2) = 0$) and consistency modulo $2\pi i$ across summation/multiplication orders.
