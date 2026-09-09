# Held-Out Framework Validation v1 — GLM-5.3-Flash Results

Status: completed Tier-1B cross-model, same-family held-out evaluation.

Source workflow run: `34270142523`

Final report artifact: `framework-v1-glm53flash-recovered-report-34270142523`

Artifact ID: `10082933251`

Artifact SHA-256: `b28ca6a5f7d222f54b1ba6dd44fbd5f2b32b332947031a352c497c03ce431c12`

Target: `glm-5.1` on Z.AI.

Judge: `glm-5.3-flash` on Z.AI.

This evaluator is a distinct model but the same GLM family and provider. The result is therefore Tier-1B cross-model same-family evidence, not independent-provider validation.

## Frozen design

The run used the preregistered design without changing scientific parameters:

- exact frozen `benchmark/heldout_cases_v1.json` suite;
- suite freeze commit `2975376ade5df0863340ce10aa867f3b3e0e1404`;
- suite git blob SHA `5fa2ab6f678728124b93ea9dd6c9158e5d6e9698`;
- 36 held-out cases;
- CONTROL, COMPACT, and FULL on every case;
- 3 target-generation replicates per case/condition;
- 3 blinded randomized judge votes per generated pair;
- pair aggregation within generation replicate;
- generation replicates averaged within case;
- case-clustered bootstrap confidence intervals;
- cost descriptive only.

Completeness:

- target runs: `324/324`;
- judge votes: `972/972`.

## Primary endpoint

Primary comparison: `FULL_vs_CONTROL`.

Preregistered success rule:

- score >= `0.60`;
- case-clustered 95% CI lower bound > `0.50`;
- no original task stratum with at least six cases below `0.45`.

Observed:

- score: **`0.6898`**;
- 95% CI: **`0.6096–0.7685`**;
- generation-replicate majorities: `61` FULL wins / `27` ties / `20` losses;
- case-level direction: `26` wins / `2` ties / `8` losses across 36 cases;
- mean judge-vote agreement: `0.8889`;
- unanimous generation-replicate verdict fraction: `0.6944`.

The primary statistical rule passed.

### Robustness gate

Preregistered task-stratum harm floor: `0.45`.

Observed FULL vs CONTROL task-stratum scores:

| Task stratum | Score | 95% CI | Cases |
|---|---:|---:|---:|
| ENGINEER | **0.9012** | 0.8025–0.9753 | 9 |
| TEST | **0.7901** | 0.6790–0.9012 | 9 |
| BOTH | **0.6296** | 0.4074–0.8519 | 6 |
| NONE | **0.4861** | 0.4074–0.5556 | 12 |

No preregistered task stratum fell below `0.45`, so the robustness gate passed.

Overall preregistered result:

**`validation_pass = true`**.

## Secondary endpoints

### COMPACT vs CONTROL

Observed:

- score: `0.5864`;
- 95% CI: `0.5077–0.6667`;
- case-level direction: `18` wins / `5` ties / `13` losses.

The secondary compact success rule required the same `0.60` point-estimate threshold and CI lower bound > `0.50`.

The CI condition passed, but the point estimate did not reach `0.60`.

Therefore:

**COMPACT did not pass its preregistered secondary success rule.**

### FULL vs COMPACT

Observed:

- score: **`0.5957`**;
- 95% CI: **`0.5417–0.6543`**;
- case-level direction: `21` wins / `7` ties / `8` losses.

The preregistered directional rule classified this as **FULL** because the point estimate exceeded the `0.55` directional threshold. No formal equivalence test was preregistered.

This is the first held-out result in this program where FULL shows a clear directional advantage over COMPACT under the frozen evaluator design.

## Heterogeneity

The primary average should not be interpreted as uniform benefit.

FULL vs CONTROL by action requirement:

- requires action: `0.7375`, 95% CI `0.6437–0.8238`, 24 case-level wins / 0 ties / 5 losses across 29 cases;
- does not require action: `0.4921`, 95% CI `0.4127–0.5796`, 2 wins / 2 ties / 3 losses across 7 cases.

FULL vs CONTROL by sequential design:

- sequential: `0.6528`, 95% CI `0.5093–0.8056`;
- non-sequential: `0.7083`, 95% CI `0.6134–0.7986`.

The strongest positive effects occur in cases that demand explicit testing or engineering/action. Cases with neither target demand are close to neutral.

The most defensible interpretation is therefore:

> The frozen FULL reasoning protocol improves held-out reasoning quality on average relative to an uncontrolled baseline under a distinct same-family judge, with especially strong gains on test- and engineering-oriented tasks. The evidence does not support a claim that explicit full-depth reasoning is uniformly beneficial on all task types.

## Execution recovery

The first source run, `34232674771`, generated all held-out target outputs but terminated during judge parsing because `glm-5.3-flash` sometimes returned a valid JSON object followed by additional text.

This was treated as an execution-format failure, not a scientific endpoint result.

Before inspecting partial outcome distributions, the recovery path was frozen to:

- restore the six source-run artifacts;
- require all `54` target-run keys per shard;
- forbid target regeneration;
- retain all valid existing vote keys;
- request only missing preregistered votes with the original deterministic A/B orientation seed;
- accept the first complete JSON object when trailing text follows it;
- never repair malformed JSON;
- treat malformed/invalid outputs as non-votes and retry the same missing vote up to three format attempts.

Recovery totals:

- retained target outputs: `324/324`;
- target outputs regenerated: `0`;
- retained valid judge votes: `369`;
- missing judge votes completed: `603`;
- observed formatting retries during recovery: `6`;
- final judge votes: `972/972`.

All six source artifact digests matched the preregistered provenance. The final report records `target_outputs_regenerated = false` and `outcome_peeking_before_recovery_design = false`.

## Cost diagnostics

Cost did not enter any quality endpoint.

Target-model descriptive totals:

| Condition | Runs | Input tokens | Output tokens | Target latency ms |
|---|---:|---:|---:|---:|
| CONTROL | 108 | 32,728 | 319,505 | 6,420,481 |
| COMPACT | 108 | 57,446 | 287,888 | 5,902,251 |
| FULL | 108 | 67,700 | 341,303 | 6,946,484 |

No cost optimization claim follows from this experiment.

## Evidentiary boundary

This result supports:

> held-out framework improvement under cross-model, same-family evaluation.

It does **not** establish:

- independent-provider evaluation;
- independent model-family evaluation;
- universal benefit across all task types;
- autonomous routing validity;
- cost optimality;
- generalization to target models other than `glm-5.1`.

The next strongest validation step is to evaluate the same frozen target outputs or a preregistered fresh replication with a genuinely independent evaluator from another model family/provider, preferably with a human-reviewed subset.
