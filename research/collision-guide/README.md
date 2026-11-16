# Reuse the finite-polynomial collision certificate

defines: graph.riemann.collision_guide.readme
consumer: graph.riemann.gap.proof

This chapter explains the finite heat-flow certificate, its documented development, practical applications and its precise connection to the Riemann Hypothesis. Start with [the guide](guide.md), then inspect [the narrated script](script.json). The result bounds a collision-free interval for a specified finite polynomial; it is not a new prime test or an RH theorem. Novelty has not been established.

Watch the [focused explanation with repository ending](media/finite-root-collision-guide.mp4) (10:50.917), or the [updated complete presentation](media/presentation-with-collision-guide.mp4) (20:42.125). Download the [portable checker and proof toolkit](media/collision-certificate-toolkit.zip). Media include narration and selectable English captions; the source chapter is 720p and the combined exports are 1080p. Caption sentence timing is approximate.

From the Graphics repository root:

```powershell
python -B research/collision-guide/use_certificate.py --roots=-3,-1,1,3 --duration=17/32
```

The interval status is `certified`; the pointwise exact check finds four distinct real roots and no repeated root. Duration `3/5` is outside the interval guarantee but still has four simple real roots. The guide explains why these are different questions.

`verify_explanation.py` independently checks polynomial arithmetic, rational bound enclosures, 100 root counts across 25 cases, wrapper controls and provenance source hashes. `evidence/explanation-review.json` also records the manual narrative and mathematical review. `trace_discovery.py` captures the declared lineage and original Git milestones; its saved receipt is frozen with the reviewed script. Regeneration changes its observation timestamp and requires a new evidence review.

`render_chapter.py` produces a 23-scene narrated chapter from matched local voice clips. `assemble.py` inserts that chapter before the repository card in the preserved prior presentation. `export_focused.py` exports the chapter with that closing card. `verify_media.py` checks decoding, diagram formulas, scene frames, narration placement, source preservation and captions. `package_delivery.py` creates the portable exact-arithmetic toolkit and viewing guide.

Recur Warp: `graph.riemann.collision_guide`, with explanation and video gates. The watcher records matching filesystem events; internal collaboration workers carry out delegated tasks. Completion of this documentary lane does not close `graph.riemann.gap.next` or the parent RH investigation.

The public repository is https://github.com/UserLevelUp/Graphics on branch `graph/riemann-continuation`. Media are exported separately; manifests bind their content hashes and the source checkpoint. The previous video remains unchanged.

Final review passed all three video/audio decodes, 219 frame comparisons, all 23 narration clips and captions. The compact toolkit reproduced the exact worked example after copying. [Acceptance](evidence/acceptance.json) binds the mathematical, provenance, media and visual-review evidence; trace and Eventness metadata organize those observations rather than proving their claims automatically.
