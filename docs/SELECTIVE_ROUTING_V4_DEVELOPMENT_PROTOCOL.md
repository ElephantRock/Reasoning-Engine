# Selective Routing v4 — Development Protocol

Status: **development-only protocol; frozen before candidate evaluation**.

This stage uses only the already-exposed routing v1–v3 suites. It is not fresh validation and cannot support a new routing-performance claim.

## Development corpus

Source cases:

- routing v1: 48 exposed cases;
- routing v2: 48 exposed cases;
- routing v3: 48 exposed cases.

Total: **144 cases**.

Observed FULL-vs-CONTROL outcomes are frozen in:

`benchmark/routing_v4_exposed_outcomes.csv`

The CSV encodes each case score as `score18`, where `score = score18 / 18`. This preserves the exact blinded case-level pairwise score without floating-point ambiguity.

Frozen outcome-table SHA-256:

`8711a6aff96df9bda7f9c7c6f209ae33cd6370b811886a27f5d28ddbe791b295`

The development target is:

`g_i = FULL_vs_CONTROL_i - 0.5`.

Positive `g_i` means FULL showed empirical marginal quality benefit on exposed case `i`.

Only user-visible turn-1 input may be used for prediction. Author route labels, evaluator keys, design metadata, later turns, prior router signals, and domain names are excluded from model inputs. Domain and suite identities may be used only to define cross-validation folds and diagnostics.

## Candidate families

All candidates are deterministic and require no paid model calls.

### Baseline A — ALWAYS_FULL

Route every case to FULL. This is the quality reference and is not selective.

### Baseline B — ALWAYS_CONTROL

Route every case to CONTROL. Policy score is 0.5 by construction.

### Baseline C — DIRECT_BYPASS

A fixed text-only heuristic routes clearly deterministic/direct tasks to CONTROL and otherwise routes FULL. The heuristic is frozen in the development script before results are inspected.

### Candidate family D — TF-IDF k-nearest-neighbor gain prediction

Using turn-1 text only:

1. tokenize lowercase alphanumeric terms;
2. build TF-IDF vectors from the training fold only;
3. estimate expected gain by similarity-weighted mean gain of the nearest training cases;
4. evaluate `k ∈ {5, 9, 15}`;
5. optionally combine the prediction with the frozen DIRECT_BYPASS rule, which can force obvious deterministic tasks to CONTROL.

### Candidate family E — Bernoulli Naive Bayes positive-gain prediction

Using turn-1 tokens only:

1. define the training label as `1[g_i > 0]`;
2. use Bernoulli token presence with Laplace smoothing `alpha = 1`;
3. restrict the vocabulary to tokens appearing in at least two training cases;
4. predict the log posterior odds that FULL has positive marginal gain;
5. optionally combine the prediction with the frozen DIRECT_BYPASS rule.

No author labels or hidden metadata enter either empirical predictor.

## Threshold calibration

For each held-out fold, the routing threshold is calibrated **only on the training portion**.

Training cases receive leave-one-out predictions from the candidate. The threshold is selected to target a FULL invocation rate of **0.58** on those training predictions. Ties prefer the threshold producing the lower invocation rate.

The selected threshold is then applied unchanged to the held-out fold.

This avoids calibrating the invocation threshold on the held-out cases themselves.

## Cross-validation

Every candidate is evaluated under two complementary schemes.

### Leave-one-suite-out (LOSO)

Three folds:

- hold out v1;
- hold out v2;
- hold out v3.

This is the primary development generalization test because suite construction changed materially across routing versions.

### Leave-one-domain-out (LODO)

Hold out every observed domain in turn. Domain identity defines folds but is never a predictor feature.

## Policy metrics

For every held-out case:

- route FULL -> use the observed `FULL_vs_CONTROL` score;
- route CONTROL -> assign policy score `0.5`.

Report:

- ROUTED-vs-CONTROL mean policy score;
- ALWAYS-FULL mean score on the same held-out cases;
- paired decrement `ROUTED - ALWAYS_FULL`;
- FULL invocation rate;
- recall on high-gain cases where `g_i >= 0.20`;
- fold-level routed score and invocation rate.

## Candidate acceptance gates

A candidate qualifies for a possible v4 freeze only if **all** development gates pass.

### LOSO gates

- pooled routed score >= `0.60`;
- pooled paired decrement >= `-0.03`;
- pooled FULL invocation rate between `0.50` and `0.63`, inclusive;
- worst suite-held-out routed score >= `0.56`;
- recall on held-out high-gain cases >= `0.70`.

### LODO gates

- pooled routed score >= `0.59`;
- pooled paired decrement >= `-0.04`;
- pooled FULL invocation rate between `0.50` and `0.63`, inclusive;
- recall on held-out high-gain cases >= `0.65`.

These are development filters, not future validation thresholds.

## Candidate selection

Among candidates passing all gates, select the candidate maximizing:

`min(LOSO routed score, LODO routed score)`.

Tie-breakers, in order:

1. smaller absolute paired decrement;
2. lower FULL invocation rate;
3. for k-nearest-neighbor candidates, smaller `k`;
4. fixed candidate-name lexical order.

If no candidate passes all gates, **do not author a fresh v4 validation suite**. The routing-development stop rule triggers and the recommended architecture remains ALWAYS-FULL, optionally with only a trivial deterministic bypass if that bypass itself is robust.

## Evidence boundary

All results from this development protocol are in-sample-to-program evidence because v1–v3 are exposed. Even clean cross-validation is only candidate-development evidence.

A future routing claim requires:

1. freeze the selected router implementation and thresholding rule;
2. preregister a new validation experiment;
3. author a completely untouched validation suite only after the router freeze;
4. retain the established quality, preservation, and selectivity gates prospectively.
