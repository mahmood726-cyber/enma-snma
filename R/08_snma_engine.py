#!/usr/bin/env python3
"""
Spectral Network Meta-Analysis (S-NMA) Engine

A novel method that detects inconsistency by treating the NMA network as a
weighted graph, computing the graph Laplacian, and identifying high-frequency
spectral energy as evidence of transitivity violations.

Author: Mahmood Ahmad
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from scipy import stats
import warnings


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SNMAResult:
    """Results from S-NMA analysis."""
    treatment_effects: pd.DataFrame       # relative to reference
    spectral_energy: pd.DataFrame         # energy per eigenmode
    edge_contributions: pd.DataFrame      # per-edge spectral inconsistency score
    eigenvalues: np.ndarray               # graph Laplacian eigenvalues
    eigenvectors: np.ndarray              # graph Laplacian eigenvectors
    total_spectral_energy: float          # total signal energy
    high_freq_ratio: float                # fraction of energy in high-frequency modes
    inconsistency_detected: bool          # overall verdict
    p_value: float                        # global spectral test p-value
    rankings: Dict[str, float]
    reference: str = "A"


# ---------------------------------------------------------------------------
# S-NMA Implementation
# ---------------------------------------------------------------------------

class SNMA:
    """
    Spectral Network Meta-Analysis.

    Builds a weighted graph Laplacian from the NMA evidence network, performs
    eigen-decomposition, and analyses the spectral energy distribution of the
    treatment effect signal to detect and localise inconsistency.
    """

    def __init__(self, alpha: float = 0.05,
                 high_freq_threshold: float = 0.5):
        """
        Args:
            alpha: Significance level for the spectral test.
            high_freq_threshold: Fraction of eigenvalue range above which
                modes are considered "high frequency". Default 0.5 means
                the top half of the spectrum.
        """
        self.alpha = alpha
        self.high_freq_threshold = high_freq_threshold

    def fit(self, data: pd.DataFrame, outcome_type: str = "binary",
            reference: str = "A") -> SNMAResult:
        """
        Run the full S-NMA pipeline.

        Args:
            data: Arm-level NMA data.
            outcome_type: "binary" or "continuous".
            reference: Reference treatment.

        Returns:
            SNMAResult.
        """
        treatments = sorted(data["treatment"].unique().tolist())
        n = len(treatments)
        treat_idx = {t: i for i, t in enumerate(treatments)}

        # Step 1: Compute contrast-level summaries per edge
        from importlib import import_module
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        enma_mod = import_module("07_enma_engine")

        contrasts = enma_mod.arm_to_contrast(data, outcome_type)
        pooled = enma_mod._pool_direct(contrasts)

        # Step 2: Build weighted adjacency and Laplacian
        W = np.zeros((n, n))
        effect_matrix = np.zeros((n, n))

        for (t1, t2), (eff, se) in pooled.items():
            i = treat_idx[t1]
            j = treat_idx[t2]
            precision = 1.0 / (se**2) if se > 0 else 0
            W[i, j] = precision
            W[j, i] = precision
            effect_matrix[i, j] = eff
            effect_matrix[j, i] = -eff

        D = np.diag(W.sum(axis=1))
        L = D - W  # Graph Laplacian

        # Step 3: Eigen-decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        # Sort ascending (eigh returns sorted, but be safe)
        idx = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Step 4: Construct treatment effect signal
        # Use simple NMA (inverse-variance weighted) to get point estimates
        signal = self._simple_nma(contrasts, treatments, reference, treat_idx)

        # Step 5: Project signal into spectral domain (Graph Fourier Transform)
        spectral_coefficients = eigenvectors.T @ signal

        # Step 6: Compute spectral energy distribution
        energy = spectral_coefficients**2
        total_energy = energy.sum()

        # Classify modes as high/low frequency
        if n > 1:
            max_eigenvalue = eigenvalues[-1]
            threshold_value = max_eigenvalue * self.high_freq_threshold
            high_freq_mask = eigenvalues >= threshold_value
        else:
            high_freq_mask = np.zeros(n, dtype=bool)

        high_freq_energy = energy[high_freq_mask].sum()
        high_freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0.0

        # Step 7: Statistical test
        # Under consistency, signal should be smooth (low-frequency).
        # Use a permutation-based or chi-squared test on the high-freq ratio.
        p_value, inconsistency_detected = self._spectral_test(
            energy, eigenvalues, high_freq_mask, n
        )

        # Step 8: Localise inconsistency to edges
        edge_contributions = self._localise_to_edges(
            eigenvectors, energy, eigenvalues, high_freq_mask,
            treatments, pooled, treat_idx
        )

        # Step 9: Treatment effects (from simple NMA)
        treatment_effects = self._effects_to_df(
            signal, treatments, reference, treat_idx, contrasts
        )
        rankings = self._compute_rankings(treatment_effects)

        # Spectral energy table
        spectral_df = pd.DataFrame({
            "mode": list(range(n)),
            "eigenvalue": eigenvalues,
            "energy": energy,
            "is_high_freq": high_freq_mask,
            "energy_fraction": energy / total_energy if total_energy > 0 else energy
        })

        return SNMAResult(
            treatment_effects=treatment_effects,
            spectral_energy=spectral_df,
            edge_contributions=edge_contributions,
            eigenvalues=eigenvalues,
            eigenvectors=eigenvectors,
            total_spectral_energy=float(total_energy),
            high_freq_ratio=float(high_freq_ratio),
            inconsistency_detected=bool(inconsistency_detected),
            p_value=float(p_value),
            rankings=rankings,
            reference=reference
        )

    def _simple_nma(self, contrasts, treatments, reference, treat_idx):
        """Inverse-variance weighted NMA for the treatment effect signal."""
        n = len(treatments)
        ref_idx = treat_idx[reference]

        n_c = len(contrasts)
        X = np.zeros((n_c, n))
        y = np.zeros(n_c)
        w = np.zeros(n_c)

        for k, c in enumerate(contrasts):
            i = treat_idx.get(c.treat1)
            j = treat_idx.get(c.treat2)
            if i is None or j is None:
                continue
            X[k, j] = 1
            X[k, i] = -1
            y[k] = c.effect
            w[k] = 1.0 / (c.se**2) if c.se > 0 else 0

        keep = [i for i in range(n) if i != ref_idx]
        X_red = X[:, keep]
        WX = X_red * w[:, np.newaxis]
        XtWX = X_red.T @ WX
        XtWy = WX.T @ y

        try:
            d_hat = np.linalg.solve(XtWX, XtWy)
        except np.linalg.LinAlgError:
            d_hat = np.linalg.lstsq(XtWX, XtWy, rcond=None)[0]

        signal = np.zeros(n)
        for k_idx, orig_idx in enumerate(keep):
            signal[orig_idx] = d_hat[k_idx]

        return signal

    def _spectral_test(self, energy, eigenvalues, high_freq_mask, n):
        """
        Test whether high-frequency energy is significantly larger than
        expected under consistency.

        Under H0 (consistency), the signal is "smooth" and should concentrate
        in low-frequency modes. We use a ratio test comparing observed
        high-frequency energy fraction to the null expectation.

        Under the null, if the signal were random noise, each mode would have
        equal expected energy. So the expected high-freq fraction = n_hf / n.
        We use a binomial-type test.
        """
        total = energy.sum()
        if total <= 0 or n < 3:
            return 1.0, False

        n_hf = high_freq_mask.sum()
        observed_ratio = energy[high_freq_mask].sum() / total
        expected_ratio = n_hf / n if n > 0 else 0

        # Use a one-sided z-test on the transformed ratio
        # Variance under null: p(1-p)/n for fraction
        if expected_ratio <= 0 or expected_ratio >= 1:
            return 1.0, False

        se_null = np.sqrt(expected_ratio * (1 - expected_ratio) / max(n, 1))
        if se_null <= 0:
            return 1.0, False

        z = (observed_ratio - expected_ratio) / se_null
        p_value = 1.0 - stats.norm.cdf(z)  # one-sided: excess high-freq energy

        return float(p_value), p_value < self.alpha

    def _localise_to_edges(self, eigenvectors, energy, eigenvalues,
                           high_freq_mask, treatments, pooled, treat_idx):
        """
        Map high-frequency spectral peaks back to specific edges.

        For each high-frequency mode, the contribution of edge (i,j) is
        proportional to |u_l(i) - u_l(j)|^2 * energy_l, where u_l is the
        l-th eigenvector and energy_l is its spectral energy.
        """
        n = len(treatments)
        rows = []

        for (t1, t2) in pooled:
            i = treat_idx[t1]
            j = treat_idx[t2]
            score = 0.0

            for l in range(n):
                if high_freq_mask[l]:
                    diff = eigenvectors[i, l] - eigenvectors[j, l]
                    score += diff**2 * energy[l]

            rows.append({
                "treat1": t1,
                "treat2": t2,
                "spectral_inconsistency_score": float(score)
            })

        df = pd.DataFrame(rows)
        if len(df) > 0:
            max_score = df["spectral_inconsistency_score"].max()
            df["normalized_score"] = (
                df["spectral_inconsistency_score"] / max_score
                if max_score > 0 else 0.0
            )
        return df

    def _effects_to_df(self, signal, treatments, reference, treat_idx,
                       contrasts):
        """Convert signal vector to a DataFrame with CIs."""
        from importlib import import_module
        enma_mod = import_module("07_enma_engine")

        # Re-estimate with CIs
        n = len(treatments)
        ref_idx = treat_idx[reference]
        n_c = len(contrasts)
        X = np.zeros((n_c, n))
        y = np.zeros(n_c)
        w = np.zeros(n_c)

        for k, c in enumerate(contrasts):
            i_idx = treat_idx.get(c.treat1)
            j_idx = treat_idx.get(c.treat2)
            if i_idx is None or j_idx is None:
                continue
            X[k, j_idx] = 1
            X[k, i_idx] = -1
            y[k] = c.effect
            w[k] = 1.0 / (c.se**2) if c.se > 0 else 0

        keep = [i for i in range(n) if i != ref_idx]
        X_red = X[:, keep]
        WX = X_red * w[:, np.newaxis]
        XtWX = X_red.T @ WX
        XtWy = WX.T @ y

        try:
            d_hat = np.linalg.solve(XtWX, XtWy)
            cov = np.linalg.inv(XtWX)
        except np.linalg.LinAlgError:
            d_hat = np.linalg.lstsq(XtWX, XtWy, rcond=None)[0]
            cov = np.linalg.pinv(XtWX)

        se_hat = np.sqrt(np.diag(cov))
        z = stats.norm.ppf(1 - self.alpha / 2)
        idx_map = {keep[k]: k for k in range(len(keep))}

        rows = []
        for i in range(n):
            if i == ref_idx:
                rows.append({"treatment": treatments[i], "effect": 0.0,
                             "se": 0.0, "ci_lower": 0.0, "ci_upper": 0.0})
            else:
                k = idx_map[i]
                eff = d_hat[k]
                se = se_hat[k]
                rows.append({
                    "treatment": treatments[i],
                    "effect": float(eff), "se": float(se),
                    "ci_lower": float(eff - z * se),
                    "ci_upper": float(eff + z * se)
                })
        return pd.DataFrame(rows)

    def _compute_rankings(self, effects_df):
        sorted_df = effects_df.sort_values("effect")
        return {row["treatment"]: rank + 1
                for rank, (_, row) in enumerate(sorted_df.iterrows())}


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def run_snma(data: pd.DataFrame,
             outcome_type: str = "binary",
             reference: str = "A",
             alpha: float = 0.05,
             high_freq_threshold: float = 0.5) -> SNMAResult:
    """
    Run S-NMA on arm-level NMA data.

    Args:
        data: DataFrame with columns [study, treatment, responders, sample_size]
              or [study, treatment, mean, sd, sample_size].
        outcome_type: "binary" or "continuous".
        reference: Reference treatment.
        alpha: Significance level.
        high_freq_threshold: Fraction of spectrum considered high-frequency.

    Returns:
        SNMAResult.
    """
    engine = SNMA(alpha=alpha, high_freq_threshold=high_freq_threshold)
    return engine.fit(data, outcome_type=outcome_type, reference=reference)


# ---------------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from importlib import import_module

    sim_mod = import_module("03_simulation_engine")

    print("\n" + "=" * 73)
    print("  S-NMA ENGINE - DEMONSTRATION")
    print("=" * 73 + "\n")

    # --- Consistent data ---
    print("--- Consistent Network (Baseline) ---\n")
    config_base = sim_mod.create_baseline_scenario()
    sim_base = sim_mod.NMASimulator(config_base)
    data_base = sim_base.generate()

    result_base = run_snma(data_base, outcome_type="binary", reference="A")

    print(f"High-frequency energy ratio: {result_base.high_freq_ratio:.4f}")
    print(f"Spectral test p-value:       {result_base.p_value:.4f}")
    print(f"Inconsistency detected:      {result_base.inconsistency_detected}\n")

    print("Spectral Energy Distribution:")
    print(result_base.spectral_energy.to_string(index=False))

    print("\nTreatment Effects:")
    print(result_base.treatment_effects.to_string(index=False))

    # --- Inconsistent data ---
    print("\n" + "=" * 73)
    print("--- Inconsistent Network (magnitude=0.3) ---\n")

    config_inc = sim_mod.create_inconsistency_scenario(0.3)
    sim_inc = sim_mod.NMASimulator(config_inc)
    data_inc = sim_inc.generate()

    result_inc = run_snma(data_inc, outcome_type="binary", reference="A")

    print(f"High-frequency energy ratio: {result_inc.high_freq_ratio:.4f}")
    print(f"Spectral test p-value:       {result_inc.p_value:.4f}")
    print(f"Inconsistency detected:      {result_inc.inconsistency_detected}\n")

    print("Edge-level Spectral Inconsistency Scores:")
    print(result_inc.edge_contributions.to_string(index=False))

    print("\nTreatment Effects:")
    print(result_inc.treatment_effects.to_string(index=False))

    print("\nTrue Effects:")
    true_eff = sim_inc.get_true_effects()
    print(true_eff.to_string(index=False))

    print("\n" + "=" * 73)
    print("  S-NMA demonstration complete.")
    print("=" * 73 + "\n")
