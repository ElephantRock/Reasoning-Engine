# Selective Routing v4 — Development Results

Status: **development stop rule triggered; no v4 router frozen; no fresh validation suite should be authored.**

Development run: `34635603882`

Development artifact: `selective-routing-v4-development-34635603882`

Artifact SHA-256: `c578ccae20c00204868546921a9d6f738a8b876d3b6dbdf27969cc7568ec48be`

Evidence status: exposed-data development only. These results are not fresh validation.

## Development corpus

The development harness used exactly 144 already-exposed routing cases:

- v1: 48;
- v2: 48;
- v3: 48.

Mean observed FULL-vs-CONTROL score across the corpus was **0.67284**.

The predictor was restricted to user-visible turn-1 text. CI explicitly fails if the script accesses author route labels, evaluator keys, or hidden design metadata. Suite and domain identity were used only to define held-out folds.

## Frozen decision rule

Before candidate evaluation, the development protocol required a candidate to pass both leave-one-suite-out (LOSO) and leave-one-domain-out (LODO) gates. If no candidate passed all gates, the routing-development stop rule would trigger and no fresh v4 validation suite would be authored.

That stop condition occurred.

`qualifying_candidates = []`

`selected_candidate = null`

`stop_rule_triggered = true`

## Baselines

### ALWAYS-FULL

- routed score: **0.67284**;
- FULL invocation: **100%**;
- paired decrement: **0**.

This remains the quality reference.

### ALWAYS-CONTROL

- routed score: **0.50000**;
- FULL invocation: **0%**;
- paired decrement: **-0.17284**.

### DIRECT-BYPASS

The fixed direct-task heuristic preserved quality reasonably well but did not satisfy the selectivity target:

- routed score: **0.65123**;
- paired decrement: **-0.02160**;
- FULL invocation: **69.44%**;
- high-gain recall: **87.5%**.

It failed the frozen development FULL-rate range (`0.50–0.63`).

## Empirical predictors

No TF-IDF k-nearest-neighbor or Bernoulli Naive Bayes candidate passed all frozen development gates.

The strongest candidate was `NB_DIRECT`.

### NB_DIRECT — leave-one-suite-out

- routed score: **0.63927**;
- FULL score on the same cases: **0.67284**;
- paired decrement: **-0.03356**;
- FULL invocation: **56.25%**;
- high-gain recall: **79.69%**;
- worst suite-held-out routed score: **0.62269**.

It failed only the frozen LOSO paired-decrement gate, which required `>= -0.03`.

Suite-held-out behavior was not stable enough to override that preregistered development decision:

- hold out v1: routed **0.66204**, FULL use **54.17%**;
- hold out v2: routed **0.62269**, FULL use **47.92%**;
- hold out v3: routed **0.63310**, FULL use **66.67%**.

The v3 held-out fold therefore crossed the eventual 65% selectivity ceiling even though the pooled development rate was acceptable.

### NB_DIRECT — leave-one-domain-out

- routed score: **0.64931**;
- paired decrement: **-0.02353**;
- FULL invocation: **58.33%**;
- high-gain recall: **84.38%**.

These pooled metrics passed the frozen LODO gates, but small-domain behavior remained heterogeneous. The worst four-case domain routed score was **0.45833**. This was not itself a preregistered LODO failure criterion, but it reinforces the decision not to freeze the near-miss candidate.

## Other near candidates

`KNN9_DIRECT`:

- LOSO score **0.62809**, decrement **-0.04475**, FULL rate **53.47%**;
- LODO score **0.64429**, decrement **-0.02855**, FULL rate **59.72%**.

`KNN5_DIRECT`:

- LOSO score **0.62616**, decrement **-0.04668**, FULL rate **56.25%**;
- LODO score **0.64275**, decrement **-0.03009**, FULL rate **58.33%**.

Both failed the frozen LOSO preservation requirement.

## Review

The v4 development harness was reviewed after execution.

No leakage or aggregation defect was identified:

- the frozen empirical outcome table is hash-checked;
- only turn-1 text enters candidate prediction;
- threshold calibration occurs on training-fold leave-one-out predictions;
- held-out suite/domain cases do not determine their own thresholds;
- every case is evaluated exactly once per cross-validation scheme;
- policy utility uses the same construction as prior routing experiments: FULL uses observed FULL-vs-CONTROL quality, CONTROL contributes 0.5.

The main finding is therefore substantive: text-only empirical prediction improves substantially over the failed v3 semantic router, but the available 144-case exposed corpus does not support a router that meets the deliberately conservative quality-preservation and selectivity requirements robustly enough to justify another fresh validation run.

The closest candidate is also too unstable across suite shifts to justify relaxing the frozen development gate after seeing the result.

## Program decision

The selective-routing research line is **closed for now under the frozen stop rule**.

Do not:

- tune additional semantic prompts on v1–v3;
- relax the v4 development gates post hoc;
- author a fresh v4 validation suite for `NB_DIRECT`;
- claim that cross-validation on exposed cases is a validated router result.

The current recommended architecture is:

`ALWAYS-FULL for non-trivial reasoning tasks`,

with direct answering still permitted for genuinely trivial/deterministic tasks under the framework's existing trivial-task rule, but not presented as a validated 65%-cap selective router.

Routing may be reopened only if materially new development information becomes available—for example substantially more labeled marginal-value cases, a different target-model family, or a better deployment-available signal than turn-1 text alone.
