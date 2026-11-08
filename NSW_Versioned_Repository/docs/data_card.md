# Data card — Dehejia–Wahba NSW experimental subset

**Project:** ICT 5143 AFGML Capstone, Problem 6  
**Documentation and local checksum verification:** 8 November 2026

## Source and provenance

The primary data are the Dehejia–Wahba RE74 experimental subset of the National Supported Work Demonstration, with one record per participant. The sample contains 445 participants: 185 historically assigned to training and 260 experimental controls. It is derived from the male NSW subsample. The source further subsets the experiment based on pre-intervention variables to include information on 1974 earnings. The project uses these two experimental files. The overlap and hidden-confounding experiments use separately generated simulation data.

- [Source documentation and dataset variants](https://users.nber.org/~rdehejia/data/.nswdata2.html)
- [Original data directory](https://users.nber.org/~rdehejia/data/)
- [Dehejia and Wahba (1999)](https://doi.org/10.1080/01621459.1999.10473858)

| Local path | Participants | SHA-256 of local source file |
|---|---:|---|
| `data/raw/nswre74_treated.txt` | 185 | `e7b742fe0ff07a0f45e129b4ff108bb9611cd83d53604732c48a8a0a3e20eda3` |
| `data/raw/nswre74_control.txt` | 260 | `a1364cea459d953dc691a667d99194b4ad335d6d550354fe23a5d2dc58d729b5` |

Acquire the original two text files from the source directory. Save the files under the listed paths and run `check_data.py`. The documented source supplies download access. An explicit reuse license was not identified on the source page reviewed. Keep the raw files local and submit source links, checksums, code, and aggregate outputs.

## Schema and usage

The input is a whitespace-delimited ten-column file with no header.

| Column order | Role |
|---|---|
| Treatment indicator | Historical assignment T. 1 is treated and 0 is control. |
| Age, education | Baseline years of age and education. |
| Black indicator, Hispanic indicator | Recorded binary fields used to construct race audit groups. |
| Married, no high-school degree | Baseline binary indicators. |
| RE74, RE75 | Baseline real earnings in 1974 and 1975. |
| RE78 | Observed real earnings in 1978. Used for training or evaluation according to the split. |

The loader checks arm labels, finite values, and expected file shape. All 445 loaded rows enter the empirical evaluation. Participant indices are derived from file order after concatenating treated and control records. The source files do not supply those indices as personal identifiers. The project uses five treatment-stratified outer folds, with 267 development, 89 validation, and 89 test participants per fold. Every participant appears once across pooled outer tests. Ridge standardization is fitted on the relevant training split. The earnings-transformation sensitivity uses asinh(RE78/1000) as its training target.

## Recorded demographics and support

Race groups are derived from the two recorded indicators. **Neither indicator recorded** means both indicators equal zero. It does not assert a more specific identity. Age is used as a continuous feature in some models and audited in two bands, under 25 and 25 or over. Race-by-age groups combine these fields. The code checks for overlapping positive race indicators.

| Pooled outer-test race group | Total | Historically treated | Historical control |
|---|---:|---:|---:|
| Black | 371 | 156 | 215 |
| Hispanic | 39 | 11 | 28 |
| Neither indicator recorded | 35 | 18 | 17 |

The project flags groups below 30 and reports treatment-arm support separately. With constant assignment weights within each arm, arm-specific Kish effective sample sizes equal the corresponding arm counts. See `results/metrics/nsw_subgroup_ess.csv`.

## Intended use and limitations

Use this dataset for a historical, experimental evaluation of job-training effects and hypothetical capacity-constrained allocation policies. Limited subgroup support and a historical male sample restrict generalization and prevent a gender fairness analysis. Treat each observed outcome as the realized outcome under historical assignment. Individual treatment effects and outcomes under the new allocation policy are unobserved. The binary RE78-positive outcome is a secondary diagnostic. It is separate from the continuous earnings outcome used to estimate incremental value.
