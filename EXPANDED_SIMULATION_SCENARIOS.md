# Expanded Simulation Scenarios - Complete Reference
**NMA Methods Research: Enhanced Simulation Engine**
**Date:** 2026-01-15

---

## Overview

The expanded simulation engine now supports **10 network topologies** and **6 treatment effect patterns**, enabling comprehensive testing of NMA methods under diverse conditions.

---

## Network Topologies

### 1. Dense Network
**Description:** Well-connected network with many random connections

**Properties:**
- High connectivity
- All treatments connected
- Short path lengths
- Maximum evidence flow

**Use Case:** Baseline performance, ideal conditions

**Example Output:**
```
Topology: dense
Studies: 30, Treatments: 5, Arms: 77
Connections: 10
```

---

### 2. Sparse Network
**Description:** Limited connections, minimal branching

**Properties:**
- Chain-like structure
- Few multi-arm studies
- Limited indirect evidence
- Challenging for estimation

**Use Case:** Testing robustness to limited data

**Example Output:**
```
Topology: sparse
Studies: 15, Treatments: 5, Arms: 30
Connections: 9
```

---

### 3. Star Network
**Description:** All studies include reference treatment

**Properties:**
- Reference treatment (A) in all studies
- No direct comparisons between non-reference treatments
- All inference goes through reference
- Common in clinical trials

**Use Case:** Reference-based comparisons

**Example Output:**
```
Topology: star
Studies: 30, Treatments: 5, Arms: 60
Connections: 4 (only to A)
```

---

### 4. Loop Network
**Description:** Closed triangular loops

**Properties:**
- Multiple closed loops
- Tests inconsistency detection
- Direct and indirect evidence
- A-B-C-A structure

**Use Case:** Inconsistency method validation

**Example Output:**
```
Topology: loop
Studies: 30, Treatments: 5, Arms: 79
Connections: 8
Loops: Multiple triangular
```

---

### 5. Scale-Free Network ⭐ NEW
**Description:** Few hub treatments with many connections (Barabási-Albert model)

**Properties:**
- Power-law degree distribution
- 20% hub treatments (highly connected)
- Preferential attachment
- Mimics real citation networks

**Use Case:** Real-world networks with popular treatments

**Example Output:**
```
Topology: scale_free
Studies: 40, Treatments: 7, Arms: 121
Hubs: A, B (highly connected)
```

**Code:**
```python
config = SimulationConfig(
    network=NetworkStructure(
        name="scale_free",
        n_treatments=7,
        n_studies=40,
        connectivity="scale_free"
    ),
    ...
)
```

---

### 6. Small-World Network ⭐ NEW
**Description:** High clustering, short path lengths (Watts-Strogatz model)

**Properties:**
- High clustering coefficient
- Mostly local connections
- Some random long-range connections
- Six degrees of separation

**Use Case:** Clinical networks with local treatment classes

**Example Output:**
```
Topology: small_world
Studies: 35, Treatments: 6, Arms: 90
Clustering: High (0.4)
Path length: Short
```

**Code:**
```python
config = SimulationConfig(
    network=NetworkStructure(
        name="small_world",
        n_treatments=6,
        n_studies=35,
        connectivity="small_world",
        clustering_coefficient=0.4
    ),
    ...
)
```

---

### 7. Geometric Network ⭐ NEW
**Description:** Treatments in 2D space, connected if within radius

**Properties:**
- Spatial treatment embedding
- Distance-based connectivity
- Simulates clinical similarity
- Natural clustering

**Use Case:** Treatment classes with similar mechanisms

**Example Output:**
```
Topology: geometric
Studies: 30, Treatments: 6, Arms: 86
Connection radius: 0.4
Spatial: 2D embedding
```

---

### 8. Bipartite Network ⭐ NEW
**Description:** Two treatment groups with mostly within-group comparisons

**Properties:**
- Two disconnected groups
- 80% within-group, 20% cross-group
- Mimics drug class comparisons
- Tests transitivity assumptions

**Use Case:** Comparing treatments within same class

**Example Output:**
```
Topology: bipartite
Studies: 40, Treatments: 8, Arms: 115
Groups: 2 (A-D vs E-H)
Cross-group: 20%
```

---

