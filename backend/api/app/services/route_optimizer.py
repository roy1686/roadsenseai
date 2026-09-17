import math
from typing import List, Dict, Any, Optional

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two geographic points in kilometers."""
    R = 6371.0  # Earth's mean radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(R * c, 4)


def calculate_tour_distance(tour: List[int], dist_matrix: List[List[float]]) -> float:
    dist = 0.0
    for i in range(len(tour) - 1):
        dist += dist_matrix[tour[i]][tour[i + 1]]
    return dist


def two_opt_optimize(tour: List[int], dist_matrix: List[List[float]], max_iterations: int = 200) -> List[int]:
    """2-Opt local search heuristic for the Traveling Salesperson Problem."""
    best_tour = list(tour)
    best_dist = calculate_tour_distance(best_tour, dist_matrix)
    n = len(tour)
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for i in range(1, n - 1):
            for k in range(i + 1, n):
                new_tour = best_tour[:i] + best_tour[i:k + 1][::-1] + best_tour[k + 1:]
                new_dist = calculate_tour_distance(new_tour, dist_matrix)
                if new_dist < best_dist - 1e-6:
                    best_tour = new_tour
                    best_dist = new_dist
                    improved = True
                    break
            if improved:
                break

    return best_tour


def optimize_damage_route(damage_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given a list of damage instances from a survey, filter for valid coordinates
    and compute an optimized geodesic repair route using Nearest-Neighbor + 2-Opt.
    """
    # 1. Filter only records with valid GPS coordinates
    geo_damages = [
        d for d in damage_records
        if d.get("latitude") is not None and d.get("longitude") is not None
    ]

    if not geo_damages:
        return {
            "status": "no_gps_coordinates",
            "message": "No georeferenced damage instances available for route optimization.",
            "stops": [],
            "stops_count": 0,
            "original_distance_km": 0.0,
            "optimized_distance_km": 0.0,
            "estimated_savings_pct": 0.0,
            "distance_metric": "Estimated Geodesic (Haversine)",
            "note": "Route optimization requires synchronized GPS coordinates. Non-GPS detections are logged by frame index."
        }

    if len(geo_damages) == 1:
        d = geo_damages[0]
        return {
            "status": "single_stop",
            "stops": [{
                "sequence": 1,
                "damage_id": d.get("id", d.get("damage_code")),
                "damage_code": d.get("damage_code", "DMG-01"),
                "damage_type": d.get("damage_type", "Pothole"),
                "severity": d.get("severity", "Moderate"),
                "priority": d.get("priority", 3),
                "latitude": d.get("latitude"),
                "longitude": d.get("longitude")
            }],
            "stops_count": 1,
            "original_distance_km": 0.0,
            "optimized_distance_km": 0.0,
            "estimated_savings_pct": 0.0,
            "distance_metric": "Estimated Geodesic (Haversine)"
        }

    # 2. Build Distance Matrix
    n = len(geo_damages)
    dist_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i][j] = haversine_distance_km(
                    geo_damages[i]["latitude"], geo_damages[i]["longitude"],
                    geo_damages[j]["latitude"], geo_damages[j]["longitude"]
                )

    # 3. Initial Sequential Tour
    initial_tour = list(range(n))
    orig_dist = calculate_tour_distance(initial_tour, dist_matrix)

    # 4. Nearest Neighbor Seeding
    unvisited = set(range(1, n))
    nn_tour = [0]
    curr = 0
    while unvisited:
        next_node = min(unvisited, key=lambda x: dist_matrix[curr][x])
        nn_tour.append(next_node)
        unvisited.remove(next_node)
        curr = next_node

    # 5. 2-Opt Optimization
    opt_tour_indices = two_opt_optimize(nn_tour, dist_matrix)
    opt_dist = calculate_tour_distance(opt_tour_indices, dist_matrix)

    savings_pct = 0.0
    if orig_dist > 0:
        savings_pct = max(0.0, round(((orig_dist - opt_dist) / orig_dist) * 100.0, 1))

    # 6. Format Ordered Stops
    ordered_stops = []
    for seq, idx in enumerate(opt_tour_indices, 1):
        d = geo_damages[idx]
        ordered_stops.append({
            "sequence": seq,
            "damage_id": str(d.get("id", "")),
            "damage_code": d.get("damage_code", f"DMG-{seq:03d}"),
            "damage_type": d.get("damage_type", "Pothole"),
            "severity": d.get("severity", "Moderate"),
            "priority": d.get("priority", 3),
            "latitude": d.get("latitude"),
            "longitude": d.get("longitude"),
            "estimated_repair_cost": d.get("estimated_repair_cost", 0.0)
        })

    return {
        "status": "optimized",
        "stops": ordered_stops,
        "stops_count": len(ordered_stops),
        "original_distance_km": round(orig_dist, 2),
        "optimized_distance_km": round(opt_dist, 2),
        "estimated_savings_pct": savings_pct,
        "distance_metric": "Estimated Geodesic (Haversine)",
        "disclaimer": "Distances and savings are algorithmic estimates calculated from straight-line geodesic coordinates."
    }
