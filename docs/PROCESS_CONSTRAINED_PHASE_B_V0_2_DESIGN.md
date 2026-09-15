# Process-Constrained ARC Phase B v0.2 — Corrected Development Design

Status: **zero-cost correction/design only. No paid/model execution is authorized by this document or branch.**

Phase B v0.2 is a new experiment version motivated by the mandatory post-run audit of Phase B v0.1. It does not rerun, repair in place, or reinterpret the consumed v0.1 workflow. The v0.1 raw artifact and nominal frozen-rule result remain historical facts; v0.2 changes the measurement interface and therefore requires a fresh full comparison.

## 1. Trigger and correction target

The v0.1 post-run audit found two upstream validity defects before scientific interpretation:

1. the specialist runtime enforced state-specific negative/no-action timing rules that were not completely surfaced as target-visible allowed/forbidden action metadata; nine of ten specialist execution failures occurred on such no-action states, including all six decision-theoretic specialists on the first transition;
2. the deductive `restart_minute` endpoint was behaviorally ambiguous between restart start time and restart completion/service-restoration time.

v0.2 changes only what is necessary to make those measurement contracts explicit and testable. It does not treat the v0.1 nominal `STOP_PROCESS_CONSTRAINED_SELECTOR_PATH` output as evidence that the underlying specialist reasoning operators lack value.

## 2. Scientific question

For each of the same four initial process families, under matched environment affordances and action budgets:

> Does the externally enforced specialist process improve objective outcome/error/action profiles relative to a generic matched process scaffold when the complete operational action contract is explicitly visible to the target?

Families remain:

- `DEDUCTIVE_CONSTRAINT`;
- `ABDUCTIVE_DIAGNOSTIC`;
- `SEARCH_PLANNING`;
- `DECISION_THEORETIC`.

This is still a development study. It does not establish a universal reasoning taxonomy, hidden-cognition fidelity, cross-model generalization, or a validated autonomous selector.

## 3. Fresh development suite

Use `benchmark/process_phase_b_cases_v02.json`:

- 24 cases total;
- 6 cases per family;
- all case IDs are new `PCB2-*` identifiers;
- no exact v0.1 parameter cell is reused;
- deductive and decision-theoretic numerical parameters are fresh;
- diagnostic and planning cases use fresh public scenario surfaces and a changed hidden-case allocation while preserving their already-hardened causal mechanics;
- tasks remain synthetic and objectively scored by environment ground truth;
- internal case IDs, family labels, experimental condition labels, and hidden parameters are not shown to the target.

Because diagnostic/planning v0.2 retain the same environment family mechanics as v0.1, this is a **fresh corrected development suite**, not independent external-environment validation.

## 4. Conditions and primary contrast

Every case in the eventual paid study must again be executed under all four conditions:

1. `SPECIALIST` — the case family's externally enforced protocol with the corrected complete target-visible action contract;
2. `MATCHED_SCAFFOLD` — generic structured process with the same maximum transition range and identical environment-action budget, but no specialist semantic/action-timing constraints;
3. `FULL` — the frozen eight-stage FULL system prompt, using the same environment action universe and family action budget;
4. `CONTROL` — no reasoning-specific system prompt, using the same environment action universe and family action budget.

Primary causal development contrast remains:

`SPECIALIST - MATCHED_SCAFFOLD`

`FULL` and `CONTROL` remain contextual fixed-policy comparators. No LLM judge determines the primary endpoint or eligibility decision.

The v0.1 comparator outputs must **not** be reused as primary v0.2 controls. Correcting the specialist interface changes the intervention and requires a newly balanced contemporaneous four-condition crossing.

## 5. Corrected specialist interface contract

The runtime is still allowed to constrain when environment actions may occur. That timing is part of the specialist process intervention. The correction is that the target must now be told the exact operational rule it is scored against.

For every legal next state, the model-visible `next_state_contracts` entry must contain both:

- `payload_contract` — public semantic content required for the state;
- `action_contract` — mechanically derived from the same `TransitionRule` and environment action tags used by enforcement.

Every `action_contract` must expose:

- `environment_action_mode`: exactly one of `required`, `optional`, or `forbidden`;
- `environment_action_required`: boolean;
- `environment_action_must_be_null`: boolean;
- `allowed_action_tags`: exact allowed runtime tags;
- `allowed_action_names`: exact currently available action names satisfying those tags.

If a state permits no environment action, the contract must explicitly state:

- `environment_action_mode = forbidden`;
- `environment_action_must_be_null = true`;
- `allowed_action_names = []`.

The contract must be generated mechanically from the enforcement rule, not maintained as a second hand-written copy. Zero-cost tests must prove exact interface/enforcement equivalence for every specialist state before any paid runner is authorized.

## 6. Corrected deductive endpoint

