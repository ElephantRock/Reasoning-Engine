#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["BENCHMARK_SUITE"] = "combined"
import run_v05 as v05  # noqa: E402
import run_v07 as v07  # noqa: E402
import run_v08 as v08  # noqa: E402

v03 = v05.v03
ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "selective_control_cases_v09.json").read_text(encoding="utf-8"))

GENERATION_REPLICATES = max(1, int(os.getenv("V09_GENERATION_REPLICATES", "3")))
JUDGE_VOTES = int(os.getenv("V09_JUDGE_VOTES", "3"))
STRESS_DROP_GATE = float(os.getenv("V09_STRESS_DROP_GATE", "0.5"))
RECOVERY_LIFT_GATE = float(os.getenv("V09_RECOVERY_LIFT_GATE", "0.5"))

if JUDGE_VOTES < 3 or JUDGE_VOTES % 2 == 0:
    raise ValueError("V09_JUDGE_VOTES must be an odd integer >= 3")

FAMILIES = ("DIAGNOSE", "REVISE", "ENGINEER")
VARIANTS = ("CLEAN", "STRESS")
CONDITIONS = ("CONTROL", "ATTENTION", "TARGET")

CONTROL = v08.CONTROL
ATTENTION = v08.ATTENTION
TARGET_MODULES = {family: v07.TARGET_MODULES[family] for family in FAMILIES}
PAIR_SPECS = v08.PAIR_SPECS


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def system_for(case: dict[str, Any], condition: str) -> str:
    if condition == "CONTROL":
        return CONTROL
    if condition == "ATTENTION":
        return ATTENTION
    if condition == "TARGET":
        return CONTROL + TARGET_MODULES[case["family"]]
    raise ValueError(condition)


def transcript(case: dict[str, Any], run: dict[str, Any]) -> str:
    return v03.transcript(case, run, case["turns"][-1]["turn"])


def generate(case: dict[str, Any], condition: str, replicate: int) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    messages: list[dict[str, str]] = []
    responses: list[dict[str, Any]] = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = v03.target_call(system_for(case, condition), messages)
        v03.add_usage(usage, result["usage"])
        responses.append({"turn": turn["turn"], "text": result["text"]})
        messages.append({"role": "assistant", "content": result["text"]})
    return {
        "case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "family": case["family"],
        "variant": case["variant"],
        "condition": condition,
        "replicate": replicate,
        "responses": responses,
        "usage": usage,
    }


