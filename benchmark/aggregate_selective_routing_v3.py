#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results_routing_validation_v3"
BOOTSTRAP_SAMPLES = int(os.getenv("BENCHMARK_BOOTSTRAP_SAMPLES", "5000"))
EXPECTED_CASES = 48
EXPECTED_ROUTES = 48
EXPECTED_RUNS = 48 * 2 * 3
EXPECTED_VOTES = 48 * 3 * 3
FRAMEWORK_MIN_SCORE = 0.60
BENEFIT_MIN_SCORE = 0.60
QUALITY_CI_LOW_EXCLUSIVE = 0.50
NONINFERIORITY_MARGIN = -0.05
MAX_FULL_INVOCATION = 0.65
FROZEN_ROUTER_GIT_BLOB = "6ebb72e443c846aee35281c20e64f3b5d173a7a0"

if BOOTSTRAP_SAMPLES != 5000:
    raise ValueError("Selective Routing v3 aggregation requires exactly 5000 bootstrap samples")


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
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def summarize_scores(case_scores: dict[str, float], seed: str) -> dict[str, Any]:
    observed = sum(case_scores.values()) / len(case_scores)
    ids = sorted(case_scores)
    rng = random.Random(seed)
    draws = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = [case_scores[rng.choice(ids)] for _ in ids]
        draws.append(sum(sample) / len(sample))
    return {
        "score": observed,
        "ci95_low": percentile(draws, 0.025),
        "ci95_high": percentile(draws, 0.975),
        "n_cases": len(case_scores),
        "case_level_wins": sum(v > 0.5 for v in case_scores.values()),
        "case_level_ties": sum(v == 0.5 for v in case_scores.values()),
        "case_level_losses": sum(v < 0.5 for v in case_scores.values()),
        "case_scores": case_scores,
    }


def summarize_delta(case_delta: dict[str, float], seed: str) -> dict[str, Any]:
    observed = sum(case_delta.values()) / len(case_delta)
    ids = sorted(case_delta)
    rng = random.Random(seed)
    draws = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = [case_delta[rng.choice(ids)] for _ in ids]
        draws.append(sum(sample) / len(sample))
    return {
        "delta": observed,
        "ci95_low": percentile(draws, 0.025),
        "ci95_high": percentile(draws, 0.975),
        "n_cases": len(case_delta),
        "case_deltas": case_delta,
    }


def validate_completeness(routes: list[dict[str, Any]], runs: list[dict[str, Any]], votes: list[dict[str, Any]]) -> None:
    if len(routes) != EXPECTED_ROUTES:
        raise RuntimeError(f"expected {EXPECTED_ROUTES} routes, found {len(routes)}")
    if len(runs) != EXPECTED_RUNS:
        raise RuntimeError(f"expected {EXPECTED_RUNS} target runs, found {len(runs)}")
    if len(votes) != EXPECTED_VOTES:
        raise RuntimeError(f"expected {EXPECTED_VOTES} judge votes, found {len(votes)}")
    route_keys = Counter(r["case_id"] for r in routes)
    run_keys = Counter((r["case_id"], r["condition"], int(r["replicate"])) for r in runs)
    vote_keys = Counter((v["case_id"], int(v["replicate"]), int(v["vote_index"])) for v in votes)
    if len(route_keys) != EXPECTED_CASES or set(route_keys.values()) != {1}:
        raise RuntimeError("route keys incomplete or duplicated")
    if len(run_keys) != EXPECTED_RUNS or set(run_keys.values()) != {1}:
        raise RuntimeError("target run keys incomplete or duplicated")
    if len(vote_keys) != EXPECTED_VOTES or set(vote_keys.values()) != {1}:
        raise RuntimeError("judge vote keys incomplete or duplicated")


