# Model card — Capacity-constrained job-training allocation

**Project:** ICT 5143 AFGML Capstone, Problem 6  
**Team:** Akshay Wali and Mohit Das  
**Scope:** Historical research evaluation of hypothetical allocations on the 445-person experimental NSW subset.

## Models and outputs

Separate ridge outcome regressions predict RE78 under historical control and training. The post-training earnings baseline ranks by the training prediction; the benefit baseline ranks by the difference between the two predictions. The policy-value evaluator uses doubly robust scores with a constant historical assignment propensity equal to the experimental sample fraction, 185/445. Historical assignment and observed RE78 enter evaluation scores. Prospective allocation decisions use pretreatment inputs and cohort capacity.

The constrained policy class comprises development-fitted stumps using age, education, RE74, or RE75. The preferred leaf is filled first and remaining ties use the fixed ranking in code. Validation selects the highest estimated value among candidates passing the relevant point-estimate or simultaneous lower-bound floor. The unconstrained comparator uses the same candidates and capacity. An infeasible fold produces no selected constrained policy and no substitute test estimate. The shallow regression tree is a separate earnings prediction baseline. A zero-plus-lognormal model provides separate predictive calibration diagnostics.

## Recorded race and age by stage

| Method | Recorded race at prediction or allocation time | Recorded age at prediction or allocation time | Other uses |
|---|---|---|---|
| Random allocation | No | No | Race and age can be used for reporting. |
| Ridge earnings model and the ridge-based earnings and benefit rankings | Yes. Black and Hispanic indicators are input columns. | Yes. Raw age is an input column. | Historical assignment determines the observed-arm prediction during predictive evaluation. The hypothetical ranking uses modeled outcomes. |
| Equal race allocation-rate rule | Yes. The rule sets race-group quotas and uses ridge benefit scores within each group. | Yes, through the ridge benefit score used for within-group ranking. | Age and intersections are also audited. |
| Unconstrained, point-estimate-floor, and lower-bound-floor allocation stumps | No. The final stump ranks using one feature from age, education, RE74, or RE75. | Only if the chosen stump splits on age. | Point-estimate and lower-bound selection use race groups on validation data. The unconstrained objective does not apply a race floor. All three use development and validation doubly robust scores, whose ridge nuisance models use race and age. |
| Depth-two earnings regression tree | Race indicators are available split features. A fitted tree uses them only if it selects a split on them. | Raw age is available and used if selected for a split. | Predictive comparison only. |
| Zero-plus-lognormal earnings calibration model | Yes. The indicator columns are supplied. | Yes. Raw age is supplied. | A separate predictive diagnostic. It does not generate the allocation rankings. |

**Verified feature use in the saved run.** The Black indicator appeared in all five fitted control-arm regression trees and in none of the treated-arm trees. The Hispanic indicator appeared in none of the ten fitted trees. Age appeared in one control-arm tree and three treated-arm trees. Across the three capacity settings, age was the chosen split for 8 of 15 unconstrained selections and 3 of 9 point-estimate selections. The lower-bound variant had no selected stump.

The ATE methods are estimators rather than allocation policies. Adjusted OLS uses the eight baseline covariates, including recorded race and age. The unadjusted experimental difference and constant-propensity IPW use no race or age inputs.

## Primary fairness criterion and rationale

The primary metric is **minimum estimated race-group incremental earnings per eligible group member**. For group g, the target is E[D × (Y(1) − Y(0)) ∣ G = g]. It credits additional earnings attributable to the proposed allocation and includes everyone eligible in the group, including people receiving no place. The minimum targets the group with the smallest estimated gain. A population mean alone could hide that group's outcome. The validation floor is zero. The lower-bound variant requires evidence that each group's incremental benefit reaches that floor, within the tested candidates and assumptions.

Equal allocation rates measure access. They can coexist with unequal gains if treatment effects differ. Conversely, a zero group-benefit floor may be met by allocating no places to a group, so allocation gaps, selection ratios, subgroup support, and zero allocations are reported as separate diagnostics. Age and race-by-age audits are descriptive. The main benefit-floor constraint applies to recorded race groups.

## Evaluation and limitations

Five outer folds isolate the test outcomes from policy selection. Predictive baselines use the same test participants and raw earnings scale. Pooled ridge MAE/RMSE were 4,912.74/6,807.66 and shallow tree MAE/RMSE were 4,880.91/6,805.01. Both paired intervals included zero. The 40% lower-bound policy was infeasible in all five original folds and 500 development-sample fold refits. Its full-sample held-out value was unavailable.

Use the models to compare research policies under the documented assumptions and capacity. Small subgroups, historical covariates, the male-only sample, and uncertainty in conditional benefit estimates limit application to other populations or current job programs. The analysis does not establish individual treatment effects or justify live allocation decisions. See [data_card.md](data_card.md), [causal_diagram.md](causal_diagram.md), and [protocol.md](protocol.md).
