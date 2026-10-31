import streamlit as st
import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load
import time

# --- Page Config ---
st.set_page_config(page_title="Project Aura | Mission Control", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Professional Look ---
st.markdown("""
    <style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: #1E2129;
        border: 1px solid #2E323D;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* Hide Main Menu and Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Custom Fonts */
    h1, h2, h3 {
        color: #4CAF50 !important;
        font-family: 'Courier New', Courier, monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1 style='text-align: center;'>🛰️ PROJECT AURA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #A0AAB5;'>Real-Time Satellite Conjunction Assessment & Collision Avoidance</p>", unsafe_allow_html=True)
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b2/NASA_logo.svg", width=100)
    st.header("Mission Parameters")
    
    tle_data = {
        "ISS (ZARYA)": ['1 25544U 98067A   24121.54791667  .00016717  00000+0  30777-3 0  9993', '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49815570444578'],
        "STARLINK-1007": ['1 44713U 19074A   24121.50000000  .00002182  00000+0  16411-3 0  9990', '2 44713  53.0541 198.3234 0001421  93.8295 266.2878 15.06384507244455']
    }
    
    sat_a_name = st.selectbox("Primary Asset (Sat A)", list(tle_data.keys()), index=0)
    sat_b_name = st.selectbox("Secondary Object (Sat B)", list(tle_data.keys()), index=1)
    
    time_window = st.slider("Time Window (Minutes)", 10, 120, 90)
    st.info("System running on Skyfield Engine.")

# --- Calculations ---
ts = load.timescale()
t = ts.utc(2024, 5, 1, 0, 0, range(0, time_window * 60, 10))

sat_a = EarthSatellite(tle_data[sat_a_name][0], tle_data[sat_a_name][1], sat_a_name, ts)
sat_b = EarthSatellite(tle_data[sat_b_name][0], tle_data[sat_b_name][1], sat_b_name, ts)

pos_a = sat_a.at(t).position.km
pos_b = sat_b.at(t).position.km

distances = np.linalg.norm(pos_a - pos_b, axis=0)
min_dist = np.min(distances)
min_index = np.argmin(distances)

sigma = 0.5 
hbr = 0.02  
pc = (hbr**2 / (2 * np.pi * sigma**2)) * np.exp(-(min_dist**2) / (2 * sigma**2)) if min_dist < 50.0 else 0.0

# --- Metrics Row ---
col1, col2, col3 = st.columns(3)
col1.metric("Minimum Distance", f"{min_dist:.2f} km", "Safe" if min_dist > 50 else "Critical", delta_color="normal" if min_dist > 50 else "inverse")
col2.metric("Probability of Collision (Pc)", f"{pc:.2e}", "Below Threshold (1e-4)" if pc < 1e-4 else "Above Threshold", delta_color="normal" if pc < 1e-4 else "inverse")

if pc > 1e-4:
    col3.error("🚨 HIGH RISK DETECTED")
else:
    col3.success("✅ SYSTEM SECURE")

st.divider()

# --- 3D Plotly Graph ---
st.subheader("🌐 3D Orbital Trajectories (ECI Frame)")
fig = go.Figure()

# Earth
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:20j]
xe = 6371 * np.cos(u)*np.sin(v)
ye = 6371 * np.sin(u)*np.sin(v)
ze = 6371 * np.cos(v)
fig.add_trace(go.Surface(x=xe, y=ye, z=ze, colorscale='Blues', opacity=0.4, showscale=False, name='Earth'))

# Orbits
fig.add_trace(go.Scatter3d(x=pos_a[0], y=pos_a[1], z=pos_a[2], mode='lines', name=sat_a_name, line=dict(color='#00BFFF', width=4)))
fig.add_trace(go.Scatter3d(x=pos_b[0], y=pos_b[1], z=pos_b[2], mode='lines', name=sat_b_name, line=dict(color='#FF4500', width=4)))

# Mark TCA
fig.add_trace(go.Scatter3d(x=[pos_a[0][min_index]], y=[pos_a[1][min_index]], z=[pos_a[2][min_index]], mode='markers', name='TCA Point', marker=dict(color='yellow', size=8, symbol='x')))

fig.update_layout(
    scene=dict(
        xaxis=dict(backgroundcolor="rgb(20, 20, 20)", gridcolor="rgb(50, 50, 50)", showbackground=True),
        yaxis=dict(backgroundcolor="rgb(20, 20, 20)", gridcolor="rgb(50, 50, 50)", showbackground=True),
        zaxis=dict(backgroundcolor="rgb(20, 20, 20)", gridcolor="rgb(50, 50, 50)", showbackground=True),
        aspectmode='cube'
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, b=0, t=0),
    height=600,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"Data Source: Space-Track TLEs | Engine: Skyfield | Computed for Window: T+{time_window} mins")
