from itertools import product
from pathlib import Path

import numpy as np

from experiment2_group_audit import write_csv


OUTPUT = Path("results/metrics")
SEEDS = (11, 22, 33, 44, 55)
REPEATS = 100
N = 800
CLIPS = (0.0, 0.01, 0.025, 0.05)

# Scenario name, effect of X on assignment, effect of hidden U on assignment.
SCENARIOS = (
    ("Good overlap", 0.5, 0.0),
    ("Moderate overlap", 1.5, 0.0),
    ("Weak overlap", 3.0, 0.0),
    ("Moderate overlap + mild hidden confounding", 1.5, 0.6),
    ("Moderate overlap + strong hidden confounding", 1.5, 1.2),
)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def effective_n(weights):
    total = weights.sum()
    return float(total**2 / np.sum(weights**2)) if total > 0 else np.nan


def standardized_gap(x, treated_weights, control_weights):
    treated_mean = np.average(x, weights=treated_weights)
    control_mean = np.average(x, weights=control_weights)
    return float((treated_mean - control_mean) / x.std(ddof=1))


def simulate(rng, overlap_strength, hidden_strength):
    x = rng.normal(size=N)
    group = rng.binomial(1, 0.25, size=N)
    hidden = rng.choice([-1.0, 1.0], size=N)

    logit = overlap_strength * x + 0.6 * group
    oracle_p = sigmoid(logit + hidden_strength * hidden)

    # U is equally likely to be -1 or +1 independently of X and group.
    # Marginalizing over U gives the exact observed-covariate propensity.
    observed_p = (
        sigmoid(logit - hidden_strength) + sigmoid(logit + hidden_strength)
    ) / 2

    treatment = rng.random(N) < oracle_p
    effect = 900.0 + 400.0 * x
    no_training = (
        4000.0 + 1000.0 * x + 350.0 * group
        + 1100.0 * hidden + rng.normal(0, 1200, N)
    )
    earnings = no_training + treatment * effect

    # Fixed policy: allocate to the top 40% by the baseline covariate X.
    # Its decisions are set without using observed earnings or assignment.
    selected = np.zeros(N, dtype=bool)
    selected[np.argsort(x)[-(40 * N // 100):]] = True

    return x, group, treatment, earnings, effect, selected, observed_p, oracle_p


def main():
    runs = []

    for scenario_id, (scenario, overlap, hidden) in enumerate(SCENARIOS):
        for seed in SEEDS:
            rng = np.random.default_rng(
                np.random.SeedSequence([seed, scenario_id])
            )

            for replicate in range(1, REPEATS + 1):
                x, g, t, y, effect, decision, observed_p, oracle_p = simulate(
                    rng, overlap, hidden
                )
                true_ate = float(effect.mean())
                true_value = float((decision * effect).mean())
                unweighted_gap = standardized_gap(x, t, ~t)

                for estimator, propensity in (
                    ("Observed covariates", observed_p),
                    ("Oracle with hidden variable", oracle_p),
                ):
                    for clip in CLIPS:
                        p = np.clip(propensity, clip, 1 - clip)
                        w1 = t / p
                        w0 = (~t) / (1 - p)

                        # Normalized IPW (Hájek), with the same target
                        # population denominator for policy value.
                        ate = np.average(y, weights=w1) - np.average(y, weights=w0)
                        value = (
                            np.average(decision * y, weights=w1)
                            - np.average(decision * y, weights=w0)
                        )

                        runs.append({
                            "scenario": scenario,
                            "estimator": estimator,
                            "clip": clip,
                            "seed": seed,
                            "replicate": replicate,
                            "true_ate": true_ate,
                            "estimated_ate": float(ate),
                            "ate_error": float(ate - true_ate),
                            "true_policy_value": true_value,
                            "estimated_policy_value": float(value),
                            "policy_value_error": float(value - true_value),
                            "propensity_outside_05_95_pct": float(
                                100 * ((propensity < 0.05) | (propensity > 0.95)).mean()
                            ),
                            "n_clipped": int(np.count_nonzero(p != propensity)),
                            "max_realized_weight": float(max(w1.max(), w0.max())),
                            "treated_ess": effective_n(w1),
                            "control_ess": effective_n(w0),
                            "majority_treated_ess": effective_n(w1[g == 0]),
                            "majority_control_ess": effective_n(w0[g == 0]),
                            "minority_treated_ess": effective_n(w1[g == 1]),
                            "minority_control_ess": effective_n(w0[g == 1]),
                            "abs_x_smd_before": abs(unweighted_gap),
                            "abs_x_smd_after": abs(standardized_gap(x, w1, w0)),
                        })

    summary = []
    scenarios = [scenario for scenario, _, _ in SCENARIOS]
    estimators = ("Observed covariates", "Oracle with hidden variable")

    for scenario, estimator, clip in product(scenarios, estimators, CLIPS):
        rows = [
            row for row in runs
            if row["scenario"] == scenario
            and row["estimator"] == estimator
            and row["clip"] == clip
        ]
        ate_error = np.array([row["ate_error"] for row in rows])
        value_error = np.array([row["policy_value_error"] for row in rows])

        summary_row = {
            "scenario": scenario,
            "estimator": estimator,
            "clip": clip,
            "datasets": len(rows),
            "ate_bias": round(float(ate_error.mean()), 2),
            "ate_rmse": round(float(np.sqrt(np.mean(ate_error**2))), 2),
            "policy_value_bias": round(float(value_error.mean()), 2),
            "policy_value_rmse": round(float(np.sqrt(np.mean(value_error**2))), 2),
        }

        for field in (
            "propensity_outside_05_95_pct", "n_clipped", "max_realized_weight",
            "treated_ess", "control_ess", "majority_treated_ess",
            "majority_control_ess", "minority_treated_ess", "minority_control_ess",
            "abs_x_smd_before", "abs_x_smd_after",
        ):
            summary_row[f"mean_{field}"] = round(
                float(np.nanmean([row[field] for row in rows])), 3
            )

        summary.append(summary_row)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "overlap_simulation_runs.csv", runs)
    write_csv(OUTPUT / "overlap_simulation_summary.csv", summary)
    print(f"Saved {len(runs)} run rows and {len(summary)} summary rows")


if __name__ == "__main__":
    main()