import math

satellites = [
    {"id": 1, "pos": [0, 0, 0], "vel": [0.001, 0, 0], "maneuvered": False, "docked": False, "docking_intent": True},
    {"id": 2, "pos": [0.03, 0, 0], "vel": [-0.001, 0, 0], "maneuvered": False, "docked": False, "docking_intent": True}, # 30 meters door
    {"id": 3, "pos": [0, 50, 0], "vel": [0, 1, 0], "maneuvered": False, "docked": False, "docking_intent": False},
    {"id": 4, "pos": [0, 0, 80], "vel": [0, 0, -1], "maneuvered": False, "docked": False, "docking_intent": False},
    {"id": 5, "pos": [10, 10, 10], "vel": [0.5, 0.5, 0.5], "maneuvered": False, "docked": False, "docking_intent": False}
]

SAFETY_DISTANCE = 10.0
MAGNETIC_RANGE = 0.01     # 10 meters
DOCK_DISTANCE = 0.001     # 1 meter
DAMPING = 0.3             # Speed kam karne ke liye
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

def get_distance(sat1, sat2):
    return math.sqrt(sum((sat2["pos"][i] - sat1["pos"][i])**2 for i in range(3)))

print("Project Aura: Real-Time Collision Avoidance & Magnetic Docking")
print("-" * 70)

for second in range(1, 101):
    for sat in satellites:
        if not sat["docked"]:
            sat["pos"] = [sat["pos"][i] + sat["vel"][i] for i in range(3)]
    
    for i in range(len(satellites)):
        for j in range(i+1, len(satellites)):
            if satellites[i]["docked"] and satellites[j]["docked"]:
                continue
                
            dist = get_distance(satellites[i], satellites[j])
            
            if dist <= MAGNETIC_RANGE and not satellites[i]["docked"] and not satellites[j]["docked"]:
                # DAMPING: Pehle relative velocity kam karo (braking)
                for k in range(3):
                    satellites[i]["vel"][k] *= (1 - DAMPING)
                    satellites[j]["vel"][k] *= (1 - DAMPING)
                
                if dist <= DOCK_DISTANCE:
                    satellites[i]["docked"] = True
                    satellites[j]["docked"] = True
                    satellites[i]["vel"] = [0,0,0]
                    satellites[j]["vel"] = [0,0,0]
                    print(f"[{second}s] 🟢 DOCKED: Sat {satellites[i]['id']} & Sat {satellites[j]['id']} successfully docked!")
                else:
                    # Magnetic Attraction
                    attraction_force = 0.005 * (MAGNETIC_RANGE - dist) / MAGNETIC_RANGE
                    for k in range(3):
                        direction = (satellites[j]["pos"][k] - satellites[i]["pos"][k]) / dist
                        satellites[i]["vel"][k] += attraction_force * direction
                        satellites[j]["vel"][k] -= attraction_force * direction
                    if second % 5 == 0:
                        print(f"[{second}s] 🧲 MAGNETIC ATTRACTION: Sat {satellites[i]['id']} & Sat {satellites[j]['id']} (Dist: {dist*1000:.2f} m)")
            
            elif not satellites[i]["docking_intent"] and not satellites[j]["docking_intent"]:
                result = calculate_risk(satellites[i], satellites[j])
                if result:
                    tca, dca = result
                    if dca < SAFETY_DISTANCE:
                        if not satellites[i]["maneuvered"] or not satellites[j]["maneuvered"]:
                            if latency_timer < 2:
                                latency_timer += 1
                                print(f"[{second}s] 🚨 COLLISION RISK: Sat {satellites[i]['id']} & Sat {satellites[j]['id']}. Waiting (Latency: {latency_timer}s)...")
                            else:
                                satellites[i]["vel"][1] += 0.5 
                                satellites[j]["vel"][1] -= 0.5
                                satellites[i]["maneuvered"] = True
                                satellites[j]["maneuvered"] = True
                                print(f"[{second}s] 🛠️ MANEUVER EXECUTED by Sat {satellites[i]['id']} and Sat {satellites[j]['id']}!")

print("-" * 70)
print("Simulation Complete!")
