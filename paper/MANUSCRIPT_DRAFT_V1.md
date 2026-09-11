# Structured Reasoning Control Improves LLM Decision Quality but Resists Reliable Selective Routing

**Manuscript draft v1 — not yet submission-ready**

## Abstract

Large language models can often produce plausible answers without explicitly separating observations from causal explanations, hypotheses from evidence, or recommendations from tested mechanisms. We evaluate a frozen structured-reasoning control protocol that organizes non-trivial reasoning as **Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**. On a preregistered 36-case held-out suite, GLM-5.1 responses generated with the full protocol were preferred to uncontrolled responses with a pairwise score of **0.6898** under blinded GLM-5.3-Flash judging, with a 95% case-clustered bootstrap interval of **0.6096–0.7685**. Three subsequent fresh 48-case suites again favored the same frozen FULL protocol over CONTROL, with scores of **0.6771**, **0.6875**, and **0.6539**. Effects were heterogeneous: in the primary held-out suite, gains were strongest on testing-, engineering-, and action-oriented cases, while no-action cases were near neutral. Attempts to causally attribute the framework effect to individual named stages were inconclusive because removing instructions often failed to remove the corresponding latent capability. Four generations of selective-routing work likewise failed prospectively frozen quality/selectivity criteria; a final exposed-data development stage triggered a preregistered stop rule. These results support a narrow conclusion: structured scientific/engineering reasoning control can improve decision-quality outputs on difficult tasks for GLM-5.1, but individual-stage causality and reliable input-only prediction of when deep reasoning can safely be skipped remain unresolved. Because target and evaluator share the GLM family and Z.AI provider, the evidence is cross-model same-family rather than independent-family/provider validation.

## 1. Introduction

Modern large language models are capable of fluent explanation and increasingly strong problem solving, yet response fluency does not guarantee disciplined inference. A model may move from an observed phenomenon directly to a preferred explanation; treat correlation as mechanism; recommend an intervention without identifying discriminating evidence; or fail to revise a causal model when later evidence contradicts it. These failure modes are especially consequential in tasks that require testing, intervention design, operational decisions, reversibility, monitoring, or second-order reasoning.

A large body of prior work shows that inference can be improved by eliciting intermediate reasoning, decomposing problems, sampling multiple reasoning paths, performing explicit search, incorporating reflection, or interleaving reasoning with actions. Chain-of-Thought prompting elicits intermediate rationales; Least-to-Most prompting decomposes hard problems into simpler subproblems; Self-Consistency aggregates multiple reasoning paths; Tree of Thoughts explicitly searches over candidate thought trajectories; ReAct combines reasoning and action; and Self-Refine and Reflexion use iterative feedback and revision. These methods establish that inference-time structure can matter.

The present work asks a different empirical question: **does a fixed scientific/engineering reasoning-control policy improve the quality of model decisions and explanations, and can that benefit be decomposed or selectively invoked without sacrificing quality?**

We study the following protocol:

> **Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**

The stages are intended to impose an epistemic order. The model should first separate observations from interpretation, consider competing explanations, derive relevant first principles and constraints, formulate testable mechanisms, state predictions, seek discriminating evidence, revise when evidence changes, and only then engineer an action with explicit constraints, reversibility, monitoring, and failure modes.

The project was deliberately organized as an iterative research program rather than a single benchmark run. Development studies first tested whether structured prompting produced quality gains. Component studies then asked whether named stage instructions actually induced distinct behavior and whether behavior changes mediated quality. A preregistered held-out experiment tested the frozen FULL protocol as a whole. Later fresh suites were created for selective-routing studies; these also provided prospective replications of the FULL-vs-CONTROL comparison. Finally, routing development was stopped after multiple frozen criteria failed.

The paper makes four contributions:

1. **Framework-level evidence.** A frozen eight-stage structured-reasoning protocol outperformed an uncontrolled baseline on a preregistered held-out suite, and the direction replicated on three later fresh suites.
2. **Heterogeneity evidence.** The benefit was concentrated in testing-, engineering-, and action-oriented tasks rather than being uniformly positive.
3. **Component-identification evidence.** Removing or adding named instructions did not cleanly identify the causal value of individual reasoning capabilities, highlighting the distinction between a prompt instruction and a model's endogenous capability.
4. **Negative routing evidence.** Several semantic and empirical routing strategies failed conservative quality-preservation/selectivity criteria, suggesting that measuring average benefit is easier than predicting per-instance marginal benefit from the input alone.

