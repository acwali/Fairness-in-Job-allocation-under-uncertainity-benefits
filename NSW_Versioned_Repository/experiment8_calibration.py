import csv
from pathlib import Path
from statistics import NormalDist

import numpy as np

from experiment1_ate import load_arm
from experiment2_group_audit import group_labels, write_csv
from experiment3_constraints import read_scores


OUTPUT = Path("results/metrics")
PENALTY = 10.0
INTERVAL_LEVEL = 0.90
MIN_GROUP_N = 30
BIN_EDGES = np.linspace(0.0, 1.0, 6)
NORMAL = NormalDist()


def sigmoid(values):
    return 1.0 / (1.0 + np.exp(-np.clip(values, -40.0, 40.0)))


def fit_logistic(design, positive, penalty):
    """Fit penalized logistic regression with an unpenalized intercept."""
    coefficients = np.zeros(design.shape[1])

    for _ in range(100):
        probability = sigmoid(design @ coefficients)
        weights = np.maximum(probability * (1 - probability), 1e-8)
        gradient = design.T @ (positive - probability) - penalty @ coefficients
        hessian = design.T @ (design * weights[:, None]) + penalty
        step = np.linalg.solve(hessian, gradient)
        coefficients += step

        if np.max(np.abs(step)) < 1e-8:
            return coefficients

    raise RuntimeError("Logistic regression failed to converge")


def mixture_quantile(level, probability, log_mean, log_sd):
    """Quantile of a distribution with a point mass at zero."""
    result = np.zeros(len(probability))
    positive = level > 1 - probability

    if positive.any():
        levels = (level - (1 - probability[positive])) / probability[positive]
        levels = np.clip(levels, 1e-12, 1 - 1e-12)
        z_scores = np.array([NORMAL.inv_cdf(float(p)) for p in levels])
        result[positive] = np.exp(log_mean[positive] + log_sd * z_scores)

    return result


def predict_arm(raw, train_ids, test_ids):
    x_train = raw[train_ids, 1:9]
    x_test = raw[test_ids, 1:9]
    center = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale[scale == 0] = 1.0

    train = np.column_stack((np.ones(len(train_ids)), (x_train - center) / scale))
    test = np.column_stack((np.ones(len(test_ids)), (x_test - center) / scale))
    penalty = PENALTY * np.eye(train.shape[1])
    penalty[0, 0] = 0.0

    earnings = raw[train_ids, 9]
    positive = earnings > 0
    if not positive.any() or positive.all():
        raise ValueError("Training arm needs both zero and positive earnings")

    logistic = fit_logistic(train, positive.astype(float), penalty)
    p_positive = np.clip(sigmoid(test @ logistic), 1e-12, 1 - 1e-12)

    positive_design = train[positive]
    log_earnings = np.log(earnings[positive])
    log_coefficients = np.linalg.solve(
        positive_design.T @ positive_design + penalty,
        positive_design.T @ log_earnings,
    )
    log_mean = test @ log_coefficients
    residuals = log_earnings - positive_design @ log_coefficients
    log_sd = max(float(np.sqrt(np.mean(residuals**2))), 1e-6)
    mean_earnings = p_positive * np.exp(log_mean + 0.5 * log_sd**2)

    tail = (1 - INTERVAL_LEVEL) / 2
    lower = mixture_quantile(tail, p_positive, log_mean, log_sd)
    upper = mixture_quantile(1 - tail, p_positive, log_mean, log_sd)

    observed = raw[test_ids, 9]
    observed_positive = observed > 0
    log_score = np.log1p(-p_positive)
    log_y = np.log(observed[observed_positive])
    z = (log_y - log_mean[observed_positive]) / log_sd
    log_score[observed_positive] = (
        np.log(p_positive[observed_positive])
        - log_y
        - np.log(log_sd)
        - 0.5 * np.log(2 * np.pi)
        - 0.5 * z**2
    )

    return p_positive, mean_earnings, lower, upper, log_score