def validate_meta() -> dict[str, Any]:
    paths = sorted(RESULTS.glob("routing_v3_meta_shard_*.json"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six v3 metadata files, found {len(paths)}")
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if {int(row["shard_index"]) for row in rows} != set(range(6)):
        raise RuntimeError("invalid v3 metadata shard indices")
    ref = rows[0]
    invariant = [
        "measurement_version", "experiment_role", "evaluation_tier", "shard_count",
        "suite", "suite_sha256", "n_cases_total", "generation_replicates",
        "judge_votes_per_pair", "conditions", "full_prompt_sha256", "router_prompt_sha256",
        "router_git_blob", "target", "judge", "router", "pair_spec", "policy_construction",
        "global_preflight_connectivity_required", "shard_connectivity_probe",
    ]
    for row in rows[1:]:
        for field in invariant:
            if row[field] != ref[field]:
                raise RuntimeError(f"metadata disagreement for {field}")
    if ref["n_cases_total"] != EXPECTED_CASES:
        raise RuntimeError("metadata does not freeze 48 cases")
    if ref["router_git_blob"] != FROZEN_ROUTER_GIT_BLOB:
        raise RuntimeError("v3 router implementation blob mismatch")
    if ref["shard_connectivity_probe"] is not False:
        raise RuntimeError("v3 shards must not perform connectivity probes")
    return {field: ref[field] for field in invariant}


def replicate_rows(votes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for vote in votes:
        by_key.setdefault((vote["case_id"], int(vote["replicate"])), []).append(vote)
    out = []
    for (case_id, replicate), group in sorted(by_key.items()):
        if len(group) != 3:
            raise RuntimeError(f"expected 3 votes for {(case_id, replicate)}, found {len(group)}")
        counts = {
            "FULL": sum(v["winner"] == "FULL" for v in group),
            "CONTROL": sum(v["winner"] == "CONTROL" for v in group),
            "TIE": sum(v["winner"] == "TIE" for v in group),
        }
        out.append({
            "case_id": case_id,
            "replicate": replicate,
            "full_score": sum(float(v["focal_score"]) for v in group) / 3,
            "agreement": max(counts.values()) / 3,
            "unanimous": max(counts.values()) == 3,
            "vote_counts": counts,
        })
    if len(out) != EXPECTED_CASES * 3:
        raise RuntimeError("case-replicate row count mismatch")
    return out


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


def policy_scores(routes: list[dict[str, Any]], reps: list[dict[str, Any]]) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float]]:
    route_map = {row["case_id"]: row["selected_mode"] for row in routes}
    full_by_case: dict[str, list[float]] = {}
    routed_by_case: dict[str, list[float]] = {}
    routed_full_by_case: dict[str, list[float]] = {}
    for row in reps:
        case_id = row["case_id"]
        s = float(row["full_score"])
        mode = route_map[case_id]
        full_by_case.setdefault(case_id, []).append(s)
        routed_by_case.setdefault(case_id, []).append(s if mode == "FULL" else 0.5)
        routed_full_by_case.setdefault(case_id, []).append(0.5 if mode == "FULL" else 1.0 - s)
    mean = lambda xs: sum(xs) / len(xs)
    full = {k: mean(v) for k, v in full_by_case.items()}
    routed = {k: mean(v) for k, v in routed_by_case.items()}
    routed_full = {k: mean(v) for k, v in routed_full_by_case.items()}
    delta = {k: routed[k] - full[k] for k in full}
    return full, routed, routed_full, delta


def subgroup(scores: dict[str, float], metadata: dict[str, dict[str, Any]], field: str, seed: str) -> dict[str, Any]:
    out = {}
    for value in sorted({str(row[field]) for row in metadata.values()}):
        subset = {case: score for case, score in scores.items() if str(metadata[case][field]) == value}
        out[value] = summarize_scores(subset, f"{seed}:{field}:{value}")
    return out


def route_diagnostics(routes: list[dict[str, Any]]) -> dict[str, Any]:
    full = sum(r["selected_mode"] == "FULL" for r in routes)
    by_label = {}
    for label in ("CLEAR_FULL", "CLEAR_CONTROL", "CAUSAL_TRAP", "QUIET_FULL"):
        subset = [r for r in routes if r["author_route_label"] == label]
        by_label[label] = {
            "n": len(subset),
            "full_routes": sum(r["selected_mode"] == "FULL" for r in subset),
            "full_rate": sum(r["selected_mode"] == "FULL" for r in subset) / len(subset),
        }
    clear = [r for r in routes if r["author_route_label"] in {"CLEAR_FULL", "CLEAR_CONTROL"}]
    clear_correct = sum(
        (r["author_route_label"] == "CLEAR_FULL" and r["selected_mode"] == "FULL")
        or (r["author_route_label"] == "CLEAR_CONTROL" and r["selected_mode"] == "CONTROL")
        for r in clear
    )
    by_domain = {}
    for domain in sorted({r["domain"] for r in routes}):
        subset = [r for r in routes if r["domain"] == domain]
        by_domain[domain] = {
            "n": len(subset),
            "full_routes": sum(r["selected_mode"] == "FULL" for r in subset),
            "full_rate": sum(r["selected_mode"] == "FULL" for r in subset) / len(subset),
        }
    return {
        "n_cases": len(routes),
        "full_invocations": full,
        "control_invocations": len(routes) - full,
        "full_invocation_rate": full / len(routes),
        "clear_stratum_n": len(clear),
        "clear_stratum_accuracy": clear_correct / len(clear),
        "causal_trap_control_rate": 1.0 - by_label["CAUSAL_TRAP"]["full_rate"],
        "quiet_full_full_rate": by_label["QUIET_FULL"]["full_rate"],
        "by_author_label": by_label,
        "by_domain": by_domain,
    }


def usage_diagnostics(routes: list[dict[str, Any]], runs: list[dict[str, Any]], votes: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition = {}
    for condition in ("CONTROL", "FULL"):
        subset = [r for r in runs if r["condition"] == condition]
        by_condition[condition] = {
            "n_runs": len(subset),
            "input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }
    router_usage = {
        "n_routes": len(routes),
        "input_tokens": int(sum(r["usage"]["input_tokens"] for r in routes)),
        "output_tokens": int(sum(r["usage"]["output_tokens"] for r in routes)),
        "latency_ms": sum(r["usage"]["latency_ms"] for r in routes),
    }
    judge_usage = {
        "n_votes": len(votes),
        "input_tokens": int(sum(v["judge_usage"]["input_tokens"] for v in votes)),
        "output_tokens": int(sum(v["judge_usage"]["output_tokens"] for v in votes)),
        "latency_ms": sum(v["judge_usage"]["latency_ms"] for v in votes),
        "format_retries": int(sum(max(0, int(v.get("format_attempts", 1)) - 1) for v in votes)),
    }
    route_map = {r["case_id"]: r["selected_mode"] for r in routes}
    selected = [r for r in runs if r["condition"] == route_map[r["case_id"]]]
    projected = {
        "selected_target_runs": len(selected),
        "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in selected)),
        "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in selected)),
        "target_latency_ms": sum(r["usage"]["latency_ms"] for r in selected),
        "router_input_tokens": router_usage["input_tokens"],
        "router_output_tokens": router_usage["output_tokens"],
        "router_latency_ms": router_usage["latency_ms"],
    }
    return {"generated_experiment": by_condition, "router": router_usage, "judge": judge_usage, "projected_routed_policy": projected}


def main() -> None:
    routes = load_all("routing_v3_routes")
    runs = load_all("routing_v3_runs")
    votes = load_all("routing_v3_votes")
    validate_completeness(routes, runs, votes)
    meta = validate_meta()
    reps = replicate_rows(votes)
    metadata = case_metadata(votes)
    full_scores, routed_scores, routed_full_scores, deltas = policy_scores(routes, reps)

    full_summary = summarize_scores(full_scores, "routing-v3:full-control")
    routed_summary = summarize_scores(routed_scores, "routing-v3:routed-control")
    paired_summary = summarize_delta(deltas, "routing-v3:paired-delta")
    direct_routed_full = summarize_scores(routed_full_scores, "routing-v3:routed-full")
    routing = route_diagnostics(routes)

    framework_pass = full_summary["score"] >= FRAMEWORK_MIN_SCORE and full_summary["ci95_low"] > QUALITY_CI_LOW_EXCLUSIVE
    routed_pass = routed_summary["score"] >= BENEFIT_MIN_SCORE and routed_summary["ci95_low"] > QUALITY_CI_LOW_EXCLUSIVE
    preservation_pass = paired_summary["ci95_low"] > NONINFERIORITY_MARGIN
    selectivity_pass = routing["full_invocation_rate"] <= MAX_FULL_INVOCATION
    overall_pass = framework_pass and routed_pass and preservation_pass and selectivity_pass

    retained_gain_ratio = None
    if full_summary["score"] > 0.5:
        retained_gain_ratio = (routed_summary["score"] - 0.5) / (full_summary["score"] - 0.5)

    route_map = {r["case_id"]: r for r in routes}
    per_case = {}
    for case_id in sorted(full_scores):
        per_case[case_id] = {
            **metadata[case_id],
            "selected_mode": route_map[case_id]["selected_mode"],
            "router_confidence": route_map[case_id]["confidence"],
            "router_signals": route_map[case_id]["signals"],
            "full_vs_control_score": full_scores[case_id],
            "routed_vs_control_score": routed_scores[case_id],
            "routed_vs_full_descriptive_score": routed_full_scores[case_id],
            "paired_decrement": deltas[case_id],
        }

    report = {
        "measurement_version": "selective-routing-v3-marginal-value-validation",
        "experiment_role": "fresh semantic-stress validation of preregistered v3 marginal-value router",
        "evaluation_tier": "Tier-1B cross-model same-family; not independent-provider evaluation",
        "suite": meta["suite"],
        "suite_sha256": meta["suite_sha256"],
        "n_cases": EXPECTED_CASES,
        "target": meta["target"],
        "judge": meta["judge"],
        "router": meta["router"],
        "router_git_blob": meta["router_git_blob"],
        "generation_replicates": 3,
        "judge_votes_per_pair": 3,
        "framework_replication_gate": {
            "comparison": "FULL_vs_CONTROL",
            "score_min": FRAMEWORK_MIN_SCORE,
            "ci95_low_exclusive_min": QUALITY_CI_LOW_EXCLUSIVE,
            "observed": full_summary,
            "pass": framework_pass,
        },
        "routed_benefit_gate": {
            "comparison": "ROUTED_vs_CONTROL",
            "score_min": BENEFIT_MIN_SCORE,
            "ci95_low_exclusive_min": QUALITY_CI_LOW_EXCLUSIVE,
            "observed": routed_summary,
            "pass": routed_pass,
        },
        "paired_preservation_gate": {
            "estimand": "mean case-level ROUTED_vs_CONTROL minus FULL_vs_CONTROL score",
            "noninferiority_margin": NONINFERIORITY_MARGIN,
            "criterion": "ci95_low > margin",
            "observed": paired_summary,
            "pass": preservation_pass,
        },
        "selectivity_guard": {
            "max_full_invocation_rate": MAX_FULL_INVOCATION,
            "observed_full_invocation_rate": routing["full_invocation_rate"],
            "pass": selectivity_pass,
        },
        "routing_v3_validation_pass": overall_pass,
        "retained_gain_ratio": retained_gain_ratio,
        "direct_routed_vs_full_descriptive": direct_routed_full,
        "routing_diagnostics": routing,
        "judge_reliability": {
            "mean_vote_agreement": sum(r["agreement"] for r in reps) / len(reps),
            "unanimous_case_replicate_rate": sum(r["unanimous"] for r in reps) / len(reps),
        },
        "subgroups": {
            "full_vs_control": {
                "author_route_label": subgroup(full_scores, metadata, "author_route_label", "v3:full"),
                "domain": subgroup(full_scores, metadata, "domain", "v3:full"),
                "sequential": subgroup(full_scores, metadata, "sequential", "v3:full"),
                "requires_action": subgroup(full_scores, metadata, "requires_action", "v3:full"),
                "has_distractors": subgroup(full_scores, metadata, "has_distractors", "v3:full"),
            },
            "routed_vs_control": {
                "author_route_label": subgroup(routed_scores, metadata, "author_route_label", "v3:routed"),
                "domain": subgroup(routed_scores, metadata, "domain", "v3:routed"),
                "sequential": subgroup(routed_scores, metadata, "sequential", "v3:routed"),
                "requires_action": subgroup(routed_scores, metadata, "requires_action", "v3:routed"),
                "has_distractors": subgroup(routed_scores, metadata, "has_distractors", "v3:routed"),
            },
        },
        "per_case": per_case,
        "cost_diagnostics_descriptive_only": usage_diagnostics(routes, runs, votes),
        "frozen_thresholds": {
            "framework_score_min": FRAMEWORK_MIN_SCORE,
            "benefit_score_min": BENEFIT_MIN_SCORE,
            "quality_ci_low_exclusive_min": QUALITY_CI_LOW_EXCLUSIVE,
            "paired_noninferiority_margin": NONINFERIORITY_MARGIN,
            "max_full_invocation_rate": MAX_FULL_INVOCATION,
        },
        "interpretation_guard": "v3 success requires all four frozen gates; same-family/provider evidence only",
    }

    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / "routing_v3_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "framework_pass": framework_pass,
        "routed_pass": routed_pass,
        "preservation_pass": preservation_pass,
        "selectivity_pass": selectivity_pass,
        "routing_v3_validation_pass": overall_pass,
        "full_vs_control": full_summary["score"],
        "routed_vs_control": routed_summary["score"],
        "paired_delta": paired_summary["delta"],
        "paired_ci95_low": paired_summary["ci95_low"],
        "full_invocation_rate": routing["full_invocation_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
