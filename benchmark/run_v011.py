#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402
import run_v010 as v010  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "capability_cases_v011.json").read_text(encoding="utf-8"))

GENERATION_REPLICATES = max(1, int(os.getenv("V011_GENERATION_REPLICATES", "3")))
FIDELITY_VOTES = int(os.getenv("V011_FIDELITY_VOTES", "3"))
QUALITY_VOTES = int(os.getenv("V011_QUALITY_VOTES", "3"))
FIDELITY_LIFT_GATE = float(os.getenv("V011_FIDELITY_LIFT_GATE", "0.15"))

for name, value in (("V011_FIDELITY_VOTES", FIDELITY_VOTES), ("V011_QUALITY_VOTES", QUALITY_VOTES)):
    if value < 3 or value % 2 == 0:
        raise ValueError(f"{name} must be an odd integer >= 3")

FAMILIES = ("TEST", "ENGINEER")
CONDITIONS = ("CONTROL", "ATTENTION", "TARGET")
CONTROL = v010.CONTROL
ATTENTION = v010.ATTENTION
TARGET_MODULES = dict(v010.TARGET_MODULES)
PAIR_SPECS = list(v010.PAIR_SPECS)
QUALITY_JUDGE = v010.QUALITY_JUDGE

FIDELITY_JUDGE = r'''You are a blinded evaluator of TARGET-BEHAVIOR FIDELITY only. You will receive one response and exactly five observable criteria for a reasoning capability. Do not judge overall answer quality, style, verbosity, or whether the response uses named reasoning terminology. Do not infer which prompt condition produced the response.

For each criterion, score only the observable response behavior:
- 0.0 = absent, contrary, or materially unusable;
- 0.5 = partial, implicit, incomplete, or weakly decision-relevant;
- 1.0 = clear, substantively complete, and decision-relevant.

Treat the criteria independently. A response may clearly perform the broad capability while still receiving partial credit on specific fidelity criteria. Do not force high scores merely because the overall answer seems competent.

Return JSON only:
{"scores":[{"id":"...","score":0.0}],"notes":"brief evidence tied to the criteria"}
The scores array must contain exactly one entry for every supplied criterion id.'''


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


