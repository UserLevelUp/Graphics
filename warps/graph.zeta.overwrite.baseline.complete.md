# Four-color zeta overwrite baseline

defines: graph.zeta.overwrite

Use each center's zeta value as its local output origin. For every covered sample, color the quadrant of the difference from that local origin. Let the nearest center win and break a distance tie by the center's row-major index. Keep the union of all competing quadrants to indicate disagreement.

Use the same square of side 0.5 centered on the known zero near 0.5 + 14.1347251417i. Compare three local grids and a fixed-origin panel. Use radius 0.06 for the winding controls, centered on the zero and on 0.67 + 14.1347251417i.

Check that reversing draw order preserves owners, colors and disagreement. Compare coarse and fine grids, then translate the fine grid by half a step. Check the fixed-origin winding with 32 and 64 samples. Record evaluator and compositor timings separately.

The original WinForms build succeeded before implementation. The forward-difference evaluator produced a 108 ms zeta grid on one baseline run, with 18 ms for four stamp passes.
