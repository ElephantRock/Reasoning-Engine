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

### Absolute Behavior Identification v0.10

v0.10 removes pairwise behavior scoring as the manipulation measure and tests `TEST` and `ENGINEER` with independent absolute behavior judgments before quality interpretation.

Its role is component/control identification on development tasks, separate from framework-level held-out validation.

See `docs/ABSOLUTE_BEHAVIOR_IDENTIFICATION_V0_10.md`.

### Held-Out Framework Validation v1 — Tier-1B

The frozen FULL framework has now passed its preregistered held-out primary endpoint under a distinct same-family evaluator.

Design:

- 36 fresh held-out cases;
- 3 target-generation replicates per case/condition;
- 3 blinded randomized judge votes per generated pair;
- target `glm-5.1`;
- judge `glm-5.3-flash`;
- same GLM family and Z.AI provider.

Primary FULL vs CONTROL result:

- score: **`0.6898`**;
- 95% case-clustered CI: **`0.6096–0.7685`**;
- case-level direction: `26` wins / `2` ties / `8` losses;
- preregistered statistical threshold: passed;
- preregistered task-stratum robustness floor: passed;
- **`validation_pass = true`** for this Tier-1B evaluation.

Secondary results:

- COMPACT vs CONTROL: `0.5864`, CI `0.5077–0.6667`; secondary success rule failed because the point estimate did not reach `0.60`;
- FULL vs COMPACT: **`0.5957`**, CI **`0.5417–0.6543`**; preregistered direction favored FULL.

The effect is heterogeneous rather than universal:

- ENGINEER stratum: FULL vs CONTROL `0.9012`;
- TEST stratum: `0.7901`;
- BOTH: `0.6296`;
- NONE: `0.4861`;
- cases requiring action: `0.7375`;
- cases not requiring action: `0.4921`.

Interpretation: the frozen FULL protocol improves held-out reasoning quality on average relative to an uncontrolled baseline under a distinct same-family judge, with strongest value on test- and engineering-oriented tasks. This does not establish that full-depth explicit reasoning is beneficial on every task.

The source execution encountered a judge JSON-format failure. Recovery preserved all 324 target outputs, retained 369 valid votes, completed only the 603 missing preregistered votes, regenerated zero target outputs, and produced the complete 972-vote report.

See `docs/HELDOUT_FRAMEWORK_VALIDATION_V1_GLM53FLASH_RESULTS.md`.

## Coupled systems

The project maintains two coupled systems:

1. **Reasoning engine** — the protocol and control hypotheses under test.
2. **Evaluation engine** — adversarial measurement intended to falsify, refine, or reject those hypotheses.

Protocol compliance is not evidence of improved reasoning by itself.

## Validation boundary

Development/calibration evidence remains separate from held-out evidence.

The project now has a positive **Tier-1B cross-model, same-family held-out result** for FULL vs CONTROL. Because the evaluator is `glm-5.3-flash` while the target is `glm-5.1`, the result is stronger than same-model judging, but it is **not independent-provider or independent-family validation**.

The next strongest validation step is:

1. preserve the frozen held-out design and result;
2. evaluate with a genuinely independent model family/provider when credentials are available, preferably with a human-reviewed subset;
3. replicate framework-level effects across target model families/capability levels;
4. use the observed heterogeneity to formulate a preregistered selective-control/routing hypothesis without tuning on the held-out suite;
5. only then optimize reasoning cost subject to preserving validated quality.

The existing 36-case held-out suite is now exposed and must not be reused as a fresh holdout for prompt tuning.

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

The Tier-1B held-out evaluator was `glm-5.3-flash` on the same provider. Independent-family/provider evaluation remains required for a stronger validation claim.

## Research discipline

The framework should be revised or rejected when evidence contradicts its claimed benefits.

The governing research loop is the framework applied to itself:

**Observe benchmark failures → Diagnose → Derive → Hypothesize changes → Predict improvements → Test → Revise → Engineer**

The immediate objective is now **replicate the held-out framework effect under independent evaluation and identify when FULL depth adds value**, before returning to routing or cost optimization.
