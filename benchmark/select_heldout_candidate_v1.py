#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_V011_RUN_ID = 34182916670
DECISION_PROTOCOL_COMMIT = "c29ab7766f01e3345f2e01ccb0b2969555138e5f"
FIDELITY_MIN = 0.15
QUALITY_MIN = 0.667
CASE_FLOOR = 0.50
FAMILIES = ("TEST", "ENGINEER")

# Frozen before v0.11 outcomes. These are SHA-256 hashes of the exact module
# strings used by the held-out runner:
# TEST = run_v06.STAGE_ADDONS["TEST"]
# ENGINEER = run_v07.TARGET_MODULES["ENGINEER"]
FROZEN_MODULE_SHA256 = {
    "TEST": "65e71b8d51d126e335257273f0328c8b634dff8184d746260e8c0e4246e8caf2",
    "ENGINEER": "a3cda45729c09f7dfb414ffafcd91cbf9322ddb2e41910622e1f1f9288811cfa",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evaluate_family(report: dict[str, Any], family: str) -> dict[str, Any]:
    fidelity = report["fidelity_results"][family]
    q_control = report["quality_results"]["TARGET_vs_CONTROL"]["by_family"][family]
    q_attention = report["quality_results"]["TARGET_vs_ATTENTION"]["by_family"][family]

    fidelity_lift = float(fidelity["target_minus_control"])
    q_control_score = float(q_control["score"])
    q_attention_score = float(q_attention["score"])
    control_case_scores = {k: float(v) for k, v in q_control["case_scores"].items()}
    attention_case_scores = {k: float(v) for k, v in q_attention["case_scores"].items()}

    if len(control_case_scores) != 2 or len(attention_case_scores) != 2:
        raise RuntimeError(f"{family} must contain exactly two v0.11 family cases")
    if set(control_case_scores) != set(attention_case_scores):
        raise RuntimeError(f"{family} case IDs differ across quality comparators")

    fidelity_pass = fidelity_lift >= FIDELITY_MIN
    control_quality_pass = q_control_score >= QUALITY_MIN
    attention_quality_pass = q_attention_score >= QUALITY_MIN
    case_floor_pass = (
        min(control_case_scores.values()) >= CASE_FLOOR
        and min(attention_case_scores.values()) >= CASE_FLOOR
    )
    selected = fidelity_pass and control_quality_pass and attention_quality_pass and case_floor_pass

    return {
        "family": family,
        "fidelity_lift": fidelity_lift,
        "fidelity_min": FIDELITY_MIN,
        "fidelity_pass": fidelity_pass,
        "target_vs_control_quality": q_control_score,
        "target_vs_attention_quality": q_attention_score,
        "quality_min": QUALITY_MIN,
        "target_vs_control_case_scores": control_case_scores,
        "target_vs_attention_case_scores": attention_case_scores,
        "case_floor": CASE_FLOOR,
        "case_floor_pass": case_floor_pass,
        "selected": selected,
    }


def validate_report_identity(report: dict[str, Any]) -> None:
    if report.get("measurement_version") != "0.11-behavioral-fidelity-identification":
        raise RuntimeError("expected the frozen v0.11 behavioral-fidelity report")
    if report.get("families") != ["TEST", "ENGINEER"]:
        raise RuntimeError("v0.11 family list/order mismatch")
    if int(report.get("generation_replicates", -1)) != 3:
        raise RuntimeError("v0.11 generation replicate count mismatch")
    if int(report.get("fidelity_votes_per_response", -1)) != 3:
        raise RuntimeError("v0.11 fidelity vote count mismatch")
    if int(report.get("quality_votes_per_pair", -1)) != 3:
        raise RuntimeError("v0.11 quality vote count mismatch")

    modules = report.get("target_modules")
    if not isinstance(modules, dict) or set(modules) != set(FAMILIES):
        raise RuntimeError("v0.11 target module set mismatch")
    observed_hashes = {family: sha256_text(str(modules[family])) for family in FAMILIES}
    if observed_hashes != FROZEN_MODULE_SHA256:
        raise RuntimeError(
            f"v0.11 target modules do not match frozen TEST/ENGINEER hashes: {observed_hashes}"
        )


def select_candidate(report: dict[str, Any]) -> dict[str, Any]:
    validate_report_identity(report)
    record = {family: evaluate_family(report, family) for family in FAMILIES}
    selected = [family for family in FAMILIES if record[family]["selected"]]
    hashes = {family: FROZEN_MODULE_SHA256[family] for family in selected}

    return {
        "candidate_version": "heldout-v1-frozen-candidate",
        "source_v011_run_id": SOURCE_V011_RUN_ID,
        "decision_protocol_commit": DECISION_PROTOCOL_COMMIT,
        "selected_modules": selected,
        "module_sha256": hashes,
        "selection_record": {
            "rule": {
                "fidelity_target_minus_control_min": FIDELITY_MIN,
                "target_vs_control_quality_min": QUALITY_MIN,
                "target_vs_attention_quality_min": QUALITY_MIN,
                "per_case_quality_floor": CASE_FLOOR,
            },
            "families": record,
            "all_modules_failed": len(selected) == 0,
            "note": (
                "If all modules failed, this file records the development-stage closure but the held-out intervention runner must not launch."
                if not selected
                else "Selected modules are frozen verbatim by SHA-256 for held-out validation."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="Path to the completed v011_report.json from run 34182916670")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "heldout_candidate_v1.json",
        help="Candidate config output path",
    )
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    candidate = select_candidate(report)
    args.output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(candidate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
