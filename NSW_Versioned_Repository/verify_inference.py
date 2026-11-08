import csv
from pathlib import Path

import numpy as np


TOL = 1e-8
OUTPUT = Path("results/metrics/inference_checks.csv")

# All axes are in state order [0, 1].
P_G = np.array([0.75, 0.25])
P_T = np.array([0.60, 0.40])
P_X_G = np.array([[0.70, 0.30], [0.40, 0.60]])  # G, X
P_Y_XT = np.array([                             # X, T, Y
    [[0.80, 0.20], [0.55, 0.45]],
    [[0.45, 0.55], [0.30, 0.70]],
])


def normalize(values):
    return values / values.sum()


def evidence_mask(name, evidence):
    if name not in evidence:
        return np.ones(2)
    return (np.arange(2) == evidence[name]).astype(float)


def variable_elimination(evidence):
    # Eliminate G from the factors containing G, producing a factor on X.
    group_factor = P_G * evidence_mask("G", evidence)
    factor_x = group_factor @ P_X_G
    factor_x *= evidence_mask("X", evidence)

    # Eliminate T from the treatment and outcome factors.
    treatment_factor = P_T * evidence_mask("T", evidence)
    factor_xy = (P_Y_XT * treatment_factor[None, :, None]).sum(axis=1)

    # Eliminate X and normalize the remaining factor on Y.
    return normalize(factor_x @ factor_xy)


def clique_tree(evidence):
    left = P_G[:, None] * P_X_G
    left *= evidence_mask("G", evidence)[:, None]
    left *= evidence_mask("X", evidence)[None, :]

    right = P_T[None, :, None] * P_Y_XT
    right *= evidence_mask("T", evidence)[None, :, None]

    # Both messages have scope X, the separator between the cliques.
    left_to_right = left.sum(axis=0)
    right_to_left = right.sum(axis=(1, 2))
    calibrated_left = left * right_to_left[None, :]
    calibrated_right = right * left_to_right[:, None, None]

    left_x = normalize(calibrated_left.sum(axis=0))
    right_x = normalize(calibrated_right.sum(axis=(1, 2)))
    np.testing.assert_allclose(left_x, right_x, atol=TOL, rtol=0)

    return normalize(calibrated_right.sum(axis=(0, 1)))


def main():
    assert P_G.shape == P_T.shape == (2,)
    assert P_X_G.shape == (2, 2)
    assert P_Y_XT.shape == (2, 2, 2)
    for factor in (P_G, P_T, P_X_G, P_Y_XT):
        assert np.all(factor >= 0)
        np.testing.assert_allclose(factor.sum(axis=-1), 1, atol=TOL, rtol=0)

    # Verify T is jointly independent of (G, X) in the experimental fixture.
    joint = P_G[:, None, None, None] * P_X_G[:, :, None, None]
    joint = joint * P_T[None, None, :, None] * P_Y_XT[None, :, :, :]
    joint_gxt = joint.sum(axis=3)
    product = joint_gxt.sum(axis=2)[:, :, None] * joint_gxt.sum(axis=(0, 1))
    np.testing.assert_allclose(joint_gxt, product, atol=TOL, rtol=0)

    cases = [
        ("No evidence", {}),
        ("Control", {"T": 0}),
        ("Treated", {"T": 1}),
        ("Group 1 and treated", {"G": 1, "T": 1}),
        ("High baseline earnings and treated", {"X": 1, "T": 1}),
        ("Group 0 and low baseline earnings", {"G": 0, "X": 0}),
    ]

    rows = []
    for name, evidence in cases:
        ve = variable_elimination(evidence)
        ct = clique_tree(evidence)
        np.testing.assert_allclose(ve, ct, atol=TOL, rtol=0)
        error = float(np.max(np.abs(ve - ct)))
        rows.append((name, str(evidence), ve[1], ct[1], error, TOL))
        print(f"{name}: P(Y=1)={ve[1]:.6f}, max error={error:.2e}")

    # With X=1 and T=1, the posterior should equal the corresponding CPT row.
    np.testing.assert_allclose(
        variable_elimination({"X": 1, "T": 1}),
        [0.30, 0.70],
        atol=TOL,
        rtol=0,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "query", "evidence", "ve_p_y1", "clique_tree_p_y1",
            "max_abs_error", "tolerance",
        ])
        writer.writerows(rows)

    print(f"PASS: {len(rows)} queries, normalized factors, "
          "separator agreement, and T independent of (G, X)")
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()