# Measurement v0.3

Measurement v0.3 is a response to the empirical limitations exposed by Pilot 001. It changes the evaluator before scaling the benchmark.

## Primary changes

### 1. Pairwise judgment becomes primary

Pilot 001 scalar scores were almost saturated at 4/4. v0.3 therefore treats blinded pairwise preference against BASELINE as the primary outcome:

- challenger win = 1.0
- tie = 0.5
- challenger loss = 0.0

Scalar scores are retained only as secondary diagnostics.

### 2. Stricter anchored scalar rubric

The scalar judges now use explicit anchors:

- 0: absent/wrong/serious failure
- 1: major errors or omissions
- 2: partial with material gaps
- 3: strong with at most a minor issue
- 4: exceptional and materially complete

Judges are explicitly instructed to use 4 sparingly and to cap incomplete dimensions below 4.

### 3. Deterministic adaptive-routing score

`mode_fit` is no longer delegated to an LLM judge. For ADAPTIVE runs:

`route_correct = selected_mode in expected_modes`

The report includes routing accuracy and every routing error.

### 4. Harder stress suite

Six new cases target benchmark weaknesses not strongly separated by Pilot 001:

- RF-S01: aggregate/subgroup causal reversal and revision
- RF-S02: measurement-generation process / metric suppression
- RF-S03: material reducible uncertainty under a hard legal constraint
- RF-S04: irrelevant uncertainty and rational stopping under strict dominance
- RF-S05: adversarial user framing demanding an unsupported causal conclusion
- RF-S06: reversible intervention as a discriminating experiment

The v0.3 workflow can run `stress`, `pilot`, or `combined` suites.

### 5. Replicate-aware statistics

The runner accepts multiple stochastic replicates. Replicates are **not** treated as independent benchmark cases.

For each condition:

1. pairwise scores are averaged within each case across replicates;
2. confidence intervals bootstrap cases as clusters;
3. the reported primary score is the mean case-level challenger score against BASELINE.

This prevents pseudo-replication from artificially narrowing uncertainty.

### 6. Separate target and judge configuration

The workflow supports:

- `ZAI_API_KEY` for target calls;
- optional `ZAI_JUDGE_API_KEY` for evaluator calls;
- separate target/judge model IDs;
- separate target/judge base URLs.

If no judge key is configured, the evaluator falls back to the target key. The report flags when target and judge use the same model and endpoint.

### 7. Checkpointing

`v03_runs.jsonl` is rewritten after every completed target+evaluation run and `v03_pairwise.jsonl` after every completed pairwise judgment. Because GitHub uploads `results_v03/` even on failure, a long experiment can preserve partial evidence rather than losing the entire run.

## Recommended sequence

1. Run `stress`, 1 replicate, to validate v0.3 plumbing and discrimination.
2. Inspect scalar spread, pairwise margins, route accuracy, and failure patterns.
3. If measurement quality is acceptable, run `combined`, 1 replicate.
4. Only then run the chosen held-out/full suite with 3+ stochastic replicates and an independent judge when available.

## Decision rule

Do not promote a controller because it has the highest protocol-compliance score. Promotion should depend primarily on improved blinded decision quality relative to BASELINE, with reasoning/token cost, routing accuracy, and failure severity as constraints.
