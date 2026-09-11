# Manuscript Review v2

Status: second-pass reviewer-style audit after title narrowing, bibliography verification, and addition of submission support materials.

## Overall assessment

`paper/MANUSCRIPT_DRAFT_V2.md` is **content-ready for a technical report / public preprint**, subject to format conversion, figure rendering, and author/front-matter completion.

It is still not evidence-complete for a strong general LLM reasoning claim. A stronger conference/journal submission would benefit materially from at least one independent validation layer.

## Changes that resolved v1 review concerns

1. **Title narrowed.** The v2 title no longer implies general LLM-family validity:

   > Evaluating Structured Scientific/Engineering Reasoning Control: Quality Gains, Component Limits, and Routing Failures

2. **Same-family limitation remains in the abstract.** The abstract explicitly states that target and evaluator share GLM family and Z.AI provider.

3. **No hidden-reasoning faithfulness claim.** The introduction and limitations now state that the protocol is an output-control policy and does not establish faithful latent eight-stage cognition.

4. **Prompt-length/style confounding added.** The manuscript now identifies the possibility that FULL's longer and more prescriptive prompt may induce judge-favored organization or coverage independently of the intended epistemic mechanism.

5. **Related work now uses explicit citation hooks.** The paper distinguishes its contribution from CoT, decomposition, multi-path aggregation, search, reflection, acting, hypothesis-testing prompting, and adaptive reasoning routing.

6. **Bibliography metadata reviewed against current sources.** Self-Refine and Reflexion are recorded as NeurIPS 2023; MT-Bench/Chatbot Arena as NeurIPS 2023; Think When Needed as SIGIR 2026; and the position-bias paper retains both its 2024 preprint and 2025 IJCNLP-AACL publication records.

7. **Figure/table package added.** `paper/TABLES_AND_FIGURES_V1.md` contains the frozen numerical inputs and explicit anti-overclaiming rules for figures.

8. **Submission checklist added.** `paper/SUBMISSION_CHECKLIST_V1.md` separates preprint-ready work from stronger-venue evidence requirements.

## Numerical consistency review

The v2 manuscript remains consistent with authoritative repository results on every headline value reviewed:

- primary FULL vs CONTROL: `0.6898`, CI `0.6096–0.7685`;
- COMPACT vs CONTROL: `0.5864`, CI `0.5077–0.6667`;
- FULL vs COMPACT: `0.5957`, CI `0.5417–0.6543`;
- primary heterogeneity: ENGINEER `0.9012`, TEST `0.7901`, BOTH `0.6296`, NONE `0.4861`;
- action-required `0.7375`, no-action `0.4921`;
- routing-suite FULL replications: `0.6771`, `0.6875`, `0.6539`;
- v2 routed score `0.6840`, paired decrement approximately `-0.0035`, FULL use `70.83%`;
- v3 routed score `0.4988`, paired decrement `-0.1551`, FULL use `10.42%`;
- v4 remains exposed-data development with no qualifying candidate and no fresh validation suite.

No scientific inconsistency was identified.

## Literature-positioning review

The paper's safe novelty remains methodological and empirical rather than algorithmic.

Do not position the work as inventing structured reasoning, scientific prompting in general, reasoning-plus-action, reflection, or adaptive routing. Existing literature already covers those broad categories.

The defensible contribution is the combination of:

- one frozen scientific/engineering reasoning policy;
- prospective separation of framework, component, and routing hypotheses;
- a preregistered held-out framework test;
- three subsequent fresh-suite framework replications;
- explicit evidence that instruction removal is not capability removal;
- multiple retained routing failures;
- a development stop rule that was obeyed;
- fail-closed recovery preserving all target outputs after execution-format failure.

## Remaining reviewer risks

These are scientific limitations, not manuscript defects:

1. same-family/provider evaluator;
2. one validated target model;
3. program-authored benchmark suites;
4. no blinded human preference layer;
5. possible prompt-length/style preference confounding;
6. sequential adaptation across later research stages;
7. no external-benchmark transfer;
8. no validated cost-optimal router.

## Preprint verdict

**PASS for public technical report / preprint preparation.**

Remaining mechanical work:

- convert Markdown to LaTeX or chosen preprint template;
- render figures from `TABLES_AND_FIGURES_V1.md`;
- run bibliography build;
- add authors/affiliations/acknowledgments/license/repository link;
- perform final proofread after typesetting.

## Stronger-venue verdict

**Not yet maximally persuasive for a strong general-purpose reasoning venue.**

Highest-value new evidence, in order:

1. independent-family/provider rejudging of frozen outputs;
2. blinded human evaluation on a stratified subset;
3. cross-target replication;
4. external benchmark transfer.

Do not reopen routing development on v1-v3 exposed cases merely to improve the paper.
