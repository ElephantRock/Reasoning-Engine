#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Callable

os.environ.setdefault("OPENAI_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("ZAI_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("ZAI_JUDGE_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("BENCHMARK_SUITE", "combined")
import run_framework_validation_v1 as fv1  # noqa: E402

v05 = fv1.v05
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results_framework_validation_v1"

PRIMARY_MIN_SCORE = 0.60
PRIMARY_CI_LOW_MIN_EXCLUSIVE = 0.50
SECONDARY_COMPACT_MIN_SCORE = 0.60
SECONDARY_COMPACT_CI_LOW_MIN_EXCLUSIVE = 0.50
STRATUM_HARM_FLOOR = 0.45
ARCH_FULL_DIRECTION = 0.55
ARCH_COMPACT_DIRECTION = 0.45
EXPECTED_RUNS = 36 * 3 * 3
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
    for condition in fv1.CONDITIONS:
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

    expected_cases = {c["case_id"] for c in fv1.CASES}
    if len(expected_cases) != 36:
        raise RuntimeError("frozen held-out suite must contain 36 unique case IDs")
    if {r["case_id"] for r in runs} != expected_cases or {v["case_id"] for v in votes} != expected_cases:
        raise RuntimeError("case coverage does not match the frozen 36-case suite")


def _judge_identity(meta: dict[str, Any]) -> dict[str, Any]:
    judge = dict(meta["judge"])
    judge.pop("connectivity_probe_usage", None)
    return judge


def validate_meta() -> dict[str, Any]:
    paths = sorted(RESULTS.glob("framework_v1_meta_shard_*.json"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six framework metadata files, found {len(paths)}")
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if {row["shard_index"] for row in rows} != set(range(6)):
        raise RuntimeError("invalid shard metadata indices")
    if len({case for row in rows for case in row["case_ids"]}) != 36:
        raise RuntimeError("shard metadata does not cover 36 unique cases")

    ref = rows[0]
    invariant_fields = [
        "measurement_version",
        "experiment_role",
        "suite",
        "suite_freeze_commit",
        "suite_git_blob_sha",
        "generation_replicates",
        "judge_votes_per_pair",
        "conditions",
        "prompt_sha256",
        "target",
        "pair_specs",
    ]
    for row in rows[1:]:
        for field in invariant_fields:
            if row[field] != ref[field]:
                raise RuntimeError(f"shard metadata disagreement for {field}")
        if _judge_identity(row) != _judge_identity(ref):
            raise RuntimeError("shard metadata disagreement for judge identity")

    return {
        **{field: ref[field] for field in invariant_fields},
        "judge": _judge_identity(ref),
    }


def architecture_direction(score: float) -> str:
    if score > ARCH_FULL_DIRECTION:
        return "FULL"
    if score < ARCH_COMPACT_DIRECTION:
        return "COMPACT"
    return "NO_MATERIAL_DIRECTIONAL_SEPARATION"


def main() -> None:
    runs = load_all("framework_v1_runs")
    votes = load_all("framework_v1_votes")
    validate_completeness(runs, votes)
    meta = validate_meta()

    results: dict[str, Any] = {}
    for spec in fv1.PAIR_SPECS:
        relevant = [v for v in votes if v["pair_id"] == spec["pair_id"]]
        results[spec["pair_id"]] = {
            "overall": pair_result(relevant, spec),
            "by_task_stratum": group_breakdown(votes, spec, "routing_stratum"),
            "by_domain": group_breakdown(votes, spec, "domain"),
            "by_sequential": binary_breakdown(votes, spec, "sequential"),
            "by_distractors": binary_breakdown(votes, spec, "has_distractors"),
            "by_requires_action": binary_breakdown(votes, spec, "requires_action"),
        }

    primary = results["FULL_vs_CONTROL"]["overall"]
    compact = results["COMPACT_vs_CONTROL"]["overall"]
    depth = results["FULL_vs_COMPACT"]["overall"]

    harmful_strata = {
        name: row["score"]
        for name, row in results["FULL_vs_CONTROL"]["by_task_stratum"].items()
        if row is not None and row["n_cases"] >= 6 and row["score"] < STRATUM_HARM_FLOOR
    }

    primary_statistical_pass = (
        primary["score"] >= PRIMARY_MIN_SCORE
        and primary["ci95_low"] > PRIMARY_CI_LOW_MIN_EXCLUSIVE
    )
    robustness_pass = not harmful_strata
    validation_pass = primary_statistical_pass and robustness_pass

    compact_pass = (
        compact["score"] >= SECONDARY_COMPACT_MIN_SCORE
        and compact["ci95_low"] > SECONDARY_COMPACT_CI_LOW_MIN_EXCLUSIVE
    )

    report = {
        "measurement_version": "heldout-framework-validation-v1",
        "experiment_role": "framework-level held-out validation; no routing",
        "suite": meta["suite"],
        "suite_freeze_commit": meta["suite_freeze_commit"],
        "suite_git_blob_sha": meta["suite_git_blob_sha"],
        "n_cases": 36,
        "generation_replicates": 3,
        "judge_votes_per_pair": 3,
        "conditions": meta["conditions"],
        "prompt_sha256": meta["prompt_sha256"],
        "target": meta["target"],
        "judge": meta["judge"],
        "primary_endpoint": "FULL vs CONTROL mean case score",
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
        "validation_pass": validation_pass,
        "secondary_compact_rule": {
            "point_estimate_min": SECONDARY_COMPACT_MIN_SCORE,
            "ci95_low_exclusive_min": SECONDARY_COMPACT_CI_LOW_MIN_EXCLUSIVE,
            "observed_score": compact["score"],
            "observed_ci95_low": compact["ci95_low"],
            "observed_ci95_high": compact["ci95_high"],
            "pass": compact_pass,
        },
        "architecture_depth": {
            "full_vs_compact_score": depth["score"],
            "ci95_low": depth["ci95_low"],
            "ci95_high": depth["ci95_high"],
            "full_direction_threshold_exclusive": ARCH_FULL_DIRECTION,
            "compact_direction_threshold_exclusive": ARCH_COMPACT_DIRECTION,
            "direction": architecture_direction(depth["score"]),
            "formal_equivalence_test": False,
        },
        "quality_results": results,
        "cost_diagnostics": usage_diagnostics(runs),
        "completeness": {
            "target_runs": len(runs),
            "judge_votes": len(votes),
            "complete": True,
        },
        "interpretation_boundary": [
            "The primary claim concerns FULL versus an uncontrolled baseline on the frozen 36-case suite.",
            "COMPACT versus CONTROL and FULL versus COMPACT are secondary and cannot rescue a failed FULL primary endpoint.",
            "Original TEST/ENGINEER/BOTH/NONE labels are descriptive subgroups only; no routing or conditional prompt injection occurs.",
            "A positive result does not validate autonomous routing or universal cross-model improvement.",
            "Cost is descriptive and does not enter any quality endpoint.",
        ],
    }

    output = RESULTS / "framework_v1_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