### 9. Clinically Realistic Network ⭐ NEW
**Description:** Mimics real NMA structure from clinical trials

**Properties:**
- 70% 2-arm studies
- 25% 3-arm studies
- 5% 4+ arm studies
- 80% include reference (placebo)
- Log-normal study size distribution

**Use Case:** Most realistic for method validation

**Example Output:**
```
Topology: clinical_realistic
Studies: 50, Treatments: 7, Arms: 122
2-arm: 70%, 3-arm: 25%, 4+arm: 5%
Reference inclusion: 80%
```

**Code:**
```python
config = SimulationConfig(
    network=NetworkStructure(
        name="clinical_realistic",
        n_treatments=7,
        n_studies=50,
        connectivity="clinical_realistic"
    ),
    study_size=StudySizeDistribution(distribution="lognormal"),
    ...
)
```

---

### 10. Disconnected Components Network ⭐ NEW
**Description:** Separate network components with no connections

**Properties:**
- 2-3 disconnected components
- No evidence flow between components
- Tests method behavior
- Challenging for analysis

**Use Case:** Testing method failure modes

**Example Output:**
```
Topology: disconnected_components
Studies: 30, Treatments: 8, Arms: 92
Components: 2
Connected: False
```

---

## Treatment Effect Patterns

### 1. Monotonic
**Description:** Treatments improve monotonically (A < B < C < ...)

**True Effects:**
```
A:  0.000
B: -0.529
C: -0.457
D: -0.386
E: -0.314
```

**Use Case:** Standard improvement pattern

---

### 2. U-Shaped ⭐ NEW
**Description:** Best and worst at extremes, middle treatments neutral

**True Effects:**
```
A:  0.000 (reference)
B: -0.167 (good)
C:  0.033 (neutral)
D:  0.100 (neutral)
E:  0.033 (neutral)
F: -0.167 (good)
```

**Use Case:** Testing non-linear patterns

---

### 3. Threshold ⭐ NEW
**Description:** Plateau effect after certain point

**True Effects:**
```
A:  0.00
B: -0.20
C: -0.40
D: -0.60
E: -0.60 (plateau)
F: -0.60 (plateau)
```

**Use Case:** Diminishing returns

---

### 4. Clustered ⭐ NEW
**Description:** Two groups with similar within-group effects

**True Effects:**
```
Group 1: A=0.00, B=-0.61, C=-0.70
Group 2: D=-0.36, E=-0.19, F=-0.28
```

**Use Case:** Treatment classes

---

## Inconsistency Patterns

### 1. None
No inconsistency, consistent network

### 2. Random Loops
Random proportion of studies have inconsistency (40%)

### 3. Loop Specific
Specific treatment combinations (B-C) have inconsistency

### 4. Edge Specific
Specific edges have directional inconsistency

---

## Study Size Distributions

### 1. Uniform
Random between min and max

### 2. Log-Normal ⭐ NEW
Realistic skewed distribution (most studies medium-sized)

**Parameters:**
```python
StudySizeDistribution(
    distribution="lognormal",
    min_size=30,
    max_size=500,
    mean_size=100,
    size_variance=0.5
)
```

### 3. Bimodal ⭐ NEW
Two modes: small (30-80) and large (200-500) studies

### 4. Cluster ⭐ NEW
Clustered around specific sizes (50, 100, 200, 400)

---

## Outcome Types

### 1. Binary
Binomial outcomes (responders/sample_size)

### 2. Continuous ⭐ NEW
Normal outcomes (mean, sd, sample_size)

---

## Complete Scenario Library

