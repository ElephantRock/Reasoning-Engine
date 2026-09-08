#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import aggregate_framework_validation_v1 as base


def main() -> None:
    base.main()
    results_dir = Path(__file__).resolve().parent / "results_framework_validation_v1"
    generic = results_dir / "framework_v1_report.json"
    report = json.loads(generic.read_text(encoding="utf-8"))

    judge = report.get("judge", {})
    if judge.get("model") != "glm-5.3-flash":
        raise RuntimeError(f"unexpected judge model in aggregated report: {judge}")
    if judge.get("family") != "glm" or judge.get("provider") != "zai":
        raise RuntimeError(f"unexpected judge family/provider in aggregated report: {judge}")

    report["measurement_version"] = "heldout-framework-validation-v1-glm53flash"
    report["experiment_role"] = "framework-level held-out validation; cross-model same-family judge; no routing"
    report["evaluation_tier"] = "Tier-1B cross-model same-family; not independent-provider evaluation"
    report["independent_evaluator"] = False
    report["same_family_cross_model"] = True
    report["interpretation_boundary"] = [
        "The primary claim concerns FULL versus an uncontrolled baseline on the frozen 36-case suite.",
        "The evaluator is GLM-5.3-Flash: a distinct model from the GLM-5.1 target, but from the same GLM family and Z.AI provider.",
        "A positive result is cross-model same-family held-out evidence and must not be described as independent-provider evaluation.",
        "COMPACT versus CONTROL and FULL versus COMPACT are secondary and cannot rescue a failed FULL primary endpoint.",
        "Original TEST/ENGINEER/BOTH/NONE labels are descriptive subgroups only; no routing or conditional prompt injection occurs.",
        "A positive result does not validate autonomous routing or universal cross-model improvement.",
        "Cost is descriptive and does not enter any quality endpoint.",
    ]

    output = results_dir / "framework_v1_glm53flash_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
