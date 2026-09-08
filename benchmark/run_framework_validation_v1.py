#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "heldout_cases_v1.json").read_text(encoding="utf-8"))

GENERATION_REPLICATES = int(os.getenv("FRAMEWORK_GENERATION_REPLICATES", "3"))
JUDGE_VOTES = int(os.getenv("FRAMEWORK_JUDGE_VOTES", "3"))
SHARD_INDEX = int(os.getenv("FRAMEWORK_SHARD_INDEX", "0"))
SHARD_COUNT = int(os.getenv("FRAMEWORK_SHARD_COUNT", "6"))
TARGET_FAMILY = os.getenv("FRAMEWORK_TARGET_FAMILY", "glm").strip().lower()
TARGET_PROVIDER = os.getenv("FRAMEWORK_TARGET_PROVIDER", "zai").strip().lower()
JUDGE_FAMILY = os.getenv("FRAMEWORK_JUDGE_FAMILY", "").strip().lower()
JUDGE_PROVIDER = os.getenv("FRAMEWORK_JUDGE_PROVIDER", "").strip().lower()
INDEPENDENCE_ATTESTATION = os.getenv("FRAMEWORK_INDEPENDENT_EVALUATOR_ATTESTATION", "").strip().lower()

FROZEN_TARGET_MODEL = "glm-5.1"
FROZEN_TARGET_BASE = "https://api.z.ai/api/coding/paas/v4"
FROZEN_TARGET_FAMILY = "glm"
FROZEN_TARGET_PROVIDER = "zai"

if GENERATION_REPLICATES != 3:
    raise ValueError("Framework held-out v1 requires exactly 3 target generations per case/condition")
if JUDGE_VOTES != 3:
    raise ValueError("Framework held-out v1 requires exactly 3 blinded judge votes per generated pair")
if SHARD_COUNT != 6 or not 0 <= SHARD_INDEX < SHARD_COUNT:
    raise ValueError("Framework held-out v1 requires exactly six shards indexed 0..5")

CONDITIONS = ("CONTROL", "COMPACT", "FULL")
PAIR_SPECS = [
    {
        "pair_id": "FULL_vs_CONTROL",
        "left": "FULL",
        "right": "CONTROL",
        "focal": "FULL",
        "role": "primary_framework_validation",
    },
    {
        "pair_id": "COMPACT_vs_CONTROL",
        "left": "COMPACT",
        "right": "CONTROL",
        "focal": "COMPACT",
        "role": "secondary_compact_validation",
    },
    {
        "pair_id": "FULL_vs_COMPACT",
        "left": "FULL",
        "right": "COMPACT",
        "focal": "FULL",
        "role": "secondary_architecture_depth",
    },
]

CONTROL: str | None = None
COMPACT = v03.pilot.COMPACT
FULL = v03.pilot.FULL


def normalize_url(value: str) -> str:
    return value.strip().lower().rstrip("/")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def independent_evaluator_preflight() -> None:
    if v03.TARGET_MODEL != FROZEN_TARGET_MODEL:
        raise RuntimeError(f"target model must remain {FROZEN_TARGET_MODEL!r}")
    if normalize_url(v03.TARGET_BASE) != normalize_url(FROZEN_TARGET_BASE):
        raise RuntimeError("target endpoint does not match frozen Z.AI endpoint")
    if TARGET_FAMILY != FROZEN_TARGET_FAMILY or TARGET_PROVIDER != FROZEN_TARGET_PROVIDER:
        raise RuntimeError("target family/provider labels do not match frozen target configuration")

    judge_key = os.getenv("ZAI_JUDGE_API_KEY", "")
    if not judge_key:
        raise RuntimeError("a separate ZAI_JUDGE_API_KEY is required; target-key fallback is forbidden")
    if not JUDGE_FAMILY or not JUDGE_PROVIDER:
        raise RuntimeError("independent judge family and provider labels are required")
    if v03.JUDGE_MODEL == v03.TARGET_MODEL:
        raise RuntimeError("independent evaluator required: target and judge model IDs are identical")
    if JUDGE_FAMILY == TARGET_FAMILY:
        raise RuntimeError("independent evaluator required: target and judge model families are identical")
    if JUDGE_PROVIDER == TARGET_PROVIDER:
        raise RuntimeError("independent evaluator required: target and judge provider labels are identical")
    if normalize_url(v03.JUDGE_BASE) == normalize_url(v03.TARGET_BASE):
        raise RuntimeError("independent evaluator required: target and judge endpoints are identical")
    if INDEPENDENCE_ATTESTATION != "true":
        raise RuntimeError("FRAMEWORK_INDEPENDENT_EVALUATOR_ATTESTATION=true is required")


def independent_evaluator_connectivity_check() -> dict[str, Any]:
    # This judge-only probe occurs before any held-out target-model call and
    # contains no benchmark content. It verifies credentials/model/JSON mode.
    system = 'Return JSON only with exactly this object: {"ok":true}'
    result = v03.judge_call(system, [{"role": "user", "content": "Independent evaluator connectivity check."}])
    parsed = v03.parse_json(result["text"])
    if parsed.get("ok") is not True:
        raise RuntimeError(f"independent judge connectivity check returned unexpected payload: {parsed}")
    return result["usage"]


