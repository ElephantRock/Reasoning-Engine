#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from load_routing_validation_v2 import load_cases as load_v2_cases
from load_routing_validation_v3 import load_cases as load_v3_cases

ROOT = Path(__file__).resolve().parent
OUTCOMES = ROOT / "routing_v4_exposed_outcomes.csv"
EXPECTED_OUTCOME_SHA256 = "8711a6aff96df9bda7f9c7c6f209ae33cd6370b811886a27f5d28ddbe791b295"
TARGET_FULL_RATE = 0.58
HIGH_GAIN = 0.20
K_VALUES = (5, 9, 15)

TOKEN_RE = re.compile(r"[a-z0-9]+")
DIRECT_MARKERS = (
    "what is", "how many", "calculate", "compute", "convert", "put them in",
    "chronological order", "sort ", "which sample", "which value", "what percentage",
    "what percent", "rate", "ratio", "difference", "total", "average", "occupancy",
    "availability", "out of specification", "precise, accurate", "rank",
)
DEEP_MARKERS = (
    "what should", "how should", "should the", "recommend", "decide", "decision",
    "cause", "causal", "confound", "why did", "why is", "explain why", "uncertain",
    "uncertainty", "risk", "rollback", "reversible", "intervention", "evidence",
    "conclude", "conclusion", "hypothesis", "mechanism", "tradeoff", "trade-off",
    "before making", "investigate", "diagnose", "root cause", "what action",
    "action is justified", "what change", "which change", "do first",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def is_direct_bypass(text: str) -> bool:
    low = text.lower()
    if len(text) > 360:
        return False
    if any(marker in low for marker in DEEP_MARKERS):
        return False
    return any(marker in low for marker in DIRECT_MARKERS)


def load_development_cases() -> list[dict[str, Any]]:
    v1 = json.loads((ROOT / "routing_validation_cases_v1.json").read_text(encoding="utf-8"))
    suites = {"v1": v1, "v2": load_v2_cases(), "v3": load_v3_cases()}
    rows: list[dict[str, Any]] = []
    for suite, cases in suites.items():
        if len(cases) != 48:
            raise RuntimeError(f"{suite} must contain exactly 48 exposed cases")
        for case in cases:
            turns = case["turns"]
            if not turns or turns[0]["turn"] != 1:
                raise RuntimeError(f"invalid turn structure: {case['case_id']}")
            rows.append({
                "suite": suite,
                "case_id": case["case_id"],
                "domain": case["domain"],
                "text": turns[0]["agent_input"],
            })
    if len(rows) != 144 or len({r["case_id"] for r in rows}) != 144:
        raise RuntimeError("v4 development corpus must contain exactly 144 unique exposed cases")
    return rows


def attach_outcomes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if sha256_file(OUTCOMES) != EXPECTED_OUTCOME_SHA256:
        raise RuntimeError("frozen v4 outcome table hash mismatch")
    outcome: dict[str, tuple[str, int]] = {}
    with OUTCOMES.open(newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            cid = rec["case_id"]
            if cid in outcome:
                raise RuntimeError(f"duplicate outcome: {cid}")
            score18 = int(rec["score18"])
            if not 0 <= score18 <= 18:
                raise RuntimeError(f"invalid score18 for {cid}")
            outcome[cid] = (rec["suite"], score18)
    if len(outcome) != 144:
        raise RuntimeError("frozen v4 outcome table must contain exactly 144 rows")
    case_ids = {r["case_id"] for r in rows}
    if set(outcome) != case_ids:
        raise RuntimeError("case/outcome ID mismatch")
    joined = []
    for row in rows:
        suite, score18 = outcome[row["case_id"]]
        if suite != row["suite"]:
            raise RuntimeError(f"suite mismatch for {row['case_id']}")
        score = score18 / 18.0
        joined.append({**row, "score": score, "gain": score - 0.5})
    return joined


def build_idf(rows: list[dict[str, Any]]) -> dict[str, float]:
    df: Counter[str] = Counter()
    for row in rows:
        df.update(set(tokenize(row["text"])))
    n = len(rows)
    return {term: math.log((1 + n) / (1 + count)) + 1.0 for term, count in df.items()}


def vectorize(text: str, idf: dict[str, float]) -> dict[str, float]:
    counts = Counter(tokenize(text))
    vec = {t: (1.0 + math.log(c)) * idf[t] for t, c in counts.items() if t in idf}
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm:
        vec = {t: v / norm for t, v in vec.items()}
    return vec


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def knn_score(query: dict[str, float], train_vecs: list[dict[str, float]], gains: list[float], k: int, exclude: int | None = None) -> float:
    scored = []
    for i, vec in enumerate(train_vecs):
        if i == exclude:
            continue
        scored.append((cosine(query, vec), gains[i]))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: min(k, len(scored))]
    positive = [(sim, gain) for sim, gain in top if sim > 0]
    if not positive:
        vals = [gains[i] for i in range(len(gains)) if i != exclude]
        return sum(vals) / len(vals)
    weight = sum(sim for sim, _ in positive)
    return sum(sim * gain for sim, gain in positive) / weight


def knn_predictions(train: list[dict[str, Any]], test: list[dict[str, Any]], k: int) -> tuple[list[float], list[float]]:
    idf = build_idf(train)
    train_vecs = [vectorize(r["text"], idf) for r in train]
    gains = [r["gain"] for r in train]
    loo = [knn_score(train_vecs[i], train_vecs, gains, k, exclude=i) for i in range(len(train))]
    test_preds = [knn_score(vectorize(r["text"], idf), train_vecs, gains, k) for r in test]
    return loo, test_preds


def nb_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [1 if r["gain"] > 0 else 0 for r in rows]
    token_sets = [set(tokenize(r["text"])) for r in rows]
    df = Counter(t for ts in token_sets for t in ts)
    vocab = {t for t, c in df.items() if c >= 2}
    pos = sum(labels)
    neg = len(labels) - pos
    pos_count = Counter(t for ts, y in zip(token_sets, labels) if y for t in ts if t in vocab)
    neg_count = Counter(t for ts, y in zip(token_sets, labels) if not y for t in ts if t in vocab)
    return {"vocab": vocab, "pos": pos, "neg": neg, "pos_count": pos_count, "neg_count": neg_count}


def nb_log_odds(text: str, model: dict[str, Any]) -> float:
    present = set(tokenize(text)) & model["vocab"]
    pos, neg = model["pos"], model["neg"]
    logodds = math.log((pos + 1) / (neg + 1))
    for t in model["vocab"]:
        p1 = (model["pos_count"][t] + 1) / (pos + 2)
        p0 = (model["neg_count"][t] + 1) / (neg + 2)
        if t in present:
            logodds += math.log(p1 / p0)
        else:
            logodds += math.log((1 - p1) / (1 - p0))
    return logodds


def nb_loo_predictions(train: list[dict[str, Any]]) -> list[float]:
    labels = [1 if r["gain"] > 0 else 0 for r in train]
    token_sets = [set(tokenize(r["text"])) for r in train]
    full_df = Counter(t for ts in token_sets for t in ts)
    full_pos = sum(labels)
    full_neg = len(labels) - full_pos
    full_pos_count = Counter(t for ts, y in zip(token_sets, labels) if y for t in ts)
    full_neg_count = Counter(t for ts, y in zip(token_sets, labels) if not y for t in ts)
    out = []
    for i, (tokens, y) in enumerate(zip(token_sets, labels)):
        pos = full_pos - y
        neg = full_neg - (1 - y)
        vocab = {t for t, c in full_df.items() if c - (1 if t in tokens else 0) >= 2}
        logodds = math.log((pos + 1) / (neg + 1))
        for t in vocab:
            cp = full_pos_count[t] - (1 if y and t in tokens else 0)
            cn = full_neg_count[t] - (1 if (not y) and t in tokens else 0)
            p1 = (cp + 1) / (pos + 2)
            p0 = (cn + 1) / (neg + 2)
            if t in tokens:
                logodds += math.log(p1 / p0)
            else:
                logodds += math.log((1 - p1) / (1 - p0))
        out.append(logodds)
    return out


def nb_predictions(train: list[dict[str, Any]], test: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    model = nb_model(train)
    return nb_loo_predictions(train), [nb_log_odds(r["text"], model) for r in test]


def choose_threshold(preds: list[float], direct: list[bool]) -> float:
    unique = sorted(set(preds))
    candidates = [float("-inf"), float("inf")]
    for v in unique:
        candidates.append(v)
        candidates.append(math.nextafter(v, math.inf))
    best: tuple[tuple[float, float, float], float] | None = None
    for threshold in candidates:
        full = sum((not d) and p >= threshold for p, d in zip(preds, direct))
        rate = full / len(preds)
        key = (abs(rate - TARGET_FULL_RATE), rate, -threshold if math.isfinite(threshold) else 0.0)
        if best is None or key < best[0]:
            best = (key, threshold)
    assert best is not None
    return best[1]


def candidate_predictions(name: str, train: list[dict[str, Any]], test: list[dict[str, Any]]) -> tuple[list[bool], float | None]:
    if name == "ALWAYS_FULL":
        return [True] * len(test), None
    if name == "ALWAYS_CONTROL":
        return [False] * len(test), None
    if name == "DIRECT_BYPASS":
        return [not is_direct_bypass(r["text"]) for r in test], None

    force_direct = name.endswith("_DIRECT")
    base = name.removesuffix("_DIRECT")
    if base.startswith("KNN"):
        k = int(base[3:])
        train_pred, test_pred = knn_predictions(train, test, k)
    elif base == "NB":
        train_pred, test_pred = nb_predictions(train, test)
    else:
        raise ValueError(name)

    train_direct = [is_direct_bypass(r["text"]) if force_direct else False for r in train]
    threshold = choose_threshold(train_pred, train_direct)
    routes = [
        (not (is_direct_bypass(r["text"]) if force_direct else False)) and p >= threshold
        for r, p in zip(test, test_pred)
    ]
    return routes, threshold


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    policy = sum(r["score"] if r["route_full"] else 0.5 for r in records) / n
    full = sum(r["score"] for r in records) / n
    rate = sum(r["route_full"] for r in records) / n
    high = [r for r in records if r["gain"] >= HIGH_GAIN]
    high_recall = sum(r["route_full"] for r in high) / len(high) if high else 1.0
    folds: dict[str, Any] = {}
    for fold in sorted({r["fold"] for r in records}):
        sub = [r for r in records if r["fold"] == fold]
        folds[fold] = {
            "n": len(sub),
            "routed_score": sum(r["score"] if r["route_full"] else 0.5 for r in sub) / len(sub),
            "full_score": sum(r["score"] for r in sub) / len(sub),
            "full_rate": sum(r["route_full"] for r in sub) / len(sub),
        }
    return {
        "n": n,
        "routed_score": policy,
        "full_score": full,
        "paired_decrement": policy - full,
        "full_rate": rate,
        "high_gain_n": len(high),
        "high_gain_recall": high_recall,
        "worst_fold_routed_score": min(v["routed_score"] for v in folds.values()),
        "folds": folds,
    }


def evaluate_cv(rows: list[dict[str, Any]], name: str, field: str) -> dict[str, Any]:
    records = []
    thresholds = {}
    groups = sorted({r[field] for r in rows})
    for group in groups:
        train = [r for r in rows if r[field] != group]
        test = [r for r in rows if r[field] == group]
        routes, threshold = candidate_predictions(name, train, test)
        thresholds[str(group)] = threshold
        for row, route in zip(test, routes):
            records.append({**row, "fold": str(group), "route_full": bool(route)})
    if len(records) != len(rows) or len({r["case_id"] for r in records}) != len(rows):
        raise RuntimeError(f"cross-validation coverage failure for {name}/{field}")
    result = summarize(records)
    result["thresholds"] = thresholds
    return result


def passes_gates(loso: dict[str, Any], lodo: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    checks = {
        "loso_routed_score": loso["routed_score"] >= 0.60,
        "loso_paired_decrement": loso["paired_decrement"] >= -0.03,
        "loso_full_rate": 0.50 <= loso["full_rate"] <= 0.63,
        "loso_worst_fold": loso["worst_fold_routed_score"] >= 0.56,
        "loso_high_gain_recall": loso["high_gain_recall"] >= 0.70,
        "lodo_routed_score": lodo["routed_score"] >= 0.59,
        "lodo_paired_decrement": lodo["paired_decrement"] >= -0.04,
        "lodo_full_rate": 0.50 <= lodo["full_rate"] <= 0.63,
        "lodo_high_gain_recall": lodo["high_gain_recall"] >= 0.65,
    }
    return all(checks.values()), checks


def k_for_name(name: str) -> int:
    base = name.removesuffix("_DIRECT")
    if base.startswith("KNN"):
        return int(base[3:])
    return 10_000


def main() -> None:
    rows = attach_outcomes(load_development_cases())
    candidates = ["ALWAYS_FULL", "ALWAYS_CONTROL", "DIRECT_BYPASS"]
    candidates += [f"KNN{k}" for k in K_VALUES] + [f"KNN{k}_DIRECT" for k in K_VALUES]
    candidates += ["NB", "NB_DIRECT"]

    results: dict[str, Any] = {}
    for name in candidates:
        loso = evaluate_cv(rows, name, "suite")
        lodo = evaluate_cv(rows, name, "domain")
        passed, checks = passes_gates(loso, lodo)
        if name in {"ALWAYS_FULL", "ALWAYS_CONTROL"}:
            passed = False
        results[name] = {"LOSO": loso, "LODO": lodo, "passes_all_development_gates": passed, "gate_checks": checks}

    qualifying = [name for name, result in results.items() if result["passes_all_development_gates"]]
    selected = None
    if qualifying:
        def rank(name: str) -> tuple[Any, ...]:
            r = results[name]
            loso, lodo = r["LOSO"], r["LODO"]
            return (
                min(loso["routed_score"], lodo["routed_score"]),
                -(abs(loso["paired_decrement"]) + abs(lodo["paired_decrement"])) / 2,
                -(loso["full_rate"] + lodo["full_rate"]) / 2,
                -k_for_name(name),
                name,
            )
        selected = max(qualifying, key=rank)

    report = {
        "measurement_version": "selective-routing-v4-development-v1",
        "evidence_status": "development on exposed v1-v3 cases; not fresh validation",
        "outcome_table_sha256": sha256_file(OUTCOMES),
        "n_cases": len(rows),
        "suite_counts": dict(Counter(r["suite"] for r in rows)),
        "mean_full_vs_control_score": sum(r["score"] for r in rows) / len(rows),
        "positive_gain_cases": sum(r["gain"] > 0 for r in rows),
        "tie_gain_cases": sum(r["gain"] == 0 for r in rows),
        "negative_gain_cases": sum(r["gain"] < 0 for r in rows),
        "target_full_rate": TARGET_FULL_RATE,
        "candidates": results,
        "qualifying_candidates": qualifying,
        "selected_candidate": selected,
        "stop_rule_triggered": selected is None,
        "next_step": (
            "freeze selected development candidate before authoring any fresh v4 validation suite"
            if selected else
            "stop routing development; prefer ALWAYS_FULL or only a separately justified trivial direct bypass"
        ),
    }
    out = ROOT / "results_routing_v4_development.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({
        "n_cases": report["n_cases"],
        "mean_full_vs_control_score": report["mean_full_vs_control_score"],
        "qualifying_candidates": qualifying,
        "selected_candidate": selected,
        "stop_rule_triggered": report["stop_rule_triggered"],
        "candidate_summary": {
            name: {
                "loso_score": result["LOSO"]["routed_score"],
                "loso_delta": result["LOSO"]["paired_decrement"],
                "loso_full_rate": result["LOSO"]["full_rate"],
                "loso_high_gain_recall": result["LOSO"]["high_gain_recall"],
                "lodo_score": result["LODO"]["routed_score"],
                "lodo_delta": result["LODO"]["paired_decrement"],
                "lodo_full_rate": result["LODO"]["full_rate"],
                "lodo_high_gain_recall": result["LODO"]["high_gain_recall"],
                "passes": result["passes_all_development_gates"],
            }
            for name, result in results.items()
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
