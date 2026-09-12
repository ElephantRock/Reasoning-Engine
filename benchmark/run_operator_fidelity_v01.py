#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path
from statistics import median
from typing import Any

# Reuse the established Z.AI target/judge transport.
os.environ["BENCHMARK_SUITE"] = "combined"
import run_v03 as v03  # noqa: E402
import reasoning_policies_v01 as policies  # noqa: E402

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "operator_fidelity_cases_v01.json"
POLICIES_PATH = ROOT / "reasoning_policies_v01.py"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))

EXPECTED_CASES_BLOB = "42be38d7554bcf895ff8864f232f156bcd958c17"
EXPECTED_POLICIES_BLOB = "db1c726996bb9aed4b3fb77a6467df9a56ee511b"
JUDGE_VOTES = 2
CONDITIONS = tuple(policies.POLICIES)
SPECIALISTS = tuple(policies.SPECIALISTS)

DIMENSIONS = (
    "deductive_constraint",
    "abductive_diagnostic",
    "causal_experimental",
    "search_planning",
    "decision_theoretic",
    "systems_feedback",
)

POLICY_DIMENSION = {
    "DEDUCTIVE_CONSTRAINT": "deductive_constraint",
    "ABDUCTIVE_DIAGNOSTIC": "abductive_diagnostic",
    "CAUSAL_EXPERIMENTAL": "causal_experimental",
    "SEARCH_PLANNING": "search_planning",
    "DECISION_THEORETIC": "decision_theoretic",
    "SYSTEMS_FEEDBACK": "systems_feedback",
}

BEHAVIOR_JUDGE = r'''You are a strict blinded evaluator of observable reasoning behavior. You are not told which experimental condition produced the candidate. Judge substance only: do not reward headings, named frameworks, jargon, verbosity, or stylistic polish.

Score every dimension from 0 to 4. A score should reflect behavior actually demonstrated in this response, not behavior that would have been useful but was unnecessary.

Dimensions:
- deductive_constraint: 0 violates/ignores constraints; 1 weak constraint mention; 2 mostly respects constraints; 3 derives conclusions from premises/constraints and exposes assumptions; 4 rigorous necessity/feasibility reasoning with boundary/counterexample checking where relevant.
- abductive_diagnostic: 0 premature unsupported diagnosis; 1 superficial alternatives; 2 maintains alternatives with weak discrimination; 3 competing explanations plus discriminating evidence; 4 calibrated ranking plus evidence/action that can change the diagnosis.
- causal_experimental: 0 association treated as causation; 1 causal uncertainty only; 2 alternatives/confounding plus partially informative evidence; 3 clear discriminating intervention/comparison and predictions; 4 strong identification logic including counterfactual/intervention interpretation and falsification conditions.
- search_planning: 0 infeasible/unordered; 1 checklist with weak dependencies; 2 feasible basic ordering; 3 explicit constraints, sequencing, checkpoints and recovery; 4 robust search/plan with branching, bottleneck handling and option preservation where relevant.
- decision_theoretic: 0 ignores uncertainty/consequences; 1 mostly modal-outcome reasoning; 2 alternatives plus some downside/reversibility; 3 asymmetric consequences, information value, reversibility and key assumptions; 4 integrates uncertainty, downside, option value and stopping/information criteria.
- systems_feedback: 0 static local reasoning where dynamics matter; 1 generic second-order mention; 2 one material feedback/delay/bottleneck; 3 interacting loops/delays alter intervention or monitoring; 4 robust dynamic reasoning including adaptation, bottleneck migration and time horizon without inventing complexity.

Use 4 sparingly. accuracy_pathology should be true only for a material factual, logical, constraint, or decision error in the candidate response, not merely for a missing target behavior or ordinary incompleteness. Return JSON only:
{"scores":{"deductive_constraint":0,"abductive_diagnostic":0,"causal_experimental":0,"search_planning":0,"decision_theoretic":0,"systems_feedback":0},"accuracy_pathology":false,"pathology_note":"","notes":"brief concrete justification"}'''

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
    if len(CASES) != 6:
        raise RuntimeError(f"expected 6 cases, found {len(CASES)}")
    intended = {case["intended_policy"] for case in CASES}
    if intended != set(SPECIALISTS):
        raise RuntimeError(f"case/operator mismatch: {sorted(intended)} vs {sorted(SPECIALISTS)}")
    if v03.TARGET_MODEL != "glm-5.1":
        raise RuntimeError(f"target must be glm-5.1, got {v03.TARGET_MODEL}")
    if v03.JUDGE_MODEL != "glm-5.3-flash":
        raise RuntimeError(f"judge must be glm-5.3-flash, got {v03.JUDGE_MODEL}")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def run_target(case: dict[str, Any], condition: str) -> dict[str, Any]:
    system = policies.POLICIES[condition]
    result = v03.target_call(system, [{"role": "user", "content": case["agent_input"]}])
    return {
        "case_id": case["case_id"],
        "intended_policy": case["intended_policy"],
        "condition": condition,
        "text": result["text"],
        "usage": result["usage"],
    }


