# Stage Ablation v0.6.1 — Replication Results

## Status

v0.6.1 is a **development/calibration experiment**, not held-out framework validation.

The corrected leave-one-capability-out design compared the production `FULL` prompt with an otherwise identical prompt where one explicit instruction fragment was removed for `DIAGNOSE`, `PREDICT`, `TEST`, `REVISE`, or `ENGINEER`.

Two runs are now available:

- original v0.6.1: 1 target-generation replicate per case, 3 blinded quality votes per generated pair;
- preregistered replication: 3 additional target-generation replicates per case, 3 blinded quality votes per generated pair.

The replication used the same runner, cases, prompt construction, model, endpoint, judge design, and aggregation logic. Only target-generation replication increased.

## Original one-generation signal

The original run produced an overall `FULL vs ABLATED` score of approximately `0.667`.

Stage scores:

- `DIAGNOSE`: `0.000`
- `PREDICT`: `0.833`
- `TEST`: `0.917`
- `REVISE`: `0.833`
- `ENGINEER`: `0.750`

This looked like a strong positive signal for four components and a negative signal for `DIAGNOSE`.

## Three-generation replication

Workflow run: `34044565425`

The preregistered three-generation replication completed successfully.

Overall `FULL vs ABLATED` score:

`0.433`

95% case-clustered interval:

`0.250–0.606`

Across 30 case-generation pairs:

- 11 FULL-majority wins;
- 2 ties;
- 17 losses.

Mean repeated-judge agreement was approximately `0.811`.

Stage scores in the replication:

- `DIAGNOSE`: `0.500`
- `PREDICT`: `0.528`
- `TEST`: `0.667`
- `REVISE`: `0.333`
- `ENGINEER`: `0.139`

The original stage pattern therefore did **not** replicate.

## Combined four-generation evidence

The preregistered combination rule is to average target-generation measurements within each case and continue to treat the case, not the generation, as the independent cluster.

Combined stage scores:

- `DIAGNOSE`: `0.375`
  - `RF-V06-DG01`: `0.625`
  - `RF-V06-DG02`: `0.125`
- `PREDICT`: `0.604`
  - `RF-V06-PR01`: `0.500`
  - `RF-V06-PR02`: `0.708`
- `TEST`: `0.729`
  - `RF-V06-TS01`: `0.667`
  - `RF-V06-TS02`: `0.792`
- `REVISE`: `0.458`
  - `RF-V06-RV01`: `0.708`
  - `RF-V06-RV02`: `0.208`
- `ENGINEER`: `0.292`
  - `RF-V06-EN01`: `0.250`
  - `RF-V06-EN02`: `0.333`

Combined overall score is approximately `0.492`, with a case-bootstrap interval of roughly `0.346–0.629`.

## What the raw comparisons revealed

The result should **not** be interpreted as showing that engineering or revision as cognitive capabilities are harmful.

Inspection of the response pairs and judge notes exposed a more basic identification problem:

1. Removing an instruction fragment frequently did not remove the corresponding behavior.
2. The cases themselves often explicitly requested the target behavior, for example by asking for an experiment, an updated diagnosis, or an intervention plan.
3. Strong models can produce diagnosis, revision, and engineering behavior from task semantics and prior capability even without the explicit system instruction.
4. In several `ENGINEER` pairs, the ablated response still exhibited excellent mechanism-linked engineering and won because of ordinary generation differences such as better statistical calibration, a better guardrail, or avoiding an unsupported causal overclaim.
5. In `RF-V06-RV02`, the repeated losses were dominated by a quantitative window-alignment/arithmetic error in some FULL generations, while both conditions still performed the intended revision behavior.
6. `DIAGNOSE` split strongly by case rather than showing a stable family effect.

Therefore v0.6.1 primarily estimates the marginal effect of **mentioning an instruction fragment inside the current FULL prompt**, not the causal value of possessing or executing the underlying capability.

## Consequence

The next experiment must include a manipulation check.

A component-effect claim is interpretable only if the treatment first demonstrably changes the target reasoning behavior.

The next measurement therefore separates:

`instruction -> target behavior`

from:

`target behavior -> reasoning quality`

This is the purpose of Capability Identification v0.7.

## Current evidence boundary

The strongest component signal that survived the four-generation v0.6.1 evidence is `TEST`, followed by a weaker positive direction for `PREDICT`.

However, no component should be promoted, removed, or rewritten solely from v0.6.1 because the manipulation was not verified.

The production protocol remains frozen while the identification problem is investigated.
