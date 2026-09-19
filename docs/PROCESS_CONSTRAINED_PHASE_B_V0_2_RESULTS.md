# Process-Constrained ARC Phase B v0.2 — Audited Results

Status: **completed recovered development study; frozen decision = `STOP_PROCESS_CONSTRAINED_SELECTOR_PATH`. Phase C remains closed.**

This document records the independent post-run audit of the complete 96-cell Process-Constrained Phase B v0.2 dataset. The result uses the original frozen Phase-B v0.2 aggregation and eligibility rules. Recovery 1 repaired only the runner-control classification defect documented in `PROCESS_CONSTRAINED_PHASE_B_V02_RECOVERY_1.md`; it did not change the cases, prompts, protocols, action budgets, model, execution order, environment scoring, or scientific gates.

## 1. Execution provenance

Original authorized run:

- GitHub Actions run: `35034720355`
- source artifact: `process-constrained-phase-b-v02-results-authorized`
- source artifact id: `10422887717`
- source artifact ZIP digest: `sha256:642590fc450cfd90dc7157249111a87ceffe2491fe6baf3935b727a599abc104`
- source `runs.jsonl`: 5 records
- source `runs.jsonl` SHA-256: `23887fab0915ad8c727cd2d817b6015e9fe188d8c0fd75f92caf0f522f3c2843`

Recovery 1:

- GitHub Actions run: `35038200982`
- recovery artifact: `process-constrained-phase-b-v02-recovery1-results`
- recovery artifact id: `10426084722`
- recovery artifact ZIP digest: `sha256:82eae8e6575a1172c29deee7b9315f94f484a004af2022b18b727dab6ae24118`
- reviewed recovery source commit: `ba6744b21abe92d477780dd74ef70e36af6defc2`
- target model: `glm-5.1`
- temperature: `0`
- completion ceiling: `16384`
- Python: `3.12.14`
- `openai==3.13.0`

Recovered output hashes:

- `combined_runs.jsonl`: `fe5470e690fb9fd54868fb094e5f45806313180f2846a1e1b1f56e01ce1a3e99`
- `summary.json`: `a968c18f31e89a6132dd101d983790df5ab955aa81811b1b857e7d8d771cc663`
- `recovery_meta.json`: `7b41407b8831bba0c42c379b3a2fecef77e23e58cb232fd1f30c23618a3361b9`
- `runtime_environment.txt`: `5859317635f3aeb66e37c693c919209497201bd71c549280d13b3d35956e9ba9`

## 2. Recovery integrity audit

The independently downloaded original source artifact reproduced the frozen source ZIP digest exactly. Its five-record `runs.jsonl` reproduced the frozen SHA-256 exactly.

The recovered dataset contains exactly 96 unique `(case_id, condition)` records:

- 24 fresh v0.2 cases;
- 6 cases per family;
- 4 conditions per case;
- 24 records per condition.

Recovery preservation is exact:

- source records 1–4 are byte-for-byte identical to records 1–4 of `combined_runs.jsonl`;
- no source cell was regenerated;
- source record 5, `PCB2-AD01 / MATCHED_SCAFFOLD`, is the only mechanically reclassified source row;
- its observed error remains exactly `BudgetExceeded: MATCHED_SCAFFOLD__ABDUCTIVE_DIAGNOSTIC: environment-action budget exhausted`;
- its status changes from `technical_incomplete` to `execution_failure`;
- its effective score becomes `0.0`;
- `actions_used` is set to the frozen abductive scaffold budget of `3`;
- unavailable provider-call records, trace, and exact transition count remain unavailable rather than reconstructed;
- `cost_logging_complete=false` marks that one descriptive-usage gap.

Recovery 1 executed exactly the remaining 91 cells. `recovery_meta.json` reports 4 preserved complete source records, 1 mechanically reclassified source record, 91 new cells, 0 regenerated source cells, and 96 total records.

## 3. Transport and execution audit

The recovered run contains 403 logged provider calls. Every logged call has `finish_reason=stop`.

- no logged completion ended with `finish_reason=length`;
- no logged call reached the 16,384-token ceiling;
- maximum observed logged output-token count was 8,832;
- the only zero-call record is the known reclassified source cell whose original call log was lost by the frozen runner defect.

