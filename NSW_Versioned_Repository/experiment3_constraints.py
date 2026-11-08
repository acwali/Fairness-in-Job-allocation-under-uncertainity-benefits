import argparse
import csv
from pathlib import Path

import numpy as np

from experiment1_ate import load_arm
from experiment2_baselines import CAPACITIES, N_BOOTSTRAP
from experiment2_group_audit import group_labels, write_csv


INPUT = Path("results/experiment2")
OUTPUT = Path("results/metrics")
FLOOR = 0.0
CONFIDENCE = 0.95
TIE_SEED = 114
BOOTSTRAP_SEED = 311

FEATURES = (
    ("age", 1),
    ("education", 2),
    ("re74", 7),
    ("re75", 8),
)
METHODS = ("Unconstrained", "Point estimate", "Lower confidence bound")


def read_scores(filename, directory=INPUT):
    with (directory / filename).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def get_batch(rows, fold, role):
    batch = [
        row for row in rows
        if int(row["outer_fold"]) == fold and row["role"] == role
    ]
    ids = np.array([int(row["participant_id"]) for row in batch], dtype=int)
    scores = np.array([float(row["dr_score"]) for row in batch])
    return ids, scores


def fit_stumps(raw, ids, dr):
    """Fit candidate splits and preferred leaves on development data."""
    candidates = []

    for feature, column in FEATURES:
        values = raw[ids, column]
        for threshold in np.unique(np.quantile(values, [0.33, 0.67])):
            low = values <= threshold
            if min(low.sum(), (~low).sum()) < 20:
                continue

            prefer_low = bool(dr[low].mean() >= dr[~low].mean())
            candidates.append((feature, column, float(threshold), prefer_low))

    if not candidates:
        raise ValueError("No candidate stump met the minimum leaf size")

    return candidates


def allocate(rule, raw, ids, slots, tie_priority):
    _, column, threshold, prefer_low = rule
    low = raw[ids, column] <= threshold
    preferred = low if prefer_low else ~low
    order = np.lexsort((tie_priority[ids], -preferred.astype(int)))

    decision = np.zeros(len(ids), dtype=int)
    decision[order[:slots]] = 1
    return decision


