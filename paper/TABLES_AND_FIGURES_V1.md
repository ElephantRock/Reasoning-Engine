# Tables and Figures Package v1

Status: manuscript support package derived only from frozen repository evidence. No new inferential analysis is introduced here.

## Table 1 — Research chronology

| Stage | Primary question | Cases / corpus | Principal result | Evidence status |
|---|---|---:|---|---|
| Quality v0.5 | Does structured prompting improve quality? | 12 development cases | FULL 0.7778 vs BASELINE; COMPACT 0.8056 vs BASELINE | development/calibration |
| Ablation v0.6.1 | Are named instructions individually necessary? | development suite | replication did not yield stable component pattern | negative / identification-limited |
| Capability v0.7–v0.11 | Can specific behaviors be manipulated and linked to quality? | development cases | ENGINEER strongest signal; Diagnose/Revise often near ceiling; no robust stage module survived carry-forward | development / mixed |
| Held-out framework v1 | Does frozen FULL beat CONTROL? | 36 fresh cases | **0.6898**, CI **0.6096–0.7685** | preregistered Tier-1B primary PASS |
| Routing v1 | Can binary input-only routing preserve FULL quality at <=65% FULL use? | 48 fresh cases | routed benefit PASS, selectivity PASS, preservation FAIL | formal FAIL |
| Routing v2 | Can corrected paired preservation + selectivity both pass? | 48 fresh cases | quality/preservation PASS; FULL use **70.83%** | formal FAIL |
| Routing v3 | Can marginal-value semantic routing improve selectivity? | 48 fresh cases | routed score **0.4988**; causal-trap hypothesis falsified | formal FAIL |
| Routing v4 | Can exposed-data text prediction yield a robust candidate? | 144 exposed cases | no candidate passed all LOSO/LODO gates; stop rule triggered | development stop |

## Table 2 — Fresh-suite FULL vs CONTROL

| Suite | Cases | FULL vs CONTROL | 95% case-clustered CI | Interpretation |
|---|---:|---:|---:|---|
| Held-out framework v1 | 36 | **0.6898** | **0.6096–0.7685** | preregistered primary framework validation |
| Routing v1 suite | 48 | **0.6771** | **0.6250–0.7292** | fresh prospective replication inside routing study |
| Routing v2 suite | 48 | **0.6875** | **0.6273–0.7477** | fresh prospective replication inside routing study |
| Routing v3 suite | 48 | **0.6539** | **0.5891–0.7199** | fresh prospective replication inside routing study |

Descriptive case-count-weighted score across all 180 cases: approximately **0.6762**. Do not attach a pooled inferential CI or describe this as an independent-study meta-analysis.

## Table 3 — Primary held-out heterogeneity

| Stratum | FULL vs CONTROL |
|---|---:|
| ENGINEER | **0.9012** |
| TEST | **0.7901** |
| BOTH | **0.6296** |
| NONE | **0.4861** |
| Action-required | **0.7375** |
| No-action | **0.4921** |

Recommended use: main paper results or discussion. The point is heterogeneity, not subgroup significance testing.

## Table 4 — Routing outcomes

| Policy / stage | Quality metric | FULL use | Frozen verdict |
|---|---:|---:|---|
| ALWAYS-FULL reference on v2 | FULL vs CONTROL **0.6875** | 100% | quality reference |
| Routing v1 | ROUTED vs CONTROL **0.6620** | 50.0% | FAIL preservation |
| Routing v2 | ROUTED vs CONTROL **0.6840** | 70.83% | FAIL selectivity |
| Routing v3 | ROUTED vs CONTROL **0.4988** | 10.42% | FAIL quality + preservation |
| v4 `DIRECT_BYPASS` development | routed score **0.6512** | 69.44% | development FAIL selectivity range |
| v4 `NB_DIRECT` LOSO development | routed score **0.6393** | 56.25% | development FAIL preservation |

Do not mix fresh-validation and exposed-development rows without labeling them. v4 rows are not validation results.

## Figure 1 — Reasoning policy and evidence hierarchy

Suggested two-panel schematic.

Panel A:

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`

Under the chain, annotate:

- observation vs interpretation;
- competing mechanisms;
- first-principles constraints;
- falsifiable hypotheses;
- discriminating predictions/tests;
- evidence-driven revision;
- reversible monitored intervention.

Panel B:

`Framework effect → Component identification → Fresh replication → Routing → Cost`

Mark evidence status:

- Framework effect: supported for GLM-5.1 under same-family judge.
- Component causality: unresolved.
- Routing: failed frozen criteria / stopped.
- Cost optimum: not established.

## Figure 2 — Fresh-suite FULL-vs-CONTROL consistency

Recommended plot: four point estimates with 95% case-clustered intervals and a horizontal neutral line at 0.50.

Data:

| Suite | Estimate | Low | High |
|---|---:|---:|---:|
| Held-out v1 | 0.6898 | 0.6096 | 0.7685 |
| Routing v1 suite | 0.6771 | 0.6250 | 0.7292 |
| Routing v2 suite | 0.6875 | 0.6273 | 0.7477 |
| Routing v3 suite | 0.6539 | 0.5891 | 0.7199 |

Caption should state that later suites were sequential fresh suites inside the same research program, not independent studies.

## Figure 3 — Heterogeneous primary effect

Recommended plot: point estimates for ENGINEER, TEST, BOTH, NONE, action-required, no-action. Use the exact confidence intervals from `docs/HELDOUT_FRAMEWORK_VALIDATION_V1_GLM53FLASH_RESULTS.md` where reported.

Interpretation line: strongest gains occur when outputs require explicit testing or engineering/action; near-neutral groups motivated routing research but did not yield a validated router.

## Figure 4 — Routing quality/selectivity trajectory

Suggested scatter plot:

- x-axis: FULL invocation rate;
- y-axis: routed-vs-CONTROL score;
- reference point: ALWAYS-FULL at x=1.0, y equal to suite-specific FULL score;
- mark the 65% selectivity ceiling;
- distinguish validated fresh-suite points from exposed-development points by marker shape.

Minimum points:

- v1: (0.50, 0.6620)
- v2: (0.7083, 0.6840)
- v3: (0.1042, 0.4988)
- v4 `DIRECT_BYPASS` development: (0.6944, 0.6512)
- v4 `NB_DIRECT` LOSO development: (0.5625, 0.6393)

Do not draw a single Pareto frontier across different fresh suites as though all points were evaluated on identical cases. If a frontier is shown, it must be explicitly descriptive.

## Figure-review rules

1. No figure should imply independent-study meta-analysis.
2. Do not add inferential error bars to the descriptive 180-case aggregate.
3. Mark v4 as exposed-data development only.
4. Keep the 36-case held-out result visually primary.
5. Do not label DIRECT→FULL deployment interpretation as a validated router.
