# Reasoning Engine

An experimental reasoning-control architecture for moving from observations to justified interventions while explicitly managing causal uncertainty, evidence, revision, and engineering consequences.

## Core protocol

For substantial non-trivial problems:

**Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**

Compact scaffold:

**Problem → First Principle → Mechanism → Evidence → Solution**

An adaptive routing layer also exists experimentally, but routing is currently **deferred from the primary research question**.

## Current research question

The project is now testing two questions in sequence:

1. **Does explicit structured reasoning improve reasoning quality relative to an uncontrolled baseline?**
2. **Which additional capabilities in the full protocol add marginal quality beyond Compact?**

The research hierarchy is:

1. **Quality first** — establish the reasoning-quality effect.
2. **Component value second** — identify which reasoning capabilities cause the marginal gain.
3. **Reliability third** — reproduce effects across cases, generations, and evaluators.
4. **Cost last** — optimize reasoning cost only after the quality-producing process is understood.

Token count, latency, and routing efficiency are not primary outcomes in the current phase.

## Current evidence

Quality Measurement v0.5 used 12 existing pilot + stress cases, one target-generation replicate, and three repeated blinded judge votes per response pair.

Directional calibration results:

- **FULL vs BASELINE:** score `0.7778`, 95% case-bootstrap interval `0.5833–0.9444`, 8 wins / 3 ties / 1 loss, mean vote agreement `0.9722`.
- **COMPACT vs BASELINE:** score `0.8056`, interval `0.6250–0.9583`, 9 wins / 1 tie / 2 losses.
- **FULL vs COMPACT:** score `0.5833`, interval `0.4167–0.7500`, 6 wins / 3 ties / 3 losses.

Interpretation: structured reasoning shows a strong quality signal over baseline on these development cases, but v0.5 does **not** establish that the full eight-stage protocol is superior to Compact.

See `docs/QUALITY_V0_5_RESULTS.md` for exact provenance and interpretation boundaries.

## Measurement v0.6 — stage ablation

v0.6 asks which additional capabilities add marginal quality beyond Compact.

Each `TARGETED` treatment starts from the **identical Compact prompt** and adds exactly one capability:

- `DIAGNOSE` — competing causal explanations and causal-level distinction;
- `PREDICT` — prospective mechanism-specific predictions;
- `TEST` — discriminating/falsifying evidence;
- `REVISE` — explicit model updating after contradiction;
- `ENGINEER` — mechanism-linked intervention design under constraints, robustness, reversibility, feedback, and second-order effects.

Each stage has two dedicated development/calibration cases in `benchmark/stage_ablation_cases_v06.json`.

Four conditions are generated per case:

- `COMPACT` — unchanged Compact scaffold;
- `ATTENTION` — Compact plus a generic extra quality-control pass;
- `TARGETED` — Compact plus the case-relevant capability instruction;
- `FULL` — the complete protocol, used only as a ceiling/headroom diagnostic.

Primary comparisons:

1. **TARGETED vs COMPACT** — marginal component effect;
2. **TARGETED vs ATTENTION** — stage specificity beyond generic extra checking;
3. **FULL vs TARGETED** — residual headroom of the full protocol;
4. **ATTENTION vs COMPACT** — generic-attention control effect.

Each pair receives repeated blinded quality-only votes with independently randomized A/B orientation. Cost remains outside the quality score.

See `docs/STAGE_ABLATION_V0_6.md` for the full design.

## Coupled systems

The project maintains two coupled systems:

1. **Reasoning engine** — the protocol and component hypotheses under test.
2. **Evaluation engine** — adversarial benchmarks intended to falsify, refine, or reject those hypotheses.

Protocol compliance is not evidence of improved reasoning by itself.

## Validation boundary

The current v0.5 and v0.6 cases are development/calibration cases, not final held-out validation.

Framework validation will require, after prompts and component definitions are frozen:

1. fresh held-out cases not used in prompt or benchmark development;
2. multiple stochastic target generations per case;
3. repeated blinded judgments;
4. preferably a judge model independent of the target model;
5. predeclared primary effects and interpretation thresholds.

Only after component value is understood should the project return to Adaptive routing and reasoning-cost optimization.

## Cost policy

Target token usage and latency are still recorded as descriptive diagnostics.

They do **not** enter:

- the quality judge prompt;
- pairwise quality scores;
- current component promotion decisions.

Later, cost becomes a constrained optimization problem:

> Minimize reasoning cost subject to preserving the quality of the validated best reasoning process within a predefined tolerance.

## Model provider: Z.AI

The canonical runtime uses Z.AI through its OpenAI-compatible Chat Completions protocol.

Default endpoint:

`https://api.z.ai/api/coding/paas/v4`

Default model:

`glm-5.1`

The evaluator can use a different model, API key, and base URL. Configure optional `ZAI_JUDGE_API_KEY` for a separate judge credential; if absent it falls back to `ZAI_API_KEY`.

See `docs/ZAI_PROVIDER.md` for provider details.

## Run Measurement v0.6

In GitHub Actions, open **Reasoning Stage Ablation v0.6** and use the calibration defaults:

- generation replicates: `1`;
- judge votes: `3`;
- target model: `glm-5.1`;
- judge model: `glm-5.1` unless an independent evaluator is available.

The workflow writes artifacts under `benchmark/results_v06/`:

- `v06_runs.jsonl`;
- `v06_judge_votes.jsonl`;
- `v06_report.json` when the full run completes.

API keys must never be committed to the repository.

## Research discipline

The framework should be revised or rejected when evidence contradicts its claimed benefits.

The governing research loop is the framework applied to itself:

**Observe benchmark failures → Diagnose → Derive → Hypothesize changes → Predict improvements → Test → Revise → Engineer**

The immediate objective is **reproducibly better reasoning quality and an evidence-based account of which components produce it**. Efficiency optimization comes later.
