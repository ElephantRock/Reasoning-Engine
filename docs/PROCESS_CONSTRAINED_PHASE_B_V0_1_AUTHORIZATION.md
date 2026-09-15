# Process-Constrained ARC Phase B v0.1 — Execution Authorization

Status: **authorized for one manual paid development run after this freeze is merged to `main` and all required CI checks pass**.

This document authorizes execution of the already frozen Phase-B v0.1 development study. It does not authorize changes to the task suite, protocol definitions, objective scoring, conditions, eligibility gates, or program decision after target execution begins.

## Scientific scope

Phase B asks whether externally enforced reasoning protocols produce objective task-outcome improvements beyond a generic matched scaffold under matched action budgets.

Primary contrast:

`SPECIALIST - MATCHED_SCAFFOLD`

The four frozen families are:

- `DEDUCTIVE_CONSTRAINT`
- `ABDUCTIVE_DIAGNOSTIC`
- `SEARCH_PLANNING`
- `DECISION_THEORETIC`

`FULL` and `CONTROL` remain contextual fixed-policy comparators. No LLM judge determines the primary endpoint.

## Review completed before authorization

The execution review verified or corrected the following:

1. Original Phase-A toy environments were not used as the paid suite because they contained answer leakage/triviality risks. The hardened v0.3 environments and 24 fresh cases are used instead.
2. Model-facing requests exclude internal case identifiers and experimental condition labels.
3. `SPECIALIST` and `MATCHED_SCAFFOLD` share the same environment action universe and frozen action/turn budgets; the matched scaffold does not receive specialist semantic/action-timing rules.
4. Failed environment actions consume budget and are recorded.
5. Formatting repair is limited to one schema-only retry before environment mutation; semantic/runtime-invalid requests do not receive a hidden reasoning retry.
6. Completion-cap/provider interruptions stop scientific aggregation and preserve partial call records for a separately frozen recovery if needed.
7. Family order is round-robin and condition order uses a four-position cyclic rotation so family/condition are not mechanically confounded with execution time.
8. The provider adapter and dependency surface are frozen. The paid workflow uses Python 3.12.14, OpenAI Python package 3.13.0 and the exact dependency lock in `benchmark/requirements_process_phase_b_v01.txt`.
9. The paid workflow is manual (`workflow_dispatch`) only, is job-gated to `refs/heads/main`, and checks out the exact frozen source commit `607113d8be11dfeebf3230a264aa846b1ed10817` rather than the dispatch-selected branch head. It verifies that exact checkout before frozen-artifact validation or any model call.
10. GitHub Actions used for checkout, Python setup and artifact upload are pinned by commit SHA, and checkout credentials are not persisted into the frozen source worktree.
11. The runtime environment and frozen source SHA are recorded into the resulting artifact for auditability.

## Frozen execution configuration

- target model: `glm-5.1`
- provider base URL: `https://api.z.ai/api/coding/paas/v4`
- temperature: `0`
- per-call completion ceiling: `16384`
- frozen source commit: `607113d8be11dfeebf3230a264aa846b1ed10817`
- one generation per `(case, condition)`
- 24 cases × 4 conditions = 96 case-condition executions
- primary outcome: environment-derived `normalized_score`
- no LLM judge in the eligibility decision

Exact scientific source identities are recorded and mechanically checked by `benchmark/process_phase_b_freeze_v01.json` and `benchmark/validate_process_phase_b_freeze_v01.py`. The paid workflow is an orchestration boundary reviewed separately: it may run only from `main` and must execute the exact frozen source commit above.

## Frozen family eligibility gate

A family is eligible for Phase-C design only if all frozen Phase-B conditions hold:

- mean `SPECIALIST - MATCHED_SCAFFOLD` normalized-score lift >= `+0.10`;
- specialist strictly beats matched scaffold on at least 4/6 cases;
- specialist reaches a valid terminal execution on at least 5/6 cases;
- specialist catastrophic/irreversible failures do not exceed matched scaffold;
- the comparison is not invalidated by unequal action or information access.

Program rule:

- 2–4 eligible families -> `DESIGN_PHASE_C_ELIGIBLE_SUBSET`;
- exactly 1 eligible family -> `ONE_SPECIALIST_NO_SELECTOR`;
- 0 eligible families -> `STOP_PROCESS_CONSTRAINED_SELECTOR_PATH`.

A Phase-B result never itself authorizes a paid Phase-C run. Phase C requires a separately frozen full-factorial design.

## Recovery boundary

If the authorized run is technically interrupted, preserve every completed record and artifact. Do not silently regenerate completed case-condition executions. Any recovery must identify the exact missing/incomplete keys and be frozen before new model calls.

## Authorization

After merge and successful CI, one manual execution of `.github/workflows/process-constrained-phase-b-v01-paid.yml` from the `main` branch is authorized. The workflow must execute frozen source commit `607113d8be11dfeebf3230a264aa846b1ed10817`; selecting any other dispatch branch must result in a skipped paid job. Scientific interpretation must wait for an independent raw-artifact audit that reproduces all family-level effects, gates and the program decision from `runs.jsonl` rather than trusting `summary.json` alone.
