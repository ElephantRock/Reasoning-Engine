#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import run_operator_fidelity_v02 as core

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_operator_fidelity_v02"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_frozen_targets(runs_path: Path, meta_path: Path) -> list[dict[str, Any]]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("measurement_version") != "operator-fidelity-v0.2":
        raise RuntimeError("target artifact measurement version mismatch")
    if meta.get("target_model") != core.v03.TARGET_MODEL:
        raise RuntimeError("target artifact model mismatch")
    if meta.get("cases_blob") != core.EXPECTED_CASES_BLOB:
        raise RuntimeError("target artifact case blob mismatch")
    if meta.get("policies_blob") != core.EXPECTED_POLICIES_BLOB:
        raise RuntimeError("target artifact policy blob mismatch")
    if int(meta.get("target_cap", 0)) != core.TARGET_CAP:
        raise RuntimeError("target artifact completion cap mismatch")
    if meta.get("runs_sha256") != sha256_file(runs_path):
        raise RuntimeError("target artifact runs SHA-256 mismatch")

    runs = read_jsonl(runs_path)
    expected = {(case["case_id"], condition) for case in core.CASES for condition in core.CONDITIONS}
    keys = [(run.get("case_id"), run.get("condition")) for run in runs]
    if len(runs) != 96 or len(set(keys)) != 96 or set(keys) != expected:
        raise RuntimeError("target artifact does not match frozen 12x8 design")

    intended = {case["case_id"]: case["intended_policy"] for case in core.CASES}
    for run in runs:
        if run.get("intended_policy") != intended[run["case_id"]]:
            raise RuntimeError(f"target intended-policy mismatch for {run['case_id']} {run['condition']}")
        if not core.target_complete(run):
            raise RuntimeError(f"target artifact contains incomplete output: {run['case_id']} {run['condition']}")
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-runs", required=True, type=Path)
    parser.add_argument("--source-meta", required=True, type=Path)
    args = parser.parse_args()

    core.validate_frozen_files()
    OUT.mkdir(exist_ok=True)
    runs = load_frozen_targets(args.source_runs, args.source_meta)
    shutil.copyfile(args.source_runs, OUT / "runs.jsonl")
    shutil.copyfile(args.source_meta, OUT / "target_meta.json")

    index = {(run["case_id"], run["condition"]): run for run in runs}
    failures: list[dict[str, Any]] = []
    core.write_jsonl(OUT / "judge_format_failures.jsonl", failures)

    votes: list[dict[str, Any]] = []
    for case in core.CASES:
        for condition in core.CONDITIONS:
            run = index[(case["case_id"], condition)]
            for vote_index in range(1, core.JUDGE_VOTES + 1):
                print("fidelity", case["case_id"], condition, vote_index, flush=True)
                votes.append(core.fidelity_vote(case, run, vote_index, failures, OUT))
                core.write_jsonl(OUT / "fidelity_votes.jsonl", votes)

    quality: list[dict[str, Any]] = []
    for case in core.CASES:
        operator = case["intended_policy"]
        specialist = index[(case["case_id"], operator)]
        for opponent in ("CONTROL", "FULL"):
            pair_id = f"{operator}_vs_{opponent}"
            print("quality", case["case_id"], pair_id, flush=True)
            quality.append(
                core.quality_vote(
                    case,
                    specialist,
                    index[(case["case_id"], opponent)],
                    pair_id,
                    failures,
                    OUT,
                )
            )
            core.write_jsonl(OUT / "quality_sanity.jsonl", quality)

    if len(votes) != 192 or len(quality) != 24:
        raise RuntimeError("v0.2 judging phase completed with wrong record counts")

    summary = core.aggregate(runs, votes, quality)
    summary["target_source"] = {
        "runs_sha256": sha256_file(args.source_runs),
        "meta_sha256": sha256_file(args.source_meta),
        "records": len(runs),
    }
    summary["judge_format_failures"] = len(failures)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": summary["program_decision"], "eligible": summary["eligible_operators"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
