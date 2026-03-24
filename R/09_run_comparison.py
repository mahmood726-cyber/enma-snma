#!/usr/bin/env python3
"""
E-NMA vs S-NMA vs Standard NMA: Head-to-Head Comparison

Runs all three approaches on the same simulated datasets and reports
RMSE, coverage, ranking accuracy, and inconsistency detection performance.

Author: Mahmood Ahmad
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List

# Ensure sibling modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

sim_mod = import_module("03_simulation_engine")
enma_mod = import_module("07_enma_engine")
snma_mod = import_module("08_snma_engine")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Simple standard NMA (inverse-variance weighted, no inconsistency handling)
# ---------------------------------------------------------------------------

def run_standard_nma(data: pd.DataFrame, outcome_type: str = "binary",
                     reference: str = "A") -> pd.DataFrame:
    """Standard fixed-effect NMA as baseline comparator."""
    from scipy import stats as sp_stats

    treatments = sorted(data["treatment"].unique().tolist())
    contrasts = enma_mod.arm_to_contrast(data, outcome_type)
    n = len(treatments)
    treat_idx = {t: i for i, t in enumerate(treatments)}
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
        cov = np.linalg.inv(XtWX)
    except np.linalg.LinAlgError:
        d_hat = np.linalg.lstsq(XtWX, XtWy, rcond=None)[0]
        cov = np.linalg.pinv(XtWX)

    se_hat = np.sqrt(np.diag(cov))
    z = sp_stats.norm.ppf(0.975)
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


# ---------------------------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------------------------

def evaluate(estimated: pd.DataFrame, true_effects: pd.DataFrame) -> Dict:
    """Compute RMSE, bias, coverage against true effects."""
    merged = estimated.merge(true_effects, on="treatment", suffixes=("_est", "_true"))
    merged = merged[merged["treatment"] != "A"]  # skip reference

    if len(merged) == 0:
        return {"rmse": np.nan, "bias": np.nan, "coverage": np.nan,
                "rank_corr": np.nan}

    bias = (merged["effect"] - merged["true_effect"]).values
    rmse = float(np.sqrt((bias**2).mean()))
    mean_bias = float(bias.mean())

    # Coverage
    if "ci_lower" in merged.columns and "ci_upper" in merged.columns:
        covered = ((merged["true_effect"] >= merged["ci_lower"]) &
                   (merged["true_effect"] <= merged["ci_upper"]))
        coverage = float(covered.mean())
    else:
        coverage = np.nan

    # Rank correlation
    est_ranks = merged["effect"].rank().values
    true_ranks = merged["true_effect"].rank().values
    if len(est_ranks) > 1:
        rank_corr = float(np.corrcoef(est_ranks, true_ranks)[0, 1])
    else:
        rank_corr = np.nan

    return {"rmse": rmse, "bias": mean_bias, "coverage": coverage,
            "rank_corr": rank_corr}


# ---------------------------------------------------------------------------
# Run comparison
# ---------------------------------------------------------------------------

def run_comparison(n_reps: int = 50) -> pd.DataFrame:
    """
    Run head-to-head comparison across scenarios and methods.

    Returns a DataFrame with one row per (scenario, replication, method).
    """
    scenarios = [
        ("Baseline", sim_mod.create_baseline_scenario),
        ("Sparse", sim_mod.create_sparse_network_scenario),
        ("Inconsistency_0.3", lambda: sim_mod.create_inconsistency_scenario(0.3)),
        ("High_Heterogeneity", sim_mod.create_high_heterogeneity_scenario),
        ("Star", sim_mod.create_star_network_scenario),
    ]

    all_rows = []

    for scenario_name, config_fn in scenarios:
        print(f"\n{'='*60}")
        print(f"  Scenario: {scenario_name}")
        print(f"{'='*60}")

        for rep in range(n_reps):
            config = config_fn()
            config.seed = 42 + rep
            simulator = sim_mod.NMASimulator(config)
            data = simulator.generate()
            true_effects = simulator.get_true_effects()

            # Standard NMA
            try:
                std_effects = run_standard_nma(data, "binary", "A")
                std_metrics = evaluate(std_effects, true_effects)
                std_metrics["method"] = "Standard_NMA"
            except Exception as e:
                std_metrics = {"method": "Standard_NMA", "rmse": np.nan,
                               "bias": np.nan, "coverage": np.nan,
                               "rank_corr": np.nan, "error": str(e)}

            # E-NMA
            try:
                enma_result = enma_mod.run_enma(
                    data, "binary", "A", omega=1.0, n_boot=100, seed=config.seed
                )
                enma_metrics = evaluate(enma_result.treatment_effects, true_effects)
                enma_metrics["method"] = "E-NMA"
            except Exception as e:
                enma_metrics = {"method": "E-NMA", "rmse": np.nan,
                                "bias": np.nan, "coverage": np.nan,
                                "rank_corr": np.nan, "error": str(e)}

            # S-NMA
            try:
                snma_result = snma_mod.run_snma(data, "binary", "A")
                snma_metrics = evaluate(snma_result.treatment_effects, true_effects)
                snma_metrics["method"] = "S-NMA"
                snma_metrics["inconsistency_detected"] = snma_result.inconsistency_detected
                snma_metrics["high_freq_ratio"] = snma_result.high_freq_ratio
            except Exception as e:
                snma_metrics = {"method": "S-NMA", "rmse": np.nan,
                                "bias": np.nan, "coverage": np.nan,
                                "rank_corr": np.nan, "error": str(e)}

            for m in [std_metrics, enma_metrics, snma_metrics]:
                m["scenario"] = scenario_name
                m["replication"] = rep
                all_rows.append(m)

            if (rep + 1) % 10 == 0:
                print(f"  Completed {rep + 1}/{n_reps}")

    return pd.DataFrame(all_rows)


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise comparison results across replications."""
    summary = df.groupby(["scenario", "method"]).agg(
        rmse_mean=("rmse", "mean"),
        rmse_sd=("rmse", "std"),
        bias_mean=("bias", "mean"),
        coverage_mean=("coverage", "mean"),
        rank_corr_mean=("rank_corr", "mean"),
        n_reps=("rmse", "count")
    ).reset_index()
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time as _time

    print("\n" + "=" * 73)
    print("  E-NMA vs S-NMA vs Standard NMA: HEAD-TO-HEAD COMPARISON")
    print("=" * 73 + "\n")

    n_reps = 100  # Scaled up for manuscript (was 20)
    t0 = _time.time()
    results = run_comparison(n_reps=n_reps)
    elapsed = _time.time() - t0
    print(f"\nTotal wall-clock time: {elapsed:.1f} seconds ({elapsed/60:.1f} min)")

    # Save raw results
    results.to_csv(OUTPUT_DIR / "raw_comparison_results.csv", index=False)
    print(f"\nRaw results saved to {OUTPUT_DIR / 'raw_comparison_results.csv'}")

    # Summary
    summary = summarise(results)
    summary.to_csv(OUTPUT_DIR / "comparison_summary.csv", index=False)
    print(f"Summary saved to {OUTPUT_DIR / 'comparison_summary.csv'}\n")

    print("=" * 73)
    print("  SUMMARY")
    print("=" * 73)
    print(summary.to_string(index=False))

    print("\n" + "=" * 73)
    print("  Comparison complete.")
    print("=" * 73 + "\n")
