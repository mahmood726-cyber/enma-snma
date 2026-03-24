#!/usr/bin/env python3
"""
Ensemble Network Meta-Analysis (E-NMA) Engine

A novel framework that synthesizes inconsistency detection across multiple
paradigms (KL divergence, Local-Global Hybrid, Bootstrap) to produce an
Inconsistency Confidence Score (ICS) per comparison, then performs
locally-weighted robust synthesis.

Author: Mahmood Ahmad
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from scipy import stats
import json
import warnings


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ContrastData:
    """Contrast-level data for one comparison."""
    treat1: str
    treat2: str
    effect: float          # log-OR / SMD
    se: float              # standard error of the effect
    study_id: str = ""
    n1: int = 0
    n2: int = 0


@dataclass
class ENMAResult:
    """Results from E-NMA analysis."""
    treatment_effects: pd.DataFrame       # relative to reference
    ics_scores: pd.DataFrame              # ICS per comparison edge
    method_flags: Dict[str, pd.DataFrame] # per-method binary flags
    adjusted_effects: pd.DataFrame        # after variance inflation
    rankings: Dict[str, float]            # treatment rankings (lower = better)
    omega: float = 1.0                    # tuning parameter used
    reference: str = "A"


# ---------------------------------------------------------------------------
# Helper: arm-based data to contrast-level
# ---------------------------------------------------------------------------

def arm_to_contrast(data: pd.DataFrame,
                    outcome_type: str = "binary") -> List[ContrastData]:
    """
    Convert arm-level NMA data to contrast-level data.

    For binary outcomes: expects columns [study, treatment, responders, sample_size].
    For continuous outcomes: expects columns [study, treatment, mean, sd, sample_size].
    """
    contrasts = []

    for study_id, grp in data.groupby("study"):
        if len(grp) < 2:
            continue
        arms = grp.sort_values("treatment").reset_index(drop=True)
        treatments = arms["treatment"].tolist()

        # Compute log-OR (binary) or MD (continuous) for each pair vs first arm
        for i in range(len(treatments)):
            for j in range(i + 1, len(treatments)):
                t1, t2 = treatments[i], treatments[j]
                a1 = arms[arms["treatment"] == t1].iloc[0]
                a2 = arms[arms["treatment"] == t2].iloc[0]

                if outcome_type == "binary":
                    r1, n1 = int(a1["responders"]), int(a1["sample_size"])
                    r2, n2 = int(a2["responders"]), int(a2["sample_size"])
                    # Continuity correction
                    r1c = r1 + 0.5 if r1 == 0 or r1 == n1 else r1
                    r2c = r2 + 0.5 if r2 == 0 or r2 == n2 else r2
                    n1c = n1 + (1 if r1 == 0 or r1 == n1 else 0)
                    n2c = n2 + (1 if r2 == 0 or r2 == n2 else 0)
                    log_or = (np.log(r2c / (n2c - r2c))
                              - np.log(r1c / (n1c - r1c)))
                    se = np.sqrt(1/r1c + 1/(n1c - r1c)
                                 + 1/r2c + 1/(n2c - r2c))
                    contrasts.append(ContrastData(
                        treat1=t1, treat2=t2,
                        effect=log_or, se=se,
                        study_id=str(study_id), n1=n1, n2=n2
                    ))
                else:  # continuous
                    m1, sd1, n1 = float(a1["mean"]), float(a1["sd"]), int(a1["sample_size"])
                    m2, sd2, n2 = float(a2["mean"]), float(a2["sd"]), int(a2["sample_size"])
                    md = m2 - m1
                    se = np.sqrt(sd1**2 / n1 + sd2**2 / n2)
                    contrasts.append(ContrastData(
                        treat1=t1, treat2=t2,
                        effect=md, se=se,
                        study_id=str(study_id), n1=n1, n2=n2
                    ))
    return contrasts


# ---------------------------------------------------------------------------
# Inconsistency detection methods
# ---------------------------------------------------------------------------

def _edge_key(t1: str, t2: str) -> Tuple[str, str]:
    """Canonical edge key (alphabetical order)."""
    return (min(t1, t2), max(t1, t2))


def _pool_direct(contrasts: List[ContrastData]) -> Dict[Tuple[str, str], Tuple[float, float]]:
    """Inverse-variance weighted pooling of direct evidence per edge."""
    from collections import defaultdict
    edge_data = defaultdict(list)
    for c in contrasts:
        key = _edge_key(c.treat1, c.treat2)
        # Ensure consistent direction
        effect = c.effect if c.treat1 == key[0] else -c.effect
        edge_data[key].append((effect, c.se))

    pooled = {}
    for key, pairs in edge_data.items():
        weights = [1.0 / (se**2) for _, se in pairs if se > 0]
        effects = [e for e, se in pairs if se > 0]
        if not weights:
            continue
        w_sum = sum(weights)
        pooled_effect = sum(w * e for w, e in zip(weights, effects)) / w_sum
        pooled_se = 1.0 / np.sqrt(w_sum)
        pooled[key] = (pooled_effect, pooled_se)
    return pooled


def _build_indirect_via_loops(pooled_direct: Dict,
                              treatments: List[str]) -> Dict[Tuple[str, str], Tuple[float, float]]:
    """
    Compute indirect evidence for each edge through all available two-step paths.
    Uses the consistency equation: d_AC_indirect = d_AB + d_BC.
    """
    indirect = {}
    for t1 in treatments:
        for t2 in treatments:
            if t1 >= t2:
                continue
            key = _edge_key(t1, t2)
            indirect_estimates = []
            for mid in treatments:
                if mid == t1 or mid == t2:
                    continue
                k1 = _edge_key(t1, mid)
                k2 = _edge_key(mid, t2)
                if k1 in pooled_direct and k2 in pooled_direct:
                    e1, se1 = pooled_direct[k1]
                    e2, se2 = pooled_direct[k2]
                    # Correct sign: d_{t1,mid} + d_{mid,t2} = d_{t1,t2}
                    sign1 = 1 if t1 == k1[0] else -1
                    sign2 = 1 if mid == k2[0] else -1
                    e_indirect = sign1 * e1 + sign2 * e2
                    se_indirect = np.sqrt(se1**2 + se2**2)
                    indirect_estimates.append((e_indirect, se_indirect))

            if indirect_estimates:
                # Pool indirect estimates
                weights = [1.0 / (se**2) for _, se in indirect_estimates if se > 0]
                effects = [e for e, _ in indirect_estimates]
                if weights:
                    w_sum = sum(weights)
                    pooled_e = sum(w * e for w, e in zip(weights, effects)) / w_sum
                    pooled_se = 1.0 / np.sqrt(w_sum)
                    indirect[key] = (pooled_e, pooled_se)
    return indirect


# --- Method 1: KL Divergence Inconsistency ---

def kl_divergence_inconsistency(contrasts: List[ContrastData],
                                 treatments: List[str],
                                 alpha: float = 0.05) -> pd.DataFrame:
    """
    KL divergence between direct and indirect evidence distributions.

    For each edge with both direct and indirect evidence, compute the
    symmetric KL divergence between the two normal distributions.

    Returns DataFrame with columns: treat1, treat2, kl_divergence, flagged.
    """
    pooled_direct = _pool_direct(contrasts)
    indirect = _build_indirect_via_loops(pooled_direct, treatments)

    rows = []
    for key in pooled_direct:
        if key not in indirect:
            rows.append({
                "treat1": key[0], "treat2": key[1],
                "kl_divergence": 0.0, "flagged": False
            })
            continue
        e_d, se_d = pooled_direct[key]
        e_i, se_i = indirect[key]

        # Symmetric KL divergence for two normals
        var_d = se_d**2
        var_i = se_i**2
        if var_d <= 0 or var_i <= 0:
            rows.append({
                "treat1": key[0], "treat2": key[1],
                "kl_divergence": 0.0, "flagged": False
            })
            continue

        kl = 0.5 * ((var_d / var_i) + (var_i / var_d)
                     + (e_d - e_i)**2 * (1/var_d + 1/var_i) - 2)

        # Chi-squared approximation: 2*KL ~ chi2(1) under H0
        p_value = 1.0 - stats.chi2.cdf(2 * kl, df=1)
        flagged = p_value < alpha

        rows.append({
            "treat1": key[0], "treat2": key[1],
            "kl_divergence": float(kl), "p_value": float(p_value),
            "flagged": bool(flagged)
        })

    return pd.DataFrame(rows)


# --- Method 2: Local-Global Hybrid Test ---

def local_global_hybrid_test(contrasts: List[ContrastData],
                              treatments: List[str],
                              alpha: float = 0.05) -> pd.DataFrame:
    """
    Two-stage hierarchical test:
    1. Global Q-statistic for overall inconsistency
    2. If global significant, test each edge locally (node-splitting analogue)

    Uses Bonferroni correction for family-wise error control.
    """
    pooled_direct = _pool_direct(contrasts)
    indirect = _build_indirect_via_loops(pooled_direct, treatments)

    # Edges with both direct and indirect evidence
    testable_edges = [k for k in pooled_direct if k in indirect]
    n_tests = len(testable_edges)

    if n_tests == 0:
        return pd.DataFrame(columns=["treat1", "treat2", "z_stat",
                                      "p_value", "flagged"])

    # Global test: sum of squared z-statistics
    z_stats = []
    for key in testable_edges:
        e_d, se_d = pooled_direct[key]
        e_i, se_i = indirect[key]
        diff = e_d - e_i
        se_diff = np.sqrt(se_d**2 + se_i**2)
        z = diff / se_diff if se_diff > 0 else 0
        z_stats.append((key, z, diff, se_diff))

    Q_global = sum(z**2 for _, z, _, _ in z_stats)
    p_global = 1.0 - stats.chi2.cdf(Q_global, df=n_tests)

    # Local tests with Bonferroni correction
    adjusted_alpha = alpha / max(n_tests, 1)

    rows = []
    for key, z, diff, se_diff in z_stats:
        p_local = 2 * (1.0 - stats.norm.cdf(abs(z)))
        # Only flag if both global and local are significant
        flagged = (p_global < alpha) and (p_local < adjusted_alpha)
        rows.append({
            "treat1": key[0], "treat2": key[1],
            "z_stat": float(z), "p_value": float(p_local),
            "p_global": float(p_global),
            "flagged": bool(flagged)
        })

    return pd.DataFrame(rows)


# --- Method 3: Bootstrap Validation ---

def bootstrap_inconsistency(contrasts: List[ContrastData],
                             treatments: List[str],
                             n_boot: int = 500,
                             alpha: float = 0.05,
                             seed: int = 42) -> pd.DataFrame:
    """
    Non-parametric bootstrap to assess stability of direct-indirect agreement.

    Resample studies with replacement, re-compute direct and indirect pooling,
    check if the sign/magnitude of the difference is stable.
    """
    rng = np.random.RandomState(seed)

    pooled_direct = _pool_direct(contrasts)
    indirect = _build_indirect_via_loops(pooled_direct, treatments)
    testable_edges = [k for k in pooled_direct if k in indirect]

    if not testable_edges:
        return pd.DataFrame(columns=["treat1", "treat2",
                                      "boot_inconsistency_rate", "flagged"])

    # Group contrasts by study
    from collections import defaultdict
    study_groups = defaultdict(list)
    for c in contrasts:
        study_groups[c.study_id].append(c)
    study_ids = list(study_groups.keys())

    # Bootstrap
    edge_inconsistency_count = {k: 0 for k in testable_edges}

    for b in range(n_boot):
        # Resample studies
        boot_studies = rng.choice(study_ids, size=len(study_ids), replace=True)
        boot_contrasts = []
        for i, sid in enumerate(boot_studies):
            for c in study_groups[sid]:
                boot_contrasts.append(ContrastData(
                    treat1=c.treat1, treat2=c.treat2,
                    effect=c.effect, se=c.se,
                    study_id=f"{sid}_b{i}", n1=c.n1, n2=c.n2
                ))

        boot_direct = _pool_direct(boot_contrasts)
        boot_indirect = _build_indirect_via_loops(boot_direct, treatments)

        for key in testable_edges:
            if key in boot_direct and key in boot_indirect:
                e_d, se_d = boot_direct[key]
                e_i, se_i = boot_indirect[key]
                diff = abs(e_d - e_i)
                se_diff = np.sqrt(se_d**2 + se_i**2)
                if se_diff > 0 and diff / se_diff > stats.norm.ppf(1 - alpha / 2):
                    edge_inconsistency_count[key] += 1

    rows = []
    for key in testable_edges:
        rate = edge_inconsistency_count[key] / n_boot
        rows.append({
            "treat1": key[0], "treat2": key[1],
            "boot_inconsistency_rate": float(rate),
            "flagged": rate > 0.5  # majority of bootstraps flag it
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# E-NMA: Ensemble Synthesis
# ---------------------------------------------------------------------------

class ENMA:
    """
    Ensemble Network Meta-Analysis.

    Runs multiple inconsistency detection methods, computes an Inconsistency
    Confidence Score (ICS) per edge, and performs locally-weighted synthesis
    with adaptive variance inflation.
    """

    def __init__(self, omega: float = 1.0, n_boot: int = 500,
                 alpha: float = 0.05, seed: int = 42):
        """
        Args:
            omega: Variance inflation tuning parameter (default 1.0).
            n_boot: Number of bootstrap replications.
            alpha: Significance level.
            seed: Random seed for bootstrap.
        """
        self.omega = omega
        self.n_boot = n_boot
        self.alpha = alpha
        self.seed = seed

    def fit(self, data: pd.DataFrame, outcome_type: str = "binary",
            reference: str = "A") -> ENMAResult:
        """
        Run the full E-NMA pipeline.

        Args:
            data: Arm-level NMA data with columns
                  [study, treatment, responders, sample_size] (binary) or
                  [study, treatment, mean, sd, sample_size] (continuous).
            outcome_type: "binary" or "continuous".
            reference: Reference treatment.

        Returns:
            ENMAResult with treatment effects, ICS scores, etc.
        """
        treatments = sorted(data["treatment"].unique().tolist())
        contrasts = arm_to_contrast(data, outcome_type)

        if not contrasts:
            raise ValueError("No valid contrasts could be computed from the data.")

        # --- Stage 1: Diagnostic Execution ---
        kl_results = kl_divergence_inconsistency(
            contrasts, treatments, alpha=self.alpha
        )
        hybrid_results = local_global_hybrid_test(
            contrasts, treatments, alpha=self.alpha
        )
        boot_results = bootstrap_inconsistency(
            contrasts, treatments,
            n_boot=self.n_boot, alpha=self.alpha, seed=self.seed
        )

        method_flags = {
            "kl_divergence": kl_results,
            "local_global_hybrid": hybrid_results,
            "bootstrap": boot_results
        }

        # --- Stage 2: Consensus Mapping (ICS) ---
        ics_scores = self._compute_ics(kl_results, hybrid_results, boot_results)

        # --- Stage 3: Robust Synthesis ---
        adjusted_contrasts = self._inflate_variance(contrasts, ics_scores)
        treatment_effects = self._weighted_synthesis(
            adjusted_contrasts, treatments, reference
        )
        rankings = self._compute_rankings(treatment_effects)

        return ENMAResult(
            treatment_effects=treatment_effects,
            ics_scores=ics_scores,
            method_flags=method_flags,
            adjusted_effects=treatment_effects,
            rankings=rankings,
            omega=self.omega,
            reference=reference
        )

    def _compute_ics(self, kl_df: pd.DataFrame,
                     hybrid_df: pd.DataFrame,
                     boot_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute Inconsistency Confidence Score for each edge.

        ICS = (1/M) * sum of indicator(method m flags this edge)
        """
        # Collect all edges
        all_edges = set()
        for df in [kl_df, hybrid_df, boot_df]:
            if len(df) > 0 and "treat1" in df.columns:
                for _, row in df.iterrows():
                    all_edges.add(_edge_key(row["treat1"], row["treat2"]))

        rows = []
        for edge in sorted(all_edges):
            flags = []

            # KL divergence flag
            if len(kl_df) > 0:
                mask = kl_df.apply(
                    lambda r: _edge_key(r["treat1"], r["treat2"]) == edge, axis=1
                )
                if mask.any():
                    flags.append(int(kl_df.loc[mask, "flagged"].iloc[0]))

            # Hybrid flag
            if len(hybrid_df) > 0:
                mask = hybrid_df.apply(
                    lambda r: _edge_key(r["treat1"], r["treat2"]) == edge, axis=1
                )
                if mask.any():
                    flags.append(int(hybrid_df.loc[mask, "flagged"].iloc[0]))

            # Bootstrap flag
            if len(boot_df) > 0:
                mask = boot_df.apply(
                    lambda r: _edge_key(r["treat1"], r["treat2"]) == edge, axis=1
                )
                if mask.any():
                    flags.append(int(boot_df.loc[mask, "flagged"].iloc[0]))

            ics = sum(flags) / len(flags) if flags else 0.0

            rows.append({
                "treat1": edge[0],
                "treat2": edge[1],
                "n_methods": len(flags),
                "n_flagged": sum(flags),
                "ics": ics
            })

        return pd.DataFrame(rows)

    def _inflate_variance(self, contrasts: List[ContrastData],
                          ics_df: pd.DataFrame) -> List[ContrastData]:
        """
        Adaptive variance inflation:
            se'_ij = se_ij * (1 + omega * ICS_ij)
        """
        ics_lookup = {}
        for _, row in ics_df.iterrows():
            key = _edge_key(row["treat1"], row["treat2"])
            ics_lookup[key] = row["ics"]

        adjusted = []
        for c in contrasts:
            key = _edge_key(c.treat1, c.treat2)
            ics = ics_lookup.get(key, 0.0)
            inflation = 1.0 + self.omega * ics
            adjusted.append(ContrastData(
                treat1=c.treat1, treat2=c.treat2,
                effect=c.effect, se=c.se * inflation,
                study_id=c.study_id, n1=c.n1, n2=c.n2
            ))
        return adjusted

    def _weighted_synthesis(self, contrasts: List[ContrastData],
                            treatments: List[str],
                            reference: str) -> pd.DataFrame:
        """
        Simple graph-theoretic NMA: solve the normal equations for
        treatment effects relative to reference, using inverse-variance
        weights from the (possibly inflated) contrasts.
        """
        n_treat = len(treatments)
        treat_idx = {t: i for i, t in enumerate(treatments)}
        ref_idx = treat_idx[reference]

        # Build design matrix and weight system
        # For each contrast (i,j): y_ij = d_j - d_i
        # Weighted least squares: X'WX * d = X'Wy
        n_contrasts = len(contrasts)
        X = np.zeros((n_contrasts, n_treat))
        y = np.zeros(n_contrasts)
        W = np.zeros(n_contrasts)

        for k, c in enumerate(contrasts):
            i = treat_idx.get(c.treat1)
            j = treat_idx.get(c.treat2)
            if i is None or j is None:
                continue
            X[k, j] = 1
            X[k, i] = -1
            y[k] = c.effect
            W[k] = 1.0 / (c.se**2) if c.se > 0 else 0

        # Remove reference column (d_ref = 0 constraint)
        keep = [i for i in range(n_treat) if i != ref_idx]
        X_red = X[:, keep]

        # Weighted least squares
        WX = X_red * W[:, np.newaxis]
        XtWX = X_red.T @ WX
        XtWy = WX.T @ y

        try:
            d_hat = np.linalg.solve(XtWX, XtWy)
        except np.linalg.LinAlgError:
            # Fallback to pseudoinverse
            d_hat = np.linalg.lstsq(XtWX, XtWy, rcond=None)[0]

        # Standard errors from inverse of XtWX
        try:
            cov = np.linalg.inv(XtWX)
        except np.linalg.LinAlgError:
            cov = np.linalg.pinv(XtWX)

        se_hat = np.sqrt(np.diag(cov))

        # Build results
        rows = []
        d_full = np.zeros(n_treat)
        se_full = np.zeros(n_treat)
        idx_map = {keep[k]: k for k in range(len(keep))}
        for i in range(n_treat):
            if i == ref_idx:
                rows.append({
                    "treatment": treatments[i],
                    "effect": 0.0,
                    "se": 0.0,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0
                })
            else:
                k = idx_map[i]
                eff = d_hat[k]
                se = se_hat[k]
                z = stats.norm.ppf(1 - self.alpha / 2)
                rows.append({
                    "treatment": treatments[i],
                    "effect": float(eff),
                    "se": float(se),
                    "ci_lower": float(eff - z * se),
                    "ci_upper": float(eff + z * se)
                })

        return pd.DataFrame(rows)

    def _compute_rankings(self, effects_df: pd.DataFrame) -> Dict[str, float]:
        """Rank treatments by effect (lower = better for log-OR)."""
        sorted_df = effects_df.sort_values("effect")
        return {row["treatment"]: rank + 1
                for rank, (_, row) in enumerate(sorted_df.iterrows())}


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def run_enma(data: pd.DataFrame,
             outcome_type: str = "binary",
             reference: str = "A",
             omega: float = 1.0,
             n_boot: int = 500,
             alpha: float = 0.05,
             seed: int = 42) -> ENMAResult:
    """
    Run E-NMA on arm-level NMA data.

    Args:
        data: DataFrame with columns [study, treatment, responders, sample_size]
              (binary) or [study, treatment, mean, sd, sample_size] (continuous).
        outcome_type: "binary" or "continuous".
        reference: Reference treatment name.
        omega: Variance inflation parameter.
        n_boot: Bootstrap replications.
        alpha: Significance level.
        seed: Random seed.

    Returns:
        ENMAResult with treatment effects, ICS, rankings.
    """
    engine = ENMA(omega=omega, n_boot=n_boot, alpha=alpha, seed=seed)
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
    print("  E-NMA ENGINE - DEMONSTRATION")
    print("=" * 73 + "\n")

    # Generate a dataset with known inconsistency
    config = sim_mod.create_inconsistency_scenario(0.3)
    simulator = sim_mod.NMASimulator(config)
    data = simulator.generate()
    true_effects = simulator.get_true_effects()

    print("Generated data with inconsistency magnitude = 0.3")
    print(f"Studies: {data['study'].nunique()}, "
          f"Treatments: {data['treatment'].nunique()}\n")

    # Run E-NMA
    result = run_enma(data, outcome_type="binary", reference="A",
                      omega=1.0, n_boot=200, seed=42)

    print("--- Treatment Effects (E-NMA) ---")
    print(result.treatment_effects.to_string(index=False))

    print("\n--- Inconsistency Confidence Scores ---")
    print(result.ics_scores.to_string(index=False))

    print("\n--- Rankings ---")
    for t, rank in sorted(result.rankings.items(), key=lambda x: x[1]):
        print(f"  {t}: rank {rank}")

    print("\n--- True Effects ---")
    print(true_effects.to_string(index=False))

    # Also run on a consistent dataset
    print("\n" + "=" * 73)
    print("  E-NMA on CONSISTENT data (baseline)")
    print("=" * 73 + "\n")

    config_base = sim_mod.create_baseline_scenario()
    sim_base = sim_mod.NMASimulator(config_base)
    data_base = sim_base.generate()

    result_base = run_enma(data_base, outcome_type="binary", reference="A",
                           omega=1.0, n_boot=200, seed=42)

    print("--- ICS Scores (should be ~0 for consistent data) ---")
    print(result_base.ics_scores.to_string(index=False))

    print("\n" + "=" * 73)
    print("  E-NMA demonstration complete.")
    print("=" * 73 + "\n")
