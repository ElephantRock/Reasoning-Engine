#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("ZAI_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("ZAI_JUDGE_API_KEY", "unused-aggregation-shim")
os.environ.setdefault("BENCHMARK_SUITE", "combined")

import aggregate_framework_validation_v1 as base  # noqa: E402

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results_framework_validation_v1"
SOURCE_RUN_ID = 34270142523
SOURCE_ARTIFACT_DIGESTS = {
    "0": "sha256:b4300a47e880f26618648fcc0efffa1068924e75147a3136b1f78acd68922568",
    "1": "sha256:1aa15f29b546c1fbb1e0d5670062d7be4be02c1acf86144c1c6f1fa13264e863",
    "2": "sha256:1cd73a393eedf7c8e584dd70ca6036705978b3e6e358c13aba441eb75ae8561c",
    "3": "sha256:176a0a7aa3507eb6eb7b77d6f726b3b96b081462d1efa5140a126385182e2563",
    "4": "sha256:ac722072fce97a893e0ce0bc326db42721b3c140ccfeb896b2ab21ad4b57d28f",
    "5": "sha256:458e78e78ce9c2e9715fd9b9f87673d853c5b1a4cacb3d48bd497b5c8207151b",
}


def validate_independent_meta() -> dict:
    paths = sorted(RESULTS.glob("framework_v1_meta_shard_*.json"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six independent metadata files, found {len(paths)}")
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if {row["shard_index"] for row in rows} != set(range(6)):
        raise RuntimeError("independent rejudge shard indices are incomplete")

    for row in rows:
        if row.get("independent_evaluator") is not True:
            raise RuntimeError("independent evaluator flag missing")
        if row.get("source_target_run_id") != SOURCE_RUN_ID:
            raise RuntimeError("source target run provenance mismatch")
        expected_digest = SOURCE_ARTIFACT_DIGESTS[str(row["shard_index"])]
        if row.get("source_target_artifact_digest") != expected_digest:
            raise RuntimeError("source target artifact digest mismatch")
        if row.get("target_outputs_reused") != 54 or row.get("target_outputs_regenerated") != 0:
            raise RuntimeError("target-output reuse invariant failed")
        if row.get("prior_glm53flash_votes_reused") != 0 or row.get("new_independent_votes") != 162:
            raise RuntimeError("independent-vote accounting mismatch")

    target = rows[0]["target"]
    judge = rows[0]["judge"]
    if judge["model"] == target["model"]:
        raise RuntimeError("judge and target model IDs are identical")
    if judge["family"] == target["family"]:
        raise RuntimeError("judge and target model families are identical")
    if judge["provider"] == target["provider"]:
        raise RuntimeError("judge and target providers are identical")
    if base.fv1.normalize_url(judge["base_url"]) == base.fv1.normalize_url(target["base_url"]):
        raise RuntimeError("judge and target endpoints are identical")

    return {
        "target": target,
        "judge": judge,
        "format_retries_observed": sum(int(row.get("format_retries_observed", 0)) for row in rows),
    }


def main() -> None:
    independent = validate_independent_meta()
    base.main()

    generic_path = RESULTS / "framework_v1_report.json"
    report = json.loads(generic_path.read_text(encoding="utf-8"))

    report["measurement_version"] = "heldout-framework-validation-v1-independent-rejudge"
    report["experiment_role"] = (
        "independent-provider re-evaluation of frozen held-out target outputs; "
        "no target regeneration; no routing"
    )
    report["evaluation_tier"] = (
        "Tier-2 independent-family/provider judging of previously generated frozen held-out outputs"
    )
    report["independent_evaluator"] = True
    report["same_family_cross_model"] = False
    report["source_target_run_id"] = SOURCE_RUN_ID
    report["source_target_artifact_digests"] = SOURCE_ARTIFACT_DIGESTS
    report["target_outputs_reused"] = 324
    report["target_outputs_regenerated"] = 0
    report["prior_glm53flash_votes_reused"] = 0
    report["new_independent_votes"] = 972
    report["format_retries_observed"] = independent["format_retries_observed"]
    report["interpretation_boundary"] = [
        "The primary claim concerns FULL versus an uncontrolled baseline on the frozen 36-case suite.",
        "All 324 target outputs are exact reused outputs from recovery run 34270142523; no target output is regenerated.",
        "All 972 quality votes are newly produced by an evaluator whose model family, provider, model ID, and endpoint differ from the GLM-5.1/Z.AI target.",
        "No GLM-5.3-Flash vote is reused in this evaluation.",
        "Because the evaluator is introduced after the Tier-1B result and the target outputs are already exposed as a completed held-out experiment, this is independent re-judging of fixed held-out outputs, not a fresh end-to-end held-out replication.",
        "COMPACT versus CONTROL and FULL versus COMPACT remain secondary and cannot rescue a failed FULL primary endpoint.",
        "Original TEST/ENGINEER/BOTH/NONE labels remain descriptive subgroups only; no routing or conditional prompt injection occurs.",
        "A positive result does not validate autonomous routing, universal task benefit, or cross-target-model generalization.",
        "Cost is descriptive and does not enter any quality endpoint.",
    ]

    output = RESULTS / "framework_v1_independent_rejudge_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
