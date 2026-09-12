# Operator Fidelity v0.1 — Frozen Recovery Procedure 2

Status: **frozen before second recovery execution**.

## Trigger

Recovery 1 (workflow run `34720490036`) correctly preserved the original source artifact and began regenerating the 20 outputs that had hit the original 4096 completion-token ceiling. Ten capped outputs were successfully recovered with non-empty visible responses, `finish_reason = stop`, and completion-token counts below the Recovery-1 ceiling of 16384.

Recovery 1 then stopped, as predeclared, when `ARC-V01-DT01 / DEDUCTIVE_CONSTRAINT` again exhausted the target completion budget:

- completion tokens: `16384`;
- finish reason: `length`;
- visible response: empty.

No behavior or quality judgment was attempted in Recovery 1. Therefore no Stage-0 score or judge vote has been observed.

## Frozen sources

Original Stage-0 source:

- workflow run: `34710001873`;
- artifact id: `10302974552`;
- artifact name: `operator-fidelity-v01-results-authorized`;
- `runs.jsonl` SHA-256: `730341ae792afc3693d3f233c29e7cf14d914beba7c75d17fefda644fd08b5fb`;
- 48 original case/condition records.

Recovery-1 partial artifact:

- workflow run: `34720490036`;
- artifact id: `10304964963`;
- artifact name: `operator-fidelity-v01-recovery-results`;
- `combined_runs.jsonl` SHA-256: `30d47ec2410da62114277b46a59cbb7840b6a57dc94fbe6726ffe03eb501d07a`;
- 34 records reached before the stop;
- 24 are preserved original outputs;
- 10 are successful Recovery-1 target regenerations.

The ten successful Recovery-1 regenerations are preserved exactly in Recovery 2. They are not regenerated again.

## Recovery-2 target rule

Construct the 48-output target set as follows:

1. preserve all 28 original outputs whose visible text is non-empty and whose original completion-token count is below 4096;
2. preserve the 10 successful Recovery-1 regenerated outputs exactly;
3. regenerate only the remaining 10 originally capped outputs that do not yet have a successful recovered response.

The remaining ten keys are frozen as:

- `ARC-V01-DT01 / DEDUCTIVE_CONSTRAINT`;
- `ARC-V01-DT01 / ABDUCTIVE_DIAGNOSTIC`;
- `ARC-V01-DT01 / CAUSAL_EXPERIMENTAL`;
- `ARC-V01-DT01 / SEARCH_PLANNING`;
- `ARC-V01-DT01 / DECISION_THEORETIC`;
- `ARC-V01-DT01 / SYSTEMS_FEEDBACK`;
- `ARC-V01-SF01 / CONTROL`;
- `ARC-V01-SF01 / FULL`;
- `ARC-V01-SF01 / DEDUCTIVE_CONSTRAINT`;
- `ARC-V01-SF01 / SEARCH_PLANNING`.

These ten calls use the same target model, endpoint, temperature, case text, and condition prompts. Only the completion-token ceiling is increased from 16384 to `32768`.

If any Recovery-2 target output is empty, reaches 32768 completion tokens, or returns `finish_reason = length`, stop before judging and preserve the partial artifact. Do not regenerate any already valid target output.

## Judge rule

No valid or invalid judge vote from Recovery 1 exists because judging had not started.

Recovery 2 uses the unchanged behavior and quality judge prompts, schemas, blinded presentation, vote counts, and pathology gates. The judge completion-token ceiling is increased to `16384` before the first Recovery-2 judge call.

For each required vote, retain the existing recovery rule:

- JSON mode;
- up to three formatting/schema attempts;
- failed formatting attempts are logged but do not count as votes;
- only the first valid schema-conforming response counts;
- after three failed attempts, stop and preserve all completed target outputs and valid votes.

## Scientific boundary

Recovery 2 does not change any case, reasoning policy, rubric, Stage-1 eligibility threshold, pathology rule, or program decision rule. It changes only the maximum completion budget needed to obtain visible complete responses and parseable judgments.

If Recovery 2 completes, its 48-output combined set plus the complete 96 behavior votes and 12 quality sanity votes form the Stage-0 result. The final report must disclose both recovery events.
