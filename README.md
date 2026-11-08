# Fair Allocation of Job Training under Uncertain Treatment Benefits

**AFGML Capstone | Problem 6**

| Student | Registration number |
|---|---|
| Akshay Wali | 261090830018 |
| Mohit Das | 261090840018 |

## Research question

Under a limited job-training budget, does requiring evidence of nonnegative incremental benefit for every audited race group change which allocation policies can be selected?

We compare an unconstrained policy, a policy that requires nonnegative estimated group benefits, and a policy that requires nonnegative lower confidence bounds on group benefits. The primary comparison uses a 40% target capacity. We also evaluate 20% and 60% capacity.

## Data and evaluation

The primary dataset is the Dehejia–Wahba National Supported Work (NSW) experimental subset. It contains 445 participants, including 185 assigned to training and 260 assigned to control. The outcome is real earnings in 1978 (`RE78`).

The evaluation uses five outer folds. Each fold has 267 development participants, 89 validation participants, and 89 test participants. Candidate rules are developed and selected before their corresponding outer-test outcomes are used for evaluation. Across the five outer-test folds, every participant is evaluated once. Policy value is estimated using doubly robust scores and is reported as incremental earnings per eligible participant.

## Main results

The experimental difference in mean earnings was **1,794.34**, with a 95% confidence interval of **[518.53, 3,132.21]**. Adjusted outcome regression estimated **1,676.34**, with a 95% interval of **[448.12, 2,997.58]**. Constant-propensity IPW reproduced the experimental difference because the analysis used the same assignment fraction for every participant.

### Policy selection at 40% capacity

| Method | Original folds with a feasible policy | Fold refits with a feasible policy | Complete five-fold refit repeats | Original outer-test value per eligible participant |
|---|---:|---:|---:|---:|
| Unconstrained | 5/5 | 500/500 | 100/100 | 1,074.67 |
| Point-estimate constraint | 2/5 | 158/500 | 0/100 | Unavailable |
| Lower-confidence-bound constraint | 0/5 | 0/500 | 0/100 | Unavailable |

The lower-confidence-bound rule selected no feasible candidate at 40% capacity under the tested policy class and benefit floor. The full-sample held-out value is therefore unavailable. The point-estimate rule selected candidates in two original folds, but only one fold met the 200-unit validation utility tolerance used in the matched-utility audit.

At 40% capacity, ranking by estimated treatment benefit instead of predicted post-training earnings improved estimated policy value by **394.98** per eligible participant. The paired 95% interval was **[−110.36, 856.59]**, which includes zero.

[Main NSW results figure](results/figures/nsw_main_results.pdf)

Figure note. NSW policy results. Panels B and D show feasibility. A zero bar indicates zero feasible selections. At 40% capacity, the lower-confidence-bound rule selected a feasible policy in 0 of 5 original outer folds and 0 of 500 development-sample fold refits. Its full-sample held-out policy value was unavailable. Panel C shows fixed-policy bootstrap intervals.

## Requirements-to-evidence matrix

Paths below are relative to the project root. The pipeline generates the outputs under `results/`.

| Analysis or requirement | Implementation | Output or verification |
|---|---|---|
| NSW sample and treatment-effect estimation | `check_data.py`, `experiment1_ate.py` | `results/metrics/ate_estimators.csv` |
| Graphical-model inference checks | `verify_inference.py` | `results/metrics/inference_checks.csv`. Six queries agreed between variable elimination and clique-tree inference. Maximum absolute discrepancy was \(5.55\times10^{-17}\). |
| Held-out baseline policy evaluation and ranking ablation | `experiment2_scores.py`, `experiment2_baselines.py` | `results/metrics/baseline_policy_values.csv`. The run log reports paired comparisons between benefit ranking and earnings ranking. |
| Allocation-rate and group-benefit audit | `experiment2_group_audit.py` | `results/metrics/policy_group_metrics.csv`, `results/metrics/policy_fairness_summary.csv` |
| Replace the lower bound with a point estimate and remove the group-benefit constraint | `experiment3_constraints.py` | `results/metrics/constraint_selections.csv`, `results/metrics/constraint_outer_summary.csv`. At 40%, the comparison identifies differences in feasibility. The lower-bound policy-value comparison is unavailable. |
| Matched validation utility and paired outer evaluation | `experiment3_comparison.py` | `results/metrics/constraint_matched_utility_audit.csv`, `results/metrics/constraint_paired_20pct.csv`. The paired outer comparison at 20% is separate from the matched-utility audit. |
| Known-effect policy simulation | `experiment4_simulation.py` | `results/metrics/simulation_summary.csv` |
| Overlap, propensity clipping, and hidden-confounding stress tests | `experiment5_overlap.py` | `results/metrics/overlap_simulation_summary.csv`. These are simulation results, reported separately from NSW estimates. |
| Transformed-earnings sensitivity | `experiment2_scores.py`, `experiment3_constraints.py` | `results/metrics/asinh_on_asinh/constraint_outer_summary.csv`, `results/metrics/asinh_on_raw/constraint_outer_summary.csv`. Selection files matched exactly across the two evaluation scales. |
| Training and selection variability | `experiment6_refitting.py` | `results/metrics/refitting/refitting_summary.csv`. Development data were resampled while validation and test participants were held fixed. |
| Outcome-conditioned fairness | `experiment7_outcome_fairness.py` | `results/metrics/outcome_fairness_summary.csv`, `results/metrics/outcome_fairness_coverage.csv`. Sparse denominators are flagged. |
| Predictive calibration and interval coverage | `experiment8_calibration.py` | `results/metrics/predictive_calibration_summary.csv`, `results/metrics/predictive_calibration_groups.csv`, `results/metrics/predictive_calibration_bins.csv` |
| Main results figure | `make_nsw_results_figure.py` | `results/figures/nsw_main_results.pdf`, `results/figures/nsw_main_results.png` |
| End-to-end clean reproduction | `run_all.ps1`, `requirements-lock.txt` | Successful fresh-environment run and exact SHA-256 matches for the four CSVs listed below. |

## Reproduce the analysis

The clean run was verified on Windows with PowerShell and Python 3.14. Place the original NSW experimental files at these paths:

```text
data/raw/nswre74_treated.txt
data/raw/nswre74_control.txt
```

From the project root, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements-lock.txt
& .\run_all.ps1
```

The success marker is `Full run completed`. If regenerating the figures on Windows, close any open copy of `nsw_main_results.pdf` first so Matplotlib can overwrite it.

### Clean reproduction record

We copied the source scripts, dependency lock, and two original NSW input files to a fresh directory with no generated results. We created a new virtual environment, installed the pinned dependencies, and ran the full pipeline. SHA-256 checks confirmed exact matches for:

- `results/metrics/ate_estimators.csv`
- `results/metrics/constraint_selections.csv`
- `results/metrics/constraint_outer_summary.csv`
- `results/metrics/refitting/refitting_summary.csv`

The clean run also regenerated the PNG and PDF figures. The hash comparison covered the four listed CSVs.

## Interpretation and limitations

The feasibility result applies to the candidate rules, audited groups, benefit floor, and uncertainty procedure tested here. It does not establish that every possible NSW allocation policy is infeasible. Sparse group denominators limit the interpretation of outcome-conditioned fairness gaps. The calibration audit evaluates a separate predictive earnings model, and the known-effect and hidden-confounding simulations provide controlled checks alongside the experimental NSW analysis.
