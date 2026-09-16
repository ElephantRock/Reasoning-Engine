# Process-Constrained Phase B v0.2 — Recovery 1 freeze

Status: **recovery design frozen for review; no additional paid call is authorized by this document**.

The authorized Phase-B v0.2 execution (GitHub Actions run `35034720355`) passed all frozen pre-provider checks and then stopped after five records. The interruption occurred at `PCB2-AD01 / MATCHED_SCAFFOLD` with:

`BudgetExceeded: MATCHED_SCAFFOLD__ABDUCTIVE_DIAGNOSTIC: environment-action budget exhausted`

The uploaded source artifact is `process-constrained-phase-b-v02-results-authorized` (artifact id `10422887717`, artifact digest `sha256:642590fc450cfd90dc7157249111a87ceffe2491fe6baf3935b727a599abc104`). Its `runs.jsonl` contains exactly five records and has SHA-256 `23887fab0915ad8c727cd2d817b6015e9fe188d8c0fd75f92caf0f522f3c2843`.

Four records are complete `PCB2-DC01` executions, one for each frozen condition. The fifth is the interrupted `PCB2-AD01 / MATCHED_SCAFFOLD` record.

## Root cause

`ProtocolRuntime.transition()` raises `BudgetExceeded` when a protocol/scaffold requests an environment action after exhausting its frozen action budget. The generic comparator path already treats the same behavior as an ordinary scientific `execution_failure`. The protocol path caught `InvalidTransition` and `EnvironmentError` but omitted `BudgetExceeded`, so this observable condition failure escaped the per-condition handler and was incorrectly promoted to a study-wide technical interruption.

This is a runner-control classification defect. It does **not** justify changing the cases, prompts, action budgets, environments, model, temperature, token ceiling, execution order, or scientific gates.

## Frozen Recovery 1 rule

Recovery 1 must:

- preserve the four completed `PCB2-DC01` JSONL records byte-for-byte;
- never regenerate any of the five source cells;
- mechanically reclassify only the exact fifth source record (`PCB2-AD01 / MATCHED_SCAFFOLD`) from `technical_incomplete` to `execution_failure` with effective score `0.0`;
- set `actions_used=3` for that cell because the frozen abductive scaffold action budget is exactly 3 and `BudgetExceeded` is raised before a fourth action is executed;
- leave the unavailable original provider-call records, protocol trace, and exact transition count unavailable rather than reconstructing or fabricating them;
- mark cost logging incomplete for that one source cell and exclude it only from descriptive call/token/latency means; primary outcome scoring and execution-failure rate still include it;
- execute only the remaining **91** case×condition cells, in the original frozen order and with the original condition-position metadata;
- classify any future protocol `BudgetExceeded` as a per-condition `execution_failure`, preserving the completed model calls and protocol trace for that cell;
- stop again on any genuine provider/completion/adapter technical interruption and preserve every completed record;
- keep the frozen model `glm-5.1`, temperature `0`, completion ceiling `16384`, Z.AI endpoint, case suite, action catalogs, protocol/scaffold structures, FULL prompt, CONTROL behavior, execution balancing, objective environment scores, and Phase-C eligibility gates unchanged.

## Recovery implementation

The reviewed candidate implementation is `benchmark/recover_process_phase_b_v02_r1.py`. It imports the frozen v0.2 scientific surface and contains a recovery-local copy of the protocol-condition execution loop with one scientific change only: `BudgetExceeded` is caught alongside other semantic/runtime execution failures. The original frozen `benchmark/run_process_phase_b_v02.py` remains unchanged for historical reproducibility.

The runner validates the exact source `runs.jsonl` SHA-256 and exact five-cell execution prefix before doing anything. The first four source lines are copied directly into the combined JSONL. The fifth is mechanically reclassified under the rule above. The runner then skips all five source keys and executes the remaining 91 cells. On completion, it runs the original `core.aggregate()` eligibility logic and replaces only the descriptive usage fields with coverage-aware means so the missing source call log is not silently treated as zero cost.

Dedicated zero-cost tests verify:

- the frozen five-cell prefix and 91-cell pending count;
- a matched-scaffold action-budget overrun becomes `execution_failure` rather than a study interruption;
- all model-call records up to the over-budget request remain present for future such failures;
- source-cell reclassification does not invent lost trace/call data;
- descriptive usage coverage reports 23/24 logged matched-scaffold cells if Recovery 1 completes;
- the complete existing Phase-B v0.2 correction, runner, and final-review test suites still pass.

## Claim boundary

Recovery 1 is a continuation of the frozen Phase-B v0.2 experiment, not a new scientific design. The one source cell has incomplete descriptive cost/trace logging because the original runner defect discarded those records. Its primary scientific classification is nevertheless mechanically determined by the observed frozen exception and by the already-frozen comparator treatment of the same budget-exhaustion behavior.

No Phase-C conclusion may be drawn from the partial source run. Only a complete 96-cell recovered dataset may enter the original frozen aggregation and decision rule.