Execution balancing also remained intact. Globally, each of the four conditions occupied each condition-execution position exactly six times. Within each family, every condition occupied every position either once or twice across the six cases, as prospectively designed. Case-position and condition-order metadata are internally consistent across all four records for each case.

There are no catastrophic failures in any condition.

## 4. Independent recomputation of the frozen family gates

The frozen family gate is:

1. mean `SPECIALIST - MATCHED_SCAFFOLD` >= `+0.10`;
2. specialist strictly beats matched scaffold on at least 4/6 cases;
3. specialist reaches valid terminal execution on at least 5/6 cases;
4. specialist catastrophic failures do not exceed matched scaffold;
5. comparison access remains valid.

Independent recomputation from `combined_runs.jsonl` exactly reproduces `summary.json`:

| Family | Specialist mean | Matched mean | Process effect | Strict wins | Valid specialist | Eligible |
|---|---:|---:|---:|---:|---:|---|
| DEDUCTIVE_CONSTRAINT | 1.0000 | 1.0000 | 0.0000 | 0/6 | 6/6 | No |
| ABDUCTIVE_DIAGNOSTIC | 0.3333 | 0.1667 | +0.1667 | 1/6 | 6/6 | No |
| SEARCH_PLANNING | 1.0000 | 0.8333 | +0.1667 | 1/6 | 6/6 | No |
| DECISION_THEORETIC | 1.0000 | 1.0000 | 0.0000 | 0/6 | 6/6 | No |

Eligible families: `[]`.

Therefore the frozen program decision is reproduced exactly:

`STOP_PROCESS_CONSTRAINED_SELECTOR_PATH`

No threshold, gate, or interpretation was changed after observing results.

## 5. Case-level primary contrast

The 24 specialist-minus-matched case lifts are almost entirely ties.

- `DEDUCTIVE_CONSTRAINT`: six ties.
- `ABDUCTIVE_DIAGNOSTIC`: one specialist win (`PCB2-AD01`, +1.0) and five ties.
- `SEARCH_PLANNING`: one specialist win (`PCB2-SP03`, +1.0) and five ties.
- `DECISION_THEORETIC`: six ties.

Across all cases there are exactly two strict specialist wins and zero matched-scaffold wins.

Both strict wins arise because the matched scaffold failed to complete successfully on that case while the specialist did:

- `PCB2-AD01`: matched scaffold exhausted its environment-action budget; specialist achieved score 1.0.
- `PCB2-SP03`: matched scaffold rolled back an unhealthy migration but exhausted its generic process before issuing the final abort, leaving the environment incomplete; specialist achieved score 1.0.

For every case where both specialist and matched scaffold completed successfully, their objective normalized scores are equal. This is a useful diagnostic: the study observed isolated process-discipline advantages, but not a persistent within-family objective-outcome advantage sufficient for selector development.

## 6. Execution-failure diagnostics

Condition-level execution failures:

- `SPECIALIST`: 0/24;
- `MATCHED_SCAFFOLD`: 3/24;
- `FULL`: 1/24;
- `CONTROL`: 0/24.

Matched-scaffold failures:

- `PCB2-AD01`: action-budget exhaustion, mechanically reclassified by Recovery 1;
- `PCB2-AD05`: action-budget exhaustion under the reviewed recovery handler;
- `PCB2-SP03`: protocol/environment did not both reach a valid terminal state.

FULL failure:

- `PCB2-AD01`: environment-action budget exhausted.

All 24 specialist executions reached valid terminal execution, and no specialist catastrophic failure occurred. Thus the specialist protocols were executable under the corrected public action contracts; the Phase-B failure is not a repeat of the v0.1 hidden-contract defect.

## 7. Ceiling and task-discrimination audit

The objective score is binary in the observed dataset: 78/96 records score `1.0`, 18/96 score `0.0`.

Family-level ceiling rates across all four conditions are:

- `DEDUCTIVE_CONSTRAINT`: 24/24 = 100%;
- `ABDUCTIVE_DIAGNOSTIC`: 7/24 = 29.2%;
- `SEARCH_PLANNING`: 23/24 = 95.8%;
- `DECISION_THEORETIC`: 24/24 = 100%.

