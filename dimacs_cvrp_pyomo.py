from pathlib import Path
from collections import Counter
from time import perf_counter
import json
import math

import numpy as np
import pyomo.environ as pyo
import vrplib


# ==========================================================
# CONFIGURATION
# ==========================================================

INSTANCE_PATH = Path("data/E-n101-k8.vrp")
RESULTS_DIR = Path("results")

TIME_LIMIT = 300
MIP_GAP = 0.01
NUM_VEHICLES = 8

RESULTS_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD INSTANCE AND BUILD DIMACS DISTANCE MATRIX
# ==========================================================

if not INSTANCE_PATH.exists():
    raise FileNotFoundError(INSTANCE_PATH.resolve())

instance = vrplib.read_instance(str(INSTANCE_PATH))

n = int(instance["dimension"])
capacity = int(instance["capacity"])
demand = [int(value) for value in instance["demand"]]
coordinates = np.asarray(instance["node_coord"], dtype=float)

# DIMACS: floor(10 * Euclidean distance)
euclidean = np.linalg.norm(
    coordinates[:, None, :] - coordinates[None, :, :],
    axis=2
)

distance = np.floor(10 * euclidean + 1e-9).astype(int)

nodes = list(range(n))
customers = list(range(1, n))

print("=" * 65)
print("DIMACS CVRP - PYOMO + GUROBI")
print("=" * 65)
print(f"Instance: {INSTANCE_PATH.name}")
print(f"Nodes: {n} | Customers: {n - 1}")
print(f"Capacity: {capacity} | Vehicles: {NUM_VEHICLES}")
print(f"Time limit: {TIME_LIMIT}s | MIP gap: {MIP_GAP * 100:.1f}%")
print("Distance convention: floor(10 x Euclidean distance)")


# ==========================================================
# BUILD MODEL
# ==========================================================

model = pyo.ConcreteModel()

model.N = pyo.Set(initialize=nodes)
model.C = pyo.Set(initialize=customers)

arcs = [(i, j) for i in nodes for j in nodes if i != j]
customer_arcs = [
    (i, j)
    for i in customers
    for j in customers
    if i != j
]

model.A = pyo.Set(dimen=2, initialize=arcs)
model.CA = pyo.Set(dimen=2, initialize=customer_arcs)

model.x = pyo.Var(model.A, domain=pyo.Binary)

model.u = pyo.Var(
    model.C,
    domain=pyo.NonNegativeReals,
    bounds=(0, capacity)
)

model.objective = pyo.Objective(
    expr=sum(distance[i, j] * model.x[i, j] for i, j in arcs),
    sense=pyo.minimize
)

# Every customer has exactly one incoming and outgoing arc.
model.incoming = pyo.Constraint(
    model.C,
    rule=lambda m, j: sum(m.x[i, j] for i in nodes if i != j) == 1
)

model.outgoing = pyo.Constraint(
    model.C,
    rule=lambda m, i: sum(m.x[i, j] for j in nodes if j != i) == 1
)

# Exactly eight vehicles leave and return to the depot.
model.depot_out = pyo.Constraint(
    expr=sum(model.x[0, j] for j in customers) == NUM_VEHICLES
)

model.depot_in = pyo.Constraint(
    expr=sum(model.x[i, 0] for i in customers) == NUM_VEHICLES
)

# MTZ capacity and subtour-elimination constraints.
model.load_lower = pyo.Constraint(
    model.C,
    rule=lambda m, i: m.u[i] >= demand[i]
)

model.mtz = pyo.Constraint(
    model.CA,
    rule=lambda m, i, j:
        m.u[i] - m.u[j] + capacity * m.x[i, j]
        <= capacity - demand[j]
)


# ==========================================================
# SOLVE
# ==========================================================

solver = pyo.SolverFactory("gurobi")

if not solver.available(exception_flag=False):
    raise RuntimeError("Gurobi is not available in this environment.")

solver.options["TimeLimit"] = TIME_LIMIT
solver.options["MIPGap"] = MIP_GAP
solver.options["MIPFocus"] = 1
solver.options["Heuristics"] = 0.2
solver.options["Threads"] = 0

print("\nStarting Gurobi optimisation...\n")

start_time = perf_counter()

results = solver.solve(
    model,
    tee=True,
    load_solutions=True
)

runtime = perf_counter() - start_time
termination = str(results.solver.termination_condition)

print("\nTermination:", termination)
print(f"Runtime: {runtime:.2f} seconds")


# ==========================================================
# CHECK FOR INCUMBENT
# ==========================================================

selected_arcs = []

for i, j in arcs:
    value = model.x[i, j].value
    if value is not None and value > 0.5:
        selected_arcs.append((i, j))

if not selected_arcs:
    raise RuntimeError(
        "Gurobi did not return a feasible solution. "
        "No result file has been saved."
    )


# ==========================================================
# EXTRACT ROUTES
# ==========================================================