The contribution is therefore not a claim that structured reasoning is new, nor that every named stage is necessary. It is an empirical account of a particular structured policy, its repeated framework-level signal, and the limits encountered when trying to decompose and route that signal.

## 2. Related Work

### 2.1 Structured and decomposed reasoning

Chain-of-Thought prompting demonstrated that prompting sufficiently capable language models to generate intermediate steps can improve arithmetic, commonsense, and symbolic reasoning. Least-to-Most prompting further showed that decomposing a difficult task into easier subproblems can improve generalization to harder compositions. Self-Consistency improved Chain-of-Thought by sampling multiple reasoning paths and aggregating their final answers. Tree of Thoughts generalized linear reasoning into explicit search over candidate thought states with lookahead and backtracking.

Our protocol is related but structurally different. It does not implement an inference tree, multi-path voting procedure, or generic subproblem decomposition. Instead, it specifies epistemic roles associated with scientific and engineering reasoning: observations, causal alternatives, first-principles constraints, falsifiable hypotheses, predictions, discriminating tests, revision, and intervention design.

### 2.2 Reflection, revision, and acting

ReAct interleaves reasoning with environment actions and observations. Self-Refine iteratively generates feedback and refines an answer, while Reflexion uses verbal feedback and episodic memory to improve future trials. These approaches make feedback and revision operational rather than treating reasoning as a single static chain.

Revision is also central to our protocol, but it appears as one component in a broader causal loop. The primary experiments evaluate textual responses rather than requiring repeated agent-environment interactions. The engineering stage additionally asks for practical controls such as reversibility, monitoring, constraints, failure modes, and second-order effects.

### 2.3 Hypothesis testing and scientific reasoning

Hypothesis Testing Prompting explicitly incorporates assumptions, backward reasoning, and fact verification into deductive reasoning. More broadly, recent work has examined the role of LLMs across scientific workflows from hypothesis generation to experimental design and discovery.

Our focus is narrower than AI-for-science: we operationalize one frozen reasoning policy and measure whether it changes answer quality on heterogeneous decision/reasoning cases. We do not claim that the protocol reproduces the full scientific method or establishes faithful internal cognition.

### 2.4 Adaptive reasoning and routing

Recent methods study when to invoke more expensive reasoning. Route to Reason jointly selects models and reasoning strategies under budget constraints, while Think When Needed uses pre-generation signals to route between Think and Non-Think modes in ranking tasks.

Our routing work differs in result more than in motivation. We observed heterogeneous FULL value and therefore attempted to route selectively, but multiple prospectively frozen strategies failed our combined quality-preservation and selectivity requirements. This negative result motivates an important distinction between **detecting average benefit** and **predicting marginal benefit for an individual input**.

### 2.5 LLM-as-a-Judge evaluation

LLM-based pairwise judging is now widely used for open-ended model evaluation. Prior work has shown useful agreement with human preferences while also documenting position, verbosity, self-enhancement, and other biases. Our design mitigates some of these issues through blinded pairwise presentation, deterministic A/B randomization, repeated independent votes, explicit agreement reporting, case-level aggregation, and case-clustered bootstrap intervals. However, the evaluator remains a model judge from the same model family/provider as the target, which is a central limitation.

## 3. Reasoning Protocol

### 3.1 FULL policy

The FULL protocol is:

1. **Observe** — identify the phenomenon and distinguish observed facts from interpretations.
2. **Diagnose** — enumerate plausible causal explanations without prematurely selecting one.
3. **Derive** — identify relevant first principles, invariants, constraints, and governing relationships.
4. **Hypothesize** — translate candidate mechanisms into testable hypotheses.
5. **Predict** — state observations expected if each hypothesis is correct.
6. **Test** — seek discriminating or falsifying evidence, prioritizing information value.
7. **Revise** — update the causal model when evidence contradicts prior beliefs.
8. **Engineer** — choose an intervention while considering constraints, reversibility, monitoring, feedback, second-order effects, and failure modes.

