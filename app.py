import streamlit as st
import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load
from datetime import datetime
import time

# --- Page Config ---
st.set_page_config(page_title="AURA-SHIELD | Mission Control", page_icon="🛰️", layout="wide", initial_sidebar_state="collapsed")

# --- ULTIMATE CUSTOM CSS (The "Wow" Factor) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    /* Deep Space Background */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #0a0f1c 0%, #000000 100%);
        color: #E2E8F0;
        font-family: 'Share Tech Mono', monospace;
    }
    
    /* Glassmorphism Metric Cards */
    .hud-card {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    .hud-card:hover {
        border-color: rgba(0, 255, 255, 0.8);
        box-shadow: 0 0 25px rgba(0, 255, 255, 0.4);
    }
    .hud-title {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .hud-value {
        font-size: 24px;
        color: #00FFFF;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }
    .hud-alert {
        color: #FF0055;
        text-shadow: 0 0 10px rgba(255, 0, 85, 0.5);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* Custom Button */
    .stButton > button {
        background: rgba(0, 255, 255, 0.1);
        color: #00FFFF;
        border: 1px solid #00FFFF;
        border-radius: 5px;
        font-family: 'Share Tech Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        background: #00FFFF;
        color: #000;
        box-shadow: 0 0 20px #00FFFF;
    }
    
    /* Hide Default Elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1 style='text-align: center; color: #00FFFF; text-shadow: 0 0 20px #00FFFF; margin-bottom: 0;'>AURA-SHIELD OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #4ade80; font-size: 12px;'>SYSTEM LIVE | UTC {datetime.utcnow().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

# --- Controls ---
col_btn, col_empty = st.columns([1, 3])
with col_btn:
    simulate_cam = st.button("🚨 EXECUTE CAM MANEUVER")

# --- Core Logic ---
ts = load.timescale()
t = ts.utc(2024, 5, 1, 0, 0, range(0, 5400, 10))
tle1 = ['1 25544U 98067A   24121.54791667  .00016717  00000+0  30777-3 0  9993', '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49815570444578']
tle2 = ['1 44713U 19074A   24121.50000000  .00002182  00000+0  16411-3 0  9990', '2 44713  53.0541 198.3234 0001421  93.8295 266.2878 15.06384507244455']

sat_a = EarthSatellite(tle1[0], tle1[1], "ISS", ts)
sat_b = EarthSatellite(tle2[0], tle2[1], "STARLINK", ts)
pos_a = sat_a.at(t).position.km
pos_b = sat_b.at(t).position.km

if simulate_cam: pos_a[2] += 20.0 

distances = np.linalg.norm(pos_a - pos_b, axis=0)
min_dist = np.min(distances)
min_index = np.argmin(distances)
tca_time = min_index * 10
pc = (0.02**2 / (2 * np.pi * 0.5**2)) * np.exp(-(min_dist**2) / (2 * 0.5**2)) if min_dist < 50.0 else 0.0

# --- Custom HUD Metrics ---
status_class = "hud-alert" if pc > 1e-4 else ""
status_text = "CRITICAL" if pc > 1e-4 else "SECURE"

st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px;">
        <div class="hud-card">
            <div class="hud-title">Miss Distance</div>
            <div class="hud-value">{min_dist:.1f} km</div>
        </div>
        <div class="hud-card">
            <div class="hud-title">Probability (Pc)</div>
            <div class="hud-value">{pc:.2e}</div>
        </div>
        <div class="hud-card">
            <div class="hud-title">Time to TCA</div>
            <div class="hud-value">{tca_time} m</div>
        </div>
        <div class="hud-card">
            <div class="hud-title">System Status</div>
            <div class="hud-value {status_class}">{status_text}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- The Ultra 3D Graph ---
fig = go.Figure()

# Add a glowing Earth wireframe (Hidden axes for cleaner look)
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
xe = 6371 * np.cos(u)*np.sin(v)
ye = 6371 * np.sin(u)*np.sin(v)
ze = 6371 * np.cos(v)
fig.add_trace(go.Surface(x=xe, y=ye, z=ze, colorscale='Blues', opacity=0.15, showscale=False, hoverinfo='skip'))

# Satellites (Neon Colors)
fig.add_trace(go.Scatter3d(x=pos_a[0], y=pos_a[1], z=pos_a[2], mode='lines', name='ISS', line=dict(color='#00FFFF', width=4), hoverinfo='name'))
fig.add_trace(go.Scatter3d(x=pos_b[0], y=pos_b[1], z=pos_b[2], mode='lines', name='STARLINK', line=dict(color='#FF0055', width=4), hoverinfo='name'))

# TCA Point (Yellow Glowing X)
if not simulate_cam:
    fig.add_trace(go.Scatter3d(x=[pos_a[0][min_index]], y=[pos_a[1][min_index]], z=[pos_a[2][min_index]], mode='markers', name='TCA', marker=dict(color='#FFFF00', size=8, symbol='x')))

fig.update_layout(
    scene=dict(
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        bgcolor='rgba(0,0,0,0)', aspectmode='cube'
    ),
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, b=0, t=0), height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
)
st.plotly_chart(fig, use_container_width=True)

# --- Terminal ---
if simulate_cam:
    log = "> [EXECUTING] AUTONOMOUS CAM...<br>> [BURN] APPLYING DELTA-V<br>> [SUCCESS] THREAT NEUTRALIZED. ORBIT SECURE."
    color = "#00FFFF"
elif pc > 1e-4:
    log = "> [CRITICAL] HIGH RISK DETECTED<br>> [ACTION] MANEUVER REQUIRED"
    color = "#FF0055"
else:
    log = "> [SAFE] NO CONJUNCTIONS IN WINDOW.<br>> [STANDBY] MONITORING NETWORK MESH."
    color = "#4ade80"

st.markdown(f"""
    <div style="background-color: #000; border: 1px solid #333; border-radius: 5px; padding: 15px; font-family: 'Share Tech Mono', monospace; color: {color}; font-size: 14px; height: 100px; box-shadow: inset 0 0 10px rgba(0,0,0,0.8);">
    {log}
    </div>
""", unsafe_allow_html=True)
