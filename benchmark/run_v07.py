#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

# Reuse the hardened provider and repeated-vote aggregation infrastructure.
os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "capability_cases_v07.json").read_text(encoding="utf-8"))
GENERATION_REPLICATES = max(1, int(os.getenv("V07_GENERATION_REPLICATES", "3")))
JUDGE_VOTES = int(os.getenv("V07_JUDGE_VOTES", "3"))
MANIPULATION_LIFT_GATE = float(os.getenv("V07_MANIPULATION_LIFT_GATE", "0.5"))

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("V07_JUDGE_VOTES must be an odd integer >= 3")

CORE = """You are a careful reasoning agent. Use the supplied evidence faithfully. Separate what is observed from what is inferred. State important assumptions and uncertainty. Respect stated constraints. Give the next action or conclusion that is justified by the evidence. Do not mechanically emit a reasoning framework or reward verbosity."""

ATTENTION = CORE + " Before answering, perform one additional internal quality-control pass for overlooked facts, arithmetic mistakes, and unsupported claims."

TARGET_MODULES = {
    "DIAGNOSE": " Under material ambiguity, keep multiple materially plausible causal explanations alive, distinguish symptom, proximate cause, and root cause where useful, and prefer a next step that separates explanations before committing to one.",
    "REVISE": " When later evidence conflicts with an earlier causal model, explicitly change the model or confidence: state what is demoted or promoted and change the recommended action accordingly rather than merely appending the new fact.",
    "ENGINEER": " Once a mechanism is sufficiently supported, translate it into a robust action under constraints. Connect the action to the mechanism, compare reversible and irreversible options, define monitoring and rollback criteria, and account for important feedback or second-order effects without inventing unsupported causal certainty.",
}

QUALITY_JUDGE = r'''You are a strict blinded evaluator of REASONING QUALITY. Compare Response A and Response B for the same case using only the supplied evidence and reference. You are not told which experimental condition produced either response.

Judge substance, not style, prompt terminology, headings, verbosity, or token count.

Priority dimensions, when applicable:
1. factual and quantitative correctness;
2. faithful separation of observation, inference, assumption, and causal claim;
3. causal/mechanistic accuracy and treatment of materially plausible alternatives;
4. discriminating value of proposed evidence or checks;
5. appropriate response to later contradictory evidence;
6. calibrated uncertainty and exposure of decision-critical assumptions;
7. correctness and robustness of the recommended action under stated constraints and material second-order effects.

Do not reward length or a named reasoning pattern. If the responses are substantively equivalent, return TIE.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"margin":0,"decisive_dimensions":["..."],"notes":"brief concrete reason"}'''

BEHAVIOR_JUDGE = r'''You are a blinded evaluator of TARGET BEHAVIOR EXPRESSION only. Do not judge overall answer quality and do not infer which prompt produced a response.

You will receive one case-specific target_behavior definition plus Response A and Response B. Score each response from 0 to 4 for how strongly the defined behavior is actually expressed in the reasoning trajectory:
0 = absent or contrary behavior;
1 = weak/implicit;
2 = partial but incomplete;
3 = clear and materially relevant;
4 = strong, explicit, and decision-relevant.

Do not reward headings, jargon, verbosity, or merely repeating the user's wording. Score observable behavior in the response.

Return JSON only:
{"A_score":0,"B_score":0,"notes":"brief evidence for the scores"}'''

PAIR_SPECS = [
    {"pair_id": "TARGET_vs_CONTROL", "left": "TARGET", "right": "CONTROL", "focal": "TARGET", "role": "primary_instruction_effect"},
    {"pair_id": "TARGET_vs_ATTENTION", "left": "TARGET", "right": "ATTENTION", "focal": "TARGET", "role": "capability_specificity"},
    {"pair_id": "ATTENTION_vs_CONTROL", "left": "ATTENTION", "right": "CONTROL", "focal": "ATTENTION", "role": "generic_attention_control"},
]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def system_for(case: dict[str, Any], condition: str) -> str:
    if condition == "CONTROL":
        return CORE
    if condition == "ATTENTION":
        return ATTENTION
    if condition == "TARGET":
        return CORE + TARGET_MODULES[case["family"]]
    raise ValueError(f"unknown condition: {condition}")


