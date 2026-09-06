#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

# Reuse v0.5's provider and repeated-vote aggregation infrastructure.
os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "stage_ablation_cases_v06.json").read_text(encoding="utf-8"))
GENERATION_REPLICATES = max(1, int(os.getenv("ABLATION_GENERATION_REPLICATES", "1")))
JUDGE_VOTES = int(os.getenv("ABLATION_JUDGE_VOTES", "3"))

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("ABLATION_JUDGE_VOTES must be an odd integer >= 3")

STAGE_ADDONS = {
    "DIAGNOSE": """\n\nAdditional capability — DIAGNOSE: When material causal ambiguity exists, explicitly maintain at least two materially plausible explanations long enough to compare them. Distinguish symptom, proximate cause, and root cause where relevant. Identify the smallest observation or test that would discriminate the leading explanations. Do not add remote possibilities merely for completeness.""",
    "PREDICT": """\n\nAdditional capability — PREDICT: Before using a proposed test outcome as evidence, derive concrete observable consequences that should differ across the leading mechanism(s). Make predictions prospective rather than post-hoc. Prefer predictions whose failure would weaken the favored mechanism.""",
    "TEST": """\n\nAdditional capability — TEST: Prefer evidence or experiments that can discriminate among mechanisms or falsify the favored explanation. State how materially different outcomes would update the diagnosis or decision. Do not treat a test as strong merely because it can confirm what is already believed.""",
    "REVISE": """\n\nAdditional capability — REVISE: When later evidence conflicts with an earlier causal model, explicitly identify what belief, assumption, or mechanism is being changed; demote explanations contradicted by the new evidence; update the recommendation accordingly; and preserve any remaining uncertainty rather than rationalizing the old model.""",
    "ENGINEER": """\n\nAdditional capability — ENGINEER: Once a mechanism is sufficiently supported, compare interventions by mechanism fit, constraints, robustness, reversibility, feasibility, feedback loops, side effects, second-order effects, and monitoring/rollback criteria. Prefer interventions that address the validated mechanism and avoid irreversible commitment when a reversible control can achieve the objective.""",
}

ATTENTION_ADDON = """\n\nAdditional control instruction: Before answering, perform one extra quality-control pass. Check for overlooked assumptions, internal contradictions, imprecise claims, and whether the recommendation actually follows from the supplied evidence. Improve precision where needed, but do not add analysis solely for completeness."""

ABLATION_JUDGE = r'''You are a strict blinded evaluator of REASONING QUALITY for a component-ablation experiment. Compare Response A and Response B using only the supplied case evidence and reference. You are not told which prompt condition produced either response.

The case reference names a target reasoning capability because the case was designed to stress that capability. Reward substantive success on the underlying reasoning requirement, not the use of that capability name, protocol terminology, headings, verbosity, or stylistic similarity to the reference.

Priority dimensions, when applicable:
1. factual correctness and faithful use of observations;
2. separation of observation, inference, assumption, and causal claim;
3. the case-specific target capability and whether it materially improves the epistemic or decision outcome;
4. causal/mechanistic accuracy and treatment of plausible alternatives;
5. discriminating evidence/tests and prospective consequences where relevant;
6. revision when later evidence contradicts an earlier model;
7. calibrated uncertainty and decision-critical assumptions;
8. correctness and robustness of the recommendation under constraints and second-order effects.

Do NOT reward an answer for being longer, more elaborate, or cheaper. If both responses are substantively equivalent on reasoning quality, return TIE.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"margin":0,"decisive_dimensions":["..."],"notes":"brief concrete reason"}
where margin is 0 for a tie, 1 for slight, 2 for clear, 3 for decisive.'''

PAIR_SPECS = [
    {"pair_id": "TARGETED_vs_COMPACT", "left": "TARGETED", "right": "COMPACT", "focal": "TARGETED", "role": "primary_component_effect"},
    {"pair_id": "TARGETED_vs_ATTENTION", "left": "TARGETED", "right": "ATTENTION", "focal": "TARGETED", "role": "stage_specificity"},
    {"pair_id": "FULL_vs_TARGETED", "left": "FULL", "right": "TARGETED", "focal": "FULL", "role": "residual_full_headroom"},
    {"pair_id": "ATTENTION_vs_COMPACT", "left": "ATTENTION", "right": "COMPACT", "focal": "ATTENTION", "role": "generic_attention_control"},
]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def system_for(case: dict[str, Any], condition: str) -> str | None:
    if condition == "COMPACT":
        return v03.pilot.COMPACT
    if condition == "ATTENTION":
        return v03.pilot.COMPACT + ATTENTION_ADDON
    if condition == "TARGETED":
        return v03.pilot.COMPACT + STAGE_ADDONS[case["family"]]
    if condition == "FULL":
        return v03.pilot.FULL
    raise ValueError(f"unknown condition: {condition}")


def run_case(case: dict[str, Any], condition: str, replicate: int) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    system = system_for(case, condition)
    messages: list[dict[str, str]] = []
    responses = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = v03.target_call(system, messages)
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


