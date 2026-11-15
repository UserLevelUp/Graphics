# Accepted quadrant adaptation

defines: graph.primes.quadrant_phase
consumer: graph.primes.function

Warp: `warps/graph.primes.quadrant_phase.warp-map.json`.

Intent: compute F(n)=(1+i)i^R from the Wilson remainder, then classify by its exact canonical quadrant. No prime labels enter the phase classifier. This is a Wilson-derived encoding, not an independent zeta predictor.

Observed: independent mathematical review supports the all-integer theorem. Python checks passed against a sieve on 0..10000 and full factorials on 2..2000, including 96/97, the 4 exception, and uncertainty controls. Evidence: `evidence/validation.json`.

Accepted: the native export and interactive view compute the phase and exact quadrant. Seven exported records/images passed native integration checks (805 candidate records, 707 tile colors, 28 sector samples). Independent review passed 16 checks with no blockers. The reviewer inspected both 0-degree and 37-degree views. Root UI observation confirmed the 4/96/97 controls and rotation. Evidence is recorded in `evidence/review.json`, `evidence/native-validation.json` and `evidence/ui-validation.json`.

Both equation and native Warp gates are complete; `evidence/warp-progress.json` records the live projection. The Recur watcher observed this bounded lane; its events are not test or gate acceptance. A Recur-git snapshot records the handoff state. The existing presentation video remains unchanged.

Use: `Graphics.exe --prime-quadrant-lab` opens the interactive mode. See `README.md` for the explicit newer-runtime roll-forward setting and export commands. The mathematical proof applies to all integers n>=2; native computation is capped at100000. No independent zeta or pixel-readback test has been established.