This matters for interpretation. In deductive and decision-theoretic tasks, all four policies solved every case. Search/planning was also almost fully saturated. Those three families therefore provide little room for an enforced specialist process to demonstrate objective superiority over the matched scaffold, FULL, or CONTROL.

The abductive family was not ceiling-saturated, but specialist, FULL, and CONTROL each averaged only 0.3333 and the specialist beat the matched scaffold on only one of six cases. The process did not produce the persistent advantage required by the frozen gate.

This pattern matches two prospectively identified Phase-B stop concerns in `ADAPTIVE_REASONING_CONTROLLER_V0_2_PLAN.md`: specialist effects largely disappear against the matched scaffold, and several environment families determine the answer strongly enough that reasoning policy has little measurable headroom.

## 8. Contextual FULL and CONTROL results

Contextual fixed-policy means by family:

| Family | FULL | CONTROL |
|---|---:|---:|
| DEDUCTIVE_CONSTRAINT | 1.0000 | 1.0000 |
| ABDUCTIVE_DIAGNOSTIC | 0.3333 | 0.3333 |
| SEARCH_PLANNING | 1.0000 | 1.0000 |
| DECISION_THEORETIC | 1.0000 | 1.0000 |

These are development-environment outcomes, not replacements for the earlier blinded natural-language quality evidence. The synthetic Phase-B environments are specifically designed for objective process experiments and should not be used to infer that FULL and CONTROL are generally equivalent on non-trivial reasoning tasks.

## 9. Descriptive usage

Usage is descriptive only and is not part of the frozen eligibility gate.

Descriptive condition metrics are:

| Condition | Model calls | Input tokens | Output tokens | Environment actions | Execution failure rate |
|---|---:|---:|---:|---:|---:|
| SPECIALIST | 5.458 | 5300.2 | 6105.5 | 3.458 | 0.0% |
| MATCHED_SCAFFOLD | 5.391 | 4164.3 | 3119.7 | 3.083 | 12.5% |
| FULL | 3.208 | 3052.6 | 2723.0 | 3.167 | 4.2% |
| CONTROL | 2.958 | 1977.3 | 1964.1 | 2.958 | 0.0% |

For `MATCHED_SCAFFOLD`, model-call/token/latency means cover the 23/24 records with complete cost logs; environment-action and execution-failure statistics still cover all 24 records. The original `PCB2-AD01` call log was lost, but its execution-failure classification and primary score remain included.

The specialist process consumed substantially more model output than the matched scaffold and fixed-policy comparators while failing to meet any family eligibility gate. No cost-optimality claim is warranted from this development study.

## 10. Scientific interpretation

The corrected v0.2 study answers a narrower question than the original FULL-vs-CONTROL quality program.

Supported by this experiment:

- the corrected specialist protocols completed valid terminal executions on all 24 specialist cells under explicit state/action contracts on `glm-5.1`;
- on two development cases, the specialist condition completed successfully where the matched scaffold did not;
- none of the four tested families showed the persistent specialist-over-matched advantage required for Phase-C selector development;
- the frozen selector-path stop rule therefore triggers.

Not supported:

- that externally constrained reasoning processes are universally useless;
- that the four reasoning families are not meaningful analytic descriptions;
- that FULL and CONTROL are generally equivalent outside these synthetic objective environments;
- that another target model would show the same pattern;
- that more difficult or externally sourced environments could not reveal process effects;
- that hidden cognition has been measured or decomposed.

The strongest interpretation is methodological: once extra structure/computation was controlled by a matched scaffold, the tested specialist processes did not produce sufficiently frequent task-conditional objective gains on this development suite, and three of four environment families were substantially ceiling-limited.

## 11. Program consequence

Under the prospectively frozen rules, **Phase C is not authorized**. No autonomous selector should be derived from these data, and the same process-constrained selector path should not be continued by tuning thresholds, prompts, state machines, or case parameters against these exposed results.

The supported deployment architecture remains unchanged:

`DIRECT for genuinely trivial/deterministic tasks; otherwise frozen FULL`.

Any future reopening of adaptive reasoning control requires materially new information or a materially different research object, such as harder/external objective environments, cross-target replication, or an independently motivated control mechanism. Such work would be a new research generation, not Phase C of this frozen program.
