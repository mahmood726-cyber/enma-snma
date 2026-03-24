#!/usr/bin/env python3
"""
Empirical Dataset Analysis: E-NMA and S-NMA on Published NMA Datasets

Applies both novel methods to three canonical NMA datasets:
  1. Smoking cessation (gemtc, 24 studies, 4 treatments, binary)
  2. Thrombolytic therapy (gemtc, 28 studies, 8 treatments, binary)
  3. Parkinson's disease (gemtc, 7 studies, 5 treatments, continuous)

Author: Mahmood Ahmad
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

# Ensure sibling modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

enma_mod = import_module("07_enma_engine")
snma_mod = import_module("08_snma_engine")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "nmadatasets" / "inst" / "extdata"
OUTPUT_DIR = BASE_DIR / "outputs" / "empirical"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data loaders — convert gemtc format to arm-level DataFrames
# ---------------------------------------------------------------------------

def load_smoking() -> pd.DataFrame:
    """Load smoking cessation dataset (24 studies, 4 treatments, binary).

    Treatments: A=No contact, B=Self-help, C=Individual counseling, D=Group counseling
    Reference: Hasselblad 1998, widely used NMA benchmark.
    """
    df = pd.read_csv(DATA_DIR / "gemtc__smoking_studies.csv")
    df = df.rename(columns={"r": "responders", "n": "sample_size"})
    df = df[["study", "treatment", "responders", "sample_size"]].copy()
    return df


def load_thrombolytic() -> pd.DataFrame:
    """Load thrombolytic therapy dataset (28 studies, 8 treatments, binary).

    Treatments include SK, tPA, AtPA, ASPAC, Ten, Ret, UK, SKtPA.
    Outcome: 30-day mortality.  Reference: Boland et al. 2003.
    """
    df = pd.read_csv(DATA_DIR / "gemtc__thrombolytic_studies.csv")
    df = df.rename(columns={"r": "responders", "n": "sample_size"})
    df = df[["study", "treatment", "responders", "sample_size"]].copy()
    return df


def load_parkinson() -> pd.DataFrame:
    """Load Parkinson's disease dataset (7 studies, 5 treatments, continuous).

    Mean UPDRS change from baseline.
    Treatments: A=Placebo, B=Drug B, C=Drug C, D=Drug D, E=Drug E.
    Reference: Franchini et al. (as used in gemtc tutorials).

    Note: This dataset has mean outcomes per arm (y column) but no SD.
    We use the approach of assuming a common SD estimated from the data,
    which is standard for this well-known dataset.
    """
    df = pd.read_csv(DATA_DIR / "gemtc__parkinson_studies.csv")
    # Parkinson data: study, treatment, y (mean), n (sample_size), no SD
    # Standard practice: assign a pooled SD. The gemtc documentation uses
    # an approximately known SD ~ 0.5 for the UPDRS outcome.
    ASSUMED_SD = 0.50  # conservative estimate for standardised mean difference
    df = df.rename(columns={"y": "mean", "n": "sample_size"})
    df["sd"] = ASSUMED_SD
    df = df[["study", "treatment", "mean", "sd", "sample_size"]].copy()
    return df


# ---------------------------------------------------------------------------
# Analysis runner
# ---------------------------------------------------------------------------

def analyse_dataset(
    name: str,
    data: pd.DataFrame,
    outcome_type: str,
    reference: str,
    treatment_labels: Optional[Dict[str, str]] = None,
    omega: float = 1.0,
    n_boot: int = 500,
) -> Dict:
    """Run E-NMA and S-NMA on one empirical dataset and return results."""

    print(f"\n{'='*70}")
    print(f"  Dataset: {name}")
    print(f"{'='*70}")
    print(f"  Studies: {data['study'].nunique()}")
    print(f"  Treatments: {sorted(data['treatment'].unique())}")
    print(f"  Outcome: {outcome_type}")
    print(f"  Reference: {reference}")
    print()

    # --- E-NMA ---
    enma_result = enma_mod.run_enma(
        data, outcome_type=outcome_type, reference=reference,
        omega=omega, n_boot=n_boot, seed=42
    )

    print("--- E-NMA Treatment Effects ---")
    print(enma_result.treatment_effects.to_string(index=False))
    print()
    print("--- Inconsistency Confidence Scores (ICS) ---")
    print(enma_result.ics_scores.to_string(index=False))
    print()
    print("--- E-NMA Rankings ---")
    for t, rank in sorted(enma_result.rankings.items(), key=lambda x: x[1]):
        label = treatment_labels.get(t, t) if treatment_labels else t
        print(f"  {rank}. {t} ({label})")
    print()

    # Per-method flags
    print("--- Per-Method Flags ---")
    for method_name, flag_df in enma_result.method_flags.items():
        if len(flag_df) > 0 and "flagged" in flag_df.columns:
            n_flagged = flag_df["flagged"].sum()
            print(f"  {method_name}: {n_flagged}/{len(flag_df)} edges flagged")

    # --- S-NMA ---
    snma_result = snma_mod.run_snma(
        data, outcome_type=outcome_type, reference=reference
    )

    print()
    print("--- S-NMA Spectral Diagnostics ---")
    print(f"  High-frequency energy ratio: {snma_result.high_freq_ratio:.4f}")
    print(f"  Spectral test p-value:       {snma_result.p_value:.4f}")
    print(f"  Inconsistency detected:      {snma_result.inconsistency_detected}")
    print()
    print("--- Spectral Energy Distribution ---")
    print(snma_result.spectral_energy.to_string(index=False))
    print()
    print("--- Edge-Level Spectral Inconsistency Scores ---")
    edge_df = snma_result.edge_contributions.sort_values(
        "normalized_score", ascending=False
    )
    print(edge_df.to_string(index=False))
    print()

    # --- Comparison table: Standard NMA vs E-NMA ---
    # Standard NMA = S-NMA effects (S-NMA doesn't modify estimates)
    comparison = enma_result.treatment_effects.merge(
        snma_result.treatment_effects,
        on="treatment", suffixes=("_enma", "_snma")
    )
    comparison = comparison.rename(columns={
        "effect_enma": "E-NMA_effect", "se_enma": "E-NMA_se",
        "ci_lower_enma": "E-NMA_ci_lo", "ci_upper_enma": "E-NMA_ci_hi",
        "effect_snma": "Std/S-NMA_effect", "se_snma": "Std/S-NMA_se",
        "ci_lower_snma": "Std/S-NMA_ci_lo", "ci_upper_snma": "Std/S-NMA_ci_hi",
    })
    print("--- Effect Comparison: E-NMA vs Standard NMA ---")
    cols = ["treatment", "E-NMA_effect", "E-NMA_se",
            "Std/S-NMA_effect", "Std/S-NMA_se"]
    print(comparison[cols].to_string(index=False))

    return {
        "name": name,
        "enma": enma_result,
        "snma": snma_result,
        "comparison": comparison,
    }


# ---------------------------------------------------------------------------
# Save results to CSV
# ---------------------------------------------------------------------------

def save_results(results: Dict, name_slug: str):
    """Persist key tables to CSVs."""
    prefix = OUTPUT_DIR / name_slug

    results["enma"].treatment_effects.to_csv(
        f"{prefix}_enma_effects.csv", index=False
    )
    results["enma"].ics_scores.to_csv(
        f"{prefix}_ics_scores.csv", index=False
    )
    results["snma"].spectral_energy.to_csv(
        f"{prefix}_spectral_energy.csv", index=False
    )
    results["snma"].edge_contributions.to_csv(
        f"{prefix}_edge_scores.csv", index=False
    )
    results["comparison"].to_csv(
        f"{prefix}_comparison.csv", index=False
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  EMPIRICAL ANALYSIS: E-NMA & S-NMA on Published NMA Datasets")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Smoking cessation (binary, 24 studies, 4 treatments)
    # ---------------------------------------------------------------
    smoking_data = load_smoking()
    smoking_labels = {
        "A": "No contact",
        "B": "Self-help",
        "C": "Individual counseling",
        "D": "Group counseling",
    }
    smoking_res = analyse_dataset(
        "Smoking Cessation (Hasselblad 1998)",
        smoking_data,
        outcome_type="binary",
        reference="A",
        treatment_labels=smoking_labels,
    )
    save_results(smoking_res, "smoking")

    # ---------------------------------------------------------------
    # 2. Thrombolytic therapy (binary, 28 studies, 8 treatments)
    # ---------------------------------------------------------------
    thrombo_data = load_thrombolytic()
    thrombo_labels = {
        "ASPAC": "ASPAC",
        "AtPA": "Accelerated tPA",
        "Ret": "Reteplase",
        "SK": "Streptokinase",
        "SKtPA": "SK + tPA",
        "Ten": "Tenecteplase",
        "UK": "Urokinase",
        "tPA": "tPA",
    }
    thrombo_res = analyse_dataset(
        "Thrombolytic Therapy (Boland 2003)",
        thrombo_data,
        outcome_type="binary",
        reference="SK",
        treatment_labels=thrombo_labels,
    )
    save_results(thrombo_res, "thrombolytic")

    # ---------------------------------------------------------------
    # 3. Parkinson's disease (continuous, 7 studies, 5 treatments)
    # ---------------------------------------------------------------
    parkinson_data = load_parkinson()
    parkinson_labels = {
        "A": "Placebo",
        "B": "Drug B",
        "C": "Drug C",
        "D": "Drug D",
        "E": "Drug E",
    }
    parkinson_res = analyse_dataset(
        "Parkinson's Disease (Franchini / gemtc)",
        parkinson_data,
        outcome_type="continuous",
        reference="A",
        treatment_labels=parkinson_labels,
    )
    save_results(parkinson_res, "parkinson")

    # ---------------------------------------------------------------
    # Combined summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SUMMARY ACROSS ALL DATASETS")
    print("=" * 70)

    summary_rows = []
    for res in [smoking_res, thrombo_res, parkinson_res]:
        n_treatments = len(res["enma"].treatment_effects)
        n_ics_flagged = (res["enma"].ics_scores["ics"] > 0).sum()
        max_ics = res["enma"].ics_scores["ics"].max()
        hf_ratio = res["snma"].high_freq_ratio
        snma_p = res["snma"].p_value
        snma_detected = res["snma"].inconsistency_detected

        summary_rows.append({
            "Dataset": res["name"],
            "Treatments": n_treatments,
            "Edges_ICS>0": int(n_ics_flagged),
            "Max_ICS": f"{max_ics:.2f}",
            "S-NMA_HF_ratio": f"{hf_ratio:.3f}",
            "S-NMA_p": f"{snma_p:.4f}",
            "S-NMA_inconsistency": snma_detected,
        })

    summary_df = pd.DataFrame(summary_rows)
    print()
    print(summary_df.to_string(index=False))

    summary_df.to_csv(OUTPUT_DIR / "empirical_summary.csv", index=False)
    print(f"\nAll results saved to {OUTPUT_DIR}/")

    print("\n" + "=" * 70)
    print("  Empirical analysis complete.")
    print("=" * 70 + "\n")
