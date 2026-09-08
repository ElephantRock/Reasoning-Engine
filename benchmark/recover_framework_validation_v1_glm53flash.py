#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

import run_framework_validation_v1 as base
import run_framework_validation_v1_glm53flash as tier

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results_framework_validation_v1"
SOURCE_RUN_ID = 34232674771
MAX_FORMAT_ATTEMPTS = 3
EXPECTED_RUNS_PER_SHARD = 6 * 3 * 3
EXPECTED_VOTES_PER_SHARD = 6 * 3 * 3 * 3


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"recovery checkpoint is missing: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_first_json_object(text: str) -> dict[str, Any]:
    """Parse the first complete JSON object without inventing repairs.

    This accepts a valid object followed by extra prose/code-fence text. It does
    not repair syntactically malformed JSON; malformed responses must be retried.
    """
    decoder = json.JSONDecoder()
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise json.JSONDecodeError("no complete JSON object found", stripped, 0)


def recovery_connectivity_check() -> dict[str, Any]:
    system = 'Return JSON only with exactly this object: {"ok":true}'
    result = base.v03.judge_call(system, [{"role": "user", "content": "Cross-model recovery connectivity check."}])
    parsed = parse_first_json_object(result["text"])
    if parsed.get("ok") is not True:
        raise RuntimeError(f"GLM-5.3-Flash recovery connectivity check returned unexpected payload: {parsed}")
    return result["usage"]


def expected_run_keys(shard_cases: list[dict[str, Any]]) -> set[tuple[str, str, int]]:
    return {
        (case["case_id"], condition, replicate)
        for replicate in range(1, base.GENERATION_REPLICATES + 1)
        for case in shard_cases
        for condition in base.CONDITIONS
    }


def expected_vote_keys(shard_cases: list[dict[str, Any]]) -> set[tuple[str, str, int, int]]:
    return {
        (case["case_id"], spec["pair_id"], replicate, vote_index)
        for replicate in range(1, base.GENERATION_REPLICATES + 1)
        for case in shard_cases
        for spec in base.PAIR_SPECS
        for vote_index in range(1, base.JUDGE_VOTES + 1)
    }


def validate_checkpoint(
    runs: list[dict[str, Any]], votes: list[dict[str, Any]], shard_cases: list[dict[str, Any]]
) -> tuple[set[tuple[str, str, int]], set[tuple[str, str, int, int]]]:
    run_keys = [(r["case_id"], r["condition"], int(r["replicate"])) for r in runs]
    vote_keys = [
        (v["case_id"], v["pair_id"], int(v["replicate"]), int(v["vote_index"]))
        for v in votes
    ]
    if len(run_keys) != len(set(run_keys)):
        raise RuntimeError("recovery checkpoint contains duplicate target-run keys")
    if len(vote_keys) != len(set(vote_keys)):
        raise RuntimeError("recovery checkpoint contains duplicate judge-vote keys")

    expected_runs = expected_run_keys(shard_cases)
    expected_votes = expected_vote_keys(shard_cases)
    actual_runs = set(run_keys)
    actual_votes = set(vote_keys)

    # Scientific-integrity guard: the source run completed every target generation.
    # Recovery is forbidden from regenerating any held-out target output.
    if actual_runs != expected_runs or len(runs) != EXPECTED_RUNS_PER_SHARD:
        missing = sorted(expected_runs - actual_runs)
        extra = sorted(actual_runs - expected_runs)
        raise RuntimeError(
            f"recovery refuses target regeneration: runs={len(runs)} missing={missing[:3]} extra={extra[:3]}"
        )
    if not actual_votes <= expected_votes:
        raise RuntimeError(f"recovery checkpoint contains unexpected vote keys: {sorted(actual_votes - expected_votes)[:3]}")
    return actual_runs, actual_votes


