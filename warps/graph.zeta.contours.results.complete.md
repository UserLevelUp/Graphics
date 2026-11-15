# Oriented zeta contours results

publish: graph.zeta.contours

Built the WinForms project and opened the Zeta contours view using its button. The window showed the same two phase plots and band counts as the PNG exported through --zeta-contours. The original --zeta-preview export matched the previous overwrite PNG byte for byte.

At 16 and 32 boundary samples per edge, ordinary zeta counted 0/1/0 in the left, center and right bands and the shifted control counted 0/0/1. Reversing traversal produced 0/-1/0 and 0/0/-1. Both outer rectangles counted 1 counterclockwise. The Hardy Z sign bracket gave t approximately 14.134725142 on the critical line.

The check covers one low-height window and uses floating-point evaluations, including truncated zeta and log-gamma approximations. Agreement at two sample spacings cannot exclude aliasing between samples. The next mathematical step would be to bound zeta on every boundary segment using ball arithmetic, verify the on-line sign bracket with error bounds, and compare the certified counts against a published finite verification.

Preview PNG SHA-256 f22f53d14f9d0b2d1247b9fb26fabf28a0204021c2c3d680cb9bf4d2b5c86918.
