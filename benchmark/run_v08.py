#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "capability_candidates_v08.json").read_text(encoding="utf-8"))

SCREEN_REPLICATES = max(1, int(os.getenv("V08_SCREEN_REPLICATES", "2")))
TEST_REPLICATES = max(1, int(os.getenv("V08_TEST_REPLICATES", "3")))
JUDGE_VOTES = int(os.getenv("V08_JUDGE_VOTES", "3"))
SCREEN_MAX_CONTROL = float(os.getenv("V08_SCREEN_MAX_CONTROL", "2.5"))
MIN_HEADROOM = float(os.getenv("V08_MIN_HEADROOM", "1.0"))
SELECT_PER_FAMILY = max(1, int(os.getenv("V08_SELECT_PER_FAMILY", "3")))
MIN_SELECTED = max(1, int(os.getenv("V08_MIN_SELECTED", "2")))
MANIPULATION_LIFT_GATE = float(os.getenv("V08_MANIPULATION_LIFT_GATE", "0.5"))

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("V08_JUDGE_VOTES must be an odd integer >= 3")

FAMILIES = ("DIAGNOSE", "REVISE")

CONTROL = (
    "Answer accurately and concisely using the evidence provided. "
    "Respect stated constraints and recommend the next action that is justified. "
    "Do not use a named reasoning framework."
)
ATTENTION = CONTROL + (
    " Before answering, perform one additional internal quality-control pass for overlooked facts, "
    "arithmetic mistakes, and unsupported claims."
)
TARGET_MODULES = {
    "DIAGNOSE": (
        " Under material ambiguity, keep multiple materially plausible causal explanations alive, "
        "distinguish symptom, proximate cause, and root cause where useful, and prefer a next step "
        "that separates explanations before committing to one."
    ),
    "REVISE": (
        " When later evidence conflicts with an earlier causal model, explicitly change the model "
        "or confidence: state what is demoted or promoted and change the recommended action accordingly "
        "rather than merely appending the new fact."
    ),
}

SCREEN_BEHAVIOR_JUDGE = r'''You are a blinded evaluator of TARGET BEHAVIOR EXPRESSION only.
Do not judge overall answer quality and do not infer which prompt produced the response.

You will receive one case-specific target_behavior definition and one response trajectory.
Score the response from 0 to 4 for how strongly the defined behavior is actually expressed:
0 = absent or contrary behavior;
1 = weak/implicit;
2 = partial but incomplete;
3 = clear and materially relevant;
4 = strong, explicit, and decision-relevant.

Do not reward headings, jargon, verbosity, or merely repeating the user's wording.
Return JSON only:
{"score":0,"notes":"brief evidence for the score"}'''

PAIR_BEHAVIOR_JUDGE = r'''You are a blinded evaluator of TARGET BEHAVIOR EXPRESSION only.
Do not judge overall answer quality and do not infer which prompt produced either response.

You will receive one case-specific target_behavior definition plus Response A and Response B.
Score each response from 0 to 4 for how strongly the defined behavior is actually expressed:
0 = absent or contrary behavior;
1 = weak/implicit;
2 = partial but incomplete;
3 = clear and materially relevant;
4 = strong, explicit, and decision-relevant.

Do not reward headings, jargon, verbosity, or merely repeating the user's wording.
Return JSON only:
{"A_score":0,"B_score":0,"notes":"brief evidence for the scores"}'''

QUALITY_JUDGE = r'''You are a strict blinded evaluator of REASONING QUALITY.
Compare Response A and Response B for the same case using only the supplied evidence and reference.
You are not told which experimental condition produced either response.

Judge substance, not style, prompt terminology, headings, verbosity, or token count.

Priority dimensions, when applicable:
1. factual and quantitative correctness;
2. faithful separation of evidence from unsupported causal claims;
3. causal/mechanistic accuracy and treatment of materially plausible alternatives;
4. discriminating value of proposed evidence or checks;
5. appropriate response to later contradictory evidence;
6. calibrated uncertainty and exposure of decision-critical assumptions;
7. correctness and robustness of the recommended action under stated constraints.

Do not reward length or a named reasoning pattern. If the responses are substantively equivalent, return TIE.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"margin":0,"decisive_dimensions":["..."],"notes":"brief concrete reason"}'''

