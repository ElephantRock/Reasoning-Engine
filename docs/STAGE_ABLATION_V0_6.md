# Measurement v0.6 — Stage Ablation

## Research question

The v0.5 calibration supports a directional claim that explicit structured reasoning improves quality relative to baseline, but it did not establish that FULL is better than COMPACT.

v0.6 therefore asks:

> **Which additional reasoning capabilities add marginal reasoning quality beyond Compact?**

The stage-ablation program is intentionally about **quality**, not routing or reasoning cost.

## Experimental unit

The base treatment is the existing Compact prompt:

**Problem → First Principle → Mechanism → Evidence → Solution**

Each `TARGETED` treatment is the **identical Compact prompt plus exactly one capability instruction**:

1. `DIAGNOSE` — maintain materially plausible competing explanations and distinguish symptom/proximate/root cause where relevant.
2. `PREDICT` — derive prospective, mechanism-specific observable consequences before using test outcomes.
3. `TEST` — prefer discriminating/falsifying evidence and specify how outcomes update the model.
4. `REVISE` — explicitly update beliefs/mechanisms/recommendations when evidence contradicts the prior model.
5. `ENGINEER` — compare mechanism-linked interventions under constraints, robustness, reversibility, feedback, side effects, and monitoring.

## Control conditions

Each case is generated under four conditions:

- `COMPACT` — unmodified Compact prompt.
- `ATTENTION` — Compact plus a generic extra quality-control pass; this controls for the effect of simply adding more prompting/checking.
- `TARGETED` — Compact plus the one stage-specific capability relevant to the case family.
- `FULL` — the existing full eight-stage protocol; retained only as a ceiling/headroom diagnostic.

## Cases

`benchmark/stage_ablation_cases_v06.json` contains 10 new development/calibration cases, two per capability family.

These cases are **not future held-out validation cases**. They were deliberately designed to stress the ablated components and may be used to refine the component definitions.

## Pairwise comparisons

Each response pair receives repeated blinded quality-only votes with independently randomized A/B orientation.

Primary comparisons:

1. `TARGETED_vs_COMPACT` — marginal component effect.
2. `TARGETED_vs_ATTENTION` — stage specificity beyond generic extra checking.
3. `FULL_vs_TARGETED` — residual headroom of the complete protocol over the isolated stage augmentation.
4. `ATTENTION_vs_COMPACT` — generic-attention control effect.

The primary stage-effect question is answered by `TARGETED_vs_COMPACT`, with `TARGETED_vs_ATTENTION` guarding against the confound that any extra instruction improves performance.

## Measurement

The evaluator judges reasoning quality only. It does not receive token cost as a criterion.

Priority dimensions include:

- factual correctness;
- observation/inference/causal separation;
- substantive success on the case-specific target capability;
- mechanism quality;
- discriminating evidence and prospective predictions where relevant;
- revision under contradiction;
- uncertainty calibration;
- decision/intervention robustness.

The report includes:

- overall pairwise score;
- case-clustered bootstrap interval;
- majority wins/ties/losses;
- repeated-vote agreement;
- per-stage family breakdown;
- cost diagnostics kept separate from quality.

## Interpretation discipline

A stage is not established as useful merely because its prompt contains more instructions.

Evidence for marginal value is stronger when:

- `TARGETED` beats `COMPACT` on stage-relevant cases;
- `TARGETED` also beats or matches `ATTENTION`;
- repeated judge votes are stable;
- the effect appears across both cases in that family;
- `FULL` has little remaining headroom, suggesting the isolated capability captures the relevant advantage.

A null or negative result can mean the capability is redundant with Compact, poorly operationalized, unnecessary for those cases, or harmful through over-reasoning. These possibilities should be diagnosed before changing the canonical protocol.

## Validation boundary

v0.6 remains **component calibration**. Framework validation requires, after prompts are frozen:

1. fresh held-out cases not used in prompt or benchmark development;
2. multiple stochastic target generations per case;
3. repeated blinded judgments;
4. preferably an evaluator model independent of the target model;
5. predeclared primary effects and interpretation thresholds.

Only after component value is understood should the project return to Adaptive routing and reasoning-cost optimization.
