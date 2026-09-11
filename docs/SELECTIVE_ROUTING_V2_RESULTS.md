# Selective Routing v2 — Results

Status: **formally failed** under the frozen four-gate preregistration.

Source run: `34432326377`

Source commit: `ca20c4a9452a389057eb1d27b38ba781747c1102`

Final report artifact: `selective-routing-v2-report-34432326377`

Artifact SHA-256: `4380f339422c2b71377e763ec6936e936c2b09aabd7c0343b97a03f025ed2054`

Suite SHA-256: `0fc2c5e011e8731ca4435104b36fc66f327b7254b84b9c3a57a15f298c031682`

Evaluation tier: Tier-1B cross-model, same-family/provider; not independent-provider evaluation.

## Frozen gate results

| Gate | Frozen criterion | Observed | Result |
|---|---|---:|---|
| Framework replication | FULL vs CONTROL >= 0.60 and CI95 low > 0.50 | `0.6875`, CI `0.6273–0.7477` | PASS |
| Routed benefit | ROUTED vs CONTROL >= 0.60 and CI95 low > 0.50 | `0.6840`, CI `0.6262–0.7408` | PASS |
| Paired preservation | CI95 low of case-level `(ROUTED−CONTROL) − (FULL−CONTROL)` > -0.05 | delta `-0.00347`, CI `-0.02546–0.01273` | PASS |
| Selectivity | FULL invocation <= 0.65 | `34/48 = 0.7083` | **FAIL** |

Therefore:

`routing_utility_validation_pass = false`

No threshold is changed after exposure. v2 remains a failed validation.

## Secondary diagnostics

- Retained gain ratio: `0.98148`.
- Direct ROUTED vs FULL descriptive score: `0.49653`, CI `0.47569–0.51389`.
- Clear-stratum diagnostic routing accuracy: `1.0`.
- Boundary FULL rate: `22/24 = 0.9167`.
- Overall FULL rate: `34/48 = 0.7083`.
- All six shards and final aggregation completed successfully.

## What v2 establishes

The quality side of selective routing is now substantially better supported than after v1:

1. FULL again replicated over CONTROL on a fresh 48-case suite.
2. The routed policy retained nearly all observed FULL-over-CONTROL gain.
3. The paired non-inferiority criterion passed comfortably.
4. The unchanged v1 router was not selective enough on the harder boundary-heavy suite.

The failure is therefore a **selectivity failure**, not a framework-quality failure and not a preservation failure.

## Post-hoc development diagnosis

The following is explicitly post-hoc and may be used only to motivate later router development, never to reinterpret v2.

A simple confidence cutoff is not a satisfactory repair. On the exposed v2 cases, the first confidence cutoff that would bring FULL usage under the 0.65 cap (`>= 0.82`) also produces an estimated paired decrement too large to satisfy the frozen -0.05 preservation margin on that same exposed data. Confidence is therefore not treated as a calibrated marginal-value score.

Qualitative inspection suggests the v1 router over-selects FULL on a recurring class of **straightforward causal-confounding diagnoses**. These prompts contain multiple plausible causes and a consequential context, but the competent baseline can often reach the key answer with a simple pattern:

> do not attribute from timing/correlation; isolate the obvious alternatives with direct measurements or one straightforward comparison.

By contrast, the largest FULL gains more often occur when the answer requires nontrivial intervention choice, allocation, tradeoff analysis, reversible experimentation, or sequential model revision.

This motivates the v3 hypothesis:

`causal-looking task != marginal value from FULL`

and more specifically:

> Route FULL only when deep mechanism/engineering reasoning is likely to change the decision or action beyond what a competent unstructured answer would already produce; route CONTROL for obvious causal-caution/deconfounding tasks whose correct resolution is a direct check or single straightforward comparison.

The v2 suite is now exposed and must not be used as fresh validation for v3.