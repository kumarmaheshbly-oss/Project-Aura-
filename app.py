import streamlit as st
import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="AURA-SHIELD OS", page_icon="🛰️", layout="centered")

# --- ULTIMATE MOBILE-FIRST CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    /* Deep Space Background */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #0a0f1c 0%, #000000 100%);
        color: #E2E8F0;
        font-family: 'Share Tech Mono', monospace;
    }
    
    /* Fix Button */
    .stButton > button {
        background: rgba(0, 255, 255, 0.05);
        color: #00FFFF;
        border: 1px solid #00FFFF;
        border-radius: 8px;
        font-family: 'Share Tech Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
        padding: 10px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: #00FFFF;
        color: #000;
        box-shadow: 0 0 20px #00FFFF;
    }
    
    /* Responsive Grid for Cards */
    .hud-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    
    /* Perfectly Sized Glassmorphism Cards */
    .hud-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 10px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 90px; /* Fixed height for perfect uniformity */
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.05);
    }
    
    .hud-title {
        font-size: 10px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
        text-align: center;
    }
    
    .hud-value {
        font-size: 18px; /* Perfect size for mobile */
        color: #00FFFF;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        white-space: nowrap; /* Prevents text wrap */
    }
    
    .hud-alert { color: #FF0055; text-shadow: 0 0 10px rgba(255, 0, 85, 0.5); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    /* Hide Streamlit elements */
    header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1 style='text-align: center; color: #00FFFF; text-shadow: 0 0 15px #00FFFF; margin-bottom: 0; font-size: 24px;'>AURA-SHIELD OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #4ade80; font-size: 11px; margin-top: 0;'>SYSTEM LIVE | UTC {datetime.utcnow().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

# --- Controls ---
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
    <div class="hud-grid">
        <div class="hud-card">
            <div class="hud-title">MISS DISTANCE</div>
            <div class="hud-value">{min_dist:.1f} km</div>
        </div>
        <div class="hud-card">
            <div class="hud-title">PROBABILITY (Pc)</div>
            <div class="hud-value">{pc:.2e}</div>
        </div>
        <div class="hud-card">
            <div class="hud-title">TIME-TO-TCA</div>
            <div class="hud-value">{tca_time} m</div>
        </div>
        <div class="hud-card">
            <div class="hud-title">STATUS</div>
            <div class="hud-value {status_class}">{status_text}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 3D Graph (Clean Mode) ---
fig = go.Figure()

# Earth
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
xe = 6371 * np.cos(u)*np.sin(v)
ye = 6371 * np.sin(u)*np.sin(v)
ze = 6371 * np.cos(v)
fig.add_trace(go.Surface(x=xe, y=ye, z=ze, colorscale='Blues', opacity=0.1, showscale=False, hoverinfo='skip'))

# Satellites
fig.add_trace(go.Scatter3d(x=pos_a[0], y=pos_a[1], z=pos_a[2], mode='lines', name='ISS', line=dict(color='#00FFFF', width=4), hoverinfo='skip'))
fig.add_trace(go.Scatter3d(x=pos_b[0], y=pos_b[1], z=pos_b[2], mode='lines', name='STARLINK', line=dict(color='#FF0055', width=4), hoverinfo='skip'))

if not simulate_cam:
    fig.add_trace(go.Scatter3d(x=[pos_a[0][min_index]], y=[pos_a[1][min_index]], z=[pos_a[2][min_index]], mode='markers', name='TCA', marker=dict(color='#FFFF00', size=6, symbol='x'), hoverinfo='skip'))

# CLEAN LAYOUT: No axes, No toolbar, No default legend
fig.update_layout(
    scene=dict(
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        bgcolor='rgba(0,0,0,0)', aspectmode='cube'
    ),
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, b=0, t=0), height=350,
    showlegend=False # Hiding Plotly's ugly default legend
)

# config={'displayModeBar': False} removes the floating icons on top
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- Custom HTML Legend ---
st.markdown("""
    <div style="display: flex; justify-content: center; gap: 15px; font-family: 'Share Tech Mono', monospace; font-size: 12px; margin-bottom: 20px;">
        <div style="color: #00FFFF;"><span style="color: #00FFFF;">━</span> ISS</div>
        <div style="color: #FF0055;"><span style="color: #FF0055;">━</span> STARLINK</div>
        <div style="color: #FFFF00;"><span style="color: #FFFF00;">✖</span> TCA</div>
    </div>
""", unsafe_allow_html=True)

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
    <div style="background-color: #000; border: 1px solid #333; border-radius: 5px; padding: 10px; font-family: 'Share Tech Mono', monospace; color: {color}; font-size: 11px; height: 70px;">
    {log}
    </div>
""", unsafe_allow_html=True)
