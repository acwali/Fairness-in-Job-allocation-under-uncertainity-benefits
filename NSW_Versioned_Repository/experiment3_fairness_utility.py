from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np

from experiment1_ate import load_arm
from experiment2_baselines import CAPACITIES
from experiment2_group_audit import SMALL_GROUP, group_labels, write_csv
from experiment3_comparison import TOLERANCE, load_table
from experiment3_constraints import OUTPUT, get_batch, read_scores

matplotlib.use("Agg")
import matplotlib.pyplot as plt


FIGURES = Path("results/figures")
PRIMARY_CAPACITY = 40
FOLDS = range(1, 6)


def validation_frontier():
    """Summarize the recorded validation candidates without using test outcomes."""
    grouped = defaultdict(list)
    for row in load_table("constraint_validation_candidates.csv"):
        key = (int(row["capacity_pct"]), int(row["outer_fold"]), int(row["candidate"]))
        grouped[key].append(row)

    reference = {
        (int(row["capacity_pct"]), int(row["outer_fold"])): float(row["validation_value"])
        for row in load_table("constraint_selections.csv")
        if row["method"] == "Unconstrained"
    }
    by_fold = defaultdict(list)
    for (capacity, fold, candidate), group_rows in sorted(grouped.items()):
        first = group_rows[0]
        value = float(first["validation_value"])
        loss = reference[capacity, fold] - value
        if loss < -1e-7:
            raise ValueError(f"Candidate exceeds the saved unconstrained maximum in fold {fold}")
        rates = [int(row["n_allocated"]) / int(row["n_eligible"]) for row in group_rows]
        point_ok = first["point_feasible"] == "True"
        bound_ok = first["bound_feasible"] == "True"
        by_fold[capacity, fold].append({
            "capacity_pct": capacity,
            "outer_fold": fold,
            "candidate": candidate,
            "feature": first["feature"],
            "threshold": first["threshold"],
            "preferred_leaf": first["preferred_leaf"],
            "validation_value": value,
            "validation_utility_loss": max(0.0, loss),
            "worst_race_group_benefit": min(float(row["group_benefit"]) for row in group_rows),
            "worst_race_group_lcb": min(float(row["group_lower_bound"]) for row in group_rows),
            "race_allocation_gap_pp": 100 * (max(rates) - min(rates)),
            "smallest_race_group_n": min(int(row["n_eligible"]) for row in group_rows),
            "point_feasible": point_ok,
            "lcb_feasible": bound_ok,
            "within_utility_tolerance": loss <= TOLERANCE,
            "pareto_frontier": False,
        })

    expected = {(capacity, fold) for capacity in CAPACITIES for fold in FOLDS}
    if set(by_fold) != expected:
        raise ValueError("Missing capacity or fold in the candidate diagnostics.")

    for rows in by_fold.values():
        # At tied utility, inspect the best fairness first.
        ordered = sorted(
            rows,
            key=lambda row: (row["validation_utility_loss"], -row["worst_race_group_benefit"]),
        )
        best = -np.inf
        for row in ordered:
            benefit = row["worst_race_group_benefit"]
            if benefit > best:
                row["pareto_frontier"] = True
                best = benefit

    return by_fold


def matched_summary(by_fold):
    audit = {
        (int(row["capacity_pct"]), int(row["outer_fold"]), row["method"]): row
        for row in load_table("constraint_matched_utility_audit.csv")
    }
    summary = []
    for capacity in CAPACITIES:
        for method, field in (("Point estimate", "point_feasible"), ("Lower confidence bound", "lcb_feasible")):
            feasible_folds = 0
            matched_folds = 0
            for fold in FOLDS:
                feasible = [row for row in by_fold[capacity, fold] if row[field]]
                matched = [row for row in feasible if row["within_utility_tolerance"]]
                saved = audit[capacity, fold, method]
                if (len(feasible), len(matched)) != (
                    int(saved["feasible_candidates"]), int(saved["matched_candidates"]),
                ):
                    raise ValueError(f"Matched-utility audit disagrees at {capacity}% in fold {fold}")
                feasible_folds += bool(feasible)
                matched_folds += bool(matched)
            summary.append({
                "capacity_pct": capacity,
                "method": method,
                "validation_tolerance": TOLERANCE,
                "folds": len(FOLDS),
                "folds_with_feasible_candidate": feasible_folds,
                "folds_with_utility_match": matched_folds,
            })
    return summary


def kish_ess(weights):
    denominator = np.dot(weights, weights)
    return float(weights.sum() ** 2 / denominator) if denominator > 0 else 0.0


