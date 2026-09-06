# Quality Measurement v0.5 — Calibration Results

## Provenance

- Workflow: `Reasoning Quality Measurement v0.5`
- Run ID: `34004295451`
- Commit: `3747062335d41001e0f98f3104168a8cdc968cee`
- Suite: `combined` (12 pilot + stress cases)
- Generation replicates: 1
- Judge votes per pair: 3
- Target: Z.AI `glm-5.1`
- Judge: Z.AI `glm-5.1`
- Target/judge endpoint: `https://api.z.ai/api/coding/paas/v4`
- Artifact ID: `9982051100`
- Artifact SHA256: `b438155486aecd0e2d0d11213f0a2f5dd447a6111d443a1b1e822728d399cd1a`

This run is a **calibration**, not framework validation. The 12 cases had already influenced framework development, and target and judge used the same model and endpoint.

## Primary: FULL vs BASELINE

- Pairwise score: **0.7778**
- 95% case-clustered bootstrap interval: **0.5833–0.9444**
- Majority outcomes: **8 wins / 3 ties / 1 loss**
- Mean repeated-vote agreement: **0.9722**
- Unanimous fraction: **0.9167**

Only `RF-C01` was non-unanimous (2 FULL votes, 1 tie).

Case scores:

- RF-A02: 1.0
- RF-B01: 1.0
- RF-C01: 0.8333
- RF-D01: 1.0
- RF-E04: 1.0
- RF-F01: 0.5
- RF-S01: 0.5
- RF-S02: 1.0
- RF-S03: 1.0
- RF-S04: 0.5
- RF-S05: 0.0
- RF-S06: 1.0

Interpretation: explicit structured reasoning shows a strong directional quality advantage over baseline on these development cases, with high evaluator agreement.

## Ablation: COMPACT vs BASELINE

- Pairwise score: **0.8056**
- 95% interval: **0.6250–0.9583**
- Majority outcomes: **9 wins / 1 tie / 2 losses**
- Mean vote agreement: **0.9167**
- Unanimous fraction: **0.7500**

Interpretation: the lighter Compact scaffold also shows a strong directional quality advantage over baseline.

## Depth ablation: FULL vs COMPACT

- Pairwise score: **0.5833**
- 95% interval: **0.4167–0.7500**
- Majority outcomes: **6 wins / 3 ties / 3 losses**
- Mean vote agreement: **0.8333**
- Unanimous fraction: **0.5000**

Interpretation: v0.5 does **not** establish that the full eight-stage protocol is superior to Compact. The next question is which additional capabilities contribute marginal quality beyond Compact.

## Cost diagnostics

Cost did not enter the judge prompt or quality metric.

- BASELINE output tokens: 50,081
- COMPACT output tokens: 42,200
- FULL output tokens: 40,137

These values are descriptive only and should not drive the current stage-ablation research question.

## Next experiment

Measurement v0.6 should isolate marginal stage contributions by starting from the identical Compact prompt and adding one capability at a time, evaluated on cases where that capability is decision-relevant. A generic extra-attention control should distinguish stage-specific value from the effect of simply adding more prompting/checking.