PAIR_SPECS = [
    {"pair_id": "TARGET_vs_CONTROL", "left": "TARGET", "right": "CONTROL", "focal": "TARGET", "role": "primary_instruction_effect"},
    {"pair_id": "TARGET_vs_ATTENTION", "left": "TARGET", "right": "ATTENTION", "focal": "TARGET", "role": "capability_specificity"},
    {"pair_id": "ATTENTION_vs_CONTROL", "left": "ATTENTION", "right": "CONTROL", "focal": "ATTENTION", "role": "generic_attention_control"},
]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def transcript(case: dict[str, Any], run: dict[str, Any]) -> str:
    return v03.transcript(case, run, case["turns"][-1]["turn"])


def system_for(case: dict[str, Any], condition: str) -> str:
    if condition == "CONTROL":
        return CONTROL
    if condition == "ATTENTION":
        return ATTENTION
    if condition == "TARGET":
        return CONTROL + TARGET_MODULES[case["family"]]
    raise ValueError(condition)


def generate(case: dict[str, Any], condition: str, replicate: int, phase: str) -> dict[str, Any]:
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
        "phase": phase,
        "condition": condition,
        "replicate": replicate,
        "responses": responses,
        "usage": usage,
    }


def score_screen_behavior(case: dict[str, Any], run: dict[str, Any], vote_index: int) -> dict[str, Any]:
    content = {
        "case_id": case["case_id"],
        "target_behavior": case["evaluator_key"]["target_behavior"],
        "response": transcript(case, run),
    }
    result = v03.judge_call(
        SCREEN_BEHAVIOR_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    score = parsed.get("score")
    if not isinstance(score, (int, float)) or not 0 <= float(score) <= 4:
        raise RuntimeError(f"invalid screen behavior score: {parsed}")
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "screen_replicate": run["replicate"],
        "vote_index": vote_index,
        "score": float(score),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def select_cases(screen_votes: list[dict[str, Any]]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for family in FAMILIES:
        candidates = []
        family_ids = sorted({v["case_id"] for v in screen_votes if v["family"] == family})
        for case_id in family_ids:
            rows = [v for v in screen_votes if v["case_id"] == case_id]
            mean = sum(v["score"] for v in rows) / len(rows)
            headroom = 4.0 - mean
            eligible = mean <= SCREEN_MAX_CONTROL and headroom >= MIN_HEADROOM
            candidates.append(
                {
                    "case_id": case_id,
                    "control_behavior_mean": mean,
                    "headroom": headroom,
                    "eligible": eligible,
                    "n_votes": len(rows),
                }
            )
        eligible_rows = sorted(
            [r for r in candidates if r["eligible"]],
            key=lambda r: (r["control_behavior_mean"], r["case_id"]),
        )
        chosen = [r["case_id"] for r in eligible_rows[:SELECT_PER_FAMILY]]
        selected[family] = {
            "candidates": candidates,
            "selected_case_ids": chosen,
            "proceed": len(chosen) >= MIN_SELECTED,
            "required_minimum": MIN_SELECTED,
            "selection_rule": (
                f"CONTROL behavior mean <= {SCREEN_MAX_CONTROL}, headroom >= {MIN_HEADROOM}, "
                f"then choose up to {SELECT_PER_FAMILY} lowest-baseline cases"
            ),
        }
    return selected


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


def behavior_vote(
    case: dict[str, Any],
    target: dict[str, Any],
    control: dict[str, Any],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"v08-behavior:{case['case_id']}:{target['replicate']}:{vote_index}"
    first, second = target, control
    if random.Random(seed).random() < 0.5:
        first, second = second, first
    content = {
        "case_id": case["case_id"],
        "target_behavior": case["evaluator_key"]["target_behavior"],
        "response_A": transcript(case, first),
        "response_B": transcript(case, second),
    }
    result = v03.judge_call(
        PAIR_BEHAVIOR_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    a, b = parsed.get("A_score"), parsed.get("B_score")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise RuntimeError(f"invalid behavior result: {parsed}")
    if not (0 <= float(a) <= 4 and 0 <= float(b) <= 4):
        raise RuntimeError(f"behavior score out of range: {parsed}")
    scores = {first["condition"]: float(a), second["condition"]: float(b)}
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "replicate": target["replicate"],
        "vote_index": vote_index,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "target_score": scores["TARGET"],
        "control_score": scores["CONTROL"],
        "lift": scores["TARGET"] - scores["CONTROL"],
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def quality_vote(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"v08-quality:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
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


def manipulation_summary(votes: list[dict[str, Any]], selection: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for family in FAMILIES:
        rows = [v for v in votes if v["family"] == family]
        if not selection[family]["proceed"] or not rows:
            out[family] = {
                "status": "insufficient_manipulation_capacity",
                "identification_gate": False,
                "behavior_lift": None,
            }
            continue
        target_mean = sum(v["target_score"] for v in rows) / len(rows)
        control_mean = sum(v["control_score"] for v in rows) / len(rows)
        lift = target_mean - control_mean
        out[family] = {
            "status": "tested",
            "n_behavior_votes": len(rows),
            "target_behavior_mean": target_mean,
            "control_behavior_mean": control_mean,
            "behavior_lift": lift,
            "identification_gate": lift >= MANIPULATION_LIFT_GATE,
            "gate_threshold": MANIPULATION_LIFT_GATE,
        }
    return out


def aggregate_quality(
    votes: list[dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for spec in PAIR_SPECS:
        by_family = {}
        all_rows = []
        for family in FAMILIES:
            rows = [
                v for v in votes
                if v["family"] == family and v["pair_id"] == spec["pair_id"]
            ]
            all_rows.extend(rows)
            by_family[family] = (
                v05.aggregate_pair(rows, spec)
                if selection[family]["proceed"] and rows
                else None
            )
        result[spec["pair_id"]] = {
            "overall": v05.aggregate_pair(all_rows, spec) if all_rows else None,
            "by_family": by_family,
        }
    return result


def usage_totals(runs: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for condition in sorted({r["condition"] for r in runs}):
        subset = [r for r in runs if r["condition"] == condition]
        out[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }
    return out


def main() -> None:
    out = ROOT / "results_v08"
    out.mkdir(exist_ok=True)

    screen_runs: list[dict[str, Any]] = []
    screen_votes: list[dict[str, Any]] = []
    test_runs: list[dict[str, Any]] = []
    behavior_votes: list[dict[str, Any]] = []
    quality_votes: list[dict[str, Any]] = []

    # Stage 1: CONTROL-only manipulation-capacity screen.
    for replicate in range(1, SCREEN_REPLICATES + 1):
        for case in CASES:
            print("screen generate", replicate, case["case_id"], flush=True)
            run = generate(case, "CONTROL", replicate, "screen")
            screen_runs.append(run)
            write_jsonl(out / "v08_screen_runs.jsonl", screen_runs)
            for vote_index in range(1, JUDGE_VOTES + 1):
                print("screen behavior", replicate, case["case_id"], vote_index, flush=True)
                screen_votes.append(score_screen_behavior(case, run, vote_index))
                write_jsonl(out / "v08_screen_behavior_votes.jsonl", screen_votes)

    selection = select_cases(screen_votes)
    (out / "v08_selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    case_by_id = {c["case_id"]: c for c in CASES}
    selected_cases = []
    for family in FAMILIES:
        if selection[family]["proceed"]:
            selected_cases.extend(case_by_id[cid] for cid in selection[family]["selected_case_ids"])

    # Stage 2: entirely fresh generations, only after selection is frozen.
    for replicate in range(1, TEST_REPLICATES + 1):
        for case in selected_cases:
            for condition in ("CONTROL", "ATTENTION", "TARGET"):
                print("test generate", replicate, case["case_id"], condition, flush=True)
                test_runs.append(generate(case, condition, replicate, "test"))
                write_jsonl(out / "v08_test_runs.jsonl", test_runs)

    index = {
        (r["case_id"], r["condition"], r["replicate"]): r
        for r in test_runs
    }
    for replicate in range(1, TEST_REPLICATES + 1):
        for case in selected_cases:
            target = index[(case["case_id"], "TARGET", replicate)]
            control = index[(case["case_id"], "CONTROL", replicate)]
            for vote_index in range(1, JUDGE_VOTES + 1):
                print("test behavior", replicate, case["case_id"], vote_index, flush=True)
                behavior_votes.append(behavior_vote(case, target, control, vote_index))
                write_jsonl(out / "v08_behavior_votes.jsonl", behavior_votes)

            for spec in PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, JUDGE_VOTES + 1):
                    print("test quality", replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    quality_votes.append(quality_vote(case, left, right, spec, vote_index))
                    write_jsonl(out / "v08_quality_votes.jsonl", quality_votes)

    manipulation = manipulation_summary(behavior_votes, selection)
    quality = aggregate_quality(quality_votes, selection)

    interpretation = {}
    for family in FAMILIES:
        if not selection[family]["proceed"]:
            interpretation[family] = {
                "status": "insufficient_manipulation_capacity",
                "capability_quality_interpretable": False,
                "reason": "Fewer than the predeclared minimum eligible low-baseline cases passed Stage 1.",
            }
            continue
        identified = manipulation[family]["identification_gate"]
        primary = quality["TARGET_vs_CONTROL"]["by_family"][family]
        specificity = quality["TARGET_vs_ATTENTION"]["by_family"][family]
        interpretation[family] = {
            "status": "identified" if identified else "manipulation_failed",
            "capability_quality_interpretable": identified,
            "behavior_lift": manipulation[family]["behavior_lift"],
            "target_vs_control_quality_score": primary["score"] if primary else None,
            "target_vs_attention_quality_score": specificity["score"] if specificity else None,
            "rule": (
                "Quality effects may be interpreted as instruction-mediated capability evidence."
                if identified
                else "Behavior manipulation remained too weak; quality differences are non-identifying."
            ),
        }

    report = {
        "measurement_version": "0.8-two-stage-capability-identification",
        "experiment_role": "development diagnostic, not held-out validation",
        "families": list(FAMILIES),
        "n_candidate_cases": len(CASES),
        "screen_replicates": SCREEN_REPLICATES,
        "test_replicates": TEST_REPLICATES,
        "judge_votes": JUDGE_VOTES,
        "screening": selection,
        "manipulation_checks": manipulation,
        "quality_results": quality,
        "family_interpretation": interpretation,
        "screen_control_prompt": CONTROL,
        "attention_prompt": ATTENTION,
        "target_modules": TARGET_MODULES,
        "identification_rule": (
            f"Family quality is interpretable only if Stage 1 selects at least {MIN_SELECTED} "
            f"cases and Stage 2 TARGET minus CONTROL behavior lift >= {MANIPULATION_LIFT_GATE}."
        ),
        "selection_integrity": [
            "Stage 1 observes CONTROL generations and behavior scores only.",
            "TARGET responses and all quality outcomes are generated only after selection is frozen.",
            "Stage 1 generations are never reused in Stage 2.",
        ],
        "cost_diagnostics": {
            "screen": usage_totals(screen_runs),
            "test": usage_totals(test_runs) if test_runs else {},
        },
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
            "ENGINEER is intentionally excluded and remains frozen after the positive identified v0.7 result.",
            "TEST and PREDICT are not modified or retested here.",
            "Candidate cases are development-screened and cannot serve as fresh held-out validation.",
            "Failure to find low-baseline cases is itself an empirical result about model priors and experimental manipulability.",
        ],
    }
    (out / "v08_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
