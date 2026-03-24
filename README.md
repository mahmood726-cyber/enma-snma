# E-NMA & S-NMA: Novel Methods for Network Meta-Analysis

Two world-first methods for inconsistency-robust evidence synthesis in network meta-analysis (NMA), developed as part of a systematic evaluation of 8 NMA R packages across 121 curated datasets.

## Methods

### Ensemble Network Meta-Analysis (E-NMA)

E-NMA resolves the "diagnostic disagreement" problem in NMA inconsistency detection. When different tests (Design-by-Treatment, node-splitting, KL divergence) give conflicting results, E-NMA synthesizes them into a single framework:

1. **Diagnostic Execution** -- Runs three complementary inconsistency detection methods: KL divergence, Local-Global Hybrid (with Bonferroni correction), and Bootstrap validation
2. **Consensus Mapping** -- Computes an Inconsistency Confidence Score (ICS) per treatment comparison edge: the fraction of methods that flag it
3. **Robust Synthesis** -- Inflates the variance of inconsistent comparisons by `se' = se * (1 + omega * ICS)`, then solves the NMA via weighted least squares

Key property: when all methods agree the network is consistent (ICS = 0 everywhere), E-NMA produces identical results to standard NMA.

### Spectral Network Meta-Analysis (S-NMA)

S-NMA applies graph signal processing to NMA. It treats the evidence network as a weighted graph and analyses the "frequency" content of the treatment effect signal:

1. **Graph Laplacian** -- Builds `L = D - W` where edge weights are evidence precision
2. **Eigen-decomposition** -- Computes `L = U * Lambda * U^T` to get graph "frequencies" (eigenvalues) and "harmonics" (eigenvectors)
3. **Graph Fourier Transform** -- Projects the treatment effect signal into spectral domain: `s_hat = U^T * s`
4. **Inconsistency Detection** -- Measures the high-frequency energy ratio. Consistent networks have smooth (low-frequency) signals; inconsistency creates high-frequency "spikes"
5. **Edge Localization** -- Maps spectral peaks back to specific edges using eigenvector analysis

Key property: runs in O(T^3) for T treatments (milliseconds for typical NMA), vs. minutes/hours for MCMC-based methods.

## Simulation Results (100 replications per scenario)

| Scenario | Method | RMSE | Coverage | Bias | Rank r |
|----------|--------|------|----------|------|--------|
| Baseline | Standard NMA | 0.076 (0.029) | 92.5% | 0.002 | 0.92 |
| Baseline | E-NMA | 0.079 (0.030) | 94.0% | 0.004 | 0.90 |
| Sparse | Standard NMA | 0.190 (0.084) | 94.8% | -0.044 | 0.61 |
| Sparse | E-NMA | 0.198 (0.089) | 97.0% | -0.045 | 0.60 |
| Inconsistency 0.3 | Standard NMA | 0.150 (0.046) | 72.3% | 0.050 | 0.78 |
| Inconsistency 0.3 | E-NMA | 0.152 (0.047) | 74.0% | 0.050 | 0.78 |
| High heterogeneity | Standard NMA | 0.082 (0.038) | 88.5% | 0.002 | 0.91 |
| High heterogeneity | E-NMA | 0.082 (0.040) | 90.3% | 0.001 | 0.90 |
| Star | Standard/E-NMA | 0.097 (0.040) | 95.3% | 0.000 | 0.78 |

Key finding: E-NMA consistently improves coverage by 1.5--2.2 percentage points across all scenarios where inconsistency or uncertainty is present, without substantially increasing RMSE. S-NMA produces identical point estimates to standard NMA (diagnostic-only tool).

## Empirical Analyses

Three canonical NMA datasets were analysed with both methods:

| Dataset | Studies | Treatments | Outcome | Max ICS | S-NMA R_HF | S-NMA p |
|---------|---------|------------|---------|---------|------------|---------|
| Smoking cessation | 24 | 4 | Binary | 0.33 | 0.225 | 0.55 |
| Thrombolytic therapy | 28 | 8 | Binary | 0.67 | 0.009 | 0.94 |
| Parkinson's disease | 7 | 5 | Continuous | 0.67 | 0.323 | 0.64 |

Results are saved to `outputs/empirical/` with per-dataset CSVs for treatment effects, ICS scores, spectral energy, and edge scores.

## Project Structure

