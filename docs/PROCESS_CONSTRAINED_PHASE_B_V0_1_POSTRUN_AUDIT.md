# Process-Constrained ARC Phase B v0.1 — Independent Post-Run Audit

Status: **execution complete; frozen numerical result reproduced; intended process-effect interpretation not accepted because the post-run audit found measurement/interface validity defects. No Phase-C design or paid run is authorized from v0.1.**

This document records the independent raw-artifact audit required by `PROCESS_CONSTRAINED_PHASE_B_V0_1_AUTHORIZATION.md`. It does not rewrite the preregistered rules or the result emitted by the frozen runner. It distinguishes the **nominal frozen-rule result** from the **scientific-validity review** performed before interpretation.

## 1. Execution provenance and artifact integrity

Authorized workflow run:

- GitHub Actions run ID: `34981526860`;
- authorized run attempt: `1`;
- target: `glm-5.1`;
- provider base URL: `https://api.z.ai/api/coding/paas/v4`;
- temperature: `0`;
- completion-token ceiling: `16384`;
- frozen scientific source commit: `febffa5c9bd277136a78bfaa02aa365ee04a11b1`;
- Python: `3.12.14`;
- OpenAI Python package: `3.13.0`.

The workflow completed successfully after accepting the one-shot gate. Its zero-cost preflight ran 34 tests successfully before the first paid target call.

Uploaded artifact:

- artifact ID: `10407162264`;
- artifact name: `process-constrained-phase-b-v01-results`;
- uploaded ZIP SHA-256: `b3705dcf13e8e1b4c8adc768667297b91a43274ee0e68eeaba82be8273fea5d2`;
- artifact files: `manifest.json`, `runs.jsonl`, `summary.json`, `runtime_environment.txt`.

The artifact manifest declares 96 complete case-condition records. Independent hashing reproduced:

- `runs.jsonl`: `9a6861e99ba587b14faf68c17c04916ac76136d68872b94872e4d53638f7bb74`;
- `summary.json`: `500006fbe0eacca955d19f530fcfad5fb9407f4f60653b2b45c25e717a62a11f`.

The raw record audit found exactly 24 cases × 4 conditions, no duplicate `(case_id, condition)` keys, six cases per family, and no completion-ceiling (`finish_reason=length`) interruption. There were three schema-format repair calls; all completed with `finish_reason=stop`. A scan of model-facing request payloads found no internal `PCB-*` case ID, experimental condition label, or internal family label. Execution-order reconstruction also reproduced the frozen balancing rule: globally every condition occupied each execution position six times, and within every family each condition occupied each position once or twice.

## 2. Nominal frozen-rule result

The frozen runner emitted:

`STOP_PROCESS_CONSTRAINED_SELECTOR_PATH`

with zero Phase-C-eligible families.

| Family | SPECIALIST | MATCHED_SCAFFOLD | FULL | CONTROL | Specialist − matched | Strict wins | Valid specialist |
|---|---:|---:|---:|---:|---:|---:|---:|
| `DEDUCTIVE_CONSTRAINT` | 0.3333 | 0.5000 | 0.3333 | 0.5000 | -0.1667 | 0/6 | 5/6 |
| `ABDUCTIVE_DIAGNOSTIC` | 0.1667 | 0.3000 | 0.7333 | 0.4667 | -0.1333 | 0/6 | 4/6 |
| `SEARCH_PLANNING` | 0.8333 | 1.0000 | 1.0000 | 1.0000 | -0.1667 | 0/6 | 5/6 |
| `DECISION_THEORETIC` | 0.0000 | 1.0000 | 1.0000 | 1.0000 | -1.0000 | 0/6 | 0/6 |

Across all 24 cases, descriptive condition means were `SPECIALIST=0.3333`, `MATCHED_SCAFFOLD=0.7000`, `FULL=0.7667`, and `CONTROL=0.7417`. The specialist had 10 execution failures out of 24 (41.67%); the other three conditions had none.

These values and the frozen family gates were independently recomputed from `runs.jsonl` rather than taken on trust from `summary.json`.

## 3. Validity finding A — specialist action legality was not fully observable

The largest defect is a mismatch between what the runtime enforced and what the specialist could explicitly observe in its control interface.

The frozen runtime contains state-specific action-tag legality. Some states require a particular action class, while other states permit **no environment action**. A request that violates those rules terminates the case immediately with no semantic retry. The matched scaffold, by design, permits any action from the common action universe at its generic states subject to environment prerequisites and the same action budget.

The specialist request exposed:

- current protocol state;
- legal next protocol state(s);
- the complete common action catalog;
- a public payload contract for the legal next state;
- an instruction saying that the runtime enforces protocol-specific timing.

However, it did **not** expose a machine-readable allowed-action set or an explicit `environment_action must be null` requirement for states in which the runtime prohibited action. Required-action states often said to use a TEST/EVIDENCE/CHECKPOINT/COMMIT action; prohibited-action states generally specified only the payload semantics.

This mattered materially. Of the ten specialist execution failures:

- six `DECISION_THEORETIC` cases failed on their first transition, `ACTIONS -> OUTCOMES`, because the model requested `run_pilot`, `buy_annual`, or `decline` while the runtime silently required no environment action at `OUTCOMES`;
- two `ABDUCTIVE_DIAGNOSTIC` cases failed at `PREDICTIONS` for requesting evidence while the runtime required no action there;
- one `DEDUCTIVE_CONSTRAINT` case failed at `DERIVATION` for requesting a candidate test while the runtime required no action there;
- one `SEARCH_PLANNING` case failed at `CHECKPOINT` by using an `EXECUTE` action where the visible contract explicitly required the CHECKPOINT action.

