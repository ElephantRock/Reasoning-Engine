# Held-Out Validation v1 — Preregistration

Status: protocol frozen before Behavioral Fidelity v0.11 results are available.

Role: first genuinely fresh validation phase after development/calibration. This document fixes the validation design; it does not launch the validation run and it does not change the production reasoning protocol.

## Objective

Test whether the frozen candidate reasoning controller improves reasoning quality on fresh cases that were not used to design, tune, select, or measure the development-stage prompts.

The validation target is not protocol compliance. The primary outcome is reasoning quality.

## Candidate selection

The candidate is determined mechanically from the already-merged post-v0.11 decision protocol.

For each of TEST and ENGINEER:

1. the v0.11 independent behavioral-fidelity lift must satisfy `TARGET - CONTROL >= 0.15` on the 0–1 composite;
2. `TARGET vs CONTROL` quality must be `>= 0.667`;
3. `TARGET vs ATTENTION` quality must be `>= 0.667`;
4. neither of the two v0.11 family cases may score below `0.5` against either comparator.

A module that passes is frozen verbatim. A module that fails is excluded. No wording changes are permitted after v0.11.

## Frozen routing policy

Routing is rule-based and fixed before validation results.

- TEST trigger: use TEST only when the problem contains material mechanism uncertainty and the next justified decision can be materially improved by evidence that separates or falsifies competing explanations.
- ENGINEER trigger: use ENGINEER only when a mechanism is sufficiently supported and the task requires an intervention/design under constraints where robustness, reversibility, monitoring, rollback, side effects, or second-order effects are materially decision-relevant.
- BOTH trigger: if both rules hold, apply TEST first and ENGINEER second.
- NONE: use the neutral CONTROL core only.

The router may activate only modules that survived v0.11 selection. The routing rule itself may not be tuned on held-out outcomes.

## Held-out suite

Target size: **36 fresh cases**.

Cases must be written without looking at candidate-vs-control model outputs. No development case from v0.5–v0.11 may be reused, paraphrased, or structurally cloned.

Strata:

- 9 TEST-relevant cases;
- 9 ENGINEER-relevant cases;
- 6 BOTH-relevant cases;
- 12 NONE/general-control cases.

Across the 36 cases, include at least six substantive domains (for example software/operations, physical systems, policy/organization, science/measurement, finance/resource allocation, and everyday planning) with no domain contributing more than 8 cases.

At least 12 cases must be sequential/multi-turn. At least 12 must contain plausible distractors or misleading-but-non-decisive evidence. At least 12 must require explicit action or decision under constraints. These categories may overlap.

Case prompts must not use the framework stage names or directly instruct the target behavior being measured.

## Comparisons

Primary comparison:

`CANDIDATE_CONTROLLER vs CONTROL`

Secondary specificity comparison:

`CANDIDATE_CONTROLLER vs ATTENTION`

Development reference comparison, descriptive only:

`FULL vs CONTROL`

The FULL comparison is not used to select or modify the candidate.

## Generation and judging

- 3 stochastic target generations per case and condition.
- 3 blinded quality votes per generated pair.
- randomized A/B orientation for every vote.
- aggregate judge votes within `(case_id, generation_replicate)` first;
- average generation replicates within case;
- treat the 36 cases, not generations or judge votes, as the independent units;
- bootstrap case clusters for uncertainty intervals.

## Evaluator independence

Strong validation requires an evaluator that is independent of the target model family.

The validation run must not launch unless either:

1. a judge model from a different model family/provider is configured; or
2. a preregistered human-blinded evaluation path is used for the primary comparison.

Using `glm-5.1` to judge `glm-5.1` is not sufficient for the primary validation claim.

A human-reviewed audit subset of at least 12 cases is recommended even when an independent model judge is available.

## Primary endpoint

For each case, compute the case-level CANDIDATE_CONTROLLER score against CONTROL after vote aggregation and generation averaging. The primary endpoint is the mean across 36 cases.

The primary success criterion is deliberately stricter than merely exceeding 0.5:

- point estimate `>= 0.60`; and
- case-clustered 95% bootstrap lower bound `> 0.50`.

This threshold is fixed before held-out outputs exist.

## Specificity/support criterion

`CANDIDATE_CONTROLLER vs ATTENTION` is supporting evidence, not the primary endpoint.

Support is considered directionally consistent if its point estimate is `>= 0.55`. Failure of this secondary criterion does not erase a positive primary result, but it weakens the claim that gains are attributable to the specific controller rather than generic extra deliberation.

## Harm / robustness checks

Report, without post-hoc exclusion:

- score by routing stratum: TEST, ENGINEER, BOTH, NONE;
- score by domain;
- score on sequential vs single-turn cases;
- score on distractor/stress vs clean cases;
- per-case win/tie/loss;
- judge agreement and unanimity;
- output-token and latency diagnostics.

A candidate is not considered robust if any preregistered routing stratum with at least 6 cases has a mean primary score `< 0.45`, even if the overall endpoint passes.

## Missing data and failures

No case may be silently dropped because the candidate performs poorly.

Provider/runtime failures may be retried only under a logged deterministic retry policy. If a case remains incomplete, report it and perform both available-case and conservative sensitivity analyses.

## No tuning after exposure

Once any held-out candidate output or quality judgment has been observed:

- no prompt/module wording changes;
- no routing-rule changes;
- no threshold changes;
- no case removals or replacements except objective corruption/runtime defects documented before outcome inspection;
- no evaluator rubric changes.

A failed validation remains a failed validation. Any subsequent redesign starts a new development cycle and requires a new held-out suite.

## Interpretation

If the primary endpoint and robustness checks pass, the project may claim that the frozen candidate controller improved reasoning quality on this held-out suite under the tested target/evaluator configuration.

It still should not claim universal reasoning improvement without replication across additional model families and evaluators.

If the primary endpoint fails, do not resume routing/cost optimization. Return to model diagnosis only after formally closing this validation attempt.

## Cost policy

Token usage and latency remain descriptive during validation. Cost optimization resumes only after a quality-valid candidate exists.
