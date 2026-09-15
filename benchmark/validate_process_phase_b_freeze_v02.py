#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "benchmark/process_phase_b_freeze_v02.json"


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data["measurement_version"] != "process-constrained-phase-b-v0.2":
        raise RuntimeError("measurement version drift")
    if data["scientific_base_commit"] != "642a7160e75fae1a03faf5139f83c87cabf9d0e0":
        raise RuntimeError("scientific base commit drift")
    if data["target_model"] != "glm-5.1":
        raise RuntimeError("target model drift")
    if int(data["completion_token_ceiling"]) != 16384:
        raise RuntimeError("completion ceiling drift")
    if float(data["temperature"]) != 0.0:
        raise RuntimeError("temperature drift")
    expected_conditions = ["SPECIALIST", "MATCHED_SCAFFOLD", "FULL", "CONTROL"]
    if data["conditions"] != expected_conditions:
        raise RuntimeError("condition set/order drift")
    if data["provider_base_url"] != "https://api.z.ai/api/coding/paas/v4":
        raise RuntimeError("provider base URL drift")
    if data["python_version"] != "3.12.14":
        raise RuntimeError("frozen Python version drift")
    if data["openai_package_version"] != "3.13.0":
        raise RuntimeError("frozen OpenAI package version drift")

    order = data["execution_order"]
    if order["case_order"] != "round_robin_four_families":
        raise RuntimeError("case-order scheme drift")
    if order["condition_order"] != "family_balanced_cyclic_rotation_v1":
        raise RuntimeError("condition-order scheme drift")
    if order["within_family_position_count_range"] != [1, 2]:
        raise RuntimeError("within-family position gate drift")
    if int(order["global_position_count_per_condition"]) != 6:
        raise RuntimeError("global position gate drift")

    gate = data["family_gate"]
    expected_gate = {
        "minimum_mean_lift": 0.10,
        "minimum_strict_case_wins": 4,
        "minimum_valid_specialist_executions": 5,
        "catastrophic_failures_must_not_exceed_matched": True,
        "comparison_access_must_be_valid": True,
    }
    if gate != expected_gate:
        raise RuntimeError("family eligibility gate drift")

    failures = []
    for rel, expected in data["files"].items():
        path = ROOT / rel
        if not path.exists():
            failures.append(f"missing {rel}")
            continue
        actual = git_blob(path)
        if actual != expected:
            failures.append(f"{rel}: {actual} != {expected}")
    if failures:
        raise RuntimeError("frozen artifact validation failed:\n" + "\n".join(failures))

    if os.getenv("PHASE_B_ENFORCE_RUNTIME_ENV") == "1":
        if os.getenv("ZAI_TARGET_MODEL") != data["target_model"]:
            raise RuntimeError("runtime target model does not match freeze")
        if os.getenv("ZAI_BASE_URL") != data["provider_base_url"]:
            raise RuntimeError("runtime provider base URL does not match freeze")
        if int(os.getenv("ZAI_MAX_TOKENS", "0")) != data["completion_token_ceiling"]:
            raise RuntimeError("runtime completion ceiling does not match freeze")
        if float(os.getenv("ZAI_TEMPERATURE", "-1")) != float(data["temperature"]):
            raise RuntimeError("runtime temperature does not match freeze")
        if os.getenv("PHASE_B_V02_EXECUTION_AUTHORIZED") != "1":
            raise RuntimeError("v0.2 executable authorization flag is not set")
        runtime_python = ".".join(map(str, sys.version_info[:3]))
        if runtime_python != data["python_version"]:
            raise RuntimeError(f"runtime Python {runtime_python} does not match freeze")
        installed_openai = importlib.metadata.version("openai")
        if installed_openai != data["openai_package_version"]:
            raise RuntimeError(f"runtime openai {installed_openai} does not match freeze")
        expected_source = os.getenv("PHASE_B_V02_FROZEN_SOURCE_SHA")
        if not expected_source:
            raise RuntimeError("PHASE_B_V02_FROZEN_SOURCE_SHA is required at execution")
        actual_source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        if actual_source != expected_source:
            raise RuntimeError(
                f"runtime source {actual_source} does not match authorized source {expected_source}"
            )

    print("Process-Constrained Phase B v0.2 frozen artifacts validated")


if __name__ == "__main__":
    main()
