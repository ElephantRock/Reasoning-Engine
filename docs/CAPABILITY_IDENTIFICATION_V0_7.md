# Capability Identification v0.7

## Purpose

v0.7 is a **development diagnostic** created after the v0.6.1 replication showed that leave-one-instruction-out comparisons did not reliably remove the corresponding reasoning behavior.

The central identification requirement is:

> Do not interpret a quality difference as evidence about a reasoning capability unless the experimental treatment first measurably changes expression of that capability.

## Research question

For each target family (`DIAGNOSE`, `REVISE`, `ENGINEER`):

1. Does adding an explicit capability module increase expression of the target behavior relative to a neutral reasoning core?
2. If the manipulation is successful, does the induced behavior improve reasoning quality?
3. Is any improvement capability-specific, or is it explained by a generic extra-attention instruction?

## Conditions

All conditions share the same neutral core:

- use supplied evidence faithfully;
- separate observation from inference;
- state important assumptions and uncertainty;
- respect stated constraints;
- give the action/conclusion justified by evidence.

The conditions are:

### CONTROL

Neutral core only. It contains no explicit `DIAGNOSE`, `REVISE`, or `ENGINEER` module.

### ATTENTION

CONTROL plus one generic internal quality-control pass for overlooked facts, arithmetic mistakes, and unsupported claims.

This controls for the possibility that any extra instruction simply causes the model to spend more attention.

### TARGET

CONTROL plus exactly one family-specific module.

`DIAGNOSE`:

> Under material ambiguity, keep multiple materially plausible causal explanations alive, distinguish symptom, proximate cause, and root cause where useful, and prefer a next step that separates explanations before committing to one.

`REVISE`:

> When later evidence conflicts with an earlier causal model, explicitly change the model or confidence: state what is demoted or promoted and change the recommended action accordingly rather than merely appending the new fact.

`ENGINEER`:

> Once a mechanism is sufficiently supported, translate it into a robust action under constraints. Connect the action to the mechanism, compare reversible and irreversible options, define monitoring and rollback criteria, and account for important feedback or second-order effects without inventing unsupported causal certainty.

## Cases

Six new development cases are used, two per family.

The case prompts intentionally avoid explicit instructions such as:

- “diagnose the cause”;
- “generate hypotheses”;
- “revise/update your model”;
- “design an intervention”;
- “engineer a solution.”

They present the evidence and ask for the next warranted action or conclusion. This reduces direct task-language elicitation of the target capability.

## Manipulation check

A separate blinded behavior judge receives only:

- the case-specific target-behavior definition;
- Response A;
- Response B.

It scores target-behavior expression from 0 to 4.

The behavior judge does **not** judge overall answer quality.

Each TARGET-vs-CONTROL generated pair receives 3 independently oriented behavior-judge votes.

For each case-generation pair, behavior scores are averaged across those repeated votes. Replicates are then averaged within cases/families.

### Identification gate

Predeclared gate:

`mean behavior lift = TARGET - CONTROL >= 0.5` on the 0–4 scale.

If the gate is not met for a family, quality differences for that family are labeled **non-identifying**. They may describe prompt effects but cannot be used as evidence that the capability itself improves or harms reasoning.

## Quality comparisons

Quality is judged separately from behavior expression. The quality judge is **not shown the target-behavior definition**.

Each exact generated pair receives 3 blinded quality votes with deterministic randomized A/B orientation.

Comparisons:

1. `TARGET vs CONTROL` — primary instruction-mediated quality effect;
2. `TARGET vs ATTENTION` — capability specificity beyond generic extra checking;
3. `ATTENTION vs CONTROL` — generic-attention control effect.

Quality remains the primary outcome. Cost is descriptive only.

## Replication

Default target-generation replicates: `3`.

Default repeated quality votes per pair: `3`.

Default repeated behavior votes per TARGET-vs-CONTROL pair: `3`.

Repeated judge calls are nested within generated pairs. Target generations are nested within cases. Cases remain the independent benchmark clusters.

## Interpretation logic

For family `s`:

1. Estimate behavior lift:

   `B_s = behavior(TARGET_s) - behavior(CONTROL)`

2. If `B_s < 0.5`, stop. The manipulation is too weak to identify the component.

3. If `B_s >= 0.5`, inspect quality:

   `Q_s = quality(TARGET_s vs CONTROL)`

4. Compare against generic attention:

   `S_s = quality(TARGET_s vs ATTENTION)`

A useful capability module should ideally show:

- a positive manipulation lift;
- quality above the neutral point against CONTROL;
- quality above or at least not below ATTENTION;
- consistency across its two cases and target generations.

This is a development diagnostic, so no promotion threshold is treated as confirmatory evidence.

## What v0.7 does not test

v0.7 does not validate the full eight-stage protocol.

It does not test `PREDICT` or `TEST`; those are left unchanged while the weakest/most ambiguous component families are diagnosed.

It does not test Adaptive routing or reasoning cost optimization.

It does not provide evaluator independence because target and judge may still use the same model family/provider.

## Next decision

After v0.7:

- if a treatment does not change behavior, redesign the elicitation/manipulation rather than changing the framework based on quality noise;
- if behavior changes but quality does not improve, reconsider the component formulation or its conditional applicability;
- if behavior and quality improve consistently, preserve that component as a candidate for the frozen protocol;
- only after component definitions stabilize should a fresh held-out validation suite be created.
