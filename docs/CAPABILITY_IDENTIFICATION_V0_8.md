# Capability Identification v0.8

## Purpose

v0.8 is a development experiment for two capabilities that remained unidentified in v0.7: `DIAGNOSE` and `REVISE`.

v0.7 showed that the control condition already expressed these behaviors near ceiling. The problem was therefore insufficient manipulation headroom, not a demonstrated negative capability effect.

v0.8 asks two sequential questions:

1. Can we find cases where a minimal control does **not already express** the target behavior strongly?
2. On those cases, does adding the unchanged target-capability instruction increase the behavior and improve reasoning quality beyond both a minimal control and a generic extra-attention control?

`ENGINEER` is intentionally excluded and frozen after the identified positive v0.7 result. `TEST` and `PREDICT` are not changed or retested here.

## Conditions

### CONTROL

`Answer accurately and concisely using the evidence provided. Respect stated constraints and recommend the next action that is justified. Do not use a named reasoning framework.`

### ATTENTION

CONTROL plus one generic quality-control pass for overlooked facts, arithmetic mistakes, and unsupported claims.

### TARGET

CONTROL plus the unchanged v0.7 family-specific module for `DIAGNOSE` or `REVISE`.

The control is an experimental baseline only. It is not proposed as a replacement production protocol.

## Stage 1 — manipulation-capacity screening

Candidate bank: 12 development cases, six per family.

Only CONTROL is generated during screening.

Defaults:

- 2 independent CONTROL generations per candidate;
- 3 blinded absolute behavior-score votes per generation;
- no TARGET responses;
- no ATTENTION responses;
- no quality judging.

Eligibility is predeclared:

- mean CONTROL target-behavior score `<= 2.5 / 4`; and
- nominal headroom `>= 1.0` point.

Up to the three lowest-baseline eligible cases are selected per family. At least two eligible cases are required to proceed for that family.

Selection is based only on CONTROL behavior scores. TARGET behavior and quality outcomes are unavailable at selection time.

## Stage 2 — fresh identification test

Screening generations are discarded for causal estimation.

For each selected case:

- 3 fresh generations per condition;
- 3 blinded TARGET-vs-CONTROL behavior votes per generated pair;
- 3 blinded quality votes per exact pair for:
  - TARGET vs CONTROL;
  - TARGET vs ATTENTION;
  - ATTENTION vs CONTROL.

The behavior identification gate remains:

`TARGET behavior mean - CONTROL behavior mean >= 0.5 / 4`.

Quality effects are interpreted as instruction-mediated capability evidence only if the family both passes Stage 1 capacity requirements and passes the Stage 2 manipulation gate.

## Interpretation

Possible outcomes:

- **No capacity:** fewer than two low-baseline cases exist in the candidate bank. The experiment does not test capability value.
- **Capacity but failed manipulation:** cases had room, but the instruction still did not move behavior enough. Quality differences are non-identifying.
- **Manipulation passed, quality positive:** evidence that the explicit capability instruction causes more target behavior and that induced behavior improves reasoning quality on these development cases.
- **Manipulation passed, quality neutral/negative:** evidence that the induced behavior does not help, or harms, on these development cases; inspect mechanism and interactions before protocol revision.

## Validation boundary

v0.8 is explicitly development data. Screening the candidate bank contaminates it for final validation. Any promoted protocol must later be tested on fresh held-out cases, with multiple generations and preferably an evaluator independent of the target model.
