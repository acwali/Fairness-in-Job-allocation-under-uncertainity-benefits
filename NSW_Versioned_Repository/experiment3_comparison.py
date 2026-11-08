import ast
import csv

import numpy as np

from experiment1_ate import load_arm
from experiment2_baselines import CAPACITIES, N_BOOTSTRAP
from experiment2_group_audit import group_labels, write_csv
from experiment3_constraints import (
    OUTPUT, TIE_SEED, allocate, get_batch, read_scores,
)


TOLERANCE = 200.0
PAIRED_CAPACITY = 20
PAIRED_SEED = 312


def load_table(filename):
    with (OUTPUT / filename).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def match_validation_utility(selections, diagnostics):
    rows = []

    for capacity in CAPACITIES:
        for fold in range(1, 6):
            subset = [
                row for row in diagnostics
                if int(row["capacity_pct"]) == capacity
                and int(row["outer_fold"]) == fold
            ]
            # Feasibility and overall value repeat across each candidate's
            # race-group diagnostic rows. Retain one row per candidate.
            candidates = {row["candidate"]: row for row in subset}
            reference = float(
                selections[capacity, fold, "Unconstrained"]["validation_value"]
            )

            for method, field in (
                ("Point estimate", "point_feasible"),
                ("Lower confidence bound", "bound_feasible"),
            ):
                feasible = [
                    row for row in candidates.values() if row[field] == "True"
                ]
                matched = [
                    row for row in feasible
                    if abs(reference - float(row["validation_value"])) <= TOLERANCE
                ]
                best = max(
                    matched, key=lambda row: float(row["validation_value"]),
                    default=None,
                )
                best_value = float(best["validation_value"]) if best else None

                status = "matched"
                if not feasible:
                    status = "constraint infeasible"
                elif best is None:
                    status = "outside utility tolerance"

                rows.append({
                    "capacity_pct": capacity,
                    "outer_fold": fold,
                    "method": method,
                    "status": status,
                    "reference_validation_value": round(reference, 2),
                    "tolerance": TOLERANCE,
                    "feasible_candidates": len(feasible),
                    "matched_candidates": len(matched),
                    "matched_candidate": best["candidate"] if best else "",
                    "matched_validation_value": (
                        round(best_value, 2) if best_value is not None else ""
                    ),
                    "validation_utility_loss": (
                        round(reference - best_value, 2)
                        if best_value is not None else ""
                    ),
                })

    return rows


def paired_outer_comparison(selections):
    raw = np.vstack((
        load_arm("treated", assignment=1, expected_rows=185),
        load_arm("control", assignment=0, expected_rows=260),
    ))
    race, _, _ = group_labels(raw)
    labels = np.unique(race)
    tie_priority = np.random.default_rng(TIE_SEED).permutation(len(raw))
    methods = ("Unconstrained", "Point estimate")
    test = read_scores("outer_test_scores.csv")
    contributions = np.full((len(methods), len(raw)), np.nan)

    for fold in range(1, 6):
        ids, dr = get_batch(test, fold, "outer_test")
        slots = PAIRED_CAPACITY * len(ids) // 100

        for i, method in enumerate(methods):
            selection = selections[PAIRED_CAPACITY, fold, method]
            if selection["status"] != "selected":
                raise ValueError(f"Fold {fold}: no selected {method} policy")
            rule = ast.literal_eval(selection["rule"])
            decision = allocate(rule, raw, ids, slots, tie_priority)
            contributions[i, ids] = decision * dr

    if not np.isfinite(contributions).all():
        raise ValueError("Expected contributions for all 445 participants")

    rng = np.random.default_rng(PAIRED_SEED)
    draws = rng.integers(len(raw), size=(N_BOOTSTRAP, len(raw)))
    sampled = contributions[:, draws]
    overall = contributions.mean(axis=1)
    sampled_overall = sampled.mean(axis=2)

    group_means = []
    sampled_group_means = []
    valid = np.ones(N_BOOTSTRAP, dtype=bool)

    for group in labels:
        members = race == group
        drawn_members = members[draws]
        counts = drawn_members.sum(axis=1)
        valid &= counts > 0
        group_means.append(contributions[:, members].mean(axis=1))
        sampled_group_means.append(
            (sampled * drawn_members[None, :, :]).sum(axis=2)
            / np.maximum(counts, 1)
        )

    worst_group = np.stack(group_means).min(axis=0)
    sampled_worst = np.stack(sampled_group_means).min(axis=0)
    metrics = (
        ("Overall value per eligible", overall, sampled_overall),
        ("Worst race-group benefit", worst_group, sampled_worst[:, valid]),
    )

    rows = []
    for name, estimates, bootstrap in metrics:
        paired = bootstrap[1] - bootstrap[0]
        lower, upper = np.percentile(paired, [2.5, 97.5])
        rows.append({
            "capacity_pct": PAIRED_CAPACITY,
            "metric": name,
            "unconstrained": round(float(estimates[0]), 2),
            "point_estimate_policy": round(float(estimates[1]), 2),
            "point_minus_unconstrained": round(float(estimates[1] - estimates[0]), 2),
            "ci95_lower": round(float(lower), 2),
            "ci95_upper": round(float(upper), 2),
            "valid_bootstrap_replicates": len(paired),
        })

    return rows


def main():
    selections = {
        (int(row["capacity_pct"]), int(row["outer_fold"]), row["method"]): row
        for row in load_table("constraint_selections.csv")
    }
    diagnostics = load_table("constraint_validation_candidates.csv")

    matches = match_validation_utility(selections, diagnostics)
    write_csv(OUTPUT / "constraint_matched_utility_audit.csv", matches)

    paired = paired_outer_comparison(selections)
    write_csv(OUTPUT / "constraint_paired_20pct.csv", paired)
    print(f"Saved {len(matches)} utility-audit rows and {len(paired)} paired results")


if __name__ == "__main__":
    main()