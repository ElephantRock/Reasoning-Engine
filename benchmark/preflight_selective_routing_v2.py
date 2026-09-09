#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402
import selective_router_v1 as router_v1  # noqa: E402
from load_routing_validation_v2 import load_cases, suite_digest  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
FROZEN_TARGET_MODEL = "glm-5.1"
FROZEN_JUDGE_MODEL = "glm-5.3-flash"
FROZEN_ROUTER_MODEL = "glm-5.3-flash"
FROZEN_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
FROZEN_ROUTER_GIT_BLOB = "a64fb4ed1dba3c7509163ab62831c2fe0cd81cc6"
ATTESTATION = os.getenv("ROUTING_V2_SAME_FAMILY_ATTESTATION", "").strip().lower()


def norm(value: str) -> str:
    return value.strip().lower().rstrip("/")


def validate_frozen_configuration() -> dict:
    cases = load_cases()
    if v03.TARGET_MODEL != FROZEN_TARGET_MODEL:
        raise RuntimeError(f"target model must be exactly {FROZEN_TARGET_MODEL}")
    if v03.JUDGE_MODEL != FROZEN_JUDGE_MODEL:
        raise RuntimeError(f"judge model must be exactly {FROZEN_JUDGE_MODEL}")
    if router_v1.ROUTER_MODEL != FROZEN_ROUTER_MODEL:
        raise RuntimeError(f"router model must be exactly {FROZEN_ROUTER_MODEL}")
    if norm(v03.TARGET_BASE) != norm(FROZEN_BASE_URL):
        raise RuntimeError("target endpoint mismatch")
    if norm(v03.JUDGE_BASE) != norm(FROZEN_BASE_URL):
        raise RuntimeError("judge endpoint mismatch")
    if norm(router_v1.ROUTER_BASE_URL) != norm(FROZEN_BASE_URL):
        raise RuntimeError("router endpoint mismatch")
    if not os.getenv("ZAI_API_KEY"):
        raise RuntimeError("ZAI_API_KEY is required")
    if not os.getenv("ZAI_JUDGE_API_KEY"):
        raise RuntimeError("ZAI_JUDGE_API_KEY is required")
    if ATTESTATION != "true":
        raise RuntimeError("ROUTING_V2_SAME_FAMILY_ATTESTATION=true is required")

    blob = subprocess.check_output(
        ["git", "hash-object", str(ROOT / "selective_router_v1.py")],
        cwd=REPO_ROOT,
        text=True,
    ).strip()
    if blob != FROZEN_ROUTER_GIT_BLOB:
        raise RuntimeError(f"router implementation blob changed: {blob}")

    return {
        "n_cases": len(cases),
        "suite_sha256": suite_digest(),
        "router_git_blob": blob,
        "full_prompt_sha256": hashlib.sha256(v03.pilot.FULL.encode("utf-8")).hexdigest(),
        "router_prompt_sha256": hashlib.sha256(router_v1.ROUTER_V1.encode("utf-8")).hexdigest(),
    }


def connectivity() -> dict:
    # Benchmark-free, one-time connectivity only. Do not require an exact semantic payload.
    judge = v03.judge_call(
        'Return a JSON object confirming connectivity. JSON only.',
        [{"role": "user", "content": "Connectivity probe only; no benchmark content."}],
    )
    payload = v03.parse_json(judge["text"])
    if not isinstance(payload, dict):
        raise RuntimeError("judge connectivity response was not a JSON object")

    route = router_v1.route_text("What is 7 + 5? Answer the arithmetic question.")
    if route.get("mode") not in {"FULL", "CONTROL"}:
        raise RuntimeError("router connectivity did not return a valid route")

    return {
        "judge_usage": judge["usage"],
        "router_usage": route["usage"],
        "router_probe_mode": route["mode"],
    }


def main() -> None:
    frozen = validate_frozen_configuration()
    live = connectivity()
    print(json.dumps({"frozen": frozen, "connectivity": live}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