def absolute_behavior_vote(case: dict[str, Any], run: dict[str, Any], vote_index: int) -> dict[str, Any]:
    content = {
        "case_id": case["case_id"],
        "target_behavior": case["evaluator_key"]["target_behavior"],
        "response": transcript(case, run),
    }
    result = v03.judge_call(
        v08.SCREEN_BEHAVIOR_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    score = parsed.get("score")
    if not isinstance(score, (int, float)) or not 0 <= float(score) <= 4:
        raise RuntimeError(f"invalid absolute behavior score: {parsed}")
    return {
        "case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "family": case["family"],
        "variant": case["variant"],
        "condition": run["condition"],
        "replicate": run["replicate"],
        "vote_index": vote_index,
        "score": float(score),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def pair_behavior_vote(
    case: dict[str, Any],
    target: dict[str, Any],
    control: dict[str, Any],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"v09-behavior:{case['case_id']}:{target['replicate']}:{vote_index}"
    first, second = target, control
    if random.Random(seed).random() < 0.5:
        first, second = second, first
    content = {
        "case_id": case["case_id"],
        "target_behavior": case["evaluator_key"]["target_behavior"],
        "response_A": transcript(case, first),
        "response_B": transcript(case, second),
    }
    result = v03.judge_call(
        v08.PAIR_BEHAVIOR_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    a, b = parsed.get("A_score"), parsed.get("B_score")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise RuntimeError(f"invalid pair behavior score: {parsed}")
    if not (0 <= float(a) <= 4 and 0 <= float(b) <= 4):
        raise RuntimeError(f"pair behavior score out of range: {parsed}")
    scores = {first["condition"]: float(a), second["condition"]: float(b)}
    return {
        "case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "family": case["family"],
        "variant": case["variant"],
        "replicate": target["replicate"],
        "vote_index": vote_index,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "target_score": scores["TARGET"],
        "control_score": scores["CONTROL"],
        "lift": scores["TARGET"] - scores["CONTROL"],
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def quality_reference(case: dict[str, Any]) -> dict[str, Any]:
    evaluator = case.get("evaluator_key", {})
    allowed = {
        "observations",
        "not_observed",
        "plausible_hypotheses",
        "discriminating_evidence",
        "decision_critical_uncertainties",
        "constraints",
        "acceptable_interventions",
        "scoring_notes",
    }
    return {
        "case_id": case["case_id"],
        "case_reference": {k: v for k, v in evaluator.items() if k in allowed and v},
        "turn_references": [
            {"turn": t["turn"], "expected_revision": t.get("expected_revision")}
            for t in case["turns"]
        ],
    }


def quality_vote(
    case: dict[str, Any],
    run_x: dict[str, Any],
    run_y: dict[str, Any],
    spec: dict[str, str],
    vote_index: int,
) -> dict[str, Any]:
    seed = f"v09-quality:{case['case_id']}:{run_x['replicate']}:{spec['pair_id']}:{vote_index}"
    first, second = run_x, run_y
    if random.Random(seed).random() < 0.5:
        first, second = second, first
    content = {
        **quality_reference(case),
        "response_A": transcript(case, first),
        "response_B": transcript(case, second),
    }
    result = v03.judge_call(
        v08.QUALITY_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
    )
    parsed = v03.parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid quality result: {parsed}")
    resolved = "TIE" if winner == "TIE" else (first if winner == "A" else second)["condition"]
    focal = spec["focal"]
    focal_score = 0.5 if resolved == "TIE" else (1.0 if resolved == focal else 0.0)
    return {
        "case_id": case["case_id"],
        "case_pair_id": case["pair_id"],
        "pair_id": spec["pair_id"],
        "family": case["family"],
        "variant": case["variant"],
        "replicate": run_x["replicate"],
        "pair_role": spec["role"],
        "focal_condition": focal,
        "vote_index": vote_index,
        "A_condition": first["condition"],
        "B_condition": second["condition"],
        "winner": resolved,
        "focal_score": focal_score,
        "confidence": parsed.get("confidence"),
        "margin": parsed.get("margin"),
        "decisive_dimensions": parsed.get("decisive_dimensions", []),
        "notes": parsed.get("notes", ""),
        "judge_usage": result["usage"],
    }


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def stress_summary(
    absolute_votes: list[dict[str, Any]],
    pair_behavior_votes: list[dict[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for family in FAMILIES:
        clean_abs = [
            v["score"] for v in absolute_votes
            if v["family"] == family and v["variant"] == "CLEAN" and v["condition"] == "CONTROL"
        ]
        stress_abs = [
            v["score"] for v in absolute_votes
            if v["family"] == family and v["variant"] == "STRESS" and v["condition"] == "CONTROL"
        ]
        clean_mean = mean(clean_abs)
        stress_mean = mean(stress_abs)
        stress_drop = (clean_mean - stress_mean) if clean_mean is not None and stress_mean is not None else None

        stress_pair = [
            v for v in pair_behavior_votes
            if v["family"] == family and v["variant"] == "STRESS"
        ]
        clean_pair = [
            v for v in pair_behavior_votes
            if v["family"] == family and v["variant"] == "CLEAN"
        ]
        stress_target = mean([v["target_score"] for v in stress_pair])
        stress_control = mean([v["control_score"] for v in stress_pair])
        clean_target = mean([v["target_score"] for v in clean_pair])
        clean_control = mean([v["control_score"] for v in clean_pair])
        stress_recovery = (
            stress_target - stress_control
            if stress_target is not None and stress_control is not None
            else None
        )
        clean_lift = (
            clean_target - clean_control
            if clean_target is not None and clean_control is not None
            else None
        )
        out[family] = {
            "clean_control_behavior_mean": clean_mean,
            "stress_control_behavior_mean": stress_mean,
            "stress_behavior_drop": stress_drop,
            "stress_effect_gate": stress_drop is not None and stress_drop >= STRESS_DROP_GATE,
            "stress_drop_threshold": STRESS_DROP_GATE,
            "clean_target_minus_control_behavior_lift": clean_lift,
            "stress_target_behavior_mean": stress_target,
            "stress_pair_control_behavior_mean": stress_control,
            "stress_target_minus_control_behavior_lift": stress_recovery,
            "recovery_gate": stress_recovery is not None and stress_recovery >= RECOVERY_LIFT_GATE,
            "recovery_threshold": RECOVERY_LIFT_GATE,
            "recovery_fraction_of_stress_drop": (
                stress_recovery / stress_drop
                if stress_drop is not None and stress_drop > 0 and stress_recovery is not None
                else None
            ),
        }
    return out


def aggregate_quality(votes: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for spec in PAIR_SPECS:
        spec_rows = [v for v in votes if v["pair_id"] == spec["pair_id"]]
        by_variant: dict[str, Any] = {}
        for variant in VARIANTS:
            rows = [v for v in spec_rows if v["variant"] == variant]
            by_variant[variant] = v05.aggregate_pair(rows, spec) if rows else None
        by_family: dict[str, Any] = {}
        for family in FAMILIES:
            by_family[family] = {}
            for variant in VARIANTS:
                rows = [
                    v for v in spec_rows
                    if v["family"] == family and v["variant"] == variant
                ]
                by_family[family][variant] = v05.aggregate_pair(rows, spec) if rows else None
        result[spec["pair_id"]] = {
            "overall": v05.aggregate_pair(spec_rows, spec) if spec_rows else None,
            "by_variant": by_variant,
            "by_family_variant": by_family,
        }
    return result


def paired_quality_interaction(votes: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [v for v in votes if v["pair_id"] == "TARGET_vs_CONTROL"]
    result: dict[str, Any] = {}
    for family in FAMILIES:
        pair_ids = sorted({v["case_pair_id"] for v in rows if v["family"] == family})
        pair_effects = []
        for pair_id in pair_ids:
            variant_scores = {}
            for variant in VARIANTS:
                subset = [
                    v for v in rows
                    if v["family"] == family and v["case_pair_id"] == pair_id and v["variant"] == variant
                ]
                by_rep = []
                for rep in sorted({v["replicate"] for v in subset}):
                    xs = [v["focal_score"] for v in subset if v["replicate"] == rep]
                    by_rep.append(sum(xs) / len(xs))
                variant_scores[variant] = mean(by_rep)
            if variant_scores["CLEAN"] is not None and variant_scores["STRESS"] is not None:
                pair_effects.append({
                    "pair_id": pair_id,
                    "clean_score": variant_scores["CLEAN"],
                    "stress_score": variant_scores["STRESS"],
                    "stress_minus_clean": variant_scores["STRESS"] - variant_scores["CLEAN"],
                })
        result[family] = {
            "pair_effects": pair_effects,
            "mean_stress_minus_clean": mean([p["stress_minus_clean"] for p in pair_effects]),
        }
    return result


def usage_totals(runs: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for condition in CONDITIONS:
        subset = [r for r in runs if r["condition"] == condition]
        out[condition] = {
            "n_runs": len(subset),
            "target_input_tokens": int(sum(r["usage"]["input_tokens"] for r in subset)),
            "target_output_tokens": int(sum(r["usage"]["output_tokens"] for r in subset)),
            "target_latency_ms": sum(r["usage"]["latency_ms"] for r in subset),
        }
    return out


def main() -> None:
    out = ROOT / "results_v09"
    out.mkdir(exist_ok=True)

    runs: list[dict[str, Any]] = []
    absolute_votes: list[dict[str, Any]] = []
    behavior_votes: list[dict[str, Any]] = []
    quality_votes: list[dict[str, Any]] = []

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            for condition in CONDITIONS:
                print("generate", replicate, case["case_id"], condition, flush=True)
                runs.append(generate(case, condition, replicate))
                write_jsonl(out / "v09_runs.jsonl", runs)

    index = {
        (r["case_id"], r["condition"], r["replicate"]): r
        for r in runs
    }

    for replicate in range(1, GENERATION_REPLICATES + 1):
        for case in CASES:
            control = index[(case["case_id"], "CONTROL", replicate)]
            target = index[(case["case_id"], "TARGET", replicate)]

            for vote_index in range(1, JUDGE_VOTES + 1):
                print("absolute behavior", replicate, case["case_id"], vote_index, flush=True)
                absolute_votes.append(absolute_behavior_vote(case, control, vote_index))
                write_jsonl(out / "v09_absolute_behavior_votes.jsonl", absolute_votes)

                print("pair behavior", replicate, case["case_id"], vote_index, flush=True)
                behavior_votes.append(pair_behavior_vote(case, target, control, vote_index))
                write_jsonl(out / "v09_pair_behavior_votes.jsonl", behavior_votes)

            for spec in PAIR_SPECS:
                left = index[(case["case_id"], spec["left"], replicate)]
                right = index[(case["case_id"], spec["right"], replicate)]
                for vote_index in range(1, JUDGE_VOTES + 1):
                    print("quality", replicate, case["case_id"], spec["pair_id"], vote_index, flush=True)
                    quality_votes.append(quality_vote(case, left, right, spec, vote_index))
                    write_jsonl(out / "v09_quality_votes.jsonl", quality_votes)

    stress = stress_summary(absolute_votes, behavior_votes)
    quality = aggregate_quality(quality_votes)
    interaction = paired_quality_interaction(quality_votes)

    interpretation: dict[str, Any] = {}
    primary = quality["TARGET_vs_CONTROL"]["by_family_variant"]
    specificity = quality["TARGET_vs_ATTENTION"]["by_family_variant"]
    attention = quality["ATTENTION_vs_CONTROL"]["by_family_variant"]
    for family in FAMILIES:
        stress_ok = stress[family]["stress_effect_gate"]
        recovery_ok = stress[family]["recovery_gate"]
        identified = stress_ok and recovery_ok
        interpretation[family] = {
            "stress_effect_identified": stress_ok,
            "target_recovery_identified": recovery_ok,
            "selective_control_identified": identified,
            "stress_target_vs_control_quality_score": (
                primary[family]["STRESS"]["score"] if primary[family]["STRESS"] else None
            ),
            "stress_target_vs_attention_quality_score": (
                specificity[family]["STRESS"]["score"] if specificity[family]["STRESS"] else None
            ),
            "stress_attention_vs_control_quality_score": (
                attention[family]["STRESS"]["score"] if attention[family]["STRESS"] else None
            ),
            "clean_target_vs_control_quality_score": (
                primary[family]["CLEAN"]["score"] if primary[family]["CLEAN"] else None
            ),
            "interpretation_rule": (
                "Stress suppressed endogenous target behavior and the explicit module restored it; stress quality effects may be interpreted as selective-control evidence."
                if identified
                else "At least one behavioral gate failed; quality differences are non-identifying for selective-control value."
            ),
        }

    report = {
        "measurement_version": "0.9-selective-control-under-stress",
        "experiment_role": "development diagnostic, not held-out validation",
        "primary_research_question": (
            "When adverse context suppresses endogenous reasoning, does an explicit capability module recover the target behavior and improve reasoning quality beyond generic attention?"
        ),
        "families": list(FAMILIES),
        "n_case_variants": len(CASES),
        "n_base_pairs": len({c["pair_id"] for c in CASES}),
        "generation_replicates": GENERATION_REPLICATES,
        "judge_votes": JUDGE_VOTES,
        "conditions": {
            "CONTROL": "minimal neutral reasoning prompt",
            "ATTENTION": "CONTROL plus a generic extra quality-control pass",
            "TARGET": "CONTROL plus the frozen family-specific capability module from v0.7",
        },
        "stress_design": {
            "paired_clean_stress": True,
            "stressors": "authority anchors, irrelevant metrics, conflicting stakeholder pressure, historical analogies, time pressure, and familiar-action bias; decisive evidence and correct action are held constant within each pair",
            "stress_gate": f"CLEAN minus STRESS CONTROL behavior >= {STRESS_DROP_GATE} on the 0-4 behavior scale",
            "recovery_gate": f"STRESS TARGET minus STRESS CONTROL behavior >= {RECOVERY_LIFT_GATE} on the 0-4 behavior scale",
        },
        "stress_and_recovery": stress,
        "quality_results": quality,
        "paired_quality_interaction": interaction,
        "family_interpretation": interpretation,
        "cost_policy": "cost is descriptive only and does not enter identification or quality decisions",
        "cost_diagnostics": usage_totals(runs),
        "provider": "z.ai",
        "target": {"model": v03.TARGET_MODEL, "base_url": v03.TARGET_BASE},
        "judge": {
            "model": v03.JUDGE_MODEL,
            "base_url": v03.JUDGE_BASE,
            "same_model_and_endpoint_as_target": (
                v03.TARGET_MODEL == v03.JUDGE_MODEL and v03.TARGET_BASE == v03.JUDGE_BASE
            ),
        },
        "notes": [
            "The production reasoning protocol is unchanged.",
            "DIAGNOSE, REVISE, and ENGINEER target modules are frozen byte-for-byte from v0.7.",
            "v0.9 tests selective control under adverse context, not whether the model possesses the capability in easy conditions.",
            "Cases are development diagnostics and cannot serve as fresh held-out validation.",
            "A later model-family replication should test whether control value increases as endogenous capability decreases.",
        ],
    }
    (out / "v09_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