def fidelity_vote(case: dict[str, Any], run: dict[str, Any], vote_index: int) -> dict[str, Any]:
    criteria = case["evaluator_key"]["fidelity_criteria"]
    content = {
        "case_id": case["case_id"],
        "capability_description": case["evaluator_key"]["target_behavior"],
        "criteria": criteria,
        "response": transcript(case, run),
    }
    result = v03.judge_call(
        FIDELITY_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    rows = parsed.get("scores")
    if not isinstance(rows, list):
        raise RuntimeError(f"invalid fidelity result: {parsed}")
    expected = [c["id"] for c in criteria]
    found: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError(f"invalid fidelity row: {parsed}")
        cid = row.get("id")
        score = row.get("score")
        if cid not in expected or cid in found:
            raise RuntimeError(f"invalid/duplicate fidelity criterion: {parsed}")
        if not isinstance(score, (int, float)) or float(score) not in {0.0, 0.5, 1.0}:
            raise RuntimeError(f"invalid fidelity score: {parsed}")
        found[cid] = float(score)
    if set(found) != set(expected):
        raise RuntimeError(f"missing fidelity criterion: {parsed}")
    composite = sum(found.values()) / len(expected)
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "condition": run["condition"],
        "replicate": run["replicate"],
        "vote_index": vote_index,
        "criterion_scores": found,
        "composite": composite,
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
    seed = f"v011-quality:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
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


def fidelity_summary(votes: list[dict[str, Any]]) -> dict[str, Any]:
    # votes -> exact response -> case -> family, preserving generation/case boundaries.
    response_rows: dict[tuple[str, str, int], dict[str, Any]] = {}
    for case in CASES:
        ids = [c["id"] for c in case["evaluator_key"]["fidelity_criteria"]]
        for condition in CONDITIONS:
            for replicate in range(1, GENERATION_REPLICATES + 1):
                rows = [
                    v for v in votes
                    if v["case_id"] == case["case_id"]
                    and v["condition"] == condition
                    and v["replicate"] == replicate
                ]
                if not rows:
                    continue
                response_rows[(case["case_id"], condition, replicate)] = {
                    "composite": sum(v["composite"] for v in rows) / len(rows),
                    "criteria": {
                        cid: sum(v["criterion_scores"][cid] for v in rows) / len(rows)
                        for cid in ids
                    },
                }

    case_rows: dict[str, dict[str, Any]] = {}
    for case in CASES:
        ids = [c["id"] for c in case["evaluator_key"]["fidelity_criteria"]]
        case_rows[case["case_id"]] = {}
        for condition in CONDITIONS:
            rows = [
                response_rows[(case["case_id"], condition, rep)]
                for rep in range(1, GENERATION_REPLICATES + 1)
                if (case["case_id"], condition, rep) in response_rows
            ]
            if not rows:
                continue
            case_rows[case["case_id"]][condition] = {
                "composite": sum(r["composite"] for r in rows) / len(rows),
                "criteria": {cid: sum(r["criteria"][cid] for r in rows) / len(rows) for cid in ids},
            }

    out: dict[str, Any] = {}
    for family in FAMILIES:
        family_cases = [c for c in CASES if c["family"] == family]
        ids = [c["id"] for c in family_cases[0]["evaluator_key"]["fidelity_criteria"]]
        condition_means: dict[str, float | None] = {}
        criterion_condition_means: dict[str, dict[str, float | None]] = {cid: {} for cid in ids}
        for condition in CONDITIONS:
            composites = [
                case_rows[c["case_id"]][condition]["composite"]
                for c in family_cases if condition in case_rows[c["case_id"]]
            ]
            condition_means[condition] = mean(composites)
            for cid in ids:
                xs = [
                    case_rows[c["case_id"]][condition]["criteria"][cid]
                    for c in family_cases if condition in case_rows[c["case_id"]]
                ]
                criterion_condition_means[cid][condition] = mean(xs)

        target = condition_means["TARGET"]
        control = condition_means["CONTROL"]
        attention = condition_means["ATTENTION"]
        target_control = target - control if target is not None and control is not None else None
        target_attention = target - attention if target is not None and attention is not None else None
        attention_control = attention - control if attention is not None and control is not None else None
        criterion_deltas = {
            cid: {
                "target_minus_control": (
                    criterion_condition_means[cid]["TARGET"] - criterion_condition_means[cid]["CONTROL"]
                    if criterion_condition_means[cid]["TARGET"] is not None and criterion_condition_means[cid]["CONTROL"] is not None
                    else None
                ),
                "target_minus_attention": (
                    criterion_condition_means[cid]["TARGET"] - criterion_condition_means[cid]["ATTENTION"]
                    if criterion_condition_means[cid]["TARGET"] is not None and criterion_condition_means[cid]["ATTENTION"] is not None
                    else None
                ),
            }
            for cid in ids
        }
        out[family] = {
            "condition_means": condition_means,
            "target_minus_control": target_control,
            "target_minus_attention": target_attention,
            "attention_minus_control": attention_control,
            "identification_gate": target_control is not None and target_control >= FIDELITY_LIFT_GATE,
            "gate_threshold": FIDELITY_LIFT_GATE,
            "criterion_condition_means": criterion_condition_means,
            "criterion_deltas": criterion_deltas,
            "case_means": {c["case_id"]: case_rows[c["case_id"]] for c in family_cases},
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
    return v010.usage_totals(runs)


def main() -> None:
    out = ROOT / "results_v011"
    out.mkdir(exist_ok=True)
    runs: list[dict[str, Any]] = []
    fidelity_votes: list[dict[str, Any]] = []
    quality_votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in CONDITIONS:
                print("generate", replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
                write_jsonl(out / "v011_runs.jsonl", runs)

    index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in CONDITIONS:
                run = index[(case["case_id"], condition, replicate)]
                for vote_index in range(1, FIDELITY_VOTES + 1):
                    print("fidelity", replicate, case["case_id"], condition, vote_index, flush=True)
                    fidelity_votes.append(fidelity_vote(case, run, vote_index))
                    write_jsonl(out / "v011_fidelity_votes.jsonl", fidelity_votes)

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for spec in PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, QUALITY_VOTES + 1):
                    print("quality", replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    quality_votes.append(quality_vote(case, left, right, spec, vote_index))
                    write_jsonl(out / "v011_quality_votes.jsonl", quality_votes)

    fidelity = fidelity_summary(fidelity_votes)
    quality = quality_summary(quality_votes)

    interpretation: dict[str, Any] = {}
    for family in FAMILIES:
        identified = fidelity[family]["identification_gate"]
        primary = quality["TARGET_vs_CONTROL"]["by_family"][family]
        specificity = quality["TARGET_vs_ATTENTION"]["by_family"][family]
        interpretation[family] = {
            "fidelity_identified": identified,
            "target_minus_control_fidelity": fidelity[family]["target_minus_control"],
            "target_minus_attention_fidelity": fidelity[family]["target_minus_attention"],
            "target_vs_control_quality_score": primary["score"] if primary else None,
            "target_vs_attention_quality_score": specificity["score"] if specificity else None,
            "capability_quality_interpretable": identified,
            "rule": (
                "Quality differences may be interpreted as instruction-mediated evidence because the independently scored behavioral-fidelity manipulation passed."
                if identified
                else "Behavioral-fidelity manipulation remained below the predeclared gate; quality differences are non-identifying for capability value."
            ),
        }

    report = {
        "measurement_version": "0.11-behavioral-fidelity-identification",
        "experiment_role": "development diagnostic, not held-out validation",
        "research_question": "Do explicit TEST and ENGINEER modules improve execution fidelity of their observable sub-behaviors, and when they do, does reasoning quality improve beyond CONTROL and generic ATTENTION?",
        "families": list(FAMILIES),
        "n_cases": len(CASES),
        "generation_replicates": GENERATION_REPLICATES,
        "fidelity_votes_per_response": FIDELITY_VOTES,
        "quality_votes_per_pair": QUALITY_VOTES,
        "fidelity_measurement": "five independently scored observable criteria per response; no fidelity judge sees two conditions side by side",
        "fidelity_gate": f"family TARGET minus CONTROL composite fidelity >= {FIDELITY_LIFT_GATE:.2f} on a 0-1 scale",
        "fidelity_results": fidelity,
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
            "same_model_and_endpoint_as_target": v03.TARGET_MODEL == v03.JUDGE_MODEL and v03.TARGET_BASE == v03.JUDGE_BASE,
        },
        "notes": [
            "v0.10 showed coarse absolute behavior at ceiling even when TARGET responses won on quality; v0.11 tests execution fidelity rather than capability presence.",
            "ENGINEER and TEST modules are frozen from v0.10; wording is not tuned to v0.11 outcomes.",
            "Fidelity criteria are derived from the frozen module semantics and are predeclared before v0.11 generations.",
            "User prompts avoid named reasoning-stage requests.",
            "All v0.11 cases are development cases and cannot serve as future held-out validation.",
        ],
    }
    (out / "v011_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
