#!/usr/bin/env python3
"""
NMA Methods Research: Expanded Simulation Engine
Purpose: Generate diverse NMA networks with complex structures for comprehensive method testing

Part of the E-NMA / S-NMA project.
Author: Mahmood Ahmad
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
import json
from collections import defaultdict
import itertools

# Set up paths -- relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "simulations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)


# ============================================================================
# ENHANCED DATA STRUCTURES
# ============================================================================

@dataclass
class NetworkStructure:
    """Define network topology with enhanced options"""
    name: str
    n_treatments: int
    n_studies: int
    arms_per_study: tuple = (2, 5)
    connectivity: str = "dense"  # dense, sparse, star, loop, scale_free, small_world, geometric, bipartite
    treatment_names: Optional[List[str]] = None
    clustering_coefficient: float = 0.3  # For small-world networks
    preferential_attachment: float = 1.0  # For scale-free networks


@dataclass
class TreatmentEffectPattern:
    """Define treatment effect patterns"""
    pattern: str  # monotonic, u_shaped, threshold, plateau, random, clustered
    min_effect: float = -0.8
    max_effect: float = 0.2
    reference_treatment: str = "A"
    effect_variance: float = 0.1


@dataclass
class InconsistencyPattern:
    """Define inconsistency patterns"""
    pattern: str = "none"  # none, random_loops, design_effects, loop_specific, edge_specific, covariate_interaction
    magnitude: float = 0.0
    proportion_affected: float = 0.2  # Proportion of comparisons with inconsistency
    affected_loops: List[str] = field(default_factory=list)
    direction: str = "random"  # positive, negative, random


@dataclass
class StudySizeDistribution:
    """Define study size distribution"""
    distribution: str = "lognormal"  # uniform, lognormal, bimodal, cluster
    min_size: int = 30
    max_size: int = 500
    mean_size: int = 100
    size_variance: float = 0.5


@dataclass
class Heterogeneity:
    """Between-study heterogeneity parameters"""
    tau_squared: float = 0.04
    i_squared: float = 0.5


@dataclass
class SimulationConfig:
    """Complete simulation configuration with expanded options"""
    network: NetworkStructure
    effect_pattern: TreatmentEffectPattern
    heterogeneity: Heterogeneity = None
    inconsistency: InconsistencyPattern = None
    outcome_type: str = "binary"
    study_size: StudySizeDistribution = None
    within_study_sd: float = 1.0
    baseline_event_rate: float = 0.3
    seed: int = 42

    def __post_init__(self):
        if self.heterogeneity is None:
            self.heterogeneity = Heterogeneity(tau_squared=0.04, i_squared=0.5)
        if self.inconsistency is None:
            self.inconsistency = InconsistencyPattern(pattern="none", magnitude=0.0)
        if self.study_size is None:
            self.study_size = StudySizeDistribution()


# ============================================================================
# EXPANDED NETWORK GENERATOR
# ============================================================================

class ExpandedNetworkGenerator:
    """
    Generate diverse network topologies for NMA simulation

    Supports:
    - Standard topologies (dense, sparse, star, loop)
    - Complex topologies (scale-free, small-world, geometric, bipartite)
    - Realistic clinical networks
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.treatments = self._generate_treatment_names()
        self.study_assignments = []

    def _generate_treatment_names(self) -> List[str]:
        """Generate treatment names"""
        if self.config.network.treatment_names:
            return self.config.network.treatment_names
        n = self.config.network.n_treatments
        # Use more realistic names
        if n <= 26:
            return [chr(65 + i) for i in range(n)]  # A, B, C, ...
        else:
            return [f"T{i+1}" for i in range(n)]

    def generate_network(self) -> List[Dict]:
        """
        Generate study network structure based on topology type

        Returns list of studies with their assigned treatments
        """
        topology = self.config.network.connectivity

        if topology == "dense":
            return self._generate_dense_network()
        elif topology == "sparse":
            return self._generate_sparse_network()
        elif topology == "star":
            return self._generate_star_network()
        elif topology == "loop":
            return self._generate_loop_network()
        elif topology == "scale_free":
            return self._generate_scale_free_network()
        elif topology == "small_world":
            return self._generate_small_world_network()
        elif topology == "geometric":
            return self._generate_geometric_network()
        elif topology == "bipartite":
            return self._generate_bipartite_network()
        elif topology == "clinical_realistic":
            return self._generate_clinical_network()
        elif topology == "disconnected_components":
            return self._generate_disconnected_network()
        else:
            return self._generate_dense_network()

    def _generate_dense_network(self) -> List[Dict]:
        """Dense network: many connections, well-connected"""
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments
        arms_range = self.config.network.arms_per_study

        for i in range(n_studies):
            n_arms = np.random.randint(*arms_range)
            n_arms = min(n_arms, n_treatments)
            treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "dense"
            })

        return studies

    def _generate_sparse_network(self) -> List[Dict]:
        """Sparse network: few connections, limited comparators"""
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Create a chain-like structure with minimal branching
        treatment_chain = self.treatments.copy()
        used_pairs = set()

        for i in range(n_studies):
            # Prefer 2-arm studies
            n_arms = np.random.choice([2, 3], p=[0.7, 0.3])
            n_arms = min(n_arms, n_treatments)

            # Select treatments to maintain sparsity
            if i == 0:
                treatments = treatment_chain[:n_arms]
            else:
                # Include at least one treatment from previous study
                anchor = np.random.choice(studies[-1]["treatments"])
                remaining = [t for t in self.treatments if t != anchor]
                selected = np.random.choice(
                    remaining,
                    size=min(n_arms-1, len(remaining)),
                    replace=False
                ).tolist()
                treatments = [anchor] + selected

            pair_key = tuple(sorted(treatments))
            if pair_key not in used_pairs:
                studies.append({
                    "study_id": f"S{i+1:03d}",
                    "treatments": treatments,
                    "topology": "sparse"
                })
                used_pairs.add(pair_key)

        return studies

    def _generate_star_network(self) -> List[Dict]:
        """Star network: all studies include reference treatment"""
        studies = []
        n_studies = self.config.network.n_studies
        reference = self.treatments[0]  # First treatment is reference
        other_treatments = self.treatments[1:]

        for i in range(n_studies):
            n_arms = np.random.randint(2, min(self.config.network.arms_per_study[1],
                                             len(other_treatments) + 1))

            treatments = [reference]
            if len(other_treatments) > 0:
                selected = np.random.choice(
                    other_treatments,
                    size=min(n_arms-1, len(other_treatments)),
                    replace=False
                ).tolist()
                treatments.extend(selected)

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "star"
            })

        return studies

    def _generate_loop_network(self) -> List[Dict]:
        """Loop network: creates closed loops for inconsistency testing"""
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Create triangular loops
        n_loops = min(n_treatments - 1, n_studies // 3)
        studies_per_loop = n_studies // n_loops if n_loops > 0 else n_studies

        for loop_idx in range(n_loops):
            # Define loop treatments (e.g., A-B-C-A)
            base = loop_idx * 2
            loop_treatments = self.treatments[base:min(base+3, n_treatments)]

            if len(loop_treatments) < 3:
                break

            # Create studies for this loop
            for j in range(studies_per_loop):
                if len(studies) >= n_studies:
                    break

                # Create pairs within the loop
                pair_idx = j % len(loop_treatments)
                treatments = [loop_treatments[pair_idx],
                             loop_treatments[(pair_idx + 1) % len(loop_treatments)]]

                # Add third treatment sometimes
                if np.random.random() < 0.3:
                    third_treatment = loop_treatments[(pair_idx + 2) % len(loop_treatments)]
                    if third_treatment not in treatments:
                        treatments.append(third_treatment)

                studies.append({
                    "study_id": f"S{len(studies)+1:03d}",
                    "treatments": treatments,
                    "topology": "loop",
                    "loop_id": loop_idx
                })

        # Fill remaining studies with random assignments
        while len(studies) < n_studies:
            n_arms = np.random.randint(*self.config.network.arms_per_study)
            n_arms = min(n_arms, n_treatments)
            treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()

            studies.append({
                "study_id": f"S{len(studies)+1:03d}",
                "treatments": treatments,
                "topology": "loop"
            })

        return studies

    def _generate_scale_free_network(self) -> List[Dict]:
        """
        Scale-free network: few hub treatments with many connections
        Follows Barabási-Albert model principles
        """
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Define hub treatments (20% of treatments)
        n_hubs = max(1, n_treatments // 5)
        hubs = self.treatments[:n_hubs]
        non_hubs = self.treatments[n_hubs:]

        # Track treatment degrees
        treatment_degree = {t: 0 for t in self.treatments}

        for i in range(n_studies):
            # Preferential attachment: more connected treatments more likely to be selected
            weights = np.array([1 + treatment_degree[t] for t in self.treatments])
            weights = weights / weights.sum()

            n_arms = np.random.randint(*self.config.network.arms_per_study)
            n_arms = min(n_arms, n_treatments)

            # Select treatments with preferential attachment
            treatments = list(np.random.choice(
                self.treatments,
                size=n_arms,
                replace=False,
                p=weights
            ))

            # Ensure at least one hub is included in most studies
            if len(hubs) > 0 and np.random.random() < 0.7:
                if not any(t in hubs for t in treatments):
                    # Replace one treatment with a hub
                    treatments[0] = np.random.choice(hubs)

            # Update degrees
            for t1 in treatments:
                for t2 in treatments:
                    if t1 != t2:
                        treatment_degree[t1] += 1

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "scale_free",
                "is_hub_study": any(t in hubs for t in treatments)
            })

        return studies

    def _generate_small_world_network(self) -> List[Dict]:
        """
        Small-world network: high clustering, short path lengths
        Based on Watts-Strogatz model
        """
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Create initial ring structure
        treatments_per_neighborhood = max(3, n_treatments // 3)

        for i in range(n_studies):
            # Determine neighborhood
            center_idx = i % n_treatments
            neighborhood_start = center_idx
            neighborhood_end = (center_idx + treatments_per_neighborhood) % n_treatments

            if neighborhood_end < neighborhood_start:
                neighborhood = self.treatments[neighborhood_start:] + self.treatments[:neighborhood_end]
            else:
                neighborhood = self.treatments[neighborhood_start:neighborhood_end]

            # Select from neighborhood with high probability
            n_arms = np.random.randint(*self.config.network.arms_per_study)
            n_arms = min(n_arms, len(neighborhood))

            if np.random.random() < 0.8:  # High clustering
                treatments = np.random.choice(neighborhood, size=n_arms, replace=False).tolist()
            else:  # Random long-range connection
                treatments = np.random.choice(self.treatments, size=n_arms, replace=False).tolist()

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "small_world"
            })

        return studies

    def _generate_geometric_network(self) -> List[Dict]:
        """
        Geometric network: treatments in 2D space, connect if within radius
        Simulates clinical similarity
        """
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Place treatments in 2D space
        treatment_positions = {}
        for t in self.treatments:
            treatment_positions[t] = np.random.rand(2)

        # Calculate distances
        connection_radius = 0.4  # Connect if distance < threshold

        for i in range(n_studies):
            # Select a random treatment as center
            center_treatment = np.random.choice(self.treatments)
            center_pos = treatment_positions[center_treatment]

            # Find nearby treatments
            nearby = [center_treatment]
            for t in self.treatments:
                if t != center_treatment:
                    distance = np.linalg.norm(center_pos - treatment_positions[t])
                    if distance < connection_radius:
                        nearby.append(t)

            # Add some random long-distance connections
            if len(nearby) < 3 or np.random.random() < 0.2:
                others = [t for t in self.treatments if t not in nearby]
                if others:
                    n_add = min(2, len(others))
                    nearby.extend(np.random.choice(others, size=n_add, replace=False).tolist())

            # Create study with nearby treatments
            n_arms = np.random.randint(2, min(len(nearby), self.config.network.arms_per_study[1]) + 1)
            treatments = np.random.choice(nearby, size=n_arms, replace=False).tolist()

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "geometric"
            })

        return studies

    def _generate_bipartite_network(self) -> List[Dict]:
        """
        Bipartite network: two groups of treatments, comparisons mostly within groups
        Simulates comparing drugs within same class
        """
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Split treatments into two groups
        mid_point = n_treatments // 2
        group_a = self.treatments[:mid_point]
        group_b = self.treatments[mid_point:]

        for i in range(n_studies):
            # 80% within-group, 20% cross-group
            if np.random.random() < 0.8:
                group = group_a if np.random.random() < 0.5 else group_b
                n_arms = np.random.randint(2, min(len(group) + 1, self.config.network.arms_per_study[1] + 1))
                treatments = np.random.choice(group, size=min(n_arms, len(group)), replace=False).tolist()
            else:
                # Cross-group comparison
                n_from_a = np.random.randint(1, min(len(group_a), 3))
                n_from_b = np.random.randint(1, min(len(group_b), 3))
                treatments = (list(np.random.choice(group_a, size=n_from_a, replace=False)) +
                            list(np.random.choice(group_b, size=n_from_b, replace=False)))

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "bipartite"
            })

        return studies

    def _generate_clinical_network(self) -> List[Dict]:
        """
        Clinically realistic network: mimics real NMA structures
        Common in practice: mix of 2-arm and 3-arm studies
        """
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Realistic distribution: 70% 2-arm, 25% 3-arm, 5% 4+ arm
        arm_distribution = [2] * 7 + [3] * 2 + [4, 5]

        # Create reference treatment (placebo or standard care)
        reference = self.treatments[0]

        for i in range(n_studies):
            n_arms = np.random.choice(arm_distribution)
            n_arms = min(n_arms, n_treatments)

            # 80% of studies include reference (realistic)
            if np.random.random() < 0.8:
                treatments = [reference]
                remaining = [t for t in self.treatments if t != reference]
                n_extra = n_arms - 1
                if remaining and n_extra > 0:
                    selected = np.random.choice(remaining, size=min(n_extra, len(remaining)),
                                              replace=False).tolist()
                    treatments.extend(selected)
            else:
                # Active comparator study
                treatments = np.random.choice(self.treatments[1:], size=n_arms,
                                             replace=False).tolist()

            studies.append({
                "study_id": f"S{i+1:03d}",
                "treatments": treatments,
                "topology": "clinical_realistic"
            })

        return studies

    def _generate_disconnected_network(self) -> List[Dict]:
        """
        Disconnected network: separate components
        Tests method behavior with disconnected networks
        """
        studies = []
        n_studies = self.config.network.n_studies
        n_treatments = self.config.network.n_treatments

        # Create 2-3 disconnected components
        n_components = np.random.choice([2, 2, 3])
        treatments_per_component = n_treatments // n_components

        components = []
        for i in range(n_components):
            start = i * treatments_per_component
            end = start + treatments_per_component if i < n_components - 1 else n_treatments
            components.append(self.treatments[start:end])

        studies_per_component = n_studies // n_components

        for comp_idx, component in enumerate(components):
            for i in range(studies_per_component):
                if len(studies) >= n_studies:
                    break

                n_arms = np.random.randint(2, min(len(component) + 1,
                                                 self.config.network.arms_per_study[1] + 1))
                treatments = np.random.choice(component, size=min(n_arms, len(component)),
                                             replace=False).tolist()

                studies.append({
                    "study_id": f"S{len(studies)+1:03d}",
                    "treatments": treatments,
                    "topology": "disconnected",
                    "component_id": comp_idx
                })

        return studies