The governing principle is **correct models before confident solutions**.

The policy does not require verbose stage labels in the final answer. Its purpose is to control reasoning content, not surface formatting.

### 3.2 CONTROL and COMPACT

CONTROL receives no reasoning-specific system prompt. It therefore measures the target model's endogenous behavior under the task prompt alone.

A COMPACT scaffold was also developed:

> **Problem → First Principle → Mechanism → Evidence → Solution**

COMPACT is useful as a lower-overhead structured baseline, but it did not pass the held-out secondary success threshold against CONTROL, and FULL showed a preregistered directional advantage over COMPACT in the primary held-out suite.

### 3.3 Instruction versus capability

A central methodological issue emerged during development: deleting an explicit instruction does not necessarily remove the associated behavior. A model may still diagnose alternatives, revise beliefs, or propose engineering controls because the task itself or the model's training already elicits those capabilities.

We therefore distinguish:

> **reasoning capability ≠ reasoning instruction**

This distinction constrains interpretation of component ablations throughout the paper.

## 4. Evaluation Methodology

### 4.1 Research hierarchy

The project used the following evidence order:

1. establish whether the whole framework improves quality;
2. test whether individual controls measurably change behavior;
3. test whether behavior changes improve quality;
4. replicate on fresh cases;
5. only then attempt routing and cost optimization.

Quality was always primary; token and latency measures were descriptive.

### 4.2 Target and judge

The target model in the validated experiments is **GLM-5.1** accessed through Z.AI's OpenAI-compatible endpoint. The principal evaluator is **GLM-5.3-Flash**, also through Z.AI.

The evaluator is therefore a distinct model but not an independent model family or provider. We refer to this evidence as **cross-model same-family/provider**, or Tier-1B within the project's internal evidence taxonomy.

### 4.3 Pairwise judging

For quality comparisons, candidate responses were presented in randomized A/B order to the judge. The judge returned a winner or tie. Each exact generation pair received repeated votes. Orientation was deterministically randomized from case/replicate identifiers so recovery could reproduce presentation order without outcome-dependent choices.

Scores assign 1 to a FULL win, 0.5 to a tie, and 0 to a CONTROL win from FULL's perspective.

### 4.4 Unit of analysis

Judge votes and stochastic generations were not treated as independent benchmark cases. Votes were aggregated within each generation pair, generation replicates were averaged within case, and cases were treated as the independent units for uncertainty estimation.

Confidence intervals use case-clustered bootstrap resampling.

### 4.5 Execution recovery discipline

The primary held-out validation encountered a judge-format failure after all target outputs had already been generated. Before examining partial outcome distributions, a recovery protocol was frozen that retained all generated targets, retained all valid votes, requested only missing preregistered votes, preserved deterministic A/B orientation, and regenerated zero target outputs.

The completed primary report therefore contains all target runs and all planned votes without replacing target generations after the failure.

## 5. Development Studies

Development studies are included to explain the protocol's evolution and the limits of component-level interpretation. They should not be treated as independent confirmatory replications.

### 5.1 Initial quality calibration

On 12 development cases:

- FULL vs BASELINE: **0.7778**, 95% case-bootstrap interval **0.5833–0.9444**;
- COMPACT vs BASELINE: **0.8056**, interval **0.6250–0.9583**;
- FULL vs COMPACT: **0.5833**, interval **0.4167–0.7500**.

These results motivated freezing both structured prompts for stronger validation.

### 5.2 Stage ablation and capability identification

A leave-one-instruction-out experiment initially suggested positive contributions from several stages, but replication did not reproduce a stable overall component pattern. The main identification problem was behavioral redundancy: removing an instruction often did not remove the corresponding capability.

Subsequent studies separated behavior manipulation from quality. Engineering showed the strongest development signal, but Diagnose and Revise were often already near behavioral ceiling under CONTROL. Later absolute and behavioral-fidelity measurements reduced some evaluation artifacts but did not yield a stable stage module that satisfied the project's frozen carry-forward criteria.

