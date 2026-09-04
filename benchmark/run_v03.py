#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any

# Reuse the established controller prompts and case structure without invoking
# the legacy provider path.
os.environ.setdefault("OPENAI_API_KEY", "unused-provider-shim")
import pilot  # noqa: E402
from zai_adapter import DEFAULT_BASE_URL, chat_completion  # noqa: E402

ROOT = Path(__file__).resolve().parent
TARGET_MODEL = os.getenv("ZAI_TARGET_MODEL", "glm-5.1")
JUDGE_MODEL = os.getenv("ZAI_JUDGE_MODEL", TARGET_MODEL)
TARGET_KEY = os.environ["ZAI_API_KEY"]
JUDGE_KEY = os.getenv("ZAI_JUDGE_API_KEY") or TARGET_KEY
TARGET_BASE = os.getenv("ZAI_BASE_URL", DEFAULT_BASE_URL)
JUDGE_BASE = os.getenv("ZAI_JUDGE_BASE_URL", TARGET_BASE)
REPLICATES = max(1, int(os.getenv("BENCHMARK_REPLICATES", "1")))
SUITE = os.getenv("BENCHMARK_SUITE", "stress").lower()
BOOTSTRAP_SAMPLES = max(500, int(os.getenv("BENCHMARK_BOOTSTRAP_SAMPLES", "5000")))

STRICT_PROTOCOL_JUDGE = r'''You are a strict blinded evaluator of reasoning-protocol behavior. You are not told which experimental condition produced the response. Score ONLY the listed applicable dimensions from 0 to 4 using the anchors below. Do not reward headings, jargon, verbosity, or a merely plausible answer.

Anchors:
0 = absent, contradicted by the response, or a serious failure.
1 = weak; major decision-relevant errors or omissions.
2 = partial; some correct reasoning but at least one important gap.
3 = strong; substantively correct with at most one non-fatal omission or calibration issue.
4 = exceptional; complete on the dimension, precise, evidence-calibrated, and no material omission.

Use 4 sparingly. If a turn-specific reference contains multiple decision-critical requirements and any is materially missing, that dimension cannot receive 4. If the response asserts causation or confidence beyond the supplied evidence, penalize the relevant observation/evidence/uncertainty dimensions even when the final recommendation happens to be good. Evaluate only the transcript prefix and turn-specific reference; never infer future evidence.

Return JSON only:
{"scores":{"criterion":0},"violations":["Pxx"],"notes":"brief justification naming the main missing or strong element"}

Violation codes: P01 premature solutioning; P02 observation/inference collapse; P03 single-hypothesis fixation; P04 principle laundering; P05 correlation as mechanism; P06 unfalsifiable explanation; P07 post-hoc prediction; P08 confirmation-only testing; P09 evidence-free confidence; P10 model-preservation bias; P11 uncertainty erasure; P12 hidden critical assumption; P13 constraint blindness; P14 solution monoculture; P15 solution-model disconnect; P16 local optimization; P17 fragile decision; P18 premature irreversibility; P19 premature termination; P20 analysis paralysis; P21 ceremonial compliance.'''

STRICT_OUTCOME_JUDGE = r'''You are a strict blinded evaluator of answer and decision quality. Ignore named reasoning frameworks and score ONLY the listed applicable dimensions from 0 to 4.

Anchors:
0 = wrong or harmful relative to the supplied evidence/reference.
1 = mostly wrong or misses a decision-critical fact.
2 = mixed/partial; useful but materially incomplete.
3 = strong and decision-usable, with only a minor omission or imprecision.
4 = exceptional: correct, complete on the dimension, appropriately qualified, and no material decision-relevant omission.

Use 4 sparingly. A polished answer is not automatically a 4. If a reference contains several essential elements, missing one generally caps the relevant dimension at 3. decision_quality means the quality of the action or next step given ONLY the information available at that turn. Never use future evidence.

Return JSON only:
{"scores":{"criterion":0},"notes":"brief justification naming the main differentiator"}'''

STRICT_PAIRWISE_JUDGE = r'''You are a strict blinded pairwise evaluator. Compare Response A and Response B for the same case. You are not told which experimental condition produced either. Use the supplied reference as ground truth and judge substance, not style.

Priority order:
1. factual/causal correctness relative to available evidence;
2. quality of the decision or next action;
3. sensitivity to contradiction and revision across sequential turns;
4. discrimination among mechanisms and evidence quality;
5. calibrated uncertainty and assumption handling;
6. robustness/reversibility/second-order effects when relevant;
7. efficient reasoning depth.

Do not reward framework terminology, headings, or length. A shorter answer should win when it reaches the same or better decision with less unnecessary reasoning. TIE is appropriate only when neither response has a meaningful decision-relevant advantage.

Return JSON only:
{"winner":"A|B|TIE","confidence":0.0,"margin":0,"notes":"brief concrete reason"}
where margin is 0 for a tie, 1 for slight, 2 for clear, 3 for decisive.'''

