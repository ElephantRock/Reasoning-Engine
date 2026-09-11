# Selective Routing v3 — Marginal-Value Router Preregistration

Status: preregistered after Selective Routing v2 completed and **before any v3 validation case is authored, any v3 route is generated, or any v3 target/judge output exists**.

## Why v3 exists

Selective Routing v2 formally failed only the frozen selectivity gate:

- FULL vs CONTROL: `0.6875`, CI `0.6273–0.7477` — PASS;
- ROUTED vs CONTROL: `0.6840`, CI `0.6262–0.7408` — PASS;
- paired decrement: `-0.00347`, CI `-0.02546–0.01273` against margin `-0.05` — PASS;
- FULL invocation: `0.7083` against cap `0.65` — FAIL.

v2 remains failed. Its exposed suite may motivate v3 development but may not validate v3.

The post-hoc v2 diagnosis is that the v1 router often treated **causal-looking complexity** as equivalent to **marginal value from the FULL prompt**. Several tasks with multiple plausible causes and consequential context could still be solved by a competent baseline with one obvious causal-caution/deconfounding step.

v3 tests a narrower hypothesis:

> FULL should be invoked when deliberate structured mechanism/engineering reasoning is likely to materially change the answer or action beyond a competent unstructured GLM-5.1 response, not merely because the prompt contains causal ambiguity.

## Frozen v3 router

Implementation: `benchmark/selective_router_v3.py`

Git blob SHA: `6ebb72e443c846aee35281c20e64f3b5d173a7a0`

Model/configuration:

- router model: `glm-5.3-flash`;
- provider: Z.AI;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- temperature: `0` where supported;
- route input: turn-1 user text only;
- action space: `FULL | CONTROL`;
- one route decision per case;
- future sequential turns are not visible to the router;
- confidence is diagnostic only and is **not** thresholded.

The v3 router prompt explicitly distinguishes marginal FULL value from absolute complexity and adds a conservative exclusion for tasks whose correct resolution is one direct measurement, one straightforward comparison, or one obvious deconfounding step.

The router prompt, implementation, model, endpoint, action space, parser, and temperature are frozen for v3 validation.

## Fresh v3 validation suite

A new untouched manifest-closed suite will be authored only after this preregistration commit.

Planned size: **48 cases across 12 domains**, four cases per domain.

Each domain will contain one case from each author diagnostic stratum:

1. `CLEAR_FULL` — strong expected marginal FULL value;
2. `CLEAR_CONTROL` — direct/established task with little expected FULL value;
3. `CAUSAL_TRAP` — deliberately causal-looking task whose key resolution should be a simple direct check, obvious deconfounding step, or straightforward comparison;
4. `QUIET_FULL` — task with substantial intervention/allocation/revision value but without conspicuous causal/test vocabulary.

These labels are diagnostic only. They are not ground truth and do not determine success.

Suite requirements:

- exactly 48 unique cases;
- exactly 12 domains, 4 cases each;
- exactly 12 cases in each diagnostic stratum;
- at least 12 sequential cases;
- at least 20 action-requiring cases;
- at least 20 distractor/surface-mismatch cases;
- no reuse, paraphrase, or structural clone of v1, v2, Framework Validation v1, or v0.5–v0.11 cases;
- no case prompt may contain framework stage names or the strings `FULL`, `CONTROL`, `COMPACT`, or `router` in a way that reveals the experimental policy.

Once the manifest and domain files are merged, a deterministic suite digest freezes the suite. No case may be changed after any v3 model output exists.

## Target and judge

Target:

- model: `glm-5.1`;
- provider: Z.AI;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- conditions generated on every case: CONTROL and exact frozen FULL prompt from `benchmark/pilot.py`;
- 3 stochastic generations per case/condition.

Judge:

- model: `glm-5.3-flash`;
- same Z.AI endpoint/provider;
- 3 blinded randomized pairwise quality votes per `(case, replicate)` comparing FULL vs CONTROL;
- same frozen quality rubric and randomized A/B orientation used in v2.

This remains Tier-1B cross-model, same-family/provider evidence only.

## ROUTED policy construction

ROUTED generates no third target answer.

For each case/replicate, let `s_ir` be the blinded FULL-vs-CONTROL score in `[0,1]` after aggregating the three judge votes.

- If route = FULL, `R_ir = s_ir`.
- If route = CONTROL, `R_ir = 0.5`.
- ALWAYS-FULL uses `F_ir = s_ir`.

Average replicates within case before inference. Cases are the independent units.

## Frozen success gates

The v2 gates are retained unchanged.

### Gate 0 — framework replication

FULL vs CONTROL must satisfy:

- score >= `0.60`;
- case-clustered CI95 lower bound > `0.50`.

### Gate 1 — routed benefit

ROUTED vs CONTROL must satisfy:

- score >= `0.60`;
- case-clustered CI95 lower bound > `0.50`.

### Gate 2 — paired preservation

For case `i`:

`D_i = R_i - F_i`.

With exactly 5,000 paired case-bootstrap draws, v3 passes preservation only if:

- `CI95_low(mean(D_i)) > -0.05`.

### Gate 3 — selectivity

- FULL invocation rate <= `0.65`.

### Overall

`routing_v3_validation_pass = true` only if **all four** gates pass.

No gate may be relaxed after any v3 output exists.

## Secondary diagnostics

Report, without converting them into success criteria:

- retained gain ratio;
- direct ROUTED-vs-FULL descriptive score/CI;
- route distribution and quality by all four diagnostic strata;
- clear-stratum diagnostic accuracy for `CLEAR_FULL` and `CLEAR_CONTROL`;
- `CAUSAL_TRAP` CONTROL rate;
- `QUIET_FULL` FULL rate;
- domain, sequential, distractor, and action subgroups;
- per-case route, signals, confidence, FULL-vs-CONTROL score, and paired decrement;
- judge agreement/unanimity;
- target/router/judge token and latency diagnostics.

## Connectivity and recovery

- one benchmark-free global connectivity preflight only;
- shards do not repeat strict semantic probes;
- six shards, eight cases per shard, `max-parallel: 3`;
- checkpoint outputs are uploaded even on shard failure;
- a failed shard that has already produced target outputs must be recovered from checkpoints rather than regenerated;
- a shard failing before any scientific data are written may be rerun alone.

## Stop rules

After the first v3 route or target output exists, do not change:

- v3 router prompt/code/model/action space;
- case suite or labels;
- FULL/CONTROL prompts;
- judge rubric/model;
- generation/vote counts;
- bootstrap count;
- thresholds `0.60`, `0.50`, `-0.05`, or `0.65`.

A failed v3 result remains failed. Any later policy change requires another fresh validation suite.

## Supported claim if v3 passes

> On a fresh 48-case semantic-stress routing suite, the preregistered marginal-value GLM-5.3-Flash router preserved the validated FULL reasoning benefit over CONTROL within the frozen 0.05 paired non-inferiority margin while invoking FULL on no more than 65% of cases under same-family/provider blinded evaluation.

This would support a practical selective-routing architecture, but would not establish independent-provider validation or universal optimality.