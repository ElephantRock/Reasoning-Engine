# Quality Measurement v0.5

## Research objective

The primary project question is:

> Does the reasoning protocol improve reasoning quality relative to an uncontrolled baseline?

Measurement v0.5 therefore separates **reasoning quality research** from **reasoning-cost optimization**.

The current hierarchy is:

1. **Quality** — establish whether a reasoning protocol produces better epistemic and decision outcomes.
2. **Reliability** — establish whether that quality advantage reproduces across cases, generations, and evaluators.
3. **Cost** — only after a quality advantage is established, ask whether the same quality can be obtained with less reasoning.

Routing and cost optimization are deferred from primary evidence in this phase.

## Conditions

v0.5 evaluates only:

- `BASELINE` — no reasoning controller;
- `COMPACT` — Problem → First Principle → Mechanism → Evidence → Solution;
- `FULL` — Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer.

`ADAPTIVE` is intentionally excluded. Adaptive routing is an optimization layer, not the theory currently under test.

## Primary hypothesis

The primary quantity is the reasoning-quality advantage of FULL over BASELINE:

`Delta Q = Q(FULL) - Q(BASELINE)`

The primary empirical comparison is therefore:

`FULL vs BASELINE`

Two secondary ablations are retained:

- `COMPACT vs BASELINE` — does a lighter scaffold improve quality?
- `FULL vs COMPACT` — does the complete protocol add quality beyond the compact scaffold?

## What counts as reasoning quality

The blinded evaluator prioritizes, when applicable:

1. factual correctness and faithful use of observations;
2. separation of observation, inference, assumption, and causal claim;
3. causal/mechanistic accuracy and materially plausible alternatives;
4. quality and discriminatory value of evidence/tests;
5. revision under contradictory or sequential evidence;
6. calibrated uncertainty and exposed decision-critical assumptions;
7. correctness and robustness of decisions/interventions, including constraints and second-order effects.

The evaluator is explicitly told **not** to reward shorter answers, cheaper answers, framework terminology, headings, or verbosity. Token cost is not visible to the quality judge.

## Judge reliability

v0.4 revealed that one pair of identical responses could receive materially different pairwise verdicts on repeated evaluation. v0.5 therefore treats evaluator reliability as a first-class measurement property.

Each response pair receives an odd number of blinded judge votes (default: 3). A/B orientation is independently randomized for every vote. The report exposes:

- vote-level outcomes;
- majority winner;
- mean vote agreement;
- unanimous fraction;
- every non-unanimous case;
- case-clustered bootstrap confidence intervals.

A disagreement among judge votes is not hidden. It is evidence about evaluator uncertainty.

## Cost policy

Target input tokens, output tokens, and latency are still recorded because they will matter later. They are **descriptive diagnostics only**.

They do not enter:

- the quality judge prompt;
- pairwise winner selection;
- the primary quality score;
- controller promotion in this phase.

The later cost-optimization problem is conditional:

> Minimize reasoning cost subject to preserving the quality of the validated best reasoning process within a predefined tolerance.

That problem should not be optimized before the quality benchmark establishes a credible best process.

## First v0.5 experiment

The initial calibration uses the existing `pilot + stress` cases (12 cases total), one target-generation replicate per condition, and three repeated judge votes per response pair.

This is explicitly a **calibration experiment, not framework validation**, because these cases have already influenced framework and evaluator development.

The calibration asks:

1. Is `FULL vs BASELINE` directionally positive?
2. Does repeated judging produce enough agreement for pairwise evaluation to be trusted?
3. Is `FULL vs COMPACT` positive, neutral, or negative?
4. Which case families produce the largest quality differences?

If measurement is stable enough, validation should move to fresh held-out cases and preferably an evaluator model independent of the target model.

## Promotion discipline

Do not promote FULL, COMPACT, or any later controller because it is more protocol-compliant or more token-efficient.

A reasoning protocol should be promoted only if it produces a reproducible improvement in blinded reasoning quality on appropriately held-out tasks without introducing serious failure modes.
