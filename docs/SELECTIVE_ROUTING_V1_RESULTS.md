# Selective Routing v1 — Results

Status: completed fresh routing validation; **formal result = failed** under the preregistered preservation rule.

Source workflow run: `34308303072`

Final report artifact: `selective-routing-v1-report-34308303072`

Artifact ID: `10113776537`

Artifact SHA-256: `306a5ae4a9dacb30cd4f36215f3d23606845d5cfa91d43a121f75aa41847a715`

Target: `glm-5.1` on Z.AI.

Router/judge: `glm-5.3-flash` on Z.AI.

Evidence tier: cross-model, same-family/provider; not independent-provider validation.

## Frozen design

- 48 fresh cases across 12 domains;
- binary input-only router: FULL vs CONTROL;
- exact frozen FULL prompt and exact frozen `selective_router_v1.py` policy;
- 3 target generations per case/condition;
- 3 blinded randomized quality votes per FULL-vs-CONTROL pair;
- routed policy constructed without a third target generation by selecting the already-generated FULL or CONTROL answer;
- case-clustered bootstrap with 5,000 draws;
- author route labels diagnostic only.

## Preregistered gates

### 1. ROUTED vs CONTROL benefit

Observed:

- score: **0.6620**;
- 95% CI: **0.6100–0.7176**.

Frozen rule: point estimate >= 0.60 and CI lower bound > 0.50.

**Pass.**

### 2. ROUTED vs ALWAYS-FULL preservation

Observed:

- score: **0.4850**;
- 95% CI: **0.4641–0.5000**.

Frozen rule: point estimate >= 0.50 and CI lower bound > 0.45.

The interval condition passed but the point estimate did not.

**Fail.**

### 3. Selectivity

Observed FULL invocation rate: **24/48 = 0.50**.

Frozen maximum: 0.65.

**Pass.**

Overall preregistered result:

**`routing_validation_pass = false`**.

This verdict is final for v1 and is not changed by later diagnostics.

## Framework replication on the fresh routing suite

ALWAYS-FULL vs CONTROL:

- score: **0.6771**;
- 95% CI: **0.6250–0.7292**;
- case direction: 30 FULL wins / 15 ties / 3 CONTROL wins.

This is a second fresh held-out replication of the framework-level FULL advantage under the available same-family judge.

## Routing diagnostics

The router selected FULL on 24 cases and CONTROL on 24 cases.

Against the author-designed diagnostic labels:

- accuracy: **48/48 = 1.00**;
- false-FULL: 0;
- false-CONTROL: 0.

That diagnostic success did not satisfy the primary scientific preservation endpoint, confirming that authored task categories are not ground truth for actual marginal quality value.

ROUTED vs CONTROL was especially strong on:

- action-required cases: approximately **0.799**;
- sequential cases: approximately **0.736**;
- no-action cases: **0.500**.

## Post-hoc endpoint diagnostic — not a v1 success criterion

After the v1 verdict was fixed, the intended non-inferiority question was re-expressed as the paired decrement in quality benefit relative to CONTROL:

`delta_i = score_i(ROUTED vs CONTROL) - score_i(FULL vs CONTROL)`.

On the exposed v1 suite:

- mean paired delta: approximately **-0.0150**;
- post-hoc case-bootstrap 95% interval: approximately **-0.0359 to 0.0000**;
- retained point-estimate gain over neutral: approximately **91.5%** of ALWAYS-FULL's gain.

This analysis is explicitly post-hoc and cannot rescue v1. It identifies a measurement-design issue: the v1 text described a 0.05 allowable-loss margin, while its actual preservation gate additionally required a ROUTED-vs-FULL point estimate >= 0.50, effectively requiring no average loss at all.

The next experiment must therefore use a new untouched suite and preregister the paired non-inferiority estimand before any outputs are generated.

## Execution note

Five shards completed in the initial attempt. Shard 2 failed during a redundant benchmark-free connectivity probe before any routing decision, target generation, or judge vote. After the matrix resolved, only shard 2 was rerun. The rerun completed successfully and final aggregation then completed. No successful shard was regenerated.

## Evidentiary conclusion

Supported:

> The frozen input-only router preserved a strong quality benefit over CONTROL while using FULL on only half of the fresh cases, but it failed the exact v1 preservation criterion relative to ALWAYS-FULL.

Not supported:

- v1 routing validation success;
- cost optimality;
- universal routing optimality;
- independent-provider validation.
