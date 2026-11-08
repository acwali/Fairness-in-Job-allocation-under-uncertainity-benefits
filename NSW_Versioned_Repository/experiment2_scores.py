import argparse
import csv
from pathlib import Path

import numpy as np

from experiment1_ate import load_arm


OUTPUT = Path("results/experiment2")
SPLIT_SEED = 11
OUTER_FOLDS = 5
INNER_FOLDS = 4
RIDGE_PENALTY = 10.0
ASINH_SCALE = 1000.0

COLUMNS = [
    "outer_fold", "role", "participant_id", "inner_fold",
    "m0", "m1", "estimated_benefit", "propensity", "dr_score",
]


def stratified_folds(indices, treatment, n_folds, seed):
    """Distribute each historical treatment arm across the folds."""
    rng = np.random.default_rng(seed)
    treated = rng.permutation(indices[treatment[indices] == 1])
    control = rng.permutation(indices[treatment[indices] == 0])

    return [
        np.sort(np.concatenate((treated_chunk, control_chunk)))
        for treated_chunk, control_chunk in zip(
            np.array_split(treated, n_folds),
            np.array_split(control, n_folds),
        )
    ]


def score_participants(data, fit_ids, score_ids, propensity):
    """Fit treatment-arm earnings models and score disjoint participants."""
    assert np.intersect1d(fit_ids, score_ids).size == 0

    baseline_fit = data[fit_ids, 1:9]
    baseline_score = data[score_ids, 1:9]
    center = baseline_fit.mean(axis=0)
    scale = baseline_fit.std(axis=0)
    scale[scale == 0] = 1.0

    x_fit = np.column_stack((
        np.ones(len(fit_ids)),
        (baseline_fit - center) / scale,
    ))
    x_score = np.column_stack((
        np.ones(len(score_ids)),
        (baseline_score - center) / scale,
    ))

    penalty = RIDGE_PENALTY * np.eye(x_fit.shape[1])
    penalty[0, 0] = 0.0
    predictions = []

    for arm in (0, 1):
        in_arm = data[fit_ids, 0] == arm
        x_arm = x_fit[in_arm]
        y_arm = data[fit_ids[in_arm], 9]
        coefficients = np.linalg.solve(
            x_arm.T @ x_arm + penalty,
            x_arm.T @ y_arm,
        )
        predictions.append(x_score @ coefficients)

    m0, m1 = predictions
    treatment = data[score_ids, 0]
    earnings = data[score_ids, 9]
    benefit = m1 - m0
    dr_score = (
        benefit
        + treatment * (earnings - m1) / propensity
        - (1 - treatment) * (earnings - m0) / (1 - propensity)
    )

    scores = np.column_stack((
        m0,
        m1,
        benefit,
        np.full(len(score_ids), propensity),
        dr_score,
    ))
    assert np.isfinite(scores).all()
    return scores


def write_scores(writer, fold, role, ids, scores, inner_fold=""):
    for participant_id, score in zip(ids, scores):
        writer.writerow((fold, role, int(participant_id), inner_fold, *score))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcome", choices=("raw", "asinh"), default="raw")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output
    if output is None:
        output = OUTPUT if args.outcome == "raw" else Path("results/experiment2_asinh")

    treated = load_arm("treated", assignment=1, expected_rows=185)
    control = load_arm("control", assignment=0, expected_rows=260)
    data = np.vstack((treated, control))

    if args.outcome == "asinh":
        data[:, 9] = np.arcsinh(data[:, 9] / ASINH_SCALE)

    ids = np.arange(len(data))
    treatment = data[:, 0]
    propensity = len(treated) / len(data)

    outer_folds = stratified_folds(ids, treatment, OUTER_FOLDS, SPLIT_SEED)
    assert np.array_equal(np.sort(np.concatenate(outer_folds)), ids)

    output.mkdir(parents=True, exist_ok=True)
    with (
        (output / "development_validation_scores.csv").open(
            "w", newline="", encoding="utf-8"
        ) as development_file,
        (output / "outer_test_scores.csv").open(
            "w", newline="", encoding="utf-8"
        ) as test_file,
    ):
        development_writer = csv.writer(development_file)
        test_writer = csv.writer(test_file)
        development_writer.writerow(COLUMNS)
        test_writer.writerow(COLUMNS)

        for fold, test_ids in enumerate(outer_folds, start=1):
            outer_train = np.setdiff1d(ids, test_ids)
            validation_ids = stratified_folds(
                outer_train, treatment, 4, SPLIT_SEED + fold
            )[0]
            development_ids = np.setdiff1d(outer_train, validation_ids)

            inner_folds = stratified_folds(
                development_ids, treatment, INNER_FOLDS, SPLIT_SEED + 100 + fold
            )
            assert np.array_equal(
                np.sort(np.concatenate(inner_folds)), development_ids
            )

            for inner_fold, score_ids in enumerate(inner_folds, start=1):
                fit_ids = np.setdiff1d(development_ids, score_ids)
                scores = score_participants(data, fit_ids, score_ids, propensity)
                write_scores(
                    development_writer, fold, "development",
                    score_ids, scores, inner_fold,
                )

            validation_scores = score_participants(
                data, development_ids, validation_ids, propensity
            )
            write_scores(
                development_writer, fold, "validation",
                validation_ids, validation_scores,
            )

            test_scores = score_participants(data, outer_train, test_ids, propensity)
            write_scores(test_writer, fold, "outer_test", test_ids, test_scores)

            print(
                f"Fold {fold}: development={len(development_ids)}, "
                f"validation={len(validation_ids)}, test={len(test_ids)}"
            )

    print(f"Saved {args.outcome} score files in {output}")


if __name__ == "__main__":
    main()