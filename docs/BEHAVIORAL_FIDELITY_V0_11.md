# Behavioral Fidelity Identification v0.11

## Motivation

v0.10 replaced side-by-side behavior scoring with independent absolute scoring. That removed the contrast-bias concern, but both tested families saturated the coarse 0–4 behavior scale:

- TEST: CONTROL = 4.0, ATTENTION = 4.0, TARGET = 4.0;
- ENGINEER: CONTROL = 4.0, ATTENTION = 3.67, TARGET = 4.0.

Despite that ceiling, TARGET still won strongly on blinded reasoning quality. Raw quality-judge notes repeatedly attributed the difference to finer-grained execution: prospective outcome branches, explicit falsification logic, quantified rollback limits, staged reversibility, stronger monitoring, and second-order controls.

Therefore the next question is not whether the broad capability is present. It is whether the explicit module improves **behavioral fidelity**: completeness and decision relevance of the module's observable sub-behaviors.

## Design

Families:

- TEST
- ENGINEER

Conditions:

- CONTROL — v0.10 neutral core;
- ATTENTION — same generic quality-control instruction as v0.10;
- TARGET — CONTROL plus the frozen family-specific module from v0.10.

Cases:

- four fresh development cases;
- two per family;
- user prompts do not request named reasoning stages;
- cases were written before v0.11 outcomes exist.

Default replication:

- 3 stochastic target generations per case/condition;
- 3 fidelity votes per exact response;
- 3 blinded pairwise quality votes per generated comparison.

## Fidelity measurement

Each response is shown **alone** to the fidelity judge. The judge receives five predeclared observable criteria derived from the frozen module semantics.

Each criterion is scored:

- 0.0 — absent, contrary, or materially unusable;
- 0.5 — partial, implicit, incomplete, or weakly decision-relevant;
- 1.0 — clear, substantively complete, and decision-relevant.

The response composite is the mean of its five criteria.

Aggregation order:

1. average repeated judge votes within the exact response;
2. average generation replicates within the case/condition;
3. average cases within the family.

Generation and judge replicates are not treated as independent cases.

## Predeclared identification gate

For family `s`:

`DeltaF_s = Fidelity(TARGET_s) - Fidelity(CONTROL_s)`

The module is considered behaviorally identified only if:

`DeltaF_s >= 0.15`

on the 0–1 composite scale.

This threshold is fixed before any v0.11 model generations.

Quality is interpreted as instruction-mediated capability evidence only when the fidelity gate passes.

Secondary diagnostics:

- TARGET minus ATTENTION composite fidelity;
- criterion-level TARGET minus CONTROL deltas;
- TARGET vs CONTROL quality;
- TARGET vs ATTENTION quality;
- ATTENTION vs CONTROL quality.

## Interpretation discipline

If fidelity fails the gate, any quality advantage remains non-identifying for capability value; it may reflect other prompt effects.

If fidelity passes and TARGET beats CONTROL on quality, the evidence supports an instruction -> fidelity -> quality pathway on development cases.

If fidelity passes but quality does not improve, the induced behavior may be unnecessary, poorly matched to the cases, or costly without quality benefit.

This remains development calibration. Held-out validation still requires frozen prompts, fresh cases, multiple generations, repeated blinded judgments, and preferably an evaluator independent of the target model.
