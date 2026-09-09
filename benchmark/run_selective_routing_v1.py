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
import selective_router_v1 as router_v1  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "routing_validation_cases_v1.json").read_text(encoding="utf-8"))

GENERATION_REPLICATES = int(os.getenv("ROUTING_V1_GENERATION_REPLICATES", "3"))
JUDGE_VOTES = int(os.getenv("ROUTING_V1_JUDGE_VOTES", "3"))
SHARD_INDEX = int(os.getenv("ROUTING_V1_SHARD_INDEX", "0"))
SHARD_COUNT = int(os.getenv("ROUTING_V1_SHARD_COUNT", "6"))
BOOTSTRAP_SAMPLES = int(os.getenv("BENCHMARK_BOOTSTRAP_SAMPLES", "5000"))
ATTESTATION = os.getenv("ROUTING_V1_SAME_FAMILY_ATTESTATION", "").strip().lower()
MAX_FORMAT_ATTEMPTS = 3

FROZEN_TARGET_MODEL = "glm-5.1"
FROZEN_JUDGE_MODEL = "glm-5.3-flash"
FROZEN_ROUTER_MODEL = "glm-5.3-flash"
FROZEN_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
CONDITIONS = ("CONTROL", "FULL")
PAIR_SPEC = {
    "pair_id": "FULL_vs_CONTROL",
    "left": "FULL",
    "right": "CONTROL",
    "focal": "FULL",
    "role": "routing_quality_base_pair",
}
FULL = v03.pilot.FULL
CONTROL: str | None = None

if GENERATION_REPLICATES != 3:
    raise ValueError("Selective Routing v1 requires exactly 3 target generations")
if JUDGE_VOTES != 3:
    raise ValueError("Selective Routing v1 requires exactly 3 judge votes per pair")
if SHARD_COUNT != 6 or not 0 <= SHARD_INDEX < 6:
    raise ValueError("Selective Routing v1 requires six shards indexed 0..5")
if BOOTSTRAP_SAMPLES != 5000:
    raise ValueError("Selective Routing v1 requires exactly 5000 bootstrap samples")


