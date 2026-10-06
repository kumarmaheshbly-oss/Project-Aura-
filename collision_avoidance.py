import math

# 5 Satellites ka data (Position aur Velocity)
satellites = [
    {"id": 1, "pos": [0, 0, 0], "vel": [1.0, 0, 0], "maneuvered": False},
    {"id": 2, "pos": [20, 0, 0], "vel": [-1.0, 0, 0], "maneuvered": False}, # Sat 1 ki taraf aa raha hai
    {"id": 3, "pos": [0, 50, 0], "vel": [0, 1, 0], "maneuvered": False},
    {"id": 4, "pos": [0, 0, 80], "vel": [0, 0, -1], "maneuvered": False},
    {"id": 5, "pos": [10, 10, 10], "vel": [0.5, 0.5, 0.5], "maneuvered": False}
]

SAFETY_DISTANCE = 10.0
latency_timer = 0

def calculate_risk(sat1, sat2):
    r = [sat2["pos"][i] - sat1["pos"][i] for i in range(3)]
    v = [sat2["vel"][i] - sat1["vel"][i] for i in range(3)]
    v_sq = sum(x**2 for x in v)
    if v_sq == 0: return None
    r_dot_v = sum(r[i] * v[i] for i in range(3))
    tca = -r_dot_v / v_sq
    if tca < 0: return None
    future_r = [r[i] + v[i] * tca for i in range(3)]
    dca = math.sqrt(sum(x**2 for x in future_r))
    return tca, dca

print("Project Aura: Real-Time Collision Avoidance Simulation")
print("-" * 60)

# 10 second ki simulation loop
for second in range(1, 11):
    # 1. Position Update (Har second satellite aage badhta hai)
    for sat in satellites:
        sat["pos"] = [sat["pos"][i] + sat["vel"][i] for i in range(3)]
    
    # 2. Check Risk aur Maneuver Logic
    for i in range(len(satellites)):
        for j in range(i+1, len(satellites)):
            result = calculate_risk(satellites[i], satellites[j])
            if result:
                tca, dca = result
                if dca < SAFETY_DISTANCE:
                    if not satellites[i]["maneuvered"] or not satellites[j]["maneuvered"]:
                        if latency_timer < 2:
                            latency_timer += 1
                            print(f"[{second}s] RISK DETECTED: Sat {satellites[i]['id']} & Sat {satellites[j]['id']}. Waiting for reaction (Latency: {latency_timer}s)...")
                        else:
                            # Maneuver: Velocity ko thoda sa perpendicular kar do
                            satellites[i]["vel"][1] += 0.5 
                            satellites[j]["vel"][1] -= 0.5
                            satellites[i]["maneuvered"] = True
                            satellites[j]["maneuvered"] = True
                            print(f"[{second}s] MANEUVER EXECUTED by Sat {satellites[i]['id']} and Sat {satellites[j]['id']}!")
    
    # 3. Final Verification har second
    if second == 10:
        print("-" * 60)
        print("Post-Maneuver Verification:")
        for i in range(len(satellites)):
            for j in range(i+1, len(satellites)):
                result = calculate_risk(satellites[i], satellites[j])
                if result:
                    tca, dca = result
                    status = "SAFE" if dca >= SAFETY_DISTANCE else "COLLISION RISK"
                    print(f"Sat {satellites[i]['id']} & Sat {satellites[j]['id']}: DCA = {dca:.2f} km -> {status}")
