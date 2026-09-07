# Absolute Behavior Identification v0.10

## Why this experiment exists

v0.9 exposed a measurement-format problem: absolute CONTROL behavior scores remained near ceiling, while side-by-side TARGET-vs-CONTROL behavior scoring sometimes pushed CONTROL materially lower. This makes pairwise behavior lift vulnerable to contrast effects.

v0.10 removes that ambiguity. A behavior judge sees exactly one response trajectory at a time. CONTROL, ATTENTION, and TARGET are each scored independently from 0–4 for the case-specific target behavior. Behavior lift is calculated only after all independent judgments are complete.

## Research question

For two capabilities with materially different prior evidence—`TEST` and `ENGINEER`—does an explicit module:

1. independently increase expression of the intended reasoning behavior relative to CONTROL;
2. improve reasoning quality relative to CONTROL;
3. outperform generic additional attention?

`ENGINEER` is the positive-control family because v0.7 and v0.9 both produced strong quality signals. `TEST` is the most promising unresolved capability from the replicated v0.6.1 ablations.

## Conditions

- `CONTROL` — the neutral v0.7 core.
- `ATTENTION` — CONTROL plus the frozen v0.7 generic quality-control pass.
- `TARGET` — CONTROL plus the capability module.

The `ENGINEER` module is frozen byte-for-byte from v0.7. The `TEST` module is the existing explicit TEST module from v0.6; it is not rewritten in response to v0.10 cases.

## Cases

Four new development cases:

- two `TEST` cases;
- two `ENGINEER` cases.

The user prompts do not explicitly request a named test, experiment, engineering framework, or reasoning stage. The target behavior exists only in the hidden evaluator key and treatment module.

These are development cases and cannot later serve as fresh held-out validation.

## Replication and judging

Default preregistered settings:

- 3 target-generation replicates per case/condition;
- 3 independent absolute behavior votes per exact generated response;
- 3 blinded pairwise quality votes per generated comparison.

There are 4 cases × 3 conditions × 3 generations = 36 target generations.

Behavior judging requires 36 × 3 = 108 single-response judgments. Quality judging covers three pairwise comparisons, giving 4 × 3 generations × 3 comparisons × 3 votes = 108 quality judgments.

This smaller design is intentionally sized well below the hosted-runner limit that cancelled v0.9 during report synthesis.

## Behavior aggregation

The independent unit is the case, not the judge vote or stochastic generation.

Aggregation order:

1. average behavior votes within one exact generated response;
2. average generation replicates within `(case, condition)`;
3. average cases within `(family, condition)`;
4. compute condition differences from those family means.

Primary manipulation quantity:

`behavior_lift = TARGET - CONTROL`

Predeclared identification gate:

`TARGET - CONTROL >= 0.5` on the 0–4 absolute behavior scale.

`TARGET - ATTENTION` and `ATTENTION - CONTROL` are reported descriptively to show whether generic extra deliberation induces similar behavior.

## Quality comparisons

1. `TARGET_vs_CONTROL` — primary instruction effect;
2. `TARGET_vs_ATTENTION` — capability specificity;
3. `ATTENTION_vs_CONTROL` — generic attention control.

Quality remains blinded pairwise evaluation because pairwise comparison is the outcome metric; the contrast-effect concern applies specifically to using side-by-side scoring as a manipulation measure.

## Interpretation discipline

A family's quality difference is interpretable as instruction-mediated capability evidence only if its independently scored absolute behavior manipulation passes the predeclared `+0.5` gate.

If the gate fails, quality differences remain descriptive and non-identifying for capability value.

Evidence is stronger when:

- TARGET passes the absolute behavior gate;
- TARGET beats CONTROL on quality;
- TARGET also beats generic ATTENTION on quality;
- both family cases support the direction across stochastic generations;
- judge agreement is stable.

No token or latency metric enters the quality or component decision.

## Validation boundary

v0.10 is a development diagnostic. It does not validate the reasoning framework. Strong validation still requires a frozen candidate, fresh held-out cases, multiple target generations, repeated blinded judgments, and preferably an independent evaluator model.