def quality_vote_with_format_retry(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> dict[str, Any]:
    # Keep the exact frozen A/B orientation seed used by the original run.
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

    total_usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    last_error: Exception | None = None
    for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
        result = base.v03.judge_call(
            base.v05.QUALITY_PAIRWISE_JUDGE,
            [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
        )
        base.v03.add_usage(total_usage, result["usage"])
        try:
            parsed = parse_first_json_object(result["text"])
            winner = parsed.get("winner")
            if winner not in {"A", "B", "TIE"}:
                raise RuntimeError(f"invalid held-out framework quality result: {parsed}")
        except (json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            print(
                "judge-format-retry",
                base.SHARD_INDEX,
                run_x["replicate"],
                case["case_id"],
                spec["pair_id"],
                vote_index,
                attempt,
                type(exc).__name__,
                flush=True,
            )
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
            "judge_usage": total_usage,
            "judge_format_retries": attempt - 1,
        }

    raise RuntimeError(
        f"GLM-5.3-Flash judge did not return one valid JSON vote after {MAX_FORMAT_ATTEMPTS} attempts: {last_error}"
    )


def write_meta(
    path: Path,
    shard_cases: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    votes: list[dict[str, Any]],
    retained_votes: int,
) -> None:
    format_retries = int(sum(int(v.get("judge_format_retries", 0)) for v in votes))
    meta = {
        "measurement_version": "heldout-framework-validation-v1-glm53flash",
        "experiment_role": "framework-level held-out validation; cross-model same-family judge; no routing",
        "evaluation_tier": "Tier-1B cross-model same-family; not independent-provider evaluation",
        "independent_evaluator": False,
        "same_family_cross_model": True,
        "suite": "heldout_cases_v1.json",
        "suite_freeze_commit": "2975376ade5df0863340ce10aa867f3b3e0e1404",
        "suite_git_blob_sha": "5fa2ab6f678728124b93ea9dd6c9158e5d6e9698",
        "shard_index": base.SHARD_INDEX,
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
            "connectivity_probe_usage": {"recovery_workflow_preflight": True},
        },
        "pair_specs": base.PAIR_SPECS,
        "n_runs": len(runs),
        "n_votes": len(votes),
        "execution_recovery": {
            "source_run_id": SOURCE_RUN_ID,
            "source_artifact": f"framework-v1-glm53flash-shard-{base.SHARD_INDEX}-{SOURCE_RUN_ID}",
            "retained_target_runs": len(runs),
            "retained_valid_votes_at_resume": retained_votes,
            "new_votes_requested": EXPECTED_VOTES_PER_SHARD - retained_votes,
            "target_regeneration_allowed": False,
            "format_policy": "accept first complete JSON object; never repair malformed JSON; retry malformed/invalid vote format",
            "max_format_attempts_per_missing_vote": MAX_FORMAT_ATTEMPTS,
            "format_retries_observed_in_recovery_votes": format_retries,
        },
    }
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    tier.cross_model_same_family_preflight()

    shard_cases = [case for i, case in enumerate(base.CASES) if i % base.SHARD_COUNT == base.SHARD_INDEX]
    if len(base.CASES) != 36 or len(shard_cases) != 6:
        raise RuntimeError(f"frozen suite/shard size mismatch: total={len(base.CASES)}, shard={len(shard_cases)}")

    RESULTS.mkdir(exist_ok=True)
    runs_path = RESULTS / f"framework_v1_runs_shard_{base.SHARD_INDEX}.jsonl"
    votes_path = RESULTS / f"framework_v1_votes_shard_{base.SHARD_INDEX}.jsonl"
    meta_path = RESULTS / f"framework_v1_meta_shard_{base.SHARD_INDEX}.json"

    runs = read_jsonl(runs_path)
    votes = read_jsonl(votes_path)
    _, completed_votes = validate_checkpoint(runs, votes, shard_cases)
    retained_votes = len(votes)

    index = {(r["case_id"], r["condition"], int(r["replicate"])): r for r in runs}
    for replicate in range(1, base.GENERATION_REPLICATES + 1):
        for case in shard_cases:
            for spec in base.PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, base.JUDGE_VOTES + 1):
                    key = (case["case_id"], spec["pair_id"], replicate, vote_index)
                    if key in completed_votes:
                        continue
                    print("recover-judge", base.SHARD_INDEX, replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    vote = quality_vote_with_format_retry(case, left, right, spec, vote_index)
                    votes.append(vote)
                    completed_votes.add(key)
                    base.write_jsonl(votes_path, votes)

    if len(votes) != EXPECTED_VOTES_PER_SHARD or completed_votes != expected_vote_keys(shard_cases):
        raise RuntimeError(f"recovery incomplete: votes={len(votes)} expected={EXPECTED_VOTES_PER_SHARD}")

    write_meta(meta_path, shard_cases, runs, votes, retained_votes)
    print(
        json.dumps(
            {
                "recovery": "complete",
                "source_run_id": SOURCE_RUN_ID,
                "shard": base.SHARD_INDEX,
                "retained_runs": len(runs),
                "retained_votes": retained_votes,
                "final_votes": len(votes),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