Thus **9/10 specialist failures were caused by no-action timing constraints that were enforced but not explicitly surfaced as allowed/forbidden action metadata**. The remaining planning failure was a genuine violation of an explicitly stated action-class contract.

The process intervention is allowed to constrain when actions are legal; that is part of the research design. The validity problem is narrower: the target must be given the operational contract it is being scored against. Otherwise the endpoint mixes the value of the reasoning process with the model's ability to infer an undocumented negative API constraint from state names and omitted guidance.

Because valid-specialist-execution rate is itself a frozen family gate, this interface defect directly affects eligibility and is not merely a secondary usability observation. The `DECISION_THEORETIC` family is the clearest example: all six specialist scores became zero before the protocol sequence could be executed.

## 4. Validity finding B — deductive terminal quantity is semantically ambiguous

The deductive environment defines:

`minimum_restart = isolation + middle_work + restart_duration`

and awards full credit only when `commit_restart(restart_minute=minimum_restart)` is used. In other words, the scorer treats `restart_minute` as the minute by which restart is complete/service is restored.

The task text, however, says that restart **takes** a stated number of minutes, that restart **can begin** only after calibration and verification are complete, and asks for the earliest defensible **restart commitment**. The public action is named `commit_restart` with argument `restart_minute`. A natural reading is therefore the minute at which restart begins, not the minute at which it finishes.

The raw outputs show that this ambiguity was behaviorally active rather than hypothetical. Among the 23 deductive executions that reached a commitment, every committed value was exactly one of two quantities:

- 13 committed the earliest restart **start** minute (`isolation + middle_work`);
- 10 committed the environment's expected restart **completion/restoration** minute (`isolation + middle_work + restart_duration`).

For `PCB-DC01`, all four conditions committed minute 60 and explicitly reasoned that restart would then complete at minute 70; the environment expected 70 and scored every condition zero. Similar start-versus-completion splits occurred elsewhere in the family.

The preflight correctly checked that `env.minimum_restart` receives full score and that candidate testing does not reveal the optimum, but it did not test that the natural-language task and action schema unambiguously denote the scorer's terminal quantity.

Therefore the deductive scores should not be used as clean evidence about deductive-process value without repairing the endpoint language.

## 5. Scientific classification

The v0.1 run is **technically valid and reproducible**: the authorized frozen code ran once, completed all 96 cells, produced a hash-consistent artifact, respected execution balancing, and reproduced its own preregistered calculation.

The v0.1 run is **not accepted as a clean test of the intended reasoning-process effect**. The audit found two post-freeze measurement defects that are upstream of the scientific interpretation:

1. specialist outcome scores are confounded by incompletely exposed runtime action-legality rules, with a large observed effect on execution failure;
2. the deductive family contains an active start-versus-completion ambiguity in the terminal quantity being scored.

Accordingly, the nominal frozen-rule decision `STOP_PROCESS_CONSTRAINED_SELECTOR_PATH` is preserved as the exact v0.1 runner output, but it is **not promoted to the program-level scientific conclusion that specialist reasoning protocols lack value**.

A narrower result remains useful: this implementation demonstrates that externally enforced reasoning controllers can become brittle when the action contract is stricter than the interface makes explicit. That is an engineering/control-plane finding, not evidence against the underlying reasoning operators themselves.

The existing deployment decision is unchanged: `DIRECT` for genuinely trivial/deterministic tasks and frozen `FULL` for non-trivial reasoning tasks. No adaptive selector is authorized.

## 6. Required correction before another paid process-effect study

A corrected Phase B must be a new frozen version; the consumed v0.1 one-shot workflow must never be rerun.

Before any v0.2 target call:

1. **Expose action legality completely.** Every specialist turn must include an explicit machine-readable action contract for each legal next state, including the exact allowed environment action names/tags and whether an action is required, optional, or forbidden. A no-action state must explicitly say that `environment_action` must be `null`.
2. **Add interface-completeness tests.** Static tests must prove that every runtime action-tag restriction is reflected in the model-facing specialist request, including negative/no-action restrictions.
3. **Remove deductive endpoint ambiguity.** Rename or redefine the action/quantity to an unambiguous observable such as `service_restored_minute`, or explicitly define `restart_minute` as completion/restoration time. Precedence relative to isolation must be explicit in every task variant. Add adversarial wording tests for start-versus-completion confusion.
4. **Use a fresh frozen 24-case development suite for the corrected study.** The v0.1 cases and failure modes are now exposed and have influenced the redesign; fresh cases prevent result-contingent task adaptation from being mistaken for validation.
5. **Run the full four-condition factorial again.** Do not rerun only failed specialist cells and do not reuse the v0.1 matched/FULL/CONTROL responses as the primary comparison. A corrected interface changes the intervention and must be evaluated under a newly balanced execution schedule.
6. **Freeze and review before execution.** The corrected scientific source, suite, runtime, target-visible interface, scoring, execution order, provider adapter, dependency lock, and a new one-shot workflow must receive a separate static review and authorization.

No paid v0.2 run is authorized by this audit.

## 7. Program state after audit

The next research sequence is:

`v0.1 artifact preserved -> post-run validity failure documented -> correct measurement interface -> freeze fresh Phase B v0.2 -> static/Codex review -> separate execution authorization -> one paid v0.2 run -> independent raw-artifact audit`

Phase C remains closed unless a scientifically valid corrected Phase B meets its prospectively frozen gate.