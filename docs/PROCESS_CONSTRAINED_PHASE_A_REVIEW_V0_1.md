# Process-Constrained ARC Phase A — Environment Review v0.1

Status: **review finding; no paid experiment authorized by this document**.

This review evaluates the deterministic Phase-A prototype merged in PR #49 against the safeguards in `ADAPTIVE_REASONING_CONTROLLER_V0_2_PLAN.md`: common environment affordances, matched budgets, objective scoring, no answer leakage, and no protocol-induced triviality.

## 1. Review conclusion

The Phase-A runtime successfully demonstrates that an external controller can enforce legal state transitions, budgets, rollback rules, trace logging, and objective environment scoring without any model/API call. That engineering milestone is valid.

However, the original four toy environments are **not suitable as Phase-B experimental environments without hardening**. They are intentionally simple demonstrations, and several of them make the optimal behavior too easy to infer from a single environment response or from hard-coded prerequisites. Using them unchanged in a paid model study would risk measuring environment scaffolding rather than reasoning-process effects.

Phase B therefore remains unauthorized until the hardening requirements below pass static tests.

## 2. Findings by environment

### 2.1 Feasibility / deductive environment

The Phase-A `test_deadline` response returns `minimum_restart_minute` directly. This reveals the numerical answer that the deductive process is supposed to derive. A condition can therefore succeed after querying the environment without demonstrating the intended derivation.

Required correction:

- candidate testing may return feasibility and violated constraints;
- it must not return the exact optimum/minimum answer;
- the terminal score should reward the earliest feasible commitment rather than any arbitrarily late safe answer.

### 2.2 Diagnostic / abductive environment

The Phase-A environment has one fixed hidden cause (`route_change`) and several evidence checks whose outputs strongly cue that cause. A single check can be close to diagnostic, and there is no hidden-state variation across cases.

Required correction:

- use multiple possible hidden causes;
- construct evidence so no single check/outcome uniquely identifies the cause;
- require at least two pieces of evidence for a fully supported diagnosis;
- include multiple hidden causes across the frozen suite.

### 2.3 Planning environment

The Phase-A migration environment is mostly a fixed prerequisite chain. The environment itself rejects unsafe ordering, so a generic condition can discover the correct sequence by following errors. There is no contingent state that requires a genuine checkpoint-dependent branch.

Required correction:

- include a hidden or initially unknown post-cutover health condition;
- require a checkpoint before irreversible finalization;
- include both healthy and unhealthy instances;
- make rollback/abort objectively correct on some cases and completion objectively correct on others;
- count failed environment attempts against the action budget.

### 2.4 Decision environment

The Phase-A pilot is a perfect signal of whether the product is good. This makes value-of-information behavior nearly mechanical and does not test whether the policy can decide when information is worth buying.

Required correction:

- use an explicit prior, asymmetric payoffs, pilot cost, sensitivity, and false-positive rate;
- make the pilot noisy rather than perfectly revealing;
- include cases where the optimal initial action is `pilot`, `buy now`, and `decline now`;
- score policy optimality using expected utility given the information available at the time, while retaining realized utility/regret as secondary outcomes.

## 3. Runtime finding

The Phase-A runtime validates state order, budgets, and non-empty payloads, but it does not yet mechanically validate most state semantics. Nor does it constrain environment-action classes to the protocol states where they are supposed to occur.

For Phase B, an enforced protocol must be more than renamed turns. The hardening runtime must therefore add:

- per-state payload contracts (for example at least two hypotheses in an abductive `HYPOTHESES` state);
- protocol-state action-tag rules (for example evidence acquisition before diagnostic commitment);
- guards that can inspect prior successful trace actions;
- the same underlying environment action universe for specialist and comparison conditions;
- a matched generic scaffold with the same transition range and environment-action budget but without specialist semantic constraints.

These checks establish **observable protocol compliance only**. They do not establish hidden-cognition fidelity.

## 4. Anti-triviality gates before Phase B

The hardened environment suite must pass all of the following before any paid target call:

1. no environment response returns a gold answer, hidden cause, oracle action, or exact optimum that the target is supposed to derive;
2. diagnostic evidence has no single-check outcome that uniquely identifies one hidden cause across the candidate cause set;
3. the planning suite contains at least two distinct objectively optimal terminal branches (complete vs rollback/abort);
4. the decision suite contains at least the three optimal initial policies `pilot`, `buy`, and `decline`;
5. at least one family contains cases where acquiring more information is useful and cases where acquiring more information is unnecessary or dominated;
6. failed environment actions consume budget and remain visible in the trace;
7. specialist and matched-scaffold conditions receive identical environment action universes and equal action budgets;
8. objective scoring is computed entirely from environment state/ground truth, not from condition labels or an LLM judge.

## 5. Consequence

The correct next step is **not** to run Phase B on the original Phase-A toys. The next step is to harden the runtime/environments, freeze a fresh development suite, and then review the Phase-B experiment specification.

The current deployment decision remains unchanged: `DIRECT` for genuinely trivial/deterministic tasks and frozen `FULL` for non-trivial reasoning tasks.