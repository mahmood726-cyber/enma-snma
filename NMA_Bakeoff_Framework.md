# NMA Methods Research: Cross-Package Bake-Off Framework
**Step 2: Cross-Package Method Comparison**
**Date:** 2026-01-15

---

## Executive Summary

This document outlines the framework for comparing NMA methods across different R packages using identical datasets. The goal is to identify when and why methods disagree.

---

## Data Audit Results Summary

| Metric | Value |
|--------|-------|
| Total CSV files audited | 121 |
| Files with issues | 74 (61%) |
| Files OK | 47 (39%) |
| Cross-package datasets | 15 |

### Key Finding: "Placeholder" Labels Are Not Bugs

The audit flagged many datasets with "placeholder treatment labels" (1, 2, 3, 4 or A, B, C, D). **These are NOT bugs** - they are internal codes used by the packages. The actual treatment names are in the `_nodes.csv` files.

### Real Issues Found

1. **Empty labels (NA values)**: multinma, MBNMAdose, pcnetmeta packages
2. **Duplicate (study, treatment) rows**: Multiple packages
3. **Empty _nodes.csv files**: multinma, MBNMAdose, pcnetmeta

---

## Cross-Package Datasets Identified

| Dataset | Files | Packages | Usability | Notes |
|---------|-------|----------|-----------|-------|
| **Smoking** | 11 | bnma, gemtc, multinma, nmaINLA, netmeta, BUGSnet | HIGH | Best for comparison |
| **Thrombolytic** | 9 | bnma, gemtc, BUGSnet, multinma | HIGH | 9 treatments, 50 studies |
| **Parkinson** | 16 | bnma, gemtc, multinma, nmaINLA, netmeta, BUGSnet | HIGH | 5 treatments |
| **Diabetes** | 11 | BUGSnet, gemtc, multinma, nmaINLA, pcnetmeta | MEDIUM | Some data quality issues |
| **Dietary Fat** | 9 | gemtc, multinma, nmaINLA, netmeta, pcnetmeta | MEDIUM | 2 treatments only |
| **Blocker** | 7 | bnma, gemtc, multinma | MEDIUM | Beta-blockers for MI |
| **Statins** | 4 | bnma, multinma | MEDIUM | 2 treatments only |

---

## Bake-Off Design

### Primary Datasets for Comparison

#### 1. Smoking Cessation (Best Candidate)
- **Outcome**: Abstinence at ≥6 months
- **Design**: Binary arm-based
- **Treatments**: 4-7 depending on package
- **Studies**: 24
- **Why best**: Exists in 6 packages with consistent data

#### 2. Thrombolytic Therapy
- **Outcome**: Mortality/Stroke
- **Design**: Binary arm-based
- **Treatments**: 8-9
- **Studies**: 28-50
- **Why good**: Larger network, exists in 4 packages

#### 3. Parkinson's Disease
- **Outcome**: UPDRS score change (continuous)
- **Design**: Continuous outcome
- **Treatments**: 4-5
- **Studies**: 7-15
- **Why good**: Tests continuous outcomes

---

## Methods to Compare

| Package | Framework | Key Features | Inconsistency Detection |
|---------|-----------|--------------|------------------------|
| **netmeta** | Frequentist | Fast, no MCMC | Design-by-treatment, node-splitting |
| **gemtc** | Bayesian (JAGS) | MCMC sampling | Design-by-treatment |
| **multinma** | Bayesian (Stan) | IPD + AgD, UME | UME inconsistency model |
| **bnma** | Bayesian (JAGS) | Network meta-analysis | Basic inconsistency checks |
| **nmaINLA** | Bayesian (INLA) | Fast approximation | Design-by-treatment |

---

## Comparison Metrics

For each dataset-method combination, capture:

### 1. Model Convergence
- MCMC convergence diagnostics (R-hat, effective sample size)
- Warnings or errors
- Runtime

### 2. Treatment Effects
- Point estimates for each treatment comparison
- Confidence/credible intervals
- Standard errors

### 3. Treatment Rankings
- SUCRA scores (Bayesian)
- P-scores (frequentist)
- Rank probabilities

### 4. Inconsistency Assessment
- Global inconsistency p-value (DBT model)
- Local inconsistency (node-splitting)
- Inconsistency variance estimate

### 5. Heterogeneity
- Between-study variance (tau²)
- Heterogeneity statistics (I², Q)

### 6. Model Fit
- Deviance Information Criterion (DIC)
- Residual deviance
- Posterior predictive checks

---

## Expected Disagreements (Hypotheses)

