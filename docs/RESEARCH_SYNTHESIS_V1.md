# Reasoning Engine — Research Synthesis v1

Status: **current whole-program evidence freeze after Selective Routing v4 stop rule**.

This document separates what the program has established from what remains unresolved. It is intended to be the claim boundary for future manuscripts, talks, and follow-up experiments.

## Core finding

The strongest supported claim is framework-level, not component-level and not routing-level:

> On GLM-5.1, the frozen FULL structured-reasoning prompt repeatedly improves blinded pairwise reasoning quality relative to an uncontrolled baseline under GLM-5.3-Flash judging on the same Z.AI provider. The result is cross-model, same-family/provider evidence rather than independent-family/provider validation.

The frozen FULL protocol is:

`Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer`

with direct answering still allowed for genuinely trivial or established tasks.

## Fresh-suite FULL vs CONTROL evidence

FULL vs CONTROL was measured on four fresh suites after prompt freeze:

| Suite | Cases | FULL vs CONTROL | 95% case-clustered CI | Notes |
|---|---:|---:|---:|---|
| Held-Out Framework Validation v1 | 36 | **0.6898** | **0.6096–0.7685** | preregistered primary endpoint passed |
| Selective Routing v1 suite | 48 | **0.6771** | **0.6250–0.7292** | fresh routing-validation suite; FULL replicated |
| Selective Routing v2 suite | 48 | **0.6875** | **0.6273–0.7477** | framework-replication gate passed |
| Selective Routing v3 suite | 48 | **0.6539** | **0.5891–0.7199** | framework-replication gate passed |

Across these 180 fresh cases, the case-count-weighted descriptive FULL-vs-CONTROL score is approximately **0.6762**.

This pooled value is **descriptive only**. It was not a preregistered meta-analytic endpoint, the suites were produced sequentially within one research program, and all use the same target model family/provider and judge family/provider. No pooled inferential CI should be attached to it as if the four suites were independent studies.

The important pattern is consistency: every fresh suite favored FULL, and every suite-level confidence interval was above 0.50.

## Held-out architecture evidence

The 36-case held-out validation is the cleanest primary framework test.

- FULL vs CONTROL: **0.6898**, CI **0.6096–0.7685**; primary rule passed.
- COMPACT vs CONTROL: **0.5864**, CI **0.5077–0.6667**; preregistered secondary success rule failed because the point estimate was below 0.60.
- FULL vs COMPACT: **0.5957**, CI **0.5417–0.6543**; preregistered directional rule favored FULL.

The evidence therefore supports the frozen FULL prompt over the uncontrolled baseline more strongly than it supports the compact scaffold as a replacement.

## Heterogeneity

The benefit is not universal.

In the original held-out suite, FULL was strongest on:

- ENGINEER: **0.9012**;
- TEST: **0.7901**;
- BOTH: **0.6296**;
- cases requiring action: **0.7375**.

Near-neutral groups included:

- NONE: **0.4861**;
- no-action cases: **0.4921**.

This heterogeneity motivated routing research, but it does not imply that a deployable router can reliably identify the marginal-value cases from the input alone.

## Component-level evidence

The component-identification program produced useful methodological lessons but did not establish a stable causal decomposition of the eight-stage protocol.

Key findings:

- leave-one-instruction-out ablation did not reliably remove the corresponding capability;
- Diagnose and Revise were frequently near behavioral ceiling even without explicit stage instructions;
- Engineering showed the strongest development quality signal in early manipulation studies;
- coarse behavior scores saturated, motivating finer behavioral-fidelity measurement;
- the frozen post-v0.11 selection procedure did not yield an explicit stage module strong enough to carry forward as a validated selective intervention.

Therefore the framework-level result should **not** be represented as proof that each named stage independently contributes causal value.

The correct distinction remains:

`reasoning capability ≠ reasoning instruction`.

## Routing program result

Selective Routing v1–v4 did not produce a validated router.

### v1

The binary router used FULL on 50% of cases and ROUTED beat CONTROL, but it failed the original frozen preservation endpoint against ALWAYS-FULL. v1 remains a formal failure.

### v2

