# Interaction-aware finite-polynomial bounds

defines: graph.riemann.gap.tool
consumer: graph.riemann.gap.proof
consumer: graph.riemann.gap.verify

This research tool accepts a finite set of at least three distinct rational real roots. It computes rigorous rational enclosures for two guaranteed collision-free durations under P_t=-P_zz, then independently checks selected rational times with exact Sturm root counts. Its input is a polynomial root configuration, not a list of primes or Riemann zeros. It does not solve RH or establish a new prime algorithm.

From C:/src/graph:

```powershell
python -B research/gap-bound/verify_bound.py
python -B research/gap-bound/verify_bound.py --roots=-3,-1,1,3 --output work/custom-gap-certificate.json
python -B research/gap-bound/verify_bound.py --roots=0,1/20,1,3,6
python -B research/gap-bound/render_bounds.py
```

Create the output parent directory first if using --output. Unsorted input is sorted; duplicates are rejected. The CLI supports degree at least three. The separate exact degree-two formula is proved in interaction-bound-proof.md. Display decimals and the PNG are approximate; the reported Fraction endpoints and Sturm counts are exact. Very small gap-to-diameter ratios may need more than the fixed 80 bisection steps to display a strict dynamic improvement, and the output explicitly reports whether its enclosures establish that comparison.

The general interval guarantee comes from interaction-bound-proof.md. The finite test suite alone does not prove it. The checker uses no known collision answer in bound_data or certify_case; the known quartic threshold appears only in independent controls.

Watch orchestration uses graph.riemann.gap with Carbon and Codex mathematical reviews, a Hydrogen evidence checklist, explicit clock deadlines, coordinator steering, and trace-token acknowledgements. Reviewers do not execute the mathematical checker. The coordinator reviews their reasoning and executes the checks separately. A produced Watch attempt records successful protocol verification; it does not establish mathematical truth or accept the final gate.

See evidence/certificates.json, evidence/manifest.json, the provider run histories, and warps/graph.riemann.gap.results.complete.md for the observed outcome. The open infinite-system obligation is warps/graph.riemann.gap.next.current.md.
