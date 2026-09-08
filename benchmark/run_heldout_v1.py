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
import run_v06 as v06  # noqa: E402
import run_v07 as v07  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "heldout_cases_v1.json").read_text(encoding="utf-8"))
CANDIDATE_PATH = ROOT / "heldout_candidate_v1.json"

GENERATION_REPLICATES = max(1, int(os.getenv("HELDOUT_GENERATION_REPLICATES", "3")))
JUDGE_VOTES = int(os.getenv("HELDOUT_JUDGE_VOTES", "3"))
SHARD_INDEX = int(os.getenv("HELDOUT_SHARD_INDEX", "0"))
SHARD_COUNT = int(os.getenv("HELDOUT_SHARD_COUNT", "6"))
TARGET_FAMILY = os.getenv("HELDOUT_TARGET_FAMILY", "glm").strip().lower()
JUDGE_FAMILY = os.getenv("HELDOUT_JUDGE_FAMILY", "").strip().lower()

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("HELDOUT_JUDGE_VOTES must be an odd integer >= 3")
if GENERATION_REPLICATES != 3:
    raise ValueError("Held-out validation v1 requires exactly 3 target generations per case/condition")
if JUDGE_VOTES != 3:
    raise ValueError("Held-out validation v1 requires exactly 3 blinded quality votes per generated pair")
if SHARD_COUNT != 6 or not 0 <= SHARD_INDEX < SHARD_COUNT:
    raise ValueError("Held-out validation v1 requires exactly six shards indexed 0..5")

CONDITIONS = ("CONTROL", "ATTENTION", "CANDIDATE_POLICY", "FULL")
PAIR_SPECS = [
    {
        "pair_id": "CANDIDATE_POLICY_vs_CONTROL",
        "left": "CANDIDATE_POLICY",
        "right": "CONTROL",
        "focal": "CANDIDATE_POLICY",
        "role": "primary_heldout_quality",
    },
    {
        "pair_id": "CANDIDATE_POLICY_vs_ATTENTION",
        "left": "CANDIDATE_POLICY",
        "right": "ATTENTION",
        "focal": "CANDIDATE_POLICY",
        "role": "secondary_specificity",
    },
    {
        "pair_id": "FULL_vs_CONTROL",
        "left": "FULL",
        "right": "CONTROL",
        "focal": "FULL",
        "role": "descriptive_development_reference",
    },
]

CONTROL = v07.CORE
ATTENTION = v07.ATTENTION
FROZEN_MODULES = {
    "TEST": v06.STAGE_ADDONS["TEST"],
    "ENGINEER": v07.TARGET_MODULES["ENGINEER"],
}
FULL = v03.pilot.FULL


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def load_candidate() -> dict[str, Any]:
    if not CANDIDATE_PATH.exists():
        raise RuntimeError(
            "heldout_candidate_v1.json does not exist. It may be created only after v0.11 is complete "
            "and the preregistered post-v0.11 decision rule has been applied."
        )
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    required = {
        "candidate_version",
        "source_v011_run_id",
        "decision_protocol_commit",
        "selected_modules",
        "module_sha256",
        "selection_record",
    }
    if set(candidate) != required:
        raise RuntimeError(f"invalid candidate config fields: {sorted(candidate)}")
    if candidate["candidate_version"] != "heldout-v1-frozen-candidate":
        raise RuntimeError("candidate_version mismatch")
    if int(candidate["source_v011_run_id"]) != 34182916670:
        raise RuntimeError("candidate must be selected from the frozen v0.11 run 34182916670")
    if candidate["decision_protocol_commit"] != "c29ab7766f01e3345f2e01ccb0b2969555138e5f":
        raise RuntimeError("candidate decision protocol commit mismatch")

    selected = candidate["selected_modules"]
    if not isinstance(selected, list) or len(selected) != len(set(selected)):
        raise RuntimeError("selected_modules must be a unique list")
    if not set(selected).issubset(FROZEN_MODULES):
        raise RuntimeError(f"unsupported selected module(s): {selected}")
    if not selected:
        raise RuntimeError(
            "No module survived the locked v0.11 selection rule. Do not launch an intervention validation run."
        )

    expected_hashes = {name: sha256_text(FROZEN_MODULES[name]) for name in selected}
    if candidate["module_sha256"] != expected_hashes:
        raise RuntimeError("candidate module hashes do not match the frozen development modules")
    return candidate


