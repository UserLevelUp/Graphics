# Completed zero-index slope test and animation

defines: graph.riemann.zero_index
consumer: graph.riemann.continuation.animation.model

The user's screenshot shows the bright Z3 continuation trajectory and its start at sigma=1/2. It does not label input integers as primes. The final comparison therefore uses Z_p for each prime index p<=100, with nonprime indices as controls. An earlier tentative interpretation using integer heights t=p was superseded by this clarification; it is not the primary test.

Paths satisfy zeta(s(a))=a with real a. Where zeta'(s) is nonzero, ds/da=1/zeta'(s). Where Re(ds/da) is nonzero, the plotted slope dt/dsigma is Im(ds/da)/Re(ds/da). The old recorded paths already give starting slopes about -0.159 for Z1, +0.224 for Z2 and -0.347 for Z3. Prime index2 is a counterexample to the proposed negative-slope rule.

Completed: independently reviewed starting slopes for indices 1..100, 651 short-path samples for all 25 prime indices plus six controls, 32 native phase backgrounds, and the 84-second standalone animation at `media/zero-index-slope-tour.mp4`.

The sign test fails: prime indices have 14 negative and 11 positive initial slopes; composite indices have 35 negative and 39 positive slopes. Index 1 is neither and has a negative slope. This is a test of zero-index labels, not individual prime values.

Review evidence is in `evidence/independent-math-grid-review.json`, `evidence/independent-visual-review.json`, and `evidence/media-review.json`. The movie decoded fully: 2016 frames at 1280x720 and 24 fps, silent; all 33 scenes, 66 scene-boundary frames and five additional motion frames were checked. The acceptance record is `evidence/acceptance.json`; live Warp progress is saved separately after publication of both declared review gates.

Starting known zeros on sigma=1/2 is input selection, not an RH proof. Numerical comparisons are not rigorous error enclosures. Colors at a zero are undefined; the movie masks near-zero values neutrally. The earlier 320-second presentation remains byte-identical. No novelty, new prime function, or speed advantage is claimed.
