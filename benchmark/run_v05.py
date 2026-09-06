#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

# run_v03 performs provider setup at import time and requires one of its known suites.
# v0.5 loads its own quality suite after import.
os.environ["BENCHMARK_SUITE"] = "combined"
import run_v03 as v03  # noqa: E402

ROOT = Path(__file__).resolve().parent
QUALITY_SUITE = os.getenv("QUALITY_SUITE", "combined").lower()
GENERATION_REPLICATES = max(1, int(os.getenv("QUALITY_GENERATION_REPLICATES", "1")))
JUDGE_VOTES = int(os.getenv("QUALITY_JUDGE_VOTES", "3"))
BOOTSTRAP_SAMPLES = max(1000, int(os.getenv("BENCHMARK_BOOTSTRAP_SAMPLES", "5000")))

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("QUALITY_JUDGE_VOTES must be an odd integer >= 3")

QUALITY_PAIRWISE_JUDGE = r'''You are a strict blinded evaluator of REASONING QUALITY. Compare Response A and Response B for the same case using only the supplied evidence and reference. You are not told which experimental condition produced either response.

The research question is whether one reasoning process produces a materially better epistemic and decision outcome. Judge substance, not style, protocol terminology, headings, verbosity, or token count.

Priority dimensions, when applicable:
1. factual correctness and faithful use of the observations;
2. separation of observation, inference, assumption, and causal claim;
3. causal/mechanistic accuracy and consideration of materially plausible alternatives;
4. quality and discriminating value of proposed evidence/tests;
5. revision when later evidence contradicts an earlier model;
6. calibrated uncertainty and exposure of decision-critical assumptions;
7. correctness and robustness of the decision/intervention, including constraints and second-order effects when relevant.

Do NOT reward an answer for being shorter or cheaper. Do NOT penalize length unless it creates a material reasoning error, contradiction, or unusable recommendation. If both responses are substantively equivalent on reasoning quality, return TIE.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"margin":0,"decisive_dimensions":["..."],"notes":"brief concrete reason"}
where margin is 0 for a tie, 1 for slight, 2 for clear, 3 for decisive.'''

PAIR_SPECS = [
    {"pair_id": "FULL_vs_BASELINE", "left": "FULL", "right": "BASELINE", "focal": "FULL", "role": "primary"},
    {"pair_id": "COMPACT_vs_BASELINE", "left": "COMPACT", "right": "BASELINE", "focal": "COMPACT", "role": "ablation"},
    {"pair_id": "FULL_vs_COMPACT", "left": "FULL", "right": "COMPACT", "focal": "FULL", "role": "depth_ablation"},
]


def load_quality_cases() -> list[dict[str, Any]]:
    pilot = json.loads((ROOT / "pilot_cases.json").read_text(encoding="utf-8"))
    stress = json.loads((ROOT / "stress_cases_v03.json").read_text(encoding="utf-8"))
    if QUALITY_SUITE == "pilot":
        return pilot
    if QUALITY_SUITE == "stress":
        return stress
    if QUALITY_SUITE == "combined":
        return pilot + stress
    raise ValueError("QUALITY_SUITE must be pilot, stress, or combined")


CASES = load_quality_cases()
v03.CASES = CASES


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def quality_reference(case: dict[str, Any]) -> dict[str, Any]:
    evaluator = case.get("evaluator_key", {})
    allowed = {
        "observations",
        "not_observed",
        "plausible_hypotheses",
        "critical_first_principles",
        "discriminating_evidence",
        "decision_critical_uncertainties",
        "constraints",
        "acceptable_interventions",
        "scoring_notes",
    }
    return {
        "case_id": case["case_id"],
        "case_reference": {k: v for k, v in evaluator.items() if k in allowed and v},
        "turn_references": [
            {
                "turn": t["turn"],
                "protocol": t.get("judge_reference", {}).get("protocol", []),
                "outcome": t.get("judge_reference", {}).get("outcome", []),
                "expected_revision": t.get("expected_revision"),
            }
            for t in case["turns"]
        ],
    }


