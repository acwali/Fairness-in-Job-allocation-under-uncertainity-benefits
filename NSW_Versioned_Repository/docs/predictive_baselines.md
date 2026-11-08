# Predictive baselines — Problem 6

## Requirement and evidence

| Required component | Implementation | Evidence |
|---|---|---|
| Ridge earnings regression | Existing separate-arm ridge in `experiment2_scores.py`, reused in `experiment2_predictive_baselines.py` | `results/metrics/predictive_baselines.csv` |
| Shallow tree earnings regression | Depth-two squared-error regression tree with a minimum of 20 training participants per leaf in `experiment2_predictive_baselines.py` | `results/metrics/predictive_baselines.csv` and `results/metrics/predictive_baselines_paired.csv` |
| Policy ranking by predicted post-training earnings | Existing `experiment2_baselines.py` ranks by the ridge model's estimated earnings under training, m1. It fills the available places within each fold. | Rows named `Predicted post-training earnings` in `results/metrics/baseline_policy_values.csv` |

The post-training earnings ranking policy has results at all three capacities. Its held-out estimated value at 40% target capacity is 546.17 earnings units per eligible participant, with 175 places across the five test folds. That value estimates the incremental effect of the allocation policy. MAE and RMSE assess predictive error on observed earnings.

## Held-out earnings comparison

Both models use the same eight baseline columns, the same arm-specific training participants, and the same five held-out NSW folds. The script reconstructs the original test-fold membership and verifies both ridge predictions against the saved out-of-fold scores for all 445 participants. Observed earnings are compared with the prediction under each participant's observed historical assignment. Metrics are in original RE78 earnings units.

| Model | Held-out n | MAE | RMSE |
|---|---:|---:|---:|
| Ridge | 445 | 4,912.74 | 6,807.66 |
| Shallow regression tree | 445 | 4,880.91 | 6,805.01 |

The paired difference (tree minus ridge) was -31.83 for MAE (95% interval -158.73 to 85.97) and -2.65 for RMSE (95% interval -135.84 to 130.95). Both intervals include zero. They use 2,000 paired participant bootstrap draws within test-fold and treatment strata, conditional on the fitted models. These intervals describe evaluation uncertainty and do not include model refitting.

## Install and reproduce

Extract the ZIP into the project root. Merge the `docs` and `results` folders with the existing folders. The included `run_all.ps1` adds the new step immediately after the raw earnings scoring step. If you have edited your local runner, add `Invoke-ProjectPython experiment2_predictive_baselines.py` immediately after its first `Invoke-ProjectPython experiment2_scores.py` line instead.

With the raw NSW inputs, locked environment, and raw outer-test scores already present, the new comparison can be run on its own:

```powershell
.\.venv\Scripts\python.exe experiment2_predictive_baselines.py
```

The script writes aggregate metrics by fold and treatment arm plus pooled paired intervals. The ZIP contains no NSW participant data. No additional package is required.