The deductive environment uses one unambiguous terminal observable:

`service_restored_minute`

The public task must explicitly state all of the following:

- isolation occurs before calibration/verification;
- restart may begin only after calibration and verification are complete;
- the terminal commitment is the minute when restart has **finished** and service is restored;
- this is **not** the minute when restart begins.

The environment actions are renamed accordingly:

- `inspect_constraints`;
- `test_candidate(service_restored_minute=...)`;
- `commit_restoration(service_restored_minute=...)`.

The scorer rewards the earliest feasible service-restoration minute. Static tests must demonstrate that the earliest restart-start minute fails the restoration candidate test whenever restart duration is positive, while the exact restoration minute receives full credit.

## 7. Fairness and information access

For a given case, all eventual conditions must receive identical:

- user-visible task text;
- common environment action names/descriptions;
- environment responses for the same action/history;
- environment action budget;
- no direct access to hidden environment parameters or gold scores.

The specialist's action-timing restrictions may reduce when an action is legal, but those restrictions must be fully disclosed by its public action contract. `MATCHED_SCAFFOLD` retains generic `ANY` action timing subject to environment prerequisites and the same action budget; this remains the planned causal contrast between task-specific process structure and generic structured computation.

Failed environment actions consume budget. Semantic/runtime-invalid requests receive no hidden reasoning retry. Formatting/JSON-schema repair remains limited to one schema-only retry before environment mutation.

## 8. Objective endpoint and frozen family gate

The primary outcome remains environment-derived `effective_normalized_score` in `[0,1]`:

- valid execution: environment `normalized_score`;
- protocol/semantic/format execution failure: `0`;
- technical/provider interruption: unscored and stops aggregation pending a separately frozen recovery.

For each family `f`:

`process_effect_f = mean(SPECIALIST - MATCHED_SCAFFOLD)`

across its six fresh cases.

The v0.2 family eligibility gate remains unchanged from v0.1 to avoid outcome-contingent threshold revision. A family is eligible for Phase-C design only if all hold:

1. mean specialist-minus-matched lift >= `+0.10`;
2. specialist strictly beats matched scaffold on at least 4/6 cases;
3. specialist reaches a valid terminal execution on at least 5/6 cases;
4. specialist catastrophic/irreversible failures do not exceed matched scaffold;
5. the comparison is not invalidated by unequal action or information access.

Program rule remains:

- 2–4 eligible families -> `DESIGN_PHASE_C_ELIGIBLE_SUBSET`;
- exactly 1 eligible family -> `ONE_SPECIALIST_NO_SELECTOR`;
- 0 eligible families -> `STOP_PROCESS_CONSTRAINED_SELECTOR_PATH`.

A scientifically valid v0.2 result is required before any Phase-C design can be reopened.

## 9. Zero-cost gates before executable work

The correction branch must pass static tests showing at minimum:

- 24 unique fresh cases, six per family;
- no exact v0.1 case/parameter-cell reuse;
- diagnostic single-check outcomes remain non-unique over candidate causes;
- planning contains both healthy/finalize and unhealthy/rollback-abort cases;
- decision tasks contain pilot, buy-now, and decline-now optimal initial policies;
- deductive endpoint language and action schema explicitly denote service restoration;
- restart start time is not accepted as the restoration endpoint;
- every specialist state exposes an exact action contract mechanically equivalent to runtime enforcement;
- formerly implicit no-action states explicitly require `environment_action = null`;
- target-visible request builders exclude case IDs, family labels, and experimental condition labels.

Failure of any gate blocks executable/paid authorization.

## 10. Planned execution configuration — not yet authorized

For comparability with v0.1, the intended later executable freeze is:

- target model: `glm-5.1`;
- provider base URL: `https://api.z.ai/api/coding/paas/v4`;
- temperature: `0`;
- one execution per `(case, condition)`;
- 24 × 4 = 96 case-condition executions;
- completion-token ceiling: `16384`;
- family-interleaved case order;
- prospectively family-balanced condition order;
- exact dependency/provider adapter/runtime freeze before the first target call.

These are design intentions only. They do not authorize provider spend.

## 11. Authorization boundary

This branch may implement and test the corrected suite, environment semantics, public interface, and zero-cost validators. It must not add or dispatch a paid Phase-B v0.2 workflow.

Before any model execution, a later executable-freeze change must separately:

1. implement the full four-condition v0.2 runner;
2. re-review blinding, execution order, logging, interruption/recovery behavior, and aggregation;
3. record exact scientific-source Git identities;
4. freeze provider adapter and dependency/runtime surface;
5. add a new manual one-shot workflow whose authorization cannot be consumed by v0.1 history;
6. receive a separate review and explicit execution authorization.

The consumed Phase-B v0.1 workflow must never be rerun as a substitute for v0.2.