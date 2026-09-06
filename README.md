# Reasoning Engine

An experimental reasoning-control architecture for moving from observations to justified interventions while explicitly managing causal uncertainty, evidence, revision, and engineering consequences.

## Core protocol

For substantial non-trivial problems:

**Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**

Compact ablation:

**Problem → First Principle → Mechanism → Evidence → Solution**

An adaptive routing layer also exists experimentally, but routing is currently **deferred from the primary research question**.

## Current research question

The operating protocol is specified, but its value as an agent controller remains an empirical hypothesis.

The project is currently testing:

> **Does the reasoning protocol produce better reasoning quality than an uncontrolled baseline?**

The research hierarchy is now explicit:

1. **Quality first** — establish whether FULL reasoning improves epistemic and decision outcomes.
2. **Reliability second** — establish whether any quality advantage reproduces across cases, generations, and evaluators.
3. **Cost third** — only after a credible quality advantage exists, optimize reasoning cost while preserving that quality.

Token count, latency, and routing efficiency are not primary outcomes in the current phase.

## Why the focus changed

Pilot 001 and Measurement v0.3 showed directional differences between BASELINE, COMPACT, FULL, and ADAPTIVE, but also exposed scalar-score ceiling effects and stochastic pairwise judging.

Routing v0.4 then showed that identical response pairs could receive materially different pairwise verdicts on repeated evaluation. That makes evaluator reliability a prerequisite for further controller optimization.

Measurement v0.5 therefore returns to the core theory and removes Adaptive routing from the primary experiment.

See:

- `docs/OPERATING_PROTOCOL.md` — canonical reasoning protocol;
- `docs/PILOT_001_RESULTS.md` — first empirical pilot;
- `docs/MEASUREMENT_V0_3.md` — hardened evaluator and stress suite;
- `docs/ROUTING_V0_4_CANDIDATE.md` — routing candidate, retained as a later optimization layer;
- `docs/QUALITY_MEASUREMENT_V0_5.md` — current quality-first measurement design.

## Coupled systems

The project maintains two coupled systems:

1. **Reasoning engine** — the protocol and controller under test.
2. **Evaluation engine** — adversarial benchmarks intended to falsify, refine, or reject the reasoning claims.

Protocol compliance is not evidence of improved reasoning by itself.

## Current experimental conditions

Quality Measurement v0.5 evaluates only:

- `BASELINE` — no reasoning controller;
- `COMPACT` — Problem → First Principle → Mechanism → Evidence → Solution;
- `FULL` — Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer.

The primary comparison is:

**FULL vs BASELINE**

Secondary ablations are:

- **COMPACT vs BASELINE**;
- **FULL vs COMPACT**.

`ADAPTIVE` is intentionally excluded from quality promotion evidence. It is an efficiency/control layer to revisit only after the underlying reasoning-quality effect is established.

## Quality Measurement v0.5

The quality judge evaluates substantive reasoning only, including correctness, causal/mechanistic accuracy, evidence discrimination, revision, uncertainty calibration, assumptions, constraints, and decision/intervention quality when applicable.

The judge is explicitly told not to reward shorter or cheaper answers.

Each response pair receives repeated blinded votes with independently randomized A/B orientation. The report exposes vote agreement and non-unanimous cases rather than silently treating one stochastic verdict as ground truth.

The initial v0.5 calibration uses the existing 12 `pilot + stress` cases, one target-generation replicate, and three judge votes per pair. Because those cases have already influenced framework development, this run is **calibration, not validation**.

Fresh held-out cases and preferably an evaluator model independent of the target model are required for framework validation.

## Cost policy

Target token usage and latency are still recorded, but only as descriptive diagnostics.

They do **not** enter:

- the quality judge prompt;
- the pairwise quality score;
- the primary promotion criterion.

Cost optimization is a later constrained problem:

> Minimize reasoning cost subject to preserving the quality of the validated best reasoning process within a predefined tolerance.

## Model provider: Z.AI

The canonical runtime uses Z.AI through its OpenAI-compatible Chat Completions protocol.

Default endpoint:

`https://api.z.ai/api/coding/paas/v4`

Default model:

`glm-5.1`

The evaluator can use a different model, API key, and base URL. Configure optional `ZAI_JUDGE_API_KEY` for a separate judge credential; if absent it falls back to `ZAI_API_KEY`.

See `docs/ZAI_PROVIDER.md` for provider details.

## Run Quality Measurement v0.5

In GitHub Actions, open **Reasoning Quality Measurement v0.5** and use the calibration defaults:

- suite: `combined`;
- generation replicates: `1`;
- judge votes: `3`;
- target model: `glm-5.1`;
- judge model: `glm-5.1` unless an independent evaluator is available.

The workflow writes checkpointed artifacts under `benchmark/results_v05/`:

- `v05_runs.jsonl`;
- `v05_judge_votes.jsonl`;
- `v05_report.json` when the full run completes.

API keys must never be committed to the repository.

## Research discipline

The framework should be revised or rejected when evidence contradicts its claimed benefits.

The governing research loop is the framework applied to itself:

**Observe benchmark failures → Diagnose → Derive → Hypothesize changes → Predict improvements → Test → Revise → Engineer**

The immediate objective is **reproducibly better reasoning quality**. Efficiency optimization comes later.