def independent_evaluator_preflight() -> None:
    judge_key = os.getenv("ZAI_JUDGE_API_KEY", "")
    if not judge_key:
        raise RuntimeError("ZAI_JUDGE_API_KEY is required for held-out validation; target-key fallback is forbidden")
    if not JUDGE_FAMILY:
        raise RuntimeError("HELDOUT_JUDGE_FAMILY must identify the independent evaluator model family")
    if JUDGE_FAMILY == TARGET_FAMILY:
        raise RuntimeError(
            f"independent evaluator required: target family={TARGET_FAMILY!r}, judge family={JUDGE_FAMILY!r}"
        )
    if v03.JUDGE_MODEL == v03.TARGET_MODEL:
        raise RuntimeError("independent evaluator required: target and judge model IDs are identical")
    if os.getenv("HELDOUT_INDEPENDENT_EVALUATOR_ATTESTATION", "").strip().lower() != "true":
        raise RuntimeError(
            "HELDOUT_INDEPENDENT_EVALUATOR_ATTESTATION=true is required to attest that the configured judge "
            "belongs to a different model family/provider and is independent of target generation"
        )


def selected_modules_for_case(case: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    selected = set(candidate["selected_modules"])
    stratum = case["routing_stratum"]
    requested: list[str] = []
    if stratum in {"TEST", "BOTH"} and "TEST" in selected:
        requested.append("TEST")
    if stratum in {"ENGINEER", "BOTH"} and "ENGINEER" in selected:
        requested.append("ENGINEER")
    return requested


def candidate_system(case: dict[str, Any], candidate: dict[str, Any]) -> str:
    modules = selected_modules_for_case(case, candidate)
    if not modules:
        return CONTROL
    return CONTROL + "".join(FROZEN_MODULES[name] for name in modules)


def system_for(case: dict[str, Any], condition: str, candidate: dict[str, Any]) -> str:
    if condition == "CONTROL":
        return CONTROL
    if condition == "ATTENTION":
        return ATTENTION
    if condition == "CANDIDATE_POLICY":
        return candidate_system(case, candidate)
    if condition == "FULL":
        return FULL
    raise ValueError(condition)


def run_case(case: dict[str, Any], condition: str, replicate: int, candidate: dict[str, Any]) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    messages: list[dict[str, str]] = []
    responses: list[dict[str, Any]] = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = v03.target_call(system_for(case, condition, candidate), messages)
        v03.add_usage(usage, result["usage"])
        responses.append({"turn": turn["turn"], "text": result["text"]})
        messages.append({"role": "assistant", "content": result["text"]})
    return {
        "case_id": case["case_id"],
        "domain": case["domain"],
        "routing_stratum": case["routing_stratum"],
        "condition": condition,
        "replicate": replicate,
        "candidate_modules_applied": selected_modules_for_case(case, candidate) if condition == "CANDIDATE_POLICY" else [],
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
    seed = f"heldout-v1:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
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
        raise RuntimeError(f"invalid held-out quality result: {parsed}")
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
    # All validity gates run before the first target-model call.
    candidate = load_candidate()
    independent_evaluator_preflight()

    shard_cases = [case for i, case in enumerate(CASES) if i % SHARD_COUNT == SHARD_INDEX]
    if len(shard_cases) != 6:
        raise RuntimeError(f"expected 6 cases in shard {SHARD_INDEX}, found {len(shard_cases)}")

    out = ROOT / "results_heldout_v1"
    out.mkdir(exist_ok=True)
    runs_path = out / f"heldout_v1_runs_shard_{SHARD_INDEX}.jsonl"
    votes_path = out / f"heldout_v1_votes_shard_{SHARD_INDEX}.jsonl"
    meta_path = out / f"heldout_v1_meta_shard_{SHARD_INDEX}.json"

    runs: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in shard_cases:
            for condition in CONDITIONS:
                print("generate", SHARD_INDEX, replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate, candidate))
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
        "measurement_version": "heldout-validation-v1",
        "experiment_role": "oracle-stratified held-out module validation",
        "shard_index": SHARD_INDEX,
        "shard_count": SHARD_COUNT,
        "case_ids": [c["case_id"] for c in shard_cases],
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes_per_pair": JUDGE_VOTES,
        "candidate": candidate,
        "target": {"model": v03.TARGET_MODEL, "family": TARGET_FAMILY, "base_url": v03.TARGET_BASE},
        "judge": {"model": v03.JUDGE_MODEL, "family": JUDGE_FAMILY, "base_url": v03.JUDGE_BASE},
        "pair_specs": PAIR_SPECS,
        "n_runs": len(runs),
        "n_votes": len(votes),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
