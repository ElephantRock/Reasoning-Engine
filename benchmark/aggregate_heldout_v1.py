#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Callable

# Aggregation uses v0.5's already-tested case-clustered pairwise implementation.
os.environ.setdefault("OPENAI_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("ZAI_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("BENCHMARK_SUITE", "combined")
import run_heldout_v1 as hv1  # noqa: E402

v05 = hv1.v05
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results_heldout_v1"

PRIMARY_MIN_SCORE = 0.60
PRIMARY_CI_LOW_MIN_EXCLUSIVE = 0.50
SPECIFICITY_MIN_SCORE = 0.55
STRATUM_HARM_FLOOR = 0.45
EXPECTED_RUNS = 36 * 3 * 4
EXPECTED_VOTES = 36 * 3 * 3 * 3


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_all(prefix: str) -> list[dict[str, Any]]:
    paths = sorted(RESULTS.glob(f"{prefix}_shard_*.jsonl"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six {prefix} shard files, found {len(paths)}")
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(read_jsonl(path))
    return rows


def pair_result(votes: list[dict[str, Any]], spec: dict[str, str]) -> dict[str, Any]:
    result = v05.aggregate_pair(votes, spec)
    case_scores = result.get("case_scores", {})
    result["case_level_wins"] = sum(score > 0.5 for score in case_scores.values())
    result["case_level_ties"] = sum(score == 0.5 for score in case_scores.values())
    result["case_level_losses"] = sum(score < 0.5 for score in case_scores.values())
    result["n_cases"] = len(case_scores)
    return result


def filtered_pair(
    votes: list[dict[str, Any]],
    spec: dict[str, str],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any] | None:
    subset = [v for v in votes if v["pair_id"] == spec["pair_id"] and predicate(v)]
    return pair_result(subset, spec) if subset else None


def group_breakdown(votes: list[dict[str, Any]], spec: dict[str, str], field: str) -> dict[str, Any]:
    values = sorted({str(v[field]) for v in votes if v["pair_id"] == spec["pair_id"]})
    return {
        value: filtered_pair(votes, spec, lambda row, value=value: str(row[field]) == value)
        for value in values
    }


def binary_breakdown(votes: list[dict[str, Any]], spec: dict[str, str], field: str) -> dict[str, Any]:
    return {
        "true": filtered_pair(votes, spec, lambda row: bool(row[field])),
        "false": filtered_pair(votes, spec, lambda row: not bool(row[field])),
    }


def usage_diagnostics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for condition in hv1.CONDITIONS:
        subset = [r for r in runs if r["condition"] == condition]
        out[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }
    return out


def validate_completeness(runs: list[dict[str, Any]], votes: list[dict[str, Any]]) -> None:
    if len(runs) != EXPECTED_RUNS:
        raise RuntimeError(f"expected {EXPECTED_RUNS} target runs, found {len(runs)}")
    if len(votes) != EXPECTED_VOTES:
        raise RuntimeError(f"expected {EXPECTED_VOTES} judge votes, found {len(votes)}")

    run_keys = Counter((r["case_id"], r["condition"], r["replicate"]) for r in runs)
    if len(run_keys) != EXPECTED_RUNS or set(run_keys.values()) != {1}:
        raise RuntimeError("target run keys are missing or duplicated")

    vote_keys = Counter((v["case_id"], v["pair_id"], v["replicate"], v["vote_index"]) for v in votes)
    if len(vote_keys) != EXPECTED_VOTES or set(vote_keys.values()) != {1}:
        raise RuntimeError("judge vote keys are missing or duplicated")

    expected_cases = {c["case_id"] for c in hv1.CASES}
    if {r["case_id"] for r in runs} != expected_cases or {v["case_id"] for v in votes} != expected_cases:
        raise RuntimeError("case coverage does not match the frozen 36-case suite")


def validate_meta() -> dict[str, Any]:
    paths = sorted(RESULTS.glob("heldout_v1_meta_shard_*.json"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six shard metadata files, found {len(paths)}")
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if {row["shard_index"] for row in rows} != set(range(6)):
        raise RuntimeError("invalid shard metadata indices")

    invariant_fields = ["candidate", "target", "judge", "generation_replicates", "judge_votes_per_pair", "pair_specs"]
    reference = rows[0]
    for row in rows[1:]:
        for field in invariant_fields:
            if row[field] != reference[field]:
                raise RuntimeError(f"shard metadata disagreement for {field}")
    if len({case for row in rows for case in row["case_ids"]}) != 36:
        raise RuntimeError("shard metadata does not cover 36 unique cases")
    return {field: reference[field] for field in invariant_fields}


def main() -> None:
    runs = load_all("heldout_v1_runs")
    votes = load_all("heldout_v1_votes")
    validate_completeness(runs, votes)
    meta = validate_meta()

    results: dict[str, Any] = {}
    for spec in hv1.PAIR_SPECS:
        relevant = [v for v in votes if v["pair_id"] == spec["pair_id"]]
        overall = pair_result(relevant, spec)
        results[spec["pair_id"]] = {
            "overall": overall,
            "by_task_stratum": group_breakdown(votes, spec, "routing_stratum"),
            "by_domain": group_breakdown(votes, spec, "domain"),
            "by_sequential": binary_breakdown(votes, spec, "sequential"),
            "by_distractors": binary_breakdown(votes, spec, "has_distractors"),
            "by_requires_action": binary_breakdown(votes, spec, "requires_action"),
        }

    primary = results["CANDIDATE_POLICY_vs_CONTROL"]["overall"]
    specificity = results["CANDIDATE_POLICY_vs_ATTENTION"]["overall"]
    stratum_primary = results["CANDIDATE_POLICY_vs_CONTROL"]["by_task_stratum"]
    harmful_strata = {
        name: row["score"]
        for name, row in stratum_primary.items()
        if row is not None and row["n_cases"] >= 6 and row["score"] < STRATUM_HARM_FLOOR
    }

    primary_statistical_pass = (
        primary["score"] >= PRIMARY_MIN_SCORE
        and primary["ci95_low"] > PRIMARY_CI_LOW_MIN_EXCLUSIVE
    )
    robustness_pass = not harmful_strata
    validation_pass = primary_statistical_pass and robustness_pass
    specificity_support = specificity["score"] >= SPECIFICITY_MIN_SCORE

    report = {
        "measurement_version": "heldout-validation-v1",
        "experiment_role": "oracle-stratified held-out module validation; not autonomous routing validation",
        "suite": "heldout_cases_v1.json",
        "n_cases": 36,
        "generation_replicates": 3,
        "judge_votes_per_pair": 3,
        "candidate": meta["candidate"],
        "target": meta["target"],
        "judge": meta["judge"],
        "primary_endpoint": "CANDIDATE_POLICY vs CONTROL mean case score",
        "primary_success_rule": {
            "point_estimate_min": PRIMARY_MIN_SCORE,
            "ci95_low_exclusive_min": PRIMARY_CI_LOW_MIN_EXCLUSIVE,
            "observed_score": primary["score"],
            "observed_ci95_low": primary["ci95_low"],
            "observed_ci95_high": primary["ci95_high"],
            "statistical_pass": primary_statistical_pass,
        },
        "robustness_rule": {
            "task_stratum_harm_floor": STRATUM_HARM_FLOOR,
            "harmful_strata": harmful_strata,
            "pass": robustness_pass,
        },
        "specificity_support_rule": {
            "candidate_vs_attention_min": SPECIFICITY_MIN_SCORE,
            "observed_score": specificity["score"],
            "directionally_supported": specificity_support,
        },
        "validation_pass": validation_pass,
        "quality_results": results,
        "cost_diagnostics": usage_diagnostics(runs),
        "completeness": {
            "target_runs": len(runs),
            "judge_votes": len(votes),
            "complete": True,
        },
        "interpretation_boundary": [
            "A positive result supports the frozen modules when applied to preregistered task strata.",
            "This experiment does not validate autonomous routing because task strata are author-assigned before generation.",
            "A failed validation remains a failed validation; no post-exposure prompt, routing, threshold, case, or evaluator retuning is permitted within v1.",
            "Cost is descriptive and does not enter the validation endpoint.",
        ],
    }
    output = RESULTS / "heldout_v1_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
