#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path
from statistics import median
from typing import Any, Callable

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v03 as v03  # noqa: E402
import reasoning_policies_v02 as policies  # noqa: E402

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "operator_fidelity_cases_v02.json"
POLICIES_PATH = ROOT / "reasoning_policies_v02.py"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))

EXPECTED_CASES_BLOB = "de1becf88db15f68acd151e642e51ac39129171c"
EXPECTED_POLICIES_BLOB = "504ca9ac63ba10fc7833c36230787aafdf02920e"
JUDGE_VOTES = 2
TARGET_CAP = 32768
JUDGE_CAP = 16384
MAX_FORMAT_ATTEMPTS = 3
CONDITIONS = tuple(policies.POLICIES)
SPECIALISTS = tuple(policies.SPECIALISTS)

FIDELITY_CRITERIA: dict[str, tuple[str, ...]] = {
    "DEDUCTIVE_CONSTRAINT": (
        "Identifies the premises, definitions, resources, or hard constraints that actually determine the result.",
        "Separates necessary conclusions from assumptions, conventions, or merely plausible claims.",
        "Derives feasibility or necessity from the constraints instead of merely asserting the answer.",
        "Checks a boundary case, counterexample, or hidden assumption that could flip the conclusion.",
        "When blocked, identifies a genuinely minimal sufficient relaxation/resource change; when feasible, identifies the margin or boundary that would make feasibility fail.",
    ),
    "ABDUCTIVE_DIAGNOSTIC": (
        "Preserves at least two materially plausible explanations rather than collapsing immediately to one story.",
        "Ties leading explanations to expected evidence, mechanism-consistent patterns, or observations.",
        "States what observation would weaken or disconfirm at least the leading explanations.",
        "Selects evidence or an action that discriminates among explanations instead of merely confirming one.",
        "Calibrates ranking and preserves residual uncertainty when the evidence remains underdetermined.",
    ),
    "CAUSAL_EXPERIMENTAL": (
        "States the causal ambiguity, effect, intervention, or counterfactual distinction rather than treating association as effect.",
        "Identifies material confounding, alternative causal paths, or rival mechanisms.",
        "Proposes an intervention, comparison, or quasi-experiment capable of changing causal beliefs.",
        "Gives outcome predictions or decision implications that differ across rival causal explanations.",
        "States a falsification, identification, or transport limitation under which the causal conclusion should be revised.",
    ),
    "SEARCH_PLANNING": (
        "Represents the objective, relevant state, hard constraints, legal actions, and prerequisites.",
        "Considers at least one materially different path, ordering, or branch before committing.",
        "Identifies a bottleneck, dependency, dead end, or irreversible step that constrains the plan.",
        "Includes checkpoints plus a branch, fallback, or recovery action tied to observed state.",
        "Preserves options or reversibility where uncertainty makes premature commitment costly.",
    ),
    "DECISION_THEORETIC": (
        "Distinguishes the feasible actions and materially different consequences.",
        "Represents consequential uncertainty rather than reasoning only from the modal outcome.",
        "Accounts for asymmetric upside/downside or opportunity cost.",
        "Uses reversibility, option value, or value of information in comparing actions.",
        "States a stopping/information criterion or an assumption under which the preferred action would change.",
    ),
    "SYSTEMS_FEEDBACK": (
        "Identifies material state variables, capacities, flows, and directional links among them.",
        "Identifies at least one feedback loop or endogenous behavioral response that changes the intervention effect.",
        "Accounts for a relevant delay, adaptation, accumulation, or time-horizon effect.",
        "Anticipates bottleneck migration, rebound, displacement, overshoot, or another supported second-order system effect.",
        "Ties monitoring, rollback, or intervention design to those dynamics rather than treating them as generic caveats.",
    ),
}

