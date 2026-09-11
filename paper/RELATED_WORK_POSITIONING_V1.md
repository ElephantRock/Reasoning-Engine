# Related-Work Positioning v1

Status: manuscript-support document. External literature was reviewed on 2026-09-11; project-internal claims remain governed by `docs/RESEARCH_SYNTHESIS_V1.md`.

## Positioning summary

The paper should **not** claim novelty for eliciting step-by-step reasoning, decomposition, reflection, search, or adaptive reasoning in general. Those ideas are already well represented by Chain-of-Thought, Least-to-Most prompting, Self-Consistency, Tree of Thoughts, ReAct, Self-Refine, Reflexion, hypothesis-testing prompting, and recent reasoning-routing work.

The strongest defensible positioning is narrower:

> We study a frozen scientific/engineering reasoning-control protocol that explicitly separates observation, diagnosis, first-principles derivation, hypothesis formation, prediction, testing, revision, and engineering action. The contribution is not merely the stage names; it is the empirical program that prospectively separates framework-level quality effects, component-identification claims, and selective-routing claims, including documented negative results and a stop rule.

## Closest conceptual precedents

### Chain-of-Thought prompting

Wei et al. (2022), *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, established that eliciting intermediate reasoning steps can improve arithmetic, commonsense, and symbolic reasoning.

Relation to this project:

- shared: explicit intermediate reasoning;
- different: the FULL protocol is a structured causal/scientific/engineering control policy rather than an unconstrained rationale chain;
- manuscript implication: do not present “step-by-step reasoning” itself as novel.

Reference: https://arxiv.org/abs/2201.11903

### Least-to-Most prompting

Zhou et al. (2022), *Least-to-Most Prompting Enables Complex Reasoning in Large Language Models*, decomposes difficult problems into simpler subproblems solved sequentially.

Relation:

- shared: decomposition and staged progression;
- different: this project organizes stages by epistemic role—observation, causal diagnosis, derivation, falsifiable prediction, revision, and intervention—rather than by subproblem granularity.

Reference: https://arxiv.org/abs/2205.10625

### Self-Consistency

Wang et al. (2022), *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, samples multiple reasoning paths and aggregates answers.

Relation:

- shared: recognition that one greedy reasoning trajectory is not always reliable;
- different: our intervention is a single structured policy prompt, while stochastic replication is used primarily for evaluation rather than answer-time ensemble selection.

Reference: https://arxiv.org/abs/2203.11171

### Tree of Thoughts

Yao et al. (2023), *Tree of Thoughts: Deliberate Problem Solving with Large Language Models*, introduces explicit search over multiple candidate thoughts with lookahead and backtracking.

Relation:

- shared: deliberate reasoning and revision;
- different: FULL does not instantiate a search tree or multi-branch inference algorithm. It instead prescribes epistemic operations within a single response trajectory.

Reference: https://arxiv.org/abs/2305.10601

### ReAct

Yao et al. (2022/2023), *ReAct: Synergizing Reasoning and Acting in Language Models*, interleaves reasoning traces with environment actions and observations.

Relation:

- shared: action, observation, and model revision are coupled;
- different: this project evaluates textual decision reasoning even without a live environment and emphasizes discriminating tests, causal uncertainty, reversibility, monitoring, and second-order effects.

Reference: https://arxiv.org/abs/2210.03629

### Self-Refine and Reflexion

Madaan et al. (2023), *Self-Refine: Iterative Refinement with Self-Feedback*, iteratively critiques and revises outputs. Shinn et al. (2023), *Reflexion: Language Agents with Verbal Reinforcement Learning*, uses linguistic reflection and feedback across trials.

Relation:

- shared: revision after feedback;
- different: Revision is one stage inside a broader evidence-to-intervention protocol; our primary held-out experiment does not require repeated self-critique loops or episodic memory.

References:

- https://arxiv.org/abs/2303.17651
- https://arxiv.org/abs/2303.11366

### Hypothesis Testing Prompting

Li et al. (2024), *Hypothesis Testing Prompting Improves Deductive Reasoning in Large Language Models*, explicitly uses assumptions, backward reasoning, and fact verification.

