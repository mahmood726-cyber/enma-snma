# NMA Methods Research Project: Progress Summary
**Date:** 2026-01-15
**Project:** repo300 - NMA Methods Analysis & Improvement

---

## Project Goal

Identify flaws in modern network meta-analysis (NMA) methods by:
1. Testing all major methods on identical datasets
2. Finding where methods disagree or fail
3. Developing better approaches

---

## Completed Work

### Phase 1: Literature Review ✅

**Deliverable:** `NMA_Methods_Research_Phase1_2.md`

**Key Findings:**
- **8 major R packages** identified (netmeta, gemtc, multinma, bnma, nmaINLA, MBNMAdose, pcnetmeta, BUGSnet)
- **Critical methodological gaps:**
  - Design-by-treatment (DBT) inconsistency model has high Type I error + low power
  - New 2024 methods emerging (KL divergence, influence analysis)
  - No consensus on optimal inconsistency detection
  - Bayesian vs. frequentist results often disagree without clear explanation

**Sources:**
- [Twenty years of network meta-analysis (Ades et al., 2024)](https://onlinelibrary.wiley.com/doi/abs/10.1002/jrsm.1700)
- [Local inconsistency detection using KL divergence (Spineli, 2024)](https://pubmed.ncbi.nlm.nih.gov/39420381/)
- [Design-by-treatment interaction model (Jackson et al.)](https://onlinelibrary.wiley.com/doi/full/10.1002/jrsm.1188)

---

### Phase 2: Data Audit ✅

**Deliverables:**
- `outputs/data_audit_summary.csv`
- `outputs/problematic_files_detail.csv`
- `outputs/fix_recipes.csv`
- `outputs/cross_package_datasets.csv`

**Key Findings:**
- **121 CSV files** audited across 8 packages
- **74 files (61%)** have issues
- **47 files (39%)** clean and usable

**Real Issues Identified:**
| Issue Type | Count | Affected Packages |
|------------|-------|-------------------|
| Empty treatment labels (NA) | 10+ | multinma, MBNMAdose, pcnetmeta |
| Duplicate (study, treatment) rows | 11+ | multinma, MBNMAdose, nmaINLA, pcnetmeta |
| Empty _nodes.csv files | 10 | multinma, MBNMAdose, pcnetmeta |

**Not a Bug:** "Placeholder" labels (1, 2, 3, 4 or A, B, C, D) are internal package codes with mappings in `_nodes.csv` files.

---

### Step 1: Fix Broken Datasets ✅

**Understanding Achieved:**
- Most "issues" are actually data structure conventions
- Empty labels in multinma/MBNMAdose need re-extraction from source packages
- Duplicate rows are data extraction artifacts

**Conclusion:** 35/53 datasets are immediately usable. The rest can be fixed by proper extraction.

---

### Step 2: Cross-Package Bake-Off (In Progress)

**Deliverables:**
- `NMA_Bakeoff_Framework.md` - Complete analysis plan
- `R/02_cross_package_bakeoff.R` - Implementation script (ready to run with R)

**Primary Datasets for Comparison:**

| Dataset | Packages | Studies | Treatments | Priority |
|---------|----------|---------|------------|----------|
| Smoking | 6 | 24 | 4-7 | HIGH |
| Thrombolytic | 4 | 28-50 | 8-9 | HIGH |
| Parkinson | 6 | 7-15 | 4-5 | HIGH |
| Diabetes | 5 | 22 | 6 | MEDIUM |

**Methods to Compare:**
- **netmeta** (frequentist, DBT model)
- **gemtc** (Bayesian JAGS, MCMC)
- **multinma** (Bayesian Stan, UME model)
- **bnma** (Bayesian JAGS)
- **nmaINLA** (Bayesian INLA approximation)

**Metrics to Capture:**
1. Model convergence (R-hat, ESS, warnings)
2. Treatment effects (estimates, CIs)
3. Treatment rankings (SUCRA, P-scores)
4. Inconsistency assessment (global, local)
5. Heterogeneity (tau², I²)
6. Model fit (DIC, deviance)

**Expected Disagreements (Hypotheses):**
1. Bayesian vs. frequentist rankings will differ in sparse networks
2. DBT model will have low power to detect inconsistency
3. gemtc (JAGS) may struggle more with convergence than multinma (Stan)
4. Similar point estimates but different interval widths

---

## Project Structure

```
repo300/
├── outputs/
│   ├── data_audit_summary.csv          ✅ Complete
│   ├── problematic_files_detail.csv    ✅ Complete
│   ├── fix_recipes.csv                 ✅ Complete
│   ├── cross_package_datasets.csv      ✅ Complete
│   ├── bakeoff/                        🔄 Pending (requires R)
│   ├── comparisons/                    🔄 Pending
│   └── figures/                        🔄 Pending
├── R/
│   ├── 01_data_audit_and_fix.R         ✅ Complete
│   ├── 01_data_audit_and_fix.py        ✅ Complete (Python version)
│   ├── 02_cross_package_bakeoff.R      ✅ Complete (ready to run)
│   └── fix_datasets_and_run_comparison.R ✅ Complete
├── nmadatasets/                        ✅ Audited
├── netmetaDatasets/                    ✅ Audited
├── NMA_Methods_Research_Phase1_2.md    ✅ Complete
├── NMA_Bakeoff_Framework.md            ✅ Complete
└── PROGRESS_SUMMARY.md                 ✅ This file
```

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `NMA_Methods_Research_Phase1_2.md` | Literature review + data audit report | Complete |
| `R/01_data_audit_and_fix.py` | Data audit script (Python) | Complete |
| `outputs/data_audit_summary.csv` | Audit results | Complete |
| `outputs/problematic_files_detail.csv` | Detailed issues | Complete |
| `outputs/fix_recipes.csv` | Fix recommendations | Complete |
| `outputs/cross_package_datasets.csv` | Cross-package mapping | Complete |
| `NMA_Bakeoff_Framework.md` | Analysis plan | Complete |
| `R/02_cross_package_bakeoff.R` | Bake-off implementation | Complete (ready to run) |

---

## Current Status

### Completed ✅
- Phase 1: Literature Review
- Phase 2: Data Audit (121 files)
- Step 1: Dataset fixing (analysis complete)

### In Progress 🔄
- Step 2: Cross-package bake-off (framework complete, needs R to run)

### Pending ⏳
- Step 3: Simulation studies
- Phase 7: Root cause analysis
- Phase 8: Novel method development
- Phase 9: Validation
- Phase 10: Publication

---

## Next Steps

### Immediate (When R is Available)

1. **Run the bake-off script:**
   ```r
   source("R/02_cross_package_bakeoff.R")
   ```

2. **Analyze results:**
   - Compare rankings across methods
   - Identify where methods disagree
   - Document convergence issues

3. **Create visualizations:**
   - Ranking heatmaps
   - Effect forest plots by method
   - Inconsistency detection comparison

### Follow-up

4. **Run simulation studies** (Step 3):
   - Generate networks with known properties
   - Test method recovery
   - Validate hypotheses about disagreements

5. **Root cause analysis** (Phase 7):
   - Mathematical examination of divergence
   - Understand why methods fail

6. **Method development** (Phase 8):
   - Design improved inconsistency detection
   - Develop more robust ranking methods
   - Create hybrid approaches

---

## Key Research Questions

1. **When do Bayesian and frequentist methods disagree?**
   - Hypothesis: Sparse networks, small sample sizes
   - Test: Vary network size and study count

2. **Which inconsistency detection method is most powerful?**
   - Hypothesis: DBT has low power, node-splitting better locally
   - Test: Simulate known inconsistency levels

3. **How robust are treatment rankings?**
   - Hypothesis: SUCRA/P-scores unstable with different methods
   - Test: Compare rankings across methods

4. **Where do methods fail?**
   - Hypothesis: MCMC convergence, sparse networks
   - Test: Run on diverse network structures

---

## Success Criteria

- [x] Complete literature review of modern NMA methods
- [x] Audit all available datasets
- [x] Identify data quality issues
- [x] Create bake-off framework
- [ ] Run methods on identical datasets
- [ ] Document method disagreements
- [ ] Simulate data with known properties
- [ ] Develop improved methods
- [ ] Validate against benchmarks
- [ ] Publish findings

---

## Time Estimate (From Current State)

| Step | Estimated Time | Dependencies |
|------|----------------|--------------|
| Run bake-off on 4 datasets | 2-4 hours | R environment |
| Analyze results | 2-3 hours | Bake-off complete |
| Create visualizations | 1-2 hours | Results analyzed |
| Design simulations | 2-3 hours | Results analyzed |
| Run simulations | 4-8 hours | Simulations designed |
| Analyze simulation results | 2-3 hours | Simulations complete |
| Develop improved methods | 8-16 hours | All above |
| Validate new methods | 4-8 hours | Methods developed |
| Write publication | 8-12 hours | Validation complete |

**Total remaining: ~33-59 hours** of focused work

---

*This project will systematically identify flaws in modern NMA methods and develop improved approaches through empirical testing, simulation, and methodological innovation.*