| Scenario | Topology | Effect | Heterogeneity | Inconsistency | Outcome |
|----------|----------|--------|---------------|--------------|---------|
| baseline | dense | monotonic | Low (0.01) | None | binary |
| sparse | sparse | monotonic | Medium (0.04) | None | binary |
| inconsistency_0.3 | loop | monotonic | Medium (0.04) | Medium (0.3) | binary |
| high_heterogeneity | dense | monotonic | High (0.16) | None | binary |
| star | star | monotonic | Medium (0.04) | None | binary |
| **scale_free** | **scale_free** | **monotonic** | **Medium** | **None** | **binary** |
| **small_world** | **small_world** | **u_shaped** | **Medium (0.09)** | **None** | **binary** |
| **disconnected** | **disconnected** | **monotonic** | **Medium** | **None** | **binary** |
| **bipartite** | **bipartite** | **clustered** | **Medium** | **None** | **binary** |
| **clinical_realistic** | **clinical_realistic** | **monotonic** | **Medium** | **None** | **binary** |
| **threshold_effect** | **dense** | **threshold** | **Medium** | **None** | **binary** |
| **loop_inconsistency** | **loop** | **monotonic** | **Medium** | **Loop-specific** | **binary** |
| **u_shaped** | **dense** | **u_shaped** | **Medium** | **None** | **binary** |
| **scale_free_high_het** | **scale_free** | **monotonic** | **High (0.16)** | **None** | **binary** |
| **continuous** | **clinical_realistic** | **monotonic** | **Medium (0.09)** | **None** | **continuous** |

---

## Usage Examples

### Generate Single Scenario
```python
from R.expanded_simulation_engine import *

# Create scale-free network
config = create_scale_free_scenario()
simulator = ExpandedNMASimulator(config)
data = simulator.generate()
true_effects = simulator.get_true_effects()
network_info = simulator.get_network_info()
```

### Generate Custom Scenario
```python
config = SimulationConfig(
    network=NetworkStructure(
        name="my_custom_network",
        n_treatments=10,
        n_studies=50,
        connectivity="scale_free"
    ),
    effect_pattern=TreatmentEffectPattern(
        pattern="u_shaped",
        min_effect=-0.7,
        max_effect=0.1
    ),
    heterogeneity=Heterogeneity(tau_squared=0.09, i_squared=0.6),
    inconsistency=InconsistencyPattern(
        pattern="loop_specific",
        magnitude=0.4
    ),
    study_size=StudySizeDistribution(
        distribution="lognormal",
        mean_size=150
    ),
    outcome_type="binary",
    seed=42
)

simulator = ExpandedNMASimulator(config)
data = simulator.generate()
```

### Batch Generate All Scenarios
```python
from R.expanded_simulation_engine import generate_all_expanded_scenarios

results = generate_all_expanded_scenarios(n_reps=100)
# Generates 100 replications for all 10 scenarios
```

---

## Key Advantages

### 1. **Diverse Topologies**
- 10 network types covering most real-world structures
- From simple (star) to complex (scale-free, small-world)

### 2. **Realistic Patterns**
- Clinically realistic networks match actual trial structures
- Log-normal study sizes reflect real distributions

### 3. **Controlled Complexity**
- Can vary one factor at a time
- Known ground truth for validation

### 4. **Comprehensive Testing**
- Binary and continuous outcomes
- Multiple heterogeneity levels
- Multiple inconsistency patterns

---

## Research Applications

### Application 1: Method Robustness
Test how methods perform across different network structures

### Application 2: Inconsistency Detection Power
Compare detection methods with known inconsistency location

### Application 3: Ranking Accuracy
Evaluate SUCRA/P-score stability with different effect patterns

### Application 4: Disconnected Network Handling
Test method behavior when network is disconnected

### Application 5: Sample Size Requirements
Determine minimum sample sizes for reliable estimates

---

## File Structure

```
outputs/simulations/data/
├── baseline/
│   ├── sim_seed42.csv
│   ├── true_effects_seed42.csv
│   └── network_info_seed42.json
├── scale_free/
├── small_world/
├── disconnected/
├── bipartite/
├── clinical_realistic/
├── threshold_effect/
├── loop_inconsistency/
├── u_shaped/
├── scale_free_high_het/
└── continuous/
```

---

## Summary Statistics

| Metric | Original | Expanded |
|--------|----------|----------|
| Network topologies | 5 | **10** |
| Effect patterns | 1 | **6** |
| Inconsistency patterns | 1 | **4** |
| Study size distributions | 1 | **4** |
| Outcome types | 1 | **2** |
| Total scenarios | 5 | **15+** |

---

## Next Steps

1. **Generate full dataset:** 1000 replications × 15 scenarios
2. **Run method testing:** Apply NMA methods to all datasets
3. **Analyze results:** Compare method performance
4. **Identify failure modes:** When do methods fail?
5. **Develop improvements:** Design better methods

---

*The expanded simulation engine provides a comprehensive platform for rigorous NMA method evaluation and development.*