JSON_SYSTEMS = {
    pilot.ROUTER,
    STRICT_PROTOCOL_JUDGE,
    STRICT_OUTCOME_JUDGE,
    STRICT_PAIRWISE_JUDGE,
}


def load_cases() -> list[dict[str, Any]]:
    original = json.loads((ROOT / "pilot_cases.json").read_text(encoding="utf-8"))
    stress = json.loads((ROOT / "stress_cases_v03.json").read_text(encoding="utf-8"))
    if SUITE == "pilot":
        return original
    if SUITE == "stress":
        return stress
    if SUITE == "combined":
        return original + stress
    raise ValueError("BENCHMARK_SUITE must be pilot, stress, or combined")


CASES = load_cases()


def parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def wire_messages(system: str | None, messages: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    if system:
        output.append({"role": "system", "content": system})
    output.extend(messages)
    return output


def target_call(system: str | None, messages: list[dict[str, str]], json_mode: bool = False) -> dict[str, Any]:
    return chat_completion(
        model=TARGET_MODEL,
        messages=wire_messages(system, messages),
        json_mode=json_mode,
        api_key=TARGET_KEY,
        base_url=TARGET_BASE,
        max_tokens_env="ZAI_MAX_TOKENS",
        temperature_env="ZAI_TEMPERATURE",
    )


def judge_call(system: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    return chat_completion(
        model=JUDGE_MODEL,
        messages=wire_messages(system, messages),
        json_mode=True,
        api_key=JUDGE_KEY,
        base_url=JUDGE_BASE,
        max_tokens_env="ZAI_JUDGE_MAX_TOKENS",
        temperature_env="ZAI_JUDGE_TEMPERATURE",
    )


def add_usage(total: dict[str, float], usage: dict[str, float]) -> None:
    for key in total:
        total[key] += float(usage.get(key, 0) or 0)


def expected_modes(case: dict[str, Any]) -> set[str]:
    value = case["expected_mode"]
    return {value} if isinstance(value, str) else set(value)


def route(case: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    result = target_call(
        pilot.ROUTER,
        [{"role": "user", "content": case["turns"][0]["agent_input"]}],
        json_mode=True,
    )
    parsed = parse_json(result["text"])
    mode = parsed.get("mode")
    if mode not in {"DIRECT", "COMPACT", "FULL"}:
        raise RuntimeError(f"invalid router mode: {parsed}")
    return mode, parsed.get("rationale", ""), result["usage"]


def run_case(case: dict[str, Any], condition: str, replicate: int) -> dict[str, Any]:
    usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}
    selected_mode = None
    rationale = None

    if condition == "ADAPTIVE":
        selected_mode, rationale, route_usage = route(case)
        add_usage(usage, route_usage)
        system = None if selected_mode == "DIRECT" else (pilot.COMPACT if selected_mode == "COMPACT" else pilot.FULL)
    else:
        system = {"BASELINE": None, "COMPACT": pilot.COMPACT, "FULL": pilot.FULL}[condition]

    messages: list[dict[str, str]] = []
    responses = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = target_call(system, messages)
        add_usage(usage, result["usage"])
        responses.append({"turn": turn["turn"], "text": result["text"]})
        messages.append({"role": "assistant", "content": result["text"]})

    route_correct = None
    if condition == "ADAPTIVE":
        route_correct = selected_mode in expected_modes(case)

    return {
        "case_id": case["case_id"],
        "condition": condition,
        "replicate": replicate,
        "selected_mode": selected_mode,
        "expected_modes": sorted(expected_modes(case)),
        "route_correct": route_correct,
        "router_rationale": rationale,
        "responses": responses,
        "usage": usage,
    }


def transcript(case: dict[str, Any], run: dict[str, Any], through: int) -> str:
    responses = {item["turn"]: item["text"] for item in run["responses"]}
    chunks = []
    for turn in case["turns"]:
        if turn["turn"] > through:
            break
        chunks.extend(
            [
                f"TURN {turn['turn']} USER:\n{turn['agent_input']}",
                f"TURN {turn['turn']} ASSISTANT:\n{responses[turn['turn']]}",
            ]
        )
    return "\n\n".join(chunks)


def judge_turn(case: dict[str, Any], run: dict[str, Any], turn: dict[str, Any], kind: str) -> dict[str, Any]:
    profile = case["evaluation_profile"]
    dimensions = list(profile["protocol_dimensions"] if kind == "protocol" else profile["outcome_dimensions"])
    # mode_fit is measured deterministically for ADAPTIVE rather than by a model judge.
    dimensions = [d for d in dimensions if d != "mode_fit"]
    if turn["turn"] == 1:
        dimensions = [d for d in dimensions if d != "revision"]

    content = {
        "case_id": case["case_id"],
        "turn": turn["turn"],
        "transcript_prefix": transcript(case, run, turn["turn"]),
        "applicable_dimensions": dimensions,
        "turn_reference": turn.get("judge_reference", {}).get(kind, []),
    }
    system = STRICT_PROTOCOL_JUDGE if kind == "protocol" else STRICT_OUTCOME_JUDGE
    result = judge_call(system, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
    parsed = parse_json(result["text"])
    scores = {
        key: float(value)
        for key, value in parsed.get("scores", {}).items()
        if key in dimensions and isinstance(value, (int, float)) and 0 <= float(value) <= 4
    }
    return {
        "scores": scores,
        "violations": parsed.get("violations", []) if kind == "protocol" else [],
        "notes": parsed.get("notes", ""),
        "usage": result["usage"],
    }


def evaluate(case: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    turns = []
    violations: set[str] = set()
    protocol_acc: dict[str, list[float]] = {}
    outcome_acc: dict[str, list[float]] = {}
    judge_usage = {"input_tokens": 0.0, "output_tokens": 0.0, "latency_ms": 0.0}

    for turn in case["turns"]:
        protocol = judge_turn(case, run, turn, "protocol")
        outcome = judge_turn(case, run, turn, "outcome")
        add_usage(judge_usage, protocol["usage"])
        add_usage(judge_usage, outcome["usage"])
        violations.update(protocol["violations"])
        for key, value in protocol["scores"].items():
            protocol_acc.setdefault(key, []).append(value)
        for key, value in outcome["scores"].items():
            outcome_acc.setdefault(key, []).append(value)
        turns.append(
            {
                "turn": turn["turn"],
                "protocol": {k: v for k, v in protocol.items() if k != "usage"},
                "outcome": {k: v for k, v in outcome.items() if k != "usage"},
            }
        )

    protocol_avg = {k: sum(v) / len(v) for k, v in protocol_acc.items()}
    outcome_avg = {k: sum(v) / len(v) for k, v in outcome_acc.items()}
    mode_fit = None
    if run["condition"] == "ADAPTIVE":
        mode_fit = 4.0 if run["route_correct"] else 0.0

    return {
        "protocol_scores": protocol_avg,
        "outcome_scores": outcome_avg,
        "protocol_mean_secondary": sum(protocol_avg.values()) / len(protocol_avg) if protocol_avg else 0.0,
        "quality_mean_secondary": sum(outcome_avg.values()) / len(outcome_avg) if outcome_avg else 0.0,
        "mode_fit_deterministic": mode_fit,
        "violations": sorted(violations),
        "turns": turns,
        "judge_usage": judge_usage,
    }


def pairwise(case: dict[str, Any], baseline: dict[str, Any], challenger: dict[str, Any]) -> dict[str, Any]:
    seed_material = f"{case['case_id']}:{challenger['condition']}:{challenger['replicate']}"
    first, second = baseline, challenger
    if random.Random(seed_material).random() < 0.5:
        first, second = second, first

    reference = {
        key: value
        for key, value in case["evaluator_key"].items()
        if key in {
            "observations",
            "not_observed",
            "plausible_hypotheses",
            "critical_first_principles",
            "discriminating_evidence",
            "decision_critical_uncertainties",
            "constraints",
            "acceptable_interventions",
            "scoring_notes",
        } and value
    }
    last_turn = case["turns"][-1]["turn"]
    content = {
        "case_id": case["case_id"],
        "reference": reference,
        "response_A": transcript(case, first, last_turn),
        "response_B": transcript(case, second, last_turn),
    }
    result = judge_call(STRICT_PAIRWISE_JUDGE, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}])
    parsed = parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid pairwise result: {parsed}")
    resolved = "TIE" if winner == "TIE" else ((first if winner == "A" else second)["condition"])
    score = 0.5 if resolved == "TIE" else (1.0 if resolved == challenger["condition"] else 0.0)
    return {
        "case_id": case["case_id"],
        "replicate": challenger["replicate"],
        "challenger": challenger["condition"],
        "winner": resolved,
        "challenger_score": score,
        "confidence": parsed.get("confidence"),
        "margin": parsed.get("margin"),
        "notes": parsed.get("notes", ""),
        "usage": result["usage"],
    }


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def clustered_pairwise_ci(pairs: list[dict[str, Any]], condition: str) -> dict[str, float]:
    relevant = [p for p in pairs if p["challenger"] == condition]
    by_case: dict[str, list[float]] = {}
    for pair in relevant:
        by_case.setdefault(pair["case_id"], []).append(float(pair["challenger_score"]))
    case_means = {case: sum(scores) / len(scores) for case, scores in by_case.items()}
    observed = sum(case_means.values()) / len(case_means) if case_means else 0.0
    cases = list(case_means)
    if len(cases) < 2:
        return {"score": observed, "ci95_low": observed, "ci95_high": observed}
    rng = random.Random(20260904)
    draws = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sampled = [case_means[rng.choice(cases)] for _ in cases]
        draws.append(sum(sampled) / len(sampled))
    return {
        "score": observed,
        "ci95_low": percentile(draws, 0.025),
        "ci95_high": percentile(draws, 0.975),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def main() -> None:
    output_dir = ROOT / "results_v03"
    output_dir.mkdir(exist_ok=True)
    runs_path = output_dir / "v03_runs.jsonl"
    pairs_path = output_dir / "v03_pairwise.jsonl"
    runs: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []

    for replicate in range(1, REPLICATES + 1):
        for case in CASES:
            for condition in ["BASELINE", "COMPACT", "FULL", "ADAPTIVE"]:
                print("running", replicate, case["case_id"], condition, flush=True)
                run = run_case(case, condition, replicate)
                print("evaluating", replicate, case["case_id"], condition, flush=True)
                run["evaluation"] = evaluate(case, run)
                runs.append(run)
                write_jsonl(runs_path, runs)  # checkpoint after every completed run

        index = {(r["case_id"], r["condition"], r["replicate"]): r for r in runs}
        for case in CASES:
            baseline = index[(case["case_id"], "BASELINE", replicate)]
            for condition in ["COMPACT", "FULL", "ADAPTIVE"]:
                print("pairwise", replicate, case["case_id"], condition, flush=True)
                pairs.append(pairwise(case, baseline, index[(case["case_id"], condition, replicate)]))
                write_jsonl(pairs_path, pairs)  # checkpoint after every pair

    summary: dict[str, Any] = {}
    for condition in ["BASELINE", "COMPACT", "FULL", "ADAPTIVE"]:
        condition_runs = [r for r in runs if r["condition"] == condition]
        entry: dict[str, Any] = {
            "n_runs": len(condition_runs),
            "n_cases": len({r["case_id"] for r in condition_runs}),
            "quality_mean_secondary": sum(r["evaluation"]["quality_mean_secondary"] for r in condition_runs) / len(condition_runs),
            "protocol_mean_secondary": sum(r["evaluation"]["protocol_mean_secondary"] for r in condition_runs) / len(condition_runs),
            "input_tokens": int(sum(r["usage"]["input_tokens"] for r in condition_runs)),
            "output_tokens": int(sum(r["usage"]["output_tokens"] for r in condition_runs)),
            "latency_ms": sum(r["usage"]["latency_ms"] for r in condition_runs),
        }
        if condition != "BASELINE":
            ci = clustered_pairwise_ci(pairs, condition)
            condition_pairs = [p for p in pairs if p["challenger"] == condition]
            entry["primary_pairwise"] = {
                **ci,
                "wins": sum(p["winner"] == condition for p in condition_pairs),
                "ties": sum(p["winner"] == "TIE" for p in condition_pairs),
                "losses": sum(p["winner"] == "BASELINE" for p in condition_pairs),
            }
        if condition == "ADAPTIVE":
            entry["routing"] = {
                "accuracy": sum(bool(r["route_correct"]) for r in condition_runs) / len(condition_runs),
                "correct": sum(bool(r["route_correct"]) for r in condition_runs),
                "total": len(condition_runs),
                "errors": [
                    {
                        "case_id": r["case_id"],
                        "replicate": r["replicate"],
                        "selected": r["selected_mode"],
                        "expected": r["expected_modes"],
                    }
                    for r in condition_runs if not r["route_correct"]
                ],
            }
        summary[condition] = entry

    same_model_judge = TARGET_MODEL == JUDGE_MODEL and TARGET_BASE == JUDGE_BASE
    report = {
        "measurement_version": "0.3",
        "suite": SUITE,
        "replicates": REPLICATES,
        "primary_metric": "blinded pairwise challenger score vs baseline, clustered by case",
        "secondary_metric": "strict anchored scalar judge means",
        "provider": "z.ai",
        "target": {"model": TARGET_MODEL, "base_url": TARGET_BASE},
        "judge": {"model": JUDGE_MODEL, "base_url": JUDGE_BASE, "same_model_and_endpoint_as_target": same_model_judge},
        "notes": [
            "Pairwise score: win=1, tie=0.5, loss=0.",
            "95% confidence intervals bootstrap cases as clusters; stochastic replicates within a case are averaged before resampling.",
            "Adaptive mode fit is deterministic against case gold labels and is not model-judged.",
            "Scalar 0-4 judge scores are secondary because Pilot #1 showed ceiling saturation.",
        ],
        "summary": summary,
    }
    (output_dir / "v03_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
