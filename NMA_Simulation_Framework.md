# NMA Methods Research: Simulation Study Framework
**Step 3: Simulation Studies with Known Ground Truth**
**Date:** 2026-01-15

---

## Purpose

Generate synthetic network meta-analysis data with **known properties** to:
1. Test which methods recover true treatment effects
2. Measure Type I error rates for inconsistency detection
3. Assess power to detect real inconsistencies
4. Evaluate ranking accuracy (SUCRA/P-score)
5. Identify when and why methods fail

---

## Simulation Design Factors

### Factor 1: Network Structure

| Structure | Description | Studies | Treatments | Edge Density |
|-----------|-------------|---------|------------|--------------|
| **Star** | All studies compare vs. common control | 30 | 5 | High (100% connected to A) |
| **Loop** | Closed loops, multiple comparisons | 30 | 5 | Medium |
| **Sparse** | Few connections, disconnected components | 30 | 5 | Low |
| **Dense** | Many comparisons, well-connected | 30 | 5 | High |
| **Scale-free** | Hub treatments with many connections | 30 | 5 | Variable |

### Factor 2: Sample Size

| Level | Studies | Arms per Study | Total Arms |
|-------|---------|----------------|------------|
| **Small** | 10 | 2-3 | 20-30 |
| **Medium** | 30 | 2-4 | 60-120 |
| **Large** | 100 | 2-5 | 200-500 |

### Factor 3: Between-Study Heterogeneity

| Level | Tau² | I² | Interpretation |
|-------|-----|-----|----------------|
| **Low** | 0.01 | 25% | Minimal heterogeneity |
| **Medium** | 0.04 | 50% | Moderate heterogeneity |
| **High** | 0.16 | 75% | Substantial heterogeneity |

### Factor 4: Inconsistency

| Level | Description | Magnitude | Expected Impact |
|-------|-------------|-----------|-----------------|
| **None** | Consistent network | 0 | Methods should agree |
| **Small** | Minor loop inconsistency | 0.1 log-OR | Hard to detect |
| **Medium** | Moderate inconsistency | 0.3 log-OR | Detectable by good methods |
| **Large** | Severe inconsistency | 0.5 log-OR | All methods should detect |

### Factor 5: Outcome Type

| Type | Distribution | Link Function |
|------|--------------|---------------|
| **Binary** | Binomial | Logit (log-OR) |
| **Continuous** | Normal | Identity (MD) |
| **Count** | Poisson | Log (log-Rate) |

---

## Data Generation Process

### Step 1: Define Network Structure

```
1. Specify number of treatments (T)
2. Specify number of studies (N)
3. Generate study arm counts (2-5 arms per study)
4. Assign treatment pairs to studies
5. Create study-treatment incidence matrix
```

### Step 2: Generate True Treatment Effects

```
1. Set reference treatment (A) effect = 0
2. Generate true effects d_AB, d_AC, d_AD, ... from N(μ, σ²)
3. Ensure transitivity: d_AD = d_AB + d_BD (for consistent networks)
4. For inconsistent networks: Add inconsistency to specific loops
```

### Step 3: Generate Study-Level Effects

```
For each study i and treatment j:
  θ_ij = true_effect_j + δ_i

where δ_i ~ N(0, τ²) is random study effect
```

### Step 4: Generate Outcome Data

**Binary outcomes:**
```
For each arm (study i, treatment j):
  n_ij = sample size (from specified distribution)
  p_ij = inv_logit(θ_ij + baseline)
  r_ij ~ Binomial(n_ij, p_ij)
```

**Continuous outcomes:**
```
For each arm (study i, treatment j):
  n_ij = sample size
  μ_ij = θ_ij + baseline
  y_ij ~ N(μ_ij, σ²)  # σ² is within-study variance
```

### Step 5: Add Inconsistency (if specified)

```
For each loop with inconsistency:
  - Identify loops in network (e.g., A-B-C-A)
  - Add inconsistency parameter to one comparison
  - Ensure inconsistency propagates correctly
```

---

## Simulation Scenarios

### Scenario 1: Baseline Performance
- **Purpose:** Establish how methods perform under ideal conditions
- **Design:** Dense network, medium sample size, low heterogeneity, no inconsistency
- **Expected:** All methods should recover true effects

### Scenario 2: Sparse Network Challenge
- **Purpose:** Test robustness to limited data
- **Design:** Sparse network, small sample size, medium heterogeneity
- **Expected:** Bayesian methods may shrink more; rankings unstable

### Scenario 3: Inconsistency Detection Power
- **Purpose:** Compare inconsistency detection methods
- **Design:** Vary inconsistency magnitude (none, small, medium, large)
- **Expected:** DBT has low power for small inconsistencies

### Scenario 4: Heterogeneity Impact
- **Purpose:** Test how heterogeneity affects rankings
- **Design:** Vary tau² (low, medium, high) with no inconsistency
- **Expected:** Higher heterogeneity → less stable rankings

### Scenario 5: Network Structure Effects
- **Purpose:** Compare star vs. loop networks
- **Design:** Same treatments/studies, different connectivity
- **Expected:** Loop networks better for inconsistency detection

### Scenario 6: Sample Size Effects
- **Purpose:** Determine minimum sample size requirements
- **Design:** Vary total arms (20, 60, 200, 500)
- **Expected:** Larger samples → better convergence, narrower CIs

---

## Evaluation Metrics

