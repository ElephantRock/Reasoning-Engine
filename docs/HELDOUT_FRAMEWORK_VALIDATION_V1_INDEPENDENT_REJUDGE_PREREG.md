# Held-Out Framework Validation v1 — Independent Rejudge Preregistration

Status: preregistered after completion of the Tier-1B GLM-5.3-Flash evaluation and before any quality vote from the future independent evaluator.

## Role

This experiment independently re-judges the exact frozen target outputs already generated for Held-Out Framework Validation v1.

It is designed to answer:

> Does the FULL-versus-CONTROL held-out quality advantage persist when every quality vote is produced by a genuinely different model family and provider?

This is **not** a new target-generation experiment. It is an evaluator-independence test on fixed held-out outputs.

## Why reuse target outputs

The Tier-1B run completed all target generations and produced a complete held-out report using `glm-5.3-flash` as a distinct but same-family/same-provider judge.

Reusing the exact target outputs has two advantages:

1. evaluator identity becomes the only intentional experimental change;
2. no additional stochastic target-generation variation can be mistaken for an evaluator effect.

The scientific cost is explicit: because the Tier-1B result is already known, this is not a pristine end-to-end held-out replication. It is independent re-evaluation of a fixed held-out sample.

## Frozen source outputs

Source recovery workflow run: `34270142523`.

All 324 target outputs are reused exactly:

- 36 cases;
- 3 conditions: CONTROL, COMPACT, FULL;
- 3 target-generation replicates per case/condition;
- total target runs: 324.

No target API call is permitted in this experiment.

Recovered source artifact SHA-256 digests:

- shard 0: `b4300a47e880f26618648fcc0efffa1068924e75147a3136b1f78acd68922568`
- shard 1: `1aa15f29b546c1fbb1e0d5670062d7be4be02c1acf86144c1c6f1fa13264e863`
- shard 2: `1cd73a393eedf7c8e584dd70ca6036705978b3e6e358c13aba441eb75ae8561c`
- shard 3: `176a0a7aa3507eb6eb7b77d6f726b3b96b081462d1efa5140a126385182e2563`
- shard 4: `ac722072fce97a893e0ce0bc326db42721b3c140ccfeb896b2ab21ad4b57d28f`
- shard 5: `458e78e78ce9c2e9715fd9b9f87673d853c5b1a4cacb3d48bd497b5c8207151b`

The runner must validate, per shard:

- exactly 54 unique target-run keys;
- the frozen held-out suite identifiers;
- exact CONTROL/COMPACT/FULL prompt hashes;
- target `glm-5.1` / family `glm` / provider `zai` / frozen Z.AI endpoint;
- recovery provenance showing all target outputs were retained and target regeneration was forbidden.

If any target-run key or provenance invariant is missing, the shard fails closed. It must never regenerate the target output.

## Independent evaluator requirement

Before any independent quality vote is requested, the configured judge must satisfy all of the following:

1. a dedicated independent judge API credential is present;
2. judge model ID differs from `glm-5.1`;
3. judge family label differs from `glm`;
4. judge provider label differs from `zai`;
5. normalized judge endpoint differs from the frozen Z.AI target endpoint;
6. `FRAMEWORK_INDEPENDENT_EVALUATOR_ATTESTATION=true`;
7. a benchmark-free connectivity/JSON probe succeeds.

The evaluator must be chosen for availability and genuine independence, not because it is expected to reproduce or overturn the Tier-1B result.

Once an evaluator is configured and the first independent vote is requested, its model, family, provider, endpoint, rubric, temperatures/settings, and vote count are frozen for this experiment.

## Frozen judging design

The following remain exactly as in Held-Out Framework Validation v1:

- pair definitions:
  1. `FULL_vs_CONTROL` — primary;
  2. `COMPACT_vs_CONTROL` — secondary;
  3. `FULL_vs_COMPACT` — secondary architecture comparison;
- 3 blinded randomized judge votes per generated pair;
- exact deterministic A/B orientation seed from the original experiment;
- exact quality rubric;
- pair aggregation within `(case_id, generation_replicate)`;
- generation-replicate scores averaged within case;
- 36 cases as independent units;
- 5,000-sample case-clustered bootstrap;
- all subgroup reports retained;
- cost excluded from quality judgment.

Total new independent judge votes: `972`.

No GLM-5.3-Flash vote is reused.

## Format handling

Before any independent vote exists, the response-format policy is frozen to:

- accept the first complete JSON object in a response;
- allow surrounding/trailing text around that complete object;
- never repair malformed JSON;
- never infer a winner from prose;
- malformed JSON or an invalid winner field is a non-vote;
- retry the same vote key up to three format attempts;
- preserve the same A/B orientation on every format retry.

Transport/provider failures remain execution failures, not scientific outcomes.

## Primary endpoint and thresholds

The primary endpoint remains the frozen `FULL_vs_CONTROL` mean case score.

The original preregistered success rule is reused without modification:

- point estimate >= `0.60`;
- case-clustered 95% bootstrap lower bound > `0.50`;
- no original author task stratum with at least six cases below `0.45`.

Secondary interpretation remains unchanged:

- `COMPACT_vs_CONTROL` uses the same `0.60` / CI-lower-bound rule;
- `FULL_vs_COMPACT > 0.55` direction favors FULL;
- `< 0.45` direction favors COMPACT;
- `[0.45, 0.55]` means no material directional separation;
- no secondary endpoint can rescue a failed primary endpoint.

## Interpretation

If the primary endpoint passes under this independent evaluator:

> The fixed held-out target outputs show a FULL-versus-CONTROL quality advantage under independent-family/provider judging.

That would materially strengthen the Tier-1B result by reducing evaluator-family/provider dependence.

It would **not** by itself establish:

- a fresh end-to-end held-out replication;
- generalization to a different target model family;
- universal benefit across all task types;
- autonomous routing validity;
- cost optimality.

If the primary endpoint fails, the project must record evaluator dependence or unresolved evaluator disagreement. The Tier-1B result must not be promoted to independent validation.

## No post-exposure tuning

Once any independent vote exists:

- do not alter source target outputs;
- do not change cases, prompts, pair definitions, thresholds, rubric, evaluator identity, replicate counts, vote counts, or subgroup labels;
- do not inspect partial results to change the experiment;
- do not substitute another evaluator after seeing an unfavorable result under the configured independent evaluator.

Any further confirmatory experiment after that requires a separately preregistered design.
