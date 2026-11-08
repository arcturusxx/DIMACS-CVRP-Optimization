# DIMACS CVRP Optimization

### Solving the Capacitated Vehicle Routing Problem using PyVRP

## 1. Project Overview

This project addresses the **Capacitated Vehicle Routing Problem (CVRP)** using the DIMACS Vehicle Routing Challenge benchmark instance `E-n101-k8`.

The objective is to determine efficient delivery routes from a central depot to multiple customers while ensuring that:
- Every customer is visited exactly once.
- Every route starts and ends at the depot.
- Vehicle capacity constraints are satisfied.
- Total travel distance is minimised.

## 2. Benchmark Instance

| Parameter | Value |
|---|---:|
| Benchmark instance | E-n101-k8 |
| Total nodes | 101 |
| Customers | 100 |
| Depot | 1 |
| Vehicle capacity | 200 |
| Routes in obtained solution | 8 |

## 3. Methodology

The project uses **PyVRP**, a Python-based vehicle routing optimisation library, to solve the CVRP.

The solution approach uses Hybrid Genetic Search, combining population-based search with local improvement procedures to identify high-quality feasible routes.

### Technology Stack

- Python
- PyVRP
- VRPLIB
- VS Code

## 4. Mathematical Formulation

The objective is to minimise total routing distance:

**Minimise:**

\[
\min \sum_{i}\sum_{j} c_{ij}x_{ij}
\]

Subject to:

1. Every customer is visited exactly once.
2. Flow conservation is maintained at each customer.
3. Every vehicle route originates and terminates at the depot.
4. The total demand assigned to a route does not exceed vehicle capacity.
5. Decision variables satisfy the required routing restrictions.

## 5. Experimental Results

The algorithm was executed with a 300-second runtime limit.

| Performance Metric | Result |
|---|---:|
| Total distance | **8,215** |
| Number of routes | 8 |
| Customers served | 100 |
| Runtime | 300 seconds |
| Search iterations | 724,012 |
| Feasibility | Passed |
| Completeness | Passed |

### Route-wise Results

| Vehicle | Load | Capacity Utilisation | Distance |
|---|---:|---:|---:|
| 1 | 196 | 98.0% | 822 |
| 2 | 199 | 99.5% | 1,182 |
| 3 | 198 | 99.0% | 1,258 |
| 4 | 165 | 82.5% | 978 |
| 5 | 108 | 54.0% | 406 |
| 6 | 199 | 99.5% | 1,383 |
| 7 | 194 | 97.0% | 1,054 |
| 8 | 199 | 99.5% | 1,132 |

### Validation

The final solution passed the following checks:

- All 100 customers visited.
- No missing customers.
- No duplicate customer visits.
- All vehicle capacity constraints satisfied.
- Sum of route distances equals the reported objective.

**The objective of 8,215 represents the best feasible solution found in this run, not a proven global optimum.**

## 6. Project Structure

```text
DIMACS-CVRP-Optimization/
│
├── README.md
├── requirements.txt
├── dimacs_cvrp_pyvrp.py
├── dimacs_cvrp_solution.txt
│
├── data/
│   └── README.md
│
└── results/
    └── results_summary.md
```

## 7. Installation and Execution

Clone the repository:

```bash
git clone https://github.com/arcturusxx/DIMACS-CVRP-Optimization.git
cd DIMACS-CVRP-Optimization
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the `E-n101-k8.vrp` benchmark instance and place it inside the `data/` directory.

Run the implementation:

```bash
python dimacs_cvrp_pyvrp.py
```

## 8. Conclusion

The project demonstrates the application of heuristic optimisation techniques to a large-scale vehicle routing problem.

The implementation produced a feasible solution covering 100 customers using eight routes, with a total travel distance of 8,215.

The results illustrate how specialised heuristic optimisation can produce practical solutions for combinatorial routing problems within a limited computational budget.

## 9. References

- [DIMACS Vehicle Routing Implementation Challenge](https://dimacs.rutgers.edu/programs/implementation-challenges/vehicle-routing)
- [PyVRP Documentation](https://pyvrp.org/)
- [VRPLIB](https://github.com/PyVRP/VRPLIB)

---

**Academic Project:** Advanced Optimization Techniques for Managers  
**Repository:** https://github.com/arcturusxx/DIMACS-CVRP-Optimization