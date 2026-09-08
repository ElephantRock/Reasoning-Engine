# Held-Out Framework Validation v1 — Preregistration

Status: preregistered after Behavioral Fidelity v0.11 development closure and before any model output or quality judgment has been generated on `benchmark/heldout_cases_v1.json`.

Role: first framework-level held-out validation. This is a new hypothesis test, not a continuation of the null selective-controller candidate.

## Why this validation exists

Behavioral Fidelity v0.11 closed the TEST/ENGINEER selective-controller development path with no module surviving the already-frozen selection rule. The original `HELDOUT_VALIDATION_V1_PREREG.md` therefore remains historically valid but cannot launch an intervention validation because its candidate is empty.

The strongest surviving development hypothesis is broader: structured reasoning prompts appeared to improve reasoning quality over the uncontrolled baseline in v0.5. This validation tests that framework-level claim directly.

No v0.11 threshold, module wording, case, or outcome is used to tune the FULL or COMPACT prompts.

## Frozen held-out suite

Use exactly `benchmark/heldout_cases_v1.json` as frozen before v0.11 resolved.

- suite freeze commit: `2975376ade5df0863340ce10aa867f3b3e0e1404`
- current Git blob SHA: `5fa2ab6f678728124b93ea9dd6c9158e5d6e9698`
- cases: 36
- original author strata: 9 TEST, 9 ENGINEER, 6 BOTH, 12 NONE
- nine substantive domains, four cases each
- the original task-stratum labels are used only for subgroup robustness reporting in this experiment; no routing or conditional prompt injection occurs.

The suite was originally authored for held-out selective-control validation, so its task mix is enriched for mechanism testing and intervention-design problems. A positive result generalizes to this frozen suite and task mix, not automatically to all reasoning tasks.

No held-out target outputs or quality judgments have been observed before this preregistration.

## Frozen conditions

Three conditions are generated for every case and every replicate:

### CONTROL

No reasoning-specific system instruction (`None`). This is the same uncontrolled baseline concept used by v0.5 `BASELINE`.

### COMPACT

Exact `benchmark/pilot.py::COMPACT` string. No changes after this preregistration.

### FULL

Exact `benchmark/pilot.py::FULL` string. No changes after this preregistration.

All three conditions use the same target model, endpoint, user messages, generation settings, and case evidence.

## Target configuration

The primary validation target is frozen to:

- provider: Z.AI
- endpoint: `https://api.z.ai/api/coding/paas/v4`
- model: `glm-5.1`
- target family label: `glm`

Changing the target model/provider creates a different validation experiment.

## Comparisons

### Primary

`FULL_vs_CONTROL`

This directly tests the surviving framework-level hypothesis from v0.5.

### Secondary

`COMPACT_vs_CONTROL`

This tests whether the shorter structured scaffold also generalizes.

### Architecture comparison

`FULL_vs_COMPACT`

This tests whether the additional explicit structure of FULL provides held-out quality beyond COMPACT. It is secondary and is not allowed to rescue a failed primary endpoint.

## Generation and judging

- 3 stochastic target generations per case and condition;
- 3 blinded quality votes per generated pair;
- randomized A/B orientation for every vote;
- judge votes aggregate within `(case_id, generation_replicate)` first;
- generation-replicate scores are averaged within case;
- the 36 cases are the independent units;
- uncertainty uses case-clustered bootstrap with 5,000 samples;
- no token, latency, condition label, prompt text, or cost information is shown to the quality judge.

## Independent evaluator requirement

The run must fail before any held-out target generation unless all of the following are configured:

1. a separate judge API credential;
2. judge model ID different from `glm-5.1`;
3. judge model-family label different from `glm`;
4. judge provider label different from `zai`;
5. normalized judge base URL different from the Z.AI target endpoint;
6. explicit independent-evaluator attestation;
7. a preflight connectivity/JSON-response check against the judge succeeds before any target call.

A same-family or same-provider judge is calibration, not this validation.

## Primary endpoint and success rule

For each case, aggregate `FULL_vs_CONTROL` judge votes within each generation replicate, then average the three generation scores. The primary endpoint is the mean of the 36 case scores.

Framework validation passes only if:

- `FULL_vs_CONTROL` point estimate is `>= 0.60`; and
- case-clustered 95% bootstrap lower bound is `> 0.50`; and
- no original author stratum with at least six cases has mean `FULL_vs_CONTROL < 0.45`.

These thresholds are fixed before held-out outputs exist.

## Secondary interpretation

`COMPACT_vs_CONTROL` is evaluated with the same statistical success rule (`score >= 0.60` and `CI95 low > 0.50`) but is secondary.

`FULL_vs_COMPACT` is reported with its case-clustered interval and subgroup breakdown. It is not a formal equivalence test. Directional interpretation is:

- score `> 0.55`: evidence direction favors FULL;
- score `< 0.45`: evidence direction favors COMPACT;
- score in `[0.45, 0.55]`: no material directional separation on this suite.

No architecture choice may override a failed `FULL_vs_CONTROL` primary validation claim.

## Robustness reporting

Report every comparison:

- overall;
- by original author task stratum;
- by domain;
- sequential vs single-turn;
- distractor vs non-distractor;
- requires-action vs non-action;
- per-case scores and win/tie/loss;
- judge agreement and unanimity;
- target token and latency diagnostics.

No subgroup may be silently excluded.

## Missing data

No case may be dropped for poor model performance. Provider/runtime errors may use only the existing deterministic retry policy. If a shard remains incomplete, the validation run is incomplete and no positive validation claim is permitted from a partial primary endpoint.

## No post-exposure tuning

Once any held-out target output or quality vote exists:

- do not edit CONTROL, COMPACT, or FULL;
- do not modify the 36 cases or subgroup labels;
- do not change evaluator rubric, judge model, thresholds, replicate counts, or pair definitions;
- do not remove cases except objective file/runtime corruption documented without outcome inspection;
- do not reinterpret a failed endpoint as validation via a secondary comparison.

A failed result remains a failed held-out framework validation. Any redesign requires a new development cycle and a new untouched held-out suite.

## Interpretation matrix

If FULL passes the primary endpoint and COMPACT also passes:

- structured prompting generalizes on this held-out suite;
- `FULL_vs_COMPACT` determines only whether added depth shows directional incremental value.

If FULL passes and COMPACT fails:

- evidence supports the fuller framework configuration on this suite.

If COMPACT passes but FULL fails:

- the broad claim `structured prompting can help` may still be supported secondarily, but the preregistered FULL primary validation fails; the project must report both facts explicitly.

If neither passes:

- the v0.5 development advantage did not generalize to this held-out suite under the tested target/evaluator configuration.

No outcome validates autonomous routing. Routing and cost optimization remain downstream questions only after a quality-valid framework configuration exists.

## Cost policy

Cost and latency are descriptive only. They cannot change the validation conclusion.