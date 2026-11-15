# Worker coordination

defines: graph.primes.phase.coordination
consumer: graph.primes.phase
consumer: graph.primes.phase.carbon.progress
consumer: graph.primes.phase.copilot.progress
consumer: graph.primes.phase.codex.progress
consumer: graph.primes.phase.hydrogen.progress

The coordinator reviews every checkpoint and decides whether to continue, steer, or stop. Carbon reviews the analytic derivation, Copilot reviews numerical and display failure cases, Codex independently audits the mathematical inference, and Hydrogen prepares routine implementation checklists. Each worker has its own directory beneath research/prime-phase.

Each model is given an absolute UTC deadline and asked to execute `Get-Date -Format o` at the start, after each reasoning step lasting at most 30 seconds, and immediately before returning. The target is to yield 30 seconds before the 180-second deadline. A response contains STATUS, ACK, and CLOCK plus findings or a final review. Timestamp parsing checks the response format; a timestamp alone does not prove tool execution. Actual clock access was tested for all provider families.

The supervisor measures elapsed time with a monotonic clock. At 180 seconds without a returned response it publishes `checkpoint_overdue`, explicitly labeled runner status with model progress still pending. At 240 seconds it stops its owned process tree and retains partial stdout/stderr. A deadline prompt cannot guarantee that an inference service responds on time. A successful early response yields immediately.

A CHECKPOINT pauses at a real turn boundary. The coordinator has 300 seconds to publish a decision for the exact run and turn using `steer-review.py PROVIDER RUN_ID TURN continue|steer|stop INSTRUCTION_FILE`. Decisions are atomically published once. The next prompt includes the instruction and prior response transcript, and the model must echo its unique ACK token. The records distinguish queued, delivered, and acknowledged. This uses explicit transcript replay rather than a provider's global most-recent session.

Runs allow at most three model turns. Recur's outer attempt timeout is 1800 seconds. Dispatch allows three concurrent workers, one per helper host, with disjoint workspaces. Four attempts are permitted per slice for this setup, including retained historical launcher failures. Recovery remains an explicit coordinator operation. No worker performs a Git commit, pushes, or accepts its own gate.

The `graph.primes.phase` recur-watch topic has coordinator, carbon, copilot, codex, and hydrogen subscribers. Workers drain notifications at turn boundaries with at most three attempts and retain diagnostics. Progress publications use `graph.primes.phase.PROVIDER.progress` and reference the exact run status. Status references the model response or final review. Steering is carried by an exact-run JSON decision, and the transition is published through the same trace. Notifications carry trace IDs; the coordinator reads the referenced artifact for meaning.

Useful commands, rooted at C:/src/graph:

```powershell
recur warp show graph.primes.phase -d C:/src/graph --json
recur warp dispatch graph.primes.phase -d C:/src/graph --json
recur-watch topic drain graph.primes.phase --id coordinator --confirm -d C:/src/graph --json
recur trace-id graph.primes.phase --scope '**' --format full -d C:/src/graph
python research/prime-phase/test_review_protocol.py
```

The current helpers were tested with AGY 1.5.9, Copilot 1.0.112, and Codex CLI 0.154.0. Carbon uses gemini-4-carbon, Hydrogen uses gemini-4-hydrogen, and Copilot uses its supported auto routing. Codex uses its built-in configuration with supported automatic approval review because the saved model was rejected by this ChatGPT account; the observed default was gpt-6-astra. These are invocation settings, not edits to the user's global model preferences.

Raw runtime state and CLI stderr remain local. Immutable review responses, steering decisions, progress events, and archived Recur attempt records are retained with the project snapshot. A `produced` attempt means its configured artifact checks passed. Coordinator review accepts the review gate separately. No review gate asserts that the renderer or the Riemann proof is complete.