The component program therefore does not support claims that each named stage is individually necessary.

## 6. Preregistered Held-Out Framework Validation

### 6.1 Design

The primary confirmatory experiment used 36 fresh held-out cases. Every case was generated under CONTROL, COMPACT, and FULL, with three stochastic target-generation replicates per condition. Every generated pair received three blinded randomized judge votes.

The preregistered primary comparison was FULL vs CONTROL. Success required:

- point estimate at least **0.60**;
- case-clustered 95% CI lower bound above **0.50**;
- no sufficiently populated preregistered task stratum below the harm floor of **0.45**.

### 6.2 Primary result

FULL vs CONTROL achieved:

- score: **0.6898**;
- 95% CI: **0.6096–0.7685**;
- generation-replicate majorities: **61 FULL wins / 27 ties / 20 losses**;
- case-level direction: **26 wins / 2 ties / 8 losses**;
- mean judge-vote agreement: **0.8889**;
- unanimous generation-replicate verdict fraction: **0.6944**.

The preregistered primary endpoint passed.

### 6.3 Secondary comparisons

COMPACT vs CONTROL scored **0.5864** with CI **0.5077–0.6667**. Its secondary success rule required a point estimate of at least 0.60, so it did not pass.

FULL vs COMPACT scored **0.5957** with CI **0.5417–0.6543**. The preregistered directional criterion favored FULL.

These results support the full protocol more strongly than the compact scaffold as a replacement.

### 6.4 Heterogeneity

FULL's benefit was not uniform across the primary suite.

By task stratum:

| Stratum | FULL vs CONTROL |
|---|---:|
| ENGINEER | **0.9012** |
| TEST | **0.7901** |
| BOTH | **0.6296** |
| NONE | **0.4861** |

By action requirement:

- action-required cases: **0.7375**;
- no-action cases: **0.4921**.

This pattern supports a narrower interpretation: explicit structured reasoning is especially valuable when the answer must discriminate mechanisms, design tests, or choose consequential actions.

## 7. Fresh-Suite Replications

The same frozen FULL prompt was subsequently used on three additional fresh 48-case suites created for routing-validation studies. Although these experiments had routing-specific primary questions, FULL vs CONTROL remained a prospectively measured quality comparison.

| Fresh suite | Cases | FULL vs CONTROL | 95% CI |
|---|---:|---:|---:|
| Primary held-out framework validation | 36 | **0.6898** | **0.6096–0.7685** |
| Routing v1 suite | 48 | **0.6771** | **0.6250–0.7292** |
| Routing v2 suite | 48 | **0.6875** | **0.6273–0.7477** |
| Routing v3 suite | 48 | **0.6539** | **0.5891–0.7199** |

Across the 180 fresh cases, the case-count-weighted descriptive score is approximately **0.6762**. This pooled number is descriptive only. The four suites were produced sequentially inside one research program and share the same target/evaluator families, so they should not be presented as four independent studies or assigned a pooled meta-analytic confidence interval.

The important observation is directional consistency: all four fresh suites favored FULL and all four suite-level confidence intervals were above 0.50.

## 8. Selective Routing Experiments

The heterogeneity in Section 6 motivated a natural engineering question: can the model invoke FULL only when it is likely to add decision-relevant value?

### 8.1 Routing v1

The first binary router selected FULL for 50% of cases. ROUTED beat CONTROL but failed the frozen preservation criterion against ALWAYS-FULL. v1 therefore remained a formal failure.

### 8.2 Routing v2

A new fresh suite corrected the preservation estimand prospectively while keeping the router unchanged.

Results:

- FULL vs CONTROL: **0.6875**;
- ROUTED vs CONTROL: **0.6840**;
- paired ROUTED-minus-FULL decrement: **-0.0035**, 95% CI **-0.0255 to 0.0127**;
- retained FULL gain: **98.15%**;
- FULL invocation: **70.83%**.

The quality gates passed, but the frozen selectivity cap of 65% failed. v2 was therefore a formal failure despite near-perfect quality preservation.

### 8.3 Routing v3

v3 changed the semantic routing hypothesis. It attempted to suppress FULL on causal-looking cases where a direct confound diagnosis appeared obvious.

