# Held-Out Framework Validation v1 — GLM-5.3-Flash Judge

Status: preregistered before any held-out output is generated under this evaluator.

## Purpose

This is a Tier-1B cross-model, same-family evaluation of the already-frozen Held-Out Framework Validation v1.

The stronger independent-provider validation path remains unchanged. This path exists because no independent-provider credential is currently configured, while the existing Z.AI credential may provide access to GLM-5.3-Flash.

## Evidentiary classification

Target:
- model: `glm-5.1`
- family: `glm`
- provider: `zai`
- endpoint: `https://api.z.ai/api/coding/paas/v4`

Judge:
- model: `glm-5.3-flash`
- family: `glm`
- provider: `zai`
- endpoint: `https://api.z.ai/api/coding/paas/v4`

The judge is a distinct model, but it is not an independent model family/provider. Therefore a positive result supports only:

> held-out framework improvement under cross-model, same-family evaluation.

It must not be described as independently evaluated held-out validation.

## Frozen scientific design

This path changes no scientific design element from `docs/HELDOUT_FRAMEWORK_VALIDATION_V1_PREREG.md`.

- suite: exact frozen `benchmark/heldout_cases_v1.json`
- suite freeze commit: `2975376ade5df0863340ce10aa867f3b3e0e1404`
- suite git blob SHA: `5fa2ab6f678728124b93ea9dd6c9158e5d6e9698`
- conditions on every case: CONTROL, COMPACT, FULL
- CONTROL: no reasoning-specific system prompt
- COMPACT: exact `pilot.COMPACT`
- FULL: exact `pilot.FULL`
- 36 cases
- 3 target-generation replicates per case/condition
- 3 blinded randomized pairwise judge votes per generated pair
- six execution shards
- pair aggregation within generation replicate, generation replicates averaged within case, and case-level clustered bootstrap
- cost remains descriptive only

Primary comparison:

`FULL_vs_CONTROL`

Primary success rule:

- score >= `0.60`
- case-clustered 95% CI lower bound > `0.50`
- no original author stratum with at least six cases below `0.45`

Secondary comparisons:

- `COMPACT_vs_CONTROL`
- `FULL_vs_COMPACT`

Secondary results cannot rescue a failed primary endpoint.

## Evaluator-specific preflight

Before the first held-out target call, the workflow must verify:

1. target remains exactly GLM-5.1 at the frozen Z.AI coding endpoint;
2. judge is exactly `glm-5.3-flash`;
3. judge model ID differs from the target model ID;
4. family/provider/endpoint are explicitly `glm` / `zai` / frozen Z.AI endpoint;
5. `FRAMEWORK_CROSS_MODEL_SAME_FAMILY_ATTESTATION=true`;
6. a benchmark-free judge-only JSON connectivity probe succeeds.

The same repository `ZAI_API_KEY` may be supplied as both target and judge credential because evaluator independence is not claimed in this tier. The model IDs remain different.

## Stop/interpretation rules

- Do not alter cases, prompts, thresholds, judge rubric, generation count, vote count, aggregation, or routing labels after this preregistration.
- If GLM-5.3-Flash is unavailable to the existing Z.AI credential or endpoint, stop without generating held-out target outputs.
- If the primary endpoint fails, record failure; do not retune within this suite.
- If the primary endpoint passes, the claim is limited to cross-model same-family evaluation until a different-family/provider evaluator is available.