def ablation_reference(case: dict[str, Any]) -> dict[str, Any]:
    evaluator = case.get("evaluator_key", {})
    allowed = {
        "target_capability", "observations", "not_observed", "plausible_hypotheses",
        "critical_first_principles", "discriminating_evidence", "decision_critical_uncertainties",
        "constraints", "acceptable_interventions", "scoring_notes",
    }
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "case_reference": {k: v for k, v in evaluator.items() if k in allowed and v},
        "turn_references": [
            {"turn": t["turn"], "expected_revision": t.get("expected_revision")}
            for t in case["turns"]
        ],
    }


def judge_vote(case: dict[str, Any], run_x: dict[str, Any], run_y: dict[str, Any], spec: dict[str, str], vote_index: int) -> dict[str, Any]:
    seed_material = f"v06:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed_material).random() < 0.5:
        first, second = second, first

    last_turn = case["turns"][-1]["turn"]
    content = {
        **ablation_reference(case),
        "response_A": v03.transcript(case, first, last_turn),
        "response_B": v03.transcript(case, second, last_turn),
    }
    result = v03.judge_call(
        ABLATION_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid v0.6 judge result: {parsed}")

    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    focal = spec["focal"]
    focal_score = 0.5 if resolved == "TIE" else (1.0 if resolved == focal else 0.0)
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
        "focal_score": focal_score,
        "confidence": parsed.get("confidence"),
        "margin": parsed.get("margin"),
        "decisive_dimensions": parsed.get("decisive_dimensions", []),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def family_breakdown(votes: list[dict[str, Any]], spec: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for family in STAGE_ADDONS:
        subset = [v for v in votes if v["pair_id"] == spec["pair_id"] and v["family"] == family]
        if not subset:
            continue
        by_case: dict[str, list[dict[str, Any]]] = {}
        for vote in subset:
            by_case.setdefault(vote["case_id"], []).append(vote)
        rows = []
        for case_id, group in sorted(by_case.items()):
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
            rows.append({
                "case_id": case_id,
                "score": sum(v["focal_score"] for v in group) / len(group),
                "majority_winner": majority,
                "agreement": max(counts.values()) / len(group),
                "vote_counts": counts,
            })
        out[family] = {
            "n_cases": len(rows),
            "score": sum(r["score"] for r in rows) / len(rows),
            "majority_wins": sum(r["majority_winner"] == spec["focal"] for r in rows),
            "majority_ties": sum(r["majority_winner"] == "TIE" for r in rows),
            "majority_losses": sum(r["majority_winner"] not in {spec["focal"], "TIE"} for r in rows),
            "mean_vote_agreement": sum(r["agreement"] for r in rows) / len(rows),
            "cases": rows,
        }
    return out


def main() -> None:
    out = ROOT / "results_v06"
    out.mkdir(exist_ok=True)
    runs_path = out / "v06_runs.jsonl"
    votes_path = out / "v06_judge_votes.jsonl"
    runs: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []

    conditions = ["COMPACT", "ATTENTION", "TARGETED", "FULL"]
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in conditions:
                print("running", replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
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

    pair_results: dict[str, Any] = {}
    for spec in PAIR_SPECS:
        aggregate = v05.aggregate_pair(votes, spec)
        aggregate["by_family"] = family_breakdown(votes, spec)
        pair_results[spec["pair_id"]] = aggregate

    cost_diagnostics = {}
    for condition in conditions:
        subset = [r for r in runs if r["condition"] == condition]
        cost_diagnostics[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }

    report = {
        "measurement_version": "0.6-stage-ablation",
        "experiment_role": "component calibration, not held-out framework validation",
        "n_cases": len(CASES),
        "cases_per_stage": {family: sum(c["family"] == family for c in CASES) for family in STAGE_ADDONS},
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes_per_pair": JUDGE_VOTES,
        "primary_research_question": "Which additional reasoning capabilities add marginal reasoning quality beyond Compact?",
        "primary_metric": "TARGETED stage augmentation vs COMPACT on stage-relevant cases using repeated blinded quality-only votes",
        "control": "ATTENTION adds a generic extra quality-control pass without the target stage instruction",
        "pair_roles": {spec["pair_id"]: spec["role"] for spec in PAIR_SPECS},
        "cost_policy": "token and latency measurements are descriptive diagnostics only and do not enter quality judgments",
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
            "Each TARGETED condition is the identical Compact prompt plus exactly one stage-specific capability instruction.",
            "ATTENTION controls for the possibility that extra prompting or an extra checking pass improves quality without stage-specific content.",
            "FULL is retained only as a ceiling/headroom diagnostic, not as the stage-effect treatment.",
            "The v0.6 cases were designed for this ablation program and therefore are development/calibration cases, not future held-out validation cases.",
            "Validation still requires frozen prompts, fresh cases, generation replicates, and preferably an evaluator independent of the target model.",
        ],
    }
    (out / "v06_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
