# Operator Fidelity v0.2 — Bounded-Operator Fidelity Study

Status: **development design; freeze before any paid v0.2 target generation**.

## 1. Motivation

Operator Fidelity v0.1 formally returned `STOP_REDESIGN_OPERATORS`: none of the six specialists passed the frozen lift-and-separation gate.

The review in `OPERATOR_FIDELITY_V0_1_RESULTS.md` identifies two measurement problems that must be corrected before abandoning the operator hypothesis:

1. the broad 0–4 behavior scale saturated (39/48 intended-dimension condition scores were exactly 4.0; all six probes had a nonmatching-specialist median of 4.0);
2. several v0.1 user prompts directly requested the target behavior, making CONTROL and unrelated specialists likely to express it without the specialist instruction.

This v0.2 study remains Stage 0. It does **not** authorize Stage 1 unless the redesigned manipulation passes prospectively frozen gates.

## 2. Scientific question

For each proposed specialist policy `s`, does the instruction cause a reproducible increase in the **fidelity of its intended observable sub-behaviors** on fresh tasks where that reasoning mode is useful but is not explicitly requested by the user?

The primary object is instruction-induced behavioral fidelity, not answer quality.

## 3. Conditions

Every case is run under eight conditions:

- `CONTROL`
- frozen v0.1 `FULL`
- `DEDUCTIVE_CONSTRAINT`
- `ABDUCTIVE_DIAGNOSTIC`
- `CAUSAL_EXPERIMENTAL`
- `SEARCH_PLANNING`
- `DECISION_THEORETIC`
- `SYSTEMS_FEEDBACK`

The six specialist prompts are new v0.2 prompts. Their conceptual families are unchanged, but each is explicitly a **bounded primary operator**: it should allocate reasoning effort to its own epistemic function and avoid expanding into unrelated modes unless minimally necessary to complete the task.

`FULL` is copied exactly from v0.1 and remains the generalist comparator.

## 4. Fresh probes

Use 12 new development cases: two per specialist family.

Rules:

- no v0.1 Stage-0 case is reused;
- user prompts do not name the operator or ask for its canonical sub-behaviors;
- each case has a neutral decision request such as "What should we do?", "Is this allowed?", or "Should we proceed?";
- the target operator should be materially useful but not the only behavior a capable model could exhibit;
- domains vary within each family;
- all required facts are supplied in the case so the study does not depend on external factual recall.

## 5. Fidelity measurement

The v0.1 six-dimensional 0–4 rubric is retired for Stage-0 manipulation testing.

Each specialist family has five predeclared observable criteria. Each response is shown **alone** to the fidelity judge and scored on the criteria for that case's intended family:

- `0.0` — absent, contrary, or unusable;
- `0.5` — partial, implicit, weak, or incomplete;
- `1.0` — clear, substantively complete, and decision-relevant.

The response fidelity composite is the unweighted mean of the five criteria.

### DEDUCTIVE_CONSTRAINT criteria

1. identifies the premises/constraints that actually determine the result;
2. separates necessary conclusions from assumptions or conventions;
3. derives feasibility/necessity rather than merely asserting it;
4. checks a boundary case, counterexample, or hidden assumption that could flip the conclusion;
5. if blocked, identifies a genuinely minimal relaxation/resource change and explains why it is sufficient.

### ABDUCTIVE_DIAGNOSTIC criteria

1. preserves at least two materially plausible explanations rather than collapsing immediately;
2. ties each leading explanation to expected evidence or mechanism-consistent observations;
3. states what would weaken or disconfirm at least the leading explanations;
4. chooses evidence/action that discriminates among explanations rather than only confirming one;
5. calibrates the ranking and preserves residual uncertainty when the evidence remains underdetermined.

### CAUSAL_EXPERIMENTAL criteria

1. states the causal ambiguity/estimand or counterfactual distinction rather than treating association as effect;
2. identifies material confounding, alternative paths, or rival causal mechanisms;
3. proposes an intervention/comparison capable of changing causal beliefs;
4. gives outcome predictions or decision implications that differ across rival explanations;
5. states a falsification/identification limitation or condition under which the causal conclusion should be revised.

### SEARCH_PLANNING criteria

1. represents the relevant objective, state, hard constraints, and legal actions/prerequisites;
2. considers at least one materially different path, ordering, or branch rather than extending the first idea automatically;
3. identifies a bottleneck, dependency, dead end, or irreversible step that constrains the plan;
4. includes checkpoints plus a branch, fallback, or recovery action tied to observed state;
5. preserves options/reversibility where uncertainty makes premature commitment costly.

