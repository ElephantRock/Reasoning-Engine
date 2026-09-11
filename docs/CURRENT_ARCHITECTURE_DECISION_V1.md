# Current Architecture Decision v1

Status: **frozen after Selective Routing v4 stop rule**.

## Decision

Use:

`DIRECT` for genuinely trivial, deterministic, or fully established tasks.

Use:

`FULL` for non-trivial reasoning tasks.

FULL is the frozen protocol:

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`.

## Rationale

1. FULL passed the preregistered 36-case held-out primary endpoint against CONTROL.
2. FULL again favored CONTROL on three subsequent fresh 48-case suites.
3. COMPACT did not pass its held-out secondary success rule and FULL was directionally favored over COMPACT.
4. Routing v1–v3 failed frozen validation criteria for different reasons.
5. v4 text-only empirical routing development produced no candidate that passed all frozen generalization/preservation/selectivity gates.
6. Therefore the evidence supports retaining FULL as the default non-trivial policy rather than deploying an unvalidated selective router.

## Important boundary

This is an **architecture decision under current evidence**, not a validated claim that FULL is optimal for every task.

The held-out data show near-neutral groups, especially no-action / NONE cases. The program simply does not yet have a sufficiently reliable deployment-available predictor for identifying those cases without losing too much quality elsewhere.

## Reopening criteria

Routing development should remain closed unless at least one materially new source of information appears:

- substantially more empirical marginal-value labels;
- a better deployment-available signal than turn-1 text alone;
- a different target model family for which routing structure may differ;
- external benchmark evidence revealing a stable separable regime;
- a validated confidence/calibration signal tied directly to marginal FULL value.

Do not reopen routing merely by retuning semantic prompts, thresholds, or the existing 144 exposed cases.

## Next research priority

The next priority is **generalization and evaluator independence**, not efficiency optimization:

1. independent-family/provider evaluation;
2. human-reviewed blinded subset;
3. cross-target-model replication;
4. external benchmark transfer.