# ============================================================================
# ENHANCED SIMULATION ENGINE
# ============================================================================

class ExpandedNMASimulator:
    """
    Enhanced NMA simulator with diverse network structures and effect patterns
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.network_generator = ExpandedNetworkGenerator(config)
        self.treatments = self.network_generator.treatments
        self.generated_data = None

    def _generate_true_effects(self) -> Dict[str, float]:
        """Generate true treatment effects based on pattern"""
        effects = {self.config.effect_pattern.reference_treatment: 0.0}

        pattern = self.config.effect_pattern.pattern
        n_treatments = len(self.treatments)
        reference_idx = self.treatments.index(self.config.effect_pattern.reference_treatment)

        for i, treatment in enumerate(self.treatments):
            if treatment == self.config.effect_pattern.reference_treatment:
                continue

            # Get treatment index for all patterns
            idx = self.treatments.index(treatment)

            if pattern == "monotonic":
                # Monotonically improving treatments
                effect = self.config.effect_pattern.min_effect + (
                    self.config.effect_pattern.max_effect - self.config.effect_pattern.min_effect
                ) * idx / n_treatments

            elif pattern == "u_shaped":
                # U-shaped: best and worst at extremes
                position = idx / n_treatments
                effect = self.config.effect_pattern.min_effect + (
                    self.config.effect_pattern.max_effect - self.config.effect_pattern.min_effect
                ) * (1 - 4 * (position - 0.5)**2)

            elif pattern == "threshold":
                # Threshold effect: plateau after certain point
                if idx < n_treatments / 2:
                    effect = self.config.effect_pattern.min_effect * idx / (n_treatments / 2)
                else:
                    effect = self.config.effect_pattern.min_effect

            elif pattern == "plateau":
                # Plateau: diminishing returns
                effect = self.config.effect_pattern.min_effect * (1 - np.exp(-idx / 3))

            elif pattern == "clustered":
                # Two groups: similar effects within groups
                group = 0 if idx < n_treatments / 2 else 1
                base_effect = self.config.effect_pattern.min_effect if group == 0 else self.config.effect_pattern.max_effect
                effect = base_effect + np.random.normal(0, self.config.effect_pattern.effect_variance)

            else:  # random
                effect = np.random.uniform(
                    self.config.effect_pattern.min_effect,
                    self.config.effect_pattern.max_effect
                )

            effects[treatment] = effect

        return effects

    def _apply_inconsistency(self, effects: Dict[str, float],
                           study_treatments: List[str],
                           study_id: str) -> Dict[str, float]:
        """Apply inconsistency based on pattern"""
        if not self.config.inconsistency or self.config.inconsistency.pattern == "none":
            return effects

        pattern = self.config.inconsistency.pattern
        magnitude = self.config.inconsistency.magnitude

        modified_effects = effects.copy()

        if pattern == "random_loops":
            # Random studies have inconsistency
            if hash(study_id) % 5 < 2:  # 40% of studies
                for treatment in study_treatments:
                    if treatment != self.config.effect_pattern.reference_treatment:
                        if np.random.random() < 0.5:
                            modified_effects[treatment] += magnitude

        elif pattern == "loop_specific":
            # Specific treatment combinations have inconsistency
            if "B" in study_treatments and "C" in study_treatments:
                modified_effects["B"] += magnitude

        elif pattern == "edge_specific":
            # Specific edges have inconsistency
            pair = tuple(sorted([study_treatments[0], study_treatments[1] if len(study_treatments) > 1 else study_treatments[0]]))
            if len(pair) == 2 and "B" in pair:
                modified_effects["B"] += magnitude * (1 if np.random.random() < 0.5 else -1)

        return modified_effects

    def _generate_study_size(self) -> int:
        """Generate study sample size based on distribution"""
        dist = self.config.study_size.distribution

        if dist == "uniform":
            return np.random.randint(self.config.study_size.min_size,
                                    self.config.study_size.max_size + 1)

        elif dist == "lognormal":
            # Log-normal distribution (more realistic)
            mean = np.log(self.config.study_size.mean_size)
            sigma = self.config.study_size.size_variance
            size = int(np.random.lognormal(mean, sigma))
            return np.clip(size, self.config.study_size.min_size,
                          self.config.study_size.max_size)

        elif dist == "bimodal":
            # Two modes: small and large studies
            if np.random.random() < 0.5:
                return np.random.randint(self.config.study_size.min_size, 80)
            else:
                return np.random.randint(200, self.config.study_size.max_size)

        else:  # cluster
            # Clustered around specific sizes
            centers = [50, 100, 200, 400]
            center = np.random.choice(centers)
            return int(np.random.normal(center, center * 0.1))

    def _generate_binary_outcome(self, study_id: str, treatment: str,
                                true_effect: float, study_effect: float) -> Dict:
        """Generate binary outcome data"""
        n = self._generate_study_size()

        # Calculate probability of response
        baseline_logit = np.log(self.config.baseline_event_rate / (1 - self.config.baseline_event_rate))
        logit = baseline_logit + true_effect + study_effect
        p = 1 / (1 + np.exp(-logit))

        p = np.clip(p, 0.01, 0.99)
        r = np.random.binomial(n, p)

        return {
            "study": study_id,
            "treatment": treatment,
            "responders": r,
            "sample_size": n
        }

    def _generate_continuous_outcome(self, study_id: str, treatment: str,
                                    true_effect: float, study_effect: float) -> Dict:
        """Generate continuous outcome data"""
        n = self._generate_study_size()

        baseline = self.config.study_size.mean_size / 10  # Arbitrary baseline
        mean = baseline + true_effect + study_effect
        observed_mean = np.random.normal(mean, self.config.within_study_sd / np.sqrt(n))

        return {
            "study": study_id,
            "treatment": treatment,
            "mean": observed_mean,
            "sd": self.config.within_study_sd,
            "sample_size": n
        }

    def generate(self) -> pd.DataFrame:
        """Generate complete NMA dataset"""
        np.random.seed(self.config.seed)

        # Generate network structure
        studies = self.network_generator.generate_network()

        # Generate true effects
        true_effects = self._generate_true_effects()

        # Generate data for each study
        data_rows = []

        for study_info in studies:
            study_id = study_info["study_id"]
            treatments = study_info["treatments"]

            # Study-specific random effect
            tau = np.sqrt(self.config.heterogeneity.tau_squared)
            study_effect = np.random.normal(0, tau)

            # Apply inconsistency
            effects = self._apply_inconsistency(true_effects, treatments, study_id)

            # Generate outcome data
            for treatment in treatments:
                true_effect = effects.get(treatment, 0.0)

                if self.config.outcome_type == "binary":
                    row = self._generate_binary_outcome(study_id, treatment,
                                                        true_effect, study_effect)
                else:
                    row = self._generate_continuous_outcome(study_id, treatment,
                                                           true_effect, study_effect)

                data_rows.append(row)

        self.generated_data = pd.DataFrame(data_rows)
        return self.generated_data

    def get_true_effects(self) -> pd.DataFrame:
        """Get true treatment effects"""
        effects = self._generate_true_effects()
        return pd.DataFrame([
            {"treatment": t, "true_effect": e}
            for t, e in effects.items()
        ])

    def get_network_info(self) -> Dict:
        """Get network information"""
        if self.generated_data is None:
            self.generate()

        n_studies = self.generated_data["study"].nunique()
        n_treatments = self.generated_data["treatment"].nunique()
        n_arms = len(self.generated_data)

        return {
            "n_studies": n_studies,
            "n_treatments": n_treatments,
            "n_arms": n_arms,
            "connectivity_type": self.config.network.connectivity,
            "effect_pattern": self.config.effect_pattern.pattern,
            "outcome_type": self.config.outcome_type,
            "has_inconsistency": self.config.inconsistency.pattern != "none",
            "inconsistency_magnitude": self.config.inconsistency.magnitude,
            "tau_squared": self.config.heterogeneity.tau_squared,
            "i_squared": self.config.heterogeneity.i_squared
        }


# ============================================================================
# PRE-DEFINED EXPANDED SCENARIOS
# ============================================================================

def create_scale_free_scenario() -> SimulationConfig:
    """Scale-free network with hub treatments"""
    return SimulationConfig(
        network=NetworkStructure(
            name="scale_free_network",
            n_treatments=7,
            n_studies=40,
            connectivity="scale_free"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="monotonic",
            min_effect=-0.6,
            max_effect=-0.1
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=100
    )


def create_small_world_scenario() -> SimulationConfig:
    """Small-world network with high clustering"""
    return SimulationConfig(
        network=NetworkStructure(
            name="small_world_network",
            n_treatments=6,
            n_studies=35,
            connectivity="small_world",
            clustering_coefficient=0.4
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="u_shaped",
            min_effect=-0.5,
            max_effect=0.1
        ),
        heterogeneity=Heterogeneity(tau_squared=0.09, i_squared=0.6),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=101
    )


def create_disconnected_scenario() -> SimulationConfig:
    """Disconnected network with separate components"""
    return SimulationConfig(
        network=NetworkStructure(
            name="disconnected_network",
            n_treatments=8,
            n_studies=30,
            connectivity="disconnected_components"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="monotonic",
            min_effect=-0.5,
            max_effect=-0.2
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=102
    )


def create_bipartite_scenario() -> SimulationConfig:
    """Bipartite network (two treatment classes)"""
    return SimulationConfig(
        network=NetworkStructure(
            name="bipartite_network",
            n_treatments=8,
            n_studies=40,
            connectivity="bipartite"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="clustered",
            min_effect=-0.6,
            max_effect=-0.2
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=103
    )


def create_clinical_realistic_scenario() -> SimulationConfig:
    """Clinically realistic network structure"""
    return SimulationConfig(
        network=NetworkStructure(
            name="clinical_realistic",
            n_treatments=7,
            n_studies=50,
            connectivity="clinical_realistic"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="monotonic",
            min_effect=-0.5,
            max_effect=-0.1
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(pattern="none"),
        study_size=StudySizeDistribution(distribution="lognormal"),
        outcome_type="binary",
        seed=104
    )


def create_threshold_effect_scenario() -> SimulationConfig:
    """Threshold effect pattern with plateau"""
    return SimulationConfig(
        network=NetworkStructure(
            name="threshold_effect",
            n_treatments=6,
            n_studies=35,
            connectivity="dense"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="threshold",
            min_effect=-0.6,
            max_effect=-0.1
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=105
    )


def create_loop_inconsistency_scenario() -> SimulationConfig:
    """Loop network with specific inconsistency"""
    return SimulationConfig(
        network=NetworkStructure(
            name="loop_with_inconsistency",
            n_treatments=5,
            n_studies=30,
            connectivity="loop"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="monotonic",
            min_effect=-0.4,
            max_effect=-0.1
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(
            pattern="loop_specific",
            magnitude=0.3
        ),
        outcome_type="binary",
        seed=106
    )


def create_u_shaped_scenario() -> SimulationConfig:
    """U-shaped treatment effects"""
    return SimulationConfig(
        network=NetworkStructure(
            name="u_shaped_effects",
            n_treatments=7,
            n_studies=40,
            connectivity="dense"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="u_shaped",
            min_effect=-0.5,
            max_effect=0.0
        ),
        heterogeneity=Heterogeneity(tau_squared=0.04, i_squared=0.5),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=107
    )


def create_high_heterogeneity_scale_free_scenario() -> SimulationConfig:
    """Scale-free network with high heterogeneity"""
    return SimulationConfig(
        network=NetworkStructure(
            name="scale_free_high_heterogeneity",
            n_treatments=6,
            n_studies=35,
            connectivity="scale_free"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="monotonic",
            min_effect=-0.5,
            max_effect=-0.1
        ),
        heterogeneity=Heterogeneity(tau_squared=0.16, i_squared=0.75),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="binary",
        seed=108
    )


def create_continuous_outcome_scenario() -> SimulationConfig:
    """Continuous outcome with realistic network"""
    return SimulationConfig(
        network=NetworkStructure(
            name="continuous_realistic",
            n_treatments=6,
            n_studies=30,
            connectivity="clinical_realistic"
        ),
        effect_pattern=TreatmentEffectPattern(
            pattern="monotonic",
            min_effect=-2.0,  # Larger effects for continuous
            max_effect=-0.5
        ),
        heterogeneity=Heterogeneity(tau_squared=0.09, i_squared=0.6),
        inconsistency=InconsistencyPattern(pattern="none"),
        outcome_type="continuous",
        within_study_sd=2.0,
        seed=109
    )


# ============================================================================
# BATCH GENERATION
# ============================================================================

def generate_all_expanded_scenarios(n_reps: int = 10) -> Dict[str, List]:
    """Generate all expanded scenarios with multiple replications"""

    scenarios = [
        ("scale_free", create_scale_free_scenario()),
        ("small_world", create_small_world_scenario()),
        ("disconnected", create_disconnected_scenario()),
        ("bipartite", create_bipartite_scenario()),
        ("clinical_realistic", create_clinical_realistic_scenario()),
        ("threshold_effect", create_threshold_effect_scenario()),
        ("loop_inconsistency", create_loop_inconsistency_scenario()),
        ("u_shaped", create_u_shaped_scenario()),
        ("scale_free_high_het", create_high_heterogeneity_scale_free_scenario()),
        ("continuous", create_continuous_outcome_scenario()),
    ]

    all_results = {}

    for scenario_name, base_config in scenarios:
        print(f"\nGenerating scenario: {scenario_name}")

        scenario_results = []

        for rep in range(n_reps):
            config = base_config
            config.seed = 100 + rep

            simulator = ExpandedNMASimulator(config)
            data = simulator.generate()
            true_effects = simulator.get_true_effects()
            network_info = simulator.get_network_info()

            # Save to file
            scenario_dir = OUTPUT_DIR / "data" / scenario_name
            scenario_dir.mkdir(parents=True, exist_ok=True)

            data_file = scenario_dir / f"sim_seed{config.seed}.csv"
            effects_file = scenario_dir / f"true_effects_seed{config.seed}.csv"
            info_file = scenario_dir / f"network_info_seed{config.seed}.json"

            data.to_csv(data_file, index=False)
            true_effects.to_csv(effects_file, index=False)

            with open(info_file, 'w') as f:
                json.dump(network_info, f, indent=2, default=str)

            scenario_results.append({
                "data": data,
                "true_effects": true_effects,
                "network_info": network_info
            })

            if (rep + 1) % 5 == 0:
                print(f"  Completed {rep + 1}/{n_reps} replications")

        all_results[scenario_name] = scenario_results

    return all_results


# ============================================================================
# DEMONSTRATION
# ============================================================================

if __name__ == "__main__":

    print("\n" + "="*73)
    print("  EXPANDED NMA SIMULATION ENGINE - DEMONSTRATION")
    print("="*73 + "\n")

    # Test each expanded scenario
    scenarios_to_test = [
        ("Scale-Free Network", create_scale_free_scenario()),
        ("Small-World Network", create_small_world_scenario()),
        ("Disconnected Components", create_disconnected_scenario()),
        ("Bipartite Network", create_bipartite_scenario()),
        ("Clinically Realistic", create_clinical_realistic_scenario()),
        ("Threshold Effects", create_threshold_effect_scenario()),
        ("Loop with Inconsistency", create_loop_inconsistency_scenario()),
        ("U-Shaped Effects", create_u_shaped_scenario()),
        ("Scale-Free + High Heterogeneity", create_high_heterogeneity_scale_free_scenario()),
        ("Continuous Outcome", create_continuous_outcome_scenario()),
    ]

    for name, config in scenarios_to_test:
        print(f"\n{'='*73}")
        print(f"Scenario: {name}")
        print(f"{'='*73}")

        simulator = ExpandedNMASimulator(config)
        data = simulator.generate()
        network_info = simulator.get_network_info()
        true_effects = simulator.get_true_effects()

        print(f"\nNetwork Properties:")
        print(f"  Topology: {network_info['connectivity_type']}")
        print(f"  Effect Pattern: {network_info['effect_pattern']}")
        print(f"  Studies: {network_info['n_studies']}")
        print(f"  Treatments: {network_info['n_treatments']}")
        print(f"  Arms: {network_info['n_arms']}")
        print(f"  Has Inconsistency: {network_info['has_inconsistency']}")

        print(f"\nTrue Effects:")
        print(true_effects.to_string(index=False))

        print(f"\nFirst 10 rows of data:")
        print(data.head(10).to_string(index=False))

    print(f"\n{'='*73}")
    print("Expanded simulation test complete!")
    print(f"{'='*73}\n")