FIDELITY_JUDGE = r'''You are a strict blinded evaluator of observable reasoning fidelity. You are given one task, one candidate response, and exactly five behavioral criteria. You are not told which experimental condition produced the response.

Score each criterion independently using only these values:
- 0.0 = absent, contrary, or materially unusable;
- 0.5 = partial, implicit, weak, or incomplete;
- 1.0 = clear, substantively complete, and decision-relevant.

Do not reward headings, named frameworks, jargon, verbosity, or stylistic polish. Do not infer hidden reasoning that is not observable in the response. A response can be correct yet score low on a criterion if it does not actually demonstrate that behavior.

Set accuracy_pathology=true only for a material factual, logical, constraint, or decision error in the candidate response, not merely for missing one of the five behaviors or ordinary incompleteness.

Return JSON only:
{"scores":{"c1":0.0,"c2":0.0,"c3":0.0,"c4":0.0,"c5":0.0},"accuracy_pathology":false,"pathology_note":"","notes":"brief concrete justification"}'''

QUALITY_JUDGE = r'''You are a blinded pairwise evaluator of answer quality. You are not told which condition produced either response. Judge correctness, use of supplied facts, fit to the actual problem, calibrated uncertainty, and decision usefulness. Do not reward headings, named reasoning frameworks, jargon, verbosity, or token count. If both are substantively equivalent, return TIE.

Also flag material_pathology only when one response contains a severe factual, logical, constraint, or decision-quality failure that should block that response's reasoning policy from further study. Ordinary inferiority, stylistic weakness, or a small omission is not a material pathology. If material_pathology is true, pathology_condition must be A or B and pathology_note must identify the concrete blocking error. Otherwise pathology_condition must be NONE.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"material_pathology":false,"pathology_condition":"A|B|NONE","pathology_note":"","notes":"brief concrete reason"}'''


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def validate_frozen_files() -> None:
    actual_cases = git_blob(CASES_PATH)
    actual_policies = git_blob(POLICIES_PATH)
    if actual_cases != EXPECTED_CASES_BLOB:
        raise RuntimeError(f"case blob changed: {actual_cases} != {EXPECTED_CASES_BLOB}")
    if actual_policies != EXPECTED_POLICIES_BLOB:
        raise RuntimeError(f"policy blob changed: {actual_policies} != {EXPECTED_POLICIES_BLOB}")
    if len(CASES) != 12:
        raise RuntimeError(f"expected 12 cases, found {len(CASES)}")
    intended = [case["intended_policy"] for case in CASES]
    for specialist in SPECIALISTS:
        if intended.count(specialist) != 2:
            raise RuntimeError(f"expected two cases for {specialist}, found {intended.count(specialist)}")
    if set(FIDELITY_CRITERIA) != set(SPECIALISTS):
        raise RuntimeError("fidelity criteria do not match specialist set")
    if any(len(criteria) != 5 for criteria in FIDELITY_CRITERIA.values()):
        raise RuntimeError("every specialist must have exactly five fidelity criteria")
    if v03.TARGET_MODEL != "glm-5.1":
        raise RuntimeError(f"target must be glm-5.1, got {v03.TARGET_MODEL}")
    if v03.JUDGE_MODEL != "glm-5.3-flash":
        raise RuntimeError(f"judge must be glm-5.3-flash, got {v03.JUDGE_MODEL}")
    if int(os.getenv("ZAI_MAX_TOKENS", "0")) != TARGET_CAP:
        raise RuntimeError(f"ZAI_MAX_TOKENS must be {TARGET_CAP}")
    if int(os.getenv("ZAI_JUDGE_MAX_TOKENS", "0")) != JUDGE_CAP:
        raise RuntimeError(f"ZAI_JUDGE_MAX_TOKENS must be {JUDGE_CAP}")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def run_target(case: dict[str, Any], condition: str) -> dict[str, Any]:
    result = v03.target_call(
        policies.POLICIES[condition],
        [{"role": "user", "content": case["agent_input"]}],
    )
    return {
        "case_id": case["case_id"],
        "intended_policy": case["intended_policy"],
        "condition": condition,
        "text": result.get("text") or "",
        "usage": result.get("usage", {}),
        "finish_reason": result.get("finish_reason"),
    }


def target_complete(run: dict[str, Any]) -> bool:
    tokens = int((run.get("usage") or {}).get("output_tokens", 0) or 0)
    return bool(str(run.get("text") or "").strip()) and run.get("finish_reason") != "length" and tokens < TARGET_CAP


