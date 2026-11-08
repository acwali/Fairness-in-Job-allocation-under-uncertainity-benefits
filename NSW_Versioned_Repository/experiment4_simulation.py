from pathlib import Path
from statistics import NormalDist

import numpy as np

from experiment2_group_audit import write_csv


OUTPUT = Path("results/metrics")
SEEDS = (11, 22, 33, 44, 55)
REPEATS = 100
MINORITY_SIZES = (20, 60, 200)
FLOORS = (0.0, 100.0)
METHODS = ("Unconstrained", "Point estimate", "Lower confidence bound")

# Strata are majority-low, majority-high, minority-low, minority-high.
MASS = np.array([0.40, 0.40, 0.10, 0.10])
BASELINE = np.array([2500.0, 4500.0, 6500.0, 2000.0])
TRUE_EFFECT = np.array([200.0, 1000.0, -900.0, 1400.0])
NOISE_SD = 1800.0
CAPACITY = 0.40


def candidate_policies():
    """Vary the two minority allocation rates and fill remaining capacity."""
    candidates = []
    for minority_low in (0.0, 0.5, 1.0):
        for minority_high in (0.0, 0.5, 1.0):
            majority_high = (
                CAPACITY - 0.10 * minority_low - 0.10 * minority_high
            ) / 0.40
            candidates.append([0.0, majority_high, minority_low, minority_high])

    policies = np.array(candidates)
    np.testing.assert_allclose(policies @ MASS, CAPACITY)
    assert np.all((policies >= 0) & (policies <= 1))
    return policies


def simulate_effect_estimates(rng, minority_size):
    """Generate observations and estimate the effect within each stratum."""
    sizes = (200, 200, minority_size // 2, minority_size // 2)
    estimates = []
    standard_errors = []

    for n, baseline, effect in zip(sizes, BASELINE, TRUE_EFFECT):
        treatment = rng.permutation(np.arange(n) < n // 2)
        earnings = baseline + treatment * effect + rng.normal(0, NOISE_SD, n)
        estimates.append(earnings[treatment].mean() - earnings[~treatment].mean())

        n_treated = int(treatment.sum())
        n_control = n - n_treated
        standard_errors.append(
            NOISE_SD * np.sqrt(1 / n_treated + 1 / n_control)
        )

    return np.array(estimates), np.array(standard_errors)


def group_benefits(policies, effects):
    # Each stratum represents half of its group in the target population.
    return (policies * effects).reshape(len(policies), 2, 2).mean(axis=2)


def main():
    policies = candidate_policies()
    true_value = (policies * MASS) @ TRUE_EFFECT
    true_groups = group_benefits(policies, TRUE_EFFECT)
    zero_group = np.any(policies.reshape(len(policies), 2, 2).sum(axis=2) == 0, axis=1)

    # The capacity oracle takes all minority-high mass and 30 percentage
    # points of majority-high mass, the two strata with the greatest effects.
    capacity_oracle = 0.10 * TRUE_EFFECT[3] + 0.30 * TRUE_EFFECT[1]
    assert np.isclose(capacity_oracle, 440.0)

    fair_oracle = {
        floor: float(true_value[np.all(true_groups >= floor, axis=1)].max())
        for floor in FLOORS
    }

    # One-sided simultaneous bounds across 9 candidates and 2 groups.
    # The simulator supplies the true Gaussian noise SD.
    critical = NormalDist().inv_cdf(1 - 0.05 / (len(policies) * 2))
    runs = []

    for minority_size in MINORITY_SIZES:
        for seed in SEEDS:
            rng = np.random.default_rng(
                np.random.SeedSequence([seed, minority_size])
            )
            for replicate in range(1, REPEATS + 1):
                effect, se = simulate_effect_estimates(rng, minority_size)
                estimated_value = (policies * MASS) @ effect
                estimated_groups = group_benefits(policies, effect)
                group_se = np.sqrt(
                    ((0.5 * policies * se) ** 2)
                    .reshape(len(policies), 2, 2)
                    .sum(axis=2)
                )
                lower_bounds = estimated_groups - critical * group_se

                for floor in FLOORS:
                    eligible_by_method = (
                        np.ones(len(policies), dtype=bool),
                        np.all(estimated_groups >= floor, axis=1),
                        np.all(lower_bounds >= floor, axis=1),
                    )

                    for method, eligible in zip(METHODS, eligible_by_method):
                        feasible = np.flatnonzero(eligible)
                        chosen = (
                            int(feasible[np.argmax(estimated_value[feasible])])
                            if feasible.size else None
                        )
                        row = {
                            "minority_n": minority_size,
                            "floor": floor,
                            "seed": seed,
                            "replicate": replicate,
                            "method": method,
                            "selected": chosen is not None,
                            "candidate": "",
                            "true_value": "",
                            "true_worst_group_benefit": "",
                            "violated_true_floor": "",
                            "zero_allocation_group": "",
                            "regret_vs_capacity_oracle": "",
                            "fair_candidate_oracle_value": fair_oracle[floor],
                        }

                        if chosen is not None:
                            worst = float(true_groups[chosen].min())
                            row.update({
                                "candidate": chosen + 1,
                                "true_value": float(true_value[chosen]),
                                "true_worst_group_benefit": worst,
                                "violated_true_floor": worst < floor,
                                "zero_allocation_group": bool(zero_group[chosen]),
                                "regret_vs_capacity_oracle": (
                                    capacity_oracle - float(true_value[chosen])
                                ),
                            })

                        runs.append(row)

    summary = []
    for minority_size in MINORITY_SIZES:
        for floor in FLOORS:
            for method in METHODS:
                rows = [
                    row for row in runs
                    if row["minority_n"] == minority_size
                    and row["floor"] == floor
                    and row["method"] == method
                ]
                selected = [row for row in rows if row["selected"]]
                violations = sum(row["violated_true_floor"] for row in selected)
                zero_groups = sum(row["zero_allocation_group"] for row in selected)

                summary.append({
                    "minority_n": minority_size,
                    "floor": floor,
                    "method": method,
                    "datasets": len(rows),
                    "selected": len(selected),
                    "infeasible": len(rows) - len(selected),
                    "violations": violations,
                    "violation_pct_all_datasets": round(100 * violations / len(rows), 2),
                    "violation_pct_when_selected": (
                        round(100 * violations / len(selected), 2) if selected else ""
                    ),
                    "zero_group_pct_when_selected": (
                        round(100 * zero_groups / len(selected), 2) if selected else ""
                    ),
                    "mean_regret_when_selected": (
                        round(float(np.mean([
                            row["regret_vs_capacity_oracle"] for row in selected
                        ])), 2) if selected else ""
                    ),
                })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "simulation_runs.csv", runs)
    write_csv(OUTPUT / "simulation_summary.csv", summary)
    print(f"Capacity oracle value: {capacity_oracle:.2f}")
    print(f"Fair candidate oracle values: {fair_oracle}")
    print(f"Saved {len(runs)} run rows and {len(summary)} summary rows")


if __name__ == "__main__":
    main()