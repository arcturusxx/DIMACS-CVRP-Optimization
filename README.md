# DIMACS CVRP Optimization

## Solving the Capacitated Vehicle Routing Problem using MILP and Hybrid Genetic Search

This project solves the Capacitated Vehicle Routing Problem (CVRP) on the `E-n101-k8` benchmark instance using two approaches:

1. **Pyomo + Gurobi:** a mixed-integer linear programming (MILP) formulation.
2. **PyVRP:** a specialised heuristic solver based on Hybrid Genetic Search.

Both implementations use the same DIMACS distance convention and a 300-second runtime budget.

## 1. Problem Overview

The CVRP considers a central depot, customers with known demands, and a fleet of capacitated vehicles. The objective is to construct routes that start and end at the depot, visit every customer exactly once, respect vehicle capacity, and minimise total travel distance.

Applications include distribution, last-mile delivery, fleet planning, and logistics operations.

## 2. Benchmark Instance

The project uses `E-n101-k8.vrp`.

| Parameter | Value |
|---|---:|
| Instance | `E-n101-k8` |
| Total nodes | 101 |
| Customers | 100 |
| Depot | Node 1 in the VRPLIB instance |
| Vehicle capacity | 200 |
| Vehicles / routes | 8 |
| Edge-weight type | `EUC_2D` |

The distance convention is:

`c_ij = floor(10 × EuclideanDistance(i, j))`

Both implementations use this convention. The Pyomo script constructs the matrix directly; the PyVRP script reads the instance with `round_func="dimacs"`.

