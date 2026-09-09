#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SUITE_DIR = ROOT / "routing_validation_v2"
MANIFEST_PATH = SUITE_DIR / "manifest.json"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def suite_digest() -> str:
    manifest = _read_json(MANIFEST_PATH)
    h = hashlib.sha256()
    h.update(MANIFEST_PATH.read_bytes())
    for name in manifest["domain_files"]:
        h.update(b"\0")
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update((SUITE_DIR / name).read_bytes())
    return h.hexdigest()


def load_cases() -> list[dict[str, Any]]:
    manifest = _read_json(MANIFEST_PATH)
    files = manifest.get("domain_files")
    if not isinstance(files, list) or len(files) != manifest["expected_domains"]:
        raise RuntimeError("routing v2 manifest domain file count mismatch")
    if len(set(files)) != len(files):
        raise RuntimeError("routing v2 manifest contains duplicate files")

    cases: list[dict[str, Any]] = []
    for name in files:
        path = SUITE_DIR / name
        if not path.is_file():
            raise RuntimeError(f"missing routing v2 domain file: {name}")
        domain_cases = _read_json(path)
        if not isinstance(domain_cases, list) or len(domain_cases) != manifest["cases_per_domain"]:
            raise RuntimeError(f"routing v2 domain file must contain exactly four cases: {name}")
        cases.extend(domain_cases)

    if len(cases) != manifest["expected_cases"]:
        raise RuntimeError(f"routing v2 expected {manifest['expected_cases']} cases, found {len(cases)}")

    ids = [case.get("case_id") for case in cases]
    if len(set(ids)) != len(ids) or any(not isinstance(x, str) for x in ids):
        raise RuntimeError("routing v2 case IDs must be unique strings")

    domain_counts = Counter(case.get("domain") for case in cases)
    if len(domain_counts) != manifest["expected_domains"]:
        raise RuntimeError(f"routing v2 expected {manifest['expected_domains']} domains, found {len(domain_counts)}")
    if set(domain_counts.values()) != {manifest["cases_per_domain"]}:
        raise RuntimeError(f"routing v2 cases-per-domain mismatch: {dict(domain_counts)}")

    labels = Counter(case.get("author_route_label") for case in cases)
    if dict(labels) != manifest["expected_labels"]:
        raise RuntimeError(f"routing v2 author label balance mismatch: {dict(labels)}")

    sequential = 0
    requires_action = 0
    mismatch = 0
    for case in cases:
        turns = case.get("turns")
        if not isinstance(turns, list) or not turns or turns[0].get("turn") != 1:
            raise RuntimeError(f"invalid turns for {case['case_id']}")
        metadata = case.get("design_metadata", {})
        if metadata.get("sequential") != (len(turns) > 1):
            raise RuntimeError(f"sequential metadata mismatch for {case['case_id']}")
        sequential += bool(metadata.get("sequential"))
        requires_action += bool(metadata.get("requires_action"))
        mismatch += bool(metadata.get("has_distractors") or metadata.get("adversarial_surface"))
        freshness = str(metadata.get("freshness_attestation", ""))
        if "Selective Routing v2" not in freshness or "not reused" not in freshness:
            raise RuntimeError(f"missing freshness attestation for {case['case_id']}")
        if not isinstance(case.get("evaluator_key"), dict):
            raise RuntimeError(f"missing evaluator key for {case['case_id']}")

    if sequential < manifest["minimum_sequential"]:
        raise RuntimeError(f"routing v2 sequential minimum failed: {sequential}")
    if requires_action < manifest["minimum_requires_action"]:
        raise RuntimeError(f"routing v2 action minimum failed: {requires_action}")
    if mismatch < manifest["minimum_distractor_or_surface_mismatch"]:
        raise RuntimeError(f"routing v2 distractor/surface-mismatch minimum failed: {mismatch}")

    # Every domain must contain one clear FULL, one clear CONTROL, and two boundary cases.
    for domain in domain_counts:
        domain_labels = Counter(case["author_route_label"] for case in cases if case["domain"] == domain)
        if domain_labels != Counter({"BOUNDARY": 2, "CLEAR_FULL": 1, "CLEAR_CONTROL": 1}):
            raise RuntimeError(f"routing v2 domain label composition mismatch for {domain}: {dict(domain_labels)}")

    return cases


if __name__ == "__main__":
    cases = load_cases()
    print(json.dumps({
        "cases": len(cases),
        "domains": len({c['domain'] for c in cases}),
        "labels": dict(Counter(c['author_route_label'] for c in cases)),
        "sequential": sum(bool(c['design_metadata']['sequential']) for c in cases),
        "requires_action": sum(bool(c['design_metadata']['requires_action']) for c in cases),
        "distractor_or_surface_mismatch": sum(bool(c['design_metadata']['has_distractors'] or c['design_metadata']['adversarial_surface']) for c in cases),
        "suite_sha256": suite_digest(),
    }, indent=2, sort_keys=True))
