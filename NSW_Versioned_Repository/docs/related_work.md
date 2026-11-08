# Related work and restricted baseline

**ICT 5143 AFGML Capstone, Problem 6**  
**Team:** Akshay Wali and Mohit Das  
**Documentation date:** 8 November 2026

## Eight-paper comparison

The graphical-model column describes the causal representation relevant to each paper. A potential-outcomes formulation does not imply that the paper fits a graphical model.

| Study | Data or empirical setting | Identification assumptions and graphical representation | Fairness or decision criterion | Inference or learning | Limitation for this capstone | Source |
|---|---|---|---|---|---|---|
| LaLonde (1986), *Evaluating the Econometric Evaluations of Training Programs with Experimental Data* | NSW experimental job-training data and nonexperimental comparison samples | Randomized assignment anchors the experimental comparison. Observational estimates depend on their adjustment and selection assumptions. Evaluation design rather than a fitted graph. | Treatment-impact recovery against the experimental benchmark. | Compare experimental estimates with econometric estimators using alternative control samples and specifications. | Motivates the experimental benchmark and overlap diagnostics. It does not test group-benefit constraints. | [AER record](https://ideas.repec.org/a/aea/aecrev/v76y1986i4p604-20.html) |
| Dehejia and Wahba (1999), *Causal Effects in Nonexperimental Studies* | NSW participants with separate CPS and PSID comparison samples | Conditional comparability and overlap are central to propensity adjustment. The framework is expressed in potential outcomes. | Recover the impact of training for the treated against an experimental benchmark. | Propensity-score adjustment, including stratification and matching. | Provides dataset and comparison context. An adjusted impact estimate does not determine a fair allocation policy. | [Journal article PDF](https://users.nber.org/~rdehejia/papers/dehejia_wahba_jasa.pdf) |
| Kitagawa and Tetenov (2018), *Who Should Be Treated?* | National JTPA experimental application | Potential outcomes and identifiable treatment effects. The core result treats the propensity score as known. | Maximize population welfare within an admissible policy class, allowing budget restrictions. | Empirical welfare maximization with regret analysis. | Closely related capacity objective. It does not isolate finite-sample uncertainty in a minimum group-benefit constraint. | [Econometrica](https://doi.org/10.3982/ECTA13288) |
| Athey and Wager (2021), *Policy Learning with Observational Data* | California GAIN randomized evaluation and simulations including endogenous assignment | Identification depends on the available design, such as selection on observables or valid instruments. The method uses potential outcomes and design-specific scores. | Maximize policy welfare in a restricted class. Constraints can encode limits on cost or form. | Cross-fitted doubly robust scoring and welfare optimization with regret analysis. | Closest computational baseline. Our NSW implementation uses ridge outcome models, constant assignment propensity, a finite stump grid, and honest validation selection. | [Econometrica](https://doi.org/10.3982/ECTA15732) |
| Kim and Zubizarreta (2023), *Fair and Robust Estimation of Heterogeneous Treatment Effects for Policy Learning* | Simulations and COMPAS pretrial-release example | Potential-outcomes identification with measured covariates and regularity conditions for doubly robust estimation. | Fairness restrictions on effect estimates and their policy implications. The case study reports individual demographic parity and predictive bias measures. | Nonparametric constrained estimation and doubly robust learning. | Fairness is introduced at the effect-estimation stage. Our comparison changes the selection criterion while holding the underlying scores fixed. | [PMLR](https://proceedings.mlr.press/v202/kim23ab.html) |
| Viviano and Bradic (2024), *Fair Policy Targeting* | North American undergraduate entrepreneurship training and incubation quasi-experiment | Conditional treatment-effect and group-welfare identification under the paper's selection assumptions. Potential-outcomes representation. | Select a fair policy on a group-welfare Pareto frontier. | Estimate the frontier and solve a mixed-integer optimization problem. | Closest fairness comparator. Our rule uses an absolute benefit floor and a simultaneous sampling bound, rather than estimating a group-welfare frontier. | [JASA](https://doi.org/10.1080/01621459.2022.2142591) |
| Joshi, Zhang, and Bareinboim (2024), *Towards Safe Policy Learning under Partial Identifiability* | Synthetic data and International Stroke Trial data with induced selection bias | Causal graphs allow latent confounding and partially observed experiments. Identification bounds depend on the specified graph and available data. | Improve safely relative to a baseline policy under partial identification. | Sharp causal identification bounds and robust policy selection. | Their bounds address what the available data identify. Our NSW bounds address sampling uncertainty under randomized assignment assumptions. | [AAAI](https://doi.org/10.1609/aaai.v38i12.29198) |
| Kock and Preinerstorfer (2026), *Regularizing Fairness in Optimal Policy Learning with Distributional Targets* | Simulations, Pennsylvania reemployment bonus experiment, and entrepreneurship-program data | Potential-outcome distributions are learned under the paper's treatment assignment and support assumptions. | Penalize deviations between subgroup outcome distributions and the policy-induced overall distribution. | Empirical success policies with a fairness penalty and regret and consistency guarantees. | The penalty targets distributional disparity. Our floor targets each group's mean incremental benefit and permits infeasibility. | [Journal of Econometrics](https://doi.org/10.1016/j.jeconom.2026.106186), [working-paper details](https://arxiv.org/pdf/2401.17909) |

## Closest implemented baseline

The unconstrained arm of `experiment3_constraints.py` is a **restricted NSW adaptation of doubly robust empirical welfare maximization** as in Athey and Wager (2021). It retains the scoring and value-maximization principle. Viviano and Bradic are the closest conceptual comparison for fairness and are discussed as related work. The implementation does not reproduce their Pareto-frontier solver.

| Method component | Implemented NSW baseline |
|---|---|
| Effect score | `experiment2_scores.py` fits separate ridge outcome models by treatment arm and uses a constant assignment propensity. The score augments the estimated arm-mean difference with inverse-propensity-weighted observed residuals. Development scores are cross-fitted. |
| Policy class | `fit_stumps` considers age, education, RE74, and RE75. It uses the 33rd and 67th development percentiles and discards splits with fewer than 20 development observations in either leaf. Development scores determine the preferred leaf. |
| Budget | `allocate` ranks the preferred leaf first, resolves ties using a fixed seeded order, and fills floor(capacity × cohort size) places. This is a budgeted cohort allocation. |
| Objective | Within each fold and capacity, the unconstrained baseline selects the candidate with the largest mean of allocation times the validation doubly robust score. The group-benefit floor is disabled. The constrained methods use the same candidate class and objective. |
| Evaluation | The selected rule is frozen before test scores are read. The held-out CSV reports value per eligible participant and minimum estimated race-group benefit. |
| Scope of reproduction | This adapts the score-and-maximize principle to NSW, the finite stump grid, and a validation split. The paper's GAIN example, instrumental-variable simulation, broader nuisance-model choices, and theoretical guarantees are outside this reproduction. |

## Verification against the saved run

I independently checked all **15** unconstrained selections in `results/metrics/constraint_selections.csv` against `results/metrics/constraint_validation_candidates.csv`. In every fold-capacity pair, the recorded selected rule attained the highest recorded candidate validation value.

| Target capacity | Feasible outer folds | Held-out value per eligible participant | Minimum estimated race-group benefit |
|---:|---:|---:|---:|
| 20% | 5/5 | 648.25 | 112.57 |
| 40% | 5/5 | 1,074.67 | 88.80 |
| 60% | 5/5 | 1,351.22 | 149.26 |

Source: `results/metrics/constraint_outer_summary.csv`. To reproduce from the project root in a configured environment, run `& .\run_all.ps1`, or run `experiment2_scores.py` followed by `experiment3_constraints.py` with the default arguments. The feasibility and welfare comparison is interpreted within the tested class. The primary LCB comparison has no full-sample held-out policy value.

## Evidence-matrix entries

| Requirement | Evidence | Status |
|---|---|---|
| Proposal and falsifiable contribution | `docs/proposal.md` and `results/metrics/simulation_summary.csv` | Documented retrospectively from the verified implementation. |
| Eight-paper related-work table | `docs/related_work.md`, Eight-paper comparison | Complete in these files. |
| Closest-method baseline | `experiment2_scores.py`, `experiment3_constraints.py`, and the three constraint CSVs described above | Restricted adaptation documented. All 15 selections verified against the saved validation candidates. |