def judge_vote(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> dict[str, Any]:
    seed_material = f"v05:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed_material).random() < 0.5:
        first, second = second, first

    last_turn = case["turns"][-1]["turn"]
    content = {
        **quality_reference(case),
        "response_A": v03.transcript(case, first, last_turn),
        "response_B": v03.transcript(case, second, last_turn),
    }
    result = v03.judge_call(
        QUALITY_PAIRWISE_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid quality judge result: {parsed}")

    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    focal = spec["focal"]
    focal_score = 0.5 if resolved == "TIE" else (1.0 if resolved == focal else 0.0)
    return {
        "case_id": case["case_id"],
        "replicate": run_x["replicate"],
        "pair_id": spec["pair_id"],
        "pair_role": spec["role"],
        "focal_condition": focal,
        "vote_index": vote_index,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": resolved,
        "focal_score": focal_score,
        "confidence": parsed.get("confidence"),
        "margin": parsed.get("margin"),
        "decisive_dimensions": parsed.get("decisive_dimensions", []),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def aggregate_pair(votes: list[dict[str, Any]], spec: dict[str, str]) -> dict[str, Any]:
    relevant = [v for v in votes if v["pair_id"] == spec["pair_id"]]
    by_case_rep: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for vote in relevant:
        by_case_rep.setdefault((vote["case_id"], vote["replicate"]), []).append(vote)

    replicate_rows = []
    for (case_id, replicate), group in sorted(by_case_rep.items()):
        focal = spec["focal"]
        opponent = spec["right"] if focal == spec["left"] else spec["left"]
        counts = {
            focal: sum(v["winner"] == focal for v in group),
            opponent: sum(v["winner"] == opponent for v in group),
            "TIE": sum(v["winner"] == "TIE" for v in group),
        }
        if counts[focal] > counts[opponent]:
            majority = focal
        elif counts[opponent] > counts[focal]:
            majority = opponent
        else:
            majority = "TIE"
        replicate_rows.append(
            {
                "case_id": case_id,
                "replicate": replicate,
                "vote_score": sum(v["focal_score"] for v in group) / len(group),
                "majority_winner": majority,
                "vote_counts": counts,
                "agreement": max(counts.values()) / len(group),
                "unanimous": max(counts.values()) == len(group),
            }
        )

    by_case: dict[str, list[float]] = {}
    for row in replicate_rows:
        by_case.setdefault(row["case_id"], []).append(row["vote_score"])
    case_scores = {case: sum(xs) / len(xs) for case, xs in by_case.items()}
    observed = sum(case_scores.values()) / len(case_scores) if case_scores else 0.0

    cases = list(case_scores)
    rng = random.Random(20260906)
    draws = []
    if len(cases) >= 2:
        for _ in range(BOOTSTRAP_SAMPLES):
            sample = [case_scores[rng.choice(cases)] for _ in cases]
            draws.append(sum(sample) / len(sample))
    else:
        draws = [observed]

    focal = spec["focal"]
    opponent = spec["right"] if focal == spec["left"] else spec["left"]
    return {
        "pair_id": spec["pair_id"],
        "role": spec["role"],
        "focal_condition": focal,
        "opponent_condition": opponent,
        "score": observed,
        "ci95_low": percentile(draws, 0.025),
        "ci95_high": percentile(draws, 0.975),
        "majority_wins": sum(r["majority_winner"] == focal for r in replicate_rows),
        "majority_ties": sum(r["majority_winner"] == "TIE" for r in replicate_rows),
        "majority_losses": sum(r["majority_winner"] == opponent for r in replicate_rows),
        "mean_vote_agreement": sum(r["agreement"] for r in replicate_rows) / len(replicate_rows),
        "unanimous_fraction": sum(r["unanimous"] for r in replicate_rows) / len(replicate_rows),
        "non_unanimous": [r for r in replicate_rows if not r["unanimous"]],
        "case_scores": case_scores,
    }


def main() -> None:
    out = ROOT / "results_v05"
    out.mkdir(exist_ok=True)
    runs_path = out / "v05_runs.jsonl"
    votes_path = out / "v05_judge_votes.jsonl"
    runs: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in ["BASELINE", "COMPACT", "FULL"]:
                print("running", replicate, case["case_id"], condition, flush=True)
                runs.append(v03.run_case(case, condition, replicate))
                write_jsonl(runs_path, runs)

    index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for spec in PAIR_SPECS:
                run_x = index[(case["case_id"], spec["left"], replicate)]
                run_y = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, JUDGE_VOTES + 1):
                    print("judging", replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    votes.append(judge_vote(case, run_x, run_y, spec, vote_index))
                    write_jsonl(votes_path, votes)

    pair_results = {spec["pair_id"]: aggregate_pair(votes, spec) for spec in PAIR_SPECS}

    cost_diagnostics = {}
    for condition in ["BASELINE", "COMPACT", "FULL"]:
        subset = [r for r in runs if r["condition"] == condition]
        cost_diagnostics[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }

    report = {
        "measurement_version": "0.5-quality-first",
        "experiment_role": "calibration, not framework validation",
        "suite": QUALITY_SUITE,
        "n_cases": len(CASES),
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes_per_pair": JUDGE_VOTES,
        "primary_research_question": "Does FULL reasoning improve reasoning quality relative to BASELINE?",
        "primary_metric": "repeated blinded quality-only pairwise judgments for FULL vs BASELINE, clustered by case",
        "secondary_ablations": ["COMPACT vs BASELINE", "FULL vs COMPACT"],
        "cost_policy": "token and latency measurements are descriptive diagnostics only and do not enter the quality score or judge prompt",
        "provider": "z.ai",
        "target": {"model": v03.TARGET_MODEL, "base_url": v03.TARGET_BASE},
        "judge": {
            "model": v03.JUDGE_MODEL,
            "base_url": v03.JUDGE_BASE,
            "same_model_and_endpoint_as_target": v03.TARGET_MODEL == v03.JUDGE_MODEL and v03.TARGET_BASE == v03.JUDGE_BASE,
        },
        "quality_results": pair_results,
        "cost_diagnostics": cost_diagnostics,
        "notes": [
            "Adaptive routing is intentionally excluded from v0.5 quality evidence.",
            "Each response pair is judged multiple times with independently randomized A/B orientation.",
            "Judge agreement is reported explicitly; unstable verdicts are evidence about evaluator reliability, not silently averaged away.",
            "Existing pilot/stress cases have influenced framework development, so this run calibrates measurement and effect direction rather than validating the framework.",
            "Future validation requires fresh held-out cases and preferably an evaluator model independent of the target model.",
        ],
    }
    (out / "v05_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
