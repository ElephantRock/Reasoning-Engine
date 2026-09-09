# Selective Routing v1 — Preregistration

Status: preregistered after Tier-1B Held-Out Framework Validation v1 and before any target output or quality judgment is generated on the routing-validation suite.

## Scientific transition

Held-Out Framework Validation v1 established a cross-model, same-family quality effect for the frozen FULL protocol on the frozen 36-case suite:

- FULL vs CONTROL: `0.6898`, case-clustered 95% CI `0.6096–0.7685`;
- strongest descriptive subgroups: ENGINEER `0.9012`, TEST `0.7901`, requires-action `0.7375`;
- near-neutral descriptive subgroups: NONE `0.4861`, no-action `0.4921`.

That 36-case suite is now exposed. It may motivate the routing hypothesis but may not validate it.

The next question is therefore not generic task complexity. It is:

> Can an input-only controller predict when FULL reasoning has decision-relevant marginal value, preserving the validated quality benefit while avoiding unnecessary FULL invocation?

## Frozen routing policy

Routing is binary in v1:

- `FULL`: apply the exact frozen `benchmark/pilot.py::FULL` prompt;
- `CONTROL`: apply no reasoning-specific system prompt.

`COMPACT` is deliberately excluded from the routing action space because it did not pass the preregistered secondary held-out success threshold in Framework Validation v1.

The router is a separate classification call using `glm-5.3-flash` on the existing Z.AI endpoint. It sees only the user input available at routing time. It never sees evaluator keys, author route labels, target responses, judge votes, or future turns.

Frozen router prompt:

> Decide whether deep FULL reasoning is likely to add decision-relevant quality beyond an unstructured answer. Choose FULL only when the current user input materially requires at least one of: (1) distinguishing competing causal mechanisms with discriminating evidence or a consequential test; (2) designing or choosing an intervention under uncertainty where reversibility, monitoring, feedback, constraints, failure modes, or second-order effects can change the action; (3) integrating contradictory or sequential evidence where causal-model revision is decision-critical; (4) a consequential action under materially reducible causal uncertainty. Choose CONTROL for factual retrieval, direct explanation, straightforward computation, established procedure, low-consequence advice, or cases where added causal/engineering analysis is unlikely to change the answer or action. Difficulty, length, technical vocabulary, or the words 'test'/'experiment' alone are not reasons to choose FULL. Return JSON only: {"mode":"FULL|CONTROL","signals":["short signal"],"confidence":0.0}.

Router temperature is fixed to `0` where supported. One route decision is made per case before target generation. Sequential cases are routed from turn 1 only; future turns are not available to the router.

## Fresh routing-validation suite

Use exactly `benchmark/routing_validation_cases_v1.json` once frozen by merge.

Final suite size: `48` cases. The initial planning minimum was 40; before any model output existed, eight additional already-authored fresh cases were retained to improve domain coverage. No scientific threshold or route rule changed as a consequence.

Design balance:

- 12 domains × 4 cases each;
- 24 author-designed `FULL_VALUE` cases and 24 `CONTROL_VALUE` cases for diagnostics only;
- 12 sequential cases;
- at least 24 distractor/misleading-surface cases;
- at least 24 action-requiring cases;
- at least 10 adversarial surface mismatches, including CONTROL-value cases that mention tests/experiments and FULL-value cases without framework-stage vocabulary.

The author-designed route labels are **not** ground truth for the primary endpoint. They are reported only as diagnostic classification metadata. Routing validity is determined by blinded response quality.

No case may be reused, paraphrased, or structurally cloned from the exposed 36-case framework-validation suite or v0.5–v0.11 development cases.

## Target and evaluator

Target:

- provider: Z.AI;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- model: `glm-5.1`;
- conditions generated on every case: CONTROL and FULL;
- 3 stochastic target generations per case and condition.

Judge:

- provider: Z.AI;
- endpoint: same Z.AI endpoint;
- model: `glm-5.3-flash`;
- distinct-model, same-family/provider Tier-1B evidence only;
- 3 blinded randomized pairwise votes per `(case, generation replicate)` for FULL vs CONTROL.

The inability to obtain a genuinely independent provider/family is an explicit evidence limitation, not silently relaxed independence.

## Policy evaluation without a third target generation

ROUTED does not generate a third answer. For each case and generation replicate, it deterministically selects the already-generated FULL or CONTROL output according to the frozen input-only route.

Let `s` be the aggregate FULL-vs-CONTROL score for a generation replicate (`1` FULL win, `0.5` tie, `0` CONTROL win after judge-vote aggregation).

Then:

- ROUTED vs CONTROL score = `s` if route=FULL, else `0.5`;
- ROUTED vs FULL score = `0.5` if route=FULL, else `1-s`.

Generation-replicate policy scores are averaged within case; cases are the independent units. Confidence intervals use case-clustered bootstrap with 5,000 samples.

This construction avoids extra target stochasticity and ensures the routing decision itself is the only difference between ROUTED and the two fixed policies.

## Primary quality endpoint

Primary benefit comparison:

`ROUTED_vs_CONTROL`.

Routing v1 clears the benefit gate only if:

- point estimate >= `0.60`; and
- case-clustered 95% CI lower bound > `0.50`.

## Quality-preservation guard relative to ALWAYS-FULL

`ROUTED_vs_FULL` is treated as a non-inferiority-style guard, not a superiority claim.

Frozen acceptable-loss margin: `0.05` around the neutral score `0.50`.

The preservation guard passes only if:

- point estimate >= `0.50`; and
- case-clustered 95% CI lower bound > `0.45`.

This is not a formal equivalence test. It is a preregistered operational guard against a router that saves FULL calls by materially degrading reasoning quality.

## Selectivity / cost guard

Only if both quality gates pass, routing efficiency is evaluated.

The selectivity guard passes if:

- FULL invocation rate <= `0.65` across the 48 cases.

Target token and latency totals remain descriptive. They do not rescue a quality-gate failure.

Overall `routing_validation_pass = true` only if all three are true:

1. ROUTED vs CONTROL benefit gate passes;
2. ROUTED vs FULL preservation guard passes;
3. FULL invocation rate <= `0.65`.

## Secondary diagnostics

Report:

- ALWAYS-FULL vs CONTROL overall score and CI;
- route rate overall and by domain;
- diagnostic accuracy against author `FULL_VALUE` / `CONTROL_VALUE` labels;
- false-FULL and false-CONTROL diagnostic rates;
- routing policy score by author route label, domain, sequential status, distractor status, and action requirement;
- per-case route, router signals/confidence, FULL-vs-CONTROL score, and resulting policy contribution;
- judge agreement/unanimity;
- target and router token/latency diagnostics.

Author labels cannot override the quality endpoint.

## Stop rules

Once any routing-validation target output exists:

- do not edit the router prompt, threshold, model, route action space, suite, evaluator rubric, replicate counts, success thresholds, or policy-score construction;
- do not remove difficult or misrouted cases;
- do not reclassify a failed primary result as success using author route labels;
- do not tune routing on this suite after exposure.

A failed routing validation remains failed. Any redesigned router requires a new development cycle and another untouched routing-validation suite.

## Interpretation

If all three gates pass, the supported claim is limited to:

> On this fresh routing-validation suite, a frozen input-only GLM-5.3-Flash controller selectively invoked the frozen FULL GLM-5.1 reasoning policy, retained a preregistered quality benefit over CONTROL, was not materially worse than ALWAYS-FULL within the frozen guard, and used FULL on no more than 65% of cases under same-family/provider blinded judging.

This does not establish universal routing optimality, cross-provider generalization, or cost optimality.