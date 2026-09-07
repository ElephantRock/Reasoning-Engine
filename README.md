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
3. **When a behavior is successfully induced or recovered, does it improve reasoning quality?**
4. **Under what conditions does explicit control add value rather than redundant prompting?**
5. **Do those effects replicate across cases, generations, model families, and independent evaluators?**
6. **Only then: can the validated process be routed or compressed more cheaply?**

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

Inspection revealed the key identification problem:

**removing an instruction does not necessarily remove the capability.**

The task wording and model priors could still elicit diagnosis, revision, or engineering. Therefore v0.6.1 primarily measured the marginal effect of mentioning instruction fragments, not the causal value of the underlying capability.

See `docs/ABLATION_V0_6_1_REPLICATION_RESULTS.md`.

### Capability Identification v0.7

v0.7 separated behavior manipulation from quality.

Three conditions were compared:

- `CONTROL` — neutral reasoning core;
- `ATTENTION` — CONTROL plus a generic extra quality-control pass;
- `TARGET` — CONTROL plus a family-specific capability module.

A separate blinded behavior judge measured whether TARGET actually increased target-behavior expression before quality effects were interpreted.

Predeclared manipulation gate:

`TARGET behavior - CONTROL behavior >= 0.5` on a 0–4 scale.

Results:

- `ENGINEER`: behavior lift `+1.00`, gate **passed**; TARGET vs CONTROL quality `1.000`; TARGET vs ATTENTION `0.833`.
- `DIAGNOSE`: behavior lift `+0.22`, gate **failed** because CONTROL was already near ceiling.
- `REVISE`: behavior lift `+0.11`, gate **failed** because CONTROL was already near ceiling.

Interpretation: `ENGINEER` currently has positive instruction-mediated evidence. Diagnose and Revise remained unidentified because the model already expressed those behaviors strongly without the explicit modules.

See `docs/CAPABILITY_IDENTIFICATION_V0_7.md`.

### Capability Screening v0.8

v0.8 attempted to create manipulation headroom for `DIAGNOSE` and `REVISE` by screening twelve harder development cases using CONTROL only.

Predeclared eligibility required:

`CONTROL behavior <= 2.5/4`

with at least one point of headroom.

Observed CONTROL behavior:

- Diagnose cases: approximately `3.83–4.00`;
- Revise cases: `4.00` across all six candidates.

Result:

- `0/6` Diagnose cases eligible;
- `0/6` Revise cases eligible;
- Stage 2 correctly did not run.

Interpretation: on these development tasks, `glm-5.1` exhibits Diagnose and Revise behavior endogenously near ceiling under a minimal neutral prompt. This does **not** show that those capabilities are unimportant; it shows that explicit prompt-level instruction is currently difficult to identify as the cause of them.

The resulting distinction is central:

**reasoning capability ≠ reasoning instruction**

## Selective Control v0.9

The current experiment changes the research question from:

> Does the model possess the capability?

to:

> **When adverse context suppresses endogenous reasoning, does explicit control recover the capability and improve quality beyond generic extra attention?**

v0.9 uses six base problems, two each for:

- `DIAGNOSE`
- `REVISE`
- `ENGINEER`

Each base problem has paired variants:

- `CLEAN` — decisive evidence with little distraction;
- `STRESS` — the same decisive evidence and correct action plus authority anchors, irrelevant metrics, conflicting stakeholder pressure, historical analogies, time pressure, or familiar-action bias.

The production reasoning protocol is unchanged. Target modules are frozen byte-for-byte from v0.7.

Two behavioral gates must pass before stress-condition quality effects are interpreted:

1. **Stress gate:** `CLEAN CONTROL - STRESS CONTROL >= 0.5`
2. **Recovery gate:** `STRESS TARGET - STRESS CONTROL >= 0.5`

Only then are the following treated as selective-control evidence:

- `TARGET vs CONTROL` under stress;
- `TARGET vs ATTENTION` under stress;
- `ATTENTION vs CONTROL` under stress.

This tests a controller hypothesis:

**detect reasoning-risk condition → activate relevant capability control → verify outcome**

rather than forcing every stage on every problem.

See `docs/SELECTIVE_CONTROL_V0_9.md`.

## Coupled systems

The project maintains two coupled systems:

1. **Reasoning engine** — the protocol and control hypotheses under test.
2. **Evaluation engine** — adversarial measurement intended to falsify, refine, or reject those hypotheses.

Protocol compliance is not evidence of improved reasoning by itself.

## Validation boundary

All v0.5–v0.9 cases are development/calibration evidence.

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
