#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import aggregate_framework_validation_v1_glm53flash as tier

SOURCE_RUN_ID = 34232674771
ARTIFACT_DIGESTS = {
    0: "sha256:2ad2b5f56d2e729baa8d02d3d646f1fe6e81526061e041b81261acaced5305b3",
    1: "sha256:1c78104d5ab7c22dba536efde85311292a2559db04dcb629437b570850a3628e",
    2: "sha256:6928631fd4b97f4a16ac71b424dbd3b1001400f07b3256d6807cd4987c7844ba",
    3: "sha256:8701eaf2604f9ccc201baded1af16a3c8108c7671d2378f9fc9a32529709eee9",
    4: "sha256:a49249ae575864da91f0f9ab5ebef67f2bcafa909af92629b38d80b7bc685f72",
    5: "sha256:c9bd55f34fba7a026b9c6d9bc20cc781db4e5b43cef1055fc9c0016e59e1a4f3",
}


def main() -> None:
    tier.main()
    results_dir = Path(__file__).resolve().parent / "results_framework_validation_v1"
    path = results_dir / "framework_v1_glm53flash_report.json"
    report = json.loads(path.read_text(encoding="utf-8"))

    report["execution_recovery"] = {
        "source_run_id": SOURCE_RUN_ID,
        "source_run_status": "execution failure during judge JSON parsing; not a scientific endpoint result",
        "source_artifact_digests": ARTIFACT_DIGESTS,
        "target_outputs_regenerated": False,
        "retained_valid_votes_preserved": True,
        "missing_vote_policy": "request only missing preregistered vote keys with identical A/B orientation seed",
        "format_policy": "accept first complete JSON object; never repair malformed JSON; malformed/invalid format is retried and not scored",
        "outcome_peeking_before_recovery_design": False,
    }
    report["interpretation_boundary"].append(
        "Execution recovery preserved all source-run target outputs and valid judge votes; only missing vote keys were completed after a mechanical JSON-format handling repair."
    )

    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
