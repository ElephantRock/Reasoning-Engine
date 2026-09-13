# Adaptive Reasoning Controller v0.2 — Process-Constrained Research Plan

Status: **research design only; no paid experiment authorized by this document**.

This document starts a new research generation after Operator Fidelity v0.2. It does not reopen the failed prompt-only Stage-0 program and does not modify the current deployment decision.

Current supported deployment remains:

- `DIRECT` for genuinely trivial/deterministic tasks;
- frozen `FULL` for non-trivial reasoning tasks.

## 1. Trigger for the redesign

Operator Fidelity v0.1 and v0.2 both failed to identify the six candidate specialist prompts as behaviorally separable interventions on `glm-5.1`.

The v0.2 audit is decisive for the prompt-only identification strategy:

- 0/6 specialists passed the frozen Stage-1 gate;
- 89/96 independently scored response composites were exactly `1.0`;
- all 96 were at least `0.9`;
- all six matching specialists averaged `1.0` fidelity;
- all six nonmatching-specialist medians also averaged `1.0`.

Therefore another prompt rewrite plus another independent behavior rubric would violate the frozen stop rule. The six reasoning families remain useful analytic labels, but they are not currently established as causally distinct promptable modules.

The next program must change the **operational definition of an operator**, not merely the wording of its system prompt.

## 2. New scientific question

The new question is:

> Can reasoning policies become empirically distinguishable and task-conditionally useful when they are implemented as externally constrained inference processes with observable state transitions, rather than as prompt-only behavioral suggestions?

The target claim is about **reasoning-control protocols**, not hidden cognition.

A successful result would show that an external controller can constrain the model to materially different inference processes, that those processes have different task-conditional outcome profiles, and that a prospective selector can exploit those differences on fresh cases.

## 3. Core architectural change

v0.1 treated an operator approximately as:

`task + specialist system prompt -> answer`

v0.2 instead defines an operator as:

`task -> enforced protocol state machine -> validated transitions -> answer`

The candidate architecture is:

`Task -> Characterize -> Select protocol -> Execute constrained transitions -> Verify state -> Produce answer -> Evaluate outcome`

The controller is external to the model. The model proposes the content of each transition, but the runtime determines which transition types are legal, what state is carried forward, what information is available, and when the process may terminate.

This changes the intervention from "please reason in mode X" to "the model must operate through process X."

## 4. Operator protocol registry

The six prior families are retained as hypotheses, but each receives an explicit process contract.

### DEDUCTIVE_CONSTRAINT

State machine:

`PREMISES -> CONSTRAINTS -> DERIVATION -> BOUNDARY_CHECK -> CONCLUSION`

Required transition semantics:

- premises and hard constraints are represented explicitly;
- a conclusion must cite the constraints that entail or block it;
- at least one boundary, counterexample, or hidden-assumption check precedes commitment;
- an infeasible target may terminate only with the binding constraint and a sufficient relaxation.

### ABDUCTIVE_DIAGNOSTIC

State machine:

`OBSERVATIONS -> HYPOTHESES -> PREDICTIONS -> DISCRIMINATING_CHECK -> UPDATE -> RANKING`

Required transition semantics:

- at least two live hypotheses are represented before discrimination;
- each leading hypothesis has an expected observation or mechanism-linked prediction;
- the next check must distinguish alternatives rather than merely confirm the current favorite;
- ranking is updated only after evidence or an explicit no-new-evidence termination.

### CAUSAL_EXPERIMENTAL

State machine:

`ESTIMAND -> RIVAL_CAUSES -> IDENTIFICATION_PLAN -> CONTRAST_PREDICTIONS -> EVIDENCE -> CAUSAL_BOUND`

Required transition semantics:

- the causal estimand/counterfactual is explicit;
- material confounding or rival paths are represented;
- the identification action must be capable of changing the causal conclusion;
- predicted observations under rival causal accounts are declared before evidence is consumed;
- the terminal state states what the evidence identifies and what remains unidentified.

