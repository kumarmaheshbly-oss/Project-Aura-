import streamlit as st
import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load

# --- Page Config ---
st.set_page_config(page_title="Project Aura", page_icon="🛰️", layout="wide")

# --- Header ---
st.title("🛰️ Project Aura: Commercial SSA Dashboard")
st.markdown("**Real-Time Satellite Conjunction Assessment & Collision Avoidance**")
st.divider()

# --- Real TLE Data ---
tle_data = {
    "ISS (ZARYA)": [
        '1 25544U 98067A   24121.54791667  .00016717  00000+0  30777-3 0  9993',
        '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49815570444578'
    ],
    "STARLINK-1007": [
        '1 44713U 19074A   24121.50000000  .00002182  00000+0  16411-3 0  9990',
        '2 44713  53.0541 198.3234 0001421  93.8295 266.2878 15.06384507244455'
    ]
}

# --- Setup Skyfield ---
ts = load.timescale()
t = ts.utc(2024, 5, 1, 0, 0, range(0, 5400, 10))

# --- Calculate Orbits ---
sat_a = EarthSatellite(tle_data["ISS (ZARYA)"][0], tle_data["ISS (ZARYA)"][1], "ISS", ts)
sat_b = EarthSatellite(tle_data["STARLINK-1007"][0], tle_data["STARLINK-1007"][1], "STARLINK", ts)

pos_a = sat_a.at(t).position.km
pos_b = sat_b.at(t).position.km

distances = np.linalg.norm(pos_a - pos_b, axis=0)
min_dist = np.min(distances)

# --- Foster-1992 Pc Calculation ---
sigma = 0.5 
hbr = 0.02  
pc = (hbr**2 / (2 * np.pi * sigma**2)) * np.exp(-(min_dist**2) / (2 * sigma**2)) if min_dist < 50.0 else 0.0

# --- Metrics Display ---
col1, col2, col3 = st.columns(3)
col1.metric("Minimum Distance", f"{min_dist:.2f} km")
col2.metric("Probability (Pc)", f"{pc:.2e}")

status = "🔴 HIGH RISK" if pc > 1e-4 else "🟢 SAFE"
col3.metric("Status", status)

# --- 3D Plotly Graph ---
st.subheader("3D Orbital Trajectories")
fig = go.Figure()

# Earth Wireframe
u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
xe = 6371 * np.cos(u)*np.sin(v)
ye = 6371 * np.sin(u)*np.sin(v)
ze = 6371 * np.cos(v)
fig.add_trace(go.Surface(x=xe, y=ye, z=ze, colorscale='Greys', opacity=0.3, showscale=False))

# Orbits
fig.add_trace(go.Scatter3d(x=pos_a[0], y=pos_a[1], z=pos_a[2], mode='lines', name="ISS Orbit", line=dict(color='blue', width=4)))
fig.add_trace(go.Scatter3d(x=pos_b[0], y=pos_b[1], z=pos_b[2], mode='lines', name="Starlink Orbit", line=dict(color='red', width=4)))

fig.update_layout(scene=dict(aspectmode='cube'), margin=dict(l=0, r=0, b=0, t=0))
st.plotly_chart(fig, use_container_width=True)
