# v0.7 result and v0.8 identification plan

## What v0.7 established

v0.7 separated target-behavior manipulation from reasoning-quality effects.

The preregistered manipulation gate was TARGET minus CONTROL behavior lift >= 0.5 on a 0–4 behavior scale.

Observed family-level behavior lifts:

- DIAGNOSE: +0.22 — gate failed.
- REVISE: +0.11 — gate failed.
- ENGINEER: +1.00 — gate passed.

Quality effects are therefore interpretable as instruction-mediated capability evidence only for ENGINEER in v0.7. ENGINEER produced a 1.000 TARGET-vs-CONTROL quality score and 0.833 TARGET-vs-ATTENTION score in that development diagnostic.

DIAGNOSE and REVISE remain unidentified rather than negative: their control responses already expressed the target behaviors near ceiling.

## Identification defect revealed by v0.7

The neutral v0.7 control was still behaviorally rich:

> Use the supplied evidence faithfully. Separate what is observed from what is inferred. State important assumptions and uncertainty. Respect stated constraints. Give the next action or conclusion that is justified by the evidence.

That wording, together with relatively transparent cases, can itself elicit diagnostic competition and model revision. A failed manipulation gate is therefore evidence that the experiment lacks behavioral headroom, not evidence that the capability has no value.

## v0.8 objective

v0.8 does not change the production reasoning protocol and does not retest ENGINEER. It is a two-stage development experiment for DIAGNOSE and REVISE only:

1. **Manipulation-capacity screen** — run a minimal control on a larger bank of harder candidate cases and estimate baseline target-behavior expression using repeated blinded behavior judgments.
2. **Fresh-generation identification test** — only cases with sufficient baseline headroom are eligible. Generate new CONTROL, ATTENTION, and TARGET responses and evaluate behavior lift and reasoning quality.

Candidate selection uses only CONTROL behavior scores. No quality outcome and no TARGET response is observed before selection.

## Minimal experimental control

The v0.8 control is intentionally narrower than v0.7:

> Answer accurately and concisely using the evidence provided. Respect stated constraints and recommend the next action that is justified. Do not use a named reasoning framework.

ATTENTION adds one generic quality-control pass. TARGET adds the unchanged v0.7 family module to the same minimal control.

This is an experimental control only. It is not a candidate replacement for the production protocol.

## Stage 1: capacity screen

Candidate bank:

- 6 DIAGNOSE cases;
- 6 REVISE cases.

For each candidate:

- 2 independent CONTROL generations;
- 3 independent blinded behavior-score votes per generation;
- no TARGET generation;
- no quality judging.

Predeclared eligibility rule:

- mean CONTROL behavior score <= 2.5/4; and
- at least 1.0 point of nominal headroom to the maximum score.

The workflow selects up to the 3 lowest-baseline cases per family. A family requires at least 2 eligible cases to proceed to Stage 2. If fewer than 2 qualify, that family is reported as `insufficient_manipulation_capacity` and no capability-quality claim is attempted.

## Stage 2: fresh identification test

Screening generations are never reused.

For each selected case:

- 3 fresh generations per condition: CONTROL, ATTENTION, TARGET;
- 3 blinded quality votes per exact response pair;
- 3 blinded behavior votes for TARGET vs CONTROL;
- case-level aggregation preserves generation-replicate boundaries.

Primary identification gate remains:

TARGET minus CONTROL behavior lift >= 0.5/4.

Quality effects are interpreted as capability evidence only when the family passes that manipulation gate.

Primary quality comparison:

TARGET vs CONTROL.

Specificity comparison:

TARGET vs ATTENTION.

Generic-deliberation control:

ATTENTION vs CONTROL.

## Interpretation boundaries

v0.8 remains development evidence. Candidate cases are explicitly screened and therefore cannot serve as fresh held-out validation. Same-model target/judge runs remain evaluator-dependent.

ENGINEER is frozen from v0.7 and is not retuned based on v0.8. TEST and PREDICT are also untouched in this experiment.
