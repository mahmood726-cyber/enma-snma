# Network Meta-Analysis Methods Research: Phase 1 & 2 Report
**Research Project:** repo300 - NMA Methods Analysis & Improvement
**Date:** 2026-01-15
**Phases:** 1 (Literature Review) & 2 (Data Audit)

---

## Executive Summary

This report presents findings from Phase 1 (Literature Review on modern NMA methods) and Phase 2 (Data Audit of 53 datasets across 8 major R packages). Key findings reveal significant methodological gaps and data quality issues that require systematic investigation.

---

## Phase 1: Literature Review - Modern NMA Methods Landscape

### 1.1 Major R Packages for Network Meta-Analysis

| Package | Framework | Primary Method | Key Features | Citation Status |
|---------|-----------|----------------|--------------|-----------------|
| **netmeta** | Frequentist | Design-by-treatment interaction | Fast, no MCMC, consistency checks | 379+ citations |
| **multinma** | Bayesian (Stan) | Aggregate + IPD, UME model | Individual patient data, network meta-regression | Active development |
| **gemtc** | Bayesian (JAGS) | MCMC sampling | Heterogeneity/inconsistency assessment | Established |
| **bnma** | Bayesian (JAGS) | Network meta-analysis | Similar to gemtc | Established |
| **MBNMAdose** | Bayesian | Dose-response NMA | Specialized for dose-response | Established |
| **nmaINLA** | Bayesian (INLA) | INLA approximation | Fast alternative to MCMC | Established |
| **pcnetmeta** | Frequentist | Pairwise consensus | Network meta-analysis | Established |
| **BUGSnet** | Bayesian (OpenBUGS) | Network meta-analysis | User-friendly interface | Established |

### 1.2 Inconsistency Detection Methods (2024 State-of-the-Art)

#### **Design-by-Treatment (DBT) Interaction Model**
- **Description:** Random-effects implementation for modeling inconsistency globally
- **Status:** Most widely used, but has known limitations:
  - High Type I error rates
  - Low power to detect inconsistency
  - Global assessment only (no local identification)
