import random
import csv
import requests
from shapely.geometry import Point, Polygon

# ---------------- CONFIG ----------------
API_KEY = "YOUR_API_KEY"  # <-- put your actual key here
N = 50  # number of pairs to generate
OUTPUT_FILE = "distance_results.csv"

# 4 corner coordinates (lat, lon)
corners = [
    (38.663332, -74.919915),
    (38.522134, -74.945856),
    (38.600000, -75.000000),
    (38.700000, -74.980000)
]

# ---------------------------------------

def random_point_in_polygon(polygon):
    """Generate a random point within a polygon (rough bounding box rejection sampling)."""
    minx, miny, maxx, maxy = polygon.bounds
    while True:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(p):
            return p

def generate_pairs(polygon, n_pairs):
    """Generate N random pairs of points inside polygon."""
    points = [random_point_in_polygon(polygon) for _ in range(n_pairs * 2)]
    random.shuffle(points)
    return [(points[i], points[i+1]) for i in range(0, len(points), 2)]

def batch_pairs(pairs, batch_size=10):
    """Yield batches of up to 10x10 (100 elements) for API."""
    for i in range(0, len(pairs), batch_size):
        yield pairs[i:i + batch_size]

def query_distance_matrix(origins, destinations):
    """Call the Google Distance Matrix API."""
    origins_str = "|".join([f"{p.y},{p.x}" for p in origins])
    dest_str = "|".join([f"{p.y},{p.x}" for p in destinations])

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origins_str}&destinations={dest_str}"
        f"&mode=driving&units=metric&key={API_KEY}"
    )

    r = requests.get(url)
    return r.json()

def main():
    polygon = Polygon(corners)
    pairs = generate_pairs(polygon, N)

    results = []

    # Break into batches (10x10 recommended)
    for batch in batch_pairs(pairs, 10):
        origins = [p[0] for p in batch]
        destinations = [p[1] for p in batch]
        data = query_distance_matrix(origins, destinations)

        # Parse results
        for i, origin in enumerate(origins):
            for j, dest in enumerate(destinations):
                element = data["rows"][i]["elements"][j]
                if element["status"] == "OK":
                    duration = element["duration"]["value"]  # in seconds
                    results.append({
                        "origin_lat": origin.y,
                        "origin_lng": origin.x,
                        "dest_lat": dest.y,
                        "dest_lng": dest.x,
                        "duration_sec": duration
                    })

    # Write to CSV
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["origin_lat", "origin_lng", "dest_lat", "dest_lng", "duration_sec"])
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Done! Saved {len(results)} valid pairs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