def behavior_vote(case: dict[str, Any], run: dict[str, Any], vote_index: int) -> dict[str, Any]:
    content = {
        "case_id": case["case_id"],
        "task": case["agent_input"],
        "target_behavior_note": case["evaluator_key"]["target_behavior"],
        "candidate_response": run["text"],
        "vote_id": f"{case['case_id']}:{run['condition']}:{vote_index}",
    }
    result = v03.judge_call(BEHAVIOR_JUDGE, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
    parsed = v03.parse_json(result["text"])
    scores = parsed.get("scores", {})
    if set(scores) != set(DIMENSIONS):
        raise RuntimeError(f"missing/extra behavior scores: {parsed}")
    clean: dict[str, float] = {}
    for dim in DIMENSIONS:
        value = float(scores[dim])
        if not 0 <= value <= 4:
            raise RuntimeError(f"invalid behavior score {dim}={value}")
        clean[dim] = value
    return {
        "case_id": case["case_id"],
        "condition": run["condition"],
        "vote_index": vote_index,
        "scores": clean,
        "accuracy_pathology": bool(parsed.get("accuracy_pathology", False)),
        "pathology_note": parsed.get("pathology_note", ""),
        "notes": parsed.get("notes", ""),
        "usage": result["usage"],
    }


def quality_vote(case: dict[str, Any], left: dict[str, Any], right: dict[str, Any], pair_id: str) -> dict[str, Any]:
    first, second = left, right
    if random.Random(f"arc-v01:{case['case_id']}:{pair_id}").random() < 0.5:
        first, second = second, first
    content = {
        "case_id": case["case_id"],
        "task": case["agent_input"],
        "target_behavior_note": case["evaluator_key"]["target_behavior"],
        "response_A": first["text"],
        "response_B": second["text"],
    }
    result = v03.judge_call(QUALITY_JUDGE, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid pairwise quality result: {parsed}")

    material_pathology = bool(parsed.get("material_pathology", False))
    pathology_side = parsed.get("pathology_condition", "NONE")
    if pathology_side not in {"A", "B", "NONE"}:
        raise RuntimeError(f"invalid pathology_condition: {parsed}")
    if material_pathology and pathology_side not in {"A", "B"}:
        raise RuntimeError(f"material pathology requires A or B attribution: {parsed}")
    if not material_pathology and pathology_side != "NONE":
        raise RuntimeError(f"non-pathology must use NONE attribution: {parsed}")

    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    pathology_condition = None
    if material_pathology:
        pathology_condition = (first if pathology_side == "A" else second)["condition"]

    return {
        "case_id": case["case_id"],
        "pair_id": pair_id,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": resolved,
        "confidence": parsed.get("confidence"),
        "material_pathology": material_pathology,
        "pathology_condition": pathology_condition,
        "pathology_note": parsed.get("pathology_note", ""),
        "notes": parsed.get("notes", ""),
        "usage": result["usage"],
    }


def aggregate(runs: list[dict[str, Any]], votes: list[dict[str, Any]], quality: list[dict[str, Any]]) -> dict[str, Any]:
    by_output: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for vote in votes:
        by_output.setdefault((vote["case_id"], vote["condition"]), []).append(vote)

    averaged: dict[tuple[str, str], dict[str, float]] = {}
    pathologies: dict[tuple[str, str], bool] = {}
    for key, group in by_output.items():
        averaged[key] = {dim: sum(v["scores"][dim] for v in group) / len(group) for dim in DIMENSIONS}
        pathologies[key] = any(v["accuracy_pathology"] for v in group)

    operator_rows = []
    for case in CASES:
        operator = case["intended_policy"]
        dim = POLICY_DIMENSION[operator]
        own = averaged[(case["case_id"], operator)][dim]
        control = averaged[(case["case_id"], "CONTROL")][dim]
        full = averaged[(case["case_id"], "FULL")][dim]
        other = [averaged[(case["case_id"], name)][dim] for name in SPECIALISTS if name != operator]
        lift = own - control
        separation = own - median(other)
        behavior_pathology = pathologies[(case["case_id"], operator)]
        quality_pathology_votes = [
            item
            for item in quality
            if item["case_id"] == case["case_id"]
            and item.get("material_pathology")
            and item.get("pathology_condition") == operator
        ]
        quality_pathology = bool(quality_pathology_votes)
        pathology = behavior_pathology or quality_pathology
        eligible = lift >= 0.50 and separation >= 0.25 and not pathology
        operator_rows.append({
            "operator": operator,
            "case_id": case["case_id"],
            "dimension": dim,
            "operator_score": own,
            "control_score": control,
            "full_score": full,
            "operator_minus_full": own - full,
            "other_specialist_median": median(other),
            "lift_control": lift,
            "separation": separation,
            "behavior_accuracy_pathology": behavior_pathology,
            "quality_material_pathology": quality_pathology,
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

    usage = {}
    for condition in CONDITIONS:
        selected = [r for r in runs if r["condition"] == condition]
        usage[condition] = {
            "mean_input_tokens": sum(float(r["usage"].get("input_tokens", 0) or 0) for r in selected) / len(selected),
            "mean_output_tokens": sum(float(r["usage"].get("output_tokens", 0) or 0) for r in selected) / len(selected),
            "mean_latency_ms": sum(float(r["usage"].get("latency_ms", 0) or 0) for r in selected) / len(selected),
            "mean_response_chars": sum(len(r["text"]) for r in selected) / len(selected),
        }

    return {
        "measurement_version": "operator-fidelity-v0.1",
        "target_model": v03.TARGET_MODEL,
        "judge_model": v03.JUDGE_MODEL,
        "cases_blob": EXPECTED_CASES_BLOB,
        "policies_blob": EXPECTED_POLICIES_BLOB,
        "operator_rows": operator_rows,
        "eligible_operators": eligible,
        "program_decision": decision,
        "quality_sanity_votes": quality,
        "condition_usage": usage,
    }


def main() -> None:
    validate_frozen_files()
    out = ROOT / "results_operator_fidelity_v01"
    out.mkdir(exist_ok=True)
    runs_path = out / "runs.jsonl"
    votes_path = out / "behavior_votes.jsonl"
    quality_path = out / "quality_sanity.jsonl"
    summary_path = out / "summary.json"

    runs: list[dict[str, Any]] = []
    for case in CASES:
        for condition in CONDITIONS:
            print("generate", case["case_id"], condition, flush=True)
            runs.append(run_target(case, condition))
            write_jsonl(runs_path, runs)

    index = {(r["case_id"], r["condition"]): r for r in runs}

    votes: list[dict[str, Any]] = []
    for case in CASES:
        for condition in CONDITIONS:
            run = index[(case["case_id"], condition)]
            for vote_index in range(1, JUDGE_VOTES + 1):
                print("behavior", case["case_id"], condition, vote_index, flush=True)
                votes.append(behavior_vote(case, run, vote_index))
                write_jsonl(votes_path, votes)

    quality: list[dict[str, Any]] = []
    for case in CASES:
        operator = case["intended_policy"]
        specialist = index[(case["case_id"], operator)]
        for opponent in ("CONTROL", "FULL"):
            print("quality", case["case_id"], operator, "vs", opponent, flush=True)
            quality.append(quality_vote(case, specialist, index[(case["case_id"], opponent)], f"{operator}_vs_{opponent}"))
            write_jsonl(quality_path, quality)

    summary = aggregate(runs, votes, quality)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_operators"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
