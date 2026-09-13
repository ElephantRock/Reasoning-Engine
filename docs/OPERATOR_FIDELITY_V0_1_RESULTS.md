# Operator Fidelity v0.1 — Audited Results

Status: **completed development result; Stage 1 is not authorized from v0.1**.

Final completed workflow:

- Recovery-2 workflow run: `34721404133`
- Recovery-2 artifact id: `10308693103`
- Artifact name: `operator-fidelity-v01-recovery2-results`
- Artifact ZIP digest: `sha256:2e757b18c824123e01e702cf270edeed65525d2476f2f4b295dfaa24d758d95f`
- `combined_runs.jsonl`: `sha256:46981533c3013b2c790c802387315457855ff4d64df356040853a3a9e3ef56e6`
- `behavior_votes.jsonl`: `sha256:85b35f6e79d88fc9d30bb54b139f9a6b6c0605fff894c06b314e2980e39a1772`
- `quality_sanity.jsonl`: `sha256:177e8bedc27576cae378256478f2d05db9362b89254c4a42ff3d5d4aea54ac24`
- `summary.json`: `sha256:7dd60a15b11c00b73b03b546e5d5ec4e1191814b6545ebc35cad97ba00051474`

The final artifact contains 48 unique target outputs, 96 valid behavior votes, 12 valid pairwise quality-sanity votes, and two logged judge-format failures that were recovered by the pre-frozen formatting retry rule. All 48 final target outputs are non-empty and none ended with `finish_reason = length`.

## 1. Frozen decision

The predeclared Stage-0 result is:

`STOP_REDESIGN_OPERATORS`

No operator passed the v0.1 Stage-1 eligibility gate.

| Operator | Own | CONTROL | Other-specialist median | Lift vs CONTROL | Separation | Eligible |
|---|---:|---:|---:|---:|---:|---|
| DEDUCTIVE_CONSTRAINT | 3.0 | 4.0 | 4.0 | -1.0 | -1.0 | no |
| ABDUCTIVE_DIAGNOSTIC | 3.5 | 3.0 | 4.0 | +0.5 | -0.5 | no |
| CAUSAL_EXPERIMENTAL | 4.0 | 4.0 | 4.0 | 0.0 | 0.0 | no |
| SEARCH_PLANNING | 4.0 | 4.0 | 4.0 | 0.0 | 0.0 | no |
| DECISION_THEORETIC | 3.5 | 4.0 | 4.0 | -0.5 | -0.5 | no |
| SYSTEMS_FEEDBACK | 4.0 | 4.0 | 4.0 | 0.0 | 0.0 | no |

The decision is therefore mechanical under the frozen rule. Stage 1 must not be started using the v0.1 operator set as if Stage 0 had passed.

## 2. Independent integrity review

The completed artifact was independently recomputed from the raw JSONL records rather than trusting `summary.json` alone.

Checks reproduced:

- 48/48 unique `(case, condition)` target outputs;
- 96/96 unique `(case, condition, behavior-vote)` records;
- 12/12 unique pairwise quality records;
- 28 final outputs preserved from the original run;
- 10 final outputs preserved from Recovery 1;
- 10 final outputs generated in Recovery 2;
- zero empty final target responses;
- zero final target responses with `finish_reason = length`;
- two judge-format retries, both resolving on the second attempt;
- zero material quality-pathology votes;
- no matching specialist was blocked by an accuracy/pathology gate;
- independent recomputation reproduced all six operator rows and `STOP_REDESIGN_OPERATORS` exactly.

Four behavior votes flagged an accuracy pathology, but they occurred on nonmatching conditions (`FULL` on the deductive probe and `SYSTEMS_FEEDBACK` on the causal probe), so they do not change specialist eligibility under the frozen rule.

## 3. Quality-sanity result

Against CONTROL on the matching probe, the specialist outcome count was:

- specialist wins: 2 (`ABDUCTIVE_DIAGNOSTIC`, `CAUSAL_EXPERIMENTAL`);
- ties: 2 (`DEDUCTIVE_CONSTRAINT`, `SEARCH_PLANNING`);
- specialist losses: 2 (`DECISION_THEORETIC`, `SYSTEMS_FEEDBACK`).

Against FULL:

- specialist wins: 0;
- ties: 3 (`DEDUCTIVE_CONSTRAINT`, `CAUSAL_EXPERIMENTAL`, `SEARCH_PLANNING`);
- FULL wins: 3 (`ABDUCTIVE_DIAGNOSTIC`, `DECISION_THEORETIC`, `SYSTEMS_FEEDBACK`).

These are one-case-per-operator development diagnostics, not inferential quality estimates. They provide no basis for claiming specialist superiority over FULL.

## 4. Main review finding: the fidelity measure saturated

The formal v0.1 failure is real, but the diagnostic pattern shows that the experiment primarily failed to establish **behavioral separability**, not that the six reasoning concepts are disproven.

On each case, examine the score for that case's intended reasoning dimension across all eight conditions. Across the resulting 48 case-condition values:

- 39/48 were exactly `4.0`;
- 43/48 were at least `3.5`;
- on all six probes, the median nonmatching-specialist score on the intended dimension was `4.0`.

Because the scale maximum was `4.0`, once the nonmatching median reached `4.0`, the frozen separation requirement `specialist - median(nonmatching) >= 0.25` became mathematically unattainable for that probe.

This repeats a failure mode already documented in `ABSOLUTE_BEHAVIOR_V0_10_RESULTS.md`: broad 0–4 behavior categories saturate on an already capable target and measure presence of a capability more readily than execution fidelity.

A second contributor is case cueing. The v0.1 prompts often directly requested the behavior that the intended operator was supposed to induce—for example asking for the "leading explanations and most informative next check," the best test of a "causal effect," a "safe sequence with verification and rollback points," or the "system effects" of an intervention. That makes high CONTROL and nonmatching-policy scores unsurprising.

Therefore the correct interpretation is:

> v0.1 does not establish behaviorally separable specialist operators under its prompts, cases, and coarse fidelity measure. It does not justify Stage 1. The next experiment must redesign operator boundedness and the Stage-0 manipulation measure before any interaction suite is authored.

## 5. Consequence for v0.2

The redesign should retain the six conceptual operator families as hypotheses but change how a specialist is operationalized and measured:

1. specialist prompts should be explicitly bounded primary operators rather than general quality prompts with a topical emphasis;
2. fresh probes should make the target reasoning behavior useful without directly asking for it;
3. broad 0–4 dimensions should be replaced by operator-specific observable sub-behavior criteria, scored independently on a finer 0/0.5/1 scale;
4. fidelity lift must be measured over more than one fresh case per operator;
5. FULL remains the frozen generalist comparator and pairwise quality remains a safety diagnostic, not the manipulation measure;
6. no v0.1 case may be reused to pass v0.2.

Until a redesigned Stage 0 passes, the supported architecture remains DIRECT for genuinely trivial/deterministic tasks and frozen FULL for non-trivial reasoning tasks.