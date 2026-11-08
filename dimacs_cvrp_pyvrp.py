
from pathlib import Path
import vrplib
from pyvrp import read, solve
from pyvrp.stop import MaxRuntime

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

INSTANCE_PATH = Path("data/E-n101-k8.vrp")
RUNTIME_SECONDS = 300
RANDOM_SEED = 42

# --------------------------------------------------
# LOAD INSTANCE
# --------------------------------------------------

if not INSTANCE_PATH.exists():
    raise FileNotFoundError(
        f"Instance not found: {INSTANCE_PATH.resolve()}"
    )

raw = vrplib.read_instance(str(INSTANCE_PATH))

capacity = int(raw["capacity"])
demands = raw["demand"]
num_nodes = len(demands)
num_customers = num_nodes - 1

print("=" * 65)
print("DIMACS CVRP - PYVRP")
print("=" * 65)

print(f"Instance        : {raw.get('name', INSTANCE_PATH.stem)}")
print(f"Total nodes     : {num_nodes}")
print(f"Customers       : {num_customers}")
print(f"Vehicle capacity: {capacity}")
print(f"Time limit      : {RUNTIME_SECONDS} seconds")

# --------------------------------------------------
# LOAD PYVRP INSTANCE
# --------------------------------------------------

data = read(str(INSTANCE_PATH), round_func="dimacs")

# --------------------------------------------------
# SOLVE
# --------------------------------------------------

print("\nStarting optimisation...\n")

result = solve(
    data,
    stop=MaxRuntime(RUNTIME_SECONDS),
    seed=RANDOM_SEED,
    display=True,
)

best = result.best

# --------------------------------------------------
# SAVE SOLUTION BEFORE REPORTING
# --------------------------------------------------

solution_path = Path("dimacs_cvrp_solution.txt")

with solution_path.open("w") as file:
    file.write(f"Objective: {best.distance()}\n")
    file.write(f"Routes: {best.num_routes()}\n\n")

    for route_no, route in enumerate(best.routes(), start=1):
        customer_ids = [
            activity.idx + 2
            for activity in route
            if activity.is_client()
        ]

        file.write(
            f"Route #{route_no}: "
            + " ".join(map(str, customer_ids))
            + "\n"
        )

print(f"\nRaw solution saved to: {solution_path.resolve()}")

# --------------------------------------------------
# SOLUTION SUMMARY
# --------------------------------------------------

print("\n" + "=" * 65)
print("BEST SOLUTION FOUND")
print("=" * 65)

print(f"Feasible solution : {best.is_feasible()}")
print(f"Complete solution : {best.is_complete()}")
print(f"Total distance    : {best.distance()}")
print(f"Number of routes  : {best.num_routes()}")
print(f"Customers served  : {best.num_clients()}")
print(f"Runtime           : {result.runtime:.2f} seconds")

# --------------------------------------------------
# ROUTE EXTRACTION
# --------------------------------------------------

visited = []
total_distance = 0
all_routes_valid = True

print("\nROUTE DETAILS")
print("-" * 65)

for route_no, route in enumerate(best.routes(), start=1):

    customer_ids = [
        activity.idx + 2
        for activity in route
        if activity.is_client()
    ]

    route_load = sum(
        int(demands[node_id - 1])
        for node_id in customer_ids
    )

    route_distance = route.distance()

    visited.extend(customer_ids)
    total_distance += route_distance

    capacity_ok = route_load <= capacity
    all_routes_valid = all_routes_valid and capacity_ok

    route_display = [1] + customer_ids + [1]

    print(f"\nVehicle {route_no}")
    print("Route      :", " -> ".join(map(str, route_display)))
    print(f"Customers  : {len(customer_ids)}")
    print(f"Load       : {route_load}/{capacity}")
    print(f"Distance   : {route_distance}")
    print(f"Utilization: {route_load / capacity * 100:.2f}%")
    print(f"Capacity OK: {capacity_ok}")

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

expected_customers = set(range(2, num_nodes + 1))
visited_set = set(visited)

missing = sorted(expected_customers - visited_set)

duplicates = sorted(
    node for node in visited_set
    if visited.count(node) > 1
)

coverage_ok = (
    visited_set == expected_customers
    and len(visited) == num_customers
)

validation_passed = (
    coverage_ok
    and all_routes_valid
    and best.is_feasible()
    and best.is_complete()
)

print("\n" + "=" * 65)
print("VALIDATION")
print("=" * 65)

print(f"Expected customers : {num_customers}")
print(f"Visited customers  : {len(visited)}")
print(f"Unique customers   : {len(visited_set)}")
print(f"Missing customers  : {missing}")
print(f"Duplicate customers: {duplicates}")
print(f"Capacity valid     : {all_routes_valid}")
print(f"Route distance sum : {total_distance}")
print(f"Solution distance  : {best.distance()}")

print(
    "\nFINAL STATUS:",
    "VALIDATION PASSED" if validation_passed
    else "VALIDATION FAILED"
)

if abs(total_distance - best.distance()) > 0:
    print("WARNING: Route distance sum differs from solution distance.")

print(f"\nSolution file: {solution_path.resolve()}")
