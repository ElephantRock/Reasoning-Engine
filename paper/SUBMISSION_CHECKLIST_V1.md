# Submission Readiness Checklist v1

Status: working checklist for a public technical report / preprint and stronger venue submission.

## A. Preprint-ready requirements

- [x] Narrow title so it does not imply general LLM-family validity.
- [x] Make same-family/provider evaluator limitation explicit in abstract.
- [x] Keep 36-case preregistered held-out experiment as primary confirmatory result.
- [x] Separate later routing-suite FULL-vs-CONTROL measurements as prospective fresh-suite replications.
- [x] Keep the 180-case aggregate descriptive only.
- [x] State that individual-stage causality is unresolved.
- [x] State that no selective router was validated.
- [x] State that no cost-optimal policy was established.
- [x] Add prompt-length/style-confounding limitation.
- [x] Add no-hidden-reasoning-faithfulness claim boundary.
- [x] Verify bibliography against current publication metadata where available.
- [x] Provide exact prompts, suite/run provenance, artifact digests, and recovery record in reproducibility appendix.
- [x] Provide paper table/figure data package.
- [ ] Convert Markdown manuscript to chosen submission format (LaTeX or venue template).
- [ ] Generate publication-quality figures from the frozen data package.
- [ ] Run final reference/citation build check after format conversion.
- [ ] Add author names, affiliations, acknowledgments, funding/conflict statements as applicable.
- [ ] Add repository/archive link and license statement appropriate for public release.

## B. Stronger conference/journal requirements

At least one additional validation layer is strongly recommended; two would materially strengthen the paper.

- [ ] Independent-family/provider rejudging of frozen outputs.
- [ ] Blinded human evaluation on a stratified subset.
- [ ] Cross-target replication on a materially different model family.
- [ ] Transfer to an external benchmark or externally authored cases.

Do not delay a technical report/preprint solely because these are unavailable, but keep claims narrow.

## C. Final scientific consistency review

Before submission, mechanically verify every headline value against authoritative repository sources:

- primary FULL vs CONTROL: `0.6898`, CI `0.6096–0.7685`;
- COMPACT vs CONTROL: `0.5864`, CI `0.5077–0.6667`;
- FULL vs COMPACT: `0.5957`, CI `0.5417–0.6543`;
- primary heterogeneity: ENGINEER `0.9012`, TEST `0.7901`, BOTH `0.6296`, NONE `0.4861`;
- action-required `0.7375`, no-action `0.4921`;
- routing-suite FULL replications: `0.6771`, `0.6875`, `0.6539`;
- v2 routed: `0.6840`, paired decrement `-0.00347`, FULL use `70.83%`;
- v3 routed: `0.4988`, paired decrement `-0.1551`, FULL use `10.42%`;
- v4 stop rule: no qualifying candidate, no v4 fresh validation suite.

## D. Claims that must not appear without new evidence

- general improvement across LLM families;
- independent-family/provider validation;
- human-validated superiority;
- causal necessity of each of the eight stages;
- faithful internal chain-of-thought implementation of the stages;
- validated autonomous routing;
- 65%-cap routing success;
- cost optimality;
- independent-study meta-analysis of the four fresh suites;
- external-benchmark generalization.

## E. Recommended public-paper framing

Preferred title:

**Evaluating Structured Scientific/Engineering Reasoning Control: Quality Gains, Component Limits, and Routing Failures**

Preferred one-sentence thesis:

> A frozen scientific/engineering reasoning-control prompt improves judged GLM-5.1 output quality on a preregistered held-out suite and three later fresh suites, while stage-level causal identification and input-only selective routing remain unresolved under conservative prospective tests.

Preferred paper type today:

- technical report / preprint;
- workshop or empirical-methods submission with explicit limitations.

For a stronger full-paper venue, prioritize independent evaluation or cross-target replication rather than further routing tuning on exposed data.
