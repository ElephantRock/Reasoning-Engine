#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import re
import time
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "pilot_cases.json").read_text(encoding="utf-8"))
TARGET = os.getenv("OPENAI_TARGET_MODEL", "gpt-5.6-sol")
JUDGE = os.getenv("OPENAI_JUDGE_MODEL", TARGET)
API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=API_KEY, base_url=os.getenv("OPENAI_BASE_URL") or None)

COMPACT = """You are a reasoning agent. For non-trivial tasks, use internally: Problem → First Principle → Mechanism → Evidence → Solution. Define the actual problem before solving it. Distinguish observation, inference, assumption, hypothesis, prediction, evidence, conclusion, and recommendation. First principles are necessities/invariants, not conventions or existing implementations. A plausible explanation is not an established cause; correlation is not mechanism. Expose decision-critical assumptions and uncertainty. Seek evidence capable of weakening the favored mechanism. Revise when evidence contradicts the model. Engineer from the best-supported mechanism under constraints, including risk, reversibility, side effects, and second-order effects. Stop when more information is unlikely to change the action. For trivial or established tasks, answer directly. Do not mechanically emit protocol headings."""

FULL = """You are a reasoning agent operating under: Observe → Diagnose → Derive → Hypothesize → Predict → Test → Revise → Engineer. For trivial tasks answer directly; for moderate established tasks compress to Problem → First Principle → Mechanism → Evidence → Solution. Separate observations from interpretations. Generate multiple plausible explanations under material ambiguity. Distinguish symptoms, proximate causes, and root causes. Derive first principles as necessities/invariants, not conventions, precedent, analogies, or current implementations. Express important explanations as falsifiable mechanisms; derive observable predictions and prefer discriminating/falsifying tests. Contradictions require model revision. Preserve uncertainty; confidence tracks evidence. Expose critical assumptions. Engineer only after sufficient understanding; compare effectiveness, robustness, cost, risk, reversibility, feasibility, constraints, feedback loops, side effects, and second-order effects. Continue when uncertainty is material and reducible; stop when further information has insufficient decision value. After intervention, predict and observe outcomes. Do not mechanically expose the entire internal state."""

ROUTER = """Choose the least expensive reasoning mode that preserves reliability. DIRECT: trivial, deterministic, or established answer where causal investigation adds no value. COMPACT: moderately complex task with a reasonably established mechanism or one decision-critical uncertainty. FULL: substantial ambiguity, competing causal explanations, contradictory/sequential evidence, high stakes, or important second-order/robustness analysis. Return JSON only: {\"mode\":\"DIRECT|COMPACT|FULL\",\"rationale\":\"one short sentence\"}."""

PROTO_JUDGE = """You are a blinded evaluator of reasoning-protocol behavior. You are not told which experimental condition produced the response. Score only the dimensions listed as applicable from 0 to 4. Do not reward headings, protocol jargon, or verbosity. Use only the transcript prefix and turn-specific reference; never infer future evidence. Return JSON only: {\"scores\":{\"criterion\":0},\"violations\":[\"Pxx\"],\"notes\":\"brief justification\"}. Relevant violation codes: P01 premature solutioning; P02 observation/inference collapse; P03 single-hypothesis fixation; P04 principle laundering; P05 correlation as mechanism; P06 unfalsifiable explanation; P07 post-hoc prediction; P08 confirmation-only testing; P09 evidence-free confidence; P10 model-preservation bias; P11 uncertainty erasure; P12 hidden critical assumption; P13 constraint blindness; P14 solution monoculture; P15 solution-model disconnect; P16 local optimization; P17 fragile decision; P18 premature irreversibility; P19 premature termination; P20 analysis paralysis; P21 ceremonial compliance."""

OUTCOME_JUDGE = """You are a blinded evaluator of answer and decision quality. Ignore named reasoning frameworks. Score only listed applicable dimensions from 0 to 4. Use only the transcript prefix and turn-specific reference; never use future evidence. decision_quality means the quality of the proposed decision or next action given information currently available. Return JSON only: {\"scores\":{\"criterion\":0},\"notes\":\"brief justification\"}."""

PAIRWISE_JUDGE = """You are a blinded pairwise evaluator. Compare Response A and Response B for the same case. You are not told which condition produced either. Use the supplied reference as ground truth. Do not reward framework terminology, headings, or verbosity. Prefer better correctness, causal/mechanistic reasoning where relevant, evidence use, revision across turns, calibrated uncertainty, decision quality, robustness, and efficient depth. For sequential cases judge the trajectory against evidence available at each turn. Return JSON only: {\"winner\":\"A|B|TIE\",\"confidence\":0.0,\"notes\":\"brief reason\"}."""