successors = {i: j for i, j in selected_arcs}

routes = []
visited = []
unvisited = set(customers)

for first_customer in customers:
    if (0, first_customer) not in selected_arcs:
        continue

    route = [0]
    current = first_customer
    route_seen = set()

    while current != 0:
        if current in route_seen:
            raise RuntimeError("Cycle detected during route extraction.")

        route_seen.add(current)
        route.append(current)
        visited.append(current)
        unvisited.discard(current)

        if current not in successors:
            raise RuntimeError(f"Missing successor for node {current}.")

        current = successors[current]

    route.append(0)
    routes.append(route)

if unvisited:
    raise RuntimeError(f"Unvisited customers: {sorted(unvisited)}")


# ==========================================================
# VALIDATE AND SUMMARISE
# ==========================================================

route_results = []
total_distance = 0
capacity_valid = True

for route_no, route in enumerate(routes, start=1):
    load = sum(demand[node] for node in route if node != 0)

    route_distance = sum(
        int(distance[route[i], route[i + 1]])
        for i in range(len(route) - 1)
    )

    capacity_ok = load <= capacity
    capacity_valid = capacity_valid and capacity_ok
    total_distance += route_distance

    route_results.append({
        "vehicle": route_no,
        "route": route,
        "load": load,
        "capacity": capacity,
        "utilisation_percent": round(load / capacity * 100, 2),
        "distance": route_distance,
        "capacity_valid": capacity_ok
    })

coverage_counts = Counter(visited)
missing = sorted(set(customers) - set(visited))
duplicates = sorted(
    node for node, count in coverage_counts.items() if count > 1
)

model_objective = float(pyo.value(model.objective))

coverage_valid = (
    len(visited) == len(customers)
    and not missing
    and not duplicates
)

distance_valid = abs(total_distance - model_objective) < 1e-5

validation_passed = (
    coverage_valid
    and capacity_valid
    and distance_valid
    and len(routes) == NUM_VEHICLES
)

print("\n" + "=" * 65)
print("PYOMO + GUROBI RESULTS")
print("=" * 65)
print(f"Objective: {model_objective:.0f}")
print(f"Routes: {len(routes)}")
print(f"Customers served: {len(visited)}")
print(f"Runtime: {runtime:.2f}s")
print(f"Termination: {termination}")

for item in route_results:
    print(f"\nVehicle {item['vehicle']}: {' -> '.join(map(str, item['route']))}")
    print(f"Load: {item['load']}/{capacity}")
    print(f"Distance: {item['distance']}")
    print(f"Utilisation: {item['utilisation_percent']}%")

print("\nValidation:")
print("Missing customers:", missing)
print("Duplicate customers:", duplicates)
print("Capacity valid:", capacity_valid)
print("Distance sum:", total_distance)
print("Model objective:", model_objective)
print("FINAL STATUS:", "PASSED" if validation_passed else "FAILED")


# ==========================================================
# SAVE RESULTS
# ==========================================================

output = {
    "algorithm": "Pyomo + Gurobi MILP",
    "instance": INSTANCE_PATH.name,
    "distance_convention": "floor(10 * Euclidean distance)",
    "vehicles": NUM_VEHICLES,
    "vehicle_capacity": capacity,
    "time_limit_seconds": TIME_LIMIT,
    "mip_gap_setting": MIP_GAP,
    "runtime_seconds": round(runtime, 3),
    "termination_condition": termination,
    "objective": model_objective,
    "route_distance_sum": total_distance,
    "number_of_routes": len(routes),
    "customers_served": len(visited),
    "missing_customers": missing,
    "duplicate_customers": duplicates,
    "capacity_valid": capacity_valid,
    "coverage_valid": coverage_valid,
    "distance_valid": distance_valid,
    "validation_passed": validation_passed,
    "routes": route_results
}

json_path = RESULTS_DIR / "pyomo_gurobi_results.json"
text_path = RESULTS_DIR / "pyomo_gurobi_results.txt"

with json_path.open("w") as file:
    json.dump(output, file, indent=4)

with text_path.open("w") as file:
    file.write("DIMACS CVRP - PYOMO + GUROBI\n")
    file.write("=" * 55 + "\n")
    file.write(f"Objective: {model_objective:.0f}\n")
    file.write(f"Runtime: {runtime:.2f} seconds\n")
    file.write(f"Termination: {termination}\n")
    file.write(f"Routes: {len(routes)}\n")
    file.write(f"Validation: {'PASSED' if validation_passed else 'FAILED'}\n\n")

    for item in route_results:
        file.write(f"Vehicle {item['vehicle']}: ")
        file.write(" -> ".join(map(str, item["route"])) + "\n")
        file.write(
            f"Load: {item['load']}/{capacity} | "
            f"Distance: {item['distance']} | "
            f"Utilisation: {item['utilisation_percent']}%\n\n"
        )

print("\nSaved:")
print(json_path.resolve())
print(text_path.resolve())