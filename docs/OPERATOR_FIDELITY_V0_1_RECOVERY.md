# Operator Fidelity v0.1 — Frozen Recovery Procedure

Status: **frozen before recovery execution**.

## Trigger

The first paid Stage-0 run (`34710001873`) completed all 48 target generations but failed on the first behavior-judge call because the judge returned no parseable JSON.

The uploaded artifact contains exactly one file, `runs.jsonl`, with all 48 target-generation records and no completed behavior or quality votes.

A subsequent audit of that artifact found a second transport/runtime problem: 20/48 target generations reached the configured `4096` completion-token ceiling. Thirteen of those 20 contain an empty visible answer and seven contain visible text but also hit the ceiling, so all 20 are conservatively treated as incomplete/truncated outputs. The remaining 28 outputs are below the ceiling and are preserved exactly.

Source artifact:

- workflow run: `34710001873`
- artifact id: `10302974552`
- artifact name: `operator-fidelity-v01-results-authorized`
- `runs.jsonl` SHA-256: `730341ae792afc3693d3f233c29e7cf14d914beba7c75d17fefda644fd08b5fb`
- records: `48`
- preserved records: `28`
- records requiring technical regeneration: `20`

No valid behavior or pairwise quality judgment was produced before the failure, so no Stage-0 score had been observed when this recovery rule was frozen.

## Scientific boundary

This recovery does **not** change:

- the six cases;
- the six specialist prompts;
- FULL or CONTROL;
- the behavior rubric;
- the pairwise quality rubric;
- the two-vote behavior design;
- the matching-case pairwise quality design;
- the Stage-1 eligibility thresholds;
- the program decision rule.

It changes only execution mechanics needed to obtain complete visible responses and parseable judgments.

## Target-output preservation rule

The original target cap was `4096` completion tokens.

For each source record:

- preserve the original output exactly if visible text is non-empty **and** recorded completion tokens are `< 4096`;
- regenerate the output only if visible text is empty **or** recorded completion tokens are `>= 4096`.

The recovery runner must verify the source SHA-256 and the exact set of 20 regeneration keys before any paid call.

The 20 regenerated outputs use the same target model, endpoint, temperature, case text, and system prompt as v0.1, with only the completion-token ceiling increased to `16384` to prevent reasoning-token exhaustion. If a regenerated output is empty, has `finish_reason = length`, or reaches the new `16384` ceiling, recovery stops before judging and preserves the partial recovery artifact for a new frozen procedure.

The original 20 capped records remain in the recovery artifact as an audit trail; they are not silently overwritten.

## Judge recovery rule

The original judge cap of `2048` was insufficient for the first behavior judgment and produced no parseable visible JSON.

Recovery uses the same judge model, endpoint, temperature, prompts, rubrics, and requested schemas, but increases the judge completion-token ceiling to `8192`.

For each required vote:

- request JSON mode exactly as before;
- if the returned visible content is empty, malformed JSON, or violates the expected schema, record the failed formatting attempt and retry that same vote;
- allow at most three formatting attempts per required vote;
- count only the first valid schema-conforming response as the vote;
- if three attempts fail, stop and preserve all completed outputs and valid votes; do not regenerate target outputs.

Formatting retries are transport/schema recovery attempts, not additional judge votes.

## Recovery outputs

The recovery artifact must contain at minimum:

- original source `runs.jsonl` or an exact copy/hash reference;
- `invalid_source_runs.jsonl` containing the 20 capped/empty original records;
- `combined_runs.jsonl` containing 28 preserved and 20 recovered target outputs;
- `judge_format_failures.jsonl` for any invalid judge attempts;
- `behavior_votes.jsonl` with exactly 96 valid votes if recovery completes;
- `quality_sanity.jsonl` with exactly 12 valid pairwise votes if recovery completes;
- `summary.json` produced by the already-reviewed Stage-0 aggregation and pathology gates;
- `recovery_meta.json` documenting counts, hashes, caps, models, and source run/artifact identifiers.

## Interpretation

If recovery completes, the resulting `summary.json` is the Stage-0 result. It should be interpreted under the original v0.1 decision rule, with the recovery mechanics disclosed.

If recovery fails before a complete summary is produced, do not infer operator eligibility from partial votes and do not rerun target generation outside another frozen recovery rule.
