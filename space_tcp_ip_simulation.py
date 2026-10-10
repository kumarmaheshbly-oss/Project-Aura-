
# Project Aura: Space TCP/IP Simulation
# Satellites aapas me negotiate karte hain — bina ground control ke

import math
import random
from datetime import datetime

# 100 satellites ka swarm (2D simplification)
NUM_SATS = 100
SAFETY_DISTANCE = 10.0  # km
COMM_RANGE = 500.0      # km (laser range)

class Satellite:
    def __init__(self, id, x, y, vx, vy):
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.neighbors = []
        self.maneuver = None
    
    def position(self):
        return (self.x, self.y)
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def find_neighbors(self, all_sats):
        self.neighbors = []
        for s in all_sats:
            if s.id != self.id and self.distance_to(s) < COMM_RANGE:
                self.neighbors.append(s)
    
    def check_conflict(self):
        """Neighbors ke saath conflict check karo"""
        for n in self.neighbors:
            dist = self.distance_to(n)
            if dist < SAFETY_DISTANCE * 2:
                return n
        return None
    
    def negotiate(self):
        """Aapas me negotiate karo — kaun left, kaun right"""
        conflict = self.check_conflict()
        if conflict:
            # Simple consensus: chhota ID wala left, bada ID wala right
            if self.id < conflict.id:
                self.maneuver = "LEFT"
            else:
                self.maneuver = "RIGHT"
            return True
        return False
    
    def execute_maneuver(self):
        """Autonomous maneuver execute karo"""
        if self.maneuver == "LEFT":
            self.vx -= 0.1
        elif self.maneuver == "RIGHT":
            self.vx += 0.1
        self.maneuver = None
    
    def update(self):
        self.x += self.vx
        self.y += self.vy

# Swarm banao
random.seed(42)
satellites = []
for i in range(NUM_SATS):
    satellites.append(Satellite(
        id=i,
        x=random.uniform(-1000, 1000),
        y=random.uniform(-1000, 1000),
        vx=random.uniform(-1, 1),
        vy=random.uniform(-1, 1)
    ))

print("Project Aura: Space TCP/IP Simulation")
print("=" * 60)
print(f"Total satellites: {NUM_SATS}")
print(f"Safety distance: {SAFETY_DISTANCE} km")
print(f"Communication range: {COMM_RANGE} km")
print("=" * 60)

# 50 steps chalao
conflicts_detected = 0
maneuvers_executed = 0

for step in range(50):
    # Har satellite apne neighbors dhundhe
    for s in satellites:
        s.find_neighbors(satellites)
    
    # Conflicts detect karo aur negotiate karo
    for s in satellites:
        if s.negotiate():
            conflicts_detected += 1
    
    # Maneuvers execute karo
    for s in satellites:
        if s.maneuver:
            s.execute_maneuver()
            maneuvers_executed += 1
    
    # Positions update karo
    for s in satellites:
        s.update()

print(f"\nSimulation complete!")
print(f"Conflicts detected: {conflicts_detected}")
print(f"Maneuvers executed: {maneuvers_executed}")
print(f"Ground control commands sent: 0")
print("=" * 60)
print("Satellites ne khud negotiate kiya — bina ground control ke!")
