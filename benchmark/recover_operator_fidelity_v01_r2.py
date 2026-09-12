#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import recover_operator_fidelity_v01 as r1  # noqa: E402

base = r1.base
ROOT = Path(__file__).resolve().parent
ORIGINAL_SOURCE = Path(os.getenv("OPERATOR_FIDELITY_ORIGINAL_RUNS", ROOT / "recovery_source_original" / "runs.jsonl"))
R1_COMBINED = Path(os.getenv("OPERATOR_FIDELITY_R1_COMBINED", ROOT / "recovery_source_r1" / "combined_runs.jsonl"))
OUT = ROOT / "results_operator_fidelity_v01_recovery2"

ORIGINAL_SHA256 = "730341ae792afc3693d3f233c29e7cf14d914beba7c75d17fefda644fd08b5fb"
R1_COMBINED_SHA256 = "30d47ec2410da62114277b46a59cbb7840b6a57dc94fbe6726ffe03eb501d07a"
R1_RUN_ID = 34720490036
R1_ARTIFACT_ID = 10304964963
R2_TARGET_CAP = 32768
R2_JUDGE_CAP = 16384

R1_RECOVERED = {
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
}

PENDING = r1.EXPECTED_REGENERATION_KEYS - R1_RECOVERED


def validate_sources(original: list[dict[str, Any]], partial: list[dict[str, Any]]) -> None:
    base.validate_frozen_files()
    if r1.sha256_file(ORIGINAL_SOURCE) != ORIGINAL_SHA256:
        raise RuntimeError("original source hash mismatch")
    if r1.sha256_file(R1_COMBINED) != R1_COMBINED_SHA256:
        raise RuntimeError("Recovery-1 source hash mismatch")
    if len(original) != 48 or len(partial) != 34:
        raise RuntimeError("unexpected source record counts")
    original_keys = {(x["case_id"], x["condition"]) for x in original}
    if original_keys != r1.expected_keys():
        raise RuntimeError("original source does not match frozen design")
    recovered = {
        (x["case_id"], x["condition"])
        for x in partial
        if x.get("recovery_status") == "regenerated_from_capped_source"
    }
    if recovered != R1_RECOVERED or len(PENDING) != 10:
        raise RuntimeError("unexpected Recovery-1 success/pending set")
    for x in partial:
        if x.get("recovery_status") == "regenerated_from_capped_source":
            if not str(x.get("text") or "").strip() or x.get("finish_reason") == "length":
                raise RuntimeError("invalid Recovery-1 regenerated output")
            if int((x.get("usage") or {}).get("output_tokens", 0) or 0) >= r1.RECOVERY_TARGET_CAP:
                raise RuntimeError("Recovery-1 regenerated output hit its cap")


def regenerate(case: dict[str, Any], condition: str, original: dict[str, Any]) -> dict[str, Any]:
    result = base.v03.target_call(
        base.policies.POLICIES[condition],
        [{"role": "user", "content": case["agent_input"]}],
    )
    text = result.get("text") or ""
    tokens = int((result.get("usage") or {}).get("output_tokens", 0) or 0)
    if not text.strip() or result.get("finish_reason") == "length" or tokens >= R2_TARGET_CAP:
        raise RuntimeError(
            f"Recovery-2 output incomplete for {case['case_id']} {condition}: "
            f"tokens={tokens}, finish={result.get('finish_reason')!r}, visible={bool(text.strip())}"
        )
    return {
        "case_id": case["case_id"],
        "intended_policy": case["intended_policy"],
        "condition": condition,
        "text": text,
        "usage": result.get("usage", {}),
        "finish_reason": result.get("finish_reason"),
        "recovery_status": "regenerated_in_recovery2",
        "source_usage": original.get("usage", {}),
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    original = r1.read_jsonl(ORIGINAL_SOURCE)
    partial = r1.read_jsonl(R1_COMBINED)
    validate_sources(original, partial)
    r1.write_jsonl(OUT / "original_source_runs.jsonl", original)
    r1.write_jsonl(OUT / "recovery1_combined_runs.jsonl", partial)

    original_index = {(x["case_id"], x["condition"]): x for x in original}
    partial_index = {(x["case_id"], x["condition"]): x for x in partial}
    combined: list[dict[str, Any]] = []
    for case in base.CASES:
        for condition in base.CONDITIONS:
            key = (case["case_id"], condition)
            source = original_index[key]
            if key in R1_RECOVERED:
                item = dict(partial_index[key])
                item["recovery2_status"] = "preserved_recovery1"
            elif not r1.needs_regeneration(source):
                item = dict(source)
                item["recovery_status"] = "preserved_original"
                item["recovery2_status"] = "preserved_original"
            elif key in PENDING:
                print("recovery2-target", *key, flush=True)
                item = regenerate(case, condition, source)
                item["recovery2_status"] = "regenerated_recovery2"
            else:
                raise RuntimeError(f"unclassified key: {key}")
            combined.append(item)
            r1.write_jsonl(OUT / "combined_runs.jsonl", combined)

    if len(combined) != 48 or any(not str(x.get("text") or "").strip() for x in combined):
        raise RuntimeError("Recovery-2 target set incomplete")

    index = {(x["case_id"], x["condition"]): x for x in combined}
    r1.OUT = OUT
    failures: list[dict[str, Any]] = []
    r1.write_jsonl(OUT / "judge_format_failures.jsonl", failures)
    behavior: list[dict[str, Any]] = []
    for case in base.CASES:
        for condition in base.CONDITIONS:
            for vote_index in range(1, base.JUDGE_VOTES + 1):
                print("recovery2-behavior", case["case_id"], condition, vote_index, flush=True)
                behavior.append(r1.behavior_vote(case, index[(case["case_id"], condition)], vote_index, failures))
                r1.write_jsonl(OUT / "behavior_votes.jsonl", behavior)

    quality: list[dict[str, Any]] = []
    for case in base.CASES:
        operator = case["intended_policy"]
        specialist = index[(case["case_id"], operator)]
        for opponent in ("CONTROL", "FULL"):
            pair_id = f"{operator}_vs_{opponent}"
            print("recovery2-quality", case["case_id"], pair_id, flush=True)
            quality.append(r1.quality_vote(case, specialist, index[(case["case_id"], opponent)], pair_id, failures))
            r1.write_jsonl(OUT / "quality_sanity.jsonl", quality)

    if len(behavior) != 96 or len(quality) != 12:
        raise RuntimeError("Recovery-2 vote counts incomplete")
    summary = base.aggregate(combined, behavior, quality)
    summary["recovery2"] = {
        "original_sha256": ORIGINAL_SHA256,
        "recovery1_run_id": R1_RUN_ID,
        "recovery1_artifact_id": R1_ARTIFACT_ID,
        "recovery1_combined_sha256": R1_COMBINED_SHA256,
        "preserved_original_outputs": 28,
        "preserved_recovery1_outputs": 10,
        "regenerated_recovery2_outputs": 10,
        "target_cap": R2_TARGET_CAP,
        "judge_cap": R2_JUDGE_CAP,
        "judge_format_failures": len(failures),
        "valid_judgments_before_recovery2": 0,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "recovery_meta.json").write_text(json.dumps(summary["recovery2"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_operators"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
