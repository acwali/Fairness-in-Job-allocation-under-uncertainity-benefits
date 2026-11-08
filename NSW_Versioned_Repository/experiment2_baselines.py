import csv
from pathlib import Path

import numpy as np


SCORES = Path("results/experiment2/outer_test_scores.csv")
OUTPUT = Path("results/metrics/baseline_policy_values.csv")
CAPACITIES = (20, 40, 60)
LOTTERY_SEEDS = (11, 22, 33, 44, 55)
BOOTSTRAP_SEED = 2026
N_BOOTSTRAP = 2_000


def top_k(scores, participant_ids, slots):
    """Rank by decreasing score, breaking ties by participant ID."""
    order = np.lexsort((participant_ids, -scores))
    return order[:slots]


def allocation_values(selected, dr_scores):
    """Return one incremental-value contribution per eligible participant."""
    values = np.zeros(len(dr_scores))
    values[selected] = dr_scores[selected]
    return values


def main():
    with SCORES.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    ids = np.array([int(row["participant_id"]) for row in rows])
    folds = np.array([int(row["outer_fold"]) for row in rows])
    m1 = np.array([float(row["m1"]) for row in rows])
    benefit = np.array([float(row["estimated_benefit"]) for row in rows])
    dr_scores = np.array([float(row["dr_score"]) for row in rows])

    if not np.array_equal(np.sort(ids), np.arange(445)):
        raise ValueError("Expected each of the 445 participants exactly once")
    if not np.array_equal(np.unique(folds), np.arange(1, 6)):
        raise ValueError("Expected outer folds 1 through 5")
    if not np.isfinite(np.column_stack((m1, benefit, dr_scores))).all():
        raise ValueError("Non-finite scores found")

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    # Use the same participant draws for every policy and capacity.
    bootstrap_ids = rng.integers(
        0, len(ids), size=(N_BOOTSTRAP, len(ids))
    )

    results = []
    for capacity in CAPACITIES:
        earnings_values = np.zeros(len(ids))
        benefit_values = np.zeros(len(ids))
        random_values = np.zeros((len(LOTTERY_SEEDS), len(ids)))
        total_slots = 0

        for fold in range(1, 6):
            batch = np.flatnonzero(folds == fold)
            if len(batch) != 89:
                raise ValueError(f"Fold {fold}: expected 89 participants")

            slots = capacity * len(batch) // 100
            total_slots += slots

            earnings_selected = top_k(m1[batch], ids[batch], slots)
            benefit_selected = top_k(benefit[batch], ids[batch], slots)

            earnings_values[batch] = allocation_values(
                earnings_selected, dr_scores[batch]
            )
            benefit_values[batch] = allocation_values(
                benefit_selected, dr_scores[batch]
            )

            for i, seed in enumerate(LOTTERY_SEEDS):
                lottery = np.random.default_rng(
                    np.random.SeedSequence([seed, fold])
                )
                selected = lottery.permutation(len(batch))[:slots]
                random_values[i, batch] = allocation_values(
                    selected, dr_scores[batch]
                )

        random_average = random_values.mean(axis=0)
        policies = (
            ("Random allocation", random_average),
            ("Predicted post-training earnings", earnings_values),
            ("Estimated treatment benefit", benefit_values),
        )

        for name, values in policies:
            difference = values - random_average
            lower, upper = np.percentile(
                difference[bootstrap_ids].mean(axis=1), [2.5, 97.5]
            )
            results.append({
                "capacity_pct": capacity,
                "policy": name,
                "participants": len(ids),
                "places_allocated": total_slots,
                "realized_allocation_pct": round(100 * total_slots / len(ids), 2),
                "value_per_eligible": round(values.mean(), 2),
                "gain_vs_random": round(difference.mean(), 2),
                "gain_ci95_lower": round(float(lower), 2),
                "gain_ci95_upper": round(float(upper), 2),
            })

        # Required head-to-head comparison, using the same participants.
        paired = benefit_values - earnings_values
        lower, upper = np.percentile(
            paired[bootstrap_ids].mean(axis=1), [2.5, 97.5]
        )
        print(
            f"{capacity}% capacity | benefit ranking minus earnings ranking: "
            f"{paired.mean():,.2f} [95% CI {lower:,.2f}, {upper:,.2f}]"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()