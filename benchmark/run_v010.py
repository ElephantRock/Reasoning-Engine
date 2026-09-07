#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402
import run_v06 as v06  # noqa: E402
import run_v07 as v07  # noqa: E402
import run_v08 as v08  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "capability_cases_v010.json").read_text(encoding="utf-8"))

GENERATION_REPLICATES = max(1, int(os.getenv("V010_GENERATION_REPLICATES", "3")))
BEHAVIOR_VOTES = int(os.getenv("V010_BEHAVIOR_VOTES", "3"))
QUALITY_VOTES = int(os.getenv("V010_QUALITY_VOTES", "3"))
MANIPULATION_LIFT_GATE = float(os.getenv("V010_MANIPULATION_LIFT_GATE", "0.5"))

for name, value in (("V010_BEHAVIOR_VOTES", BEHAVIOR_VOTES), ("V010_QUALITY_VOTES", QUALITY_VOTES)):
    if value < 3 or value % 2 == 0:
        raise ValueError(f"{name} must be an odd integer >= 3")

FAMILIES = ("TEST", "ENGINEER")
CONDITIONS = ("CONTROL", "ATTENTION", "TARGET")

CONTROL = v07.CORE
ATTENTION = v07.ATTENTION
TARGET_MODULES = {
    "TEST": v06.STAGE_ADDONS["TEST"],
    "ENGINEER": v07.TARGET_MODULES["ENGINEER"],
}

PAIR_SPECS = [
    {"pair_id": "TARGET_vs_CONTROL", "left": "TARGET", "right": "CONTROL", "focal": "TARGET", "role": "primary_instruction_effect"},
    {"pair_id": "TARGET_vs_ATTENTION", "left": "TARGET", "right": "ATTENTION", "focal": "TARGET", "role": "capability_specificity"},
    {"pair_id": "ATTENTION_vs_CONTROL", "left": "ATTENTION", "right": "CONTROL", "focal": "ATTENTION", "role": "generic_attention_control"},
]

ABSOLUTE_BEHAVIOR_JUDGE = v08.SCREEN_BEHAVIOR_JUDGE
QUALITY_JUDGE = v07.QUALITY_JUDGE


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def system_for(case: dict[str, Any], condition: str) -> str:
    if condition == "CONTROL":
        return CONTROL
    if condition == "ATTENTION":
        return ATTENTION
    if condition == "TARGET":
        return CONTROL + TARGET_MODULES[case["family"]]
    raise ValueError(condition)


def run_case(case: dict[str, Any], condition: str, replicate: int) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    messages: list[dict[str, str]] = []
    responses: list[dict[str, Any]] = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = v03.target_call(system_for(case, condition), messages)
        v03.add_usage(usage, result["usage"])
        responses.append({"turn": turn["turn"], "text": result["text"]})
        messages.append({"role": "assistant", "content": result["text"]})
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "condition": condition,
        "replicate": replicate,
        "responses": responses,
        "usage": usage,
    }


def transcript(case: dict[str, Any], run: dict[str, Any]) -> str:
    return v03.transcript(case, run, case["turns"][-1]["turn"])


def absolute_behavior_vote(case: dict[str, Any], run: dict[str, Any], vote_index: int) -> dict[str, Any]:
    content = {
        "case_id": case["case_id"],
        "target_behavior": case["evaluator_key"]["target_behavior"],
        "response": transcript(case, run),
    }
    result = v03.judge_call(
        ABSOLUTE_BEHAVIOR_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    score = parsed.get("score")
    if not isinstance(score, (int, float)) or not 0 <= float(score) <= 4:
        raise RuntimeError(f"invalid absolute behavior score: {parsed}")
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "condition": run["condition"],
        "replicate": run["replicate"],
        "vote_index": vote_index,
        "score": float(score),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def quality_reference(case: dict[str, Any]) -> dict[str, Any]:
    evaluator = case.get("evaluator_key", {})
    allowed = {
        "observations",
        "not_observed",
        "plausible_hypotheses",
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
            {"turn": t["turn"], "expected_revision": t.get("expected_revision")}
            for t in case["turns"]
        ],
    }