def validation_statistics(contributions, groups, labels, seed):
    """Compute approximate simultaneous one-sided bootstrap lower bounds."""
    rng = np.random.default_rng(seed)
    estimates = []
    bootstrap = []

    for label in labels:
        group_values = contributions[:, groups == label]
        count = group_values.shape[1]
        if count == 0:
            raise ValueError(f"Missing validation group: {label}")

        estimates.append(group_values.mean(axis=1))
        draws = rng.integers(count, size=(N_BOOTSTRAP, count))
        bootstrap.append(group_values[:, draws].mean(axis=2))

    estimates = np.stack(estimates, axis=1)
    bootstrap = np.stack(bootstrap, axis=1)
    errors = bootstrap - estimates[:, :, None]
    se = bootstrap.std(axis=2, ddof=1)

    active = np.any(bootstrap != bootstrap[:, :, :1], axis=2)
    se = np.where(active, se, 0.0)
    standardized = np.divide(
        errors,
        se[:, :, None],
        out=np.zeros_like(errors),
        where=se[:, :, None] > 0,
    )
    maxima = standardized.max(axis=(0, 1))
    critical = max(0.0, float(np.quantile(maxima, CONFIDENCE)))

    return estimates, estimates - critical * se


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-scores", type=Path, default=INPUT)
    parser.add_argument("--evaluation-scores", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    output = args.output
    evaluation_scores = args.evaluation_scores or args.selection_scores

    raw = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    race, _, _ = group_labels(raw)
    labels = np.unique(race)
    tie_priority = np.random.default_rng(TIE_SEED).permutation(len(raw))

    development_validation = read_scores(
        "development_validation_scores.csv", args.selection_scores
    )
    diagnostics = []
    selections = []
    frozen = {}
    expected_test_ids = {}

    for fold in range(1, 6):
        dev_ids, dev_dr = get_batch(development_validation, fold, "development")
        val_ids, val_dr = get_batch(development_validation, fold, "validation")

        assert len(dev_ids) == 267 and len(val_ids) == 89
        assert np.intersect1d(dev_ids, val_ids).size == 0

        expected_test_ids[fold] = np.setdiff1d(
            np.arange(len(raw)), np.concatenate((dev_ids, val_ids))
        )
        candidates = fit_stumps(raw, dev_ids, dev_dr)
        val_groups = race[val_ids]

        for capacity in CAPACITIES:
            slots = capacity * len(val_ids) // 100
            decisions = np.stack([
                allocate(rule, raw, val_ids, slots, tie_priority)
                for rule in candidates
            ])
            contributions = decisions * val_dr
            values = contributions.mean(axis=1)

            estimates, bounds = validation_statistics(
                contributions,
                val_groups,
                labels,
                np.random.SeedSequence([BOOTSTRAP_SEED, fold, capacity]),
            )
            point_ok = np.all(estimates >= FLOOR, axis=1)
            bound_ok = np.all(bounds >= FLOOR, axis=1)

            for i, (feature, _, threshold, prefer_low) in enumerate(candidates):
                for j, label in enumerate(labels):
                    members = val_groups == label
                    diagnostics.append({
                        "outer_fold": fold,
                        "capacity_pct": capacity,
                        "candidate": i + 1,
                        "feature": feature,
                        "threshold": threshold,
                        "preferred_leaf": "<=" if prefer_low else ">",
                        "validation_value": values[i],
                        "race_group": label,
                        "n_eligible": int(members.sum()),
                        "n_allocated": int(decisions[i, members].sum()),
                        "exploratory_n_lt_30": members.sum() < 30,
                        "group_benefit": estimates[i, j],
                        "group_lower_bound": bounds[i, j],
                        "point_feasible": bool(point_ok[i]),
                        "bound_feasible": bool(bound_ok[i]),
                    })

            eligibility = (
                np.ones(len(candidates), dtype=bool),
                point_ok,
                bound_ok,
            )

            for method, eligible in zip(METHODS, eligibility):
                feasible = np.flatnonzero(eligible)
                best = (
                    int(feasible[np.argmax(values[feasible])])
                    if feasible.size else None
                )
                frozen[fold, capacity, method] = (
                    candidates[best] if best is not None else None
                )
                selections.append({
                    "outer_fold": fold,
                    "capacity_pct": capacity,
                    "method": method,
                    "feasible_candidates": len(feasible),
                    "status": "selected" if best is not None else "infeasible",
                    "candidate": best + 1 if best is not None else "",
                    "rule": str(candidates[best]) if best is not None else "",
                    "validation_value": values[best] if best is not None else "",
                })

    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "constraint_validation_candidates.csv", diagnostics)
    write_csv(output / "constraint_selections.csv", selections)

    # Read held-out scores after the validation choices have been saved.
    test = read_scores("outer_test_scores.csv", evaluation_scores)
    test_batches = {}

    for fold in range(1, 6):
        ids, dr = get_batch(test, fold, "outer_test")
        if len(ids) != 89 or not np.array_equal(
            np.sort(ids), expected_test_ids[fold]
        ):
            raise ValueError(
                f"Fold {fold}: evaluation participants do not match "
                "the held-out participants for the selection scores"
            )
        if not np.isfinite(dr).all():
            raise ValueError(f"Fold {fold}: non-finite evaluation scores")

        test_batches[fold] = (ids, dr)

    summary = []
    for capacity in CAPACITIES:
        for method in METHODS:
            contributions = []
            test_groups = []
            completed = 0

            for fold, (ids, dr) in test_batches.items():
                rule = frozen[fold, capacity, method]
                if rule is None:
                    continue

                slots = capacity * len(ids) // 100
                decision = allocate(rule, raw, ids, slots, tie_priority)
                contributions.extend(decision * dr)
                test_groups.extend(race[ids])
                completed += 1

            value = ""
            worst = ""
            if completed == len(test_batches):
                values = np.asarray(contributions)
                groups = np.asarray(test_groups)
                value = round(float(values.mean()), 2)
                worst = round(
                    min(float(values[groups == label].mean()) for label in labels),
                    2,
                )

            summary.append({
                "capacity_pct": capacity,
                "method": method,
                "folds_with_policy": completed,
                "folds_infeasible": len(test_batches) - completed,
                "outer_value_per_eligible": value,
                "outer_minimum_race_benefit": worst,
            })

    write_csv(output / "constraint_outer_summary.csv", summary)
    print(f"Saved {len(selections)} fold selections and {len(summary)} summary rows")


if __name__ == "__main__":
    main()