# Statistical protocol and fairness–utility evidence

## Completed NSW analysis

This record was written after the NSW results were inspected. The primary
predictive metric for reporting is held-out RMSE in original RE78 earnings
units. MAE is secondary. The primary fairness metric is the minimum estimated
incremental earnings per eligible member across the recorded race groups.
Overall utility is incremental earnings per eligible participant.

The main setting is 40% target capacity, raw earnings, and a zero benefit
floor. The existing validation audit uses a 200-earnings-unit loss tolerance
relative to the unconstrained maximum within each fold. At 40%, the
point-estimate rule matched that tolerance in 1 of 5 folds. The lower-bound
rule matched in 0 of 5. Its full-sample held-out value was unavailable.

The frontier shows validation candidates and their trade-off between utility
loss and worst-group benefit. It does not use test outcomes. Existing paired
bootstrap intervals and feasibility results are exploratory. The current
record does not support a preregistered confirmatory family or a retrospective
Holm-adjusted significance claim.

## Prospective multiplicity plan

Before inspecting outcomes in an independent evaluation sample, register the
frozen 40% policies, group definitions, endpoints, and resampling procedure.
For the lower-bound policy versus the unconstrained policy, prespecify two
one-sided tests: improvement in worst-group benefit and overall utility
noninferiority with a margin of 200 earnings units per eligible participant.
Apply Holm at familywise alpha 0.05 and require both tests to pass for the
joint claim. If a policy cannot be selected or evaluated, report the comparison
as unavailable. Do not substitute a new endpoint after observing outcomes.

## Effective sample size

Report raw counts and Kish IPW effective sample size by race, age, and
race-by-age group for validation and test folds. Treated weights are 1/p and
control weights are 1/(1-p), using p = 185/445. Because weights are constant
within each arm, arm-specific ESS equals that arm's raw count. Combined ESS
may be lower. This diagnostic describes design-weight support and does not
estimate the effective sample size of the doubly robust policy-value estimator.

## Evidence

- results/figures/fairness_utility_frontier_40pct.pdf
- results/metrics/fairness_utility_frontier.csv
- results/metrics/fairness_utility_matched_summary.csv
- results/metrics/nsw_subgroup_ess.csv
