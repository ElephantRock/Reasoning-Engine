#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

# Reuse v0.5 provider and repeated-vote aggregation infrastructure.
os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "stage_ablation_cases_v06.json").read_text(encoding="utf-8"))
GENERATION_REPLICATES = max(1, int(os.getenv("ABLATION_GENERATION_REPLICATES", "1")))
JUDGE_VOTES = int(os.getenv("ABLATION_JUDGE_VOTES", "3"))

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("ABLATION_JUDGE_VOTES must be an odd integer >= 3")

# Each ablation starts from the exact production FULL prompt and removes only
# the instruction(s) belonging to the named capability cluster. This directly
# addresses the v0.6 identification defect where Compact already contained
# Test/Revise/Engineer behavior.
REMOVALS = {
    "DIAGNOSE": [
        "Generate multiple plausible explanations under material ambiguity. ",
        "Distinguish symptoms, proximate causes, and root causes. ",
    ],
    "PREDICT": [
        " derive observable predictions and",
    ],
    "TEST": [
        " and prefer discriminating/falsifying tests",
    ],
    "REVISE": [
        "Contradictions require model revision. ",
    ],
    "ENGINEER": [
        "Engineer only after sufficient understanding; compare effectiveness, robustness, cost, risk, reversibility, feasibility, constraints, feedback loops, side effects, and second-order effects. ",
        "After intervention, predict and observe outcomes. ",
    ],
}


def ablated_full_prompt(family: str) -> str:
    prompt = v03.pilot.FULL
    for fragment in REMOVALS[family]:
        if fragment not in prompt:
            raise RuntimeError(f"ablation fragment not found for {family}: {fragment!r}")
        prompt = prompt.replace(fragment, "", 1)
    return prompt


# Fail fast if any production prompt edit makes the ablation definitions stale.
for _family in REMOVALS:
    _ = ablated_full_prompt(_family)

ABLATION_JUDGE = r'''You are a strict blinded evaluator of REASONING QUALITY for a leave-one-capability-out experiment. Compare Response A and Response B using only the supplied evidence and reference. You are not told which prompt produced either response.

The experiment asks whether removing one reasoning capability from an otherwise identical full reasoning protocol degrades substantive reasoning quality on cases designed to stress that capability. Judge the actual reasoning outcome, not stage names, protocol terminology, headings, verbosity, or stylistic similarity to the reference.

Priority dimensions, when applicable:
1. factual correctness and faithful use of observations;
2. separation of observation, inference, assumption, and causal claim;
3. the case-specific target capability and whether it changes the epistemic or decision outcome;
4. causal/mechanistic accuracy and treatment of materially plausible alternatives;
5. discriminating evidence/tests and prospective consequences where relevant;
6. explicit model revision when later evidence contradicts an earlier model;
7. calibrated uncertainty and exposure of decision-critical assumptions;
8. correctness and robustness of the recommendation under constraints and second-order effects.

Do NOT reward length or cost. If the responses are substantively equivalent on reasoning quality, return TIE.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"margin":0,"decisive_dimensions":["..."],"notes":"brief concrete reason"}
where margin is 0 for a tie, 1 for slight, 2 for clear, 3 for decisive.'''

PAIR_SPEC = {
    "pair_id": "FULL_vs_ABLATED",
    "left": "FULL",
    "right": "ABLATED",
    "focal": "FULL",
    "role": "leave_one_stage_out_effect",
}


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def system_for(case: dict[str, Any], condition: str) -> str:
    if condition == "FULL":
        return v03.pilot.FULL
    if condition == "ABLATED":
        return ablated_full_prompt(case["family"])
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


def judge_vote(case: dict[str, Any], full: dict[str, Any], ablated: dict[str, Any], vote_index: int) -> dict[str, Any]:
    seed_material = f"v061:{case['case_id']}:{full['replicate']}:{vote_index}"
    first, second = full, ablated
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
        raise RuntimeError(f"invalid v0.6.1 judge result: {parsed}")

    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    focal_score = 0.5 if resolved == "TIE" else (1.0 if resolved == "FULL" else 0.0)
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "replicate": full["replicate"],
        "pair_id": PAIR_SPEC["pair_id"],
        "pair_role": PAIR_SPEC["role"],
        "focal_condition": "FULL",
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