def subgroup_support():
    raw = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    treatment = raw[:, 0] == 1
    propensity = treatment.mean()
    test = read_scores("outer_test_scores.csv")
    if not all(np.isclose(float(row["propensity"]), propensity) for row in test):
        raise ValueError("Saved propensity differs from the experimental assignment fraction.")
    validation = read_scores("development_validation_scores.csv")
    test_batches = [get_batch(test, fold, "outer_test")[0] for fold in FOLDS]
    np.testing.assert_array_equal(np.sort(np.concatenate(test_batches)), np.arange(len(raw)))

    partitions = [("Outer test pooled", "All", np.arange(len(raw)))]
    for fold, test_ids in zip(FOLDS, test_batches):
        validation_ids = get_batch(validation, fold, "validation")[0]
        if len(np.unique(validation_ids)) != 89 or np.intersect1d(validation_ids, test_ids).size:
            raise ValueError(f"Invalid validation membership in fold {fold}")
        partitions.extend((("Validation", fold, validation_ids), ("Outer test", fold, test_ids)))

    race, age, intersection = group_labels(raw)
    rows = []
    for role, fold, ids in partitions:
        for audit, labels in (("race", race), ("age", age), ("race_by_age", intersection)):
            for label in np.unique(labels):
                group_ids = ids[labels[ids] == label]
                treated = treatment[group_ids]
                weights = np.where(treated, 1 / propensity, 1 / (1 - propensity))
                n_treated = int(treated.sum())
                n_control = len(group_ids) - n_treated
                treated_ess = kish_ess(weights[treated])
                control_ess = kish_ess(weights[~treated])
                np.testing.assert_allclose([treated_ess, control_ess], [n_treated, n_control])
                rows.append({
                    "sample": role, "outer_fold": fold, "audit": audit, "group": label,
                    "n": len(group_ids), "n_treated": n_treated, "n_control": n_control,
                    "treated_ipw_ess": round(treated_ess, 2),
                    "control_ipw_ess": round(control_ess, 2),
                    "combined_ipw_ess": round(kish_ess(weights), 2),
                    "n_lt_30": len(group_ids) < SMALL_GROUP,
                    "either_arm_ess_lt_30": min(treated_ess, control_ess) + 1e-9 < SMALL_GROUP,
                })
    return rows


def plot_frontier(by_fold):
    figure, axes = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
    style = (
        ("Fails point floor", "#8b93a1", "x", lambda row: not row["point_feasible"]),
        ("Passes point floor only", "#007f8b", "o", lambda row: row["point_feasible"] and not row["lcb_feasible"]),
        ("Passes lower-bound floor", "#aa541b", "D", lambda row: row["lcb_feasible"]),
    )
    legend = []
    for fold, axis in zip(FOLDS, axes.flat):
        rows = by_fold[PRIMARY_CAPACITY, fold]
        axis.axvspan(0, TOLERANCE, color="#e1f1ec", label="Within 200-unit tolerance")
        axis.axhline(0, color="#78818d", linewidth=1, linestyle=":")
        frontier = sorted(
            (row for row in rows if row["pareto_frontier"]),
            key=lambda row: row["validation_utility_loss"],
        )
        line, = axis.plot(
            [row["validation_utility_loss"] for row in frontier],
            [row["worst_race_group_benefit"] for row in frontier],
            color="#233349", linewidth=1.4, label="Non-dominated candidates", zorder=2,
        )
        handles = []
        for label, color, marker, matches in style:
            candidates = [row for row in rows if matches(row)]
            handles.append(axis.scatter(
                [row["validation_utility_loss"] for row in candidates],
                [row["worst_race_group_benefit"] for row in candidates],
                color=color, marker=marker, s=38, label=label, zorder=3,
            ))
        if not legend:
            legend = [axis.patches[0], line, *handles]
        axis.set_title(f"Validation fold {fold}", loc="left", fontweight="bold")
        axis.set_axisbelow(True)
        axis.grid(alpha=0.17)
        axis.spines[["top", "right"]].set_visible(False)

    panel = axes.flat[-1]
    panel.axis("off")
    panel.legend(handles=legend, loc="upper left", frameon=False, fontsize=10)
    panel.text(0.04, 0.34, "Higher group benefit is preferable.\n"
               "Lower utility loss is preferable.\n\n"
               "Each point is a candidate evaluated\n"
               "on its own validation fold.",
               transform=panel.transAxes, va="top", color="#233349")
    figure.suptitle("Validation fairness–utility frontier at 40% target capacity", fontweight="bold")
    figure.supxlabel("Validation utility loss relative to the unconstrained maximum")
    figure.supylabel("Minimum estimated race-group earnings benefit")
    FIGURES.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "png"):
        figure.savefig(FIGURES / f"fairness_utility_frontier_40pct.{extension}", dpi=200)
    plt.close(figure)


def main():
    frontier = validation_frontier()
    summary = matched_summary(frontier)
    support = subgroup_support()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "fairness_utility_frontier.csv", [row for rows in frontier.values() for row in rows])
    write_csv(OUTPUT / "fairness_utility_matched_summary.csv", summary)
    write_csv(OUTPUT / "nsw_subgroup_ess.csv", support)
    plot_frontier(frontier)
    print(f"Verified matched-utility counts for {len(summary)} capacity-by-method comparisons.")
    print(f"Saved {len(support)} real-data subgroup support rows and the 40% frontier figure.")


if __name__ == "__main__":
    main()

