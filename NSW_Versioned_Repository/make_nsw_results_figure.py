import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


METRICS = Path("results/metrics")
OUTPUT = Path("results/figures")
CAPACITIES = (20, 40, 60)

BASELINES = {
    "Random allocation": ("Random allocation", "#666666", "o"),
    "Predicted post-training earnings": ("Predicted earnings", "#C06B25", "s"),
    "Estimated treatment benefit": ("Estimated benefit", "#007D82", "^"),
}

METHODS = {
    "Unconstrained": ("Unconstrained", "#45658C"),
    "Point estimate": ("Point-estimate constraint", "#C06B25"),
    "Lower confidence bound": ("Lower-bound constraint", "#8A4F7D"),
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def style_axis(axis, title, ylabel):
    axis.set_title(title, loc="left", fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.set_axisbelow(True)
    axis.grid(axis="y", alpha=0.25)
    axis.spines[["top", "right"]].set_visible(False)


def main():
    baseline = {
        (int(row["capacity_pct"]), row["policy"]): row
        for row in read_csv(METRICS / "baseline_policy_values.csv")
    }
    constraints = {
        (int(row["capacity_pct"]), row["method"]): row
        for row in read_csv(METRICS / "constraint_outer_summary.csv")
    }
    race_groups = [
        row for row in read_csv(METRICS / "policy_group_metrics.csv")
        if row["capacity_pct"] == "40"
        and row["policy"] == "Equal race allocation rate"
        and row["audit"] == "race"
    ]
    refits = {
        row["method"]: row
        for row in read_csv(METRICS / "refitting/refitting_summary.csv")
    }

    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), layout="constrained")
    fig.suptitle("Job-training allocation in the NSW experiment", fontweight="bold")

    # A. Overall value for the capacity-matched baseline policies.
    ax = axes[0, 0]
    for policy, (label, color, marker) in BASELINES.items():
        values = [
            float(baseline[capacity, policy]["value_per_eligible"])
            for capacity in CAPACITIES
        ]
        ax.plot(CAPACITIES, values, marker=marker, color=color, label=label)

    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    ax.set_xticks(CAPACITIES)
    ax.set_xlabel("Target capacity (%)")
    style_axis(ax, "A. Baseline policy value", "Earnings gain per eligible participant")
    ax.legend(frameon=False, fontsize=9)

    # B. Number of folds where a constrained policy could be selected.
    ax = axes[0, 1]
    positions = np.arange(len(CAPACITIES))
    for offset, (method, (label, color)) in zip((-0.24, 0, 0.24), METHODS.items()):
        counts = [
            int(constraints[capacity, method]["folds_with_policy"])
            for capacity in CAPACITIES
        ]
        bars = ax.bar(positions + offset, counts, width=0.22, color=color, label=label)
        ax.bar_label(bars, padding=3, fontsize=9)

    ax.set_xticks(positions, [f"{capacity}%" for capacity in CAPACITIES])
    ax.set_xlabel("Target capacity")
    ax.set_ylim(0, 6)
    ax.set_yticks(range(6))
    style_axis(ax, "B. Feasibility by capacity", "Outer folds with a selected policy")
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    # C. Point estimates and fixed-policy bootstrap intervals by race group.
    ax = axes[1, 0]
    positions = np.arange(len(race_groups))
    for position, row in zip(positions, race_groups):
        estimate = float(row["incremental_benefit_per_eligible"])
        lower = float(row["benefit_ci95_lower"])
        upper = float(row["benefit_ci95_upper"])
        ax.vlines(position, lower, upper, color="#007D82", linewidth=2)
        ax.scatter(position, estimate, color="#007D82", zorder=3)

    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    labels = [
        f"{row['group'].replace('Neither indicator recorded', 'Neither indicator')}"
        f"\n(n={row['n_eligible']})"
        for row in race_groups
    ]
    ax.set_xticks(positions, labels, fontsize=9)
    style_axis(
        ax,
        "C. Race-group benefit under equal-rate allocation (40%)",
        "Earnings gain per eligible group member",
    )

    # D. Feasibility after resampling the development data.
    ax = axes[1, 1]
    labels = ["Unconstrained", "Point estimate", "Lower bound"]
    percentages = [float(refits[method]["feasibility_pct"]) for method in METHODS]
    colors = [color for _, color in METHODS.values()]
    bars = ax.bar(labels, percentages, color=colors, width=0.65)
    ax.bar_label(bars, labels=[f"{p:.1f}%" for p in percentages], padding=3)
    ax.set_ylim(0, 112)
    ax.set_yticks(np.arange(0, 101, 20))
    style_axis(ax, "D. Feasibility after refitting (40%)", "Feasible fold refits (%)")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / "nsw_main_results.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT / "nsw_main_results.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved nsw_main_results.png and nsw_main_results.pdf in {OUTPUT}")


if __name__ == "__main__":
    main()