def metrics(mask, earnings, probability, prediction, lower, upper, log_score):
    y = earnings[mask]
    p = probability[mask]
    observed_positive = y > 0
    errors = prediction[mask] - y
    covered = (y >= lower[mask]) & (y <= upper[mask])

    return {
        "n": len(y),
        "n_positive": int(observed_positive.sum()),
        "n_zero": int((~observed_positive).sum()),
        "small_group_n_lt_30": len(y) < MIN_GROUP_N,
        "mean_predicted_positive_pct": round(100 * p.mean(), 2),
        "observed_positive_pct": round(100 * observed_positive.mean(), 2),
        "calibration_gap_pp": round(100 * (p.mean() - observed_positive.mean()), 2),
        "brier_score": round(float(np.mean((p - observed_positive) ** 2)), 4),
        "mae": round(float(np.mean(np.abs(errors))), 2),
        "rmse": round(float(np.sqrt(np.mean(errors**2))), 2),
        "mean_predictive_log_score": round(float(log_score[mask].mean()), 4),
        "nominal_interval_coverage_pct": 100 * INTERVAL_LEVEL,
        "observed_interval_coverage_pct": round(100 * covered.mean(), 2),
        "mean_interval_width": round(float((upper[mask] - lower[mask]).mean()), 2),
    }


def main():
    raw = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    ids = np.arange(len(raw))
    treatment = raw[:, 0]
    earnings = raw[:, 9]
    if np.any(earnings < 0):
        raise ValueError("The zero-plus-lognormal model requires nonnegative earnings")

    rows = read_scores("outer_test_scores.csv")
    fold_by_id = np.full(len(raw), -1, dtype=int)

    for row in rows:
        participant = int(row["participant_id"])
        fold = int(row["outer_fold"])
        if not 0 <= participant < len(raw) or fold_by_id[participant] != -1:
            raise ValueError("Invalid or duplicate held-out participant")
        fold_by_id[participant] = fold

    if not np.array_equal(np.unique(fold_by_id), np.arange(1, 6)):
        raise ValueError("Expected each participant in one of five outer folds")

    predictions = np.full((5, len(raw)), np.nan)
    for fold in range(1, 6):
        for arm in (0, 1):
            train_ids = ids[(fold_by_id != fold) & (treatment == arm)]
            test_ids = ids[(fold_by_id == fold) & (treatment == arm)]
            predictions[:, test_ids] = predict_arm(raw, train_ids, test_ids)

    if not np.isfinite(predictions).all():
        raise ValueError("Expected finite held-out predictions for all participants")

    probability, prediction, lower, upper, log_score = predictions
    scopes = (
        ("All", np.ones(len(raw), dtype=bool)),
        ("Control", treatment == 0),
        ("Treated", treatment == 1),
    )
    race, age, intersection = group_labels(raw)
    audits = (("race", race), ("age", age), ("race_by_age", intersection))

    summary = []
    groups = []
    bins = []

    for scope, scope_mask in scopes:
        summary.append({
            "historical_arm": scope,
            **metrics(scope_mask, earnings, *predictions),
        })

        for audit, labels in audits:
            for group in np.unique(labels):
                mask = scope_mask & (labels == group)
                if mask.any():
                    groups.append({
                        "historical_arm": scope,
                        "audit": audit,
                        "group": group,
                        **metrics(mask, earnings, *predictions),
                    })

        for left, right in zip(BIN_EDGES[:-1], BIN_EDGES[1:]):
            mask = scope_mask & (probability >= left) & (probability < right)
            count = int(mask.sum())
            bins.append({
                "historical_arm": scope,
                "probability_bin_lower": round(float(left), 2),
                "probability_bin_upper": round(float(right), 2),
                "n": count,
                "mean_predicted_positive_pct": (
                    round(100 * probability[mask].mean(), 2) if count else ""
                ),
                "observed_positive_pct": (
                    round(100 * (earnings[mask] > 0).mean(), 2) if count else ""
                ),
            })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "predictive_calibration_summary.csv", summary)
    write_csv(OUTPUT / "predictive_calibration_groups.csv", groups)
    write_csv(OUTPUT / "predictive_calibration_bins.csv", bins)

    print(
        f"Scored {len(raw)} held-out participants. "
        f"Saved {len(summary)} summary rows, {len(groups)} group rows, "
        f"and {len(bins)} calibration bins."
    )


if __name__ == "__main__":
    main()