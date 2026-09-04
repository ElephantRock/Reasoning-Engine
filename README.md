# Reasoning Engine

An experimental reasoning-control architecture for moving from observations to justified interventions while explicitly managing causal uncertainty, evidence, revision, and reasoning cost.

## Core protocol

For substantial non-trivial problems:

**Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer**

Compact mode:

**Problem → First Principle → Mechanism → Evidence → Solution**

Current adaptive candidate:

**Route → Reason → Verify → Act → Observe**

with `DIRECT`, `COMPACT`, and `FULL` reasoning modes selected according to the decision-relevant complexity of the task.

## Project status

The operating protocol is specified, but its value as an agent controller is still an empirical hypothesis.

The project therefore maintains two coupled systems:

1. **Reasoning engine** — the controller and its governing principles.
2. **Evaluation engine** — adversarial benchmarks intended to falsify or refine the controller.

Do not treat benchmark-framework compliance as evidence of improved reasoning by itself. The primary question is whether the controller improves correctness and decision quality enough to justify its additional reasoning cost.

## Repository structure

```text
.
├── docs/
│   ├── OPERATING_PROTOCOL.md
│   ├── FRAMEWORK_V0_2_CANDIDATE.md
│   ├── BENCHMARK_AUDIT_V0_2.md
│   └── ZAI_PROVIDER.md
├── benchmark/
│   ├── pilot.py
│   ├── run_zai.py
│   ├── zai_adapter.py
│   ├── pilot_cases.json
│   └── requirements.txt
└── .github/workflows/
    └── reasoning-benchmark-pilot.yml
```

## Benchmark pilot

The pilot compares the same target model under four conditions:

- `BASELINE` — no reasoning controller.
- `COMPACT` — compact causal/mechanistic controller.
- `FULL` — full eight-stage controller.
- `ADAPTIVE` — router selects DIRECT, COMPACT, or FULL before answering.

The six initial cases cover:

- correlation and selection bias;
- competing causal mechanisms;
- sequential contradictory evidence and revision;
- false first-principle claims;
- risk, reversibility, and second-order effects;
- trivial-task mode control.

Sequential cases are evaluated turn by turn so future evidence is structurally withheld from earlier judgments. Evaluators are not told which experimental condition generated a response.

## Model provider: Z.AI

The canonical benchmark runtime uses Z.AI through its OpenAI-compatible Chat Completions protocol.

Default endpoint:

`https://api.z.ai/api/coding/paas/v4`

Default target and judge model:

`glm-5.1`

The base URL is workflow-configurable. This is intentional because Z.AI documents the Coding Plan endpoint for supported coding-tool scenarios and recommends the general API endpoint for other uses; if required, set the workflow base URL to `https://api.z.ai/api/paas/v4` without changing benchmark code.

See `docs/ZAI_PROVIDER.md` for the provider contract.

## Run on GitHub Actions

One-time setup:

1. Add an Actions repository secret named `ZAI_API_KEY`.
2. Open **Actions → Reasoning Benchmark Pilot → Run workflow**.
3. Keep or change:
   - target model (default `glm-5.1`);
   - evaluator model (default `glm-5.1`);
   - base URL (default `https://api.z.ai/api/coding/paas/v4`).
4. Download the generated result artifact after the workflow completes.

The workflow produces:

- `pilot_report.json`
- `pilot_runs.jsonl`
- `pilot_pairwise.jsonl`

API keys must never be committed to this repository.

## Local pilot

```bash
cd benchmark
python -m pip install -r requirements.txt
export ZAI_API_KEY=...
export ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
export ZAI_TARGET_MODEL=glm-5.1
export ZAI_JUDGE_MODEL=glm-5.1
python run_zai.py
```

The runner uses `chat.completions` and records Z.AI `prompt_tokens` and `completion_tokens` as benchmark input/output token usage. Blinded evaluator calls use JSON mode when available.

## Research discipline

The framework should be revised or rejected when evidence contradicts its claimed benefits.

The governing research loop is therefore the framework applied to itself:

**Observe benchmark failures → Diagnose → Derive → Hypothesize controller changes → Predict improvements → Test → Revise → Engineer**

The intended endpoint is not maximal reasoning. It is **maximum justified decision quality per unit of reasoning cost**.
