# Publication Readiness v1

Status: **paper-ready as a technical report / preprint with explicit evidentiary limits; stronger venue claims would benefit materially from independent evaluation and cross-target replication.**

## Recommended paper thesis

The strongest manuscript should be framed around **structured reasoning control and its empirical limits**, not around a successful routing system.

Suggested central thesis:

> A frozen structured-reasoning protocol improves GLM-5.1 reasoning quality over an uncontrolled baseline across multiple fresh benchmark suites under blinded cross-model same-family evaluation, while component-level causal attribution and input-only selective routing remain substantially harder.

This framing makes the negative results part of the contribution rather than treating them as failed side projects.

## Why the work is publishable now

The project has several characteristics expected of a credible empirical research report:

- explicit protocol and frozen prompt definitions;
- development/held-out separation;
- preregistered success criteria for the primary held-out validation;
- multiple stochastic target generations;
- repeated blinded randomized pairwise judgments;
- case-level aggregation rather than treating generations/votes as independent samples;
- case-clustered bootstrap intervals;
- preserved provenance and fail-closed recovery after execution-format failures;
- prospectively frozen routing gates across multiple fresh suites;
- documented negative and null results;
- a formal stop rule that was actually obeyed.

The strongest primary result is the 36-case Tier-1B held-out FULL-vs-CONTROL score of **0.6898** with 95% CI **0.6096–0.7685**.

Three later fresh 48-case suites again favored FULL over CONTROL: **0.6771**, **0.6875**, and **0.6539**. Their role should be described as sequential fresh-suite replications inside the same research program, not as independent studies.

## Main scientific contributions

A paper can reasonably present four contributions.

### 1. A structured reasoning protocol with held-out quality evidence

The FULL protocol operationalizes a causal/scientific/engineering reasoning loop:

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`.

The main held-out experiment supports an average quality benefit relative to no reasoning-specific system prompt.

### 2. Evidence of heterogeneous value

The protocol is not uniformly helpful. The largest held-out effects occur on testing-, engineering-, and action-oriented tasks, while no-action / NONE strata are near neutral.

This is scientifically useful because it rejects the simple claim that “more explicit reasoning is always better.”

### 3. Identification limits for reasoning components

Ablation and capability-identification experiments demonstrate that prompt-stage manipulation is not equivalent to capability manipulation. Diagnose and Revise often appear endogenously even when their explicit instructions are absent.

This motivates the distinction:

`reasoning capability ≠ reasoning instruction`.

### 4. Negative evidence on selective routing

Routing v1–v3 failed different frozen criteria, and v4 empirical development triggered a stop rule. The program therefore provides evidence that **predicting the marginal value of deep reasoning from turn-1 text is harder than measuring the average benefit of the reasoning policy itself**.

That negative result is methodologically valuable and prevents an unsupported efficiency claim.

## Major limitations reviewers are likely to raise

These should be presented proactively.

### Same-family/provider evaluator

The target is GLM-5.1 and the judge is GLM-5.3-Flash, both on Z.AI and from the GLM family. This is cross-model evaluation, but not independent-provider or independent-family evaluation.

This is the single most important evidentiary limitation.

### Single target model

The validated target is GLM-5.1. The work does not establish transfer to other model families or capability levels.

### Program-authored benchmark cases

The benchmark suites were created within the same research program. Even when suites were frozen before their corresponding outcomes, external benchmark transfer remains untested.

### Model-based judging

The primary quality outcomes use a model judge. Repeated votes and blinding reduce variance and positional bias, but they do not replace human evaluation.

### Sequential research adaptation

Later experiments were designed after earlier findings. This is appropriate for an iterative research program, but only each prospectively frozen fresh-suite test should be treated as confirmatory for its own preregistered question.

### Component causality remains unresolved

The framework-level effect should not be decomposed into claims that each stage is necessary or independently causal.

### Routing is not validated

No autonomous selective-routing system survived the complete program. Cost savings must not be a headline claim.

## Recommended manuscript structure

1. **Introduction** — problem: models often produce answers without explicit causal discrimination, falsification, revision, or engineering analysis; question: can a structured reasoning control improve output quality?
2. **Reasoning protocol** — FULL and COMPACT definitions; distinction between instruction and latent capability.
3. **Evaluation methodology** — benchmark construction, blinded pairwise judging, aggregation, bootstrap, evidence tiers.
4. **Development studies** — v0.5 through v0.11 as iterative identification work; emphasize lessons rather than every implementation detail.
5. **Held-out framework validation** — make the 36-case Tier-1B result the primary confirmatory section.
6. **Fresh-suite replications during routing research** — show repeated FULL-vs-CONTROL results across v1–v3 routing suites.
7. **Selective routing experiments** — report v1–v4 failures and stop rule as negative results.
8. **Discussion** — structured reasoning helps on average, especially action/testing/engineering; stage necessity and routing remain unresolved.
9. **Limitations** — evaluator independence, single target model, authored benchmarks, no human validation.
10. **Conclusion** — correct models before confident solutions; quality first, routing/cost only after validated prediction.

## Tables and figures worth including

### Table 1 — Experiment chronology

Columns: version, research question, cases, conditions, principal result, evidence status.

### Table 2 — Fresh-suite FULL vs CONTROL

Include the 36/48/48/48 case results and confidence intervals, with a note that the 180-case weighted average is descriptive only.

### Figure 1 — Research architecture

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`

and below it the empirical architecture decision:

`trivial/deterministic → direct`

`non-trivial → FULL`.

### Figure 2 — Heterogeneous held-out effect

Plot FULL-vs-CONTROL by ENGINEER, TEST, BOTH, NONE, and action requirement.

### Figure 3 — Routing quality/selectivity frontier

Show ALWAYS-FULL, DIRECT_BYPASS, v2 routed policy, v3 routed policy, and the best v4 development candidate. Mark which are validated, failed, or development-only.

## Suitable publication levels

### Ready now

- technical report;
- arXiv / preprint;
- workshop paper;
- empirical methods / reasoning-control position paper with substantial experiments.

### Stronger with one additional validation layer

A full conference or journal submission would become materially stronger with at least one of:

- genuinely independent-family/provider rejudging;
- blinded human evaluation on a representative subset;
- replication on a second target-model family;
- transfer to an external benchmark not authored by this project.

Two of these would substantially strengthen the case.

## Minimum additional work before submission

If submission is the immediate goal, the most efficient sequence is:

1. freeze the present synthesis and claim boundary;
2. create a manuscript draft from repository evidence only;
3. prepare reproducibility appendix with exact prompts, suite hashes, runs, and artifact digests;
4. add one independent validation layer if resources become available;
5. submit without reopening routing unless genuinely new information appears.

## Publication claim boundary

A defensible abstract-level statement is:

> We evaluate a structured reasoning protocol that requires explicit diagnosis, first-principles derivation, falsifiable hypotheses, prediction, testing, revision, and engineering analysis. On a preregistered 36-case held-out suite, GLM-5.1 responses generated with the frozen full protocol were preferred to uncontrolled responses with a score of 0.690 (95% case-clustered CI 0.610–0.769) by a blinded GLM-5.3-Flash evaluator. Three subsequent fresh 48-case suites again favored the full protocol. Benefits were heterogeneous and strongest on testing, engineering, and action-oriented tasks. Component ablations did not cleanly identify individual-stage causality, and multiple selective-routing strategies failed frozen quality/selectivity criteria, indicating that predicting when deep reasoning can safely be skipped remains unresolved. Because target and evaluator share a model family and provider, the evidence is cross-model same-family rather than fully independent validation.

This is the strongest current paper claim without overstating the evidence.
