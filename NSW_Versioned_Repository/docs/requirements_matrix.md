# AFGML Problem 6 requirements-to-evidence matrix

**Status convention.** Complete means evidence exists for the stated item. Partial means a qualifier or deliverable remains. Unavailable means the protocol produced no estimate. The report and defence references below are section or frame titles in the current LaTeX sources. Some evidence belongs in repository documentation and has no slide location.

| ID | Requirement | Evidence and result | Status | Report or defence location |
|---|---|---|---|---|
| C01 | Team, problem and bounded contribution | README, docs/proposal.md | Complete | Report title and Research question and contribution |
| C02 | Original proposal and timing | docs/proposal.md | Partial. Retrospective proposal. Earlier submission timing unverified. | Research question and contribution |
| C03 | Eight-paper literature comparison | docs/related_work.md | Complete | Report References, full comparison in repository |
| C04 | Closest method and restricted reproduction | docs/related_work.md, experiment3_constraints.py, results/metrics/constraint_selections.csv | Complete as a restricted implementation | Methods and experiments |
| C05 | Data version, origin, selection, schema, demographic meanings and hashes | data/README.md, docs/data_card.md, configs/frozen_run.json | Complete for documented provenance. Source data reuse terms remain unverified. | Data and causal model |
| C06 | Data card and model card | docs/data_card.md, docs/model_card.md | Complete | Data and causal model, full cards in repository |
| C07 | Causal diagram, factorization and adjustment assumptions | docs/causal_diagram.md, docs/assumptions.md, results/figures/nsw_causal_dag.png | Complete. Empirical and simulated DAGs distinguished. | Data and causal model, diagram in repository |
| C08 | Leakage prevention and honest participant splits | experiment2_scores.py, experiment3_constraints.py | Complete for implemented splits and selection order. Original protocol timing unverified. | Methods and experiments |
| C09 | Comparable baselines and protected inputs | docs/model_card.md, docs/predictive_baselines.md | Complete. Equal-rate and score-based policies have different group-input needs, documented explicitly. | Methods and experiments |
| C10 | Repeated runs and refitting | experiment4_simulation.py, experiment5_overlap.py, experiment6_refitting.py | Complete. Five seeds, 100 refits in total with five fold refits per repeat. | Results |
| C11 | Paired uncertainty and small groups | results/metrics/constraint_paired_20pct.csv, results/metrics/predictive_baselines_paired.csv, results/metrics/outcome_fairness_groups.csv, results/metrics/nsw_subgroup_ess.csv | Complete for available contrasts and denominators. The 40% lower-bound contrast is unavailable. | Results and Limitations |
| C12 | Primary metrics, utility tolerance and preregistration | docs/protocol.md | Partial. RMSE, minimum race-group benefit and the 200-unit tolerance are documented retrospectively. Preregistration unverified. | Results, full protocol in repository |
| C13 | Fairness–utility curve and matched utility | results/figures/fairness_utility_frontier_40pct.pdf, results/metrics/fairness_utility_matched_summary.csv | Complete for validation. At 40%, point estimate 1/5, lower bound 0/5. | Results, frontier in repository |
| C14 | Multiplicity and confirmatory claim | docs/protocol.md | Partial. Current analyses are exploratory. Holm is specified for a future independent evaluation. | Limitations, protocol in repository |
| C15 | Factor checks and exact VE/clique-tree agreement | verify_inference.py, results/metrics/inference_checks.csv | Complete. Six queries, maximum discrepancy 5.55e-17 against tolerance 1e-8. | Robustness and reproducibility |
| C16 | Causal safeguards and real/simulation separation | docs/assumptions.md, docs/causal_diagram.md, experiment5_overlap.py | Complete for the implemented analyses. | Data and causal model, Robustness and reproducibility |
| C17 | DP, EOpp, EOdds and selection-rate ratio | results/metrics/policy_fairness_summary.csv, results/metrics/outcome_fairness_summary.csv | Complete for the audited policies and defined denominators. | Methods and experiments, full metrics in repository |
| C18 | Versioned source and pinned environment | Git history, requirements-lock.txt, configs/frozen_run.json, run_all.ps1 | Complete in the versioned bundle. | Robustness and reproducibility |
| C19 | Acquisition, provenance, logs and artifact manifest | data/README.md, provenance.py, results/manifest.csv, results/logs/run_all.log | Complete for the isolated versioned rerun. | Robustness and reproducibility |
| C20 | Data privacy and code licensing | .gitignore, docs/reproducibility.md | Partial. Raw and participant-level files excluded. Code-license choice pending. | Repository documentation |
| C21 | Report, manuscript and reproducibility appendix | AFGML_Report.tex, docs/reproducibility.md | Partial. Short evaluation source present. Compiled PDF and any separately required longer manuscript remain unverified. | Report |
| C22 | Defence presentation and demo | AFGML_Defence.tex, results/logs/run_all.log | Partial. Slide source and run trace available. Compiled defence, demo instructions and oral delivery unverified. | Defence |
| C23 | Individual contributions and peer cross-checks | Team confirmation required | Missing from this snapshot | Add to report and repository |
| C24 | Dedicated regression tests | verify_inference.py, inline split and data assertions, full-run log | Partial. Smoke and runtime assertions exist. No dedicated automated test suite. | Robustness and reproducibility |
| P6-E1 | Experimental ATE, outcome regression and IPW | results/metrics/ate_estimators.csv | Complete | Results |
| P6-E2 | Honest policy fitting and held-out doubly robust evaluation | experiment2_scores.py, experiment3_constraints.py | Complete | Methods and experiments |
| P6-E3 | Allocation parity, point-estimate floor and uncertainty-aware floor | policy_fairness_summary.csv, constraint_outer_summary.csv in results/metrics | Complete as an attempted experiment. 40% lower-bound policy value unavailable. | Results, Feasibility and held-out value at 40% capacity |
| P6-E4 | Heterogeneous-effect simulation, minority sizes and oracle | results/metrics/simulation_summary.csv, docs/proposal.md | Complete. Report selection, true violations, and zero-allocation frequency jointly. | Robustness and reproducibility, detailed simulation in repository |
| P6-E5 | Simulated selection and overlap diagnostics | results/metrics/overlap_simulation_summary.csv | Complete. Simulated subgroup ESS, bias, RMSE and balance. | Robustness and reproducibility |
| P6-B1 | Ridge and shallow earnings tree on the same folds | results/metrics/predictive_baselines.csv, predictive_baselines_paired.csv | Complete. 445 held-out participants, MAE and RMSE. | Repository predictive-baseline evidence |
| P6-B2 | Predicted post-training earnings policy | results/metrics/baseline_policy_values.csv | Complete at three capacities. | Results, Ablations and reproducibility |
| P6-B3 | Causal outcome model and unconstrained adjusted policy | experiment2_scores.py, experiment3_constraints.py, docs/related_work.md | Complete for the restricted benchmark. | Data and causal model, Methods and experiments |
| P6-B4 | Random, equal-rate and point-estimate fairness comparators | results/metrics/policy_fairness_summary.csv, constraint_outer_summary.csv | Complete. Report infeasible folds for the point rule. | Methods and experiments, Results |
| P6-A1 | Replace lower bounds with point estimates | results/metrics/constraint_selections.csv | Complete. 40% point rule feasible 2/5, lower-bound rule 0/5. | Ablations and reproducibility |
| P6-A2 | Remove the group-benefit constraint | results/metrics/constraint_outer_summary.csv | Complete. 40% unconstrained feasible 5/5. | Ablations and reproducibility |
| P6-A3 | Predicted-outcome versus estimated-benefit ranking | experiment2_baselines.py, results/logs/run_all.log | Complete. Paired intervals printed at all capacities. | Results, Ablations and reproducibility |
| P6-R1 | 20%, 40%, and 60% capacities | results/metrics/constraint_outer_summary.csv | Complete | Methods and experiments |
| P6-R2 | Propensity clipping | results/metrics/overlap_simulation_summary.csv | Complete in overlap simulations. | Robustness and reproducibility |
| P6-R3 | Alternative earnings transformation | results/metrics/asinh_on_asinh and asinh_on_raw | Complete. Same transformed-trained choices evaluated on both scales. | Robustness and reproducibility |
| P6-R4 | Unmeasured confounding sensitivity | results/metrics/overlap_simulation_summary.csv | Complete in separate simulations. | Robustness and reproducibility |
| P6-M1 | Overall policy value and gain over random | results/metrics/baseline_policy_values.csv | Complete for evaluated baselines. | Results |
| P6-M2 | Allocation gap, minimum group value, benefit range and uncertainty | results/metrics/policy_fairness_summary.csv, policy_group_metrics.csv | Complete for audited baselines. Full lower-bound policy value unavailable. | Results, Limitations |
| P6-M3 | Log score, interval coverage and propensity calibration when estimated | results/metrics/predictive_calibration_summary.csv | Complete for earnings prediction. Propensity calibration not applicable to the fixed NSW propensity or known simulated assignment models. | Repository predictive-calibration evidence |
| P6-M4 | Subgroup effective sample sizes | results/metrics/nsw_subgroup_ess.csv, overlap_simulation_summary.csv | Complete as design-weight support. | Repository subgroup evidence |
| P6-I1 | Interpretability and invalid post-treatment adjustment | docs/causal_diagram.md, docs/model_card.md | Complete for the implemented design. | Data and causal model |
| P6-I2 | Ethics and limitations | docs/model_card.md, docs/protocol.md | Partial. Access, benefit and uncertainty discussed. A fuller stakeholder discussion of historical earnings as a proxy is still needed. | Limitations |
| P6-O1 | Optional observational comparison sample or IV extension | Simulated overlap route selected | N/A. Neither optional extension was required or claimed. | Robustness and reproducibility |
