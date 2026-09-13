# Operator Fidelity v0.2 — Audited Results

Status: **completed development result; Stage 1 is not authorized**.

Authorized workflow run: `34753139241`

Target artifact:
- artifact id: `10318846716`
- artifact name: `operator-fidelity-v02-targets`
- artifact ZIP digest: `sha256:3c74f653f4b54faa789b5c5508b37e08ec52fd706d922b5dbb10bd159ccfdee4`
- `runs.jsonl`: `sha256:0c267496079adc0902633dc18df6e06f769c9504de85847f041c08efb81b3b10`
- `target_meta.json`: `sha256:6308f74bf0f10d3e91cf0af0bc46e91c6864723c4f5e9b8fb24313366421d7c1`

Results artifact:
- artifact id: `10321239464`
- artifact name: `operator-fidelity-v02-results`
- artifact ZIP digest: `sha256:e83f81cf75e2ba63612625167c46199a1ce8f03e085c5c65172ca694840cfb0b`
- `runs.jsonl`: `sha256:0c267496079adc0902633dc18df6e06f769c9504de85847f041c08efb81b3b10`
- `fidelity_votes.jsonl`: `sha256:a270e324d8dce6cbb90ce4d25490ad12d39788da988038ad2a82dab541b6ecf8`
- `quality_sanity.jsonl`: `sha256:615d12c9486bc4666863a3aa720cf7fa9b1fc158e0f1031f5ef541b28b099dd9`
- `judge_format_failures.jsonl`: empty file, `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `summary.json`: `sha256:9f550317049b8790157b734075bb94030dcbfdc3d10bc787d842b9bed1a5856a`

## 1. Frozen target-artifact audit

The frozen handoff passed independently of `summary.json`:

- 96 target records exactly;
- 96 unique `(case_id, condition)` keys;
- 12 cases × 8 conditions, with exactly eight conditions on every case;
- zero empty target responses;
- all 96 final `finish_reason` values are `stop`;
- zero `finish_reason = length` responses;
- maximum target output was 18,296 completion tokens, below the frozen 32,768 cap;
- `measurement_version = operator-fidelity-v0.2`;
- target model = `glm-5.1`;
- case blob = `de1becf88db15f68acd151e642e51ac39129171c`;
- policy blob = `504ca9ac63ba10fc7833c36230787aafdf02920e`;
- `target_meta.json` records `runs_sha256 = 0c267496079adc0902633dc18df6e06f769c9504de85847f041c08efb81b3b10`, which exactly matches the downloaded target `runs.jsonl`;
- the results artifact contains byte-identical copies of the frozen target `runs.jsonl` and `target_meta.json`.

The judging phase therefore consumed the frozen target artifact as designed; no target regeneration occurred between target generation and judging.

## 2. Judge-record integrity

The results artifact contains:

- 192 fidelity votes = exactly two votes for each of 96 target responses;
- 192 unique `(case_id, condition, vote_index)` keys;
- 24 quality-sanity votes = exactly two comparisons on each of 12 cases;
- 24 unique `(case_id, pair_id)` keys;
- zero judge-format failures;
- one fidelity accuracy-pathology flag, on nonmatching condition `CAUSAL_EXPERIMENTAL` for `ARC-V02-DT02`;
- zero pairwise material-quality pathology flags.

The single fidelity pathology does not block any matching specialist under the frozen rule.

## 3. Independent recomputation of the frozen gate

The six operator rows below were recomputed from raw fidelity votes and quality records rather than trusting `summary.json`.

| Operator | Specialist fidelity | CONTROL | FULL | Median nonmatching | Lift vs CONTROL | Separation | Minimum case lift | Eligible |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| DEDUCTIVE_CONSTRAINT | 1.000 | 0.975 | 1.000 | 1.000 | +0.025 | 0.000 | 0.000 | no |
| ABDUCTIVE_DIAGNOSTIC | 1.000 | 0.925 | 1.000 | 1.000 | +0.075 | 0.000 | +0.050 | no |
| CAUSAL_EXPERIMENTAL | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | no |
| SEARCH_PLANNING | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | no |
| DECISION_THEORETIC | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | no |
| SYSTEMS_FEEDBACK | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | no |

Frozen eligibility required all of:

- `lift_control >= 0.15`;
- `separation >= 0.10`;
- nonnegative specialist-minus-CONTROL fidelity on both cases;
- no matching-specialist fidelity pathology;
- no matching-specialist quality pathology.

No operator passes the lift or separation requirements.

Independent program decision:

`STOP_REDESIGN_OPERATORS`

Eligible operators: none.

This exactly matches the generated `summary.json` decision, but the conclusion above is independently derived from raw records.

## 4. Saturation finding

The v0.2 manipulation measure saturated more strongly than v0.1:

- 89/96 response composites are exactly `1.0`;
- 96/96 are at least `0.9`;
- all six matching specialists average `1.0` fidelity;
- for all six operator families, the median nonmatching specialist also averages `1.0`.

Therefore the frozen separation gate is again mathematically unattainable on these probes once both matching and nonmatching policies reach the scale ceiling.

This is not evidence that the six reasoning concepts are meaningless. It is evidence that, on this target and these development probes, prompt-only causal identification by independently scored observable behavior cannot distinguish these operators from the already-capable general response behavior.

## 5. Program consequence

The v0.2 design explicitly stated that renewed fidelity saturation should stop further attempts to establish operator identity through prompt-only behavioral manipulation on this target.

Accordingly:

1. **Do not proceed to Stage 1.**
2. **Do not redesign another prompt-only Stage-0 fidelity experiment for these same six families on `glm-5.1`.**
3. Treat the six families as useful descriptive/analytic reasoning labels, not as empirically identified, causally distinct promptable modules.
4. The supported deployment architecture remains unchanged: DIRECT for genuinely trivial/deterministic tasks and frozen FULL for non-trivial reasoning tasks.
5. Any future adaptive-controller research should require a materially different identification strategy, such as internal mechanism/intervention access, constrained process environments, tool/action traces with discriminating state transitions, or a different target whose behaviors do not saturate the present rubric.

No further paid experiment is authorized by this result.