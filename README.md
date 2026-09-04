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

The operating protocol is specified, but its value as an agent controller remains an empirical hypothesis.

Pilot 001 successfully executed end-to-end against Z.AI `glm-5.1`. It produced encouraging directional signals—especially for Compact reasoning—but also exposed evaluator ceiling saturation and an Adaptive routing error. Measurement v0.3 therefore hardens the evaluator before the project scales to a larger benchmark.

See:

- `docs/PILOT_001_RESULTS.md` — exact Pilot 001 provenance and results;
- `docs/MEASUREMENT_V0_3.md` — evaluator changes motivated by those results.

The project maintains two coupled systems:

1. **Reasoning engine** — the controller and its governing principles.
2. **Evaluation engine** — adversarial benchmarks intended to falsify or refine the controller.

Do not treat protocol compliance as evidence of improved reasoning by itself. The primary question is whether the controller improves blinded decision quality enough to justify its reasoning cost.

## Repository structure

```text
.
├── docs/
│   ├── OPERATING_PROTOCOL.md
│   ├── FRAMEWORK_V0_2_CANDIDATE.md
│   ├── BENCHMARK_AUDIT_V0_2.md
│   ├── ZAI_PROVIDER.md
│   ├── PILOT_001_RESULTS.md
│   └── MEASUREMENT_V0_3.md
├── benchmark/
│   ├── pilot.py
│   ├── run_zai.py
│   ├── run_v03.py
│   ├── zai_adapter.py
│   ├── pilot_cases.json
│   ├── stress_cases_v03.json
│   └── requirements.txt
└── .github/workflows/
    ├── reasoning-benchmark-pilot.yml
    └── reasoning-benchmark-v03.yml
```

## Experimental conditions

The same target model is compared under four conditions:

- `BASELINE` — no reasoning controller;
- `COMPACT` — Problem → First Principle → Mechanism → Evidence → Solution;
- `FULL` — Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer;
- `ADAPTIVE` — a router selects DIRECT, COMPACT, or FULL before answering.

## Measurement v0.3

Pilot 001's 0–4 scalar quality scores were nearly saturated, so v0.3 changes the measurement hierarchy:

1. **Primary:** blinded pairwise score against BASELINE (win=1, tie=0.5, loss=0).
2. **Secondary:** stricter anchored 0–4 scalar scores.
3. **Adaptive routing:** deterministic comparison of selected mode against case gold mode(s).
4. **Uncertainty:** case-clustered bootstrap confidence intervals when stochastic replicates are used.
5. **Cost:** token and latency accounting remains explicit.

Six additional stress cases test aggregation reversal, measurement-generation changes, material vs irrelevant uncertainty, adversarial causal framing, and intervention-as-experiment reasoning.

The v0.3 workflow supports `stress`, `pilot`, and `combined` suites and an arbitrary positive number of stochastic replicates.

## Model provider: Z.AI

The canonical target runtime uses Z.AI through its OpenAI-compatible Chat Completions protocol.

Default target endpoint:

`https://api.z.ai/api/coding/paas/v4`

Default model:

`glm-5.1`

The evaluator can use a different model, API key, and base URL. Configure optional `ZAI_JUDGE_API_KEY` for a separate judge credential; if absent it falls back to `ZAI_API_KEY`.

See `docs/ZAI_PROVIDER.md` for provider details.

## Run Measurement v0.3 on GitHub Actions

One-time minimum setup:

1. Add repository Actions secret `ZAI_API_KEY`.
2. Optionally add `ZAI_JUDGE_API_KEY` for an independent evaluator credential.
3. Open **Actions → Reasoning Benchmark Measurement v0.3 → Run workflow**.
4. Start with:
   - suite: `stress`;
   - replicates: `1`;
   - target model: `glm-5.1`;
   - judge model: `glm-5.1` unless another suitable judge is available.
5. Inspect the generated artifact before increasing benchmark size or replicate count.

The workflow writes checkpointed artifacts under `benchmark/results_v03/`:

- `v03_runs.jsonl`
- `v03_pairwise.jsonl`
- `v03_report.json` when the full run completes

API keys must never be committed to the repository.

## Local Measurement v0.3

```bash
cd benchmark
python -m pip install -r requirements.txt
export ZAI_API_KEY=...
export ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
export ZAI_TARGET_MODEL=glm-5.1
export ZAI_JUDGE_MODEL=glm-5.1
export BENCHMARK_SUITE=stress
export BENCHMARK_REPLICATES=1
python run_v03.py
```

For a separate evaluator, additionally set `ZAI_JUDGE_API_KEY` and optionally `ZAI_JUDGE_BASE_URL`.

## Research discipline

The framework should be revised or rejected when evidence contradicts its claimed benefits.

The governing research loop is therefore the framework applied to itself:

**Observe benchmark failures → Diagnose → Derive → Hypothesize controller changes → Predict improvements → Test → Revise → Engineer**

The intended endpoint is not maximal reasoning. It is **maximum justified decision quality per unit of reasoning cost**.
