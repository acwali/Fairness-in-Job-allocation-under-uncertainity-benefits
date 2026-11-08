import csv
from pathlib import Path

import numpy as np

from experiment1_ate import load_arm
from experiment2_group_audit import group_labels, write_csv
from experiment2_scores import score_participants
from experiment3_constraints import (
    BOOTSTRAP_SEED,
    FLOOR,
    METHODS,
    TIE_SEED,
    allocate,
    fit_stumps,
    get_batch,
    read_scores,
    validation_statistics,
)


OUTPUT = Path("results/metrics/refitting")
CAPACITY = 40
SEEDS = (11, 22, 33, 44, 55)
REPEATS_PER_SEED = 20
OUTER_FOLDS = (1, 2, 3, 4, 5)
INNER_FOLDS = (1, 2, 3, 4)


def development_blocks(rows, fold):
    return [
        np.array([
            int(row["participant_id"])
            for row in rows
            if int(row["outer_fold"]) == fold
            and row["role"] == "development"
            and int(row["inner_fold"]) == inner
        ], dtype=int)
        for inner in INNER_FOLDS
    ]


def resample_block(ids, treatment, rng):
    """Preserve each original inner block and its treatment-arm counts."""
    samples = []
    for arm in (0, 1):
        members = ids[treatment[ids] == arm]
        samples.append(rng.choice(members, size=len(members), replace=True))
    return np.sort(np.concatenate(samples))


def refit_and_select(raw, race, labels, blocks, val_ids, propensity,
                     tie_priority, fold):
    development_ids = np.concatenate(blocks)
    development_dr = []

    for inner, score_ids in enumerate(blocks):
        fit_ids = np.concatenate([
            block for index, block in enumerate(blocks) if index != inner
        ])
        scores = score_participants(raw, fit_ids, score_ids, propensity)
        development_dr.append(scores[:, -1])

    candidates = fit_stumps(
        raw, development_ids, np.concatenate(development_dr)
    )
    val_dr = score_participants(raw, development_ids, val_ids, propensity)[:, -1]
    slots = CAPACITY * len(val_ids) // 100

    decisions = np.stack([
        allocate(rule, raw, val_ids, slots, tie_priority)
        for rule in candidates
    ])
    contributions = decisions * val_dr
    values = contributions.mean(axis=1)
    estimates, lower_bounds = validation_statistics(
        contributions,
        race[val_ids],
        labels,
        np.random.SeedSequence([BOOTSTRAP_SEED, fold, CAPACITY]),
    )
    eligibility = (
        np.ones(len(candidates), dtype=bool),
        np.all(estimates >= FLOOR, axis=1),
        np.all(lower_bounds >= FLOOR, axis=1),
    )

    selections = {}
    for method, eligible in zip(METHODS, eligibility):
        feasible = np.flatnonzero(eligible)
        if feasible.size:
            best = int(feasible[np.argmax(values[feasible])])
            selections[method] = (candidates[best], len(feasible), float(values[best]))
        else:
            selections[method] = (None, 0, None)

    return selections


def read_reference_rules():
    path = Path("results/metrics/constraint_selections.csv")
    with path.open(newline="", encoding="utf-8") as file:
        return {
            (int(row["outer_fold"]), row["method"]): row["rule"]
            for row in csv.DictReader(file)
            if int(row["capacity_pct"]) == CAPACITY
        }


def evaluate(rule, raw, ids, dr, tie_priority):
    slots = CAPACITY * len(ids) // 100
    decision = allocate(rule, raw, ids, slots, tie_priority)
    return decision * dr


def full_sample_metrics(fold_values, race, labels):
    ids = np.concatenate([batch[0] for batch in fold_values])
    values = np.concatenate([batch[1] for batch in fold_values])
    assert np.array_equal(np.sort(ids), np.arange(len(race)))

    groups = race[ids]
    return (
        float(values.mean()),
        min(float(values[groups == label].mean()) for label in labels),
    )


