#!/usr/bin/env python3
"""Generate manuscript figures from frozen published-result values.

This script performs no new inference. Values are copied from the authoritative
repository result documents and paper/TABLES_AND_FIGURES_V1.md.
"""
from pathlib import Path

import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)


def save(fig, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fresh_suite() -> None:
    labels = ["Held-out v1", "Routing v1", "Routing v2", "Routing v3"]
    est = [0.6898, 0.6771, 0.6875, 0.6539]
    low = [0.6096, 0.6250, 0.6273, 0.5891]
    high = [0.7685, 0.7292, 0.7477, 0.7199]
    y = list(range(len(labels)))
    xerr = [[e - l for e, l in zip(est, low)], [h - e for e, h in zip(est, high)]]

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.errorbar(est, y, xerr=xerr, fmt="o", capsize=4)
    ax.axvline(0.5, linestyle="--", linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0.45, 0.82)
    ax.set_xlabel("FULL vs CONTROL pairwise score")
    ax.set_title("Fresh-suite FULL vs CONTROL results")
    save(fig, "fresh_suite_full_vs_control")


def heterogeneity() -> None:
    labels = ["ENGINEER", "TEST", "BOTH", "NONE", "Action-required", "No-action"]
    est = [0.9012, 0.7901, 0.6296, 0.4861, 0.7375, 0.4921]
    low = [0.8025, 0.6790, 0.4074, 0.4074, 0.6437, 0.4127]
    high = [0.9753, 0.9012, 0.8519, 0.5556, 0.8238, 0.5796]
    y = list(range(len(labels)))
    xerr = [[e - l for e, l in zip(est, low)], [h - e for e, h in zip(est, high)]]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(est, y, xerr=xerr, fmt="o", capsize=4)
    ax.axvline(0.5, linestyle="--", linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0.35, 1.02)
    ax.set_xlabel("FULL vs CONTROL pairwise score")
    ax.set_title("Primary held-out heterogeneity")
    save(fig, "heldout_heterogeneity")


def routing() -> None:
    labels = ["Routing v1", "Routing v2", "Routing v3", "v4 DIRECT_BYPASS*", "v4 NB_DIRECT LOSO*"]
    full_rate = [0.50, 0.7083, 0.1042, 0.6944, 0.5625]
    score = [0.6620, 0.6840, 0.4988, 0.6512, 0.6393]

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.scatter(full_rate, score)
    for x, y, label in zip(full_rate, score, labels):
        ax.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.axvline(0.65, linestyle="--", linewidth=1)
    ax.axhline(0.5, linestyle="--", linewidth=1)
    ax.set_xlim(0.0, 0.82)
    ax.set_ylim(0.46, 0.71)
    ax.set_xlabel("FULL invocation rate")
    ax.set_ylabel("ROUTED vs CONTROL score")
    ax.set_title("Routing quality/selectivity trajectory")
    ax.text(0.02, 0.465, "* v4 points are exposed-data development, not validation", fontsize=8)
    save(fig, "routing_quality_selectivity")


def main() -> None:
    fresh_suite()
    heterogeneity()
    routing()
    print(f"Wrote figures to {OUT}")


if __name__ == "__main__":
    main()
