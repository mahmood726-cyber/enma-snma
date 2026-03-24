#!/usr/bin/env python3
"""
NMA Methods Research: Method Evaluator (Step 3b)
Purpose: Test NMA methods on simulated data and evaluate performance against ground truth

Part of the E-NMA / S-NMA project.
Author: Mahmood Ahmad
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import json

# Set up paths -- relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "simulations"


@dataclass
class MethodResults:
    """Results from a single NMA method"""
    method_name: str
    status: str  # success, error, not_implemented
    treatment_effects: pd.DataFrame = None
    rankings: Dict[str, float] = None
    inconsistency_p: float = None
    heterogeneity_tau2: float = None
    convergence_stats: Dict = None
    runtime_seconds: float = None
    error_message: str = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class EvaluationMetrics:
    """Performance metrics for a method"""
    method_name: str
    bias_mean: float = None
    bias_sd: float = None
    rmse: float = None
    coverage: float = None
    width_mean: float = None
    rank_correlation: float = None
    top_ranked_correct: bool = None
    mean_absolute_rank_error: float = None
    sucra_correlation: float = None
    inconsistency_detected: bool = None
    convergence_successful: bool = None


class MethodEvaluator:
    """
    Evaluate NMA method performance against known ground truth

    Compares method results to true effects from simulation
    """

    def __init__(self, simulated_data: pd.DataFrame,
                 true_effects: pd.DataFrame,
                 network_info: Dict):
        """
        Args:
            simulated_data: Arm-based data from simulation
            true_effects: True treatment effects
            network_info: Network metadata
        """
        self.data = simulated_data
        self.true_effects = true_effects
        self.network_info = network_info
        self.reference_treatment = "A"

        # Get true rankings
        self.true_rankings = self._compute_true_rankings()

    def _compute_true_rankings(self) -> Dict[str, int]:
        """Compute true treatment rankings from true effects"""
        # Lower effect = better (negative log OR means better outcome)
        sorted_treatments = sorted(self.true_effects['treatment'].tolist(),
                                   key=lambda t: self.true_effects[
                                       self.true_effects['treatment'] == t]['true_effect'].values[0])
        return {t: i+1 for i, t in enumerate(sorted_treatments)}

    def evaluate_method(self, results: MethodResults) -> EvaluationMetrics:
        """
        Evaluate method performance against ground truth

        Args:
            results: Results from NMA method

        Returns:
            EvaluationMetrics with performance measures
        """
        metrics = EvaluationMetrics(method_name=results.method_name)

        if results.status != "success" or results.treatment_effects is None:
            return metrics

        # 1. Treatment Effect Recovery
        effect_metrics = self._evaluate_effect_recovery(results)
        metrics.bias_mean = effect_metrics['bias_mean']
        metrics.bias_sd = effect_metrics['bias_sd']
        metrics.rmse = effect_metrics['rmse']
        metrics.coverage = effect_metrics['coverage']
        metrics.width_mean = effect_metrics['width_mean']

        # 2. Ranking Accuracy
        ranking_metrics = self._evaluate_ranking_accuracy(results)
        metrics.rank_correlation = ranking_metrics['rank_correlation']
        metrics.top_ranked_correct = ranking_metrics['top_ranked_correct']
        metrics.mean_absolute_rank_error = ranking_metrics['mean_absolute_rank_error']
        metrics.sucra_correlation = ranking_metrics['sucra_correlation']

        # 3. Inconsistency Detection
        if self.network_info.get('has_inconsistency', False):
            metrics.inconsistency_detected = (
                results.inconsistency_p is not None and
                results.inconsistency_p < 0.05
            )
        else:
            # Type I error: should NOT detect inconsistency
            metrics.inconsistency_detected = (
                results.inconsistency_p is not None and
                results.inconsistency_p < 0.05
            )

        # 4. Convergence
        metrics.convergence_successful = self._check_convergence(results)

        return metrics

    def _evaluate_effect_recovery(self, results: MethodResults) -> Dict:
        """Evaluate treatment effect estimation"""
        # This would compare estimated effects to true effects
        # For now, return placeholder values

        # Merge estimated effects with true effects
        merged = results.treatment_effects.merge(
            self.true_effects,
            on='treatment',
            how='inner',
            suffixes=('_est', '_true')
        )

        if len(merged) == 0:
            return {
                'bias_mean': np.nan,
                'bias_sd': np.nan,
                'rmse': np.nan,
                'coverage': np.nan,
                'width_mean': np.nan
            }

        # Calculate bias (estimated - true)
        if 'effect_est' in merged.columns and 'effect_true' in merged.columns:
            bias = merged['effect_est'] - merged['true_effect']
            bias_mean = bias.mean()
            bias_sd = bias.std()
            rmse = np.sqrt((bias ** 2).mean())

            # Coverage (if CI available)
            coverage = np.nan
            if 'ci_lower' in merged.columns and 'ci_upper' in merged.columns:
                coverage = np.mean(
                    (merged['true_effect'] >= merged['ci_lower']) &
                    (merged['true_effect'] <= merged['ci_upper'])
                )

            # CI width
            width_mean = np.nan
            if 'ci_lower' in merged.columns and 'ci_upper' in merged.columns:
                width_mean = (merged['ci_upper'] - merged['ci_lower']).mean()

            return {
                'bias_mean': bias_mean,
                'bias_sd': bias_sd,
                'rmse': rmse,
                'coverage': coverage,
                'width_mean': width_mean
            }

        return {
            'bias_mean': np.nan,
            'bias_sd': np.nan,
            'rmse': np.nan,
            'coverage': np.nan,
            'width_mean': np.nan
        }

    def _evaluate_ranking_accuracy(self, results: MethodResults) -> Dict:
        """Evaluate treatment ranking accuracy"""
        if results.rankings is None:
            return {
                'rank_correlation': np.nan,
                'top_ranked_correct': None,
                'mean_absolute_rank_error': np.nan,
                'sucra_correlation': np.nan
            }

        # Convert rankings to ordered list
        estimated_ranks = results.rankings

        # Calculate rank correlation
        true_ranks = [self.true_rankings.get(t, np.nan)
                      for t in estimated_ranks.keys()]
        est_ranks = list(estimated_ranks.values())

        # Remove NaN values
        valid_mask = [(not np.isnan(t)) and (not np.isnan(e))
                      for t, e in zip(true_ranks, est_ranks)]
        true_ranks_valid = [t for t, v in zip(true_ranks, valid_mask) if v]
        est_ranks_valid = [e for e, v in zip(est_ranks, valid_mask) if v]

        if len(true_ranks_valid) > 1:
            rank_correlation = np.corrcoef(true_ranks_valid, est_ranks_valid)[0, 1]
        else:
            rank_correlation = np.nan

        # Top-ranked correct?
        top_treatment_true = min(self.true_rankings,
                                key=self.true_rankings.get)
        top_treatment_est = min(estimated_ranks,
                               key=estimated_ranks.get) if estimated_ranks else None
        top_ranked_correct = (top_treatment_true == top_treatment_est)

        # Mean absolute rank error
        mae = np.mean([abs(t - e) for t, e in zip(true_ranks_valid, est_ranks_valid)])

        # SUCRA correlation (placeholder - would need actual SUCRA values)
        sucra_correlation = np.nan

        return {
            'rank_correlation': rank_correlation,
            'top_ranked_correct': top_ranked_correct,
            'mean_absolute_rank_error': mae,
            'sucra_correlation': sucra_correlation
        }

    def _check_convergence(self, results: MethodResults) -> bool:
        """Check if MCMC converged"""
        if results.convergence_stats is None:
            return True  # Frequentist methods don't have convergence issues

        rhat = results.convergence_stats.get('rhat', None)
        if rhat is not None:
            return rhat < 1.05

        return True


class SimulationStudyRunner:
    """
    Run complete simulation study evaluating NMA methods

    Generates data, runs methods, evaluates performance
    """

    def __init__(self):
        self.results = []

    def run_single_replication(self, scenario_name: str,
                              seed: int) -> Dict:
        """
        Run a single simulation replication

        Args:
            scenario_name: Name of scenario
            seed: Random seed

        Returns:
            Dictionary with results
        """
        # Load simulated data
        scenario_dir = OUTPUT_DIR / "data" / scenario_name
        data_file = scenario_dir / f"sim_seed{seed}.csv"
        effects_file = scenario_dir / f"true_effects_seed{seed}.csv"
        info_file = scenario_dir / f"network_info_seed{seed}.json"

        if not data_file.exists():
            return {"error": f"Data file not found: {data_file}"}

        data = pd.read_csv(data_file)
        true_effects = pd.read_csv(effects_file)

        with open(info_file, 'r') as f:
            network_info = json.load(f)

        # Create evaluator
        evaluator = MethodEvaluator(data, true_effects, network_info)

        # Run methods (placeholder - would actually call R packages)
        method_results = {}

        # Placeholder for netmeta
        netmeta_result = MethodResults(
            method_name="netmeta",
            status="not_implemented",
            runtime_seconds=0.0
        )
        method_results["netmeta"] = netmeta_result

        # Placeholder for gemtc
        gemtc_result = MethodResults(
            method_name="gemtc",
            status="not_implemented",
            runtime_seconds=0.0
        )
        method_results["gemtc"] = gemtc_result

        # Evaluate each method
        evaluations = {}
        for method_name, result in method_results.items():
            evaluations[method_name] = evaluator.evaluate_method(result)

        return {
            "scenario": scenario_name,
            "seed": seed,
            "network_info": network_info,
            "method_results": method_results,
            "evaluations": evaluations
        }

    def run_scenario_study(self, scenario_name: str,
                          n_reps: int = 100) -> pd.DataFrame:
        """
        Run all replications for a scenario

        Args:
            scenario_name: Name of scenario
            n_reps: Number of replications

        Returns:
            DataFrame with summary results
        """
        results = []

        for rep in range(n_reps):
            seed = 42 + rep
            result = self.run_single_replication(scenario_name, seed)

            # Extract key metrics
            for method_name, eval in result["evaluations"].items():
                results.append({
                    "scenario": scenario_name,
                    "replication": rep,
                    "method": method_name,
                    "bias_mean": eval.bias_mean,
                    "rmse": eval.rmse,
                    "coverage": eval.coverage,
                    "rank_correlation": eval.rank_correlation,
                    "top_ranked_correct": eval.top_ranked_correct,
                    "inconsistency_detected": eval.inconsistency_detected,
                })

        return pd.DataFrame(results)

    def generate_summary_report(self) -> pd.DataFrame:
        """Generate summary report across all scenarios"""
        # This would aggregate results across scenarios
        # Placeholder for now

        scenarios = ["baseline", "sparse", "inconsistency_0.3",
                    "high_heterogeneity", "star"]

        summary_data = []

        for scenario in scenarios:
            for method in ["netmeta", "gemtc", "multinma", "bnma"]:
                summary_data.append({
                    "scenario": scenario,
                    "method": method,
                    "bias_mean": np.nan,
                    "rmse": np.nan,
                    "coverage": np.nan,
                    "rank_correlation": np.nan,
                    "power": np.nan,  # For inconsistency scenarios
                    "type_I_error": np.nan,  # For consistent scenarios
                })

        return pd.DataFrame(summary_data)


# ============================================================================
# DEMONSTRATION
# ============================================================================

if __name__ == "__main__":

    print("\n" + "="*73)
    print("  NMA METHOD EVALUATOR - DEMONSTRATION")
    print("="*73 + "\n")

    # Test single replication
    print("Testing single replication...\n")

    result = SimulationStudyRunner().run_single_replication("baseline", 42)

    print(f"Scenario: {result['scenario']}")
    print(f"Seed: {result['seed']}")
    print(f"\nNetwork Info:")
    for key, value in result['network_info'].items():
        if key != 'connectivity_type':
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    print(f"\nMethod Evaluations:")
    for method_name, eval in result["evaluations"].items():
        print(f"\n  {method_name}:")
        print(f"    Status: {result['method_results'][method_name].status}")
        print(f"    Rank correlation: {eval.rank_correlation}")
        print(f"    Top ranked correct: {eval.top_ranked_correct}")

    print("\n" + "="*73)
    print("Note: Method implementations are placeholders")
    print("Actual R package integration would go here")
    print("="*73 + "\n")