**Instance provenance:** The included instance file was obtained from the `InstancesRounded` directory of the [CVRPController repository](https://github.com/laser-ufpb/CVRPController), which mirrors rounded CVRP instances. This repository does not claim that the file was downloaded directly from the DIMACS website.

## 3. Solution Approaches

### 3.1 Pyomo + Gurobi (MILP)

The first approach formulates CVRP as a mixed-integer linear program in Pyomo and solves it using Gurobi.

- Binary variable `x[i,j]` indicates whether the route travels directly from node `i` to node `j`.
- Continuous variable `u[i]` tracks cumulative load along a route.
- The objective minimises the sum of selected arc distances.
- Customer in-degree and out-degree constraints ensure one incoming and one outgoing arc per customer.
- Depot departure and return constraints enforce eight routes.
- MTZ load-propagation constraints enforce capacity and eliminate customer-only subtours.

The solver is configured with a 300-second time limit and a target MIP gap of 1%. The target gap is a solver setting, not a guarantee that the run will reach 1%.

### 3.2 PyVRP (Heuristic)

The second approach uses PyVRP, a specialised vehicle-routing optimisation library. PyVRP uses Hybrid Genetic Search and local-search improvement procedures to search for high-quality feasible routes.

- Runtime limit: 300 seconds
- Random seed: 42
- DIMACS distance rounding

The heuristic returns a feasible solution but does not provide a proof of global optimality.

## 4. Mathematical Formulation

Let `V` be the set of nodes including depot `0`, `C` the set of customers, `c_ij` the distance from node `i` to node `j`, `q_i` customer demand, `Q` vehicle capacity, and `K = 8` the required number of vehicles. Binary variable `x_ij` indicates whether arc `(i,j)` is used; continuous variable `u_i` represents cumulative route load.

**Objective**

Minimise:

`sum(c_ij * x_ij)` over all directed arcs `i != j`.

**Customer visit constraints**

Each customer has exactly one incoming and one outgoing arc:

- `sum(x_ij over i in V, i != j) = 1` for every customer `j`.
- `sum(x_ij over j in V, j != i) = 1` for every customer `i`.

**Depot route constraints**

Exactly eight routes leave and return to the depot:

- `sum(x_0j over j in C) = K`.
- `sum(x_i0 over i in C) = K`.

**Load and subtour-elimination constraints**

- `u_i >= q_i` for every customer.
- `u_i - u_j + Q*x_ij <= Q - q_j` for every pair of distinct customers.
- `0 <= u_i <= Q`.
- `x_ij` is binary.

The load-propagation constraints are the MTZ-style constraints implemented in the Pyomo model.

## 5. Experimental Setup

| Setting | Pyomo + Gurobi | PyVRP |
|---|---:|---:|
| Runtime limit | 300 seconds | 300 seconds |
| Vehicle capacity | 200 | 200 |
| Distance convention | DIMACS | DIMACS |
| Solver target / seed | 1% MIP gap target | Seed 42 |

The results below are from the recorded runs included in this project. Runtime values are approximately 300 seconds.

## 6. Experimental Results

| Metric | Pyomo + Gurobi | PyVRP |
|---|---:|---:|
| Total distance (objective) | 8,517 | **8,215** |
| Routes used | 8 | 8 |
| Customers served | 100 | 100 |
| Runtime | ~300 seconds | ~300 seconds |
| Validation | Passed | Passed |
| Optimality proof | Not proven | Not provided |

### MILP solver status

Gurobi reached the 300-second time limit with:

- Best feasible objective (incumbent): 8,517
- Best bound: 7,131
- Final MIP gap: 16.2733%

The run did not reach its 1% target gap and did not prove global optimality.

### Comparison

The PyVRP objective of 8,215 is 302 distance units lower than the Pyomo + Gurobi incumbent of 8,517. This is an improvement of approximately 3.55% relative to the MILP incumbent.

This compares two feasible solutions obtained under similar time limits. It does not establish that PyVRP is better than the globally optimal MILP solution, because the MILP run did not prove optimality.

### PyVRP route-wise results

| Vehicle | Load | Capacity utilisation | Distance |
|---|---:|---:|---:|
| 1 | 196 | 98.0% | 822 |
| 2 | 199 | 99.5% | 1,182 |
| 3 | 198 | 99.0% | 1,258 |
| 4 | 165 | 82.5% | 978 |
| 5 | 108 | 54.0% | 406 |
| 6 | 199 | 99.5% | 1,383 |
| 7 | 194 | 97.0% | 1,054 |
| 8 | 199 | 99.5% | 1,132 |

## 7. Solution Validation

Both scripts perform checks before saving their result files:

- all 100 customers are served;
- no customer is missing;
- no customer is visited more than once;
- every route respects vehicle capacity; and
- the sum of route distances matches the reported objective.

Both recorded solutions passed these checks.

## 8. Repository Structure

```text
DIMACS-CVRP-Optimization/
├── README.md
├── requirements.txt
├── dimacs_cvrp_pyomo.py
├── dimacs_cvrp_pyvrp.py
├── data/
│   └── E-n101-k8.vrp
└── results/
    ├── pyomo_gurobi_results.json
    ├── pyomo_gurobi_results.txt
    ├── pyvrp_results.json
    └── pyvrp_results.txt
```

## 9. Installation and Execution

Clone the repository:

```bash
git clone https://github.com/arcturusxx/DIMACS-CVRP-Optimization.git
cd DIMACS-CVRP-Optimization
```

Create and activate a virtual environment (optional but recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the Pyomo + Gurobi implementation:

```bash
python dimacs_cvrp_pyomo.py
```

This requires a working Gurobi installation and a valid Gurobi licence in addition to the Python packages.

Run the PyVRP implementation:

```bash
python dimacs_cvrp_pyvrp.py
```

Each script expects to be run from the repository root. It reads `data/E-n101-k8.vrp` and writes JSON and text results to `results/`.

## 10. Conclusion and Limitations

The project implements and compares a mathematical-programming approach and a specialised heuristic for the same CVRP benchmark.

In the recorded 300-second runs, PyVRP found a feasible solution with total distance 8,215, compared with the Pyomo + Gurobi incumbent of 8,517. Both solutions served all customers exactly once, used eight vehicles, respected capacity limits, and passed the implemented validation checks.

The main limitation is that the time-limited MILP run ended with a 16.2733% MIP gap. Consequently, the global optimum is not established, and the comparison is between feasible solutions rather than proven optimality.

## 11. References

- [DIMACS Vehicle Routing Implementation Challenge](https://dimacs.rutgers.edu/programs/implementation-challenges/vehicle-routing)
- [Pyomo Documentation](https://pyomo.readthedocs.io/)
- [Gurobi Documentation](https://docs.gurobi.com/)
- [PyVRP Documentation](https://pyvrp.org/)
- [VRPLIB](https://github.com/PyVRP/VRPLIB)
- [CVRPController – InstancesRounded mirror](https://github.com/laser-ufpb/CVRPController)

---

**Course:** Advanced Optimization Techniques for Managers  
**Repository:** https://github.com/arcturusxx/DIMACS-CVRP-Optimization
