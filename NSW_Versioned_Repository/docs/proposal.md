# Research proposal — Fair Allocation of Job Training under Uncertain Treatment Benefits

**ICT 5143 AFGML Capstone, Problem 6**  
**Team:** Akshay Wali (261090830018) and Mohit Das (261090840018)  
**Documentation date:** 8 November 2026

This document reconstructs the design from the completed implementation and recorded results. The contribution statement below describes a testable hypothesis. Its wording is retrospective.

## Research question and contribution

At fixed training capacity, how does requiring statistical evidence of nonnegative group benefit change which policies can be selected, their estimated program value, and access to training?

**Falsifiable contribution claim.** In the specified known-effect simulation at 40% capacity and a fixed group-benefit floor, replacing point-estimate constraints with simultaneous lower confidence bounds reduces the proportion of generated datasets in which the selected policy violates the true group floor when the minority sample contains 20 or 60 observations.

This claim would fail in a scenario if the lower-bound rule selected a floor-violating policy at least as often as the point-estimate rule. Because a method can avoid violations by declining to select a policy, evaluate violation frequency jointly with selection frequency, violations conditional on selection, zero-allocation frequency, and regret. At minority sample size 200, compare whether the empirical gap narrows. The comparison addresses a specific finite-sample mechanism within a restricted class of policies.

## Data and estimands

The primary data are the Dehejia–Wahba experimental NSW subset, with 185 participants assigned to training and 260 to control. The outcome is real 1978 earnings. Historical assignment identifies effects under randomization, consistency, positivity, and no interference. The causal graph uses baseline covariates and treatment as parents of earnings, with assignment independent of baseline covariates under the experimental design. Define a hypothetical allocation as D = 1 and keep it separate from historical treatment T.

- **Utility:** mean incremental earnings per eligible participant, including zero contribution from people who are not allocated a place.
- **Group benefit:** the same incremental value conditional on a group. The main constraint applies to recorded race/ethnicity groups. Age and race-by-age intersections support descriptive audits, with sparse cells flagged.
- **Access:** allocation rates, gaps, and ratios are reported separately. A zero benefit floor can be met by allocating no places to a group.
- **Scope:** NSW data are historical and male-only. Individual treatment effects are unobserved. Overlap and hidden confounding are studied using a separate simulator.

## Planned comparison as implemented

Use five outer folds. Each fold separates development (267 people), validation (89), and test (89). Cross-fitted doubly robust development scores inform a small class of stumps. Select a rule using validation scores and evaluate the frozen choice on the outer test fold. The same candidate class supports three selections: unconstrained value maximization, a point-estimate benefit floor, and a simultaneous lower-confidence-bound floor. Examine 20%, 40%, and 60% capacity. Include random, equal-rate, predicted-earnings and estimated-benefit allocations as contextual comparators.

The primary empirical capacity is 40% and the empirical floor is zero. The matched-utility diagnostic uses a 200-earnings-unit validation tolerance. A candidate meeting the floor in one fold gives evidence for that fold only. Report a full-sample held-out value as unavailable when the selected method does not furnish policies across the required folds. Keep fixed-policy uncertainty and development-sample refitting variability separate.

## How the simulation tests the claim

The simulator keeps the target population mix, four stratum-specific treatment effects, a nine-policy candidate grid, and the 40% budget fixed. It varies minority sample size (20, 60, 200), keeps the majority sample at 400, and uses 500 randomized datasets per minority-size setting. The same draws and candidate grid are used for all methods and both floors (0 and 100). The simulation uses simultaneous one-sided Gaussian bounds with known noise variance. The NSW implementation instead uses approximate simultaneous bootstrap bounds. The oracle value is 440 earnings units per eligible person for the capacity-only and fair candidate optima in both floor scenarios.

| Minority n and floor | Point-estimate selections and violations | Lower-bound selections and violations | Access or feasibility qualification |
|---|---|---|---|
| 20, floor 0 | 500 selected, 9 violations | 432 selected, 0 violations | 94.21% of selected lower-bound policies allocated zero places to at least one group. |
| 60, floor 0 | 500 selected, 1 violation | 449 selected, 0 violations | 70.16% of selected lower-bound policies allocated zero places to at least one group. |
| 20, floor 100 | 439 selected, 21 violations | 15 selected, 0 violations | The positive floor ruled out zero-allocation solutions. The lower-bound method failed to select on 485 datasets. |
| 60, floor 100 | 484 selected, 4 violations | 65 selected, 0 violations | The lower-bound method failed to select on 435 datasets. |
| 200, both floors | Zero violations at either floor | Zero violations at either floor | No observed violation-rate advantage at this sample size. |

These results support the stated simulation claim in the tested small-group settings. They also show that reduced violations can coexist with restricted access or frequent infeasibility. At 40% capacity in NSW, the lower-bound method selected a feasible policy in 0 of 5 original folds and 0 of 500 development-sample fold refits. Held-out value was unavailable, leaving the real-data value and worst-group improvement comparison unresolved.

## Evidence and reproduction

From the project root, run `& .\run_all.ps1` after installing the locked dependencies and placing the NSW input files. The claim uses `experiment4_simulation.py` and `results/metrics/simulation_summary.csv`. The NSW result uses `results/metrics/constraint_outer_summary.csv` and `results/metrics/refitting/refitting_summary.csv`. See [related_work.md](related_work.md) for the literature comparison and restricted baseline mapping.