### SEARCH_PLANNING

State machine:

`STATE -> ACTIONS -> CANDIDATE_PATHS -> CONSTRAINT_CHECK -> BRANCH_OR_COMMIT -> CHECKPOINT -> RECOVERY_OR_FINISH`

Required transition semantics:

- legal actions, prerequisites, irreversible actions, and hard constraints are explicit;
- at least two materially different paths or branches are considered before commitment when more than one feasible path exists;
- checkpoint observations determine continuation, branching, rollback, or replanning;
- irreversible actions cannot occur before their preconditions are satisfied.

### DECISION_THEORETIC

State machine:

`ACTIONS -> OUTCOMES -> UNCERTAINTY -> ASYMMETRIC_VALUE -> INFORMATION_VALUE -> DECISION -> REVERSAL_CONDITION`

Required transition semantics:

- feasible actions and materially different consequences are explicit;
- uncertainty that affects the decision is represented rather than collapsed to one forecast;
- downside, opportunity cost, reversibility, or option value must enter the comparison when material;
- information acquisition must be compared against acting now;
- the final decision includes a condition under which it would change.

### SYSTEMS_FEEDBACK

State machine:

`VARIABLES -> LINKS -> FEEDBACK_LOOPS -> DELAYS_CAPACITY -> INTERVENTION_DYNAMICS -> MONITORING -> REVISION`

Required transition semantics:

- state variables/capacities and directional links are explicit;
- at least one supported endogenous response or feedback loop is represented when present;
- delays, accumulation, adaptation, or bottleneck migration are modeled when material;
- intervention choice and monitoring are tied to the predicted dynamics;
- contradictory observations force model revision rather than preservation of the initial intervention story.

These contracts are operational definitions for experiments. They are not claims that human or neural reasoning literally decomposes into these states.

## 5. Runtime enforcement

A protocol executor should maintain machine-readable state outside the model. At each step the model receives:

- the original task;
- the current protocol state;
- only the transition types legal from that state;
- any environment evidence made available so far.

The model returns a structured transition request. The runtime validates the schema and state transition before committing it.

Invalid transitions are rejected mechanically. Repeated invalid transitions terminate the run as a protocol failure rather than being silently repaired into compliance.

The runtime, not the model, controls transition order, termination eligibility, evidence release, and branch/rollback legality.

## 6. Why observable action traces are required

The prompt-only studies saturated because a capable model could display most requested behaviors under almost every condition. A process-constrained environment must therefore make operator differences observable in the **sequence of legal actions and state changes**, not only in final prose.

For example, a diagnostic environment can hide evidence behind selectable checks. The abductive protocol must choose a discriminating check from competing hypotheses before it may commit to a diagnosis. A planning environment can expose state changes and irreversible actions; a planning protocol must preserve rollback or satisfy prerequisites before the runtime permits an irreversible transition.

This makes process compliance mechanically measurable.

## 7. Objective evaluation priority

Where possible, evaluation should be environment-based rather than LLM-judge-based.

Primary metrics should include quantities such as:

- correct terminal decision or answer;
- constraint violations;
- unnecessary or dominated information-gathering actions;
- number/cost of environment actions;
- irreversible-action failures;
- recovery success after perturbation;
- regret or realized utility where the environment defines outcomes;
- causal-estimand error where synthetic ground truth is available.

A model judge may still be used for secondary answer-quality diagnostics, but it should not be the only arbiter of whether an operator executed its protocol or succeeded.

## 8. Development sequence

### Phase A — deterministic environment prototypes

Build small synthetic/semisynthetic environments whose hidden state and scoring rules are known to the harness.

Start with four maximally separable protocol families:

- `DEDUCTIVE_CONSTRAINT`;
- `ABDUCTIVE_DIAGNOSTIC`;
- `SEARCH_PLANNING`;
- `DECISION_THEORETIC`.

