#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results_routing_validation_v1"
BOOTSTRAP_SAMPLES = int(os.getenv("BENCHMARK_BOOTSTRAP_SAMPLES", "5000"))
EXPECTED_CASES = 48
EXPECTED_ROUTES = 48
EXPECTED_RUNS = 48 * 2 * 3
EXPECTED_VOTES = 48 * 3 * 3
BENEFIT_MIN_SCORE = 0.60
BENEFIT_CI_LOW_EXCLUSIVE = 0.50
PRESERVATION_MIN_SCORE = 0.50
PRESERVATION_CI_LOW_EXCLUSIVE = 0.45
MAX_FULL_INVOCATION = 0.65

if BOOTSTRAP_SAMPLES != 5000:
    raise ValueError("Selective Routing v1 aggregation requires exactly 5000 bootstrap samples")


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


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def summarize_case_scores(case_scores: dict[str, float], seed: str) -> dict[str, Any]:
    if not case_scores:
        raise RuntimeError("cannot summarize empty case scores")
    observed = sum(case_scores.values()) / len(case_scores)
    case_ids = sorted(case_scores)
    rng = random.Random(seed)
    draws = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = [case_scores[rng.choice(case_ids)] for _ in case_ids]
        draws.append(sum(sample) / len(sample))
    return {
        "score": observed,
        "ci95_low": percentile(draws, 0.025),
        "ci95_high": percentile(draws, 0.975),
        "n_cases": len(case_scores),
        "case_level_wins": sum(score > 0.5 for score in case_scores.values()),
        "case_level_ties": sum(score == 0.5 for score in case_scores.values()),
        "case_level_losses": sum(score < 0.5 for score in case_scores.values()),
        "case_scores": case_scores,
    }


def validate_completeness(routes: list[dict[str, Any]], runs: list[dict[str, Any]], votes: list[dict[str, Any]]) -> None:
    if len(routes) != EXPECTED_ROUTES:
        raise RuntimeError(f"expected {EXPECTED_ROUTES} routes, found {len(routes)}")
    if len(runs) != EXPECTED_RUNS:
        raise RuntimeError(f"expected {EXPECTED_RUNS} target runs, found {len(runs)}")
    if len(votes) != EXPECTED_VOTES:
        raise RuntimeError(f"expected {EXPECTED_VOTES} judge votes, found {len(votes)}")

    route_keys = Counter(route["case_id"] for route in routes)
    if len(route_keys) != EXPECTED_CASES or set(route_keys.values()) != {1}:
        raise RuntimeError("route case IDs are missing or duplicated")
    run_keys = Counter((r["case_id"], r["condition"], r["replicate"]) for r in runs)
    if len(run_keys) != EXPECTED_RUNS or set(run_keys.values()) != {1}:
        raise RuntimeError("target run keys are missing or duplicated")
    vote_keys = Counter((v["case_id"], v["replicate"], v["vote_index"]) for v in votes)
    if len(vote_keys) != EXPECTED_VOTES or set(vote_keys.values()) != {1}:
        raise RuntimeError("judge vote keys are missing or duplicated")

    route_cases = set(route_keys)
    if {r["case_id"] for r in runs} != route_cases or {v["case_id"] for v in votes} != route_cases:
        raise RuntimeError("case coverage differs among routes, runs, and votes")