Relation:

- shared: hypothesis formation and explicit testing;
- different: our protocol embeds hypothesis testing within a full causal and engineering loop, including observation discipline, mechanism, prediction, revision, constraints, monitoring, and downstream action.

Reference: https://arxiv.org/abs/2405.06707

### LLMs and the scientific method

Zhang et al. (2025), *Advancing the Scientific Method with Large Language Models: From Hypothesis to Discovery*, reviews LLM involvement across stages of the scientific cycle.

Relation:

- shared: scientific-method framing;
- different: that work is a broad review of AI-for-science workflows, whereas this project operationalizes one frozen textual reasoning-control protocol and evaluates it experimentally on decision/reasoning cases.

Reference: https://arxiv.org/abs/2505.16477

## Adaptive reasoning and routing

Recent work explicitly studies when models should invoke deeper reasoning.

Pan et al. (2025), *Route to Reason: Adaptive Routing for LLM and Reasoning Strategy Selection*, jointly routes models and reasoning strategies under budget constraints.

Guo et al. (2026), *Think When Needed: Model-Aware Reasoning Routing for LLM-based Ranking*, learns a pre-generation router for Think vs Non-Think modes using task/model-aware signals.

Relation to this project:

- shared: heterogeneous marginal value of deeper reasoning and the quality-cost trade-off;
- different: our routing line is primarily a **negative result**. Under prospectively frozen quality-preservation and selectivity gates, semantic and text-only routing strategies did not robustly justify skipping FULL. The paper should use this to argue that demonstrating average reasoning-policy benefit and predicting instance-level marginal benefit are distinct empirical problems.

References:

- https://arxiv.org/abs/2505.19435
- https://arxiv.org/abs/2601.18146

## LLM-as-a-Judge literature

Zheng et al. (2023), *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, showed that strong LLM judges can approximate human preferences but documented position, verbosity, self-enhancement, and reasoning biases.

Shi et al. (2024), *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge*, further demonstrates that position bias is task- and judge-dependent.

More recent work continues to emphasize that judge choice and debiasing materially affect conclusions.

Relation to this project:

- strengths: blinded pairwise evaluation, deterministic A/B randomization, repeated votes, agreement reporting, case-level aggregation, and case-clustered bootstrap intervals;
- remaining limitation: GLM-5.1 target and GLM-5.3-Flash judge share family/provider, and the program lacks a human preference layer.

References:

- https://arxiv.org/abs/2306.05685
- https://arxiv.org/abs/2406.07791
- https://arxiv.org/abs/2604.23178

## Novelty claim that is safe

A defensible related-work paragraph should claim approximately:

> Prior prompting and inference methods show that decomposition, intermediate reasoning, search, reflection, and verification can improve LLM performance. Our focus is different: we evaluate a fixed scientific/engineering reasoning-control policy as a whole, then explicitly test whether its apparent benefit can be causally decomposed into named instruction modules and whether its marginal value can be predicted well enough for selective routing. The program therefore contributes both a positive framework-level result and negative evidence about component identification and input-only routing.

## Claims to avoid

Do not claim that this work:

- invents structured reasoning;
- is the first to use the scientific method with LLMs;
- is the first to combine reasoning and action;
- is the first to study adaptive reasoning depth;
- demonstrates faithful internal reasoning traces;
- establishes human-valid evaluation;
- establishes independent-family/provider replication.

## Reviewer-facing differentiation

The strongest differentiators are methodological:

1. **framework effect vs component effect** are treated as separate hypotheses;
2. **instruction removal vs capability removal** is empirically distinguished;
3. **fresh-suite replication** is repeated after the primary held-out result;
4. **routing quality and selectivity are prospectively gated** rather than inferred from author labels;
5. **negative routing results are retained** and a frozen stop rule is obeyed;
6. **execution recovery preserves generated targets** instead of silently regenerating after judge-format failure;
7. evidence boundaries are explicit: same-family judge, single target model, authored suites, no human layer.

These features are more defensible as the paper's contribution than the superficial eight-stage naming scheme alone.