Hold `CAUSAL_EXPERIMENTAL` and `SYSTEMS_FEEDBACK` out of the first prototype until their environments expose genuinely discriminating interventions/dynamics rather than merely different prose schemas.

No model comparison claim is made in Phase A. The goal is to verify that the runtime can enforce distinct legal traces and score them objectively.

### Phase B — process-identification development study

Use fresh development tasks. Run each task under every implemented protocol plus `FULL` and `CONTROL` where feasible.

Primary question:

`Does the enforced protocol create mechanically distinguishable traces and different error/action profiles?`

This phase does not require an LLM judge to decide operator identity: identity is defined by the runtime contract and verified from the trace.

Stop if the protocols collapse to functionally equivalent action traces or if environment design itself determines the answer so strongly that reasoning policy cannot matter.

### Phase C — policy × task interaction study

Only after Phase B shows distinct execution profiles, author a fresh interaction suite.

Primary estimand:

`outcome_quality = f(task_structure, enforced_protocol)`

Compare:

- `CONTROL`;
- frozen `FULL`;
- each process-constrained protocol;
- an oracle-by-predeclared-task-label diagnostic.

The oracle is used only to estimate whether selection has enough upside to justify building a controller.

Do not train an autonomous selector unless the oracle materially exceeds the best fixed policy on objective/quality outcomes.

### Phase D — controller derivation and fresh validation

If Phase C establishes usable interaction structure, derive one controller from deployment-available task features and freeze it before a new validation suite is authored.

The controller may select:

- one protocol;
- a predeclared composition of a small number of protocols;
- frozen `FULL` as fallback for ambiguous, composite, or high-consequence tasks.

Fresh validation must compare the controller directly against frozen `FULL` on quality and cost. Stage-D data cannot be used to change the selector.

## 9. Composition is a separate hypothesis

Do not assume that selecting one operator is sufficient.

A later composition study may test sequences such as:

`ABDUCTIVE_DIAGNOSTIC -> CAUSAL_EXPERIMENTAL -> DECISION_THEORETIC`

or

`DEDUCTIVE_CONSTRAINT -> SEARCH_PLANNING -> SYSTEMS_FEEDBACK`.

Composition should not be introduced during the first process-identification study because it would confound operator identity with orchestration complexity.

## 10. Controls against false progress

The next program must preserve the following boundaries:

1. no reuse of v0.1/v0.2 fidelity probes as confirmatory cases;
2. no claim that trace states reveal hidden chain-of-thought or neural mechanisms;
3. no operator is declared useful merely because the runtime forces its schema;
4. process compliance and outcome quality are separate endpoints;
5. task-family labels must not trivially encode the selected protocol in controller validation;
6. objective metrics are preferred where the environment supports them;
7. target/model-family generalization remains unresolved until another family becomes available;
8. no paid Phase-B/C/D run occurs until its cases, scoring, stop rules, and artifacts are frozen.

## 11. Immediate engineering milestone

The next authorized work is **zero-cost engineering and review only**:

1. implement a generic protocol-state runtime with transition validation and trace logging;
2. implement deterministic toy environments for the four Phase-A protocols;
3. implement objective scorers and static tests;
4. demonstrate locally that legal/illegal traces, rollback, evidence release, and termination rules work as specified;
5. review the environment for answer leakage and protocol-induced triviality;
6. only then write a separate frozen Phase-B experiment specification.

No API/model call is authorized by this plan.

## 12. Current decision

The prompt-only Adaptive Reasoning Controller v0.1 research path is closed by the v0.2 saturation stop rule.

The active research hypothesis becomes:

> Adaptive reasoning control may require operators to be implemented as externally enforced processes with observable state/action semantics, rather than as natural-language prompt variants whose behaviors are already latent in a capable model.

This is a new hypothesis and requires new evidence.