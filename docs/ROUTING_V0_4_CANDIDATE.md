# Routing v0.4 Candidate

## Status

Candidate only. Derived from Measurement v0.3 Stress Run 001 and not yet validated.

The central change is to replace **complexity classification** with **expected marginal decision value of deeper reasoning**.

## Objective

Choose the least expensive reasoning depth that is likely to preserve the best available decision.

Formally, for reasoning mode `m`:

`m* = argmin Cost(m)`

subject to:

`DecisionQuality(m) >= DecisionQuality(best available mode) - tolerance`

The benchmark cannot know this quantity before running all modes, so the router estimates it prospectively and the evaluation measures regret retrospectively.

## Routing policy

### DIRECT

Use DIRECT when the decision is effectively invariant under the supplied uncertainty.

Typical triggers:

- deterministic calculation;
- strict dominance;
- established mechanism with no material ambiguity;
- unresolved information cannot plausibly change the action;
- additional analysis has negligible decision value.

### COMPACT

Use COMPACT when a small number of explicit decision hinges dominate the problem.

Typical triggers:

- one material reducible uncertainty;
- one hard constraint requiring verification;
- one or a few plausible mechanisms with a cheap discriminating test;
- reversible intervention can resolve uncertainty before commitment;
- technical difficulty or high stakes exist, but the next action is still governed by a focused test.

Compact loop:

**Problem → First Principle → Mechanism → Evidence → Solution**

### FULL

Use FULL when deeper modeling can plausibly change the action because focused reasoning may leave material failure modes unresolved.

Typical triggers:

- multiple materially plausible causal mechanisms;
- measurement-generation process may itself be misleading;
- sequential or contradictory evidence requires revision;
- adversarial framing pressures unsupported causality;
- irreversible/high-cost intervention depends on locating the correct mechanism;
- feedback loops, bottleneck migration, second-order effects, or model uncertainty materially affect intervention quality.

Full loop:

**Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**

## Decision hinge

Before selecting a mode, the router should identify:

> What unknown, mechanism, constraint, contradiction, or feedback effect could actually change the next action?

The number of words required to explain the task is irrelevant. The key variable is whether additional reasoning can change the decision.

## Stop rule

Escalation stops when additional reasoning is unlikely to change the recommended action enough to justify its cost.

This is the routing analogue of the framework's general stopping criterion:

> continue while uncertainty is both material and reducible; stop when further information or analysis has insufficient decision value.

## Evaluation: replace mode-label accuracy with regret

Legacy metric:

`selected_mode in hand_authored_expected_modes`

This remains diagnostic but is no longer primary.

Routing v0.4 introduces two retrospective metrics.

### Quality regret

For each held-out case, compare ADAPTIVE against BASELINE, COMPACT, and FULL using blinded pairwise judging.

A routing failure occurs when any fixed reasoning depth produces a meaningfully better answer/decision than ADAPTIVE.

Primary routing statistic:

`quality_noninferiority_rate = cases where no fixed depth beats ADAPTIVE / all cases`

### Cost regret

When ADAPTIVE ties or beats a fixed mode, compare its token cost with the cheapest fixed mode that is not better than ADAPTIVE.

This detects unnecessary escalation even when final answer quality is preserved.

The target is therefore not maximum reasoning quality in isolation. It is a Pareto objective:

**preserve decision quality while minimizing avoidable reasoning cost.**

## Held-out evaluation suite

Routing v0.4 adds six new RF-H cases that were not used to derive the router:

- RF-H01 — strict dominance / irrelevant uncertainty → DIRECT hypothesis;
- RF-H02 — hard gating constraint with cheap verification → COMPACT hypothesis;
- RF-H03 — competing mechanisms but one cheap reversible discriminating test → COMPACT hypothesis;
- RF-H04 — measurement-process distortion plus revision → FULL hypothesis;
- RF-H05 — sequential contradiction and targeted intervention evidence → FULL hypothesis;
- RF-H06 — irreversible capital decision with multiple bottlenecks and second-order effects → FULL hypothesis.

The hand-authored modes are retained only as theory labels. Empirical regret is the primary routing evaluation.

## Research discipline

The RF-S stress cases informed this router and must not be treated as held-out evidence for Routing v0.4.

Promotion requires success on the RF-H held-out suite and replication. If Adaptive preserves quality but repeatedly spends more than the cheapest non-inferior fixed mode, the router is still inefficient. If a fixed mode repeatedly beats Adaptive, the routing policy is under-escalating or misclassifying the decision hinge.
