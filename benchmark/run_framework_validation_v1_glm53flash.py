#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

import run_framework_validation_v1 as base

EXPECTED_JUDGE_MODEL = "glm-5.3-flash"
EXPECTED_FAMILY = "glm"
EXPECTED_PROVIDER = "zai"
EXPECTED_BASE = base.FROZEN_TARGET_BASE
ATTESTATION = os.getenv("FRAMEWORK_CROSS_MODEL_SAME_FAMILY_ATTESTATION", "").strip().lower()


def cross_model_same_family_preflight() -> None:
    if base.v03.TARGET_MODEL != base.FROZEN_TARGET_MODEL:
        raise RuntimeError(f"target model must remain {base.FROZEN_TARGET_MODEL!r}")
    if base.normalize_url(base.v03.TARGET_BASE) != base.normalize_url(base.FROZEN_TARGET_BASE):
        raise RuntimeError("target endpoint does not match frozen Z.AI endpoint")
    if base.TARGET_FAMILY != EXPECTED_FAMILY or base.TARGET_PROVIDER != EXPECTED_PROVIDER:
        raise RuntimeError("target family/provider labels do not match frozen GLM/Z.AI target")

    judge_key = os.getenv("ZAI_JUDGE_API_KEY", "")
    if not judge_key:
        raise RuntimeError("ZAI_JUDGE_API_KEY is required for the GLM-5.3-Flash judge")
    if base.v03.JUDGE_MODEL != EXPECTED_JUDGE_MODEL:
        raise RuntimeError(f"judge model must be exactly {EXPECTED_JUDGE_MODEL!r}")
    if base.v03.JUDGE_MODEL == base.v03.TARGET_MODEL:
        raise RuntimeError("cross-model evaluation requires distinct target and judge model IDs")
    if base.JUDGE_FAMILY != EXPECTED_FAMILY or base.JUDGE_PROVIDER != EXPECTED_PROVIDER:
        raise RuntimeError("judge must be explicitly labeled glm/zai for this same-family tier")
    if base.normalize_url(base.v03.JUDGE_BASE) != base.normalize_url(EXPECTED_BASE):
        raise RuntimeError("judge endpoint must be the frozen Z.AI coding endpoint for this tier")
    if ATTESTATION != "true":
        raise RuntimeError("FRAMEWORK_CROSS_MODEL_SAME_FAMILY_ATTESTATION=true is required")


def cross_model_connectivity_check() -> dict:
    system = 'Return JSON only with exactly this object: {"ok":true}'
    result = base.v03.judge_call(system, [{"role": "user", "content": "Cross-model evaluator connectivity check."}])
    parsed = base.v03.parse_json(result["text"])
    if parsed.get("ok") is not True:
        raise RuntimeError(f"GLM-5.3-Flash connectivity check returned unexpected payload: {parsed}")
    return result["usage"]


def annotate_meta() -> None:
    path = Path(__file__).resolve().parent / "results_framework_validation_v1" / f"framework_v1_meta_shard_{base.SHARD_INDEX}.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["measurement_version"] = "heldout-framework-validation-v1-glm53flash"
    meta["experiment_role"] = "framework-level held-out validation; cross-model same-family judge; no routing"
    meta["evaluation_tier"] = "Tier-1B cross-model same-family; not independent-provider evaluation"
    meta["independent_evaluator"] = False
    meta["same_family_cross_model"] = True
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    base.independent_evaluator_preflight = cross_model_same_family_preflight
    base.independent_evaluator_connectivity_check = cross_model_connectivity_check
    base.main()
    annotate_meta()


if __name__ == "__main__":
    main()