### 1. Treatment Effect Recovery

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Bias** | mean(θ̂ - θ_true) | Systematic over/under-estimation |
| **RMSE** | sqrt(mean((θ̂ - θ_true)²)) | Overall error magnitude |
| **Coverage** | P(θ_true ∈ CI) | CI calibration (target: 95%) |
| **Width** | mean(CI_upper - CI_lower) | Precision of estimates |

### 2. Treatment Ranking Accuracy

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Rank Correlation** | cor(rank_true, rank_estimated) | Agreement in ordering |
| **Top-Ranked Correct** | I(top_treatment_true == top_treatment_est) | Best treatment identified |
| **Mean Absolute Rank Error** | mean(\|rank_true - rank_est\|) | Average ranking error |
| **SUCRA Correlation** | cor(SUCRA_true, SUCRA_estimated) | SUCRA accuracy |

### 3. Inconsistency Detection

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Type I Error** | P(reject_consistency \| no_inconsistency) | False positive rate (target: 5%) |
| **Power** | P(reject_consistency \| inconsistency_present) | True positive rate |
| **False Discovery Rate** | P(no_inconsistency \| reject_consistency) | Proportion of false positives |
| **AUC** | ROC curve area | Overall detection accuracy |

### 4. Model Performance

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Convergence Rate** | P(R-hat < 1.05) | MCMC convergence success |
| **Runtime** | seconds | Computational efficiency |
| **DIC / AIC** | Information criterion | Model fit (lower is better) |
| **Posterior Predictive P-value** | PPP | Model fit calibration |

---

## Statistical Power Analysis

### Required Sample Sizes for Inconsistency Detection

Based on preliminary calculations:

| Inconsistency Size | Studies Needed (80% power) |
|--------------------|---------------------------|
| Small (0.1 log-OR) | 100+ |
| Medium (0.3 log-OR) | 30-50 |
| Large (0.5 log-OR) | 15-20 |

### Required Sample Sizes for Treatment Effect Estimation

| Target Precision | Standard Error | Total Arms Needed |
|------------------|----------------|-------------------|
| ±0.1 log-OR | 0.05 | 200+ |
| ±0.2 log-OR | 0.10 | 50-100 |
| ±0.3 log-OR | 0.15 | 20-50 |

---

## Implementation Plan

### Phase 1: Core Simulation Engine (Python)
```python
class NMASimulator:
    - generate_network()
    - generate_true_effects()
    - generate_study_data()
    - add_inconsistency()
    - export_data()
```

### Phase 2: Method Testing Interface
```python
class MethodTester:
    - run_netmeta()
    - run_gemtc()
    - run_multinma()
    - extract_results()
    - compute_metrics()
```

### Phase 3: Batch Experiments
```python
def run_simulation_study():
    for scenario in scenarios:
        for rep in range(n_reps):
            data = simulator.generate()
            results = tester.run_all_methods(data)
            evaluator.compute_metrics(results)
```

### Phase 4: Analysis & Visualization
```python
def analyze_results():
    - bias_by_method_scenarios()
    - power_curves()
    - coverage_plots()
    - ranking_accuracy_heatmaps()
    - convergence_rates()
```

---

## Output Structure

```
outputs/
├── simulations/
│   ├── data/
│   │   ├── scenario1_rep001.csv
│   │   ├── scenario1_rep002.csv
│   │   └── ...
│   ├── results/
│   │   ├── scenario1_summary.csv
│   │   ├── scenario2_summary.csv
│   │   └── ...
│   └── figures/
│       ├── bias_by_method.png
│       ├── power_curves.png
│       ├── coverage_plots.png
│       └── ranking_accuracy.png
```

---

## Success Criteria

1. **Data Generation:** Valid NMA data with correct properties
2. **Reproducibility:** Same seed → same results
3. **Validation:** Generated data matches target properties
4. **Benchmarking:** Clear method performance rankings
5. **Insight:** Understanding of when methods fail

---

## Expected Findings (Hypotheses)

### Hypothesis 1: DBT Model Power
- **Prediction:** DBT model will have <50% power to detect small inconsistencies
- **Test:** Vary inconsistency magnitude, measure rejection rate
- **Implication:** Need more powerful inconsistency detection

### Hypothesis 2: Ranking Instability
- **Prediction:** Treatment rankings will be unstable with small sample sizes
- **Test:** Correlate ranking accuracy with sample size
- **Implication:** SUCRA/P-scores should not be used alone for decision-making

### Hypothesis 3: Bayesian Shrinkage
- **Prediction:** Bayesian methods will shrink estimates more in sparse networks
- **Test:** Compare Bayesian vs. frequentist CI widths
- **Implication:** Choice of prior matters in sparse networks

### Hypothesis 4: MCMC Convergence
- **Prediction:** gemtc (JAGS) will have more convergence issues than multinma (Stan)
- **Test:** Compare R-hat distributions across methods
- **Implication:** Stan may be more reliable for complex networks

### Hypothesis 5: Inconsistency Detection
- **Prediction:** Node-splitting will have better power for local inconsistencies
- **Test:** Compare DBT vs. node-splitting power curves
- **Implication:** Use multiple inconsistency detection methods

---

## Next Steps

1. ✅ Design simulation framework
2. ⏳ Implement core simulation engine (Python)
3. ⏳ Implement data generation functions
4. ⏳ Run pilot simulations (10 reps per scenario)
5. ⏳ Validate generated data properties
6. ⏳ Scale to full simulation study (1000 reps)
7. ⏳ Analyze results and visualize
8. ⏳ Document method performance
9. ⏳ Identify method improvements
10. ⏳ Publish findings

---

*This simulation framework will provide rigorous evidence about NMA method performance and identify concrete areas for improvement.*
