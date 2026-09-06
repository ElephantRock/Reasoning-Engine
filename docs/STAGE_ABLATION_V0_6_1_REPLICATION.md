# Stage Ablation v0.6.1 — Frozen 3x Replication

## Purpose

This replication tests whether the first v0.6.1 leave-one-capability-out signals are stable across target-generation stochasticity.

The reasoning protocol, ablation definitions, case set, evaluator prompt, and aggregation logic are **frozen** from v0.6.1. No protocol component is revised in response to the first-run results before this replication.

## Frozen design

Runner: `benchmark/run_v061.py`

Cases: the same 10 development/calibration cases in `benchmark/stage_ablation_cases_v06.json`, two each for:

- DIAGNOSE
- PREDICT
- TEST
- REVISE
- ENGINEER

Comparison for every case:

**FULL vs FULL-minus-target-capability**

Replication settings:

- target model: `glm-5.1`
- judge model: `glm-5.1`
- target endpoint: `https://api.z.ai/api/coding/paas/v4`
- judge endpoint: `https://api.z.ai/api/coding/paas/v4`
- target-generation replicates: **3**
- blinded judge votes per generated pair: **3**

Target and judge remain the same model and endpoint, so this is still component calibration rather than evaluator-independent validation.

## Primary replication question

Does the direction and magnitude of the v0.6.1 component signal persist when generation variability is sampled explicitly?

The first v0.6.1 run produced directional stage scores:

- DIAGNOSE: `0.000`
- PREDICT: `0.833`
- TEST: `0.917`
- REVISE: `0.833`
- ENGINEER: `0.750`

These values are motivation for replication, **not tuning targets**.

## Interpretation discipline

Analyze the 3-replicate run both:

1. **on its own** as an exact replication; and
2. **combined with the original one-replicate run**, treating generation replicates within the same case as repeated measurements rather than independent benchmark cases.

For judge reliability, preserve `(case_id, generation_replicate)` boundaries before averaging across generation replicates.

Do not revise or remove DIAGNOSE merely because the original two cases favored the ablated prompt. A negative Diagnose claim requires the direction to persist across new generation replicates and should later be challenged on fresh cases.

Likewise, positive signals for PREDICT, TEST, REVISE, or ENGINEER remain calibration evidence until reproduced on fresh held-out cases with a preferably independent evaluator.

## Cost policy

Token use and latency remain descriptive diagnostics only. They do not enter the reasoning-quality judgment or component-effect criterion.
