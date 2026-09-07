# v0.10 preregistration note

Before execution, the following analysis choices are frozen:

- families: TEST and ENGINEER only;
- cases: exactly two new development cases per family;
- conditions: CONTROL, ATTENTION, TARGET;
- target generations: 3 per case/condition;
- independent absolute behavior votes: 3 per generated response;
- pairwise quality votes: 3 per comparison;
- behavior aggregation order: judge votes within response → generations within case → cases within family;
- manipulation gate: family TARGET minus CONTROL absolute behavior >= 0.5/4;
- primary quality comparison: TARGET vs CONTROL;
- specificity comparison: TARGET vs ATTENTION;
- generic attention control: ATTENTION vs CONTROL;
- quality effects are instruction-mediated evidence only when the absolute behavior manipulation gate passes;
- token/latency diagnostics do not enter the decision;
- all v0.10 cases are development data, not held-out validation.
