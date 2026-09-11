# Reproducibility Appendix v1

Status: manuscript-support appendix. Experiment-specific repository documents remain authoritative if any discrepancy is discovered.

## A. Frozen reasoning prompts

### FULL

```text
You are a reasoning agent operating under: Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer. For trivial tasks answer directly; for moderate established tasks compress to Problem → First Principle → Mechanism → Evidence → Solution. Separate observations from interpretations. Generate multiple plausible explanations under material ambiguity. Distinguish symptoms, proximate causes, and root causes. Derive first principles as necessities/invariants, not conventions, precedent, analogies, or current implementations. Express important explanations as falsifiable mechanisms; derive observable predictions and prefer discriminating/falsifying tests. Contradictions require model revision. Preserve uncertainty; confidence tracks evidence. Expose critical assumptions. Engineer only after sufficient understanding; compare effectiveness, robustness, cost, risk, reversibility, feasibility, constraints, feedback loops, side effects, and second-order effects. Continue when uncertainty is material and reducible; stop when further information has insufficient decision value. After intervention, predict and observe outcomes. Do not mechanically expose the entire internal state.
```

### COMPACT

```text
You are a reasoning agent. For non-trivial tasks, use internally: Problem → First Principle → Mechanism → Evidence → Solution. Define the actual problem before solving it. Distinguish observation, inference, assumption, hypothesis, prediction, evidence, conclusion, and recommendation. First principles are necessities/invariants, not conventions or existing implementations. A plausible explanation is not an established cause; correlation is not mechanism. Expose decision-critical assumptions and uncertainty. Seek evidence capable of weakening the favored mechanism. Revise when evidence contradicts the model. Engineer from the best-supported mechanism under constraints, including risk, reversibility, side effects, and second-order effects. Stop when more information is unlikely to change the action. For trivial or established tasks, answer directly. Do not mechanically emit protocol headings.
```

The exact prompt strings are frozen in the project benchmark lineage. The manuscript should cite the historical experiment commits/run metadata rather than assume that unrelated runtime defaults in the current repository define the validated model/provider configuration.

## B. Primary held-out framework validation

Authoritative result document:

`docs/HELDOUT_FRAMEWORK_VALIDATION_V1_GLM53FLASH_RESULTS.md`

### Suite provenance

- suite: `benchmark/heldout_cases_v1.json`;
- suite freeze commit: `2975376ade5df0863340ce10aa867f3b3e0e1404`;
- suite Git blob SHA: `5fa2ab6f678728124b93ea9dd6c9158e5d6e9698`;
- cases: 36.

### Runtime

- target: `glm-5.1`;
- judge: `glm-5.3-flash`;
- provider: Z.AI;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- evidence tier: cross-model, same-family/provider.

### Replication structure

- conditions: CONTROL, COMPACT, FULL;
- target generations: 3 per case/condition;
- target runs: `324/324`;
- pairwise judge votes: 3 per generated comparison;
- final judge votes: `972/972`;
- cases are the independent inferential units;
- uncertainty: case-clustered bootstrap.

### Source and recovery

- source execution encountered judge-format failure after all target outputs existed;
- final recovery run: `34270142523`;
- final artifact: `framework-v1-glm53flash-recovered-report-34270142523`;
- artifact ID: `10082933251`;
- artifact SHA-256: `b28ca6a5f7d222f54b1ba6dd44fbd5f2b32b332947031a352c497c03ce431c12`;
- retained target outputs: `324/324`;
- regenerated target outputs: `0`;
- retained valid votes: `369`;
- newly completed missing votes: `603`;
- formatting retries during recovery: `6`.

### Primary result

- FULL vs CONTROL: `0.6898`;
- 95% CI: `0.6096–0.7685`;
- case direction: `26 W / 2 T / 8 L`;
- primary preregistered endpoint: PASS.

Secondary:

- COMPACT vs CONTROL: `0.5864`, CI `0.5077–0.6667`, secondary point-estimate threshold failed;
- FULL vs COMPACT: `0.5957`, CI `0.5417–0.6543`, preregistered directional rule favored FULL.

## C. Fresh routing-suite framework replications

### Routing v1

Authoritative result:

`docs/SELECTIVE_ROUTING_V1_RESULTS.md`

- run: `34308303072`;
- final artifact: `selective-routing-v1-report-34308303072`;
- artifact ID: `10113776537`;
- artifact SHA-256: `306a5ae4a9dacb30cd4f36215f3d23606845d5cfa91d43a121f75aa41847a715`;
- fresh cases: 48 across 12 domains;
- conditions: CONTROL, FULL;
- generations: 3 per case/condition;
- votes: 3 per case/generation pair;
- FULL vs CONTROL: `0.6771`, CI `0.6250–0.7292`;
- framework replication: positive;
- routing validation: FAIL under frozen preservation rule.

Execution note: shard 2 failed during a redundant benchmark-free connectivity probe before any scientific data were generated; only that shard was rerun after the matrix resolved. Successful shards were not regenerated.

### Routing v2

Authoritative result:

`docs/SELECTIVE_ROUTING_V2_RESULTS.md`