def family_breakdown(votes: list[dict[str, Any]]) -> dict[str, Any]:
    # Preserve replicate boundaries when estimating judge agreement, then
    # average replicate scores within case before family-level means.
    out: dict[str, Any] = {}
    for family in REMOVALS:
        subset = [v for v in votes if v["family"] == family]
        if not subset:
            continue

        by_case_rep: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for vote in subset:
            by_case_rep.setdefault((vote["case_id"], vote["replicate"]), []).append(vote)

        replicate_rows = []
        for (case_id, replicate), group in sorted(by_case_rep.items()):
            counts = {
                "FULL": sum(v["winner"] == "FULL" for v in group),
                "ABLATED": sum(v["winner"] == "ABLATED" for v in group),
                "TIE": sum(v["winner"] == "TIE" for v in group),
            }
            if counts["FULL"] > counts["ABLATED"]:
                majority = "FULL"
            elif counts["ABLATED"] > counts["FULL"]:
                majority = "ABLATED"
            else:
                majority = "TIE"
            replicate_rows.append({
                "case_id": case_id,
                "replicate": replicate,
                "score": sum(v["focal_score"] for v in group) / len(group),
                "majority_winner": majority,
                "agreement": max(counts.values()) / len(group),
                "vote_counts": counts,
            })

        by_case: dict[str, list[dict[str, Any]]] = {}
        for row in replicate_rows:
            by_case.setdefault(row["case_id"], []).append(row)
        case_rows = []
        for case_id, rows in sorted(by_case.items()):
            case_rows.append({
                "case_id": case_id,
                "score": sum(r["score"] for r in rows) / len(rows),
                "replicates": rows,
            })

        out[family] = {
            "n_cases": len(case_rows),
            "n_case_replicates": len(replicate_rows),
            "score": sum(r["score"] for r in case_rows) / len(case_rows),
            "mean_vote_agreement": sum(r["agreement"] for r in replicate_rows) / len(replicate_rows),
            "case_scores": {r["case_id"]: r["score"] for r in case_rows},
            "case_replicates": replicate_rows,
        }
    return out


def main() -> None:
    out = ROOT / "results_v061"
    out.mkdir(exist_ok=True)
    runs_path = out / "v061_runs.jsonl"
    votes_path = out / "v061_judge_votes.jsonl"
    runs: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in ["FULL", "ABLATED"]:
                print("running", replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
                write_jsonl(runs_path, runs)

    index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            full = index[(case["case_id"], "FULL", replicate)]
            ablated = index[(case["case_id"], "ABLATED", replicate)]
            for vote_index in range(1, JUDGE_VOTES + 1):
                print("judging", replicate, case["case_id"], vote_index, flush=True)
                votes.append(judge_vote(case, full, ablated, vote_index))
                write_jsonl(votes_path, votes)

    overall = v05.aggregate_pair(votes, PAIR_SPEC)
    overall["by_family"] = family_breakdown(votes)

    cost_diagnostics = {}
    for condition in ["FULL", "ABLATED"]:
        subset = [r for r in runs if r["condition"] == condition]
        cost_diagnostics[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }

    report = {
        "measurement_version": "0.6.1-leave-one-stage-out",
        "experiment_role": "corrected component calibration, not held-out validation",
        "supersedes": "v0.6 TARGETED-vs-COMPACT identification for component-effect claims",
        "n_cases": len(CASES),
        "cases_per_stage": {family: sum(c["family"] == family for c in CASES) for family in REMOVALS},
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes_per_pair": JUDGE_VOTES,
        "primary_research_question": "Does removing a named capability from the otherwise identical FULL protocol reduce reasoning quality on capability-relevant cases?",
        "primary_metric": "FULL vs FULL-minus-stage using repeated blinded quality-only votes, clustered by case",
        "ablation_definition": {family: REMOVALS[family] for family in REMOVALS},
        "cost_policy": "token and latency measurements are descriptive diagnostics only",
        "provider": "z.ai",
        "target": {"model": v03.TARGET_MODEL, "base_url": v03.TARGET_BASE},
        "judge": {
            "model": v03.JUDGE_MODEL,
            "base_url": v03.JUDGE_BASE,
            "same_model_and_endpoint_as_target": v03.TARGET_MODEL == v03.JUDGE_MODEL and v03.TARGET_BASE == v03.JUDGE_BASE,
        },
        "quality_result": overall,
        "cost_diagnostics": cost_diagnostics,
        "notes": [
            "FULL is the exact production pilot.FULL prompt.",
            "ABLATED starts from that exact string and removes only the instruction fragment(s) assigned to the case family.",
            "Family statistics preserve (case_id, replicate) boundaries so judge disagreement is not conflated with generation variability.",
            "The v0.6 development cases were designed for this program, so results are calibration rather than held-out framework validation.",
            "Independent evaluator models and fresh frozen held-out cases remain required before validation claims.",
        ],
    }
    (out / "v061_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
