import csv
from pathlib import Path

import numpy as np

from experiment1_ate import load_arm
from experiment2_baselines import (
    BOOTSTRAP_SEED, CAPACITIES, LOTTERY_SEEDS, N_BOOTSTRAP, SCORES, top_k,
)


OUTPUT = Path("results/metrics")
SMALL_GROUP = 30


def equal_rate_selected(groups, benefits, ids, slots):
    """Assign proportional quotas, then fill them by estimated benefit."""
    labels, counts = np.unique(groups, return_counts=True)
    numerator = slots * counts
    quotas, remainders = np.divmod(numerator, len(groups))

    # Largest remainders get the remaining places. Group label breaks ties.
    priority = np.lexsort((labels, -remainders))
    quotas[priority[:slots - quotas.sum()]] += 1

    selected = []
    for label, quota in zip(labels, quotas):
        members = np.flatnonzero(groups == label)
        ranked = top_k(benefits[members], ids[members], int(quota))
        selected.extend(members[ranked])

    assert len(selected) == slots
    return np.array(selected, dtype=int)


def group_labels(data):
    black = data[:, 3] == 1
    hispanic = data[:, 4] == 1
    if np.any(black & hispanic):
        raise ValueError("Review overlapping race indicators before grouping")

    race = np.select(
        [black, hispanic],
        ["Black", "Hispanic"],
        default="Neither indicator recorded",
    )
    age = np.where(data[:, 1] < 25, "Under 25", "25 and over")
    intersection = np.array([
        f"{race_label} / {age_label}"
        for race_label, age_label in zip(race, age)
    ])
    return race, age, intersection


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    with SCORES.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    ids = np.array([int(row["participant_id"]) for row in rows])
    folds = np.array([int(row["outer_fold"]) for row in rows])
    m1 = np.array([float(row["m1"]) for row in rows])
    benefit = np.array([float(row["estimated_benefit"]) for row in rows])
    dr = np.array([float(row["dr_score"]) for row in rows])

    raw = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    if not np.array_equal(np.sort(ids), np.arange(len(raw))):
        raise ValueError("Expected every participant exactly once")
    if not np.array_equal(np.unique(folds), np.arange(1, 6)):
        raise ValueError("Expected outer folds 1 through 5")

    race, age, intersection = group_labels(raw[ids])
    audits = (
        ("race", race),
        ("age", age),
        ("race_by_age", intersection),
    )

    # Reuse participant bootstrap draws across all policies and capacities.
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.integers(0, len(ids), size=(N_BOOTSTRAP, len(ids)))
    group_rows = []
    summary_rows = []

    for capacity in CAPACITIES:
        allocations = {
            "Random allocation": np.zeros(len(ids)),
            "Predicted post-training earnings": np.zeros(len(ids)),
            "Estimated treatment benefit": np.zeros(len(ids)),
            "Equal race allocation rate": np.zeros(len(ids)),
        }
        total_slots = 0

        for fold in range(1, 6):
            batch = np.flatnonzero(folds == fold)
            if len(batch) != 89:
                raise ValueError(f"Fold {fold}: expected 89 participants")
            slots = capacity * len(batch) // 100
            total_slots += slots

            earnings_selected = top_k(m1[batch], ids[batch], slots)
            benefit_selected = top_k(benefit[batch], ids[batch], slots)
            equal_selected = equal_rate_selected(
                race[batch], benefit[batch], ids[batch], slots
            )

            allocations["Predicted post-training earnings"][
                batch[earnings_selected]
            ] = 1
            allocations["Estimated treatment benefit"][batch[benefit_selected]] = 1
            allocations["Equal race allocation rate"][batch[equal_selected]] = 1

            for seed in LOTTERY_SEEDS:
                lottery = np.random.default_rng(
                    np.random.SeedSequence([seed, fold])
                )
                selected = lottery.permutation(len(batch))[:slots]
                allocations["Random allocation"][batch[selected]] += (
                    1 / len(LOTTERY_SEEDS)
                )

        for policy, allocation in allocations.items():
            assert np.isclose(allocation.sum(), total_slots)
            contribution = allocation * dr

            for audit, labels in audits:
                rates = []
                benefits = []

                for group in np.unique(labels):
                    members = labels == group
                    count = int(members.sum())
                    group_rate = float(allocation[members].mean())
                    group_benefit = float(contribution[members].mean())

                    drawn_members = members[draws]
                    denominator = drawn_members.sum(axis=1)
                    numerator = (contribution[draws] * drawn_members).sum(axis=1)
                    valid = denominator > 0
                    lower, upper = np.percentile(
                        numerator[valid] / denominator[valid], [2.5, 97.5]
                    )

                    rates.append(group_rate)
                    benefits.append(group_benefit)
                    group_rows.append({
                        "capacity_pct": capacity,
                        "policy": policy,
                        "audit": audit,
                        "group": group,
                        "n_eligible": count,
                        "exploratory_n_lt_30": count < SMALL_GROUP,
                        "allocated_mean_over_seeds": round(allocation[members].sum(), 2),
                        "allocation_pct": round(100 * group_rate, 2),
                        "incremental_benefit_per_eligible": round(group_benefit, 2),
                        "benefit_ci95_lower": round(float(lower), 2),
                        "benefit_ci95_upper": round(float(upper), 2),
                        "valid_bootstrap_replicates": int(valid.sum()),
                    })

                summary_rows.append({
                    "capacity_pct": capacity,
                    "policy": policy,
                    "audit": audit,
                    "places_allocated": total_slots,
                    "value_per_eligible": round(float(contribution.mean()), 2),
                    "allocation_gap_pp": round(100 * (max(rates) - min(rates)), 2),
                    "selection_rate_ratio": (
                        round(min(rates) / max(rates), 4)
                        if max(rates) > 0 else "undefined"
                    ),
                    "minimum_group_benefit": round(min(benefits), 2),
                    "group_benefit_range": round(max(benefits) - min(benefits), 2),
                })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "policy_group_metrics.csv", group_rows)
    write_csv(OUTPUT / "policy_fairness_summary.csv", summary_rows)
    print(f"Saved {len(group_rows)} group rows and {len(summary_rows)} summary rows")


if __name__ == "__main__":
    main()