def main():
    treated = load_arm("treated", assignment=1, expected_rows=185)
    control = load_arm("control", assignment=0, expected_rows=260)
    raw = np.vstack((treated, control))
    treatment = raw[:, 0]
    propensity = len(treated) / len(raw)
    race, _, _ = group_labels(raw)
    labels = np.unique(race)
    tie_priority = np.random.default_rng(TIE_SEED).permutation(len(raw))

    development = read_scores("development_validation_scores.csv")
    test = read_scores("outer_test_scores.csv")
    reference = read_reference_rules()
    batches = {}

    for fold in OUTER_FOLDS:
        blocks = development_blocks(development, fold)
        val_ids, _ = get_batch(development, fold, "validation")
        test_ids, test_dr = get_batch(test, fold, "outer_test")
        all_ids = np.concatenate((*blocks, val_ids, test_ids))

        assert np.array_equal(np.sort(all_ids), np.arange(len(raw)))

        # Verify that the unresampled refit reproduces the raw-run selections.
        original = refit_and_select(
            raw, race, labels, blocks, val_ids, propensity, tie_priority, fold
        )
        for method, (rule, _, _) in original.items():
            rule_text = str(rule) if rule is not None else ""
            if rule_text != reference[fold, method]:
                raise ValueError(
                    f"Fold {fold}: unresampled {method} rule differs from "
                    "the saved raw-run selection"
                )

        batches[fold] = (blocks, val_ids, test_ids, test_dr)

    print("Verified all 15 original fold-by-method selections")

    fold_rows = []
    replicate_rows = []

    for seed in SEEDS:
        for repeat in range(1, REPEATS_PER_SEED + 1):
            evaluated = {method: [] for method in METHODS}

            for fold, (blocks, val_ids, test_ids, test_dr) in batches.items():
                rng = np.random.default_rng(
                    np.random.SeedSequence([seed, repeat, fold])
                )
                resampled = [
                    resample_block(block, treatment, rng) for block in blocks
                ]

                selections = refit_and_select(
                    raw, race, labels, resampled, val_ids,
                    propensity, tie_priority, fold,
                )

                for method, (rule, feasible, validation_value) in selections.items():
                    rule_text = str(rule) if rule is not None else ""
                    fold_value = ""
                    if rule is not None:
                        contributions = evaluate(
                            rule, raw, test_ids, test_dr, tie_priority
                        )
                        evaluated[method].append((test_ids, contributions))
                        fold_value = float(contributions.mean())

                    fold_rows.append({
                        "seed": seed,
                        "replicate": repeat,
                        "outer_fold": fold,
                        "method": method,
                        "selected": rule is not None,
                        "feasible_candidates": feasible,
                        "rule": rule_text,
                        "same_as_original_selection": rule_text == reference[fold, method],
                        "validation_value": validation_value,
                        "outer_fold_value": fold_value,
                    })

            for method, fold_values in evaluated.items():
                value = worst = ""
                if len(fold_values) == len(OUTER_FOLDS):
                    value, worst = full_sample_metrics(fold_values, race, labels)

                replicate_rows.append({
                    "seed": seed,
                    "replicate": repeat,
                    "method": method,
                    "folds_with_policy": len(fold_values),
                    "outer_value_per_eligible": value,
                    "outer_minimum_race_benefit": worst,
                })

        print(f"Finished seed {seed}")

    summary = []
    for method in METHODS:
        folds = [row for row in fold_rows if row["method"] == method]
        selected = [row for row in folds if row["selected"]]
        complete = [
            row for row in replicate_rows
            if row["method"] == method
            and row["folds_with_policy"] == len(OUTER_FOLDS)
        ]

        summary.append({
            "capacity_pct": CAPACITY,
            "method": method,
            "fold_refits": len(folds),
            "folds_with_policy": len(selected),
            "feasibility_pct": round(100 * len(selected) / len(folds), 2),
            "full_five_fold_replicates": len(complete),
            "same_rule_pct_when_selected": (
                round(100 * np.mean([
                    row["same_as_original_selection"] for row in selected
                ]), 2) if selected else ""
            ),
            "median_outer_value_when_complete": (
                round(float(np.median([
                    row["outer_value_per_eligible"] for row in complete
                ])), 2) if complete else ""
            ),
            "median_worst_group_benefit_when_complete": (
                round(float(np.median([
                    row["outer_minimum_race_benefit"] for row in complete
                ])), 2) if complete else ""
            ),
        })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "refitting_fold_runs.csv", fold_rows)
    write_csv(OUTPUT / "refitting_replicates.csv", replicate_rows)
    write_csv(OUTPUT / "refitting_summary.csv", summary)
    print(
        f"Saved {len(fold_rows)} fold rows, {len(replicate_rows)} "
        f"replicate rows, and {len(summary)} summary rows"
    )


if __name__ == "__main__":
    main()