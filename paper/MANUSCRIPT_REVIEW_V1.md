# Manuscript Review v1

Status: internal reviewer-style audit of `paper/MANUSCRIPT_DRAFT_V1.md`.

## Overall assessment

The manuscript is strong enough for a technical report / preprint draft, but it is not yet ready for a strong conference or journal submission without either (a) one additional independent validation layer or (b) a very explicit empirical-methods framing with narrow claims.

The central result is coherent and reproducible from the repository:

- preregistered 36-case FULL vs CONTROL: `0.6898`, CI `0.6096–0.7685`;
- three later fresh-suite FULL vs CONTROL results: `0.6771`, `0.6875`, `0.6539`;
- consistent positive direction across all four fresh suites;
- strongest primary-suite effects in TEST / ENGINEER / action-required strata;
- component-level causality unresolved;
- no selective router validated;
- v4 routing stop rule obeyed.

## Highest-priority manuscript correction

The current title is broader than the evidence warrants:

> Structured Reasoning Control Improves LLM Decision Quality but Resists Reliable Selective Routing

The validated target is one model, GLM-5.1, and the evaluator is same-family/provider. Before external submission, prefer a narrower title such as:

> **Structured Scientific/Engineering Reasoning Improves GLM-5.1 Decision Quality but Resists Reliable Selective Routing**

or, if a less model-specific title is desired:

> **Evaluating Structured Scientific/Engineering Reasoning Control: Quality Gains, Component Limits, and Routing Failures**

The second title is preferable for a methods paper because it avoids implying cross-model-family generality.

## Novelty review

### Safe novelty

The safe novelty is **not** “structured reasoning” itself. Prior work already establishes:

- Chain-of-Thought reasoning;
- decomposition / Least-to-Most;
- multi-path aggregation / Self-Consistency;
- explicit search / Tree of Thoughts;
- reasoning-plus-action / ReAct;
- iterative feedback / Self-Refine and Reflexion;
- hypothesis-testing prompting;
- adaptive reasoning routing.

The defensible novelty is the combination of:

1. a fixed scientific/engineering reasoning-control policy;
2. prospective separation of framework-level, component-level, and routing-level hypotheses;
3. fresh-suite framework replication after the primary held-out result;
4. explicit evidence that instruction removal is not capability removal;
5. multiple failed routing validations retained as negative results;
6. a preregistered routing-development stop rule that was actually followed;
7. fail-closed recovery that preserved all generated target outputs after judge-format failure.

### Unsafe novelty claims

Do not write:

- “first scientific-method prompting framework”;
- “first adaptive reasoning system”;
- “first reasoning-and-action framework”;
- “proves the eight stages are necessary”;
- “general improvement for LLMs”;
- “human-validated quality improvement”.

## Methods review

### Strengths

- fresh held-out suite for the primary framework endpoint;
- preregistered primary thresholds;
- stochastic target replicates;
- repeated randomized blinded pairwise judge votes;
- case-level aggregation;
- case-clustered bootstrap intervals;
- exact suite / artifact provenance;
- recovery without target regeneration;
- routing gates frozen before their corresponding fresh-suite runs;
- negative results retained.

### Reviewer vulnerabilities

1. **Same-family evaluator.** GLM-5.3-Flash may share preferences with GLM-5.1.
2. **Single target model.** Generalization beyond GLM-5.1 is unknown.
3. **Program-authored tasks.** Freshness is preserved prospectively, but external task transfer is not established.
4. **Model judge rather than humans.** Pairwise blinding reduces some bias but cannot establish human preference validity.
5. **Sequential adaptation.** Later suites are fresh for their own questions but are not independent replications in the strongest statistical sense.
6. **Prompt-length/style confounding.** FULL may alter verbosity or structure in ways a model judge prefers; human or independent-family review would help separate substantive reasoning quality from style preference.
7. **No direct faithfulness claim.** The observed textual structure should not be interpreted as evidence that the model's latent internal reasoning faithfully follows the named stages.

## Results review

The manuscript correctly gives the 36-case held-out validation primacy. The later 48-case suites should remain under a separate “fresh-suite replications” heading and should not be pooled inferentially.

The descriptive 180-case weighted score (`~0.6762`) is acceptable only with the explicit warning already present: it is not a preregistered meta-analysis and the suites are sequential within one program.

The routing sequence is valuable as a negative contribution. In particular:

- v2 demonstrates that quality can be almost fully preserved while selectivity fails;
- v3 demonstrates that semantic intuitions about “obvious causal traps” can be actively wrong about marginal FULL value;
- v4 demonstrates that exposed-data text-only prediction improved over v3 but still failed conservative cross-suite preservation criteria.

This is stronger as a methods lesson than as an efficiency result.

## Related-work review

The current related-work scope is appropriate. The most important comparison classes are:

- Wei et al. 2022 — Chain-of-Thought;
- Zhou et al. 2022/2023 — Least-to-Most;
- Wang et al. 2022/2023 — Self-Consistency;
- Yao et al. 2023 — Tree of Thoughts;
- Yao et al. 2022/2023 — ReAct;
- Madaan et al. 2023 — Self-Refine;
- Shinn et al. 2023 — Reflexion;
- Li et al. 2024 — Hypothesis Testing Prompting;
- recent adaptive reasoning / routing work including Route to Reason and Think When Needed;
- LLM-as-a-Judge bias literature.

The literature positioning should explicitly say that the paper evaluates a **policy and research methodology**, not a new decoding algorithm.

## Minimum work before a public preprint

1. narrow the title;
2. convert references into a formal BibTeX file;
3. add a reproducibility appendix with exact prompt hashes, suite hashes, run IDs, and artifact digests;
4. add a figure/table package;
5. run a final consistency check between manuscript numbers and authoritative result documents;
6. make the same-family/single-target limitations prominent in the abstract and conclusion.

## Minimum work before a stronger venue submission

At least one of the following is strongly recommended; two would materially improve the paper:

- independent-family/provider rejudging of frozen outputs;
- blinded human evaluation on a stratified subset;
- replication on a second target-model family;
- transfer to an externally authored benchmark.

## Recommended immediate next action

Do **not** reopen routing.

Prepare a reproducibility appendix and formal bibliography on the current paper branch. If independent-evaluator or human resources become available, add that as a separate prospective validation layer rather than tuning the existing exposed benchmark suites.
