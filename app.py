import streamlit as st
import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="AURA | Mission Control", page_icon="🛰️", layout="wide")

# --- Custom CSS (Mobile Friendly) ---
st.markdown("""
    <style>
    /* Dark Space Background */
    .stApp { background-color: #05070a; color: #E2E8F0; }
    
    /* Neon Headings */
    h1, h2, h3 { color: #38bdf8 !important; font-family: 'Courier New', monospace; }
    
    /* Custom Metric Grid (For Mobile View) */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    .metric-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .metric-title { font-size: 12px; color: #94a3b8; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: bold; color: #38bdf8; }
    .metric-status { font-size: 12px; color: #4ade80; }
    
    /* Terminal Box */
    .terminal-box {
        background-color: #000;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 10px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        color: #4ade80;
        height: 200px;
        overflow-y: auto;
    }
    
    /* Hide Streamlit elements */
    header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1>🛰️ AURA-SHIELD OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#4ade80; font-family:monospace; font-size:12px;'>LIVE UTC: {datetime.utcnow().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h3>⚙️ CONTROLS</h3>", unsafe_allow_html=True)
    sim_status = st.button("🚨 EXECUTE MANEUVER", use_container_width=True)

# --- Physics ---
ts = load.timescale()
t = ts.utc(2024, 5, 1, 0, 0, range(0, 5400, 10))
tle1 = ['1 25544U 98067A   24121.54791667  .00016717  00000+0  30777-3 0  9993', '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49815570444578']
tle2 = ['1 44713U 19074A   24121.50000000  .00002182  00000+0  16411-3 0  9990', '2 44713  53.0541 198.3234 0001421  93.8295 266.2878 15.06384507244455']

sat_a = EarthSatellite(tle1[0], tle1[1], "ISS", ts)
sat_b = EarthSatellite(tle2[0], tle2[1], "STARLINK", ts)
pos_a = sat_a.at(t).position.km
pos_b = sat_b.at(t).position.km

if sim_status: pos_a[2] += 20.0 # Maneuver shift

distances = np.linalg.norm(pos_a - pos_b, axis=0)
min_dist = np.min(distances)
min_index = np.argmin(distances)
tca_time = min_index * 10
pc = (0.02**2 / (2 * np.pi * 0.5**2)) * np.exp(-(min_dist**2) / (2 * 0.5**2)) if min_dist < 50.0 else 0.0

# --- Custom Metrics Grid ---
status_text = "SECURE" if pc < 1e-4 else "CRITICAL"
status_color = "#4ade80" if pc < 1e-4 else "#f87171"

st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-box">
            <div class="metric-title">Miss Distance</div>
            <div class="metric-value">{min_dist:.1f} km</div>
        </div>
        <div class="metric-box">
            <div class="metric-title">Probability (Pc)</div>
            <div class="metric-value">{pc:.2e}</div>
        </div>
        <div class="metric-box">
            <div class="metric-title">Time to TCA</div>
            <div class="metric-value">{tca_time} m</div>
        </div>
        <div class="metric-box" style="border-color: {status_color};">
            <div class="metric-title">Status</div>
            <div class="metric-value" style="color: {status_color};">{status_text}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 3D Graph (Compact for Mobile) ---
fig = go.Figure()
u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
fig.add_trace(go.Surface(x=6371*np.cos(u)*np.sin(v), y=6371*np.sin(u)*np.sin(v), z=6371*np.cos(v), colorscale='Blues', opacity=0.1, showscale=False))
fig.add_trace(go.Scatter3d(x=pos_a[0], y=pos_a[1], z=pos_a[2], mode='lines', name='ISS', line=dict(color='#00F0FF', width=4)))
fig.add_trace(go.Scatter3d(x=pos_b[0], y=pos_b[1], z=pos_b[2], mode='lines', name='STARLINK', line=dict(color='#FF0055', width=4)))

fig.update_layout(
    scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), aspectmode='cube'),
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, b=0, t=0), height=350, # Height kam kar di
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# --- Terminal Logs (Neeche) ---
log = f"> INITIALIZING AURA OS...<br>> FETCHING TLE DATA: SUCCESS<br>"
if sim_status: log += "<span style='color:#00F0FF;'>[ACTION] CAM MANEUVER EXECUTED</span><br><span style='color:#4ade80;'>[SUCCESS] THREAT NEUTRALIZED</span>"
elif pc > 1e-4: log += "<span style='color:#f87171;'>[CRITICAL] HIGH RISK DETECTED</span>"
else: log += "<span style='color:#4ade80;'>[SAFE] NO CONJUNCTIONS</span>"

st.markdown(f"<div class='terminal-box'>{log}</div>", unsafe_allow_html=True)
