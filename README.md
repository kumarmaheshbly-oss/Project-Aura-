# Project Aura: Real-Time Collision Avoidance

A Python simulation for a distributed satellite swarm with **REAL orbital data** from Space-Track (US Space Force).

## Features

- **Real Data Analysis:** Uses live TLE data from Space-Track.org (US Space Force)
- Calculates Time-to-Closest-Approach (TCA)
- Calculates Distance of Closest Approach (DCA)
- Simulates 2-second reaction latency
- Executes autonomous avoidance maneuvers
- Magnetic docking simulation with eddy current damping
- Post-maneuver safety verification
- **Scaled Analysis:** 123 satellites with two-stage pipeline and parallel processing (0.03 sec computation time)

## Files

- `collision_avoidance.py` — Simulated 5-satellite collision avoidance with magnetic docking
- `real_leo_analysis.py` — Real LEO satellite collision analysis using live TLE data from Space-Track

## Data Source

Live satellite data from [Space-Track.org](https://www.space-track.org) — US Space Force (S4S) and CFSCC.

## How to Run

```bash
pip install sgp4
python real_leo_analysis.py
```
