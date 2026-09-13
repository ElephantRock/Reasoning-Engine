#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "benchmark/process_phase_b_freeze_v01.json"


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data["measurement_version"] != "process-constrained-phase-b-v0.1":
        raise RuntimeError("measurement version drift")
    if data["target_model"] != "glm-5.1":
        raise RuntimeError("target model drift")
    if int(data["completion_token_ceiling"]) != 16384:
        raise RuntimeError("completion ceiling drift")
    if float(data["temperature"]) != 0.0:
        raise RuntimeError("temperature drift")
    expected_conditions = ["SPECIALIST", "MATCHED_SCAFFOLD", "FULL", "CONTROL"]
    if data["conditions"] != expected_conditions:
        raise RuntimeError("condition set/order drift")

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

    # When running the paid workflow, environment values must match the freeze.
    if os.getenv("PHASE_B_ENFORCE_RUNTIME_ENV") == "1":
        if os.getenv("ZAI_TARGET_MODEL") != data["target_model"]:
            raise RuntimeError("runtime target model does not match freeze")
        if int(os.getenv("ZAI_MAX_TOKENS", "0")) != data["completion_token_ceiling"]:
            raise RuntimeError("runtime completion ceiling does not match freeze")
        if float(os.getenv("ZAI_TEMPERATURE", "-1")) != float(data["temperature"]):
            raise RuntimeError("runtime temperature does not match freeze")

    print("Process-Constrained Phase B v0.1 frozen artifacts validated")


if __name__ == "__main__":
    main()
