# Reasoning Framework v0.2 — candidate, not yet empirically validated

The strongest architectural change suggested by the harness audit is to make reasoning depth an explicit routing decision rather than loading the full protocol for every task.

## Proposed architecture

**Route → Reason → Verify → Act → Observe**

where `Reason` selects one of three modes:

```text
DIRECT
  established/trivial task
  → answer

COMPACT
  Problem
  → First Principle
  → Mechanism
  → Evidence
  → Solution

FULL
  Observe
  → Diagnose
  → Derive
  → Hypothesize
  → Predict
  → Test
  → Revise
  → Engineer
```

## Routing rule

Choose the least expensive mode that preserves decision reliability.

Use FULL when one or more are material:

- multiple plausible causal explanations;
- contradictory or sequential evidence;
- disputed mechanism;
- high-cost or difficult-to-reverse intervention;
- important second-order effects;
- substantial decision-critical uncertainty.

Use COMPACT when the mechanism is mostly established but reasoning is still needed around one or a few decisive constraints or uncertainties.

Use DIRECT when further causal decomposition has negligible decision value.

## Escalation rule

Mode selection is not permanent.

```text
DIRECT → COMPACT
if a non-trivial assumption or ambiguity appears.

COMPACT → FULL
if competing mechanisms, contradiction, or material uncertainty appears.
```

De-escalate presentation once the decision is resolved; internal complexity should not force verbose output.

## Full-mode refinements

1. **Stage relevance over ritual completion.** A stage may be skipped when its epistemic function is already satisfied by established evidence.
2. **Minimum meaningful hypothesis competition.** Generate alternatives only when ambiguity is material; do not manufacture weak hypotheses to satisfy a quota.
3. **Root/proximate distinction.** Represent causal chains so the initiating mechanism is not confused with a downstream failure state.
4. **Measurement-process diagnosis.** Treat changes in instrumentation, reporting, sampling, and observation generation as candidate explanations when the measured quantity changes.
5. **Evidence budget.** Seek additional information only when it has a realistic chance of changing the decision.
6. **Prospective vs realized outcome.** Distinguish predicted decision quality from observed intervention effectiveness.
7. **Intervention-as-test.** Under uncertainty, prefer safe reversible actions that both improve the system and generate discriminating evidence when expected value is competitive.

## Proposed controller core

```text
ROUTE
  choose DIRECT / COMPACT / FULL

REASON
  execute only the epistemically necessary stages

VERIFY
  identify the decision-critical claim
  check evidence quality
  expose material assumptions
  test robustness across surviving models

ACT
  choose the best justified intervention or answer

OBSERVE
  when action has real-world consequences, compare predicted vs actual result
  and re-enter the loop if the model is contradicted
```

## Falsification criterion

Do not promote this candidate to the governing framework unless the benchmark shows that it improves decision quality and/or reduces reasoning cost relative to the existing controller on held-out cases.

In particular, the routing layer is justified only if:

1. it preserves or improves quality on FULL-need cases;
2. it reduces unnecessary reasoning cost on DIRECT/COMPACT cases;
3. routing mistakes do not create more under-reasoning than the saved cost justifies.
