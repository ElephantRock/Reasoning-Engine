# Selective Routing v2 — Utility Validation Preregistration

Status: preregistered after Selective Routing v1 completed and before any target output, route decision, or quality judgment is generated on the v2 suite.

## Why v2 exists

Selective Routing v1 formally failed its frozen preservation gate even though it:

- passed ROUTED vs CONTROL: `0.6620`, 95% CI `0.6100–0.7176`;
- used FULL on `50%` of cases;
- routed all 48 author-designed diagnostic labels correctly;
- replicated ALWAYS-FULL vs CONTROL at `0.6771`, 95% CI `0.6250–0.7292`.

The failed v1 preservation rule required both a ROUTED-vs-FULL point estimate >= `0.50` and a CI lower bound > `0.45`. That rule remains binding for v1 and v1 remains failed.

The scientific question intended by the stated 0.05 allowable-loss margin is instead:

> How much of ALWAYS-FULL's quality benefit over CONTROL is lost when the fixed router selectively substitutes CONTROL?

v2 preregisters that paired non-inferiority estimand prospectively on a new untouched suite. It is not a reinterpretation of v1.

## Frozen router

The routing policy is **unchanged from v1**.

- implementation: exact `benchmark/selective_router_v1.py` as present on `main` when this preregistration was authored;
- Git blob SHA: `a64fb4ed1dba3c7509163ab62831c2fe0cd81cc6`;
- model: `glm-5.3-flash`;
- provider/endpoint: Z.AI, `https://api.z.ai/api/coding/paas/v4`;
- temperature: `0` where supported;
- action space: `FULL | CONTROL`;
- route input: turn-1 user text only;
- one route decision per case;
- sequential future turns are unavailable to the router.

The router prompt, model, action space, and parsing policy must not change in v2.

`COMPACT` remains outside the policy because it did not pass the prior held-out compact threshold.

## Fresh v2 suite

Use exactly the manifest-closed suite rooted at `benchmark/routing_validation_v2/manifest.json` once frozen by merge. The manifest lists exactly 12 domain JSON files; no other case file is part of the v2 suite.

Planned size: **48 cases** across **12 domains**, four cases per domain.

Design strata are diagnostic only:

- 12 `CLEAR_FULL` cases: author expects deep causal/intervention reasoning to have substantial value;
- 12 `CLEAR_CONTROL` cases: author expects little marginal value from FULL;
- 24 `BOUNDARY` cases: intentionally ambiguous marginal-value cases that should stress the router near its decision boundary.

The v2 suite is deliberately less separable than v1. Author strata are not ground truth and cannot determine validation success.

Suite requirements:

- at least 12 sequential cases;
- at least 16 action-requiring cases;
- at least 16 distractor or surface-mismatch cases;
- boundary cases distributed across every domain;
- no reuse, paraphrase, or structural clone of v1 routing cases, Framework Validation v1 cases, or v0.5–v0.11 development cases.

The exact manifest and all listed domain files are frozen together by the merge commit and a deterministic combined suite digest. No v2 case may be added, removed, edited, or relabeled after any v2 model output exists.

## Target and evaluator

Target:

- model: `glm-5.1`;
- provider: Z.AI;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- conditions generated on every case: CONTROL and exact frozen FULL;
- 3 stochastic generations per case/condition.

Judge:

- model: `glm-5.3-flash`;
- provider: Z.AI;
- same endpoint;
- 3 blinded randomized pairwise votes per `(case, replicate)` comparing FULL vs CONTROL;
- same frozen quality rubric used in Framework Validation v1 and Selective Routing v1.

This remains Tier-1B cross-model, same-family/provider evidence only.

## Policy construction

ROUTED does not generate a third target response.

For each case `i` and generation replicate `r`, aggregate the three blinded FULL-vs-CONTROL votes into a score `s_ir` in `[0,1]`, where:

- `1` favors FULL;
- `0.5` is neutral/tied;
- `0` favors CONTROL.

Then:

- if route = FULL: `R_ir = s_ir` for ROUTED vs CONTROL;
- if route = CONTROL: `R_ir = 0.5` for ROUTED vs CONTROL.

ALWAYS-FULL vs CONTROL uses `F_ir = s_ir`.

Average replicate scores within case before inference. Cases are the independent units.

## Gate 0 — framework replication precondition

The routing experiment is scientifically interpretable only if FULL again shows a benefit on the v2 suite.

