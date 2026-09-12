# Operator Fidelity v0.1 — Frozen Preflight

Status: **frozen before target generation**.

Purpose: determine whether the six candidate specialist prompts in Adaptive Reasoning Controller v0.1 create observably distinct reasoning behavior before investing in a 48-case interaction suite.

This is a development/fidelity experiment, not confirmatory evidence that any specialist improves task quality.

## Frozen artifacts

Policies:

- `benchmark/reasoning_policies_v01.py`
- git blob SHA: `db1c726996bb9aed4b3fb77a6467df9a56ee511b`

Preflight cases:

- `benchmark/operator_fidelity_cases_v01.json`
- git blob SHA: `42be38d7554bcf895ff8864f232f156bcd958c17`

Any prompt or case change after the first target call requires a new version.

## Conditions

Run all eight conditions on every case:

- `CONTROL`
- frozen `FULL`
- `DEDUCTIVE_CONSTRAINT`
- `ABDUCTIVE_DIAGNOSTIC`
- `CAUSAL_EXPERIMENTAL`
- `SEARCH_PLANNING`
- `DECISION_THEORETIC`
- `SYSTEMS_FEEDBACK`

The six specialist prompts are candidates only. FULL remains the current supported non-trivial policy regardless of this preflight outcome.

## Cases

Six fresh development cases, one primary probe for each candidate specialist.

The cases are intentionally small because Stage 0 asks only whether the prompts manipulate observable behavior strongly enough to justify a larger interaction experiment.

These six cases must never be treated as held-out evidence for controller quality.

## Runtime

Target:

- model: `glm-5.1`
- family: `glm`
- provider: `zai`
- endpoint: frozen project Z.AI coding endpoint

Judge:

- model: `glm-5.3-flash`
- family: `glm`
- provider: `zai`

The same-family/provider limitation applies. This is acceptable for operator-fidelity development because no cross-family generality claim is made.

## Generation design

- one target generation per case × condition;
- six cases × eight conditions = 48 target outputs;
- no target output may be regenerated after any behavior scores are inspected;
- record target token use and latency descriptively.

## Behavior rubric

Each response is scored independently and without revealing the condition label on six dimensions from 0 to 4.

### `deductive_constraint`

- `0`: ignores or violates explicit constraints/premises;
- `1`: mentions constraints but reasons loosely or adds unsupported assumptions;
- `2`: mostly respects premises/constraints but does not clearly distinguish necessity from plausibility;
- `3`: derives conclusions from premises/constraints and exposes important assumptions;
- `4`: rigorous necessity/feasibility reasoning with counterexample or boundary checking where relevant.

### `abductive_diagnostic`

- `0`: premature single explanation or unsupported diagnosis;
- `1`: names alternatives superficially;
- `2`: maintains alternatives but weakly discriminates them;
- `3`: materially competing explanations plus evidence that separates them;
- `4`: calibrated ranking, explicit discriminators, and action tied to information that can change the diagnosis.

### `causal_experimental`

- `0`: treats association/timing as causation;
- `1`: notes causal uncertainty without a useful identification strategy;
- `2`: identifies alternatives/confounding and suggests partially informative evidence;
- `3`: proposes a clear discriminating intervention/comparison with predicted outcomes;
- `4`: strong causal identification logic including counterfactual/intervention interpretation and falsification conditions.

### `search_planning`

- `0`: infeasible or unordered proposal;
- `1`: simple checklist with weak dependency handling;
- `2`: feasible basic ordering but little alternative search or recovery logic;
- `3`: explicit constraints, candidate sequencing, checkpoints, and recovery path;
- `4`: robust plan/search with branching, bottleneck handling, and option preservation where relevant.

### `decision_theoretic`

- `0`: ignores uncertainty or materially important consequences;
- `1`: acknowledges uncertainty but selects mainly by the most likely outcome;
- `2`: compares alternatives and some downside/reversibility considerations;
- `3`: explicit asymmetric consequences, information value, reversibility, and decision-critical assumptions;
- `4`: well-calibrated decision analysis that integrates uncertainty, downside, option value, and stopping/information criteria.

### `systems_feedback`

- `0`: static local reasoning where feedback is central;
- `1`: mentions second-order effects generically;
- `2`: identifies at least one material feedback/delay/bottleneck effect;
- `3`: models interacting loops/delays and adapts intervention/monitoring accordingly;
- `4`: robust dynamic reasoning including feedback, adaptation, bottleneck migration, and time-horizon implications without inventing unsupported complexity.

## Judge procedure

For each target output:

- provide only the case prompt, evaluator target-behavior note, and candidate response;
- hide the producing condition;
- request the six absolute 0–4 behavior scores plus a short justification;
- request two judge votes per output with deterministic vote identifiers;
- average the two votes within output.

The judge must be instructed not to reward headings, explicit framework names, or verbosity.

## Fidelity estimands

For operator `r` with its matching probe case `c_r` and matching behavior dimension `d_r`:

`lift_control(r) = score(r, c_r, d_r) - score(CONTROL, c_r, d_r)`

`separation(r) = score(r, c_r, d_r) - median(score(other_specialists, c_r, d_r))`

FULL is excluded from the separation median because it is intentionally a broad generalist and may legitimately express several behaviors.

Also report:

- FULL vs CONTROL on every dimension/case;
- response length and target token use by condition;
- all six behavior scores for every condition/case;
- the rank of the intended specialist on its matching dimension.

## Eligibility gates

A specialist is **Stage-1 eligible** only if both conditions hold on its matching probe:

1. `lift_control >= +0.50` points on the 0–4 scale;
2. `separation >= +0.25` against the median of the five nonmatching specialists.

Additional pathology gate:

- no response may contain a material task-accuracy failure attributable to the specialist instruction;
- no specialist may rely on visible operator names/headings as a substitute for the target behavior.

These gates are deliberately behavioral. They do not establish a quality advantage.

## Program decision rule

- If all six specialists pass, freeze them as candidate policies for Stage 1.
- If four or five pass, Stage 1 may proceed only with the passing subset and a revised task-family design frozen before new case authoring.
- If fewer than four pass, stop and redesign operator definitions before creating the 48-case interaction suite.
- A failed operator may be revised only under a new policy version and with new preflight cases.

Do not tune prompts against these same six cases after scores are visible and then report the retuned prompts as having passed v0.1.

## Quality sanity check

For each matching case only, run blinded pairwise quality comparison:

- intended specialist vs CONTROL;
- intended specialist vs FULL.

Use one randomized A/B vote per pair as a pathology screen only.

A quality loss does not by itself prove the operator concept invalid, but any severe factual, logical, or decision-quality failure blocks that operator from Stage 1 until a new version is tested.

## Interpretation boundary

Passing Stage 0 supports only:

> The specialist prompt changes observable reasoning behavior in the intended direction and is sufficiently separable to justify interaction testing.

It does **not** support:

- that the specialist is better than FULL;
- that the specialist is best for its named task family;
- that task-conditional routing works;
- that the behavior corresponds faithfully to hidden internal cognition;
- that the effect generalizes beyond GLM-5.1.

The next step after a pass is Stage-1 interaction discovery on new cases.
