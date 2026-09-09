#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import run_framework_validation_v1 as base  # noqa: E402

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source_framework_validation_v1"
RESULTS = ROOT / "results_framework_validation_v1"
SOURCE_RUN_ID = 34270142523
EXPECTED_RUNS_PER_SHARD = 54
EXPECTED_VOTES_PER_SHARD = 162
MAX_FORMAT_ATTEMPTS = 3

SOURCE_ARTIFACT_DIGESTS = {
    0: "sha256:b4300a47e880f26618648fcc0efffa1068924e75147a3136b1f78acd68922568",
    1: "sha256:1aa15f29b546c1fbb1e0d5670062d7be4be02c1acf86144c1c6f1fa13264e863",
    2: "sha256:1cd73a393eedf7c8e584dd70ca6036705978b3e6e358c13aba441eb75ae8561c",
    3: "sha256:176a0a7aa3507eb6eb7b77d6f726b3b96b081462d1efa5140a126385182e2563",
    4: "sha256:ac722072fce97a893e0ce0bc326db42721b3c140ccfeb896b2ab21ad4b57d28f",
    5: "sha256:458e78e78ce9c2e9715fd9b9f87673d853c5b1a4cacb3d48bd497b5c8207151b",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_first_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for pos, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[pos:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise json.JSONDecodeError("no complete JSON object found", text, 0)


def expected_run_keys(shard_cases: list[dict[str, Any]]) -> set[tuple[str, str, int]]:
    return {
        (case["case_id"], condition, replicate)
        for case in shard_cases
        for condition in base.CONDITIONS
        for replicate in range(1, base.GENERATION_REPLICATES + 1)
    }


def validate_source_checkpoint(
    runs: list[dict[str, Any]],
    meta: dict[str, Any],
    shard_cases: list[dict[str, Any]],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    expected = expected_run_keys(shard_cases)
    actual = [(r["case_id"], r["condition"], r["replicate"]) for r in runs]
    if len(runs) != EXPECTED_RUNS_PER_SHARD or len(set(actual)) != EXPECTED_RUNS_PER_SHARD:
        raise RuntimeError("source checkpoint must contain exactly 54 unique target runs")
    if set(actual) != expected:
        raise RuntimeError("source checkpoint target-run keys do not match frozen shard")

    if meta.get("suite") != "heldout_cases_v1.json":
        raise RuntimeError("source checkpoint suite mismatch")
    if meta.get("suite_freeze_commit") != "2975376ade5df0863340ce10aa867f3b3e0e1404":
        raise RuntimeError("source checkpoint suite freeze mismatch")
    if meta.get("suite_git_blob_sha") != "5fa2ab6f678728124b93ea9dd6c9158e5d6e9698":
        raise RuntimeError("source checkpoint suite blob mismatch")
    if meta.get("generation_replicates") != 3 or meta.get("judge_votes_per_pair") != 3:
        raise RuntimeError("source checkpoint replicate/vote design mismatch")
    if tuple(meta.get("conditions", [])) != base.CONDITIONS:
        raise RuntimeError("source checkpoint conditions mismatch")
    if meta.get("prompt_sha256") != {
        "CONTROL": None,
        "COMPACT": base.sha256_text(base.COMPACT),
        "FULL": base.sha256_text(base.FULL),
    }:
        raise RuntimeError("source checkpoint prompt hashes mismatch")

    target = meta.get("target", {})
    if target.get("model") != base.FROZEN_TARGET_MODEL:
        raise RuntimeError("source checkpoint target model mismatch")
    if base.normalize_url(target.get("base_url", "")) != base.normalize_url(base.FROZEN_TARGET_BASE):
        raise RuntimeError("source checkpoint target endpoint mismatch")
    if target.get("family") != base.FROZEN_TARGET_FAMILY or target.get("provider") != base.FROZEN_TARGET_PROVIDER:
        raise RuntimeError("source checkpoint target family/provider mismatch")

    recovery = meta.get("execution_recovery", {})
    if recovery.get("source_run_id") != 34232674771:
        raise RuntimeError("source checkpoint recovery provenance mismatch")
    if recovery.get("retained_target_runs") != EXPECTED_RUNS_PER_SHARD:
        raise RuntimeError("source checkpoint did not retain all target outputs")
    if recovery.get("target_regeneration_allowed") is not False:
        raise RuntimeError("source checkpoint provenance does not forbid target regeneration")

    return {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}


def independent_preflight() -> None:
    base.independent_evaluator_preflight()


def independent_connectivity_check() -> dict[str, Any]:
    system = 'Return JSON only with exactly this object: {"ok":true}'
    result = base.v03.judge_call(
        system,
        [{"role": "user", "content": "Independent evaluator connectivity check."}],
    )
    parsed = parse_first_json_object(result["text"])
    if parsed.get("ok") is not True:
        raise RuntimeError(f"independent evaluator connectivity check returned unexpected payload: {parsed}")
    return result["usage"]


def independent_quality_vote(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> tuple[dict[str, Any], int]:
    seed = f"heldout-framework-v1:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed).random() < 0.5:
        first, second = second, first

    last_turn = case["turns"][-1]["turn"]
    content = {
        **base.v05.quality_reference(case),
        "response_A": base.v03.transcript(case, first, last_turn),
        "response_B": base.v03.transcript(case, second, last_turn),
    }

    last_error: Exception | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        result = base.v03.judge_call(
            base.v05.QUALITY_PAIRWISE_JUDGE,
            [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
        )
        try:
            parsed = parse_first_json_object(result["text"])
            winner = parsed.get("winner")
            if winner not in {"A", "B", "TIE"}:
                raise RuntimeError(f"invalid independent quality result: {parsed}")
        except (json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            if attempt == MAX_FORMAT_ATTEMPTS:
                raise RuntimeError(
                    f"independent judge failed format contract after {MAX_FORMAT_ATTEMPTS} attempts"
                ) from exc
            continue

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
        }, attempt - 1

    raise AssertionError(last_error)


def main() -> None:
    independent_preflight()
    connectivity_usage = independent_connectivity_check()

    shard_index = base.SHARD_INDEX
    shard_cases = [case for i, case in enumerate(base.CASES) if i % base.SHARD_COUNT == shard_index]
    if len(base.CASES) != 36 or len(shard_cases) != 6:
        raise RuntimeError("frozen suite/shard size mismatch")

    source_runs_path = SOURCE / f"framework_v1_runs_shard_{shard_index}.jsonl"
    source_meta_path = SOURCE / f"framework_v1_meta_shard_{shard_index}.json"
    runs = read_jsonl(source_runs_path)
    source_meta = json.loads(source_meta_path.read_text(encoding="utf-8"))
    index = validate_source_checkpoint(runs, source_meta, shard_cases)

    RESULTS.mkdir(exist_ok=True)
    runs_path = RESULTS / f"framework_v1_runs_shard_{shard_index}.jsonl"
    votes_path = RESULTS / f"framework_v1_votes_shard_{shard_index}.jsonl"
    meta_path = RESULTS / f"framework_v1_meta_shard_{shard_index}.json"
    base.write_jsonl(runs_path, runs)

    votes: list[dict[str, Any]] = []
    format_retries = 0
    for replicate in range(1, base.GENERATION_REPLICATES + 1):
        for case in shard_cases:
            for spec in base.PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, base.JUDGE_VOTES + 1):
                    print(
                        "independent-judge",
                        shard_index,
                        replicate,
                        case["case_id"],
                        spec["pair_id"],
                        vote_index,
                        flush=True,
                    )
                    vote, retries = independent_quality_vote(case, left, right, spec, vote_index)
                    format_retries += retries
                    votes.append(vote)
                    base.write_jsonl(votes_path, votes)

    if len(votes) != EXPECTED_VOTES_PER_SHARD:
        raise RuntimeError(f"expected {EXPECTED_VOTES_PER_SHARD} independent votes, found {len(votes)}")

    meta = {
        "measurement_version": "heldout-framework-validation-v1-independent-rejudge",
        "experiment_role": "independent-provider re-evaluation of frozen held-out target outputs; no target regeneration; no routing",
        "suite": "heldout_cases_v1.json",
        "suite_freeze_commit": "2975376ade5df0863340ce10aa867f3b3e0e1404",
        "suite_git_blob_sha": "5fa2ab6f678728124b93ea9dd6c9158e5d6e9698",
        "shard_index": shard_index,
        "shard_count": base.SHARD_COUNT,
        "case_ids": [c["case_id"] for c in shard_cases],
        "generation_replicates": base.GENERATION_REPLICATES,
        "judge_votes_per_pair": base.JUDGE_VOTES,
        "conditions": list(base.CONDITIONS),
        "prompt_sha256": {
            "CONTROL": None,
            "COMPACT": base.sha256_text(base.COMPACT),
            "FULL": base.sha256_text(base.FULL),
        },
        "target": {
            "model": base.v03.TARGET_MODEL,
            "family": base.TARGET_FAMILY,
            "provider": base.TARGET_PROVIDER,
            "base_url": base.v03.TARGET_BASE,
        },
        "judge": {
            "model": base.v03.JUDGE_MODEL,
            "family": base.JUDGE_FAMILY,
            "provider": base.JUDGE_PROVIDER,
            "base_url": base.v03.JUDGE_BASE,
            "connectivity_probe_usage": connectivity_usage,
        },
        "pair_specs": base.PAIR_SPECS,
        "n_runs": len(runs),
        "n_votes": len(votes),
        "independent_evaluator": True,
        "source_target_run_id": SOURCE_RUN_ID,
        "source_target_artifact_digest": SOURCE_ARTIFACT_DIGESTS[shard_index],
        "target_outputs_reused": len(runs),
        "target_outputs_regenerated": 0,
        "prior_glm53flash_votes_reused": 0,
        "new_independent_votes": len(votes),
        "format_policy": "accept first complete JSON object; never repair malformed JSON; retry same vote on invalid format",
        "max_format_attempts_per_vote": MAX_FORMAT_ATTEMPTS,
        "format_retries_observed": format_retries,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
