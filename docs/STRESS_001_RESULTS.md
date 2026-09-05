# Stress Measurement 001 — v0.3

## Provenance

- GitHub Actions run: `33970402321`
- Commit: `796b00a9885c52ac970a75727808361cff443e28`
- Suite: `stress`
- Replicates: `1`
- Target: Z.AI `glm-5.1`
- Judge: Z.AI `glm-5.1`
- Endpoint: `https://api.z.ai/api/coding/paas/v4`
- Artifact: `reasoning-benchmark-v03-33970402321`
- Artifact SHA-256: `11615cdb37f9daa8884799b4b72d47f5dddef4fee747f492f6318f567fb82a39`

Target and judge used the same model and endpoint, so the result is not evaluator-independent.

## Primary results

Blinded pairwise score against BASELINE uses win=1, tie=0.5, loss=0.

| Condition | W/T/L | Score | 95% case-bootstrap CI | Output tokens |
| --- | --- | ---: | ---: | ---: |
| COMPACT | 2 / 0 / 4 | 0.333 | 0.000–0.667 | 16,014 |
| FULL | 4 / 1 / 1 | 0.750 | 0.417–1.000 | 21,821 |
| ADAPTIVE | 3 / 3 / 0 | 0.750 | 0.583–0.917 | 21,053 |
| BASELINE | reference | 0.500 | — | 19,130 |

Secondary scalar quality remained relatively compressed:

- BASELINE: 3.8754
- COMPACT: 3.8770
- FULL: 3.8829
- ADAPTIVE: 3.8794

This reinforces the decision to treat scalar scores as secondary.

## Case-level pairwise result

| Case | COMPACT vs Baseline | FULL vs Baseline | ADAPTIVE vs Baseline |
| --- | --- | --- | --- |
| RF-S01 | Win | Win | Win |
| RF-S02 | Loss | Win | Tie |
| RF-S03 | Loss | Loss | Tie |
| RF-S04 | Win | Win | Win |
| RF-S05 | Loss | Win | Win |
| RF-S06 | Loss | Tie | Tie |

## Routing observation

The legacy gold-mode score marked ADAPTIVE correct on only 3/6 cases. The apparent errors were:

- RF-S01: selected COMPACT; legacy expected FULL; Adaptive still beat Baseline.
- RF-S04: selected DIRECT; legacy expected COMPACT; Adaptive still beat Baseline.
- RF-S06: selected COMPACT; legacy expected FULL; Adaptive tied Baseline.

Therefore exact agreement with hand-authored mode labels is not a reliable routing objective by itself.

The stronger routing objective suggested by this run is:

> choose the shallowest reasoning depth that preserves decision quality relative to deeper available reasoning.

This motivates Routing v0.4.

## Replication status

Because this result is based on one stochastic replicate, an exact rerun of the same v0.3 job was initiated before promoting the v0.4 router. Do not treat this document as validation of the framework.