def run_case(case: dict[str, Any], condition: str, replicate: int) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    messages: list[dict[str, str]] = []
    responses = []
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


def quality_reference(case: dict[str, Any]) -> dict[str, Any]:
    evaluator = case.get("evaluator_key", {})
    allowed = {
        "observations", "not_observed", "plausible_hypotheses", "critical_first_principles",
        "discriminating_evidence", "decision_critical_uncertainties", "constraints",
        "acceptable_interventions", "scoring_notes",
    }
    return {
        "case_id": case["case_id"],
        "case_reference": {k: v for k, v in evaluator.items() if k in allowed and v},
        "turn_references": [
            {"turn": t["turn"], "expected_revision": t.get("expected_revision")}
            for t in case["turns"]
        ],
    }


def quality_vote(case: dict[str, Any], run_x: dict[str, Any], run_y: dict[str, Any], spec: dict[str, str], vote_index: int) -> dict[str, Any]:
    seed_material = f"v07-quality:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed_material).random() < 0.5:
        first, second = second, first
    last_turn = case["turns"][-1]["turn"]
    content = {
        **quality_reference(case),
        "response_A": v03.transcript(case, first, last_turn),
        "response_B": v03.transcript(case, second, last_turn),
    }
    result = v03.judge_call(QUALITY_JUDGE, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid v0.7 quality result: {parsed}")
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


def behavior_check(case: dict[str, Any], target: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    seed_material = f"v07-behavior:{case['case_id']}:{target['replicate']}"
    first, second = target, control
    if random.Random(seed_material).random() < 0.5:
        first, second = second, first
    last_turn = case["turns"][-1]["turn"]
    content = {
        "case_id": case["case_id"],
        "target_behavior": case["evaluator_key"]["target_behavior"],
        "response_A": v03.transcript(case, first, last_turn),
        "response_B": v03.transcript(case, second, last_turn),
    }
    result = v03.judge_call(BEHAVIOR_JUDGE, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
    parsed = v03.parse_json(result["text"])
    a = parsed.get("A_score")
    b = parsed.get("B_score")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or not (0 <= float(a) <= 4 and 0 <= float(b) <= 4):
        raise RuntimeError(f"invalid v0.7 behavior result: {parsed}")
    scores = {first["condition"]: float(a), second["condition"]: float(b)}
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "replicate": target["replicate"],
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "target_score": scores["TARGET"],
        "control_score": scores["CONTROL"],
        "lift": scores["TARGET"] - scores["CONTROL"],
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def family_quality(votes: list[dict[str, Any]], spec: dict[str, str]) -> dict[str, Any]:
    out = {}
    for family in TARGET_MODULES:
        subset = [v for v in votes if v["family"] == family and v["pair_id"] == spec["pair_id"]]
        out[family] = v05.aggregate_pair(subset, spec) if subset else None
    return out


def manipulation_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for family in TARGET_MODULES:
        rows = [r for r in checks if r["family"] == family]
        target_mean = sum(r["target_score"] for r in rows) / len(rows)
        control_mean = sum(r["control_score"] for r in rows) / len(rows)
        lift = target_mean - control_mean
        by_case = {}
        for case_id in sorted({r["case_id"] for r in rows}):
            xs = [r for r in rows if r["case_id"] == case_id]
            by_case[case_id] = {
                "target_mean": sum(r["target_score"] for r in xs) / len(xs),
                "control_mean": sum(r["control_score"] for r in xs) / len(xs),
                "lift": sum(r["lift"] for r in xs) / len(xs),
            }
        out[family] = {
            "n_case_replicates": len(rows),
            "target_behavior_mean": target_mean,
            "control_behavior_mean": control_mean,
            "behavior_lift": lift,
            "identification_gate": lift >= MANIPULATION_LIFT_GATE,
            "gate_threshold": MANIPULATION_LIFT_GATE,
            "case_breakdown": by_case,
        }
    return out


def main() -> None:
    out = ROOT / "results_v07"
    out.mkdir(exist_ok=True)
    runs_path = out / "v07_runs.jsonl"
    votes_path = out / "v07_quality_votes.jsonl"
    behavior_path = out / "v07_behavior_checks.jsonl"
    runs: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []
    behavior: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in ["CONTROL", "ATTENTION", "TARGET"]:
                print("running", replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
                write_jsonl(runs_path, runs)

    index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            target = index[(case["case_id"], "TARGET", replicate)]
            control = index[(case["case_id"], "CONTROL", replicate)]
            print("behavior", replicate, case["case_id"], flush=True)
            behavior.append(behavior_check(case, target, control))
            write_jsonl(behavior_path, behavior)
            for spec in PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, JUDGE_VOTES + 1):
                    print("quality", replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    votes.append(quality_vote(case, left, right, spec, vote_index))
                    write_jsonl(votes_path, votes)

    manipulation = manipulation_summary(behavior)
    quality_results = {}
    for spec in PAIR_SPECS:
        quality_results[spec["pair_id"]] = {
            "overall": v05.aggregate_pair(votes, spec),
            "by_family": family_quality(votes, spec),
        }

    interpretation = {}
    primary = quality_results["TARGET_vs_CONTROL"]["by_family"]
    specificity = quality_results["TARGET_vs_ATTENTION"]["by_family"]
    for family in TARGET_MODULES:
        identified = manipulation[family]["identification_gate"]
        interpretation[family] = {
            "manipulation_identified": identified,
            "target_vs_control_quality_score": primary[family]["score"],
            "target_vs_attention_quality_score": specificity[family]["score"],
            "interpretation_rule": (
                "quality effects may be interpreted as instruction-mediated capability evidence"
                if identified else
                "weak manipulation: quality differences do not identify capability value"
            ),
        }

    cost_diagnostics = {}
    for condition in ["CONTROL", "ATTENTION", "TARGET"]:
        subset = [r for r in runs if r["condition"] == condition]
        cost_diagnostics[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }

    report = {
        "measurement_version": "0.7-manipulation-checked-capability-diagnostic",
        "experiment_role": "development diagnostic, not held-out validation",
        "n_cases": len(CASES),
        "families": list(TARGET_MODULES),
        "generation_replicates": GENERATION_REPLICATES,
        "quality_judge_votes_per_pair": JUDGE_VOTES,
        "primary_research_question": "Does an explicit target-capability instruction increase the target behavior, and if so does that induced behavior improve reasoning quality beyond a neutral core?",
        "conditions": {
            "CONTROL": "neutral reasoning core with no target-capability module",
            "ATTENTION": "CONTROL plus a generic extra quality-control pass",
            "TARGET": "CONTROL plus the family-specific capability module",
        },
        "identification_rule": f"Interpret quality effects as capability evidence only when TARGET minus CONTROL behavior lift is >= {MANIPULATION_LIFT_GATE} on the 0-4 behavior scale.",
        "quality_results": quality_results,
        "manipulation_checks": manipulation,
        "family_interpretation": interpretation,
        "cost_policy": "cost is descriptive only and does not enter quality or identification decisions",
        "provider": "z.ai",
        "target": {"model": v03.TARGET_MODEL, "base_url": v03.TARGET_BASE},
        "judge": {
            "model": v03.JUDGE_MODEL,
            "base_url": v03.JUDGE_BASE,
            "same_model_and_endpoint_as_target": v03.TARGET_MODEL == v03.JUDGE_MODEL and v03.TARGET_BASE == v03.JUDGE_BASE,
        },
        "notes": [
            "v0.6.1 showed that deleting an instruction fragment often did not remove the underlying behavior because the task itself or model priors still elicited it.",
            "v0.7 therefore separates manipulation strength (behavior expression) from outcome quality.",
            "The quality judge is not shown the target_behavior definition; the behavior judge is separate to reduce criterion contamination.",
            "Cases avoid explicit requests to diagnose, revise, or engineer; they ask only for the next action/conclusion after presenting evidence.",
            "These six cases are development diagnostics and must not be reused as fresh held-out validation after protocol tuning.",
        ],
    }
    (out / "v07_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
