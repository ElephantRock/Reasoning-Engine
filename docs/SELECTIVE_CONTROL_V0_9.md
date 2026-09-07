# Selective Control v0.9 — when explicit reasoning control adds value

## Motivation

v0.7 showed positive instruction-mediated evidence for `ENGINEER`, but `DIAGNOSE` and `REVISE` were already near ceiling under a minimal control prompt. v0.8 then screened twelve harder Diagnose/Revise cases and again found essentially ceiling-level endogenous behavior, so there was no manipulation headroom.

The resulting research question is no longer "does the model possess this capability?" It is:

> **When adverse context suppresses endogenous reasoning, does an explicit capability-control instruction restore the target behavior and improve reasoning quality beyond generic extra attention?**

This reframes the framework as a potential **selective reasoning controller**, not a mandatory eight-stage script.

## Frozen production protocol

v0.9 does **not** modify the production reasoning protocol. The `DIAGNOSE`, `REVISE`, and `ENGINEER` target modules are reused byte-for-byte from v0.7.

`TEST` and `PREDICT` are not changed or re-evaluated here.

## Paired clean/stress design

There are six base problems: two each for `DIAGNOSE`, `REVISE`, and `ENGINEER`. Each base problem has two variants:

- `CLEAN` — decisive evidence and constraints with little distraction;
- `STRESS` — the same decisive evidence and correct action, plus adverse contextual load such as authority anchors, irrelevant metrics, historical analogies, conflicting stakeholder pressure, time pressure, or familiar-action bias.

The evaluator reference is identical within each clean/stress pair. Stress is intended to change **reasoning difficulty**, not ground truth.

## Conditions

For every case variant:

1. `CONTROL` — minimal neutral reasoning prompt;
2. `ATTENTION` — CONTROL plus one generic quality-control pass;
3. `TARGET` — CONTROL plus the frozen family-specific capability module.

Default calibration uses three independent target generations per case/condition and three blinded judge votes per exact generated pair.

## Identification gates

Quality effects are not interpreted automatically.

### Gate 1 — stress must suppress endogenous behavior

For each family:

`CLEAN CONTROL behavior − STRESS CONTROL behavior >= 0.5`

on the 0–4 behavior scale.

If this gate fails, the stress manipulation did not create the failure mode we intended to study.

### Gate 2 — the target module must recover behavior under stress

For each family:

`STRESS TARGET behavior − STRESS CONTROL behavior >= 0.5`

If this gate fails, the explicit module did not materially change the target reasoning behavior.

### Capability-control interpretation

Only when both gates pass may the stress-condition quality comparisons be interpreted as evidence about selective control:

- `TARGET vs CONTROL` — primary recovery effect;
- `TARGET vs ATTENTION` — capability specificity beyond generic extra attention;
- `ATTENTION vs CONTROL` — generic attention control.

The paired clean/stress quality difference is descriptive evidence about whether explicit control becomes more useful under stress.

## What a positive result would mean

A strong selective-control signal requires:

1. CONTROL behavior degrades under stress;
2. TARGET restores the intended behavior;
3. TARGET beats CONTROL on reasoning quality under stress;
4. TARGET beats or materially exceeds ATTENTION under stress;
5. the pattern is reasonably consistent across both base cases and stochastic generations.

That would support a controller policy of the form:

`detect reasoning-risk condition -> activate relevant capability control -> verify outcome`

rather than forcing every stage on every problem.

## What a null result would mean

A null can arise for different reasons and must be classified correctly:

- stress gate fails -> the model remains robust without explicit control;
- recovery gate fails -> the instruction does not induce the intended behavior;
- gates pass but quality is neutral -> the behavior may be redundant or non-value-adding in that context;
- TARGET and ATTENTION perform similarly -> generic additional attention may explain the gain;
- quality worsens -> the explicit control may induce over-processing, distraction, or an interaction cost.

## Validation boundary

v0.9 is a development diagnostic. The cases and stressors are now exposed to framework development and cannot be reused as fresh held-out validation after tuning.

Target and judge default to the same `glm-5.1` model family and endpoint, so evaluator independence remains an open requirement.

A later cross-model replication should test the hypothesis that explicit control value increases as endogenous capability/reliability decreases.

## Cost policy

Token usage and latency remain descriptive only. They do not enter identification or quality decisions.
