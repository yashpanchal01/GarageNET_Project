#!/usr/bin/env python3
import math
import sys

# MOCK DATASETS
WORKSHOPS = [
    {"name": "Pune Demo Garage", "lat": 18.5204, "lon": 73.8567, "address": "Shivajinagar, Pune"},
    {"name": "Pune Premium Garage", "lat": 18.5089, "lon": 73.8262, "address": "Kothrud, Pune"},
    {"name": "Mumbai Elite Motors", "lat": 19.0760, "lon": 72.8777, "address": "Bandra, Mumbai"},
    {"name": "Nashik Express Garage", "lat": 19.9975, "lon": 73.7898, "address": "Nashik Center"},
    {"name": "Lonavala Highway Stop", "lat": 18.7557, "lon": 73.4091, "address": "Lonavala Bypass"},
]

INVENTORY = [
    {"workshop": "Pune Demo Garage", "part_name": "Engine Oil", "quantity": 10, "price": 1200},
    {"workshop": "Pune Premium Garage", "part_name": "Engine Oil", "quantity": 5, "price": 1250},
    {"workshop": "Pune Premium Garage", "part_name": "Brake Pads", "quantity": 2, "price": 1800},
    {"workshop": "Mumbai Elite Motors", "part_name": "Engine Oil", "quantity": 15, "price": 1100},
    {"workshop": "Mumbai Elite Motors", "part_name": "Brake Pads", "quantity": 8, "price": 1750},
    {"workshop": "Nashik Express Garage", "part_name": "Engine Oil", "quantity": 1, "price": 1300},
    {"workshop": "Nashik Express Garage", "part_name": "Oil Filter", "quantity": 20, "price": 400},
    {"workshop": "Lonavala Highway Stop", "part_name": "Engine Oil", "quantity": 3, "price": 1400},
]

def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of earth in km
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2.0 * R * math.asin(math.sqrt(a))

def search_parts(center_shop, query, radius):
    c_lat, c_lon = center_shop["lat"], center_shop["lon"]
    results = []
    
    # 1. Bounding box pre-filter calculation
    delta_lat = radius / 111.0
    cos_lat = math.cos(math.radians(c_lat))
    delta_lon = radius / (111.0 * cos_lat) if abs(cos_lat) > 0.001 else 360.0
    
    min_lat, max_lat = c_lat - delta_lat, c_lat + delta_lat
    min_lon, max_lon = c_lon - delta_lon, c_lon + delta_lon
    
    for item in INVENTORY:
        # Exclude self workshop items
        if item["workshop"] == center_shop["name"]:
            continue
            
        # Match part name query
        if query.lower() not in item["part_name"].lower():
            continue
            
        # Retrieve target workshop details
        shop = next(w for w in WORKSHOPS if w["name"] == item["workshop"])
        
        # Bounding box coordinates validation
        in_bbox = (min_lat <= shop["lat"] <= max_lat) and (min_lon <= shop["lon"] <= max_lon)
        
        # Haversine distance check
        distance = haversine_distance(c_lat, c_lon, shop["lat"], shop["lon"])
        
        # Add details
        results.append({
            "part_name": item["part_name"],
            "workshop_name": shop["name"],
            "address": shop["address"],
            "qty": item["quantity"],
            "price": item["price"],
            "distance_km": round(distance, 2),
            "in_bbox": in_bbox,
            "within_radius": distance <= radius
        })
        
    # Sort nearest first
    results.sort(key=lambda r: r["distance_km"])
    return results

def main():
    center_idx = 0
    radius = 50.0
    query = "engine"
    
    while True:
        # Clear terminal screen
        print("\033[2J\033[H", end="")
        
        center_shop = WORKSHOPS[center_idx]
        results = search_parts(center_shop, query, radius)
        
        print("\x1b[1m=== HYPERLOCAL SEARCH LOGIC PROTOTYPE ===\x1b[0m")
        print(f"\x1b[1mCenter Workshop:\x1b[0m {center_shop['name']} ({center_shop['address']})")
        print(f"\x1b[1mCoordinates:\x1b[0m {center_shop['lat']}, {center_shop['lon']}")
        print(f"\x1b[1mSearch Radius:\x1b[0m {radius} km")
        print(f"\x1b[1mSearch Query:\x1b[0m '{query}'")
        print("-" * 70)
        
        print(f"\x1b[1m{'Workshop':<24} {'Part':<12} {'Qty':<4} {'Price':<6} {'Distance':<10} {'BBox?':<6} {'In Radius?':<10}\x1b[0m")
        print("-" * 70)
        
        for r in results:
            # Highlight matching within radius in green, else dim
            style = "\x1b[32m" if (r["within_radius"] and r["in_bbox"]) else "\x1b[2m"
            reset = "\x1b[0m"
            print(f"{style}{r['workshop_name']:<24} {r['part_name']:<12} {r['qty']:<4} ₹{r['price']:<5} {r['distance_km']:>5} km   {str(r['in_bbox']):<6} {str(r['within_radius']):<10}{reset}")
            
        print("-" * 70)
        print("\x1b[1m[r]\x1b[0m Change Radius   \x1b[1m[q]\x1b[0m Update Query   \x1b[1m[c]\x1b[0m Cycle Center Garage   \x1b[1m[x]\x1b[0m Exit")
        print("-" * 70)
        
        try:
            cmd = input("Action: ").strip().lower()
            if cmd == 'x':
                print("Exiting search logic prototype.")
                break
            elif cmd == 'c':
                center_idx = (center_idx + 1) % len(WORKSHOPS)
            elif cmd == 'r':
                val = input("Enter new radius (km): ").strip()
                if val:
                    try:
                        radius = float(val)
                    except ValueError:
                        pass
            elif cmd == 'q':
                val = input("Enter search query: ").strip()
                if val:
                    query = val
        except (KeyboardInterrupt, EOFError):
            print("\nExiting search logic prototype.")
            break

if __name__ == "__main__":
    main()