```
repo300-ENMA-SNMA/
|-- R/                                  # Python simulation + method engines
|   |-- 03_simulation_engine.py         # NMA data generator (5 topologies)
|   |-- 04_method_evaluator.py          # Performance evaluation framework
|   |-- 05_create_visualizations.py     # Audit result charts
|   |-- 06_expanded_simulation_engine.py # 10 network topologies
|   |-- 07_enma_engine.py               # *** E-NMA implementation ***
|   |-- 08_snma_engine.py               # *** S-NMA implementation ***
|   |-- 09_run_comparison.py            # Head-to-head comparison (100 reps)
|   |-- 10_empirical_analysis.py        # Empirical dataset analysis
|   |-- 01_data_audit_and_fix.py        # Dataset auditing
|   |-- 01_data_audit_and_fix.R         # R version of audit
|   |-- 02_cross_package_bakeoff.R      # Cross-package NMA comparison
|   +-- fix_datasets_and_run_comparison.R
|
|-- manuscript_rsm_enma.Rmd             # E-NMA paper (RSM target)
|-- manuscript_spectral_nma.Rmd         # S-NMA paper
|
|-- nmadatasets/                         # 53 curated NMA datasets
|   |-- inst/extdata/                   # CSV data files
|   +-- R/                              # Loading and validation functions
|
|-- netmetaDatasets/                     # 3 additional datasets
|-- nmaconsistent/                       # nmaconsistent R package
|
|-- outputs/
|   |-- data_audit_summary.csv          # Audit of 121 files
|   |-- cross_package_datasets.csv      # Cross-package mapping
|   |-- figures/                        # 10 audit visualization PNGs
|   |-- simulations/data/               # 5 scenarios x seeds
|   |-- comparison/                     # E-NMA vs S-NMA vs Standard (100 reps)
|   +-- empirical/                      # Empirical dataset results
|
|-- NMA_Methods_Research_Phase1_2.md    # Literature review
|-- NMA_Bakeoff_Framework.md            # Bake-off plan
|-- NMA_Simulation_Framework.md         # Simulation design
+-- COMPREHENSIVE_PROGRESS_REPORT.md    # Full progress report
```

## Quick Start

### Requirements

Python 3.10+ with:
```
numpy
pandas
scipy
```

Optional for visualizations: `matplotlib`, `seaborn`.

### Run E-NMA

```python
import sys; sys.path.insert(0, "R")
from importlib import import_module
sim = import_module("03_simulation_engine")
enma = import_module("07_enma_engine")

# Generate data with known inconsistency
config = sim.create_inconsistency_scenario(0.3)
data = sim.NMASimulator(config).generate()

# Run E-NMA
result = enma.run_enma(data, outcome_type="binary", reference="A",
                       omega=1.0, n_boot=500)

print(result.treatment_effects)
print(result.ics_scores)  # Per-edge inconsistency confidence
```

### Run S-NMA

```python
snma = import_module("08_snma_engine")

result = snma.run_snma(data, outcome_type="binary", reference="A")

print(f"High-freq ratio: {result.high_freq_ratio:.3f}")
print(f"Inconsistency detected: {result.inconsistency_detected}")
print(result.edge_contributions)  # Per-edge spectral scores
```

### Run Full Comparison (100 replications)

```bash
python R/09_run_comparison.py
```

Runs E-NMA, S-NMA, and standard NMA across 5 scenarios (100 reps each, ~9 min) and saves results to `outputs/comparison/`.

### Run Empirical Analysis

```bash
python R/10_empirical_analysis.py
```

Applies E-NMA and S-NMA to smoking cessation, thrombolytic therapy, and Parkinson's disease datasets. Saves results to `outputs/empirical/`.

### Run Demo Scripts

```bash
python R/03_simulation_engine.py   # Generate simulation data
python R/07_enma_engine.py         # E-NMA demonstration
python R/08_snma_engine.py         # S-NMA demonstration
```

## Datasets

121 NMA datasets audited across 8 R packages:

| Package | Datasets | Framework | Status |
|---------|----------|-----------|--------|
| netmeta | 5 | Frequentist | OK |
| gemtc | 9 | Bayesian (JAGS) | OK |
| multinma | 12 | Bayesian (Stan) | Some empty labels |
| bnma | 5 | Bayesian (JAGS) | OK |
| nmaINLA | 8 | Bayesian (INLA) | OK |
| MBNMAdose | 4 | Dose-response | Some empty labels |
| pcnetmeta | 4 | Bayesian | Some empty labels |
| BUGSnet | 6 | Bayesian (JAGS) | OK |

15 datasets appear across 3+ packages, enabling cross-package comparison.

## Simulation Scenarios

| Scenario | Topology | Studies | Treatments | tau^2 | Inconsistency |
|----------|----------|---------|------------|-------|---------------|
| Baseline | Dense | 30 | 5 | 0.01 | None |
| Sparse | Sparse | 15 | 5 | 0.04 | None |
| Inconsistency | Loop | 30 | 5 | 0.04 | 0.3 log-OR |
| High heterogeneity | Dense | 30 | 5 | 0.16 | None |
| Star | Star | 30 | 5 | 0.04 | None |

The expanded engine adds 5 more: scale-free, small-world, geometric, bipartite, and clinical-realistic.

## Remaining Work

1. **R package integration** -- The bake-off script (`02_cross_package_bakeoff.R`) compares netmeta, gemtc, multinma, bnma, and nmaINLA on the same datasets. Requires R with these packages installed.
2. **Omega sensitivity analysis** -- Test E-NMA with omega = 0.5, 1.0, 2.0, 5.0 to characterize the impact of the tuning parameter.
3. **Large-network simulations** -- Test S-NMA on networks with T = 10, 20, 50 treatments to characterize power curves for the spectral test.
4. **Higher replication count** -- Scale to 500--1000 reps for final publication-ready figures.

## Authors

- **Mahmood Ahmad** -- NHS England, London, UK
- **Laiba Khan** -- Independent Researcher, London, UK

## License

MIT