ALWAYS-FULL vs CONTROL must satisfy:

- score >= `0.60`;
- case-clustered 95% CI lower bound > `0.50`.

If this fails, `routing_utility_validation_pass = false` regardless of router behavior.

## Gate 1 — routed benefit

ROUTED vs CONTROL must satisfy:

- score >= `0.60`;
- case-clustered 95% CI lower bound > `0.50`.

## Gate 2 — paired preservation / non-inferiority

Define each case's paired decrement relative to ALWAYS-FULL:

`D_i = R_i - F_i`,

where `R_i` is the case-level ROUTED-vs-CONTROL score and `F_i` is the case-level FULL-vs-CONTROL score from the same case and underlying target outputs.

Primary preservation estimand:

`Delta = mean_i(D_i)`.

Use case-clustered paired bootstrap with exactly 5,000 draws, resampling cases and carrying both `R_i` and `F_i` together.

Frozen non-inferiority margin: **-0.05 pairwise-score points**.

The preservation gate passes only if:

- `CI95_low(Delta) > -0.05`.

Because a confidence lower bound cannot exceed the point estimate, this criterion also implies that the observed mean decrement is better than `-0.05`.

There is **no additional ROUTED-vs-FULL point-estimate >= 0.50 requirement in v2**. That is the prospective measurement correction being tested, not a retroactive change to v1.

Secondary descriptive statistic:

`retained_gain_ratio = (ROUTED_vs_CONTROL - 0.50) / (FULL_vs_CONTROL - 0.50)` when the denominator is positive.

This ratio is reported but is not a success gate.

## Gate 3 — selectivity

Only after quality is computed, report FULL invocation rate.

The selectivity gate passes if:

- FULL invocation rate <= `0.65` across all 48 cases.

Token and latency savings remain descriptive and cannot rescue a quality failure.

## Overall decision

`routing_utility_validation_pass = true` only if all four gates pass:

1. framework replication precondition;
2. ROUTED vs CONTROL benefit;
3. paired preservation lower CI > `-0.05`;
4. FULL invocation rate <= `0.65`.

No threshold may be changed after any v2 output exists.

## Secondary diagnostics

Report:

- FULL vs CONTROL score/CI;
- ROUTED vs CONTROL score/CI;
- paired preservation delta and CI;
- direct ROUTED-vs-FULL score as a descriptive continuity metric only;
- retained gain ratio;
- FULL invocation rate;
- route distribution by `CLEAR_FULL`, `CLEAR_CONTROL`, and `BOUNDARY`;
- clear-stratum diagnostic classification accuracy (BOUNDARY excluded from accuracy);
- route and policy scores by domain, sequential status, distractor/surface mismatch, and action requirement;
- per-case route, router signals/confidence, FULL-vs-CONTROL case score, and paired decrement;
- judge agreement/unanimity;
- target/router/judge token and latency diagnostics.

## Connectivity and recovery discipline

The benchmark-free connectivity probe runs once in a dedicated preflight job before any shard is released.

Shard workers must **not** repeat a strict semantic connectivity probe. This prevents the execution-only failure observed in v1, where GLM-5.3-Flash returned valid but non-exact probe JSON.

Each shard writes checkpoint artifacts incrementally. If a shard fails after target generation begins, recovery must reuse completed target outputs and request only missing work. If it fails before any v2 data are written, only that shard may be rerun.

## Stop rules

Once any v2 target output or route exists:

- do not edit router prompt/model/action space;
- do not edit the manifest or any listed case file;
- do not edit FULL or CONTROL definitions;
- do not edit judge rubric;
- do not edit replicate/vote counts;
- do not edit the `0.60`, `0.50`, `-0.05`, or `0.65` thresholds;
- do not remove hard or misrouted cases;
- do not convert secondary diagnostics into primary success criteria.

A failure remains a failure. Any later routing policy or measurement redesign requires another untouched suite.

## Supported claim if v2 passes

> On a fresh 48-case routing-utility suite, the unchanged input-only GLM-5.3-Flash router selectively invoked the frozen FULL GLM-5.1 reasoning policy, retained a preregistered quality benefit over CONTROL, kept the paired decrement relative to ALWAYS-FULL within a 0.05 non-inferiority margin, and invoked FULL on no more than 65% of cases under same-family/provider blinded judging.

This would not establish independent-provider validation, universal routing optimality, or cost optimality.