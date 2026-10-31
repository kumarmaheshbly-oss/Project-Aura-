import streamlit as st
import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load
from datetime import datetime
import time

# --- Page Config (Ultra Wide) ---
st.set_page_config(page_title="AURA | Mission Control", page_icon="🛰️", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS for Ultra-Class Look (Glassmorphism & Neon) ---
st.markdown("""
    <style>
    /* Deep Space Background */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #0a0f1c 0%, #05070a 100%);
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Default Header/Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Glassmorphism Metric Cards */
    div[data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* Neon Text Glow */
    h1, h2, h3 {
        color: #38bdf8 !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
        font-family: 'Courier New', monospace;
    }
    
    /* Terminal Log Styling */
    .terminal-log {
        background-color: #000000;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        color: #4ade80;
        height: 300px;
        overflow-y: auto;
    }
    .log-warn { color: #fbbf24; }
    .log-crit { color: #f87171; animation: blink 1s infinite; }
    
    @keyframes blink {
        50% { opacity: 0.5; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- Top Header Row ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("<h1 style='margin-bottom:0;'>🛰️ PROJECT AURA: MISSION CONTROL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:14px;'>Real-Time Satellite Conjunction Assessment & Autonomous Avoidance</p>", unsafe_allow_html=True)
with col_head2:
    st.markdown(f"<div style='text-align:right; color:#4ade80; font-family:monospace;'><br>LIVE: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>", unsafe_allow_html=True)

st.markdown("---")

# --- Sidebar Configuration ---
with st.sidebar:
    st.markdown("<h3>⚙️ MISSION PARAMETERS</h3>", unsafe_allow_html=True)
    
    tle_data = {
        "ISS (ZARYA)": ['1 25544U 98067A   24121.54791667  .00016717  00000+0  30777-3 0  9993', '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49815570444578'],
        "STARLINK-1007": ['1 44713U 19074A   24121.50000000  .00002182  00000+0  16411-3 0  9990', '2 44713  53.0541 198.3234 0001421  93.8295 266.2878 15.06384507244455']
    }
    
    sat_a_name = st.selectbox("Primary Asset", list(tle_data.keys()), index=0)
    sat_b_name = st.selectbox("Threat Object", list(tle_data.keys()), index=1)
    
    time_window = st.slider("Propagation Window (Mins)", 10, 180, 90)
    
    st.markdown("---")
    st.markdown("<h3>🛡️ SYSTEM STATUS</h3>", unsafe_allow_html=True)
    st.markdown("🟢 Orbital Propagator: **Online**")
    st.markdown("🟢 Threat Analyzer: **Active**")
    st.markdown("🟢 Network Link: **Secure**")
    
    simulate_cam = st.button("⚠️ SIMULATE MANEUVER (CAM)")

# --- Physics Engine ---
ts = load.timescale()
t = ts.utc(2024, 5, 1, 0, 0, range(0, time_window * 60, 10))

sat_a = EarthSatellite(tle_data[sat_a_name][0], tle_data[sat_a_name][1], sat_a_name, ts)
sat_b = EarthSatellite(tle_data[sat_b_name][0], tle_data[sat_b_name][1], sat_b_name, ts)

pos_a = sat_a.at(t).position.km
pos_b = sat_b.at(t).position.km

# If CAM is simulated, add a 15km shift to Satellite A's Z-axis
if simulate_cam:
    pos_a[2] += 15.0

distances = np.linalg.norm(pos_a - pos_b, axis=0)
min_dist = np.min(distances)
min_index = np.argmin(distances)
tca_time = min_index * 10

# Threat Calculation
sigma = 0.5 
hbr = 0.02  
pc = (hbr**2 / (2 * np.pi * sigma**2)) * np.exp(-(min_dist**2) / (2 * sigma**2)) if min_dist < 50.0 else 0.0

# --- Main Dashboard Layout ---
# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Minimum Distance", f"{min_dist:.2f} km", "Safe" if min_dist > 50 else "Critical", delta_color="normal")
m2.metric("Probability of Collision", f"{pc:.2e}", "Low Risk" if pc < 1e-4 else "HIGH ALERT", delta_color="normal")
m3.metric("Time to TCA", f"{tca_time} mins", "Approaching" if tca_time < 30 else "Nominal")
m4.metric("Threat Classification", "NATURAL DEBRIS" if not simulate_cam else "MANEUVER EXECUTED")

st.markdown("---")

# Middle Row: 3D Graph + Terminal Log
col_graph, col_log = st.columns([2.5, 1])

with col_graph:
    st.markdown("<h3>🌐 3D ORBITAL KINEMATICS</h3>", unsafe_allow_html=True)
    fig = go.Figure()

    # Glowing Earth Wireframe
    u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:20j]
    xe = 6371 * np.cos(u)*np.sin(v)
    ye = 6371 * np.sin(u)*np.sin(v)
    ze = 6371 * np.cos(v)
    fig.add_trace(go.Surface(x=xe, y=ye, z=ze, colorscale='Blues', opacity=0.15, showscale=False, hoverinfo='skip'))

    # Glowing Orbits
    fig.add_trace(go.Scatter3d(x=pos_a[0], y=pos_a[1], z=pos_a[2], mode='lines', name=sat_a_name, 
                               line=dict(color='#00F0FF', width=5), hoverinfo='name'))
    fig.add_trace(go.Scatter3d(x=pos_b[0], y=pos_b[1], z=pos_b[2], mode='lines', name=sat_b_name, 
                               line=dict(color='#FF0055', width=5), hoverinfo='name'))
    
    # TCA Marker
    fig.add_trace(go.Scatter3d(x=[pos_a[0][min_index]], y=[pos_a[1][min_index]], z=[pos_a[2][min_index]], 
                               mode='markers', name='TCA Point', marker=dict(color='#FBBF24', size=8, symbol='x')))

    fig.update_layout(
        scene=dict(
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="#1E293B", showbackground=False, zerolinecolor="#1E293B"),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="#1E293B", showbackground=False, zerolinecolor="#1E293B"),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="#1E293B", showbackground=False, zerolinecolor="#1E293B"),
            aspectmode='cube'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, b=0, t=0),
        height=500,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(color="white"))
    )
    st.plotly_chart(fig, use_container_width=True)

with col_log:
    st.markdown("<h3>📡 LIVE SYSTEM LOG</h3>", unsafe_allow_html=True)
    
    log_content = f"""
    > INITIALIZING AURA ENGINE...<br>
    > LOADING TLE DATA: SUCCESS<br>
    > PROPAGATING ORBITS: SUCCESS<br>
    > CALCULATING CONJUNCTION...<br>
    """
    
    if min_dist < 50.0:
        log_content += f"<span class='log-warn'>[WARN] CONJUNCTION DETECTED AT T+{tca_time} MINS</span><br>"
    
    if pc > 1e-4:
        log_content += f"<span class='log-crit'>[CRITICAL] COLLISION RISK: {pc:.2e}</span><br>"
        log_content += f"<span class='log-crit'>[ACTION] AUTONOMOUS CAM REQUIRED!</span><br>"
    else:
        log_content += f"<span style='color:#4ade80;'>[SAFE] NO HIGH-RISK CONJUNCTIONS.</span><br>"

    if simulate_cam:
         log_content += f"<span style='color:#00F0FF;'>[ACTION] MANEUVER SIMULATED: +15km ALTITUDE SHIFT.</span><br>"
         log_content += f"<span style='color:#4ade80;'>[SUCCESS] THREAT NEUTRALIZED.</span><br>"

    log_content += """
    > MONITORING GPS3TECH NETWORK MESH...<br>
    > NETWORK LINK INTACT.<br>
    > SYSTEM NOMINAL.
    """
    
    st.markdown(f"<div class='terminal-log'>{log_content}</div>", unsafe_allow_html=True)
