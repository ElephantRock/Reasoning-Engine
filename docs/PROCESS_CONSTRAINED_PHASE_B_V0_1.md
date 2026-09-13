# Process-Constrained ARC Phase B v0.1 — Process-Effect Development Study

Status: **design freeze candidate; no paid run is authorized until the implementation/static-review PR passes and frozen blob identities are recorded below**.

This study follows the Phase-A environment review and does not reopen prompt-only operator fidelity. Its purpose is to test whether externally enforced reasoning protocols change **objective task outcomes** beyond a generic matched process scaffold.

## 1. Scientific question

For each of four initial reasoning-protocol families, under matched environment affordances and action budgets:

> Does the specialist process improve objective outcome/error/action profiles relative to a generic structured scaffold with comparable computation opportunity?

The four families are:

- `DEDUCTIVE_CONSTRAINT`
- `ABDUCTIVE_DIAGNOSTIC`
- `SEARCH_PLANNING`
- `DECISION_THEORETIC`

This is a development study. It does not establish a general reasoning taxonomy, hidden-cognition fidelity, cross-model generalization, or a validated autonomous selector.

## 2. Fresh development suite

Use the frozen `process_phase_b_cases_v01.json` suite:

- 24 cases total;
- 6 cases per family;
- no Operator Fidelity v0.1/v0.2 probe is reused;
- tasks are synthetic and objectively scored by environment ground truth;
- family labels and hidden parameters are not shown to the target model.

Environment hardening requirements are those in `PROCESS_CONSTRAINED_PHASE_A_REVIEW_V0_1.md` and must be verified by static tests before execution.

## 3. Conditions

Each case is run under exactly four conditions:

1. `SPECIALIST` — the case family's externally enforced protocol;
2. `MATCHED_SCAFFOLD` — generic stateful structure with the specialist's maximum transition budget and identical environment-action budget, but without specialist semantic/action-timing constraints;
3. `FULL` — the frozen eight-stage FULL system prompt operating as an unconstrained interactive agent with the same environment action universe and maximum action budget;
4. `CONTROL` — no reasoning-specific system prompt, also operating with the same environment action universe and maximum action budget.

Phase B intentionally does **not** run every specialist on every task. The full policy × task crossing belongs to Phase C and is authorized only if Phase B identifies at least two specialist process effects beyond their matched scaffolds.

## 4. Fairness and information access

For a given case, all four conditions receive:

- identical user-visible task text;
- identical environment action names/descriptions;
- identical environment responses for the same action/history;
- identical environment action budget;
- no direct access to hidden environment parameters or gold scores.

`SPECIALIST` and `MATCHED_SCAFFOLD` use the same maximum model-turn budget. `FULL` and `CONTROL` receive that same maximum model-turn budget for the case family and may terminate early.

Every model call, invalid request, environment action, token count, and latency is recorded. Failed environment actions consume budget.

No condition receives an extra evidence query because of its label.

## 5. Interactive target protocol

Target model: `glm-5.1`.

Target configuration:

- temperature `0`;
- one generation per `(case, condition)`;
- structured JSON action/state responses;
- concise public protocol-state content only; do not request hidden chain-of-thought;
- per-call completion ceiling should be small enough to prevent uncontrolled deliberation and must be frozen in the runner PR before execution.

At each turn the agent receives the task, observations revealed so far, action catalog, remaining environment-action budget, and condition-specific control state.

For `SPECIALIST`, the runtime supplies only legal next protocol states and enforces payload/action-tag contracts.

For `MATCHED_SCAFFOLD`, the runtime enforces the matched generic turn structure and budget but no specialist semantic contract.

For `FULL` and `CONTROL`, the harness exposes the same action API and budget without specialist state constraints.

A formatting-only JSON/schema failure may receive at most one repair attempt. The repair attempt counts toward model-call/token cost but does not silently alter environment state. A second invalid response terminates that case-condition as an execution failure.

## 6. Primary objective endpoint

Every environment returns `normalized_score` in `[0,1]`, computed only from environment state/ground truth.

For each family `f`:

`process_effect_f = mean(normalized_score_SPECIALIST - normalized_score_MATCHED_SCAFFOLD)`

across its six frozen cases.

The matched-scaffold contrast is the primary causal development contrast. `FULL` and `CONTROL` are contextual fixed-policy comparators, not substitutes for the matched scaffold.

## 7. Secondary endpoints

Record and report, by family and condition:

- correct terminal decision rate;
- execution/protocol failure rate;
- environment-action count;
- failed/illegal action count;
- family-specific constraint violations or unsupported commitments;
- information-query count and unnecessary-query count where defined;
- realized utility/regret for decision tasks;
- token usage and latency;
- score relative to frozen FULL and CONTROL.

Do not combine incomparable family-specific raw metrics into one pooled pseudo-scale; only `normalized_score` is common by construction.

## 8. Frozen family eligibility gate

A family is Phase-C eligible only if all conditions hold:

1. mean specialist-minus-matched-scaffold `normalized_score` lift is at least `+0.10`;
2. the specialist strictly beats the matched scaffold on at least 4 of the 6 cases;
3. the specialist completes a valid terminal execution on at least 5 of 6 cases;
4. the specialist does not have more catastrophic/irreversible constraint failures than the matched scaffold;
5. any apparent lift is not produced solely by greater environment-action access or a larger action budget (which would invalidate the comparison rather than count as success).

`FULL` is not an eligibility gate in Phase B: a specialist may establish a process effect while still being worse than FULL overall. That distinction is important because Phase B asks whether the protocol structure has causal value beyond generic structure, not yet whether it should replace the generalist.

## 9. Program decision

- 2–4 eligible families: proceed to design Phase C around the frozen eligible subset;
- exactly 1 eligible family: do not build an adaptive selector; treat the result as evidence for one potentially useful specialist architecture and reassess the research question;
- 0 eligible families: stop the current process-constrained selector path on this target/environment generation.

Phase C is not automatically authorized by the Phase-B outcome; its full factorial suite and oracle-selection thresholds require a separate frozen design.

## 10. Anti-triviality stop rules

Stop before paid execution if static review finds any of the following:

- an environment response directly exposes hidden state, gold answer, exact optimum, or oracle action;
- one diagnostic evidence check can uniquely identify a cause by itself;
- all planning cases have the same optimal terminal branch;
- all decision cases have the same optimal initial information policy;
- specialist and matched-scaffold action budgets differ;
- specialist-only evidence/actions exist;
- objective score code reads the experimental condition label;
- the runner imports or reuses the exposed Operator Fidelity judgment data to choose behavior.

Stop the run before interpretation if implementation drift changes any frozen case, environment, protocol, score, condition, or gate after target generation begins.

## 11. Judge policy

No LLM judge is required for the primary or eligibility endpoints.

A later optional blinded answer-quality judge may be added only as a secondary descriptive diagnostic in a separately frozen analysis. It cannot change Phase-B eligibility.

## 12. Frozen artifacts

Before any paid run, record exact Git blob identities for:

- `benchmark/process_phase_b_cases_v01.json`;
- `benchmark/protocol_environments_v03.py`;
- `benchmark/protocol_runtime_v03.py`;
- the Phase-B runner and interactive prompts;
- the frozen FULL prompt source.

Artifact outputs must include every target call, public state transition, environment observation, invalid request, usage record, final environment score, and a SHA-256 manifest.

## 13. Current authorization boundary

This document authorizes only implementation, static testing, and review of the Phase-B runner. **No paid/model execution is authorized until a follow-up review confirms the anti-triviality gates, records all frozen blob identities, and explicitly marks the experiment executable.**