def normalize_url(value: str) -> str:
    return value.strip().lower().rstrip("/")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def parse_first_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    stripped = text.strip()
    try:
        value = json.loads(stripped)
        if not isinstance(value, dict):
            raise ValueError("judge output must be an object")
        return value
    except json.JSONDecodeError as original:
        for index, char in enumerate(stripped):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(stripped[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise original


def preflight() -> None:
    if len(CASES) != 48:
        raise RuntimeError(f"routing suite must contain 48 cases, found {len(CASES)}")
    if len({case["case_id"] for case in CASES}) != 48:
        raise RuntimeError("routing suite case IDs must be unique")
    if v03.TARGET_MODEL != FROZEN_TARGET_MODEL:
        raise RuntimeError(f"target model must be exactly {FROZEN_TARGET_MODEL}")
    if v03.JUDGE_MODEL != FROZEN_JUDGE_MODEL:
        raise RuntimeError(f"judge model must be exactly {FROZEN_JUDGE_MODEL}")
    if router_v1.ROUTER_MODEL != FROZEN_ROUTER_MODEL:
        raise RuntimeError(f"router model must be exactly {FROZEN_ROUTER_MODEL}")
    if normalize_url(v03.TARGET_BASE) != normalize_url(FROZEN_BASE_URL):
        raise RuntimeError("target endpoint must remain the frozen Z.AI endpoint")
    if normalize_url(v03.JUDGE_BASE) != normalize_url(FROZEN_BASE_URL):
        raise RuntimeError("judge endpoint must remain the frozen Z.AI endpoint")
    if normalize_url(router_v1.ROUTER_BASE_URL) != normalize_url(FROZEN_BASE_URL):
        raise RuntimeError("router endpoint must remain the frozen Z.AI endpoint")
    if not os.getenv("ZAI_API_KEY"):
        raise RuntimeError("ZAI_API_KEY is required")
    if not os.getenv("ZAI_JUDGE_API_KEY"):
        raise RuntimeError("ZAI_JUDGE_API_KEY is required")
    if ATTESTATION != "true":
        raise RuntimeError("ROUTING_V1_SAME_FAMILY_ATTESTATION=true is required")


def connectivity_checks() -> dict[str, Any]:
    judge_probe = v03.judge_call(
        'Return JSON only with exactly this object: {"ok":true}',
        [{"role": "user", "content": "Selective-routing judge connectivity check; no benchmark content."}],
    )
    judge_payload = parse_first_json_object(judge_probe["text"])
    if judge_payload.get("ok") is not True:
        raise RuntimeError(f"judge connectivity check failed: {judge_payload}")
    router_probe = router_v1.route_text("What is 2 + 2? Give only the answer.")
    if router_probe["mode"] != "CONTROL":
        raise RuntimeError(f"router benchmark-free sanity probe should route CONTROL, got {router_probe}")
    return {"judge_usage": judge_probe["usage"], "router_usage": router_probe["usage"]}


def system_for(condition: str) -> str | None:
    if condition == "CONTROL":
        return CONTROL
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
        "author_route_label": case["author_route_label"],
        "condition": condition,
        "replicate": replicate,
        "responses": responses,
        "usage": usage,
    }


def quality_vote(
    case: dict[str, Any],
    full_run: dict[str, Any],
    control_run: dict[str, Any],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"selective-routing-v1:{case['case_id']}:{full_run['replicate']}:{vote_index}"
    first, second = full_run, control_run
    if random.Random(seed).random() < 0.5:
        first, second = second, first
    last_turn = case["turns"][-1]["turn"]
    content = {
        **v05.quality_reference(case),
        "response_A": v03.transcript(case, first, last_turn),
        "response_B": v03.transcript(case, second, last_turn),
    }
    last_error: Exception | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        result = v03.judge_call(
            v05.QUALITY_PAIRWISE_JUDGE,
            [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
        )
        try:
            parsed = parse_first_json_object(result["text"])
            winner = parsed.get("winner")
            if winner not in {"A", "B", "TIE"}:
                raise RuntimeError(f"invalid winner: {parsed}")
        except (json.JSONDecodeError, RuntimeError, ValueError) as exc:
            last_error = exc
            if attempt == MAX_FORMAT_ATTEMPTS:
                raise RuntimeError("quality judge failed formatting after 3 attempts") from exc
            continue
        resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
        return {
            "case_id": case["case_id"],
            "domain": case["domain"],
            "author_route_label": case["author_route_label"],
            "sequential": bool(case["design_metadata"]["sequential"]),
            "has_distractors": bool(case["design_metadata"]["has_distractors"]),
            "requires_action": bool(case["design_metadata"]["requires_action"]),
            "adversarial_surface": bool(case["design_metadata"].get("adversarial_surface", False)),
            "replicate": full_run["replicate"],
            "pair_id": PAIR_SPEC["pair_id"],
            "pair_role": PAIR_SPEC["role"],
            "focal_condition": "FULL",
            "vote_index": vote_index,
            "A_condition": first["condition"],
            "B_condition": second["condition"],
            "winner": resolved,
            "focal_score": 0.5 if resolved == "TIE" else (1.0 if resolved == "FULL" else 0.0),
            "confidence": parsed.get("confidence"),
            "margin": parsed.get("margin"),
            "decisive_dimensions": parsed.get("decisive_dimensions", []),
            "notes": parsed.get("notes", ""),
            "judge_usage": result["usage"],
            "format_attempts": attempt,
        }
    raise last_error or RuntimeError("quality judge failed")


def main() -> None:
    preflight()
    connectivity = connectivity_checks()
    shard_cases = [case for index, case in enumerate(CASES) if index % SHARD_COUNT == SHARD_INDEX]
    if len(shard_cases) != 8:
        raise RuntimeError(f"each routing shard must contain 8 cases, found {len(shard_cases)}")

    out = ROOT / "results_routing_validation_v1"
    out.mkdir(exist_ok=True)
    routes_path = out / f"routing_v1_routes_shard_{SHARD_INDEX}.jsonl"
    runs_path = out / f"routing_v1_runs_shard_{SHARD_INDEX}.jsonl"
    votes_path = out / f"routing_v1_votes_shard_{SHARD_INDEX}.jsonl"
    meta_path = out / f"routing_v1_meta_shard_{SHARD_INDEX}.json"

    routes: list[dict[str, Any]] = []
    for case in shard_cases:
        print("route", SHARD_INDEX, case["case_id"], flush=True)
        decision = router_v1.route_case(case)
        routes.append({
            "case_id": case["case_id"],
            "domain": case["domain"],
            "author_route_label": case["author_route_label"],
            "selected_mode": decision["mode"],
            "signals": decision["signals"],
            "confidence": decision["confidence"],
            "usage": decision["usage"],
            "format_attempts": decision["format_attempts"],
        })
        write_jsonl(routes_path, routes)

    runs: list[dict[str, Any]] = []
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in shard_cases:
            for condition in CONDITIONS:
                print("generate", SHARD_INDEX, replicate, case["case_id"], condition, flush=True)
                runs.append(run_case(case, condition, replicate))
                write_jsonl(runs_path, runs)

    index = {(run["case_id"], run["condition"], run["replicate"]): run for run in runs}
    votes: list[dict[str, Any]] = []
    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in shard_cases:
            full_run = index[(case["case_id"], "FULL", replicate)]
            control_run = index[(case["case_id"], "CONTROL", replicate)]
            for vote_index in range(1, JUDGE_VOTES + 1):
                print("judge", SHARD_INDEX, replicate, case["case_id"], vote_index, flush=True)
                votes.append(quality_vote(case, full_run, control_run, vote_index))
                write_jsonl(votes_path, votes)

    meta = {
        "measurement_version": "selective-routing-v1",
        "experiment_role": "fresh selective-routing validation; binary FULL vs CONTROL; Tier-1B same-family judging",
        "evaluation_tier": "Tier-1B cross-model same-family; not independent-provider evaluation",
        "shard_index": SHARD_INDEX,
        "shard_count": SHARD_COUNT,
        "case_ids": [case["case_id"] for case in shard_cases],
        "suite": "routing_validation_cases_v1.json",
        "suite_sha256": sha256_file(ROOT / "routing_validation_cases_v1.json"),
        "n_cases_total": len(CASES),
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes_per_pair": JUDGE_VOTES,
        "conditions": list(CONDITIONS),
        "full_prompt_sha256": sha256_text(FULL),
        "router_prompt_sha256": sha256_text(router_v1.ROUTER_V1),
        "target": {"model": v03.TARGET_MODEL, "base_url": v03.TARGET_BASE, "family": "glm", "provider": "zai"},
        "judge": {"model": v03.JUDGE_MODEL, "base_url": v03.JUDGE_BASE, "family": "glm", "provider": "zai"},
        "router": {"model": router_v1.ROUTER_MODEL, "base_url": router_v1.ROUTER_BASE_URL, "family": "glm", "provider": "zai", "temperature": 0},
        "same_family_cross_model_attestation": True,
        "connectivity_probe_usage": connectivity,
        "pair_spec": PAIR_SPEC,
        "policy_construction": {
            "ROUTED_vs_CONTROL": "FULL_vs_CONTROL replicate score if routed FULL, else 0.5",
            "ROUTED_vs_FULL": "0.5 if routed FULL, else 1 - FULL_vs_CONTROL replicate score",
        },
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"shard": SHARD_INDEX, "routes": len(routes), "runs": len(runs), "votes": len(votes)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