Results:

- FULL vs CONTROL: **0.6539**;
- ROUTED vs CONTROL: **0.4988**;
- paired decrement: **-0.1551**;
- FULL invocation: **10.42%**.

The hypothesis was decisively falsified: a `CAUSAL_TRAP` stratum was routed CONTROL in all 12 cases, yet FULL scored **0.8102** on those cases.

### 8.4 Routing v4 development and stop rule

After semantic routing failed, v1-v3's 144 exposed cases were treated only as a development corpus for empirical turn-1-text prediction of FULL's marginal value. Candidate families included deterministic direct-task bypasses, TF-IDF nearest-neighbor gain prediction, and Bernoulli Naive Bayes positive-gain prediction. Thresholds were calibrated inside training folds and evaluated with leave-one-suite-out and leave-one-domain-out cross-validation.

No candidate passed all frozen development gates. The strongest candidate, `NB_DIRECT`, achieved:

- leave-one-suite-out routed score **0.6393**;
- paired decrement **-0.0336**;
- FULL invocation **56.25%**;
- leave-one-domain-out routed score **0.6493**;
- paired decrement **-0.0235**;
- FULL invocation **58.33%**.

It narrowly missed the frozen suite-held-out preservation requirement and showed unstable behavior across suite/domain shifts. The predeclared stop rule triggered. No fresh v4 routing suite was authored.

### 8.5 Routing interpretation

The routing sequence suggests that **query semantics are an imperfect proxy for marginal reasoning value**. Some apparently straightforward causal tasks still benefited strongly from FULL, and text-only empirical predictors did not generalize robustly enough under conservative preservation criteria.

This does not imply that adaptive reasoning is impossible. Rather, under the signals and target model studied here, the evidence did not justify claiming a validated router.

## 9. Discussion

### 9.1 What the framework-level result supports

The repeated FULL-vs-CONTROL advantage suggests that a structured scientific/engineering policy can improve GLM-5.1 responses on difficult reasoning and decision tasks. The strongest signal appears when answers must move beyond explanation into test design, causal discrimination, or intervention engineering.

This finding is compatible with prior structured-reasoning work but extends it into a different task regime. The protocol emphasizes not only intermediate steps but epistemic discipline: preserving alternative mechanisms, deriving constraints, making predictions that distinguish mechanisms, revising under contradictory evidence, and engineering reversible monitored actions.

### 9.2 Why component causality is harder

A whole prompt can change output quality even when removing one line does not remove the corresponding behavior. Modern models may already possess strong endogenous Diagnose or Revise capabilities. This makes naïve leave-one-instruction-out ablation a weak instrument for causal component identification.

The appropriate conclusion is therefore framework-level: the FULL prompt as a package is associated with better judged outputs. The evidence does not establish that all eight named stages are individually necessary.

### 9.3 Why routing is harder

Average treatment benefit does not imply easy instance-level treatment-effect prediction. Routing requires estimating a counterfactual: whether FULL would improve this specific case relative to CONTROL before either response is observed.

Our failures indicate that obvious surface complexity, causal language, or even learned lexical similarity are insufficient proxies under the tested constraints. This is consistent with the broader challenge of adaptive computation: the system must preserve hard-to-predict quality gains while avoiding unnecessary reasoning cost.

### 9.4 Deployment implication

The conservative architecture supported by the present evidence is:

> **DIRECT for genuinely trivial/deterministic tasks; FULL for non-trivial reasoning.**

This is not presented as a validated autonomous router. It is a deployment interpretation that prioritizes quality given the observed failure to predict marginal value reliably from non-trivial inputs.

## 10. Limitations

### 10.1 Same-family/provider judge

GLM-5.1 is evaluated by GLM-5.3-Flash, and both are GLM-family models served by Z.AI. Cross-model judging is stronger than same-model self-evaluation, but shared family/provider can induce correlated preferences or blind spots. Independent-family/provider rejudging is the highest-priority validation step.

### 10.2 Single validated target model

The framework result is established only for GLM-5.1. It may weaken, disappear, or change form on stronger, weaker, or differently trained models.

### 10.3 Program-authored benchmark suites

