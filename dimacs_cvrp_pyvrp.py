from pathlib import Path
from time import perf_counter
import json

import vrplib
from pyvrp import read, solve
from pyvrp.stop import MaxRuntime


# ==========================================================
# CONFIGURATION
# ==========================================================

INSTANCE_PATH = Path("data/E-n101-k8.vrp")
RESULTS_DIR = Path("results")

RUNTIME_SECONDS = 300
RANDOM_SEED = 42

RESULTS_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD INSTANCE
# ==========================================================

if not INSTANCE_PATH.exists():
    raise FileNotFoundError(INSTANCE_PATH.resolve())

raw = vrplib.read_instance(str(INSTANCE_PATH))

capacity = int(raw["capacity"])
demands = [int(value) for value in raw["demand"]]
num_nodes = len(demands)
num_customers = num_nodes - 1

# Same DIMACS convention as the Pyomo script.
data = read(str(INSTANCE_PATH), round_func="dimacs")

print("=" * 65)
print("DIMACS CVRP - PYVRP")
print("=" * 65)
print(f"Instance: {INSTANCE_PATH.name}")
print(f"Nodes: {num_nodes} | Customers: {num_customers}")
print(f"Capacity: {capacity}")
print(f"Time limit: {RUNTIME_SECONDS}s")
print(f"Random seed: {RANDOM_SEED}")
print("Distance convention: floor(10 x Euclidean distance)")


# ==========================================================
# SOLVE
# ==========================================================

print("\nStarting PyVRP optimisation...\n")

start_time = perf_counter()

result = solve(
    data,
    stop=MaxRuntime(RUNTIME_SECONDS),
    seed=RANDOM_SEED,
    display=True
)

runtime = perf_counter() - start_time
best = result.best


# ==========================================================
# EXTRACT AND VALIDATE ROUTES
# ==========================================================

route_results = []
visited = []
total_distance = 0
capacity_valid = True

for route_no, route in enumerate(best.routes(), start=1):

    # PyVRP client index 0 corresponds to VRPLIB node 2.
    customer_ids = [
        activity.idx + 2
        for activity in route
        if activity.is_client()
    ]

    route_load = sum(demands[node_id - 1] for node_id in customer_ids)
    route_distance = int(route.distance())

    capacity_ok = route_load <= capacity
    capacity_valid = capacity_valid and capacity_ok

    visited.extend(customer_ids)
    total_distance += route_distance

    route_results.append({
        "vehicle": route_no,
        "route": [1] + customer_ids + [1],
        "load": route_load,
        "capacity": capacity,
        "utilisation_percent": round(route_load / capacity * 100, 2),
        "distance": route_distance,
        "capacity_valid": capacity_ok
    })


# ==========================================================
# VALIDATION
# ==========================================================

expected_customers = set(range(2, num_nodes + 1))
visited_set = set(visited)

missing = sorted(expected_customers - visited_set)
duplicates = sorted(
    node for node in visited
    if visited.count(node) > 1
)

coverage_valid = (
    visited_set == expected_customers
    and len(visited) == num_customers
    and not duplicates
)

distance_valid = total_distance == int(best.distance())

validation_passed = (
    best.is_feasible()
    and best.is_complete()
    and coverage_valid
    and capacity_valid
    and distance_valid
)

print("\n" + "=" * 65)
print("PYVRP RESULTS")
print("=" * 65)
print(f"Objective: {best.distance()}")
print(f"Routes: {best.num_routes()}")
print(f"Customers served: {best.num_clients()}")
print(f"Runtime: {runtime:.2f}s")

for item in route_results:
    print(f"\nVehicle {item['vehicle']}: {' -> '.join(map(str, item['route']))}")
    print(f"Load: {item['load']}/{capacity}")
    print(f"Distance: {item['distance']}")
    print(f"Utilisation: {item['utilisation_percent']}%")

print("\nValidation:")
print("Missing customers:", missing)
print("Duplicate customers:", duplicates)
print("Capacity valid:", capacity_valid)
print("Route distance sum:", total_distance)
print("Solution distance:", best.distance())
print("FINAL STATUS:", "PASSED" if validation_passed else "FAILED")


# ==========================================================
# SAVE RESULTS
# ==========================================================

output = {
    "algorithm": "PyVRP heuristic",
    "instance": INSTANCE_PATH.name,
    "distance_convention": "floor(10 * Euclidean distance)",
    "vehicles": best.num_routes(),
    "vehicle_capacity": capacity,
    "time_limit_seconds": RUNTIME_SECONDS,
    "random_seed": RANDOM_SEED,
    "runtime_seconds": round(runtime, 3),
    "objective": int(best.distance()),
    "route_distance_sum": total_distance,
    "customers_served": best.num_clients(),
    "missing_customers": missing,
    "duplicate_customers": duplicates,
    "feasible": best.is_feasible(),
    "complete": best.is_complete(),
    "capacity_valid": capacity_valid,
    "coverage_valid": coverage_valid,
    "distance_valid": distance_valid,
    "validation_passed": validation_passed,
    "routes": route_results
}

json_path = RESULTS_DIR / "pyvrp_results.json"
text_path = RESULTS_DIR / "pyvrp_results.txt"

with json_path.open("w") as file:
    json.dump(output, file, indent=4)

with text_path.open("w") as file:
    file.write("DIMACS CVRP - PYVRP\n")
    file.write("=" * 55 + "\n")
    file.write(f"Objective: {best.distance()}\n")
    file.write(f"Runtime: {runtime:.2f} seconds\n")
    file.write(f"Routes: {best.num_routes()}\n")
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