def parse_with_retries(
    system: str,
    content: dict[str, Any],
    validator: Callable[[dict[str, Any]], dict[str, Any]],
    vote_id: str,
    failures: list[dict[str, Any]],
    out: Path,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        result = v03.judge_call(system, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
        try:
            parsed = v03.parse_json(result.get("text") or "")
            validated = validator(parsed)
            return validated, result, attempt
        except Exception as exc:
            last_error = exc
            failures.append({
                "vote_id": vote_id,
                "attempt": attempt,
                "error": f"{type(exc).__name__}: {exc}",
                "visible_text": result.get("text") or "",
                "usage": result.get("usage", {}),
                "finish_reason": result.get("finish_reason"),
            })
            write_jsonl(out / "judge_format_failures.jsonl", failures)
    raise RuntimeError(f"judge formatting failed after {MAX_FORMAT_ATTEMPTS} attempts for {vote_id}") from last_error


def validate_fidelity(parsed: dict[str, Any]) -> dict[str, Any]:
    scores = parsed.get("scores", {})
    expected = {f"c{i}" for i in range(1, 6)}
    if set(scores) != expected:
        raise ValueError(f"fidelity scores missing/extra criteria: {sorted(scores)}")
    clean: dict[str, float] = {}
    for key in sorted(expected):
        value = float(scores[key])
        if value not in {0.0, 0.5, 1.0}:
            raise ValueError(f"invalid fidelity score {key}={value}")
        clean[key] = value
    return {
        "scores": clean,
        "accuracy_pathology": bool(parsed.get("accuracy_pathology", False)),
        "pathology_note": str(parsed.get("pathology_note", "")),
        "notes": str(parsed.get("notes", "")),
    }


def fidelity_vote(
    case: dict[str, Any],
    run: dict[str, Any],
    vote_index: int,
    failures: list[dict[str, Any]],
    out: Path,
) -> dict[str, Any]:
    criteria = FIDELITY_CRITERIA[case["intended_policy"]]
    vote_id = f"{case['case_id']}:{run['condition']}:fidelity:{vote_index}"
    content = {
        "task": case["agent_input"],
        "criteria": {f"c{i+1}": text for i, text in enumerate(criteria)},
        "candidate_response": run["text"],
        "vote_id": vote_id,
    }
    parsed, result, attempts = parse_with_retries(FIDELITY_JUDGE, content, validate_fidelity, vote_id, failures, out)
    return {
        "case_id": case["case_id"],
        "intended_policy": case["intended_policy"],
        "condition": run["condition"],
        "vote_index": vote_index,
        **parsed,
        "usage": result.get("usage", {}),
        "format_attempts": attempts,
    }


def validate_quality(parsed: dict[str, Any]) -> dict[str, Any]:
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise ValueError(f"invalid quality winner: {winner!r}")
    material = bool(parsed.get("material_pathology", False))
    side = parsed.get("pathology_condition", "NONE")
    if side not in {"A", "B", "NONE"}:
        raise ValueError(f"invalid pathology_condition: {side!r}")
    if material and side not in {"A", "B"}:
        raise ValueError("material pathology requires A or B attribution")
    if not material and side != "NONE":
        raise ValueError("non-pathology requires NONE attribution")
    return {
        "winner_side": winner,
        "confidence": parsed.get("confidence"),
        "material_pathology": material,
        "pathology_side": side,
        "pathology_note": str(parsed.get("pathology_note", "")),
        "notes": str(parsed.get("notes", "")),
    }


def quality_vote(
    case: dict[str, Any],
    left: dict[str, Any],
    right: dict[str, Any],
    pair_id: str,
    failures: list[dict[str, Any]],
    out: Path,
) -> dict[str, Any]:
    first, second = left, right
    if random.Random(f"arc-v02:{case['case_id']}:{pair_id}").random() < 0.5:
        first, second = second, first
    vote_id = f"{case['case_id']}:{pair_id}:quality"
    content = {
        "task": case["agent_input"],
        "response_A": first["text"],
        "response_B": second["text"],
        "vote_id": vote_id,
    }
    parsed, result, attempts = parse_with_retries(QUALITY_JUDGE, content, validate_quality, vote_id, failures, out)
    winner_side = parsed.pop("winner_side")
    pathology_side = parsed.pop("pathology_side")
    winner = "TIE" if winner_side == "TIE" else (first if winner_side == "A" else second)["condition"]
    pathology_condition = None
    if parsed["material_pathology"]:
        pathology_condition = (first if pathology_side == "A" else second)["condition"]
    return {
        "case_id": case["case_id"],
        "pair_id": pair_id,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": winner,
        **parsed,
        "pathology_condition": pathology_condition,
        "usage": result.get("usage", {}),
        "format_attempts": attempts,
    }


def aggregate(
    runs: list[dict[str, Any]],
    votes: list[dict[str, Any]],
    quality: list[dict[str, Any]],
) -> dict[str, Any]:
    by_output: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for vote in votes:
        by_output.setdefault((vote["case_id"], vote["condition"]), []).append(vote)

    composite: dict[tuple[str, str], float] = {}
    pathology: dict[tuple[str, str], bool] = {}
    criterion_means: dict[tuple[str, str], dict[str, float]] = {}
    for key, group in by_output.items():
        if len(group) != JUDGE_VOTES:
            raise RuntimeError(f"wrong fidelity vote count for {key}: {len(group)}")
        means = {f"c{i}": sum(v["scores"][f"c{i}"] for v in group) / len(group) for i in range(1, 6)}
        criterion_means[key] = means
        composite[key] = sum(means.values()) / 5.0
        pathology[key] = any(v["accuracy_pathology"] for v in group)

    operator_rows: list[dict[str, Any]] = []
    for operator in SPECIALISTS:
        cases = [case for case in CASES if case["intended_policy"] == operator]
        case_ids = [case["case_id"] for case in cases]
        own_cases = [composite[(case_id, operator)] for case_id in case_ids]
        control_cases = [composite[(case_id, "CONTROL")] for case_id in case_ids]
        full_cases = [composite[(case_id, "FULL")] for case_id in case_ids]
        own = sum(own_cases) / len(own_cases)
        control = sum(control_cases) / len(control_cases)
        full = sum(full_cases) / len(full_cases)
        nonmatching_means = {
            other: sum(composite[(case_id, other)] for case_id in case_ids) / len(case_ids)
            for other in SPECIALISTS
            if other != operator
        }
        other_median = median(nonmatching_means.values())
        case_lifts = [own_cases[i] - control_cases[i] for i in range(len(case_ids))]
        behavior_pathology = any(pathology[(case_id, operator)] for case_id in case_ids)
        quality_pathology_votes = [
            item for item in quality
            if item["case_id"] in case_ids
            and item.get("material_pathology")
            and item.get("pathology_condition") == operator
        ]
        lift = own - control
        separation = own - other_median
        eligible = (
            lift >= 0.15
            and separation >= 0.10
            and min(case_lifts) >= 0.0
            and not behavior_pathology
            and not quality_pathology_votes
        )
        operator_rows.append({
            "operator": operator,
            "case_ids": case_ids,
            "specialist_fidelity": own,
            "control_fidelity": control,
            "full_fidelity": full,
            "median_nonmatching_specialist_fidelity": other_median,
            "nonmatching_specialist_means": nonmatching_means,
            "lift_control": lift,
            "separation": separation,
            "case_lifts": dict(zip(case_ids, case_lifts)),
            "minimum_case_lift": min(case_lifts),
            "behavior_accuracy_pathology": behavior_pathology,
            "quality_material_pathology": bool(quality_pathology_votes),
            "quality_pathology_notes": [item.get("pathology_note", "") for item in quality_pathology_votes],
            "stage1_eligible": eligible,
        })

    eligible = [row["operator"] for row in operator_rows if row["stage1_eligible"]]
    if len(eligible) == 6:
        decision = "PASS_ALL_SIX"
    elif len(eligible) >= 4:
        decision = "PASS_SUBSET_REDESIGN_STAGE1"
    else:
        decision = "STOP_REDESIGN_OPERATORS"

    usage: dict[str, Any] = {}
    for condition in CONDITIONS:
        selected = [r for r in runs if r["condition"] == condition]
        usage[condition] = {
            "mean_input_tokens": sum(float((r.get("usage") or {}).get("input_tokens", 0) or 0) for r in selected) / len(selected),
            "mean_output_tokens": sum(float((r.get("usage") or {}).get("output_tokens", 0) or 0) for r in selected) / len(selected),
            "mean_latency_ms": sum(float((r.get("usage") or {}).get("latency_ms", 0) or 0) for r in selected) / len(selected),
            "mean_response_chars": sum(len(r.get("text") or "") for r in selected) / len(selected),
        }

    all_composites = list(composite.values())
    return {
        "measurement_version": "operator-fidelity-v0.2",
        "target_model": v03.TARGET_MODEL,
        "judge_model": v03.JUDGE_MODEL,
        "cases_blob": EXPECTED_CASES_BLOB,
        "policies_blob": EXPECTED_POLICIES_BLOB,
        "eligibility_thresholds": {
            "lift_control": 0.15,
            "separation": 0.10,
            "minimum_case_lift": 0.0,
        },
        "operator_rows": operator_rows,
        "eligible_operators": eligible,
        "program_decision": decision,
        "quality_sanity_votes": quality,
        "fidelity_saturation_diagnostic": {
            "responses_at_1_0": sum(value == 1.0 for value in all_composites),
            "responses_at_or_above_0_9": sum(value >= 0.9 for value in all_composites),
            "responses_total": len(all_composites),
        },
        "criterion_means": {
            f"{case_id}:{condition}": values
            for (case_id, condition), values in criterion_means.items()
        },
        "condition_usage": usage,
    }


def main() -> None:
    validate_frozen_files()
    out = ROOT / "results_operator_fidelity_v02"
    out.mkdir(exist_ok=True)
    runs_path = out / "runs.jsonl"
    votes_path = out / "fidelity_votes.jsonl"
    quality_path = out / "quality_sanity.jsonl"
    failures_path = out / "judge_format_failures.jsonl"
    summary_path = out / "summary.json"

    runs: list[dict[str, Any]] = []
    for case in CASES:
        for condition in CONDITIONS:
            print("generate", case["case_id"], condition, flush=True)
            run = run_target(case, condition)
            runs.append(run)
            write_jsonl(runs_path, runs)
            if not target_complete(run):
                raise RuntimeError(
                    f"incomplete target output for {case['case_id']} {condition}: "
                    f"tokens={(run.get('usage') or {}).get('output_tokens')} "
                    f"finish={run.get('finish_reason')!r} visible={bool(run.get('text','').strip())}"
                )

    index = {(r["case_id"], r["condition"]): r for r in runs}
    failures: list[dict[str, Any]] = []
    write_jsonl(failures_path, failures)

    votes: list[dict[str, Any]] = []
    for case in CASES:
        for condition in CONDITIONS:
            run = index[(case["case_id"], condition)]
            for vote_index in range(1, JUDGE_VOTES + 1):
                print("fidelity", case["case_id"], condition, vote_index, flush=True)
                votes.append(fidelity_vote(case, run, vote_index, failures, out))
                write_jsonl(votes_path, votes)

    quality: list[dict[str, Any]] = []
    for case in CASES:
        operator = case["intended_policy"]
        specialist = index[(case["case_id"], operator)]
        for opponent in ("CONTROL", "FULL"):
            pair_id = f"{operator}_vs_{opponent}"
            print("quality", case["case_id"], pair_id, flush=True)
            quality.append(quality_vote(case, specialist, index[(case["case_id"], opponent)], pair_id, failures, out))
            write_jsonl(quality_path, quality)

    if len(runs) != 96 or len(votes) != 192 or len(quality) != 24:
        raise RuntimeError("operator fidelity v0.2 completed with wrong record counts")

    summary = aggregate(runs, votes, quality)
    summary["judge_format_failures"] = len(failures)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_operators"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
