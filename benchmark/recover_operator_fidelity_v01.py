#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Callable

os.environ["BENCHMARK_SUITE"] = "combined"
import run_operator_fidelity_v01 as base  # noqa: E402

ROOT = Path(__file__).resolve().parent
SOURCE_RUNS = Path(os.getenv("OPERATOR_FIDELITY_SOURCE_RUNS", ROOT / "recovery_source" / "runs.jsonl"))
OUT = ROOT / "results_operator_fidelity_v01_recovery"

SOURCE_RUNS_SHA256 = "730341ae792afc3693d3f233c29e7cf14d914beba7c75d17fefda644fd08b5fb"
SOURCE_RUN_ID = 34710001873
SOURCE_ARTIFACT_ID = 10302974552
ORIGINAL_TARGET_CAP = 4096
RECOVERY_TARGET_CAP = 16384
RECOVERY_JUDGE_CAP = 8192
MAX_FORMAT_ATTEMPTS = 3

EXPECTED_REGENERATION_KEYS = {
    ("ARC-V01-DC01", "ABDUCTIVE_DIAGNOSTIC"),
    ("ARC-V01-DC01", "CAUSAL_EXPERIMENTAL"),
    ("ARC-V01-DC01", "SEARCH_PLANNING"),
    ("ARC-V01-AD01", "FULL"),
    ("ARC-V01-AD01", "DECISION_THEORETIC"),
    ("ARC-V01-CE01", "FULL"),
    ("ARC-V01-SP01", "CONTROL"),
    ("ARC-V01-SP01", "FULL"),
    ("ARC-V01-DT01", "CONTROL"),
    ("ARC-V01-DT01", "FULL"),
    ("ARC-V01-DT01", "DEDUCTIVE_CONSTRAINT"),
    ("ARC-V01-DT01", "ABDUCTIVE_DIAGNOSTIC"),
    ("ARC-V01-DT01", "CAUSAL_EXPERIMENTAL"),
    ("ARC-V01-DT01", "SEARCH_PLANNING"),
    ("ARC-V01-DT01", "DECISION_THEORETIC"),
    ("ARC-V01-DT01", "SYSTEMS_FEEDBACK"),
    ("ARC-V01-SF01", "CONTROL"),
    ("ARC-V01-SF01", "FULL"),
    ("ARC-V01-SF01", "DEDUCTIVE_CONSTRAINT"),
    ("ARC-V01-SF01", "SEARCH_PLANNING"),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def case_index() -> dict[str, dict[str, Any]]:
    return {case["case_id"]: case for case in base.CASES}


def expected_keys() -> set[tuple[str, str]]:
    return {(case["case_id"], condition) for case in base.CASES for condition in base.CONDITIONS}


def needs_regeneration(run: dict[str, Any]) -> bool:
    text = str(run.get("text") or "")
    usage = run.get("usage") or {}
    tokens = int(usage.get("output_tokens", 0) or 0)
    return (not text.strip()) or tokens >= ORIGINAL_TARGET_CAP


def validate_source_runs(source: list[dict[str, Any]]) -> None:
    base.validate_frozen_files()
    if sha256_file(SOURCE_RUNS) != SOURCE_RUNS_SHA256:
        raise RuntimeError("source runs SHA-256 does not match frozen recovery source")
    if len(source) != 48:
        raise RuntimeError(f"expected 48 source runs, found {len(source)}")
    keys = [(item.get("case_id"), item.get("condition")) for item in source]
    if len(set(keys)) != 48:
        raise RuntimeError("source runs contain duplicate case/condition keys")
    if set(keys) != expected_keys():
        raise RuntimeError("source runs do not match the frozen 6x8 case/condition design")
    regeneration = {key for key, item in zip(keys, source) if needs_regeneration(item)}
    if regeneration != EXPECTED_REGENERATION_KEYS:
        raise RuntimeError(f"unexpected regeneration set: {sorted(regeneration)}")


def regenerate(case: dict[str, Any], condition: str, original: dict[str, Any]) -> dict[str, Any]:
    system = base.policies.POLICIES[condition]
    result = base.v03.target_call(system, [{"role": "user", "content": case["agent_input"]}])
    text = result.get("text") or ""
    usage = result.get("usage") or {}
    tokens = int(usage.get("output_tokens", 0) or 0)
    finish_reason = result.get("finish_reason")
    if not text.strip() or tokens >= RECOVERY_TARGET_CAP or finish_reason == "length":
        raise RuntimeError(
            f"recovered output still incomplete for {case['case_id']} {condition}: "
            f"tokens={tokens} finish_reason={finish_reason!r} visible={bool(text.strip())}"
        )
    return {
        "case_id": case["case_id"],
        "intended_policy": case["intended_policy"],
        "condition": condition,
        "text": text,
        "usage": usage,
        "finish_reason": finish_reason,
        "recovery_status": "regenerated_from_capped_source",
        "source_usage": original.get("usage", {}),
        "source_visible_chars": len(str(original.get("text") or "")),
    }


def preserve(original: dict[str, Any]) -> dict[str, Any]:
    return {
        **original,
        "recovery_status": "preserved_original",
    }


def parse_with_retries(
    system: str,
    content: dict[str, Any],
    validator: Callable[[dict[str, Any]], dict[str, Any]],
    vote_id: str,
    failures: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        result = base.v03.judge_call(system, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
        try:
            parsed = base.v03.parse_json(result.get("text") or "")
            validated = validator(parsed)
            return validated, result, attempt
        except Exception as exc:
            last_error = exc
            failures.append(
                {
                    "vote_id": vote_id,
                    "attempt": attempt,
                    "error": f"{type(exc).__name__}: {exc}",
                    "visible_text": result.get("text") or "",
                    "usage": result.get("usage", {}),
                    "finish_reason": result.get("finish_reason"),
                }
            )
            write_jsonl(OUT / "judge_format_failures.jsonl", failures)
    raise RuntimeError(f"judge formatting failed after {MAX_FORMAT_ATTEMPTS} attempts for {vote_id}") from last_error


def validate_behavior(parsed: dict[str, Any]) -> dict[str, Any]:
    scores = parsed.get("scores", {})
    if set(scores) != set(base.DIMENSIONS):
        raise ValueError(f"behavior scores missing/extra dimensions: {sorted(scores)}")
    clean: dict[str, float] = {}
    for dim in base.DIMENSIONS:
        value = float(scores[dim])
        if not 0 <= value <= 4:
            raise ValueError(f"invalid behavior score {dim}={value}")
        clean[dim] = value
    return {
        "scores": clean,
        "accuracy_pathology": bool(parsed.get("accuracy_pathology", False)),
        "pathology_note": str(parsed.get("pathology_note", "")),
        "notes": str(parsed.get("notes", "")),
    }


def behavior_vote(
    case: dict[str, Any], run: dict[str, Any], vote_index: int, failures: list[dict[str, Any]]
) -> dict[str, Any]:
    vote_id = f"{case['case_id']}:{run['condition']}:behavior:{vote_index}"
    content = {
        "case_id": case["case_id"],
        "task": case["agent_input"],
        "target_behavior_note": case["evaluator_key"]["target_behavior"],
        "candidate_response": run["text"],
        "vote_id": vote_id,
    }
    parsed, result, attempts = parse_with_retries(base.BEHAVIOR_JUDGE, content, validate_behavior, vote_id, failures)
    return {
        "case_id": case["case_id"],
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
    case: dict[str, Any], left: dict[str, Any], right: dict[str, Any], pair_id: str, failures: list[dict[str, Any]]
) -> dict[str, Any]:
    first, second = left, right
    if random.Random(f"arc-v01:{case['case_id']}:{pair_id}").random() < 0.5:
        first, second = second, first
    vote_id = f"{case['case_id']}:{pair_id}:quality"
    content = {
        "case_id": case["case_id"],
        "task": case["agent_input"],
        "target_behavior_note": case["evaluator_key"]["target_behavior"],
        "response_A": first["text"],
        "response_B": second["text"],
    }
    parsed, result, attempts = parse_with_retries(base.QUALITY_JUDGE, content, validate_quality, vote_id, failures)
    winner_side = parsed.pop("winner_side")
    pathology_side = parsed.pop("pathology_side")
    resolved = "TIE" if winner_side == "TIE" else (first if winner_side == "A" else second)["condition"]
    pathology_condition = None
    if parsed["material_pathology"]:
        pathology_condition = (first if pathology_side == "A" else second)["condition"]
    return {
        "case_id": case["case_id"],
        "pair_id": pair_id,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": resolved,
        **parsed,
        "pathology_condition": pathology_condition,
        "usage": result.get("usage", {}),
        "format_attempts": attempts,
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    source = read_jsonl(SOURCE_RUNS)
    validate_source_runs(source)
    write_jsonl(OUT / "source_runs.jsonl", source)

    cases = case_index()
    invalid_source = [item for item in source if needs_regeneration(item)]
    write_jsonl(OUT / "invalid_source_runs.jsonl", invalid_source)

    source_index = {(item["case_id"], item["condition"]): item for item in source}
    combined: list[dict[str, Any]] = []
    for case in base.CASES:
        for condition in base.CONDITIONS:
            key = (case["case_id"], condition)
            original = source_index[key]
            if key in EXPECTED_REGENERATION_KEYS:
                print("recover-target", case["case_id"], condition, flush=True)
                combined.append(regenerate(case, condition, original))
            else:
                combined.append(preserve(original))
            write_jsonl(OUT / "combined_runs.jsonl", combined)

    if len(combined) != 48 or any(not str(item.get("text") or "").strip() for item in combined):
        raise RuntimeError("combined recovery set is incomplete")

    index = {(item["case_id"], item["condition"]): item for item in combined}
    failures: list[dict[str, Any]] = []
    behavior: list[dict[str, Any]] = []
    for case in base.CASES:
        for condition in base.CONDITIONS:
            run = index[(case["case_id"], condition)]
            for vote_index in range(1, base.JUDGE_VOTES + 1):
                print("recover-behavior", case["case_id"], condition, vote_index, flush=True)
                behavior.append(behavior_vote(case, run, vote_index, failures))
                write_jsonl(OUT / "behavior_votes.jsonl", behavior)

    quality: list[dict[str, Any]] = []
    for case in base.CASES:
        operator = case["intended_policy"]
        specialist = index[(case["case_id"], operator)]
        for opponent in ("CONTROL", "FULL"):
            pair_id = f"{operator}_vs_{opponent}"
            print("recover-quality", case["case_id"], pair_id, flush=True)
            quality.append(quality_vote(case, specialist, index[(case["case_id"], opponent)], pair_id, failures))
            write_jsonl(OUT / "quality_sanity.jsonl", quality)

    if len(behavior) != 96 or len(quality) != 12:
        raise RuntimeError("recovery completed with wrong vote counts")

    summary = base.aggregate(combined, behavior, quality)
    summary["recovery"] = {
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_runs_sha256": SOURCE_RUNS_SHA256,
        "source_records": len(source),
        "preserved_target_outputs": 28,
        "regenerated_target_outputs": 20,
        "original_target_cap": ORIGINAL_TARGET_CAP,
        "recovery_target_cap": RECOVERY_TARGET_CAP,
        "recovery_judge_cap": RECOVERY_JUDGE_CAP,
        "judge_format_failures": len(failures),
        "valid_source_judgments": 0,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "recovery_meta.json").write_text(
        json.dumps(summary["recovery"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_operators"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
