# Selective Routing v3 — Results

Status: **formal failure under the preregistered four-gate rule**.

Run: `34560083954`

Merge/launch commit: `6e557fb76f48562087816aa17dc64c40dcfdc322`

Final artifact: `selective-routing-v3-report-34560083954`

Artifact SHA-256: `b998501e2e3889e972002eeb6416460f5b31f68838d6306b08d0ccede76d264e`

Evaluation tier: Tier-1B cross-model same-family/provider only. Target is GLM-5.1; router and judge are GLM-5.3-Flash on the frozen Z.AI coding endpoint. This is not independent-provider validation.

## Completeness

All frozen execution units completed successfully:

- 48 route decisions;
- 288 target generations (`48 cases × 2 conditions × 3 replicates`);
- 432 blinded judge votes (`48 cases × 3 replicates × 3 votes`);
- six shard metadata records;
- final aggregation completed successfully.

No recovery or rerun was required.

## Frozen gate results

### Gate 0 — framework replication

`FULL vs CONTROL`:

- score: **0.65394**;
- case-clustered 95% CI: **0.58912–0.71991**;
- cases: 30 wins / 13 ties / 5 losses.

Frozen requirement: score >= `0.60` and CI lower bound > `0.50`.

**PASS.**

This is another fresh-suite replication of the framework-level FULL benefit.

### Gate 1 — routed benefit

`ROUTED vs CONTROL`:

- score: **0.49884**;
- 95% CI: **0.46759–0.53009**;
- cases: 2 wins / 44 ties / 2 losses.

Frozen requirement: score >= `0.60` and CI lower bound > `0.50`.

**FAIL.**

### Gate 2 — paired preservation

Case-level paired decrement:

`Delta = ROUTED_vs_CONTROL - FULL_vs_CONTROL`

- observed Delta: **-0.15509**;
- 95% CI: **-0.21296 to -0.09954**.

Frozen requirement: CI lower bound > `-0.05`.

**FAIL.**

### Gate 3 — selectivity

- FULL invocations: **5 / 48**;
- FULL invocation rate: **0.10417**.

Frozen requirement: <= `0.65`.

**PASS.**

Overall:

`routing_v3_validation_pass = false`

## Diagnostic review

The v3 router was intentionally redesigned to distinguish *marginal FULL value* from merely causal-looking complexity. The fresh validation falsified the key semantic hypothesis used in that redesign.

The most important diagnostic is the `CAUSAL_TRAP` stratum:

- v3 routed **0/12** of these cases to FULL;
- nevertheless, observed `FULL vs CONTROL` score was **0.81019**;
- 95% CI: **0.72222–0.88426**;
- 11 case-level wins / 1 tie / 0 losses.

Thus, tasks that looked like straightforward confounding / causal-hygiene problems still received substantial benefit from the frozen FULL prompt under the blinded quality rubric. The router's assumption that a competent unstructured answer would already capture enough of this reasoning was not supported.

Other FULL-vs-CONTROL strata:

- `CLEAR_CONTROL`: **0.48148**;
- `CLEAR_FULL`: **0.63426**;
- `QUIET_FULL`: **0.68981**.

The router correctly suppressed obvious direct tasks, but it also suppressed most cases where FULL retained real marginal value:

- `CLEAR_FULL` FULL-route rate: **1/12 = 8.3%**;
- `QUIET_FULL` FULL-route rate: **4/12 = 33.3%**;
- `CAUSAL_TRAP` FULL-route rate: **0/12**.

The result is therefore a routing-policy failure, not an aggregation or execution failure.

## Code / aggregation review

The aggregate implementation was reviewed after the surprising result. No defect was found in the policy construction:

- if a case is routed FULL, `ROUTED_vs_CONTROL` uses that case's observed FULL-vs-CONTROL replicate score;
- if routed CONTROL, it contributes `0.5` by construction;
- the paired decrement is computed from the same case-level FULL-vs-CONTROL evidence;
- completeness checks require exactly 48 routes, 288 target runs, 432 votes, and six metadata files;
- the frozen router blob, suite digest, and all metadata invariants are checked before aggregation.

The observed collapse follows directly from selecting CONTROL on 43/48 cases while FULL still outperformed CONTROL on many of them.

## Is the 65% selectivity target itself infeasible?

No.

Post-hoc oracle analysis on the now-exposed v3 case scores shows:

- FULL beat CONTROL on **30/48 = 62.5%** of cases;
- selecting FULL exactly on those positive-gain cases would remain under the frozen 65% invocation cap;
- corresponding oracle `ROUTED vs CONTROL` score would be approximately **0.68287**;
- oracle mean paired delta versus ALWAYS-FULL would be approximately **+0.02894** because CONTROL would replace FULL on cases where FULL lost.

This is diagnostic only and cannot be claimed as validated routing performance. It does show that the quality/selectivity target is empirically attainable on v3; the failure is prediction, not an impossible constraint.

## Research conclusion

Across routing v1–v3, hand-authored semantic task classes are not reliable enough proxies for actual marginal value of the FULL policy.

The next development stage should therefore stop asking the router to infer a category such as "causal", "engineering", "boundary", or "obvious confounder" and instead train/calibrate it against the empirical target:

`expected marginal quality gain from FULL over CONTROL`.

All v1, v2, and v3 suites are now exposed and may be used only for development/diagnostics. Any later routing claim requires another untouched validation suite.
