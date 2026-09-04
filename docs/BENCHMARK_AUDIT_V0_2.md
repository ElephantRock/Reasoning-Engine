# Benchmark v0.1 audit → v0.2 corrections

This audit was performed before treating any benchmark output as evidence. The source reasoning protocol remains the object under test; the changes below repair the measurement system rather than assuming the protocol works.

## Material defects found

1. **Future-evidence leakage in sequential evaluation — high severity.** The v0.1 evaluator received the full multi-turn transcript and full hidden key at once. An instruction not to use future evidence is weaker than structurally withholding it. v0.2 evaluates each turn using only the transcript prefix and a turn-specific reference.

2. **Condition leakage to the “blinded” evaluator — high severity.** v0.1 passed `condition` to the protocol judge. v0.2 removes the condition from both judge-visible content and evaluator metadata.

3. **Non-applicable dimensions distorted composite scores — high severity.** v0.1 asked judges to score all dimensions, including revision on single-turn tasks and engineering on pure diagnostic tasks. v0.2 adds per-case applicability masks and scores only applicable dimensions.

4. **Prospective action quality was mislabeled as realized effectiveness — high severity.** Most cases do not observe intervention outcomes, so `action_effectiveness` cannot be known. v0.2 replaces it with `decision_quality`; `realized_outcome` is optional and should be used only when an outcome is actually observed.

5. **Adaptive mode selection was specified but not experimentally tested — high severity.** The v0.1 `FULL` condition loaded the full controller even for arithmetic tasks, so it paid full prompt cost regardless of visible response depth. v0.2 adds an `ADAPTIVE` condition: a router selects DIRECT, COMPACT, or FULL before the controller is loaded, and routing cost is included in usage.

6. **`selected_mode` was never populated — medium severity.** v0.2 records the controller selected by static conditions or the adaptive router, and separately uses a blinded mode judge to infer visible reasoning depth and score mode fit.

7. **Multi-seed pairwise collisions — high severity.** v0.1 indexed pairwise runs only by `(case_id, condition)`, so repeated seeds overwrite one another conceptually. v0.2 pairs by `(case_id, model, seed, condition)` and gives every run/pair a stable ID.

8. **No uncertainty estimates for aggregate effects — medium severity.** v0.2 reports mean, median, standard deviation, bootstrap 95% confidence intervals, and paired deltas versus baseline.

9. **Outcome judge was exposed to protocol-shaped evaluator guidance — medium severity.** v0.2 gives turn-specific outcome references and excludes violation labels / condition identity from outcome judging. Pairwise judging receives a sanitized factual reference rather than the protocol-compliance key.

10. **Penalty scores risk double-counting defects — medium severity.** v0.2 keeps raw quality as the primary metric, reports violation rates separately, and retains penalized quality only as a secondary diagnostic.

11. **The benchmark could reward ceremonial completeness — medium severity.** v0.2's applicability masks and mode-fit scoring make unnecessary stages a potential efficiency cost rather than an automatic scoring opportunity.

12. **Sequential revision was aggregated without explicit turn boundaries — high severity.** v0.2 stores turn-level protocol and outcome judgments so correct revision, under-revision, and stability can be inspected directly.

13. **Repeated seeds are not independent benchmark cases — medium severity.** v0.2 aggregates repeated seeds within each case/model before confidence intervals and paired effect estimates, so replication does not artificially increase the effective case count.

## Result

The v0.1 harness was suitable as a prototype but not yet strong enough for claims about whether the reasoning protocol improves model behavior. v0.2 is a substantially less biased measurement instrument.

These are harness findings, not evidence that the reasoning controller itself succeeds or fails.
