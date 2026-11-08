import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from experiment1_ate import load_arm
from experiment2_baselines import N_BOOTSTRAP
from experiment2_scores import (
    OUTER_FOLDS,
    OUTPUT as SCORE_DIRECTORY,
    SPLIT_SEED,
    score_participants,
    stratified_folds,
)


OUTPUT = Path("results/metrics")
MAX_DEPTH = 2
MIN_LEAF = 20
BOOTSTRAP_SEED = 610


@dataclass
class Node:
    value: float
    split: tuple[int, float, "Node", "Node"] | None = None

    def predict(self, x):
        if self.split is None:
            return np.full(len(x), self.value)

        feature, threshold, left, right = self.split
        goes_left = x[:, feature] <= threshold
        predictions = np.empty(len(x))
        predictions[goes_left] = left.predict(x[goes_left])
        predictions[~goes_left] = right.predict(x[~goes_left])
        return predictions


def fit_tree(x, y, depth=0):
    """Fit a deterministic squared-error regression tree."""
    node = Node(float(y.mean()))
    n = len(y)
    if depth == MAX_DEPTH or n < 2 * MIN_LEAF:
        return node

    centered = y - node.value
    cuts = np.arange(MIN_LEAF, n - MIN_LEAF + 1)
    best_gain = 0.0
    best_split = None

    for feature in range(x.shape[1]):
        order = np.argsort(x[:, feature], kind="stable")
        sorted_x = x[order, feature]
        valid_cuts = cuts[sorted_x[cuts - 1] < sorted_x[cuts]]
        if not valid_cuts.size:
            continue

        sums = np.cumsum(centered[order])
        left_sum = sums[valid_cuts - 1]
        right_sum = sums[-1] - left_sum
        gains = left_sum**2 / valid_cuts + right_sum**2 / (n - valid_cuts)
        best = int(np.argmax(gains))
        if gains[best] > best_gain:
            best_gain = gains[best]
            cut = valid_cuts[best]
            threshold = sorted_x[cut - 1] + (sorted_x[cut] - sorted_x[cut - 1]) / 2
            best_split = feature, threshold

    if best_split is not None:
        feature, threshold = best_split
        left = x[:, feature] <= threshold
        node.split = (
            feature,
            threshold,
            fit_tree(x[left], y[left], depth + 1),
            fit_tree(x[~left], y[~left], depth + 1),
        )
    return node


def recorded_ridge_predictions():
    path = SCORE_DIRECTORY / "outer_test_scores.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    predictions = {
        (int(row["outer_fold"]), int(row["participant_id"])):
        (float(row["m0"]), float(row["m1"]))
        for row in rows
        if row["role"] == "outer_test"
    }
    if len(predictions) != len(rows):
        raise ValueError(f"Duplicate or non-test rows in {path}")
    return predictions


def metrics(residuals, axis=None):
    mae = np.mean(np.abs(residuals), axis=axis)
    rmse = np.sqrt(np.mean(residuals**2, axis=axis))
    return mae, rmse


def save_table(name, rows):
    path = OUTPUT / name
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    data = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    ids = np.arange(len(data))
    treatment = data[:, 0].astype(int)
    earnings = data[:, 9]
    features = data[:, 1:9]
    propensity = treatment.mean()
    folds = stratified_folds(ids, treatment, OUTER_FOLDS, SPLIT_SEED)
    np.testing.assert_array_equal(np.sort(np.concatenate(folds)), ids)

    recorded = recorded_ridge_predictions()
    if set(recorded) != {
        (fold, person)
        for fold, test_ids in enumerate(folds, start=1)
        for person in test_ids
    }:
        raise ValueError("The saved scores do not match the reconstructed outer folds.")

    ridge = np.empty(len(data))
    tree = np.empty(len(data))
    strata = []
    slices = []

    for fold, test_ids in enumerate(folds, start=1):
        train_ids = np.setdiff1d(ids, test_ids)
        arm = treatment[test_ids]

        # Refitting the existing ridge function verifies the saved comparator.
        predictions = score_participants(data, train_ids, test_ids, propensity)[:, :2]
        saved = np.array([recorded[fold, person] for person in test_ids])
        np.testing.assert_allclose(predictions, saved, rtol=1e-10, atol=1e-7)
        ridge[test_ids] = predictions[np.arange(len(test_ids)), arm]

        for assignment in (0, 1):
            fit_ids = train_ids[treatment[train_ids] == assignment]
            score_ids = test_ids[arm == assignment]
            model = fit_tree(features[fit_ids], earnings[fit_ids])
            tree[score_ids] = model.predict(features[score_ids])
            strata.append(score_ids)

        slices.append((f"Fold {fold}", test_ids))

    slices.extend((
        ("All", ids),
        ("Control", ids[treatment == 0]),
        ("Treated", ids[treatment == 1]),
    ))
    residuals = {"Ridge": ridge - earnings, "Shallow regression tree": tree - earnings}

    rows = []
    for label, subset in slices:
        for model, errors in residuals.items():
            mae, rmse = metrics(errors[subset])
            rows.append({"scope": label, "model": model, "n": len(subset),
                         "mae": round(float(mae), 2), "rmse": round(float(rmse), 2)})

    # Paired participant bootstrap conditional on the fitted models.
    # Preserve the test-fold and historical-treatment counts in each draw.
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.concatenate([
        rng.choice(stratum, size=(N_BOOTSTRAP, len(stratum)), replace=True)
        for stratum in strata
    ], axis=1)
    point = np.subtract(metrics(residuals["Shallow regression tree"]), metrics(residuals["Ridge"]))
    paired = np.subtract(
        metrics(residuals["Shallow regression tree"][draws], axis=1),
        metrics(residuals["Ridge"][draws], axis=1),
    )
    intervals = np.percentile(paired, [2.5, 97.5], axis=1)
    comparisons = [
        {"metric": name, "tree_minus_ridge": round(float(point[i]), 2),
         "ci95_lower": round(float(intervals[0, i]), 2),
         "ci95_upper": round(float(intervals[1, i]), 2),
         "bootstrap_replicates": N_BOOTSTRAP}
        for i, name in enumerate(("MAE", "RMSE"))
    ]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    save_table("predictive_baselines.csv", rows)
    save_table("predictive_baselines_paired.csv", comparisons)
    print(f"Verified ridge predictions and fold membership for {len(data)} held-out participants.")
    for row in rows:
        if row["scope"] == "All":
            print(f"{row['model']}: MAE {row['mae']:,.2f}, RMSE {row['rmse']:,.2f}")


if __name__ == "__main__":
    main()

