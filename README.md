# Reasoning Engine

An experimental reasoning-control architecture for moving from observations to justified interventions while explicitly managing causal uncertainty, evidence, revision, and engineering consequences.

## Core protocol

For substantial non-trivial problems:

**Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**

Compact scaffold:

**Problem → First Principle → Mechanism → Evidence → Solution**

Adaptive routing exists experimentally, but routing is deferred from the primary research question.

## Research hierarchy

The project currently asks, in order:

1. **Does explicit structured reasoning improve reasoning quality relative to an uncontrolled baseline?**
2. **Which explicit reasoning instructions reliably change the intended reasoning behavior?**
3. **When a behavior is successfully induced, does it improve reasoning quality?**
4. **Do those effects replicate across cases, generations, and independent evaluators?**
5. **Only then: can the validated process be routed or compressed more cheaply?**

Quality is primary. Token count and latency remain descriptive diagnostics only.

## Evidence so far

### Quality Measurement v0.5

On 12 development/calibration cases:

- **FULL vs BASELINE:** `0.7778`, 95% case-bootstrap interval `0.5833–0.9444`, 8 wins / 3 ties / 1 loss, mean repeated-judge agreement `0.9722`.
- **COMPACT vs BASELINE:** `0.8056`, interval `0.6250–0.9583`, 9 wins / 1 tie / 2 losses.
- **FULL vs COMPACT:** `0.5833`, interval `0.4167–0.7500`, 6 wins / 3 ties / 3 losses.

Interpretation: structured reasoning shows a strong quality signal over baseline on these development cases, but the full eight-stage protocol has not been shown superior to Compact.

See `docs/QUALITY_V0_5_RESULTS.md`.

### Stage Ablation v0.6.1 and replication

v0.6.1 compared the production `FULL` prompt with `FULL` minus one explicit capability instruction.

The original one-generation run suggested strong positive effects for `PREDICT`, `TEST`, `REVISE`, and `ENGINEER`, with a negative `DIAGNOSE` effect.

A preregistered three-generation replication did **not** reproduce that pattern.

Replication-only overall `FULL vs ABLATED` score: `0.433` with interval `0.250–0.606`.

Combined four-generation stage scores, averaging generations within cases:

- `DIAGNOSE`: `0.375`
- `PREDICT`: `0.604`
- `TEST`: `0.729`
- `REVISE`: `0.458`
- `ENGINEER`: `0.292`

Combined overall score is approximately `0.492`.

Inspection of the raw response pairs revealed an identification problem: deleting an instruction fragment often did **not** remove the underlying reasoning behavior. The task wording and model priors could still elicit diagnosis, revision, or engineering. Therefore v0.6.1 primarily measures the marginal effect of mentioning an instruction fragment, not the causal value of possessing/executing the capability itself.

See `docs/ABLATION_V0_6_1_REPLICATION_RESULTS.md`.

## Capability Identification v0.7

v0.7 addresses that identification problem directly.

It currently targets the three ambiguous/problematic families:

- `DIAGNOSE`
- `REVISE`
- `ENGINEER`

Each family gets two new development cases whose user prompts avoid explicitly requesting the target behavior.

Three conditions are generated:

- `CONTROL` — neutral reasoning core only;
- `ATTENTION` — CONTROL plus a generic extra quality-control pass;
- `TARGET` — CONTROL plus the family-specific capability module.

The experiment separately measures:

1. **behavior manipulation:** did TARGET actually increase expression of the intended capability relative to CONTROL?
2. **quality effect:** did TARGET improve reasoning quality?
3. **specificity:** did TARGET outperform generic ATTENTION?

A separate blinded behavior judge scores target-behavior expression from 0–4. A separate blinded quality judge compares reasoning outcomes without being shown the target-behavior definition.

Both behavior and quality judgments are repeated with randomized A/B orientation.

Predeclared identification gate:

`mean behavior lift = TARGET - CONTROL >= 0.5`

If a family fails this gate, its quality difference is considered **non-identifying** for capability value.

Default calibration settings:

- 3 target-generation replicates per case/condition;
- 3 quality votes per generated pair;
- 3 behavior votes per TARGET-vs-CONTROL generated pair.

See `docs/CAPABILITY_IDENTIFICATION_V0_7.md`.

## Coupled systems

The project maintains two coupled systems:

1. **Reasoning engine** — the protocol and component hypotheses under test.
2. **Evaluation engine** — adversarial measurement intended to falsify, refine, or reject those hypotheses.

Protocol compliance is not evidence of improved reasoning by itself.

## Validation boundary

All v0.5, v0.6.x, and v0.7 cases are development/calibration evidence.

Framework validation requires, after prompts and component definitions are frozen:

1. fresh held-out cases not used in prompt or benchmark development;
2. multiple stochastic target generations per case;
3. repeated blinded judgments;
4. preferably a judge model independent of the target model;
5. predeclared primary effects and interpretation thresholds.

Only after that should the project return to Adaptive routing and reasoning-cost optimization.

## Cost policy

Target token usage and latency are recorded as descriptive diagnostics only. They do not enter current quality or component-identification decisions.

Later, cost becomes a constrained optimization problem:

> Minimize reasoning cost subject to preserving the quality of the validated best reasoning process within a predefined tolerance.

## Model provider

Canonical runtime: Z.AI OpenAI-compatible Chat Completions.

Default endpoint:

`https://api.z.ai/api/coding/paas/v4`

Default target model:

`glm-5.1`

The evaluator can use a different key/model/endpoint; independent evaluation remains a future requirement for strong validation claims.

## Research discipline

The framework should be revised or rejected when evidence contradicts its claimed benefits.

The governing research loop is the framework applied to itself:

**Observe benchmark failures → Diagnose → Derive → Hypothesize changes → Predict improvements → Test → Revise → Engineer**

The immediate objective is **reproducibly better reasoning quality with experimentally identified mechanisms**, not lower token cost.