CONDITION_PROMPTS = {"BASELINE": None, "COMPACT": COMPACT, "FULL": FULL}


def parse_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def call(system, messages, model):
    kwargs = {"model": model, "input": messages, "store": False}
    if system:
        kwargs["instructions"] = system
    max_out = os.getenv("OPENAI_MAX_OUTPUT_TOKENS")
    if max_out:
        kwargs["max_output_tokens"] = int(max_out)
    effort = os.getenv("OPENAI_REASONING_EFFORT")
    if effort:
        kwargs["reasoning"] = {"effort": effort}

    last = None
    for attempt in range(4):
        started = time.perf_counter()
        try:
            response = client.responses.create(**kwargs)
            usage = response.usage
            return {
                "text": response.output_text or "",
                "usage": {
                    "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
                    "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
                    "latency_ms": (time.perf_counter() - started) * 1000,
                },
                "response_id": response.id,
            }
        except Exception as exc:
            last = exc
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    raise last


def add_usage(total, usage):
    for key in total:
        total[key] += usage.get(key, 0) or 0


def route(case):
    result = call(ROUTER, [{"role": "user", "content": case["turns"][0]["agent_input"]}], TARGET)
    parsed = parse_json(result["text"])
    mode = parsed.get("mode")
    if mode not in {"DIRECT", "COMPACT", "FULL"}:
        raise RuntimeError(f"invalid router mode: {parsed}")
    return mode, parsed.get("rationale", ""), result["usage"]


def run_case(case, condition):
    usage = {"input_tokens": 0, "output_tokens": 0, "latency_ms": 0.0}
    mode = None
    rationale = None

    if condition == "ADAPTIVE":
        mode, rationale, route_usage = route(case)
        add_usage(usage, route_usage)
        system = None if mode == "DIRECT" else (COMPACT if mode == "COMPACT" else FULL)
    else:
        system = CONDITION_PROMPTS[condition]
        mode = condition if condition in {"COMPACT", "FULL"} else None

    messages = []
    responses = []
    for turn in case["turns"]:
        messages.append({"role": "user", "content": turn["agent_input"]})
        result = call(system, messages, TARGET)
        add_usage(usage, result["usage"])
        responses.append({"turn": turn["turn"], "text": result["text"]})
        messages.append({"role": "assistant", "content": result["text"]})

    return {
        "case_id": case["case_id"],
        "condition": condition,
        "selected_mode": mode,
        "router_rationale": rationale,
        "responses": responses,
        "usage": usage,
    }


def transcript(case, run, through):
    responses = {item["turn"]: item["text"] for item in run["responses"]}
    chunks = []
    for turn in case["turns"]:
        if turn["turn"] > through:
            break
        chunks += [
            f"TURN {turn['turn']} USER:\n{turn['agent_input']}",
            f"TURN {turn['turn']} ASSISTANT:\n{responses[turn['turn']]}",
        ]
    return "\n\n".join(chunks)


def judge_turn(case, run, turn, kind):
    profile = case["evaluation_profile"]
    dimensions = list(profile["protocol_dimensions"] if kind == "protocol" else profile["outcome_dimensions"])
    dimensions = [dimension for dimension in dimensions if dimension != "mode_fit"]
    if turn["turn"] == 1:
        dimensions = [dimension for dimension in dimensions if dimension != "revision"]

    reference = turn.get("judge_reference", {}).get(kind, [])
    content = {
        "case_id": case["case_id"],
        "turn": turn["turn"],
        "transcript_prefix": transcript(case, run, turn["turn"]),
        "applicable_dimensions": dimensions,
        "turn_reference": reference,
    }
    result = call(
        PROTO_JUDGE if kind == "protocol" else OUTCOME_JUDGE,
        [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
        JUDGE,
    )
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


def evaluate(case, run):
    turns = []
    violations = set()
    protocol_acc = {}
    outcome_acc = {}
    judge_usage = {"input_tokens": 0, "output_tokens": 0, "latency_ms": 0.0}

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
                "protocol": {key: value for key, value in protocol.items() if key != "usage"},
                "outcome": {key: value for key, value in outcome.items() if key != "usage"},
            }
        )

    protocol_avg = {key: sum(values) / len(values) for key, values in protocol_acc.items()}
    outcome_avg = {key: sum(values) / len(values) for key, values in outcome_acc.items()}
    return {
        "protocol_scores": protocol_avg,
        "outcome_scores": outcome_avg,
        "protocol_mean": sum(protocol_avg.values()) / len(protocol_avg) if protocol_avg else 0,
        "quality_mean": sum(outcome_avg.values()) / len(outcome_avg) if outcome_avg else 0,
        "violations": sorted(violations),
        "turns": turns,
        "judge_usage": judge_usage,
    }


