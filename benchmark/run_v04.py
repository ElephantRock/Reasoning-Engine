#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import run_v03 as v03

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "routing_holdout_v04.json").read_text(encoding="utf-8"))
v03.CASES = CASES

ROUTER_V04 = r'''You are a routing controller. Choose the LEAST expensive reasoning mode that is likely to preserve the best decision available from the current information.

The objective is not to classify task complexity. The objective is to estimate the MARGINAL DECISION VALUE of deeper reasoning.

Modes:
DIRECT — answer without a reasoning controller. Use when the decision is effectively invariant under the supplied uncertainty: deterministic calculation, strict dominance, an established mechanism with no material ambiguity, or additional analysis is very unlikely to change the action.

COMPACT — use Problem → First Principle → Mechanism → Evidence → Solution. Use when there is one or a small number of clear decision hinges, a hard constraint that is cheaply verifiable, or a cheap/reversible discriminating test can resolve the material uncertainty. Technical difficulty or high stakes alone do NOT require FULL if a focused test/verification dominates the next decision.

FULL — use Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer. Use when deeper reasoning can plausibly change the action because there are multiple materially plausible mechanisms, the measurement process itself may be misleading, evidence is sequential/contradictory, causal framing is adversarial, an irreversible/high-cost intervention depends on locating the right mechanism, or feedback/second-order effects materially change intervention quality.

Routing discipline:
1. Identify the actual decision or next action.
2. Identify the decision hinge: what unknown, mechanism, constraint, or contradiction could change that action?
3. Ask whether deeper reasoning would likely change the decision, not merely produce a richer explanation.
4. Prefer the shallowest mode that can resolve the hinge safely and correctly.
5. Escalate to FULL when multiple interacting uncertainties or mechanism errors could survive a focused Compact analysis and change the intervention.
6. Stop escalation when additional reasoning has low expected information/decision value.

Return JSON only:
{
  "mode":"DIRECT|COMPACT|FULL",
  "decision_hinge":"short statement",
  "deeper_reasoning_value":"LOW|MEDIUM|HIGH",
  "why_not_shallower":"short statement",
  "why_not_deeper":"short statement",
  "stop_condition":"short statement"
}'''


