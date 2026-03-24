#!/usr/bin/env python3
"""
NMA Methods Research: Simulation Engine (Step 3)
Purpose: Generate synthetic NMA data with known properties for method testing

Part of the E-NMA / S-NMA project.
Author: Mahmood Ahmad
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json

# Set up paths -- relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "simulations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Set random seed for reproducibility
np.random.seed(42)


@dataclass
class NetworkStructure:
    """Define network topology"""
    name: str
    n_treatments: int
    n_studies: int
    arms_per_study: tuple = (2, 5)  # min and max arms
    connectivity: str = "dense"  # dense, sparse, star, loop, scale_free
    treatment_names: Optional[List[str]] = None


@dataclass
class TrueEffects:
    """True treatment effects for simulation"""
    reference_treatment: str = "A"
    effects: Dict[str, float] = field(default_factory=dict)
    baseline_mean: float = 0.0
    baseline_sd: float = 1.0


@dataclass
class Heterogeneity:
    """Between-study heterogeneity parameters"""
    tau_squared: float = 0.04  # Between-study variance
    i_squared: float = 0.5     # Heterogeneity index


@dataclass
class Inconsistency:
    """Inconsistency parameters"""
    has_inconsistency: bool = False
    magnitude: float = 0.0     # log-OR scale
    affected_loops: List[str] = field(default_factory=list)


@dataclass
class SimulationConfig:
    """Complete simulation configuration"""
    network: NetworkStructure
    true_effects: TrueEffects
    heterogeneity: Heterogeneity
    inconsistency: Inconsistency
    outcome_type: str = "binary"  # binary, continuous
    sample_size_range: tuple = (50, 200)
    within_study_sd: float = 1.0  # for continuous outcomes
    seed: int = 42


class NMASimulator:
    """
    Network Meta-Analysis Data Simulator

    Generates synthetic NMA datasets with known properties for method testing.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.treatments = self._generate_treatment_names()
        self.studies = []
        self.study_data = []
        self.generated_data = None

    def _generate_treatment_names(self) -> List[str]:
        """Generate treatment names"""
        if self.config.network.treatment_names:
            return self.config.network.treatment_names
        n = self.config.network.n_treatments
        return [chr(65 + i) for i in range(n)]  # A, B, C, ...

    def _generate_network_structure(self) -> List[Dict]:
        """
        Generate study network structure

        Returns list of studies with their assigned treatments
        """
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments
        connectivity = self.config.network.connectivity

        studies = []

        if connectivity == "star":
            # Star network: all studies include reference treatment A
            for i in range(n_studies):
                n_arms = np.random.randint(*self.config.network.arms_per_study)
                n_arms = min(n_arms, n_treatments)
                treatments = ["A"]
                if n_arms > 1:
                    other_treatments = [t for t in self.treatments if t != "A"]
                    selected = np.random.choice(other_treatments,
                                              size=min(n_arms-1, len(other_treatments)),
                                              replace=False)
                    treatments.extend(selected.tolist())
                studies.append({
                    "study_id": f"S{i+1:03d}",
                    "treatments": treatments
                })

        elif connectivity == "dense":
            # Dense network: many connections, random assignment
            for i in range(n_studies):
                n_arms = np.random.randint(*self.config.network.arms_per_study)
                n_arms = min(n_arms, n_treatments)
                treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()
                studies.append({
                    "study_id": f"S{i+1:03d}",
                    "treatments": treatments
                })

        elif connectivity == "sparse":
            # Sparse network: limit connections
            used_pairs = set()
            for i in range(n_studies):
                n_arms = np.random.randint(2, 3)  # Mostly 2-arm studies
                treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()

                # Check if this combination is overused
                pair_key = tuple(sorted(treatments))
                if pair_key in used_pairs and np.random.random() < 0.7:
                    # Skip this combination, create another
                    treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()

                used_pairs.add(tuple(sorted(treatments)))
                studies.append({
                    "study_id": f"S{i+1:03d}",
                    "treatments": treatments
                })

        elif connectivity == "loop":
            # Loop network: create closed loops
            # For 5 treatments, create loops like A-B-C-A
            base_loops = [
                ["A", "B", "C"],
                ["B", "C", "D"],
                ["C", "D", "E"],
                ["A", "C", "E"],
            ]

            for i in range(n_studies):
                loop_idx = i % len(base_loops)
                base_loop = base_loops[loop_idx]
                n_arms = np.random.randint(2, len(base_loop) + 1)
                treatments = np.random.choice(base_loop, size=n_arms, replace=False).tolist()
                studies.append({
                    "study_id": f"S{i+1:03d}",
                    "treatments": treatments
                })

        else:  # scale_free or default
            # Scale-free: some treatments are hubs
            hub_treatments = self.treatments[:2]  # First two are hubs

            for i in range(n_studies):
                # 70% chance to include a hub
                if np.random.random() < 0.7:
                    treatments = [np.random.choice(hub_treatments)]
                    n_arms = np.random.randint(*self.config.network.arms_per_study)
                    n_arms = min(n_arms, n_treatments)
                    remaining = [t for t in self.treatments if t not in treatments]
                    if remaining:
                        extra = np.random.choice(remaining,
                                                size=min(n_arms-1, len(remaining)),
                                                replace=False).tolist()
                        treatments.extend(extra)
                else:
                    n_arms = np.random.randint(*self.config.network.arms_per_study)
                    treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()

                studies.append({
                    "study_id": f"S{i+1:03d}",
                    "treatments": treatments
                })

        return studies

    def _generate_true_effects(self) -> Dict[str, float]:
        """
        Generate true treatment effects

        Returns dictionary of treatment effects (log-OR scale)
        relative to reference treatment A
        """
        effects = {"A": 0.0}  # Reference treatment
        n_treatments = len(self.treatments)

        # Generate effects from a distribution
        # Most treatments are similar to reference, some are better/worse
        for treatment in self.treatments[1:]:
            if treatment in self.config.true_effects.effects:
                effects[treatment] = self.config.true_effects.effects[treatment]
            else:
                # Random effect: N(0, 0.3) - moderate variation
                effect = np.random.normal(0, 0.3)
                effects[treatment] = effect

        return effects

    def _apply_inconsistency(self, effects: Dict[str, float],
                           study_treatments: List[str]) -> Dict[str, float]:
        """
        Apply inconsistency to specific studies

        Modifies effects for studies in affected loops
        """
        if not self.config.inconsistency.has_inconsistency:
            return effects

        # Check if this study should have inconsistency
        # For simplicity, apply to studies with specific treatment combinations
        study_set = set(study_treatments)

        # Example: Add inconsistency to studies comparing treatments B and C
        if "B" in study_set and "C" in study_set:
            # Modify effect for one treatment in this study
            modified_effects = effects.copy()
            if "B" in modified_effects:
                modified_effects["B"] += self.config.inconsistency.magnitude
            return modified_effects

        return effects

    def _generate_binary_outcome(self, study_id: str, treatment: str,
                                true_effect: float, study_effect: float) -> Dict:
        """
        Generate binary outcome data

        Returns: responders, sample_size
        """
        n = np.random.randint(*self.config.sample_size_range)

        # Calculate probability of response
        # baseline + treatment effect + study effect
        baseline_logit = self.config.true_effects.baseline_mean
        logit = baseline_logit + true_effect + study_effect
        p = 1 / (1 + np.exp(-logit))  # Inverse logit

        # Ensure p is in valid range
        p = np.clip(p, 0.01, 0.99)

        # Generate responders
        r = np.random.binomial(n, p)

        return {
            "study": study_id,
            "treatment": treatment,
            "responders": r,
            "sample_size": n
        }

    def _generate_continuous_outcome(self, study_id: str, treatment: str,
                                    true_effect: float, study_effect: float) -> Dict:
        """
        Generate continuous outcome data

        Returns: mean, standard_deviation, sample_size
        """
        n = np.random.randint(*self.config.sample_size_range)

        # Calculate mean for this arm
        baseline = self.config.true_effects.baseline_mean
        mean = baseline + true_effect + study_effect

        # Generate observed mean
        observed_mean = np.random.normal(mean, self.config.within_study_sd / np.sqrt(n))

        return {
            "study": study_id,
            "treatment": treatment,
            "mean": observed_mean,
            "sd": self.config.within_study_sd,
            "sample_size": n
        }

    def generate(self) -> pd.DataFrame:
        """
        Generate complete NMA dataset

        Returns: DataFrame with arm-based data
        """
        # Reset random seed for reproducibility
        np.random.seed(self.config.seed)

        # Generate network structure
        self.studies = self._generate_network_structure()

        # Generate true treatment effects
        true_effects = self._generate_true_effects()

        # Generate data for each study
        data_rows = []

        for study_info in self.studies:
            study_id = study_info["study_id"]
            treatments = study_info["treatments"]

            # Study-specific random effect (heterogeneity)
            tau = np.sqrt(self.config.heterogeneity.tau_squared)
            study_effect = np.random.normal(0, tau)

            # Apply inconsistency if specified
            effects = self._apply_inconsistency(true_effects, treatments)

            # Generate outcome data for each treatment arm
            for treatment in treatments:
                true_effect = effects.get(treatment, 0.0)

                if self.config.outcome_type == "binary":
                    row = self._generate_binary_outcome(study_id, treatment,
                                                        true_effect, study_effect)
                else:  # continuous
                    row = self._generate_continuous_outcome(study_id, treatment,
                                                           true_effect, study_effect)

                data_rows.append(row)

        self.generated_data = pd.DataFrame(data_rows)
        return self.generated_data

    def get_true_effects(self) -> pd.DataFrame:
        """Get true treatment effects for validation"""
        effects = self._generate_true_effects()
        return pd.DataFrame([
            {"treatment": t, "true_effect": e}
            for t, e in effects.items()
        ])

    def get_network_info(self) -> Dict:
        """Get information about the generated network"""
        if self.generated_data is None:
            self.generate()

        n_studies = self.generated_data["study"].nunique()
        n_treatments = self.generated_data["treatment"].nunique()
        n_arms = len(self.generated_data)

        # Calculate edge connectivity
        treatment_pairs = set()
        for study in self.generated_data["study"].unique():
            study_treatments = self.generated_data[
                self.generated_data["study"] == study]["treatment"].tolist()
            for i in range(len(study_treatments)):
                for j in range(i+1, len(study_treatments)):
                    pair = tuple(sorted([study_treatments[i], study_treatments[j]]))
                    treatment_pairs.add(pair)

        return {
            "n_studies": n_studies,
            "n_treatments": n_treatments,
            "n_arms": n_arms,
            "n_connections": len(treatment_pairs),
            "connectivity_type": self.config.network.connectivity,
            "outcome_type": self.config.outcome_type,
            "has_inconsistency": self.config.inconsistency.has_inconsistency,
            "tau_squared": self.config.heterogeneity.tau_squared,
            "i_squared": self.config.heterogeneity.i_squared
        }


