# Reasoning Engine — Research Synthesis v2

Status: **current whole-program evidence synthesis after completion of Process-Constrained Phase B v0.2.**

This document supersedes `RESEARCH_SYNTHESIS_V1.md` as the current cross-program claim boundary. Experiment-specific preregistrations, recovery freezes, and post-run audits remain authoritative for their exact decisions.

## 1. Current evidence hierarchy

The program now contains three distinct empirical layers that should not be conflated:

1. **Framework-level quality evidence** — the frozen FULL structured-reasoning prompt repeatedly improves blinded pairwise reasoning quality over CONTROL on GLM-5.1 under same-provider GLM-family evaluation.
2. **Decomposition and routing evidence** — explicit stage/component attribution remains unresolved, and several selective-routing strategies failed frozen preservation/selectivity/generalization criteria.
3. **Adaptive operator-control evidence** — neither prompt-defined specialist operators nor the tested externally process-constrained specialist protocols produced evidence sufficient to authorize an autonomous selector.

The strongest positive result remains layer 1. The strongest adaptive-control conclusion is a stop result under the tested designs, not evidence that all forms of adaptive reasoning control are impossible.

## 2. Framework-level result remains the primary established finding

The frozen FULL protocol is:

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`

with direct answering still allowed for genuinely trivial or established tasks.

FULL vs CONTROL was measured on four fresh suites after prompt freeze:

| Suite | Cases | FULL vs CONTROL | 95% case-clustered CI | Status |
|---|---:|---:|---:|---|
| Held-Out Framework Validation v1 | 36 | 0.6898 | 0.6096–0.7685 | preregistered primary endpoint passed |
| Selective Routing v1 suite | 48 | 0.6771 | 0.6250–0.7292 | prospective replication |
| Selective Routing v2 suite | 48 | 0.6875 | 0.6273–0.7477 | prospective replication |
| Selective Routing v3 suite | 48 | 0.6539 | 0.5891–0.7199 | prospective replication |

Across the 180 fresh cases, the case-count-weighted descriptive score is approximately 0.6762. This pooled number is descriptive only and is not an independent-study meta-analysis.

The held-out architecture study also found:

- COMPACT vs CONTROL = 0.5864, CI 0.5077–0.6667; the frozen secondary success rule failed because the point estimate was below 0.60;
- FULL vs COMPACT = 0.5957, CI 0.5417–0.6543; the frozen directional comparison favored FULL.

The evidence therefore supports the frozen FULL framework relative to an uncontrolled baseline more strongly than it supports a compact replacement.

## 3. Heterogeneity is real, but deployable routing remains unresolved

The held-out framework effect was heterogeneous. In the original 36-case suite, FULL was strongest on:

- ENGINEER: 0.9012;
- TEST: 0.7901;
- BOTH: 0.6296;
- action-required cases: 0.7375.

Near-neutral groups included:

- NONE: 0.4861;
- no-action cases: 0.4921.

This heterogeneity motivated routing research. It does not establish that deployment-time text or semantic labels can reliably identify low-value-FULL cases.

Selective Routing v1–v4 did not produce a validated router:

- v1 formally failed its frozen preservation endpoint;
- v2 preserved 98.15% of FULL gain with only a -0.0035 paired decrement, but invoked FULL on 70.83% of cases and failed the frozen 65% selectivity cap;
- v3 reduced FULL use to 10.42% but suffered a -0.1551 paired decrement; its core `CAUSAL_TRAP` hypothesis was falsified because FULL scored 0.8102 on that stratum;
- v4 empirical text-only development found no candidate satisfying all frozen leave-one-suite-out and leave-one-domain-out gates, triggering the routing stop rule.

The current deployment decision therefore remains conservative rather than selectively optimized:

`DIRECT for genuinely trivial/deterministic tasks; otherwise frozen FULL`.

## 4. Component and prompt-defined operator attribution did not resolve cleanly

The component-identification program established a methodological distinction:

`reasoning capability ≠ reasoning instruction`.

Removing or isolating an instruction did not reliably remove or isolate the corresponding capability. Behavioral measurements often saturated, especially for behaviors already latent in a capable target model.

The later prompt-defined Operator Fidelity program made this problem explicit. Its v0.2 study produced:

- 0/6 specialists passing the frozen eligibility gate;
- 89/96 response composites exactly 1.0;
- all 96 composites at least 0.9;
- matching-specialist fidelity at ceiling while nonmatching specialists also largely exhibited the same requested behaviors.

The frozen stop rule therefore closed the prompt-only causal-identification strategy. The candidate reasoning families remain useful descriptive/engineering labels, but the program has not established them as causally separable prompt modules on GLM-5.1.

## 5. Process-constrained redesign changed the intervention, not the conclusion standard

After prompt-only saturation, the program changed the operational definition of an operator from a system-prompt suggestion to an externally enforced process:

`Task → enforced protocol state machine → validated transitions → environment actions → objective outcome`.

The model proposes transition content; an external runtime controls legal transitions, action timing, state, and termination. A generic `MATCHED_SCAFFOLD` control was introduced to distinguish benefits of specialist process structure from benefits of extra deliberation, state storage, or repeated environment interaction.

The first paid Process-Constrained Phase B v0.1 study produced a reproducible frozen numerical stop result, but its mandatory audit found two upstream validity defects:

- state-specific no-action restrictions were not fully exposed in the model-visible operational contract;
- the deductive terminal endpoint ambiguously mixed restart-start and service-restoration time.

Those defects prevented promotion of the v0.1 stop result into a clean conclusion about specialist-process value. Phase B v0.2 prospectively corrected both defects on 24 fresh development cases.

## 6. Process-Constrained Phase B v0.2: complete audited result

Phase B v0.2 tested four process families:

- `DEDUCTIVE_CONSTRAINT`;
- `ABDUCTIVE_DIAGNOSTIC`;
- `SEARCH_PLANNING`;
- `DECISION_THEORETIC`.

Each of 24 fresh cases was crossed with:

- `SPECIALIST`;
- `MATCHED_SCAFFOLD`;
- frozen `FULL`;
- `CONTROL`.

The primary causal development contrast was `SPECIALIST - MATCHED_SCAFFOLD`, scored objectively by the environment.

The original paid execution stopped after five cells because the protocol runner failed to catch an observed `BudgetExceeded` condition that the generic path already classified as a scientific execution failure. Recovery 1 froze the repair before further calls, preserved the completed source cells, mechanically reclassified only the observed interrupted source cell, and executed only the remaining 91 cells. The completed recovered dataset contains exactly 96 unique case-condition records and independently reproduces the original frozen aggregation.

Frozen family results:

| Family | Specialist | Matched scaffold | Mean process effect | Strict wins | Valid specialist | Eligible |
|---|---:|---:|---:|---:|---:|---|
| DEDUCTIVE_CONSTRAINT | 1.0000 | 1.0000 | 0.0000 | 0/6 | 6/6 | No |
| ABDUCTIVE_DIAGNOSTIC | 0.3333 | 0.1667 | +0.1667 | 1/6 | 6/6 | No |
| SEARCH_PLANNING | 1.0000 | 0.8333 | +0.1667 | 1/6 | 6/6 | No |
| DECISION_THEORETIC | 1.0000 | 1.0000 | 0.0000 | 0/6 | 6/6 | No |

Eligible families: none.

Frozen program decision:

`STOP_PROCESS_CONSTRAINED_SELECTOR_PATH`.

Phase C is therefore not authorized.

## 7. What the process-constrained result actually shows

The corrected v0.2 result differs importantly from the invalidated interpretation risk in v0.1:

- all 24 specialist executions reached valid terminal states;
- specialist catastrophic failures were zero;
- the corrected operational contracts were executable;
- exactly two of 24 specialist-vs-matched case comparisons were strict specialist wins, with zero matched-scaffold wins;
- on both strict-win cases, the specialist completed successfully where the matched scaffold failed;
- whenever both specialist and matched scaffold completed successfully, their objective normalized scores were equal.

Thus externally enforced specialist process structure showed isolated process-discipline benefits, but not the repeated within-family objective advantage required for selector development.

The development environments also had substantial ceiling limitations:

- DEDUCTIVE_CONSTRAINT: 24/24 condition records scored 1.0;
- SEARCH_PLANNING: 23/24 scored 1.0;
- DECISION_THEORETIC: 24/24 scored 1.0;
- ABDUCTIVE_DIAGNOSTIC: 7/24 scored 1.0 and therefore retained headroom, but the specialist beat the matched scaffold on only one of six cases.

The result therefore supports the frozen stop decision while also limiting its broader interpretation. Three families offered little objective headroom for process differentiation; the fourth did not show persistent specialist advantage.

## 8. Relationship between the positive FULL result and the negative selector programs

There is no contradiction between:

- FULL improving blinded natural-language reasoning quality over CONTROL on difficult fresh tasks; and
- prompt-defined/process-constrained specialist programs failing to produce a validated adaptive selector.

They test different causal objects and endpoints.

The FULL evidence asks whether one frozen general structured-reasoning policy improves answer quality relative to an uncontrolled baseline.

The later adaptive-control programs ask whether more specialized reasoning policies are separable, task-conditionally superior, and predictable/selectable strongly enough to justify switching among them.

The first question has positive evidence under the program's current target/evaluator setup. The second remains unsupported under the tested designs.

## 9. Current claims supported

The program currently supports the following statements:

1. On GLM-5.1, the frozen FULL structured-reasoning prompt improved blinded pairwise quality over CONTROL on a preregistered 36-case held-out suite under GLM-5.3-Flash evaluation.
2. The FULL-vs-CONTROL advantage replicated prospectively on three additional fresh 48-case suites.
3. FULL's marginal value is heterogeneous, with stronger effects on testing-, engineering-, and action-oriented tasks.
4. Explicit instruction manipulation is not equivalent to capability manipulation; stable component-level causal attribution remains unresolved.
5. Multiple input-only routing strategies failed frozen deployment criteria, so no autonomous DIRECT/FULL router is validated.
6. Prompt-defined specialist operators saturated behavioral-fidelity measurement and failed the frozen causal-identification gate.
7. In the corrected process-constrained Phase B v0.2 development study, none of four specialist families met the preregistered/frozen Phase-C eligibility rule relative to the matched generic scaffold.
8. Under current evidence, the adaptive process-selector path is closed and Phase C is not authorized.

## 10. Claims not supported

Do not claim:

- independent-family/provider validation;
- generalization to target models other than GLM-5.1;
- universal FULL benefit on every task;
- causal necessity of every named FULL stage;
- causal modularity of the candidate reasoning-family labels;
- a validated autonomous router or reasoning selector;
- that process-constrained reasoning is universally ineffective;
- that FULL and CONTROL are generally equivalent because they tied on the synthetic Phase-B environments;
- cost optimality;
- human-equivalent judge validity;
- hidden chain-of-thought or neural-mechanism measurement;
- that the internally authored development environments constitute external-benchmark validation.

## 11. Architecture decision

The supported deployment architecture remains:

`DIRECT for genuinely trivial, deterministic, or fully established tasks; otherwise frozen FULL`.

This is a conservative architecture decision under current evidence. It is not a proof that FULL is optimal for every non-trivial task.

Neither the routing failures nor the process-selector stop rule justify replacing FULL with CONTROL on non-trivial tasks, because the strongest framework-level evidence still favors FULL and the adaptive studies were not designed as external replications of that quality endpoint.

## 12. Research priorities after the selector stop

The highest-value next work is now **generalization and measurement independence**, not another selector variant.

Priority order:

1. **Independent evaluation** — rejudge frozen FULL/CONTROL outputs with a materially different model family/provider when available, or obtain blinded expert/human review on a stratified subset.
2. **Cross-target replication** — repeat the frozen FULL-vs-CONTROL framework test on at least one materially different target model family/capability level.
3. **External benchmark transfer** — test the frozen FULL policy on reasoning tasks not authored inside this program.
4. **Harder external objective environments** — only as a new research generation, test whether process constraints matter when synthetic ceiling effects are materially reduced and task generation is independent of the exposed Phase-B suite.
5. **Reopen adaptive control only after new interaction evidence** — selector work should remain closed unless materially new data establish task-by-policy interaction and meaningful oracle headroom relative to the best fixed policy.

Do not continue the exposed selector path by tuning thresholds, prompt wording, state machines, or case parameters against the failed development suites.

## 13. Governing interpretation

The current program supports a narrow but coherent picture:

> A frozen general structured-reasoning policy can improve model answer quality on difficult reasoning tasks, but the program has not established a reliable decomposition into separable specialist modules or a deployment-ready rule for selecting among reasoning modes. Prompt-only specialists saturated observable behavior, and a later process-constrained development study did not produce sufficiently frequent specialist-over-matched objective gains to justify Phase-C selector development. The next evidence bottleneck is external validity and evaluator/target independence rather than another internally tuned routing mechanism.