def parse_route(result: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    parsed = v03.parse_json(result["text"])
    mode = parsed.get("mode")
    if mode not in {"DIRECT", "COMPACT", "FULL"}:
        raise RuntimeError(f"invalid v0.4 router mode: {parsed}")
    rationale = json.dumps(
        {
            "decision_hinge": parsed.get("decision_hinge", ""),
            "deeper_reasoning_value": parsed.get("deeper_reasoning_value", ""),
            "why_not_shallower": parsed.get("why_not_shallower", ""),
            "why_not_deeper": parsed.get("why_not_deeper", ""),
            "stop_condition": parsed.get("stop_condition", ""),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return mode, rationale, result["usage"]


def route_v04(case: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    result = v03.target_call(
        ROUTER_V04,
        [{"role": "user", "content": case["turns"][0]["agent_input"]}],
        json_mode=True,
    )
    return parse_route(result)


v03.route = route_v04


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def adaptive_regret_analysis(runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}
    comparisons: list[dict[str, Any]] = []
    per_case: list[dict[str, Any]] = []

    for replicate in range(1, v03.REPLICATES + 1):
        for case in CASES:
            adaptive = index[(case["case_id"], "ADAPTIVE", replicate)]
            local = []
            for fixed in ["BASELINE", "COMPACT", "FULL"]:
                fixed_run = index[(case["case_id"], fixed, replicate)]
                cmp = v03.pairwise(case, fixed_run, adaptive)
                cmp["comparison"] = f"ADAPTIVE_vs_{fixed}"
                comparisons.append(cmp)
                local.append((fixed, fixed_run, cmp))

            fixed_wins = [fixed for fixed, _run, cmp in local if cmp["winner"] == fixed]
            quality_noninferior = not fixed_wins
            acceptable_fixed = [
                (fixed, fixed_run)
                for fixed, fixed_run, cmp in local
                if cmp["winner"] in {"ADAPTIVE", "TIE"}
            ]
            cheapest_nonbeating = None
            overhead_ratio = None
            if acceptable_fixed:
                cheapest_nonbeating = min(acceptable_fixed, key=lambda item: item[1]["usage"]["output_tokens"])
                denom = float(cheapest_nonbeating[1]["usage"]["output_tokens"] or 1)
                overhead_ratio = float(adaptive["usage"]["output_tokens"]) / denom

            per_case.append(
                {
                    "case_id": case["case_id"],
                    "replicate": replicate,
                    "selected_mode": adaptive.get("selected_mode"),
                    "legacy_expected_modes": adaptive.get("expected_modes"),
                    "legacy_gold_match": adaptive.get("route_correct"),
                    "quality_noninferior_to_all_fixed": quality_noninferior,
                    "fixed_modes_that_beat_adaptive": fixed_wins,
                    "cheapest_fixed_not_beating_adaptive": cheapest_nonbeating[0] if cheapest_nonbeating else None,
                    "adaptive_output_token_overhead_ratio": overhead_ratio,
                    "adaptive_output_tokens": adaptive["usage"]["output_tokens"],
                    "router_rationale": adaptive.get("router_rationale"),
                }
            )

    noninferior_rate = sum(x["quality_noninferior_to_all_fixed"] for x in per_case) / len(per_case)
    overheads = [x["adaptive_output_token_overhead_ratio"] for x in per_case if x["adaptive_output_token_overhead_ratio"] is not None]
    mode_counts: dict[str, int] = {}
    for x in per_case:
        mode_counts[x["selected_mode"]] = mode_counts.get(x["selected_mode"], 0) + 1

    summary = {
        "definition": "Routing quality is evaluated empirically: ADAPTIVE should not lose blinded pairwise comparisons to any fixed reasoning depth, and should avoid unnecessary token overhead when a cheaper fixed depth is non-inferior.",
        "n_case_replicates": len(per_case),
        "quality_noninferiority_rate_vs_all_fixed": noninferior_rate,
        "quality_regret_count": sum(not x["quality_noninferior_to_all_fixed"] for x in per_case),
        "mean_output_token_overhead_ratio_vs_cheapest_nonbeating_fixed": (sum(overheads) / len(overheads)) if overheads else None,
        "selected_mode_counts": mode_counts,
        "cases": per_case,
    }
    return comparisons, summary


def main() -> None:
    v03.main()

    source = ROOT / "results_v03"
    target = ROOT / "results_v04"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(exist_ok=True)

    runs = load_jsonl(source / "v03_runs.jsonl")
    baseline_pairs = load_jsonl(source / "v03_pairwise.jsonl")
    regret_pairs, routing = adaptive_regret_analysis(runs)

    write_jsonl(target / "v04_runs.jsonl", runs)
    write_jsonl(target / "v04_pairwise_vs_baseline.jsonl", baseline_pairs)
    write_jsonl(target / "v04_adaptive_vs_fixed.jsonl", regret_pairs)

    report = json.loads((source / "v03_report.json").read_text(encoding="utf-8"))
    report["measurement_version"] = "0.4-candidate"
    report["suite"] = "routing-holdout-v04"
    report["router"] = {
        "policy": "minimum reasoning depth by expected marginal decision value",
        "prompt_version": "routing-v0.4",
    }
    report["routing_evaluation"] = routing
    report["notes"] = [
        "This is a held-out routing experiment; the six RF-H cases were not used in Measurement v0.3.",
        "Legacy expected_mode agreement is diagnostic only and is not the primary routing metric.",
        "Primary routing criterion: ADAPTIVE should be quality-noninferior to BASELINE, COMPACT, and FULL in blinded pairwise comparisons while minimizing avoidable reasoning cost.",
        "The v0.4 router was derived from Measurement v0.3 case-level failures, so do not evaluate it on the RF-S stress cases as if they were held out.",
    ] + report.get("notes", [])
    (target / "v04_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"measurement_version": report["measurement_version"], "routing_evaluation": routing}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
