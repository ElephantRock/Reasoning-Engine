# Held-Out Framework Validation v1 — GLM-5.3-Flash execution recovery

## Status

This document is an execution-recovery addendum for the preregistered Tier-1B cross-model, same-family validation. It does not modify any scientific endpoint, case, prompt, model, replication count, vote count, randomization rule, threshold, subgroup rule, or aggregation method.

Source workflow run: `34232674771`.

The source run passed its frozen preflight and completed all target generations in every shard. Shard 0 completed. Shards 1–5 terminated during judge-vote collection because GLM-5.3-Flash occasionally returned output that the legacy JSON parser could not parse. Observed parser failures included valid JSON followed by extra text and syntactically malformed JSON. The aggregate job therefore did not run.

This is classified as an execution/parser failure, not a failed scientific validation result.

## Outcome-blind repair rule

The recovery design was fixed from workflow status, exception traces, and progress logs only. Partial vote winner distributions were not inspected before defining this repair.

The recovery is strictly mechanical:

1. Restore each shard checkpoint artifact from source run `34232674771`.
2. Require exactly all 54 preregistered target-run keys in each shard. If any target run is missing, abort. Target regeneration is forbidden.
3. Retain every already-recorded valid judge-vote key exactly as stored.
4. Request only missing preregistered judge-vote keys.
5. Preserve the original deterministic A/B orientation seed for each `(case, replicate, pair, vote_index)`.
6. Parse the first complete JSON object if a response contains a valid JSON object followed by trailing text.
7. Never infer or repair malformed JSON. A syntactically malformed response, a response containing no complete JSON object, or a parsed object without `winner` in `{A, B, TIE}` is a formatting failure and is not scored.
8. Retry only that same missing vote, with the same pair and orientation, up to three response-format attempts. A successful retry supplies the single preregistered vote; failed formatting attempts are not additional votes.
9. Preserve the original 3 target generations, 3 blinded votes, six-shard case allocation, case-clustered bootstrap, thresholds, and report interpretation tier.

## Frozen scientific design

Unchanged from the Tier-1B preregistration:

- target: `glm-5.1`
- judge: `glm-5.3-flash`
- provider/endpoint: Z.AI coding endpoint for both
- evaluator classification: cross-model, same-family; not independent-provider
- suite: frozen 36 held-out cases
- conditions: CONTROL, COMPACT, FULL
- target generations: 3 per case/condition
- judge votes: 3 per generated pair
- primary: FULL vs CONTROL
- primary point-estimate threshold: `>= 0.60`
- primary case-clustered 95% CI lower-bound rule: `> 0.50`
- robustness floor: no qualifying task stratum below `0.45`
- COMPACT vs CONTROL and FULL vs COMPACT remain secondary
- cost remains descriptive
- no routing

## Source checkpoint provenance

Artifacts retained from source run `34232674771`:

| Shard | Artifact ID | SHA-256 digest |
|---:|---:|---|
| 0 | 10068308536 | `sha256:2ad2b5f56d2e729baa8d02d3d646f1fe6e81526061e041b81261acaced5305b3` |
| 1 | 10062573733 | `sha256:1c78104d5ab7c22dba536efde85311292a2559db04dcb629437b570850a3628e` |
| 2 | 10062288787 | `sha256:6928631fd4b97f4a16ac71b424dbd3b1001400f07b3256d6807cd4987c7844ba` |
| 3 | 10065539315 | `sha256:8701eaf2604f9ccc201baded1af16a3c8108c7671d2378f9fc9a32529709eee9` |
| 4 | 10070882849 | `sha256:a49249ae575864da91f0f9ab5ebef67f2bcafa909af92629b38d80b7bc685f72` |
| 5 | 10068511569 | `sha256:c9bd55f34fba7a026b9c6d9bc20cc781db4e5b43cef1055fc9c0016e59e1a4f3` |

## Interpretation

If recovery completes, the aggregate is interpreted under the original Tier-1B rules. The execution repair does not upgrade evaluator independence. Any positive finding remains cross-model, same-family held-out evidence and must not be described as independent-provider validation.
