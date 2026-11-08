import ast
import csv
from pathlib import Path

import numpy as np

from experiment1_ate import load_arm
from experiment2_baselines import CAPACITIES, LOTTERY_SEEDS, SCORES, top_k
from experiment2_group_audit import equal_rate_selected, group_labels, write_csv
from experiment3_constraints import METHODS, TIE_SEED, allocate


OUTPUT = Path("results/metrics")
MIN_DENOMINATOR = 30
BASELINES = (
    "Random allocation",
    "Predicted post-training earnings",
    "Estimated treatment benefit",
    "Equal race allocation rate",
)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_allocations(raw, ids, folds, race, m1, benefit, capacity, selections):
    complete_methods = [
        method for method in METHODS
        if all(selections[capacity, fold, method]["status"] == "selected"
               for fold in range(1, 6))
    ]
    allocations = {
        name: np.zeros(len(ids))
        for name in (*BASELINES, *complete_methods)
    }
    tie_priority = np.random.default_rng(TIE_SEED).permutation(len(raw))
    total_slots = 0

    for fold in range(1, 6):
        batch = np.flatnonzero(folds == fold)
        if len(batch) != 89:
            raise ValueError(f"Fold {fold}: expected 89 test participants")

        slots = capacity * len(batch) // 100
        total_slots += slots
        ranked = {
            "Predicted post-training earnings": top_k(
                m1[batch], ids[batch], slots
            ),
            "Estimated treatment benefit": top_k(
                benefit[batch], ids[batch], slots
            ),
            "Equal race allocation rate": equal_rate_selected(
                race[batch], benefit[batch], ids[batch], slots
            ),
        }
        for name, selected in ranked.items():
            allocations[name][batch[selected]] = 1

        for seed in LOTTERY_SEEDS:
            rng = np.random.default_rng(np.random.SeedSequence([seed, fold]))
            selected = rng.permutation(len(batch))[:slots]
            allocations["Random allocation"][batch[selected]] += (
                1 / len(LOTTERY_SEEDS)
            )

        for method in complete_methods:
            rule = ast.literal_eval(selections[capacity, fold, method]["rule"])
            allocations[method][batch] = allocate(
                rule, raw, ids[batch], slots, tie_priority
            )

    for policy, decision in allocations.items():
        if not np.isclose(decision.sum(), total_slots):
            raise ValueError(f"{policy}: allocation count does not match capacity")

    return allocations


def calculate_rate(decision, mask):
    return float(decision[mask].mean()) if mask.any() else None


def gap_pp(rates):
    defined = [rate for rate in rates if rate is not None]
    if len(defined) < 2:
        return None
    return round(100 * (max(defined) - min(defined)), 2)


def main():
    raw = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    scores = read_csv(SCORES)
    ids = np.array([int(row["participant_id"]) for row in scores])
    folds = np.array([int(row["outer_fold"]) for row in scores])
    m1 = np.array([float(row["m1"]) for row in scores])
    benefit = np.array([float(row["estimated_benefit"]) for row in scores])

    if not np.array_equal(np.sort(ids), np.arange(len(raw))):
        raise ValueError("Expected each of the 445 participants exactly once")
    if not np.array_equal(np.unique(folds), np.arange(1, 6)):
        raise ValueError("Expected outer folds 1 through 5")

    race, age, intersection = group_labels(raw[ids])
    historical_treatment = raw[ids, 0]
    positive_earnings = raw[ids, 9] > 0
    audits = (("race", race), ("age", age), ("race_by_age", intersection))

    selections = {
        (int(row["capacity_pct"]), int(row["outer_fold"]), row["method"]): row
        for row in read_csv(OUTPUT / "constraint_selections.csv")
    }

    group_rows = []
    summary_rows = []
    coverage_rows = []

    for capacity in CAPACITIES:
        allocations = build_allocations(
            raw, ids, folds, race, m1, benefit, capacity, selections
        )

        for policy in (*BASELINES, *METHODS):
            selected_folds = 5 if policy in BASELINES else sum(
                selections[capacity, fold, policy]["status"] == "selected"
                for fold in range(1, 6)
            )
            coverage_rows.append({
                "capacity_pct": capacity,
                "policy": policy,
                "folds_with_policy": selected_folds,
                "included_in_audit": policy in allocations,
            })

        for policy, decision in allocations.items():
            for arm, arm_name in ((0, "Control"), (1, "Treated")):
                in_arm = historical_treatment == arm

                for audit, groups in audits:
                    tprs = []
                    fprs = []
                    low_support = False

                    for label in np.unique(groups):
                        members = in_arm & (groups == label)
                        positive = members & positive_earnings
                        negative = members & ~positive_earnings
                        n_positive = int(positive.sum())
                        n_negative = int(negative.sum())
                        tpr = calculate_rate(decision, positive)
                        fpr = calculate_rate(decision, negative)
                        small_positive = n_positive < MIN_DENOMINATOR
                        small_negative = n_negative < MIN_DENOMINATOR

                        tprs.append(tpr)
                        fprs.append(fpr)
                        low_support |= small_positive or small_negative

                        group_rows.append({
                            "capacity_pct": capacity,
                            "policy": policy,
                            "historical_arm": arm_name,
                            "audit": audit,
                            "group": label,
                            "n_eligible": int(members.sum()),
                            "n_positive": n_positive,
                            "n_negative": n_negative,
                            "tpr_pct": round(100 * tpr, 2) if tpr is not None else "",
                            "fpr_pct": round(100 * fpr, 2) if fpr is not None else "",
                            "tpr_exploratory": small_positive,
                            "fpr_exploratory": small_negative,
                        })

                    tpr_gap = gap_pp(tprs)
                    fpr_gap = gap_pp(fprs)
                    eo_gap = (
                        max(tpr_gap, fpr_gap)
                        if tpr_gap is not None and fpr_gap is not None
                        else ""
                    )

                    summary_rows.append({
                        "capacity_pct": capacity,
                        "policy": policy,
                        "historical_arm": arm_name,
                        "audit": audit,
                        "equality_of_opportunity_gap_pp": tpr_gap,
                        "fpr_gap_pp": fpr_gap,
                        "equalized_odds_gap_pp": eo_gap,
                        "groups_with_defined_tpr": sum(rate is not None for rate in tprs),
                        "groups_with_defined_fpr": sum(rate is not None for rate in fprs),
                        "has_low_support_denominator": low_support,
                    })

    write_csv(OUTPUT / "outcome_fairness_groups.csv", group_rows)
    write_csv(OUTPUT / "outcome_fairness_summary.csv", summary_rows)
    write_csv(OUTPUT / "outcome_fairness_coverage.csv", coverage_rows)
    print(
        f"Saved {len(group_rows)} group rows, {len(summary_rows)} summary rows, "
        f"and {len(coverage_rows)} coverage rows"
    )


if __name__ == "__main__":
    main()