def pairwise(case, baseline, challenger):
    first, second = baseline, challenger
    flipped = random.Random(case["case_id"] + challenger["condition"]).random() < 0.5
    if flipped:
        first, second = second, first

    reference = {
        key: value
        for key, value in case["evaluator_key"].items()
        if key
        in {
            "observations",
            "not_observed",
            "plausible_hypotheses",
            "critical_first_principles",
            "discriminating_evidence",
            "decision_critical_uncertainties",
            "constraints",
            "acceptable_interventions",
            "scoring_notes",
        }
        and value
    }
    last_turn = case["turns"][-1]["turn"]
    content = {
        "case_id": case["case_id"],
        "expected_mode": case["expected_mode"],
        "reference": reference,
        "response_A": transcript(case, first, last_turn),
        "response_B": transcript(case, second, last_turn),
    }
    result = call(PAIRWISE_JUDGE, [{"role": "user", "content": json.dumps(content, ensure_ascii=False)}], JUDGE)
    parsed = parse_json(result["text"])
    winner = parsed.get("winner")
    if winner not in {"A", "B", "TIE"}:
        raise RuntimeError(f"invalid pairwise result: {parsed}")
    resolved = "TIE" if winner == "TIE" else ((first if winner == "A" else second)["condition"])
    return {
        "case_id": case["case_id"],
        "challenger": challenger["condition"],
        "winner": resolved,
        "confidence": parsed.get("confidence"),
        "notes": parsed.get("notes", ""),
        "usage": result["usage"],
    }


def main():
    output_dir = ROOT / "results"
    output_dir.mkdir(exist_ok=True)

    runs = []
    for case in CASES:
        for condition in ["BASELINE", "COMPACT", "FULL", "ADAPTIVE"]:
            print("running", case["case_id"], condition, flush=True)
            run = run_case(case, condition)
            print("evaluating", case["case_id"], condition, flush=True)
            run["evaluation"] = evaluate(case, run)
            runs.append(run)

    index = {(run["case_id"], run["condition"]): run for run in runs}
    pairs = []
    for case in CASES:
        baseline = index[(case["case_id"], "BASELINE")]
        for condition in ["COMPACT", "FULL", "ADAPTIVE"]:
            print("pairwise", case["case_id"], condition, flush=True)
            pairs.append(pairwise(case, baseline, index[(case["case_id"], condition)]))

    summary = {}
    for condition in ["BASELINE", "COMPACT", "FULL", "ADAPTIVE"]:
        condition_runs = [run for run in runs if run["condition"] == condition]
        summary[condition] = {
            "n": len(condition_runs),
            "quality_mean": sum(run["evaluation"]["quality_mean"] for run in condition_runs) / len(condition_runs),
            "protocol_mean": sum(run["evaluation"]["protocol_mean"] for run in condition_runs) / len(condition_runs),
            "input_tokens": sum(run["usage"]["input_tokens"] for run in condition_runs),
            "output_tokens": sum(run["usage"]["output_tokens"] for run in condition_runs),
            "latency_ms": sum(run["usage"]["latency_ms"] for run in condition_runs),
            "pairwise_vs_baseline": {
                "wins": sum(1 for pair in pairs if pair["challenger"] == condition and pair["winner"] == condition),
                "ties": sum(1 for pair in pairs if pair["challenger"] == condition and pair["winner"] == "TIE"),
                "losses": sum(1 for pair in pairs if pair["challenger"] == condition and pair["winner"] == "BASELINE"),
            }
            if condition != "BASELINE"
            else None,
        }

    report = {
        "target_model": TARGET,
        "judge_model": JUDGE,
        "note": "This is a six-case pilot. Treat results as plumbing and directional evidence, not framework validation.",
        "summary": summary,
        "runs": runs,
        "pairwise": pairs,
    }
    (output_dir / "pilot_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "pilot_runs.jsonl").write_text("".join(json.dumps(run, ensure_ascii=False) + "\n" for run in runs), encoding="utf-8")
    (output_dir / "pilot_pairwise.jsonl").write_text("".join(json.dumps(pair, ensure_ascii=False) + "\n" for pair in pairs), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