# ============================================================================
# PRE-DEFINED SCENARIOS
# ============================================================================

def create_baseline_scenario() -> SimulationConfig:
    """Scenario 1: Baseline (ideal conditions)"""
    return SimulationConfig(
        network=NetworkStructure(
            name="baseline",
            n_treatments=5,
            n_studies=30,
            arms_per_study=(2, 4),
            connectivity="dense"
        ),
        true_effects=TrueEffects(
            effects={"B": -0.3, "C": -0.5, "D": -0.2, "E": -0.4}
        ),
        heterogeneity=Heterogeneity(tau_squared=0.01, i_squared=0.25),
        inconsistency=Inconsistency(has_inconsistency=False),
        outcome_type="binary",
        seed=42
    )


def create_sparse_network_scenario() -> SimulationConfig:
    """Scenario 2: Sparse network challenge"""
    return SimulationConfig(
        network=NetworkStructure(
            name="sparse",
            n_treatments=5,
            n_studies=15,
            arms_per_study=(2, 2),
            connectivity="sparse"
        ),
        true_effects=TrueEffects(
            effects={"B": -0.4, "C": -0.6, "D": -0.3, "E": -0.5}
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=Inconsistency(has_inconsistency=False),
        outcome_type="binary",
        sample_size_range=(30, 100),
        seed=43
    )


def create_inconsistency_scenario(magnitude: float = 0.3) -> SimulationConfig:
    """Scenario 3: Inconsistency detection"""
    return SimulationConfig(
        network=NetworkStructure(
            name=f"inconsistency_{magnitude}",
            n_treatments=5,
            n_studies=30,
            arms_per_study=(2, 3),
            connectivity="loop"
        ),
        true_effects=TrueEffects(
            effects={"B": -0.3, "C": -0.5, "D": -0.2, "E": -0.4}
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=Inconsistency(
            has_inconsistency=True,
            magnitude=magnitude,
            affected_loops=["B-C"]
        ),
        outcome_type="binary",
        seed=44
    )


def create_high_heterogeneity_scenario() -> SimulationConfig:
    """Scenario 4: High heterogeneity"""
    return SimulationConfig(
        network=NetworkStructure(
            name="high_heterogeneity",
            n_treatments=5,
            n_studies=30,
            arms_per_study=(2, 4),
            connectivity="dense"
        ),
        true_effects=TrueEffects(
            effects={"B": -0.3, "C": -0.5, "D": -0.2, "E": -0.4}
        ),
        heterogeneity=Heterogeneity(tau_squared=0.16, i_squared=0.75),
        inconsistency=Inconsistency(has_inconsistency=False),
        outcome_type="binary",
        seed=45
    )


def create_star_network_scenario() -> SimulationConfig:
    """Scenario 5: Star network"""
    return SimulationConfig(
        network=NetworkStructure(
            name="star",
            n_treatments=5,
            n_studies=30,
            arms_per_study=(2, 3),
            connectivity="star"
        ),
        true_effects=TrueEffects(
            effects={"B": -0.3, "C": -0.5, "D": -0.2, "E": -0.4}
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=Inconsistency(has_inconsistency=False),
        outcome_type="binary",
        seed=46
    )


# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def run_single_simulation(config: SimulationConfig, save: bool = True) -> Dict:
    """
    Run a single simulation

    Returns: Dictionary with data, true effects, and network info
    """
    simulator = NMASimulator(config)
    data = simulator.generate()
    true_effects = simulator.get_true_effects()
    network_info = simulator.get_network_info()

    result = {
        "data": data,
        "true_effects": true_effects,
        "network_info": network_info,
        "config": config
    }

    if save:
        scenario_dir = OUTPUT_DIR / "data" / config.network.name
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Save data
        data_file = scenario_dir / f"sim_seed{config.seed}.csv"
        data.to_csv(data_file, index=False)

        # Save true effects
        effects_file = scenario_dir / f"true_effects_seed{config.seed}.csv"
        true_effects.to_csv(effects_file, index=False)

        # Save network info
        info_file = scenario_dir / f"network_info_seed{config.seed}.json"
        with open(info_file, 'w') as f:
            # Convert to serializable format
            info_serializable = {k: (str(v) if isinstance(v, (pd.DataFrame, np.integer))
                                    else v) for k, v in network_info.items()}
            json.dump(info_serializable, f, indent=2)

    return result


def run_simulation_study(scenarios: List[SimulationConfig],
                       n_reps: int = 100) -> Dict:
    """
    Run complete simulation study

    Args:
        scenarios: List of simulation configurations
        n_reps: Number of replications per scenario

    Returns: Dictionary with all results
    """
    all_results = {}

    for scenario in scenarios:
        print(f"\nRunning scenario: {scenario.network.name}")
        scenario_results = []

        for rep in range(n_reps):
            # Update seed for each replication
            scenario.seed = 42 + rep

            result = run_single_simulation(scenario, save=True)
            scenario_results.append(result)

            if (rep + 1) % 10 == 0:
                print(f"  Completed {rep + 1}/{n_reps} replications")

        all_results[scenario.network.name] = scenario_results

    return all_results


# ============================================================================
# DEMONSTRATION
# ============================================================================

if __name__ == "__main__":

    print("\n" + "="*73)
    print("  NMA SIMULATION ENGINE - DEMONSTRATION")
    print("="*73 + "\n")

    # Test each scenario
    scenarios_to_test = [
        ("Baseline (Ideal)", create_baseline_scenario()),
        ("Sparse Network", create_sparse_network_scenario()),
        ("Inconsistency (Medium)", create_inconsistency_scenario(0.3)),
        ("High Heterogeneity", create_high_heterogeneity_scenario()),
        ("Star Network", create_star_network_scenario()),
    ]

    for name, config in scenarios_to_test:
        print(f"\n{'='*73}")
        print(f"Scenario: {name}")
        print(f"{'='*73}")

        result = run_single_simulation(config, save=True)

        print(f"\nGenerated Data:")
        print(f"  Studies: {result['network_info']['n_studies']}")
        print(f"  Treatments: {result['network_info']['n_treatments']}")
        print(f"  Total arms: {result['network_info']['n_arms']}")
        print(f"  Connections: {result['network_info']['n_connections']}")
        print(f"  Outcome type: {result['network_info']['outcome_type']}")
        print(f"  Has inconsistency: {result['network_info']['has_inconsistency']}")

        print(f"\nTrue Effects:")
        print(result['true_effects'].to_string(index=False))

        print(f"\nFirst 10 rows of data:")
        print(result['data'].head(10).to_string(index=False))

    print(f"\n{'='*73}")
    print("Simulation complete!")
    print(f"Data saved to: {OUTPUT_DIR / 'data'}")
    print(f"{'='*73}\n")
