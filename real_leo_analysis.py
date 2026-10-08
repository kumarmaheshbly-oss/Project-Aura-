!pip install sgp4

from sgp4.api import Satrec, jday
from datetime import datetime
import math

# 5 Real LEO Satellites ka TLE data (Space-Track.org - US Space Force)
# Ye naye launch hue hain (TBA = To Be Assigned), LEO orbit me hain
satellites = [
    {
        "name": "LEO-SAT 1",
        "line1": "1 70027U          26266.10562008 -.00647579  15246-3 -10650-2 0  9998",
        "line2": "2 70027  70.0027  92.3189 0004126 287.3689  72.7072 16.02919900  490"
    },
    {
        "name": "LEO-SAT 2",
        "line1": "1 70026U          26266.54245656 -.00800654  22244-3 -14135-2 0  9995",
        "line2": "2 70026  70.0027  91.0297 0006123 285.6761  74.3775 16.01712469  562"
    },
    {
        "name": "LEO-SAT 3",
        "line1": "1 70025U          26266.54199919 -.00561942  11649-3 -95730-3 0  9996",
        "line2": "2 70025  70.0028  91.0272 0005803 283.8606  76.1960 16.02290405  565"
    },
    {
        "name": "LEO-SAT 4",
        "line1": "1 70024U          26266.54116480 -.00600373  13286-3 -97518-3 0  9994",
        "line2": "2 70024  70.0029  91.0236 0006554 285.2766  74.7722 16.03095311  562"
    },
    {
        "name": "LEO-SAT 5",
        "line1": "1 70023U          26266.47978943 -.00353206  58578-4  58987-3 0  9994",
        "line2": "2 70023  70.0023  91.2121 0005171 245.5033 114.5641 16.02721493  558"
    }
]

sats = []
for sat in satellites:
    s = Satrec.twoline2rv(sat["line1"], sat["line2"])
    sats.append({"name": sat["name"], "obj": s})

print("Project Aura: REAL LEO Satellite Collision Analysis")
print("=" * 70)
print("Data Source: Space-Track.org (US Space Force)")
print("=" * 70)

now = datetime.utcnow()
jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)

positions = {}
print("\n🛰️  SATELLITE POSITIONS (Current Time)")
print("-" * 70)
for s in sats:
    error, pos, vel = s["obj"].sgp4(jd, fr)
    if error == 0:
        positions[s["name"]] = {"pos": pos, "vel": vel}
        altitude = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2) - 6371
        speed = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2) * 3600
        print(f"\n{s['name']}")
        print(f"  Position:  X={pos[0]:.2f}, Y={pos[1]:.2f}, Z={pos[2]:.2f} km")
        print(f"  Altitude:  {altitude:.2f} km")
        print(f"  Speed:     {speed:.2f} km/h")

print("\n" + "=" * 70)
print("🚨 COLLISION RISK ANALYSIS (TTC/DCA)")
print("-" * 70)

names = list(positions.keys())
risk_count = 0
for i in range(len(names)):
    for j in range(i+1, len(names)):
        p1 = positions[names[i]]["pos"]
        v1 = positions[names[i]]["vel"]
        p2 = positions[names[j]]["pos"]
        v2 = positions[names[j]]["vel"]
        
        r = [p2[k] - p1[k] for k in range(3)]
        v = [v2[k] - v1[k] for k in range(3)]
        
        v_sq = sum(x**2 for x in v)
        if v_sq == 0:
            continue
        
        r_dot_v = sum(r[k] * v[k] for k in range(3))
        tca = -r_dot_v / v_sq
        
        if tca < 0:
            continue
        
        future_r = [r[k] + v[k] * tca for k in range(3)]
        dca = math.sqrt(sum(x**2 for x in future_r))
        
        if dca < 10:
            emoji = "🚨"
            status = "COLLISION RISK"
            risk_count += 1
        elif dca < 100:
            emoji = "⚠️"
            status = "WARNING"
        else:
            emoji = "✅"
            status = "SAFE"
        
        print(f"{emoji} {names[i]} <-> {names[j]}")
        print(f"   TTC: {tca:.2f} sec | DCA: {dca:.2f} km | {status}")
        print()

print("=" * 70)
print(f"Total collision risks detected: {risk_count}")
print("=" * 70)
print("\n🛰️  Ye REAL LEO satellites ka data hai (Space-Track se)")
print("Altitude: ~280-300 km | Speed: ~29,000 km/h")
