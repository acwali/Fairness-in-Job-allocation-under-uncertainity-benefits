import csv
from pathlib import Path

import numpy as np


RAW = Path("data/raw")
OUTPUT = Path("results/metrics/ate_estimators.csv")
N_BOOTSTRAP = 2_000
SEED = 11

ESTIMATORS = (
    "Experimental difference",
    "Outcome regression (adjusted OLS)",
    "IPW (constant assignment fraction)",
)


def load_arm(arm, assignment, expected_rows):
    path = RAW / f"nswre74_{arm}.txt"
    data = np.loadtxt(path, ndmin=2)

    if data.shape != (expected_rows, 10):
        raise ValueError(f"{path}: unexpected shape {data.shape}")
    if not np.isfinite(data).all() or not np.all(data[:, 0] == assignment):
        raise ValueError(f"{path}: invalid data or treatment indicators")

    return data


def estimate_ate(data, propensity):
    treatment = data[:, 0]
    baseline = data[:, 1:9]
    earnings = data[:, 9]
    treated = treatment == 1

    experimental = earnings[treated].mean() - earnings[~treated].mean()

    # Standardize covariates for numerical stability in the OLS fit.
    scale = baseline.std(axis=0)
    scale[scale == 0] = 1
    baseline = (baseline - baseline.mean(axis=0)) / scale

    # With a common treatment effect, the treatment coefficient equals
    # the average fitted earnings difference under T=1 versus T=0.
    design = np.column_stack((np.ones(len(data)), treatment, baseline))
    coefficients = np.linalg.lstsq(design, earnings, rcond=None)[0]
    adjusted = coefficients[1]

    ipw = np.mean(
        treatment * earnings / propensity
        - (1 - treatment) * earnings / (1 - propensity)
    )

    return np.array([experimental, adjusted, ipw])


def main():
    treated = load_arm("treated", assignment=1, expected_rows=185)
    control = load_arm("control", assignment=0, expected_rows=260)
    data = np.vstack((treated, control))
    propensity = len(treated) / len(data)

    estimates = estimate_ate(data, propensity)
    rng = np.random.default_rng(SEED)
    bootstrap = np.empty((N_BOOTSTRAP, len(ESTIMATORS)))

    for replicate in range(N_BOOTSTRAP):
        treated_sample = treated[rng.integers(len(treated), size=len(treated))]
        control_sample = control[rng.integers(len(control), size=len(control))]
        sample = np.vstack((treated_sample, control_sample))
        bootstrap[replicate] = estimate_ate(sample, propensity)

    standard_errors = bootstrap.std(axis=0, ddof=1)
    lower, upper = np.percentile(bootstrap, [2.5, 97.5], axis=0)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "estimator", "ate", "bootstrap_se", "ci95_lower", "ci95_upper",
            "bootstrap_replicates", "seed",
        ])
        for i, name in enumerate(ESTIMATORS):
            writer.writerow([
                name, estimates[i], standard_errors[i], lower[i], upper[i],
                N_BOOTSTRAP, SEED,
            ])
            print(f"{name}: {estimates[i]:,.2f}  "
                  f"[95% CI {lower[i]:,.2f}, {upper[i]:,.2f}]")

    paired_delta = bootstrap[:, 1] - bootstrap[:, 0]
    delta_lower, delta_upper = np.percentile(paired_delta, [2.5, 97.5])
    print(f"Adjusted minus experimental: {estimates[1] - estimates[0]:,.2f}  "
          f"[paired 95% CI {delta_lower:,.2f}, {delta_upper:,.2f}]")
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()