def quality_vote(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"v010-quality:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed).random() < 0.5:
        first, second = second, first
    content = {
        **quality_reference(case),
        "response_A": transcript(case, first),
        "response_B": transcript(case, second),
    }
    result = v03.judge_call(
        QUALITY_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid quality result: {parsed}")
    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    focal = spec["focal"]
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "replicate": run_x["replicate"],
        "pair_id": spec["pair_id"],
        "pair_role": spec["role"],
        "focal_condition": focal,
        "vote_index": vote_index,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": resolved,
        "focal_score": 0.5 if resolved == "TIE" else (1.0 if resolved == focal else 0.0),
        "confidence": parsed.get("confidence"),
        "margin": parsed.get("margin"),
        "decisive_dimensions": parsed.get("decisive_dimensions", []),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def behavior_summary(votes: list[dict[str, Any]]) -> dict[str, Any]:
    # Aggregate votes within one exact response first, then generations within case,
    # then cases within family. This prevents judge replicates or generation replicates
    # from masquerading as independent cases.
    response_means: dict[tuple[str, str, int], float] = {}
    for case in CASES:
        for condition in CONDITIONS:
            for replicate in range(1, GENERATION_REPLICATES + 1):
                rows = [
                    v["score"] for v in votes
                    if v["case_id"] == case["case_id"]
                    and v["condition"] == condition
                    and v["replicate"] == replicate
                ]
                if rows:
                    response_means[(case["case_id"], condition, replicate)] = sum(rows) / len(rows)

    case_means: dict[str, dict[str, float]] = {}
    for case in CASES:
        case_means[case["case_id"]] = {}
        for condition in CONDITIONS:
            rows = [
                response_means[(case["case_id"], condition, replicate)]
                for replicate in range(1, GENERATION_REPLICATES + 1)
                if (case["case_id"], condition, replicate) in response_means
            ]
            if rows:
                case_means[case["case_id"]][condition] = sum(rows) / len(rows)

    out: dict[str, Any] = {}
    for family in FAMILIES:
        family_cases = [c for c in CASES if c["family"] == family]
        condition_means: dict[str, float | None] = {}
        for condition in CONDITIONS:
            xs = [
                case_means[c["case_id"]][condition]
                for c in family_cases
                if condition in case_means[c["case_id"]]
            ]
            condition_means[condition] = mean(xs)
        target = condition_means["TARGET"]
        control = condition_means["CONTROL"]
        attention = condition_means["ATTENTION"]
        target_control = target - control if target is not None and control is not None else None
        target_attention = target - attention if target is not None and attention is not None else None
        attention_control = attention - control if attention is not None and control is not None else None
        out[family] = {
            "condition_means": condition_means,
            "target_minus_control": target_control,
            "target_minus_attention": target_attention,
            "attention_minus_control": attention_control,
            "identification_gate": target_control is not None and target_control >= MANIPULATION_LIFT_GATE,
            "gate_threshold": MANIPULATION_LIFT_GATE,
            "case_means": {c["case_id"]: case_means[c["case_id"]] for c in family_cases},
        }
    return out


def quality_summary(votes: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for spec in PAIR_SPECS:
        rows = [v for v in votes if v["pair_id"] == spec["pair_id"]]
        by_family = {}
        for family in FAMILIES:
            subset = [v for v in rows if v["family"] == family]
            by_family[family] = v05.aggregate_pair(subset, spec) if subset else None
        out[spec["pair_id"]] = {
            "overall": v05.aggregate_pair(rows, spec) if rows else None,
            "by_family": by_family,
        }
    return out


def usage_totals(runs: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for condition in CONDITIONS:
        subset = [r for r in runs if r["condition"] == condition]
        out[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }
    return out


def main() -> None:
    out = ROOT / "results_v010"
    out.mkdir(exist_ok=True)
    runs: list[dict[str, Any]] = []
    behavior_votes: list[dict[str, Any]] = []
    quality_votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in CONDITIONS:
                print("generate", replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
                write_jsonl(out / "v010_runs.jsonl", runs)

    index = {
        (r["case_id"], r["condition"], r["replicate"]): r
        for r in runs
    }

    # Behavior scoring is independent/absolute. A behavior judge never sees two
    # conditions side by side; lifts are computed only after all scores exist.
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in CONDITIONS:
                run = index[(case["case_id"], condition, replicate)]
                for vote_index in range(1, BEHAVIOR_VOTES + 1):
                    print("behavior", replicate, case["case_id"], condition, vote_index, flush=True)
                    behavior_votes.append(absolute_behavior_vote(case, run, vote_index))
                    write_jsonl(out / "v010_behavior_votes.jsonl", behavior_votes)

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for spec in PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, QUALITY_VOTES + 1):
                    print("quality", replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    quality_votes.append(quality_vote(case, left, right, spec, vote_index))
                    write_jsonl(out / "v010_quality_votes.jsonl", quality_votes)

    behavior = behavior_summary(behavior_votes)
    quality = quality_summary(quality_votes)

    interpretation: dict[str, Any] = {}
    for family in FAMILIES:
        identified = behavior[family]["identification_gate"]
        primary = quality["TARGET_vs_CONTROL"]["by_family"][family]
        specificity = quality["TARGET_vs_ATTENTION"]["by_family"][family]
        interpretation[family] = {
            "behavior_identified": identified,
            "target_minus_control_behavior": behavior[family]["target_minus_control"],
            "target_minus_attention_behavior": behavior[family]["target_minus_attention"],
            "target_vs_control_quality_score": primary["score"] if primary else None,
            "target_vs_attention_quality_score": specificity["score"] if specificity else None,
            "capability_quality_interpretable": identified,
            "rule": (
                "Quality differences may be interpreted as instruction-mediated evidence because the independently scored absolute behavior manipulation passed."
                if identified
                else "Absolute behavior manipulation remained below the predeclared gate; quality differences are non-identifying for capability value."
            ),
        }

    report = {
        "measurement_version": "0.10-absolute-behavior-identification",
        "experiment_role": "development diagnostic, not held-out validation",
        "research_question": "Do explicit TEST and ENGINEER modules independently increase their intended behavior and, when they do, improve reasoning quality beyond CONTROL and generic ATTENTION?",
        "families": list(FAMILIES),
        "n_cases": len(CASES),
        "generation_replicates": GENERATION_REPLICATES,
        "behavior_votes_per_response": BEHAVIOR_VOTES,
        "quality_votes_per_pair": QUALITY_VOTES,
        "behavior_measurement": "independent absolute scoring; no behavior judge sees two conditions side by side",
        "manipulation_gate": f"family TARGET minus CONTROL absolute behavior >= {MANIPULATION_LIFT_GATE}/4",
        "behavior_results": behavior,
        "quality_results": quality,
        "family_interpretation": interpretation,
        "control_prompt": CONTROL,
        "attention_prompt": ATTENTION,
        "target_modules": TARGET_MODULES,
        "cost_diagnostics": usage_totals(runs),
        "provider": "z.ai",
        "target": {"model": v03.TARGET_MODEL, "base_url": v03.TARGET_BASE},
        "judge": {
            "model": v03.JUDGE_MODEL,
            "base_url": v03.JUDGE_BASE,
            "same_model_and_endpoint_as_target": (
                v03.TARGET_MODEL == v03.JUDGE_MODEL and v03.TARGET_BASE == v03.JUDGE_BASE
            ),
        },
        "notes": [
            "ENGINEER is a positive-control family whose module is frozen byte-for-byte from v0.7.",
            "TEST uses the existing explicit TEST module from v0.6 rather than wording tuned to v0.10 outcomes.",
            "User prompts do not explicitly ask for a test, experiment, engineering framework, or named reasoning stage.",
            "Quality judging remains pairwise and blinded; only behavior manipulation measurement changed to independent absolute scoring.",
            "All v0.10 cases are development cases and cannot serve as future held-out validation.",
        ],
    }
    (out / "v010_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
