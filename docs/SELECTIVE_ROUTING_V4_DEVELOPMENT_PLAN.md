# Selective Routing v4 — Development Plan

Status: **development only; not a validation preregistration**.

Purpose: replace semantic routing heuristics with empirical prediction of the marginal quality value of FULL.

## Why this stage exists

Routing v1–v3 produced a consistent pattern:

- v1: good quality/selectivity balance but failed its original preservation rule;
- v2: preserved approximately 98% of FULL's observed gain but invoked FULL on 70.83% of cases, above the frozen 65% cap;
- v3: over-corrected, invoked FULL on only 10.42%, and lost the quality benefit entirely.

The v3 semantic hypothesis was specifically falsified: `CAUSAL_TRAP` cases were routed CONTROL 12/12, yet FULL scored 0.810 on that stratum.

The development target is therefore not a task category. It is the empirical quantity:

`g_i = quality_score(FULL_i, CONTROL_i) - 0.5`

where positive `g_i` means FULL showed marginal quality benefit on exposed case `i`.

## Development data

Use only already-exposed routing suites:

- Selective Routing v1 — 48 cases;
- Selective Routing v2 — 48 cases;
- Selective Routing v3 — 48 cases.

Total development pool: **144 exposed cases**.

The frozen held-out framework suite and any future v4 validation suite must not be used for router fitting.

For each exposed case, retain:

- user-visible turn-1 input available to a deployed router;
- empirical FULL-vs-CONTROL case score;
- continuous marginal gain `g_i`;
- sign of `g_i` (FULL win / tie / loss);
- existing design metadata only for diagnostics, never as hidden deployment inputs.

## Router objective

A candidate v4 router should estimate one or both of:

- `E[g_i | x]`: expected marginal pairwise quality gain from FULL;
- `P(g_i > 0 | x)`: probability that FULL adds positive quality value.

It must not be optimized to reproduce author route labels.

Router confidence is not itself a routing criterion unless empirically calibrated against exposed outcomes.

## Development discipline

1. Build an immutable exposed-outcomes table from the three completed routing reports.
2. Join outcomes to the original case texts by case ID.
3. Generate only deployment-available features from turn-1 user input. Candidate feature families may include:
   - deterministic/direct-answer structure;
   - number of plausible competing mechanisms;
   - whether a consequential action is requested;
   - whether evidence is confounded or contradictory;
   - whether a discriminating test would change the action;
   - reversibility / rollback / monitoring requirements;
   - explicit resource-allocation or tradeoff structure;
   - sequential-evidence expectation when visible at turn 1;
   - whether a simple calculation/procedure fully determines the answer.
4. Fit/evaluate candidate value predictors only on the exposed pool.
5. Prefer leave-one-domain-out or leave-one-suite-out development evaluation over in-sample accuracy.
6. Evaluate policies using the same downstream utility construction as v2/v3:
   - route FULL -> observed FULL-vs-CONTROL score;
   - route CONTROL -> 0.5.
7. During development, require candidate policies to target a FULL invocation range comfortably below the final 65% cap (for example, 55–62%) so sampling noise does not make the validation cap fragile. This is a development preference, not a future validation threshold.
8. Do not author a fresh v4 validation suite until the router implementation and its decision threshold are frozen.

## Candidate acceptance for freeze

A v4 candidate should not be frozen merely because it fits the 144 exposed cases. Before freeze it should demonstrate, under development cross-validation:

- materially positive routed-vs-CONTROL benefit;
- small paired decrement versus ALWAYS-FULL;
- stable invocation rate across held-out development folds;
- no dependence on domain names or author labels;
- no catastrophic misses concentrated in high-gain cases.

The exact development thresholds may be chosen before final candidate selection and must then be reported transparently. They are not substitutes for fresh validation.

## Fresh v4 validation

Only after the value router is frozen:

1. preregister a new validation experiment;
2. author a new untouched suite;
3. preserve the v2/v3 four primary gates unless a measurement change is justified prospectively before any new case/output exists;
4. use the same available Tier-1B setup: GLM-5.1 target and GLM-5.3-Flash router/judge;
5. classify the evidence as cross-model same-family/provider, not independent-provider validation.

## Stop rule

If empirical value prediction cannot outperform simple conservative baselines under cross-validation on the 144 exposed cases, stop routing development and prefer ALWAYS-FULL (or a trivial direct-task bypass) rather than continue semantic prompt tuning.