- run: `34432326377`;
- source commit: `ca20c4a9452a389057eb1d27b38ba781747c1102`;
- final artifact: `selective-routing-v2-report-34432326377`;
- artifact SHA-256: `4380f339422c2b71377e763ec6936e936c2b09aabd7c0343b97a03f025ed2054`;
- suite SHA-256: `0fc2c5e011e8731ca4435104b36fc66f327b7254b84b9c3a57a15f298c031682`;
- fresh cases: 48;
- FULL vs CONTROL: `0.6875`, CI `0.6273–0.7477`;
- ROUTED vs CONTROL: `0.6840`, CI `0.6262–0.7408`;
- paired routed-minus-FULL decrement: `-0.00347`, CI `-0.02546–0.01273`;
- FULL invocation: `34/48 = 0.7083`;
- routing validation: FAIL because selectivity cap `<= 0.65` was not met.

### Routing v3

Authoritative result:

`docs/SELECTIVE_ROUTING_V3_RESULTS.md`

- run: `34560083954`;
- launch commit: `6e557fb76f48562087816aa17dc64c40dcfdc322`;
- final artifact: `selective-routing-v3-report-34560083954`;
- artifact SHA-256: `b998501e2e3889e972002eeb6416460f5b31f68838d6306b08d0ccede76d264e`;
- router implementation Git blob: `6ebb72e443c846aee35281c20e64f3b5d173a7a0`;
- fresh cases: 48;
- routes: 48;
- target generations: 288;
- judge votes: 432;
- FULL vs CONTROL: `0.65394`, CI `0.58912–0.71991`;
- ROUTED vs CONTROL: `0.49884`, CI `0.46759–0.53009`;
- paired decrement: `-0.15509`, CI `-0.21296 to -0.09954`;
- FULL invocation: `5/48 = 0.10417`;
- routing validation: FAIL.

Diagnostic causal-trap stratum:

- routed FULL: `0/12`;
- FULL vs CONTROL: `0.81019`, CI `0.72222–0.88426`.

## D. Routing v4 exposed-data development

Authoritative result:

`docs/SELECTIVE_ROUTING_V4_DEVELOPMENT_RESULTS.md`

- development run: `34635603882`;
- artifact: `selective-routing-v4-development-34635603882`;
- artifact SHA-256: `c578ccae20c00204868546921a9d6f738a8b876d3b6dbdf27969cc7568ec48be`;
- development corpus: 144 exposed cases from routing v1-v3;
- evidence status: development only, not fresh validation;
- mean observed FULL vs CONTROL across corpus: `0.67284`;
- qualifying candidates: none;
- selected candidate: none;
- stop rule: triggered.

Strongest candidate (`NB_DIRECT`):

- LOSO score: `0.63927`;
- LOSO paired decrement: `-0.03356`;
- LOSO FULL rate: `0.5625`;
- LODO score: `0.64931`;
- LODO paired decrement: `-0.02353`;
- LODO FULL rate: `0.5833`.

No fresh v4 validation suite was authored.

## E. Development/component studies

The manuscript should cite these for component-identification history rather than treating them as confirmatory framework replications:

- `docs/QUALITY_V0_5_RESULTS.md`;
- `docs/ABLATION_V0_6_1_REPLICATION_RESULTS.md`;
- `docs/CAPABILITY_IDENTIFICATION_V0_7.md`;
- `docs/CAPABILITY_IDENTIFICATION_V0_8.md`;
- `docs/SELECTIVE_CONTROL_V0_9_RESULTS.md`;
- `docs/ABSOLUTE_BEHAVIOR_IDENTIFICATION_V0_10.md`;
- `docs/ABSOLUTE_BEHAVIOR_V0_10_RESULTS.md`;
- `docs/BEHAVIORAL_FIDELITY_V0_11.md`.

Interpretive boundary:

> removing an instruction is not equivalent to removing a capability; the framework-level result does not establish that every named stage is individually necessary.

## F. Judge and bias controls

Quality evaluation uses model-based pairwise judgments. Relevant safeguards include:

- judge does not receive experimental condition labels;
- A/B orientation is randomized deterministically;
- repeated votes are collected;
- agreement and unanimity diagnostics are reported;
- generation/vote replicates are aggregated within case rather than counted as independent benchmark cases;
- case-level bootstrap intervals are used;
- malformed judge outputs are retried under frozen parsing rules rather than repaired semantically;
- recovery does not regenerate existing target outputs.

Remaining limitation:

- target and judge share model family and provider;
- no blinded human preference layer has yet been added.

## G. Current evidence boundary

Supported:

- FULL improves GLM-5.1 judged quality over CONTROL on the preregistered 36-case suite;
- the direction repeats on three additional fresh 48-case suites;
- benefit is heterogeneous;
- component causality remains unresolved;
- no selective router is validated.

Not supported:

- independent-family/provider validation;
- generalization to other target families;
- universal benefit on every task;
- necessity of all eight stages;
- human-equivalent judging;
- a validated 65%-cap router;
- cost optimality;
- inferential meta-analysis across the 180 fresh cases.

## H. Recommended replication additions

For a stronger venue submission, add prospectively:

1. independent-family/provider rejudging of frozen target outputs, preferably without target regeneration;
2. blinded human judgments on a stratified subset;
3. a second target-model family under the same frozen FULL/CONTROL policy;
4. external benchmark transfer.