def validate_meta() -> dict[str, Any]:
    paths = sorted(RESULTS.glob("routing_v1_meta_shard_*.json"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six routing metadata files, found {len(paths)}")
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if {row["shard_index"] for row in rows} != set(range(6)):
        raise RuntimeError("invalid metadata shard indices")
    ref = rows[0]
    invariant = [
        "measurement_version", "experiment_role", "evaluation_tier", "shard_count",
        "suite", "suite_sha256", "n_cases_total", "generation_replicates",
        "judge_votes_per_pair", "conditions", "full_prompt_sha256", "router_prompt_sha256",
        "target", "judge", "router", "pair_spec", "policy_construction",
    ]
    for row in rows[1:]:
        for field in invariant:
            if row[field] != ref[field]:
                raise RuntimeError(f"metadata disagreement for {field}")
    if ref["n_cases_total"] != EXPECTED_CASES:
        raise RuntimeError("metadata does not freeze 48 cases")
    return {field: ref[field] for field in invariant}


def replicate_rows(votes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for vote in votes:
        by_key.setdefault((vote["case_id"], int(vote["replicate"])), []).append(vote)
    rows = []
    for (case_id, replicate), group in sorted(by_key.items()):
        if len(group) != 3:
            raise RuntimeError(f"expected 3 votes for {(case_id, replicate)}, found {len(group)}")
        counts = {
            "FULL": sum(v["winner"] == "FULL" for v in group),
            "CONTROL": sum(v["winner"] == "CONTROL" for v in group),
            "TIE": sum(v["winner"] == "TIE" for v in group),
        }
        if counts["FULL"] > counts["CONTROL"]:
            majority = "FULL"
        elif counts["CONTROL"] > counts["FULL"]:
            majority = "CONTROL"
        else:
            majority = "TIE"
        rows.append({
            "case_id": case_id,
            "replicate": replicate,
            "full_score": sum(float(v["focal_score"]) for v in group) / 3,
            "majority_winner": majority,
            "agreement": max(counts.values()) / 3,
            "unanimous": max(counts.values()) == 3,
            "vote_counts": counts,
        })
    if len(rows) != EXPECTED_CASES * 3:
        raise RuntimeError(f"expected {EXPECTED_CASES * 3} case-replicate rows, found {len(rows)}")
    return rows


def case_metadata(votes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for vote in votes:
        out.setdefault(vote["case_id"], {
            "domain": vote["domain"],
            "author_route_label": vote["author_route_label"],
            "sequential": bool(vote["sequential"]),
            "has_distractors": bool(vote["has_distractors"]),
            "requires_action": bool(vote["requires_action"]),
            "adversarial_surface": bool(vote.get("adversarial_surface", False)),
        })
    return out


def policy_scores(
    routes: list[dict[str, Any]],
    reps: list[dict[str, Any]],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    route_map = {row["case_id"]: row["selected_mode"] for row in routes}
    full_by_case: dict[str, list[float]] = {}
    routed_control_by_case: dict[str, list[float]] = {}
    routed_full_by_case: dict[str, list[float]] = {}
    for row in reps:
        case_id = row["case_id"]
        s = float(row["full_score"])
        mode = route_map[case_id]
        full_by_case.setdefault(case_id, []).append(s)
        routed_control_by_case.setdefault(case_id, []).append(s if mode == "FULL" else 0.5)
        routed_full_by_case.setdefault(case_id, []).append(0.5 if mode == "FULL" else 1.0 - s)
    mean = lambda xs: sum(xs) / len(xs)
    return (
        {case: mean(values) for case, values in full_by_case.items()},
        {case: mean(values) for case, values in routed_control_by_case.items()},
        {case: mean(values) for case, values in routed_full_by_case.items()},
    )


def subgroup_summary(
    scores: dict[str, float],
    metadata: dict[str, dict[str, Any]],
    field: str,
    seed_prefix: str,
) -> dict[str, Any]:
    values = sorted({str(row[field]) for row in metadata.values()})
    out: dict[str, Any] = {}
    for value in values:
        subset = {case: score for case, score in scores.items() if str(metadata[case][field]) == value}
        out[value] = summarize_case_scores(subset, f"{seed_prefix}:{field}:{value}")
    return out


def route_diagnostics(routes: list[dict[str, Any]]) -> dict[str, Any]:
    full_count = sum(route["selected_mode"] == "FULL" for route in routes)
    correct = sum(
        (route["selected_mode"] == "FULL" and route["author_route_label"] == "FULL_VALUE")
        or (route["selected_mode"] == "CONTROL" and route["author_route_label"] == "CONTROL_VALUE")
        for route in routes
    )
    false_full = sum(route["selected_mode"] == "FULL" and route["author_route_label"] == "CONTROL_VALUE" for route in routes)
    false_control = sum(route["selected_mode"] == "CONTROL" and route["author_route_label"] == "FULL_VALUE" for route in routes)
    by_domain: dict[str, dict[str, Any]] = {}
    for domain in sorted({route["domain"] for route in routes}):
        subset = [route for route in routes if route["domain"] == domain]
        by_domain[domain] = {
            "n": len(subset),
            "full_routes": sum(route["selected_mode"] == "FULL" for route in subset),
            "full_rate": sum(route["selected_mode"] == "FULL" for route in subset) / len(subset),
        }
    return {
        "n_cases": len(routes),
        "full_invocations": full_count,
        "control_invocations": len(routes) - full_count,
        "full_invocation_rate": full_count / len(routes),
        "author_label_accuracy": correct / len(routes),
        "false_full": false_full,
        "false_control": false_control,
        "by_domain": by_domain,
    }


def usage_diagnostics(routes: list[dict[str, Any]], runs: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, Any] = {}
    for condition in ("CONTROL", "FULL"):
        subset = [run for run in runs if run["condition"] == condition]
        by_condition[condition] = {
            "n_runs": len(subset),
            "input_tokens": int(sum(run["usage"]["input_tokens"] for run in subset)),
            "output_tokens": int(sum(run["usage"]["output_tokens"] for run in subset)),
            "latency_ms": sum(run["usage"]["latency_ms"] for run in subset),
        }
    router_usage = {
        "n_routes": len(routes),
        "input_tokens": int(sum(route["usage"]["input_tokens"] for route in routes)),
        "output_tokens": int(sum(route["usage"]["output_tokens"] for route in routes)),
        "latency_ms": sum(route["usage"]["latency_ms"] for route in routes),
    }
    route_map = {route["case_id"]: route["selected_mode"] for route in routes}
    selected = [run for run in runs if run["condition"] == route_map[run["case_id"]]]
    projected = {
        "n_selected_target_runs": len(selected),
        "target_input_tokens": int(sum(run["usage"]["input_tokens"] for run in selected)),
        "target_output_tokens": int(sum(run["usage"]["output_tokens"] for run in selected)),
        "target_latency_ms": sum(run["usage"]["latency_ms"] for run in selected),
        "router_input_tokens": router_usage["input_tokens"],
        "router_output_tokens": router_usage["output_tokens"],
        "router_latency_ms": router_usage["latency_ms"],
    }
    return {"generated_experiment": by_condition, "router": router_usage, "projected_routed_policy": projected}


def main() -> None:
    routes = load_all("routing_v1_routes")
    runs = load_all("routing_v1_runs")
    votes = load_all("routing_v1_votes")
    validate_completeness(routes, runs, votes)
    meta = validate_meta()
    reps = replicate_rows(votes)
    metadata = case_metadata(votes)
    full_scores, routed_control_scores, routed_full_scores = policy_scores(routes, reps)

    full_summary = summarize_case_scores(full_scores, "routing-v1:full-control")
    benefit = summarize_case_scores(routed_control_scores, "routing-v1:routed-control")
    preservation = summarize_case_scores(routed_full_scores, "routing-v1:routed-full")
    routing = route_diagnostics(routes)

    benefit_pass = benefit["score"] >= BENEFIT_MIN_SCORE and benefit["ci95_low"] > BENEFIT_CI_LOW_EXCLUSIVE
    preservation_pass = preservation["score"] >= PRESERVATION_MIN_SCORE and preservation["ci95_low"] > PRESERVATION_CI_LOW_EXCLUSIVE
    selectivity_pass = routing["full_invocation_rate"] <= MAX_FULL_INVOCATION
    overall_pass = benefit_pass and preservation_pass and selectivity_pass

    per_case = {}
    route_map = {route["case_id"]: route for route in routes}
    for case_id in sorted(full_scores):
        per_case[case_id] = {
            **metadata[case_id],
            "selected_mode": route_map[case_id]["selected_mode"],
            "router_confidence": route_map[case_id]["confidence"],
            "router_signals": route_map[case_id]["signals"],
            "full_vs_control_score": full_scores[case_id],
            "routed_vs_control_score": routed_control_scores[case_id],
            "routed_vs_full_score": routed_full_scores[case_id],
        }

    report = {
        "measurement_version": "selective-routing-v1",
        "experiment_role": "fresh selective-routing validation; binary FULL vs CONTROL",
        "evaluation_tier": meta["evaluation_tier"],
        "suite": meta["suite"],
        "suite_sha256": meta["suite_sha256"],
        "n_cases": EXPECTED_CASES,
        "target": meta["target"],
        "judge": meta["judge"],
        "router": meta["router"],
        "generation_replicates": 3,
        "judge_votes_per_pair": 3,
        "full_vs_control": full_summary,
        "primary_benefit_gate": {
            "comparison": "ROUTED_vs_CONTROL",
            "point_estimate_min": BENEFIT_MIN_SCORE,
            "ci95_low_exclusive_min": BENEFIT_CI_LOW_EXCLUSIVE,
            "observed": benefit,
            "pass": benefit_pass,
        },
        "quality_preservation_guard": {
            "comparison": "ROUTED_vs_FULL",
            "point_estimate_min": PRESERVATION_MIN_SCORE,
            "ci95_low_exclusive_min": PRESERVATION_CI_LOW_EXCLUSIVE,
            "observed": preservation,
            "pass": preservation_pass,
        },
        "selectivity_guard": {
            "max_full_invocation_rate": MAX_FULL_INVOCATION,
            "observed_full_invocation_rate": routing["full_invocation_rate"],
            "pass": selectivity_pass,
        },
        "routing_validation_pass": overall_pass,
        "routing_diagnostics": routing,
        "judge_reliability": {
            "mean_vote_agreement": sum(row["agreement"] for row in reps) / len(reps),
            "unanimous_fraction": sum(row["unanimous"] for row in reps) / len(reps),
            "majority_full": sum(row["majority_winner"] == "FULL" for row in reps),
            "majority_tie": sum(row["majority_winner"] == "TIE" for row in reps),
            "majority_control": sum(row["majority_winner"] == "CONTROL" for row in reps),
        },
        "breakdowns": {
            "routed_vs_control_by_author_label": subgroup_summary(routed_control_scores, metadata, "author_route_label", "rvc"),
            "routed_vs_control_by_domain": subgroup_summary(routed_control_scores, metadata, "domain", "rvc"),
            "routed_vs_control_by_sequential": subgroup_summary(routed_control_scores, metadata, "sequential", "rvc"),
            "routed_vs_control_by_distractors": subgroup_summary(routed_control_scores, metadata, "has_distractors", "rvc"),
            "routed_vs_control_by_action": subgroup_summary(routed_control_scores, metadata, "requires_action", "rvc"),
            "routed_vs_full_by_author_label": subgroup_summary(routed_full_scores, metadata, "author_route_label", "rvf"),
        },
        "per_case": per_case,
        "usage_diagnostics": usage_diagnostics(routes, runs),
        "completeness": {"routes": len(routes), "target_runs": len(runs), "judge_votes": len(votes), "complete": True},
        "interpretation_boundary": [
            "Author FULL_VALUE/CONTROL_VALUE labels are diagnostic only and do not determine validation success.",
            "The router and judge are the same GLM-5.3-Flash model on the same provider, used in different blinded roles; this is a validity limitation.",
            "The result is Tier-1B same-family/provider evidence, not independent-provider validation.",
            "Cost/selectivity cannot rescue either quality-gate failure.",
            "The fresh routing suite becomes exposed after this run and cannot validate a redesigned router.",
        ],
    }

    output = RESULTS / "routing_v1_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
