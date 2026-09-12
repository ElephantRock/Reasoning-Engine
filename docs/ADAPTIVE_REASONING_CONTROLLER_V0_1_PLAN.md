# Adaptive Reasoning Controller v0.1 — Research Plan

Status: **research design; not yet preregistered**.

This document opens a new research line without changing the current deployment decision in `docs/CURRENT_ARCHITECTURE_DECISION_V1.md`.

The current supported architecture remains:

- `DIRECT` for genuinely trivial/deterministic tasks;
- frozen `FULL` for non-trivial reasoning tasks.

The purpose of this program is to test whether a task-conditional reasoning controller can outperform or match the frozen FULL policy by selecting or composing specialized reasoning operators according to problem structure.

## 1. Scientific question

The current framework established a framework-level benefit for the frozen scientific/engineering protocol:

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`.

The next question is not whether FULL is useful. It is:

> Does reasoning quality depend on an interaction between problem structure and reasoning architecture, and can that interaction support a prospectively valid adaptive controller?

The target claim is therefore an interaction claim, not a universal leaderboard claim.

Conceptually:

`quality = f(problem_structure, reasoning_policy)`

A successful program should show that:

1. specialized policies have reproducible task-conditional advantages;
2. the task representation needed to predict those advantages is available before response generation;
3. a controller derived from those relationships survives a fresh-suite test against fixed FULL;
4. any efficiency gain does not come at an unacceptable quality loss.

## 2. Critical distinction from Selective Routing v1–v4

The failed routing program attempted to predict the marginal value of `FULL` over `CONTROL` directly from the input:

`Delta(x) = Q_FULL(x) - Q_CONTROL(x)`.

That is an individual-treatment-effect prediction problem and proved difficult under frozen criteria.

This program tests a different hypothesis:

1. characterize the reasoning demands of the problem;
2. select among reasoning policies whose intended epistemic functions differ;
3. verify whether the selected policy is empirically appropriate.

This is **not** permission to reopen the old routing work or retune its exposed 144 cases. Those cases must not be used to fit the new controller.

## 3. Architecture under test

The long-term candidate architecture is:

`Task → Characterize → Infer reasoning demands → Select/compose operator(s) → Execute → Verify → Revise strategy → Act`.

The eight-stage FULL policy is treated as a frozen generalist comparator, not assumed to be either optimal or obsolete.

The candidate hierarchy is:

- **reasoning operator**: a bounded inference policy;
- **reasoning controller**: selects/composes operators and revises the strategy;
- **agent/runtime**: executes tools, state, memory, environment actions, and the selected reasoning plan.

This study concerns the first two layers only.

## 4. Initial policy set

The first interaction study should use a deliberately small, distinct operator set. Each policy must be frozen before benchmark generation.

### CONTROL

No reasoning-specific system prompt.

### FULL

Exact currently frozen FULL policy.

### DEDUCTIVE_CONSTRAINT

Purpose: derive necessary consequences from premises, invariants, constraints, and impossibility conditions.

Required behavior:

- identify premises and assumptions;
- distinguish necessary from merely plausible conclusions;
- derive constraints before proposing an answer;
- seek counterexamples to claimed necessity;
- avoid importing unsupported premises.

### ABDUCTIVE_DIAGNOSTIC

Purpose: infer and discriminate among competing explanations for observations.

Required behavior:

- separate observations from interpretations;
- generate multiple plausible explanations;
- identify evidence expected under each explanation;
- prefer discriminating evidence over confirmation;
- retain uncertainty when alternatives remain observationally equivalent.

### CAUSAL_EXPERIMENTAL

Purpose: reason about mechanisms, interventions, counterfactuals, and discriminating tests.

Required behavior:

- distinguish association from causation;
- propose competing causal mechanisms;
- derive intervention/counterfactual predictions;
- identify confounding and alternative causal paths;
- prefer falsifying or discriminating tests.

### SEARCH_PLANNING

Purpose: solve tasks requiring explicit exploration of states, action sequences, decompositions, or alternatives.

Required behavior:

- define state, goal, constraints, and legal actions;
- generate multiple candidate paths/plans;
- identify bottlenecks and dead ends;
- compare plans by feasibility and objective value;
- revise the plan when intermediate constraints fail.

### DECISION_THEORETIC

Purpose: choose among actions under uncertainty and asymmetric consequences.

Required behavior:

- enumerate feasible actions;
- identify materially distinct outcomes;
- represent uncertainty explicitly where possible;
- compare expected value, downside, reversibility, and information value;
- identify when more information is worth acquiring before acting.

### SYSTEMS_FEEDBACK

Purpose: reason about interacting variables, feedback, delays, nonlinearities, and second-order effects.

Required behavior:

- identify relevant state variables and interactions;
- distinguish reinforcing from balancing feedback;
- account for delays and adaptation;
- anticipate second-order effects and failure modes;
- prefer interventions robust to feedback and model error.

## 5. Task-demand representation

Before any reasoning response is generated, each case should be represented by deployment-available task features. Initial features should be semantic/structural rather than lexical proxies.

Candidate dimensions:

- `deductive_requirement`
- `abductive_requirement`
- `causal_requirement`
- `search_planning_requirement`
- `decision_under_uncertainty_requirement`
- `systems_feedback_requirement`
- `empirical_testability`
- `constraint_density`
- `consequence_of_error`
- `operator_composition_need`

Each dimension should use a small ordinal scale, initially `0/1/2` = absent / material / central.

Important: these features are hypotheses about problem structure. They are not assumed valid until they predict held-out policy interactions.

## 6. Program structure

The program should be split into distinct stages so that discovery cannot masquerade as validation.

### Stage 0 — operator fidelity and separability

Goal: verify that the proposed specialist prompts actually change observable reasoning behavior relative to CONTROL and relative to one another.

Use a small development set not reused for confirmatory inference.

Pass conditions should include:

- each specialist increases its intended behavioral signature over CONTROL;
- specialists are behaviorally distinguishable from FULL and from at least most other specialists;
- no prompt has systematic format/pathology failures;
- the judge rubric can assess answer quality without rewarding visible headings or verbosity.

If operator fidelity fails, revise the operator definition before any fresh interaction suite is generated.

### Stage 1 — interaction discovery

Goal: measure whether policy quality varies systematically by task-demand structure.

Proposed initial design:

- 48 fresh cases;
- six primary task families, eight cases per family;
- conditions on every case: `CONTROL`, `FULL`, and all six specialists;
- one target-generation replicate per case/condition for discovery;
- blinded randomized judging;
- use the same target model currently available (`glm-5.1`) unless access changes before freeze;
- use `glm-5.3-flash` as judge only if it remains the available evaluator, with the same-family/provider limitation stated explicitly.

The six primary task families should correspond to the six specialist hypotheses but must contain mixed/ambiguous cases so that family labels are not equivalent to a prompt keyword.

Primary Stage-1 estimand:

`policy × task-family interaction`.

Secondary estimands:

- specialist vs FULL within intended family;
- specialist vs CONTROL within intended family;
- specialist performance outside intended family;
- FULL robustness across families;
- relationship between task-demand vectors and observed policy advantage.

Stage 1 is developmental. It may be used to derive the controller but not to validate that controller.

### Stage 2 — freeze controller

After Stage 1, define exactly one controller before authoring the Stage-3 suite.

The controller must consume only information available before response generation.

Allowed outputs:

- one specialist operator;
- an explicitly defined composition of at most a small number of operators;
- `FULL` as fallback when the task is ambiguous, composite, or high-consequence.

The controller must include an uncertainty/escalation rule. A generic form is:

- high-confidence structural match → specialist;
- multi-demand/composite task → defined operator composition;
- low-confidence or high-consequence task → FULL.

Do not tune thresholds on Stage-3 data.

### Stage 3 — fresh controller validation

Goal: test the frozen controller on a new suite never used for operator design, interaction discovery, or threshold selection.

Minimum conditions:

- `CONTROL`
- frozen `FULL`
- frozen `ADAPTIVE_CONTROLLER`

Optional diagnostic condition:

- `SPECIALIST_ORACLE`, where the best policy is selected using outcome labels, used only as an unattainable upper-bound diagnostic and never as a deployment claim.

Recommended design if budget permits:

- 48 fresh cases;
- three target-generation replicates per condition;
- three blinded randomized judge votes per generated pair;
- pair aggregation within generation replicate;
- generation replicates averaged within case;
- case as the independent unit;
- case-clustered bootstrap intervals.

## 7. Proposed validation gates

Final thresholds must be frozen in a preregistration before Stage-3 target generation. The following are design candidates, not yet frozen success criteria.

### Quality preservation against FULL

Primary requirement:

`ADAPTIVE vs FULL` paired decrement must be non-inferior within a small predeclared margin.

A candidate margin is `-0.02` on pairwise score, but this must be justified before preregistration rather than chosen after seeing data.

### Benefit over CONTROL

Require:

- `ADAPTIVE vs CONTROL` point estimate materially above `0.50`;
- lower confidence bound above `0.50` if the study is powered for confirmatory superiority.

### Selectivity

The controller should not simply emit FULL on nearly all non-trivial cases.

A selectivity target should be specified only after Stage 1 shows that specialist substitution is plausible. Do not impose an arbitrary cap that forces routing at the expense of quality.

### Interaction validity

The controller should preserve a measurable relationship between predicted reasoning demands and realized policy benefit on the fresh suite.

### Failure floor

No sufficiently populated predeclared task family should exhibit a large harm relative to FULL.

## 8. Benchmark construction rules

The benchmark must be authored so that the interaction hypothesis is genuinely testable.

Requirements:

1. fresh cases only for Stage 1 and a separately fresh set for Stage 3;
2. no reuse of the 144 exposed routing cases for fitting or validation;
3. no case should announce the desired operator by name;
4. include ambiguous and mixed-demand cases;
5. include no-action cases where the correct behavior may be to avoid unnecessary intervention;
6. vary domains within each reasoning family so operator success cannot be reduced to topic recognition;
7. balance consequence, uncertainty, and answer length where practical;
8. freeze case text, task-demand annotations, and hashes before target generation;
9. record whether each case is program-authored or externally sourced/adapted;
10. where feasible, include external/open benchmark material to reduce dependence on program-authored tasks.

## 9. Evaluation safeguards

Reuse the strongest safeguards from the existing program:

- randomized blinded A/B presentation;
- repeated judge votes in confirmatory stages;
- deterministic A/B orientation randomization;
- case-level aggregation;
- case-clustered bootstrap uncertainty;
- explicit judge agreement reporting;
- frozen recovery rules for evaluator-format failures;
- no regeneration of target outputs after outcome inspection;
- claim boundaries tied to target/evaluator family and provider.

Add two new safeguards:

1. **verbosity/style control**: specialist prompts and FULL should be constrained so a judge cannot trivially reward answer length;
2. **operator-label blindness**: judge inputs must never reveal which reasoning policy produced a candidate.

## 10. Cost discipline

Quality remains primary, but this program explicitly measures computation cost because adaptive selection is meaningful only if it preserves quality while changing reasoning allocation.

Record per condition:

- input tokens;
- output tokens;
- latency if available;
- API cost if available;
- tool calls if later agentic versions use tools.

Cost must remain descriptive until a quality-preserving controller is established.

## 11. Stop rules

Stop or revise the program before fresh controller validation if any of the following occurs:

- specialist prompts are not behaviorally separable;
- no reproducible policy × task interaction appears in Stage 1;
- FULL dominates specialists broadly enough that task-conditional selection has no plausible quality or cost advantage;
- the task-demand representation cannot predict policy differences out of sample within Stage 1 cross-validation;
- controller design requires outcome information unavailable at deployment;
- the controller can only meet quality preservation by selecting FULL almost universally.

A negative result is informative: it would support FULL as a robust generalist and constrain the value of adaptive reasoning control on the tested target.

## 12. Claims permitted by outcomes

If Stage 1 shows interaction but Stage 3 controller validation fails:

> Reasoning-policy effects are task-dependent, but the tested input-available controller does not reliably exploit that structure.

If Stage 3 preserves FULL quality while selectively invoking specialists:

> A frozen task-conditional controller can allocate reasoning policies without material quality loss on fresh cases for the tested target/evaluator setup.

If Stage 3 outperforms FULL:

> A frozen adaptive reasoning controller improves judged response quality over the fixed eight-stage generalist on the tested fresh suite.

None of these outcomes establishes cross-family generality without additional target/evaluator validation.

## 13. Immediate implementation sequence

1. Freeze v0.1 definitions of the six specialist policies.
2. Build a small Stage-0 operator-fidelity suite.
3. Implement a runner that treats policies as interchangeable conditions.
4. Implement behavioral-fidelity and pairwise-quality evaluation without exposing policy labels to judges.
5. Run Stage 0 only.
6. Review whether operators are behaviorally distinct enough to justify Stage 1.
7. Only then author and freeze the 48-case Stage-1 interaction suite.

## 14. Current decision

This document authorizes **research development only**.

It does not modify `CURRENT_ARCHITECTURE_DECISION_V1.md`, does not reopen Selective Routing v4, and does not claim that an adaptive controller has been validated.
