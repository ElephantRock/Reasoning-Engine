# Post-v0.11 Decision Protocol

Status: **preregistered before v0.11 results are available**.

This document fixes the decision rule that will be applied after Behavioral Fidelity v0.11. It exists to prevent outcome-dependent reinterpretation or repeated measurement redesign on the same development families.

## Scope

v0.11 tests two explicit control modules:

- `TEST`
- `ENGINEER`

with three conditions:

- `CONTROL`
- `ATTENTION`
- `TARGET`

and independent behavioral-fidelity scoring on five predeclared observable criteria per family.

The production eight-stage reasoning protocol is not modified by this document.

## Primary identification gate

A module is behaviorally identified only if:

`TARGET composite fidelity - CONTROL composite fidelity >= 0.15`

on the normalized 0–1 fidelity scale.

If this gate fails, quality differences must not be described as evidence that the module improved quality *through the intended behavioral mechanism*.

## Quality-support rule

For a behaviorally identified module, classify development evidence as **strong directional support** only if all of the following hold:

1. `TARGET vs CONTROL` family quality score is at least `0.667`;
2. `TARGET vs ATTENTION` family quality score is at least `0.667`;
3. neither of the two family cases has a mean focal score below `0.5` against CONTROL;
4. neither of the two family cases has a mean focal score below `0.5` against ATTENTION.

The `0.667` threshold is fixed here before v0.11 results and represents a clear two-thirds directional advantage rather than a minimal edge above chance.

If the fidelity gate passes but these quality conditions do not, classify the result as **identified but quality-mixed/unsupported**.

If the fidelity gate fails, classify the result as **non-identified**, regardless of quality score.

## Module decision table

For each family independently:

### A. Fidelity gate passes + strong directional quality support

- Freeze the exact module wording used in v0.11.
- Mark it as a candidate selective-control module for held-out validation.
- Do not tune its wording on the v0.11 cases.

### B. Fidelity gate passes + quality mixed/unsupported

- Do not include the explicit module in the candidate selective controller.
- Preserve the conceptual capability in the theoretical framework, but treat explicit prompting as unsupported on current evidence.
- Do not redesign the module again on these development cases.

### C. Fidelity gate fails

- Do not claim instruction-mediated capability value.
- Do not include the explicit module in the candidate selective controller on the basis of current development evidence.
- Positive quality differences, if any, may be reported as unexplained prompt effects but not as validated mediation through the target capability.
- Do not introduce a third behavior scale for the same development cases.

## Stop rule

v0.11 is the final development-stage measurement redesign for `TEST` and `ENGINEER` on the current case families.

After v0.11:

- no additional behavior-presence scale;
- no additional fidelity decomposition;
- no threshold change;
- no wording adjustment based on v0.11 outcomes;
- no new development cases constructed solely to make either module satisfy its gate.

The next scientific phase is held-out validation, not another attempt to obtain a preferred development result.

## Candidate controller freeze

After applying the decision table, construct a frozen candidate controller:

`NEUTRAL CORE + {only explicit modules with strong directional support}`

The module set may therefore contain:

- both `TEST` and `ENGINEER`;
- only `TEST`;
- only `ENGINEER`;
- neither.

This outcome is allowed to be null. A null explicit-module result would mean that the current evidence does not justify those prompt interventions, not that the underlying reasoning capabilities are conceptually unnecessary.

## Held-out validation phase

Once the candidate controller is frozen, create a fresh benchmark not used to design prompts, modules, fidelity criteria, thresholds, or development cases.

### Primary validation comparison

`FROZEN CANDIDATE CONTROLLER vs UNCONTROLLED BASELINE`

Primary outcome: blinded reasoning-quality pairwise score aggregated by case.

### Secondary comparison

`FROZEN CANDIDATE CONTROLLER vs COMPACT`

This tests whether selective explicit control adds value beyond the strongest simpler structured prompt observed in v0.5 development calibration.

### Validation requirements

- fresh held-out cases;
- multiple stochastic target generations per case;
- repeated blinded judgments;
- case-clustered uncertainty;
- no prompt/module changes after held-out generation begins;
- preferably an evaluator from a different model family/provider than the target;
- cost remains descriptive until quality is established.

## Interpretation boundary

Even a successful held-out result validates a prompt/control policy for the tested models and task distribution. It does not establish that the eight conceptual stages are metaphysically necessary or that every model requires every explicit instruction.

The research target is narrower and operational:

> identify control interventions that reproducibly improve reasoning quality beyond endogenous reasoning, then validate them on unseen cases.