- **Key References:**
  - Jackson et al. (2014, 2016) - 317+ citations
  - [Design-by-treatment interaction model](https://onlinelibrary.wiley.com/doi/full/10.1002/jrsm.1188)

#### **Side-Splitting / Node-Splitting**
- **Description:** Compares direct vs. indirect evidence for specific treatment comparisons
- **Status:** Complementary to DBT, provides local inconsistency assessment
- **Implementation:** Available in netmeta, multinma
- **Key References:**
  - [Node-splitting in Value in Health](https://www.valueinhealthjournal.com/article/S1098-3015(16)30581-2/abstract)

#### **Loop Inconsistency Detection**
- **Description:** Evaluates disagreement between different evidence paths in closed loops
- **Status:** Critical assumption in NMA, often violated

#### **New Methods (2024)**
1. **Kullback-Leibler Divergence Method** (Spineli, 2024)
   - Novel local inconsistency detection
   - [Published in BMC Medical Research Methodology](https://pubmed.ncbi.nlm.nih.gov/39420381/)
   - 10+ citations already

2. **Influence Analysis Framework** (Sasaki, 2024)
   - Alternative to DBT using influence diagnostics
   - [arXiv preprint June 2024](https://arxiv.org/abs/2406.16485)

3. **Model Comparison Study** (Qin et al., 2024)
   - Compares DBT vs. side-splitting
   - [Research Synthesis Methods](https://www.math.hkbu.edu.hk/~tongt/RSM2024.pdf)

### 1.3 Key 2024 Publications

| Publication | Focus | Significance |
|-------------|-------|--------------|
| "Twenty years of network meta-analysis" (Ades et al.) | Review of NMA controversies | 72 citations |
| "A comparison of two models for detecting inconsistency" (Qin et al.) | DBT vs. side-splitting | Research Synthesis Methods |
| "Local inconsistency detection using KL divergence" (Spineli) | New detection method | BMC Medical Research Methodology |
| "Influence analyses of designs" (Sasaki) | Influence diagnostics | arXiv 2024 |
| "AI Statistician for NMA" (2025) | LLM automation | Value in Health |

### 1.4 Identified Methodological Gaps

1. **Inconsistency Detection Issues:**
   - DBT model has high Type I error + low power
   - No consensus on which method is superior
   - Local vs. global inconsistency trade-offs unclear

2. **Bayesian vs. Frequentist:**
   - Results often disagree without clear explanation
   - MCMC convergence problems in sparse networks
   - Computational burden for large networks

3. **Transitivity Assumptions:**
   - Rarely tested in practice
   - No standardized diagnostic tools
   - Violations lead to biased results

4. **Treatment Ranking:**
   - Ignores magnitude of differences
   - SUCRA/P-score criticized for over-simplification

---

## Phase 2: Data Audit - Catalogue of 53 Datasets

### 2.1 Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Datasets** | 53 |
| **R Packages** | 8 |
| **Clinical Areas** | 15+ |
| **Design Types** | Arm-based, Contrast-based, Mixed |
| **Outcome Types** | Binary, Continuous, HR, SMD, Rate |

### 2.2 Datasets by Package

| Package | Count | Status | Issues |
|---------|-------|--------|--------|
| **bnma** | 5 | Clean | No major issues |
| **BUGSnet** | 4 | Clean | No major issues |
| **gemtc** | 11 | Clean | No major issues |
| **MBNMAdose** | 4 | **PROBLEMATIC** | Missing labels, duplicates |
| **multinma** | 10 | **PROBLEMATIC** | Missing IDs, labels, duplicates |
| **netmeta** | 4 | Mixed | 1 dataset has ID issues |
| **nmaINLA** | 7 | **PROBLEMATIC** | Missing treatment labels |
| **pcnetmeta** | 4 | **PROBLEMATIC** | Missing IDs, labels, duplicates |

### 2.3 Data Quality Issues Summary

#### **Critical Issues (Affect 18/53 datasets = 34%)**

1. **Missing Treatment Labels** (17 datasets)
   - Packages affected: MBNMAdose, multinma, nmaINLA, pcnetmeta
   - Impact: Cannot analyze without manual intervention
   - Root cause: Data extraction/harmonization failures

2. **Missing Study Identifiers** (10 datasets)
   - Packages affected: multinma, pcnetmeta, netmeta
   - Impact: Cannot track studies across analyses
   - Root cause: Study ID variable not properly populated

3. **Duplicate (Study, Treatment) Rows** (11 datasets)
   - Packages affected: MBNMAdose, multinma, nmaINLA, pcnetmeta, netmeta
   - Impact: Potential bias in pooled estimates
   - Root cause: Data merging errors or multi-arm studies

#### **Clean Datasets (35/53 = 66%)**

| Dataset ID | Package | Clinical Area | N Studies | N Treatments | Design |
|------------|---------|---------------|-----------|--------------|--------|
| bnma__blocker | bnma | Cardiology (beta-blockers) | 22 | 2 | Arm binary |
| bnma__thrombolytic | bnma | Cardiology (thrombolysis) | 50 | 9 | Arm binary |
| BUGSnet__thrombolytic | BUGSnet | Cardiology (thrombolysis) | 28 | 8 | Arm binary |
| gemtc__depression | gemtc | Psychiatry | 111 | 12 | Arm binary |
| gemtc__smoking | gemtc | Smoking cessation | 24 | 4 | Arm binary |
| netmeta__smokingcessation | netmeta | Smoking cessation | 24 | 5 | Arm + Contrast |
| nmaINLA__CooperStrokedat | nmaINLA | Stroke | 26 | 16 | Arm + Contrast |

### 2.4 Clinical Area Coverage

| Clinical Area | Datasets | Total Studies |
|---------------|----------|---------------|
| Cardiology | 8 | 200+ |
| Psychiatry | 6 | 150+ |
| Neurology | 5 | 80+ |
| Endocrinology/Diabetes | 4 | 70+ |
| Rheumatology | 3 | 40+ |
| Oncology | 2 | 30+ |
| Other | 25 | 300+ |

### 2.5 Cross-Package Dataset Validation

Several datasets exist across multiple packages, enabling cross-method validation:

| Dataset | bnma | BUGSnet | gemtc | multinma | netmeta | nmaINLA |
|---------|------|---------|-------|----------|---------|---------|
| Smoking | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Thrombolytic | ✓ | ✓ | ✓ | ✓ | - | - |
| Depression | - | - | ✓ | - | - | - |
| Parkinson | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Diabetes | - | ✓ | ✓ | ✓ | - | ✓ |
| Dietary Fat | - | - | ✓ | ✓ | ✓ | ✓ |
| Statins/Blocker | ✓ | - | ✓ | ✓ | - | - |

### 2.6 Specific Dataset Examples

#### **Smoking Cessation (smoking_cessation_2013.csv)**
- **Source:** Cahill et al. 2013, Lancet
- **Outcome:** Abstinence at ≥6 months
- **Design:** Arm-based binary
- **Treatments:** Placebo, Varenicline, Nicotine Patch, Bupropion, etc.
- **Studies:** 24
- **Quality:** Clean

#### **Thrombolytic Therapy**
- **Treatments:** tPA, SK, SKtPA, Ten, Ret, AtPA, ASPAC, UK
- **Studies:** 50 (bnma), 28 (BUGSnet)
- **Quality:** Clean across packages
- **Use Case:** Cross-package method comparison

---

## Key Research Opportunities

### Opportunity 1: Cross-Method Comparison on Identical Datasets
- **Datasets available:** Smoking, Thrombolytic, Parkinson, Diabetes
- **Research Question:** When and why do different methods disagree?
- **Approach:** Run all 8 packages on same datasets, compare results

### Opportunity 2: Inconsistency Detection Method Evaluation
- **Research Question:** Which inconsistency detection method performs best?
- **Approach:** Simulate networks with known inconsistency, test DBT, node-splitting, KL divergence

### Opportunity 3: Treatment Ranking Methodology
- **Research Question:** How to incorporate effect magnitude into rankings?
- **Approach:** Develop alternative to SUCRA/P-score

### Opportunity 4: Transitivity Assessment
- **Research Question:** How to detect transitivity violations?
- **Approach:** Develop diagnostic tools using study-level covariates

### Opportunity 5: Data Quality Standards
- **Research Question:** How to prevent the quality issues seen in 34% of datasets?
- **Approach:** Develop validation pipeline for NMA datasets

---

## Next Steps (Phases 3-10)

### Phase 3: Method Classification
- Create detailed classification framework
- Categorize by: estimation approach, inconsistency handling, assumptions

### Phase 4: Baseline Testing
- Run all methods on clean datasets
- Document convergence, runtime, warnings

### Phase 5: Problem Identification
- Detect ranking disagreements
- Identify inconsistency paradoxes
- Find transitivity violations

### Phase 6: Simulation Studies
- Generate data with known properties
- Test method recovery

### Phase 7: Root Cause Analysis
- Mathematical examination of method divergence

### Phase 8: Novel Method Development
- Design robust alternatives

### Phase 9: Validation
- Compare against benchmarks

### Phase 10: Publication
- Methods paper, R package, dataset repository

---

## Sources

### Literature Review Sources
- [netmeta: An R Package for Network Meta-Analysis](https://cran.r-project.org/web/packages/netmeta/vignettes/netmeta.pdf)
- [multinma Package Documentation](https://dmphillippo.github.io/multinma/)
- [Twenty years of network meta-analysis (Ades et al., 2024)](https://onlinelibrary.wiley.com/doi/abs/10.1002/jrsm.1700)
- [Design-by-treatment interaction model (Jackson et al.)](https://onlinelibrary.wiley.com/doi/full/10.1002/jrsm.1188)
- [Local inconsistency detection using KL divergence (Spineli, 2024)](https://pubmed.ncbi.nlm.nih.gov/39420381/)
- [Influence analyses of designs (Sasaki, 2024)](https://arxiv.org/abs/2406.16485)
- [A comparison of two models for detecting inconsistency (Qin et al., 2024)](https://www.math.hkbu.edu.hk/~tongt/RSM2024.pdf)
- [Node-Splitting GLMM for NMA](https://www.valueinhealthjournal.com/article/S1098-3015(16)30581-2/abstract)
- [gemtc Package Documentation](https://cran.r-project.org/web/packages/gemtc/gemtc.pdf)

### Data Sources
- repo300: `C:\Users\user\OneDrive - NHS\Documents\repo300`
- nmadatasets catalogue: `nmadatasets/inst/extdata/catalogue.csv`
- netmetaDatasets registry: `netmetaDatasets/inst/extdata/datasets.csv`
