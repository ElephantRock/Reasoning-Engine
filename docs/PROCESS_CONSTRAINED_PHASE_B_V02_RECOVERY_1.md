# Process-Constrained Phase B v0.2 — Recovery 1 incident record

Status: **incident recorded; recovery implementation requires review before any additional paid call**.

The authorized Phase-B v0.2 execution (GitHub Actions run `35034720355`) passed all frozen pre-provider checks and then stopped after five records. The interruption occurred at `PCB2-AD01 / MATCHED_SCAFFOLD` with:

`BudgetExceeded: MATCHED_SCAFFOLD__ABDUCTIVE_DIAGNOSTIC: environment-action budget exhausted`

The uploaded source artifact is `process-constrained-phase-b-v02-results-authorized` (artifact id `10422887717`, artifact digest `sha256:642590fc450cfd90dc7157249111a87ceffe2491fe6baf3935b727a599abc104`). Its `runs.jsonl` contains exactly five records and has SHA-256 `23887fab0915ad8c727cd2d817b6015e9fe188d8c0fd75f92caf0f522f3c2843`.

Four records are complete `PCB2-DC01` executions, one for each frozen condition. The fifth is the interrupted `PCB2-AD01 / MATCHED_SCAFFOLD` record.

Review identified a runner-control defect rather than a provider failure: `ProtocolRuntime.transition()` raises `BudgetExceeded` when the matched scaffold requests an environment action after using its frozen action budget, but `run_protocol_condition()` catches `InvalidTransition` and `EnvironmentError` while omitting `BudgetExceeded`. The generic comparator path already treats action-budget exhaustion as an ordinary scientific `execution_failure`. For the protocol path, the uncaught exception therefore incorrectly escalated an observable condition failure into a study-wide technical interruption.

Recovery 1 must be frozen before any additional provider call. The intended recovery constraints are:

- preserve the four completed `PCB2-DC01` records exactly;
- do not regenerate the interrupted `PCB2-AD01 / MATCHED_SCAFFOLD` condition;
- mechanically reclassify that exact `BudgetExceeded` outcome as an `execution_failure` with effective score `0.0`; the action budget is known to have been fully consumed (`3` actions), while the missing raw model-call/trace details remain explicitly unavailable and must not be fabricated;
- change only the protocol-runner exception classification so future `BudgetExceeded` events become per-condition scientific failures instead of aborting the study;
- execute only the remaining 91 case×condition cells in their original frozen order;
- keep the frozen cases, prompts, environments, model (`glm-5.1`), temperature (`0`), 16,384 completion ceiling, condition balancing, and scientific eligibility gates unchanged;
- stop again on any genuine technical provider/completion interruption, preserving all completed records;
- treat cost/latency summaries as incomplete for the one reclassified source cell because its model-call log was not preserved by the original defect.

This document records the incident and recovery constraints only. It does not itself authorize a recovery run.