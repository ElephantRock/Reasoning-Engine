# Stage Ablation Measurement v0.6.1

## Purpose

Measurement v0.6.1 corrects two methodological defects identified in review of v0.6.

The research question remains quality-first:

> Which explicitly specified reasoning capabilities make a marginal contribution to reasoning quality?

This is **component calibration**, not held-out framework validation.

## Why v0.6 does not identify component value

v0.6 compared `TARGETED = COMPACT + stage-specific instruction` against `COMPACT`.

That is not a clean component ablation because the existing Compact prompt already contains several of the behaviors being tested. In particular, Compact already instructs the model to:

- seek evidence capable of weakening the favored mechanism;
- revise when evidence contradicts the model;
- engineer under constraints including risk, reversibility, side effects, and second-order effects.

Therefore `TARGETED vs COMPACT` can measure the effect of **re-emphasizing or elaborating** a capability, but it cannot establish the marginal value of introducing Test, Revise, or Engineer as components.

Any v0.6 result must be interpreted under that narrower description.

## Corrected identification strategy

v0.6.1 uses a leave-one-capability-out design.

For every stage-targeted case:

- `FULL` is the exact production `pilot.FULL` system prompt;
- `ABLATED` starts from that exact prompt and removes only the instruction fragment(s) assigned to the target capability family.

The primary comparison is therefore:

**FULL vs FULL-minus-target-capability**

The five capability families remain:

1. `DIAGNOSE` — materially plausible competing explanations; symptom/proximate/root distinctions;
2. `PREDICT` — prospective observable predictions;
3. `TEST` — discriminating/falsifying tests;
4. `REVISE` — explicit model revision under contradiction;
5. `ENGINEER` — mechanism-linked intervention design, robustness, reversibility, second-order effects, and post-intervention observation.

The case set remains the ten v0.6 development cases, two per family. Because those cases were explicitly designed for this ablation program, they are not a held-out validation set.

## Measurement

Each FULL/ABLATED response pair receives repeated blinded quality-only votes with independently randomized A/B orientation.

Primary outcome:

- focal score for FULL, where win = 1, tie = 0.5, loss = 0;
- case-clustered bootstrap interval;
- per-family score;
- repeated-vote agreement.

Token use and latency are recorded only as descriptive diagnostics and do not enter the quality judgment.

## Replicate accounting correction

v0.6 also grouped family-level judge votes only by case. With more than one stochastic generation replicate, that conflates two different sources of variance:

- judge disagreement on the **same** response pair;
- generation variability across **different** response pairs.

v0.6.1 preserves `(case_id, generation_replicate)` boundaries when calculating vote agreement and majority outcomes, then averages replicate scores within case for case-level effects.

## Interpretation

Evidence for a capability requires FULL to outperform the corresponding leave-one-out condition on cases designed to require that capability.

A tie means the explicit stage instruction did not materially change measured reasoning quality in that case; it does not prove the model failed to perform the capability spontaneously.

A loss means the stage instruction, as operationalized in the current prompt, harmed reasoning quality on that case.

The experiment tests the **causal effect of explicit protocol instructions**, not whether the underlying model is intrinsically capable of the behavior.

## Validation boundary

Even a strong v0.6.1 calibration result is not framework validation. Promotion would still require:

- frozen treatment prompts;
- genuinely fresh held-out cases not used to design the ablation;
- multiple target-generation replicates;
- repeated or ensemble judging;
- preferably an evaluator model independent of the target model.