### Hypothesis 1: Bayesian vs. Frequentist Rankings
**Expected**: SUCRA vs. P-score rankings will differ in sparse networks
**Mechanism**: Shrinkage priors in Bayesian methods

### Hypothesis 2: Inconsistency Detection
**Expected**: DBT model will have low power; node-splitting may detect different inconsistencies
**Mechanism**: Different statistical power and null hypotheses

### Hypothesis 3: MCMC Convergence Issues
**Expected**: gemtc (JAGS) may struggle more than multinma (Stan)
**Mechanism**: Different sampling algorithms

### Hypothesis 4: Treatment Effect Estimates
**Expected**: Similar point estimates but different interval widths
**Mechanism**: Frequentist vs. Bayesian uncertainty quantification

---

## Analysis Plan

### Step 1: Data Preparation
```r
# Load datasets from each package
smoking_netmeta <- read.csv("netmetaDatasets/inst/extdata/smoking_cessation_2013.csv")
smoking_gemtc <- load_from_gemtc("smoking")
# ... etc

# Harmonize to common format
smoking_unified <- unify_format(smoking_netmeta, smoking_gemtc, ...)
```

### Step 2: Run Each Method
```r
# netmeta
netmeta_result <- netmeta::netmeta(smoking_data)

# gemtc
gemtc_result <- gemtc::mtc.model(smoking_network)

# multinma
multinma_result <- multinma::nma(smoking_data, consistency = "ume")

# ... etc
```

### Step 3: Extract Comparison Metrics
```r
comparison <- data.frame(
  method = c("netmeta", "gemtc", "multinma", ...),
  runtime = ...,
  sucra_A = ..., sucra_B = ...,
  inconsistency_p = ...,
  tau_squared = ...
)
```

### Step 4: Compare Results
- Rank correlation between methods
- Plot treatment effects forest plot by method
- Compare inconsistency detection results
- Analyze convergence patterns

### Step 5: Identify Problem Cases
- Where do rankings disagree most?
- Which methods fail to converge?
- Where are treatment effects most different?

---

## Simulation Study Design (Step 3)

### Generate Networks with Known Properties

1. **Consistent networks**: Direct and indirect evidence agree
2. **Inconsistent networks**: Known violations of consistency
3. **Sparse networks**: Few studies, disconnected components
4. **Star networks**: All studies compare vs. common control
5. **Loop networks**: Many closed loops

### Vary:
- Number of treatments (3, 5, 10)
- Number of studies (10, 30, 100)
- Between-study heterogeneity (low, medium, high)
- Inconsistency magnitude (none, small, large)

### Test:
- Method recovery of true treatment effects
- Power to detect inconsistency
- Type I error rates
- Ranking accuracy

---

## Output Structure

```
outputs/
├── bakeoff/
│   ├── smoking/
│   │   ├── netmeta_results.rds
│   │   ├── gemtc_results.rds
│   │   ├── multinma_results.rds
│   │   └── comparison_summary.csv
│   ├── thrombolytic/
│   └── parkinson/
├── comparisons/
│   ├── rankings_comparison.csv
│   ├── treatment_effects_comparison.csv
│   └── inconsistency_comparison.csv
└── figures/
    ├── ranking_heatmap.png
    ├── effects_forest_by_method.png
    └── inconsistency_detection.png
```

---

## Success Criteria

1. **Method convergence**: All methods run successfully on ≥3 datasets
2. **Reproducibility**: Results can be replicated with same data
3. **Identified disagreements**: Clear documentation of where methods differ
4. **Root cause understanding**: Explain WHY methods disagree
5. **Simulation validation**: Controlled testing confirms hypotheses

---

## Next Steps

1. ✅ Data audit complete
2. ⏳ Create unified data format for cross-package loading
3. ⏳ Implement bake-off script in R
4. ⏳ Run bake-off on Smoking dataset first
5. ⏳ Analyze results and document disagreements
6. ⏳ Expand to Thrombolytic and Parkinson datasets
7. ⏳ Design simulation studies based on findings

---

## Key Questions to Answer

1. **When do Bayesian and frequentist methods disagree?**
   - Sample size?
   - Network sparsity?
   - Heterogeneity level?

2. **Which inconsistency detection method is most powerful?**
   - DBT vs. node-splitting vs. UME?
   - Local vs. global assessment?

3. **How robust are treatment rankings?**
   - Do SUCRA/P-scores change with different methods?
   - Which method is most reliable for decision-making?

4. **Where do methods fail?**
   - Convergence issues?
   - Computational time?
   - Error messages?

---

*This framework will guide the systematic comparison of NMA methods to identify flaws and develop better approaches.*
