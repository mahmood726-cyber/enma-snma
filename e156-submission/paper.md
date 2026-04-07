Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

Ensemble and Spectral Network Meta-Analysis: Novel Inconsistency-Robust Methods

Can ensemble and spectral approaches improve inconsistency detection and robustness in network meta-analysis compared to standard methods? We developed two novel methods evaluated across 100 simulation replications per scenario using five network topologies with varying heterogeneity and inconsistency, plus three canonical empirical datasets. Ensemble NMA synthesises three complementary inconsistency diagnostics into an Inconsistency Confidence Score per edge and inflates variance adaptively, while Spectral NMA applies graph Laplacian eigen-decomposition to detect inconsistency via high-frequency energy in treatment effect signals. The median coverage improvement for Ensemble NMA was 1.8 percentage points (95% CI 1.5-2.2) across scenarios where inconsistency was present, without increasing RMSE over standard network meta-analysis. Spectral NMA runs in milliseconds versus minutes for MCMC-based diagnostics and correctly identified inconsistent edges in the thrombolytic therapy dataset. These methods offer computationally efficient, complementary tools for assessing and accommodating inconsistency in evidence networks. A limitation is that simulations used normal approximations rather than exact binomial or survival data-generating processes.

Outside Notes

Type: methods
Primary estimand: Coverage improvement (percentage points)
App: repo300 E-NMA/S-NMA v0.2.0
Data: 100 simulation replications x 5 topologies + 3 empirical NMA datasets (smoking, thrombolytics, Parkinson)
Code: https://github.com/mahmood726-cyber/enma-snma
Version: 0.2.0
Validation: DRAFT

References

1. Salanti G. Indirect and mixed-treatment comparison, network, or multiple-treatments meta-analysis. Res Synth Methods. 2012;3(2):80-97.
2. Rucker G, Schwarzer G. Ranking treatments in frequentist network meta-analysis. BMC Med Res Methodol. 2015;15:58.
3. Dias S, Welton NJ, Caldwell DM, Ades AE. Checking consistency in mixed treatment comparison meta-analysis. Stat Med. 2010;29(7-8):932-944.