v2 corrected the preservation estimand prospectively on a new fresh suite while keeping the router unchanged.

- FULL vs CONTROL: **0.6875**;
- ROUTED vs CONTROL: **0.6840**;
- paired ROUTED-minus-FULL decrement: **-0.0035**, CI **-0.0255 to 0.0127**;
- retained FULL gain: **98.15%**;
- FULL invocation: **70.83%**.

Quality gates passed, but the frozen selectivity cap of 65% failed. v2 is a formal failure.

### v3

v3 changed the semantic routing hypothesis to suppress causal-looking tasks believed not to need FULL.

- FULL vs CONTROL: **0.6539**;
- ROUTED vs CONTROL: **0.4988**;
- paired decrement: **-0.1551**;
- FULL invocation: **10.42%**.

The key hypothesis was falsified: `CAUSAL_TRAP` cases were routed CONTROL 12/12, yet FULL scored **0.8102** on that stratum. v3 is a formal failure.

### v4 development stop

v4 abandoned hand-authored semantic routing and used the 144 already-exposed v1–v3 cases as a development corpus for text-only empirical marginal-value prediction.

No candidate passed all frozen leave-one-suite-out and leave-one-domain-out development gates.

The closest candidate, `NB_DIRECT`, achieved:

- LOSO routed score **0.6393**;
- LOSO paired decrement **-0.0336**;
- LOSO FULL use **56.25%**;
- LODO routed score **0.6493**;
- LODO paired decrement **-0.0235**;
- LODO FULL use **58.33%**.

It missed the frozen LOSO preservation gate and showed unstable suite/domain behavior. The stop rule therefore triggered. No fresh v4 validation suite was authored.

## Current architecture decision

The current recommended policy is:

`DIRECT for genuinely trivial/deterministic tasks; otherwise FULL`.

This should **not** be described as a validated selective router. It is a conservative deployment interpretation of the evidence:

- FULL has replicated across fresh suites;
- current routing signals are not reliable enough to justify skipping FULL on non-trivial cases while preserving quality under the program's conservative gates.

## Claims supported now

The program can support the following statements:

1. A frozen structured-reasoning prompt improved GLM-5.1 reasoning quality over an uncontrolled baseline on a preregistered 36-case held-out suite under blinded GLM-5.3-Flash evaluation.
2. The FULL-vs-CONTROL advantage replicated descriptively and prospectively on three additional fresh 48-case routing suites.
3. The effect is heterogeneous and strongest in testing-, engineering-, and action-oriented problems.
4. Explicit instruction removal is not equivalent to capability removal; component-level causal attribution remains unresolved.
5. Several routing strategies failed preregistered or frozen quality/selectivity criteria, including a later empirical text-only development phase that triggered a stop rule.

## Claims not supported

Do not claim:

- independent-provider or independent-family validation;
- generalization to target models other than GLM-5.1;
- universal FULL benefit on every task;
- causal necessity of every named reasoning stage;
- a validated autonomous router;
- cost optimality;
- human-equivalent judgment validity;
- that the descriptive 180-case pooled score is an independent-study meta-analysis.

## Scientific next steps

The highest-value next work is no longer another routing prompt.

Priority order:

1. **Independent evaluation** — rejudge frozen outputs or run a fresh replication with a genuinely different model family/provider when available.
2. **Human-reviewed subset** — obtain blinded human judgments on a stratified sample, especially cases where FULL and CONTROL differ strongly.
3. **Cross-target replication** — repeat the frozen FULL-vs-CONTROL design on at least one materially different target model family/capability level.
4. **External benchmark transfer** — test the frozen protocol on tasks not authored inside this research program.
5. **Only after new information** — reopen routing if a materially stronger deployment-available signal or larger marginal-value corpus exists.

## Governing interpretation

The strongest present conclusion is not that every stage is necessary or that routing has been solved. It is narrower and more defensible:

> Structured, explicit reasoning control can improve model reasoning quality on difficult decision, testing, and engineering tasks; however, the value is heterogeneous, individual stage causality is difficult to identify, and reliable input-only prediction of when deep reasoning can be safely skipped remains unresolved.
