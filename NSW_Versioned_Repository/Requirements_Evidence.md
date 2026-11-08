# Requirements-to-evidence matrix


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

## Main result at 40% capacity

NSW policy results. Panels B and D show feasibility. A zero bar indicates zero feasible selections. At 40% capacity, the lower-confidence-bound rule selected a feasible policy in 0 of 5 original outer folds and 0 of 500 development-sample fold refits. Its full-sample held-out policy value was unavailable. Panel C shows fixed-policy bootstrap intervals.
