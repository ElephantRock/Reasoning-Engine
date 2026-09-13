#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import run_operator_fidelity_v02 as core

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_operator_fidelity_v02_target"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    core.validate_frozen_files()
    OUT.mkdir(exist_ok=True)
    runs_path = OUT / "runs.jsonl"

    runs = []
    for case in core.CASES:
        for condition in core.CONDITIONS:
            print("generate", case["case_id"], condition, flush=True)
            run = core.run_target(case, condition)
            runs.append(run)
            core.write_jsonl(runs_path, runs)
            if not core.target_complete(run):
                raise RuntimeError(
                    f"incomplete target output for {case['case_id']} {condition}: "
                    f"tokens={(run.get('usage') or {}).get('output_tokens')} "
                    f"finish={run.get('finish_reason')!r} visible={bool((run.get('text') or '').strip())}"
                )

    keys = [(r["case_id"], r["condition"]) for r in runs]
    if len(runs) != 96 or len(set(keys)) != 96:
        raise RuntimeError("v0.2 target phase did not produce the frozen 12x8 design")

    meta = {
        "measurement_version": "operator-fidelity-v0.2",
        "target_model": core.v03.TARGET_MODEL,
        "cases_blob": core.EXPECTED_CASES_BLOB,
        "policies_blob": core.EXPECTED_POLICIES_BLOB,
        "records": len(runs),
        "runs_sha256": sha256_file(runs_path),
        "target_cap": core.TARGET_CAP,
    }
    (OUT / "target_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2), flush=True)


if __name__ == "__main__":
    main()