### DECISION_THEORETIC criteria

1. distinguishes the feasible actions and materially different consequences;
2. represents consequential uncertainty rather than reasoning only from the modal outcome;
3. accounts for asymmetric upside/downside or opportunity cost;
4. uses reversibility, option value, or value of information in comparing actions;
5. states a stopping/information criterion or assumption under which the preferred action would change.

### SYSTEMS_FEEDBACK criteria

1. identifies the material state variables/capacities and directional links among them;
2. identifies at least one feedback loop or endogenous behavioral response that changes the intervention effect;
3. accounts for a relevant delay, adaptation, accumulation, or time-horizon effect;
4. anticipates bottleneck migration, rebound, displacement, or another second-order system effect;
5. ties monitoring, rollback, or intervention design to those dynamics rather than treating them as generic caveats.

The fidelity judge must not see condition labels.

## 6. Replication and aggregation

For each of 12 cases × 8 conditions:

- one target generation;
- two independent fidelity-judge votes on the exact response.

For each exact response:

1. average the two judge votes criterion-by-criterion;
2. average the five criteria into a response composite.

For each specialist family:

1. average the matching specialist's composite across its two cases;
2. average CONTROL across the same two cases;
3. average FULL across the same two cases;
4. for each nonmatching specialist, average across the same two cases, then take the median across the five nonmatching specialists.

Primary manipulation quantities:

- `lift_control = specialist_fidelity - control_fidelity`;
- `separation = specialist_fidelity - median_nonmatching_specialist_fidelity`.

Also compute the per-case specialist-minus-CONTROL lift and retain its minimum as a consistency diagnostic.

## 7. Frozen eligibility gate

A specialist is eligible for Stage 1 only if all conditions hold:

1. `lift_control >= 0.15` on the 0–1 composite scale;
2. `separation >= 0.10`;
3. specialist-minus-CONTROL fidelity is nonnegative on both fresh cases;
4. no matching-specialist fidelity vote identifies a material factual/logical/constraint/decision pathology;
5. no pairwise quality-sanity vote attributes a material pathology to the matching specialist.

The `0.15` lift threshold reuses the pre-existing behavioral-fidelity identification threshold from the earlier v0.11 program instead of choosing a new threshold after seeing v0.2 data.

The `0.10` separation threshold corresponds to a persistent half-step improvement on one of five observable criteria and is frozen before target generation.

Program decision:

- 6 eligible → `PASS_ALL_SIX`;
- 4–5 eligible → `PASS_SUBSET_REDESIGN_STAGE1`;
- 0–3 eligible → `STOP_REDESIGN_OPERATORS`.

## 8. Quality sanity

For each case, compare the matching specialist once against CONTROL and once against FULL using the existing blinded pairwise quality rubric.

Quality is **not** the Stage-0 manipulation gate. It is used to detect severe specialist pathologies and to describe whether specialization appears to trade quality for fidelity.

No specialist is disqualified merely for an ordinary pairwise loss; only a judge-attributed material factual, logical, constraint, or decision-quality pathology blocks eligibility.

## 9. Execution safeguards

Target:

- model: `glm-5.1`;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- temperature: `0`;
- completion-token ceiling: `32768`.

Judge:

- model: `glm-5.3-flash`;
- same endpoint;
- temperature: `0`;
- completion-token ceiling: `16384`;
- JSON mode;
- up to three formatting/schema attempts per required vote; only the first valid response counts.

Target-output rule:

- if any target response is empty, returns `finish_reason = length`, or reaches the 32768 completion-token ceiling, stop before judging and preserve the partial artifact;
- do not silently regenerate a completed valid target response;
- any recovery must be frozen in a new document before execution.

Record target/judge usage, latency, finish reason, and all invalid judge-format attempts.

## 10. Interpretation

If v0.2 passes, it establishes only that the prompts induce distinct observable behavioral fidelity on fresh development probes. It does not establish that specialists improve answer quality or that a controller can select them prospectively.

If v0.2 fails with renewed fidelity saturation, stop trying to establish operator identity through prompt-only behavioral manipulation on this target and treat the six families as descriptive analysis labels rather than causally distinct promptable modules.

If v0.2 passes only for a subset, Stage 1 must be redesigned around that frozen subset; failed operators are not carried forward by convenience.

The current deployment architecture remains unchanged until later fresh controller validation.