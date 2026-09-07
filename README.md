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

1. **Does structured reasoning improve reasoning quality relative to an uncontrolled baseline?**
2. **Which explicit controls reliably change reasoning behavior beyond the model's endogenous capability?**
3. **When a behavior is successfully induced, does it improve reasoning quality?**
4. **Under what conditions does explicit control add value rather than redundant prompting?**
5. **Do those effects replicate across cases, generations, model families, and independent evaluators?**
6. **Only then: can the validated process be routed or compressed more cheaply?**

Quality is primary. Token count and latency remain descriptive diagnostics only.

## Evidence so far

### Quality Measurement v0.5

On 12 development/calibration cases:

- **FULL vs BASELINE:** `0.7778`, 95% case-bootstrap interval `0.5833–0.9444`, 8 wins / 3 ties / 1 loss.
- **COMPACT vs BASELINE:** `0.8056`, interval `0.6250–0.9583`, 9 wins / 1 tie / 2 losses.
- **FULL vs COMPACT:** `0.5833`, interval `0.4167–0.7500`, 6 wins / 3 ties / 3 losses.

Interpretation: structured reasoning shows a strong quality signal over baseline on development cases, but the full eight-stage protocol has not been shown superior to Compact.

See `docs/QUALITY_V0_5_RESULTS.md`.

### Stage Ablation v0.6.1 and replication

A leave-one-instruction-out experiment initially suggested several positive component effects, but a preregistered three-generation replication did not reproduce the original pattern.

Combined four-generation stage scores:

- `DIAGNOSE`: `0.375`
- `PREDICT`: `0.604`
- `TEST`: `0.729`
- `REVISE`: `0.458`
- `ENGINEER`: `0.292`

Combined overall score was approximately `0.492`.

The key identification problem was that deleting an instruction often did **not** remove the underlying capability. The task wording and model priors could still elicit diagnosis, revision, or engineering.

**Removing an instruction ≠ removing a capability.**

See `docs/ABLATION_V0_6_1_REPLICATION_RESULTS.md`.

### Capability Identification v0.7

v0.7 separated behavior manipulation from quality using `CONTROL`, generic `ATTENTION`, and capability-specific `TARGET` conditions.

Predeclared behavior gate:

`TARGET behavior - CONTROL behavior >= 0.5` on a 0–4 scale.

Results:

- `ENGINEER`: pairwise behavior lift `+1.00`, TARGET vs CONTROL quality `1.000`, TARGET vs ATTENTION `0.833`.
- `DIAGNOSE`: behavior lift `+0.22`; manipulation gate failed because CONTROL was already near ceiling.
- `REVISE`: behavior lift `+0.11`; manipulation gate failed because CONTROL was already near ceiling.

This made ENGINEER the strongest positive component candidate, while Diagnose and Revise remained unidentified.

See `docs/CAPABILITY_IDENTIFICATION_V0_7.md`.

### Capability Screening v0.8

v0.8 screened twelve harder Diagnose/Revise cases using CONTROL only to find behavioral headroom.

Eligibility required `CONTROL behavior <= 2.5/4` with at least one point of headroom.

Observed CONTROL behavior remained approximately `3.83–4.00` for Diagnose and `4.00` for all Revise cases. No cases were eligible, so Stage 2 correctly did not run.

This strengthened a central distinction:

**reasoning capability ≠ reasoning instruction**

On these development tasks, `glm-5.1` often performs Diagnose and Revise endogenously without explicit stage instructions.

### Selective Control v0.9

v0.9 tested whether adverse context would suppress endogenous reasoning and whether frozen capability modules could recover it.

The run produced all 108 target generations, all 108 absolute behavior votes, all 108 paired behavior votes, and 323/324 quality votes before the GitHub-hosted runner time limit cancelled final report synthesis. Every primary `TARGET_vs_CONTROL` and `TARGET_vs_ATTENTION` quality vote completed.

No family passed the preregistered stress-degradation gate:

- `DIAGNOSE`: clean CONTROL `3.556`, stress CONTROL `3.722`, stress drop `-0.167`;
- `REVISE`: `4.000 → 4.000`, stress drop `0.000`;
- `ENGINEER`: `4.000 → 3.778`, stress drop `0.222`.

Therefore v0.9 did **not** establish stress-triggered selective recovery.

Descriptive quality nevertheless replicated a strong ENGINEER signal:

- TARGET vs CONTROL clean: `1.000`;
- TARGET vs CONTROL stress: `0.972`;
- TARGET vs ATTENTION clean: `1.000`;
- TARGET vs ATTENTION stress: `1.000`.

v0.9 also revealed a measurement warning: side-by-side behavior judging sometimes scored CONTROL materially lower than independent absolute judging, indicating a plausible contrast effect.

See `docs/SELECTIVE_CONTROL_V0_9_RESULTS.md`.

## Absolute Behavior Identification v0.10

The current experiment removes pairwise behavior scoring as the manipulation measure.

It tests two families:

- `TEST` — the strongest unresolved positive directional signal from replicated v0.6.1;
- `ENGINEER` — the positive-control family from v0.7/v0.9.

Conditions remain:

- `CONTROL` — neutral v0.7 core;
- `ATTENTION` — generic extra quality-control pass;
- `TARGET` — CONTROL plus the frozen capability module.

Every generated response is behavior-scored **independently** three times. No behavior judge sees two conditions side by side. The manipulation quantity is computed only afterward:

`TARGET absolute behavior - CONTROL absolute behavior`

Predeclared identification gate:

`TARGET - CONTROL >= 0.5/4`

Quality remains repeated blinded pairwise evaluation for:

1. `TARGET_vs_CONTROL`;
2. `TARGET_vs_ATTENTION`;
3. `ATTENTION_vs_CONTROL`.

A family's quality result is interpreted as instruction-mediated capability evidence only if the independent absolute behavior gate passes.

Default run size is 4 cases × 3 conditions × 3 generations = 36 target generations, plus 108 single-response behavior judgments and 108 pairwise quality judgments. This is intentionally smaller than v0.9 to stay comfortably below hosted-runner limits.

See `docs/ABSOLUTE_BEHAVIOR_IDENTIFICATION_V0_10.md`.

## Coupled systems

The project maintains two coupled systems:

1. **Reasoning engine** — the protocol and control hypotheses under test.
2. **Evaluation engine** — adversarial measurement intended to falsify, refine, or reject those hypotheses.

Protocol compliance is not evidence of improved reasoning by itself.

## Validation boundary

All v0.5–v0.10 cases are development/calibration evidence.

Framework validation requires, after prompts and control policies are frozen:

1. fresh held-out cases not used in prompt or benchmark development;
2. multiple stochastic target generations per case;
3. repeated blinded judgments;
4. preferably a judge model independent of the target model;
5. replication across model families/capability levels;
6. predeclared primary effects and interpretation thresholds.

Only after that should the project return to Adaptive routing and reasoning-cost optimization.

## Cost policy

Target token usage and latency are descriptive diagnostics only. They do not enter current quality or control-identification decisions.

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

The immediate objective is **reproducibly better reasoning quality with experimentally identified control mechanisms**, not lower token cost.