The benchmark cases were authored within the same research program. Freshness and prospective freezing reduce direct overfitting, but they do not substitute for transfer to established external benchmarks or externally authored cases.

### 10.4 Model-based evaluation

Repeated blinded model judgments reduce some variance and positional effects but do not provide a human-grounded gold standard. A blinded human-reviewed subset is needed to assess evaluator validity and potential style preference.

### 10.5 Sequential research adaptation

Later suites and hypotheses were designed after earlier results. Each frozen experiment should be interpreted according to its own prospective question; later fresh-suite replications are not equivalent to four fully independent preregistered studies.

### 10.6 No validated cost optimum

FULL generally uses more reasoning tokens than CONTROL. The project intentionally prioritized quality before cost. Because selective routing did not survive the frozen criteria, no claim of cost-optimal reasoning is supported.

## 11. Conclusion

A frozen scientific/engineering reasoning-control protocol improved GLM-5.1 response quality over an uncontrolled baseline on a preregistered held-out suite and retained a consistent advantage on three later fresh suites. The strongest gains occurred in tasks involving testing, engineering, and consequential action. However, the experiments also exposed two important limits. First, individual-stage causal value is difficult to identify because instruction manipulation does not reliably manipulate latent capability. Second, the marginal value of deep reasoning is difficult to predict from the input alone: multiple selective-routing approaches failed frozen quality/selectivity criteria, and a final empirical development stage triggered a stop rule.

The narrow conclusion is therefore stronger than either an optimistic or pessimistic extreme. Structured reasoning control can improve difficult decision-quality outputs, but neither the necessity of every stage nor a reliable mechanism for selectively skipping deep reasoning has been established. The next decisive evidence should come from independent-family or human evaluation, cross-target replication, and external benchmark transfer rather than further tuning of the exposed routing suites.

## References

- Guo, H. et al. (2026). *Think When Needed: Model-Aware Reasoning Routing for LLM-based Ranking*. arXiv:2601.18146.
- Li, Y. et al. (2024). *Hypothesis Testing Prompting Improves Deductive Reasoning in Large Language Models*. arXiv:2405.06707.
- Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback*. arXiv:2303.17651.
- Pan, Z. et al. (2025). *Route to Reason: Adaptive Routing for LLM and Reasoning Strategy Selection*. arXiv:2505.19435.
- Shi, L. et al. (2024). *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge*. arXiv:2406.07791.
- Shinn, N. et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning*. arXiv:2303.11366.
- Wang, X. et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning in Language Models*. arXiv:2203.11171.
- Wei, J. et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. NeurIPS 2022; arXiv:2201.11903.
- Yao, S. et al. (2023). *Tree of Thoughts: Deliberate Problem Solving with Large Language Models*. NeurIPS 2023; arXiv:2305.10601.
- Yao, S. et al. (2022/2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023; arXiv:2210.03629.
- Zhang, Y. et al. (2025). *Advancing the Scientific Method with Large Language Models: From Hypothesis to Discovery*. arXiv:2505.16477.
- Zheng, L. et al. (2023/2024). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv:2306.05685.
- Zhou, D. et al. (2022/2023). *Least-to-Most Prompting Enables Complex Reasoning in Large Language Models*. ICLR 2023; arXiv:2205.10625.

## Internal evidence sources

Exact experimental values, provenance, hashes, and claim boundaries should be verified against:

- `docs/RESEARCH_SYNTHESIS_V1.md`
- `docs/HELDOUT_FRAMEWORK_VALIDATION_V1_GLM53FLASH_RESULTS.md`
- `docs/SELECTIVE_ROUTING_V1_RESULTS.md`
- `docs/SELECTIVE_ROUTING_V2_RESULTS.md`
- `docs/SELECTIVE_ROUTING_V3_RESULTS.md`
- `docs/SELECTIVE_ROUTING_V4_DEVELOPMENT_RESULTS.md`
- `docs/ABLATION_V0_6_1_REPLICATION_RESULTS.md`
- `docs/CAPABILITY_IDENTIFICATION_V0_7.md`
- `docs/BEHAVIORAL_FIDELITY_V0_11.md`
