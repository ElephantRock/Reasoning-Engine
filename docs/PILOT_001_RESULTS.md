# Pilot 001 — Z.AI GLM-5.1

## Provenance

- GitHub Actions run: `33895215844`
- Workflow: `Reasoning Benchmark Pilot`
- Repository commit: `987a964cba050f2c676318aa9029e87f7de7f2ff`
- Target model: `glm-5.1`
- Judge model: `glm-5.1`
- Endpoint: `https://api.z.ai/api/coding/paas/v4`
- Cases: 6
- Conditions: BASELINE, COMPACT, FULL, ADAPTIVE
- Artifact ID: `9947872606`
- Artifact SHA-256: `ddc3bfb71d739812f20fb5ad5bdc4c994e02f29e2735bf31b718d55a3f1e02f7`

The workflow completed successfully and uploaded all three expected result files.

## Summary

| Condition | Quality / 4 | Protocol / 4 | Pairwise vs Baseline | Output tokens |
|---|---:|---:|---:|---:|
| BASELINE | 3.9792 | 3.8101 | — | 27,413 |
| COMPACT | 4.0000 | 3.9526 | 2W / 2T / 2L | 18,219 |
| FULL | 3.9940 | 3.9838 | 3W / 1T / 2L | 23,400 |
| ADAPTIVE | 3.9792 | 3.9703 | 3W / 2T / 1L | 25,198 |

Target-generation latency totals reported by the run:

- BASELINE: 446,155 ms
- COMPACT: 323,995 ms
- FULL: 399,800 ms
- ADAPTIVE: 452,928 ms

## Directional observations

1. **Compact was the most efficient condition in this pilot.** It used materially fewer output tokens than baseline while preserving strong judged quality.
2. **Full achieved the highest protocol-behavior score** but did not clearly dominate Compact on answer quality.
3. **Adaptive had the strongest pairwise record against baseline** (3 wins, 2 ties, 1 loss), but routing was not explicitly scored in Pilot 001.
4. The adaptive router selected COMPACT for RF-C01 even though the case gold label was FULL, exposing a routing-calibration issue.
5. Scalar quality scores were nearly ceiling-saturated (3.979–4.000), so they do not provide enough discrimination to serve as the primary metric.
6. The target and evaluator were the same model (`glm-5.1`), so the pilot does not provide evaluator-independent evidence.

## Protocol violations observed

- BASELINE: P01 premature solutioning; P12 hidden critical assumption.
- COMPACT: none detected.
- FULL: one P09 evidence-free-confidence/calibration instance.
- ADAPTIVE: none detected.

## Interpretation boundary

Pilot 001 validates the end-to-end experiment plumbing and provides directional evidence only. Six cases, one stochastic realization, same-model judging, and a saturated scalar judge are insufficient to validate the Reasoning Engine.

These limitations motivate Measurement v0.3.