def system_for(condition: str) -> str | None:
    if condition == "CONTROL":
        return CONTROL
    if condition == "COMPACT":
        return COMPACT
    if condition == "FULL":
        return FULL
    raise ValueError(condition)


def run_case(case: dict[str, Any], condition: str, replicate: int) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    messages: list[dict[str, str]] = []
    responses: list[dict[str, Any]] = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = v03.target_call(system_for(condition), messages)
        v03.add_usage(usage, result["usage"])
        responses.append({"turn": turn["turn"], "text": result["text"]})
        messages.append({"role": "assistant", "content": result["text"]})
    return {
        "case_id": case["case_id"],
        "domain": case["domain"],
        "routing_stratum": case["routing_stratum"],
        "condition": condition,
        "replicate": replicate,
        "responses": responses,
        "usage": usage,
    }


def quality_vote(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"heldout-framework-v1:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed).random() < 0.5:
        first, second = second, first
    last_turn = case["turns"][-1]["turn"]
    content = {
        **v05.quality_reference(case),
        "response_A": v03.transcript(case, first, last_turn),
        "response_B": v03.transcript(case, second, last_turn),
    }
    result = v03.judge_call(
        v05.QUALITY_PAIRWISE_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid held-out framework quality result: {parsed}")
    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    focal = spec["focal"]
    return {
        "case_id": case["case_id"],
        "domain": case["domain"],
        "routing_stratum": case["routing_stratum"],
        "sequential": case["design_metadata"]["sequential"],
        "has_distractors": case["design_metadata"]["has_distractors"],
        "requires_action": case["design_metadata"]["requires_action"],
        "replicate": run_x["replicate"],
        "pair_id": spec["pair_id"],
        "pair_role": spec["role"],
        "focal_condition": focal,
        "vote_index": vote_index,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": resolved,
        "focal_score": 0.5 if resolved == "TIE" else (1.0 if resolved == focal else 0.0),
        "confidence": parsed.get("confidence"),
        "margin": parsed.get("margin"),
        "decisive_dimensions": parsed.get("decisive_dimensions", []),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def main() -> None:
    # Every validity check, including live judge connectivity, occurs before
    # the first held-out target generation.
    independent_evaluator_preflight()
    connectivity_usage = independent_evaluator_connectivity_check()

    shard_cases = [case for i, case in enumerate(CASES) if i % SHARD_COUNT == SHARD_INDEX]
    if len(CASES) != 36 or len(shard_cases) != 6:
        raise RuntimeError(f"frozen suite/shard size mismatch: total={len(CASES)}, shard={len(shard_cases)}")

    out = ROOT / "results_framework_validation_v1"
    out.mkdir(exist_ok=True)
    runs_path = out / f"framework_v1_runs_shard_{SHARD_INDEX}.jsonl"
    votes_path = out / f"framework_v1_votes_shard_{SHARD_INDEX}.jsonl"
    meta_path = out / f"framework_v1_meta_shard_{SHARD_INDEX}.json"

    runs: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in shard_cases:
            for condition in CONDITIONS:
                print("generate", SHARD_INDEX, replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
                write_jsonl(runs_path, runs)

    index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in shard_cases:
            for spec in PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, JUDGE_VOTES + 1):
                    print("judge", SHARD_INDEX, replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    votes.append(quality_vote(case, left, right, spec, vote_index))
                    write_jsonl(votes_path, votes)

    meta = {
        "measurement_version": "heldout-framework-validation-v1",
        "experiment_role": "framework-level held-out validation; no routing",
        "suite": "heldout_cases_v1.json",
        "suite_freeze_commit": "2975376ade5df0863340ce10aa867f3b3e0e1404",
        "suite_git_blob_sha": "5fa2ab6f678728124b93ea9dd6c9158e5d6e9698",
        "shard_index": SHARD_INDEX,
        "shard_count": SHARD_COUNT,
        "case_ids": [c["case_id"] for c in shard_cases],
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes_per_pair": JUDGE_VOTES,
        "conditions": list(CONDITIONS),
        "prompt_sha256": {
            "CONTROL": None,
            "COMPACT": sha256_text(COMPACT),
            "FULL": sha256_text(FULL),
        },
        "target": {
            "model": v03.TARGET_MODEL,
            "family": TARGET_FAMILY,
            "provider": TARGET_PROVIDER,
            "base_url": v03.TARGET_BASE,
        },
        "judge": {
            "model": v03.JUDGE_MODEL,
            "family": JUDGE_FAMILY,
            "provider": JUDGE_PROVIDER,
            "base_url": v03.JUDGE_BASE,
            "connectivity_probe_usage": connectivity_usage,
        },
        "pair_specs": PAIR_SPECS,
        "n_runs": len(runs),
        "n_votes": len(votes),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
