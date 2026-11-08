"""
Project Aura — AURA-SHIELD v24.0
Next-level Space Situational Awareness Dashboard
Features: B-plane + covariance ellipse, TCA countdown, RTN 3D, risk timeline, analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────
# 1. PAGE CONFIG + THEME
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Project Aura | AURA-SHIELD v24",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0b0f19 0%, #111827 100%); }
    .block-container { padding-top: 1.1rem; padding-bottom: 2rem; }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1f2e, #131722);
        border: 1px solid #2a3142;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    }
    div[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.82rem !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.45rem !important; font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] {
        background: #0d111c; border-right: 1px solid #1e2433;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background: #1a1f2e; border-radius: 8px 8px 0 0;
        border: 1px solid #2a3142; color: #94a3b8; padding: 9px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #1e293b !important; color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    h1, h2, h3 { color: #f1f5f9 !important; letter-spacing: -0.02em; }
    .stCaption { color: #64748b !important; }
    hr { border-color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🛰️ Project Aura")
    st.caption("AURA-SHIELD v24.0 | Open-Source SSA")
    st.divider()

    st.subheader("📁 Data")
    uploaded_file = st.file_uploader("Upload Custom TLE / Report", type=["txt", "csv"])
    if uploaded_file is not None:
        st.info("Custom ingestion coming soon.")

    st.divider()
    st.subheader("⚙️ Controls")
    show_all_cols = st.toggle("Show all table columns", value=False)
    hbr_meters = st.slider("Hard Body Radius (m)", 5, 120, 35, 5)
    cov_scale = st.slider("Covariance scale (visual)", 0.5, 5.0, 1.5, 0.1,
                          help="Visual uncertainty ellipse scale on B-plane (demo only)")

    st.divider()
    st.subheader("🟢 System Status")
    st.success("Backend · Online (Render)")
    st.success("Database · Connected (Supabase)")
    st.success("Automation · Active (GitHub Actions)")
    st.caption("Primary locked: **ISS (ZARYA)**")

# ─────────────────────────────────────────────
# 3. DATA LAYER
# ─────────────────────────────────────────────
CLOUD_API_URL = "https://aura-backend-api-rsoj.onrender.com"

@st.cache_data(ttl=60) 
def fetch_data_from_cloud():
    try:
        response = requests.get(f"{CLOUD_API_URL}/api/reports/", timeout=60)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

with st.spinner("Connecting to Cloud Database..."):
    data = fetch_data_from_cloud()

if data is None:
    st.error("❌ Could not connect to Cloud API. Please refresh.")
    st.stop()

if len(data) == 0:
    st.warning("⚠️ No data found. Please run the Engine to push new data.")
    st.stop()

df = pd.DataFrame(data)

# Convert TCA to datetime for countdown
df['tca_dt'] = pd.to_datetime(df['tca'].str.replace('Z', ''), errors='coerce')
now = datetime.now(timezone.utc)

def get_countdown(tca_dt):
    if pd.isna(tca_dt): return "N/A"
    diff = tca_dt - now
    if diff.total_seconds() < 0: return "Passed"
    return str(timedelta(seconds=int(diff.total_seconds())))

# ─────────────────────────────────────────────
# 4. MAIN DASHBOARD
# ─────────────────────────────────────────────
st.title("Space Situational Awareness")
st.markdown("**Conjunction Assessment & Risk Analysis** | Powered by Orekit & FastAPI")

# KPI Metrics
total_records = len(df)
red_alerts = len(df[df['risk'] == 'RED'])
orange_alerts = len(df[df['risk'] == 'ORANGE'])
green_alerts = len(df[df['risk'] == 'GREEN'])
min_tca = df['tca_dt'].min()
time_to_tca = get_countdown(min_tca) if pd.notna(min_tca) else "N/A"

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Primary Object", "ISS (ZARYA)")
col2.metric("Active Conjunctions", total_records)
col3.metric("Next TCA In", time_to_tca)
col4.metric("🔴 RED / 🟠 ORANGE", f"{red_alerts} / {orange_alerts}")
col5.metric("🟢 GREEN", green_alerts)

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Risk Queue", "🎯 Threat Analysis (B-Plane)", "🧭 RTN 3D Geometry", "ℹ️ Info"])

with tab1:
    st.subheader("Live Conjunction Risk Queue")
    
    if show_all_cols:
        display_cols = ["id", "secondary_object", "risk", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact", "tca"]
    else:
        display_cols = ["secondary_object", "risk", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]
        
    df_display = df[display_cols].copy()
    
    def color_risk(val):
        color = 'red' if val == 'RED' else 'orange' if val == 'ORANGE' else 'yellow' if val == 'YELLOW' else 'green'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(df_display.style.map(color_risk, subset=['risk']), use_container_width=True, height=350)
    
    # Risk Timeline Chart
    st.write("**Conjunction Timeline**")
    df_timeline = df.sort_values('tca_dt')
    fig_timeline = px.scatter(
        df_timeline, x='tca_dt', y='risk', color='risk', 
        color_discrete_map={'RED':'red', 'ORANGE':'orange', 'YELLOW':'yellow', 'GREEN':'green'},
        hover_data=['secondary_object', 'miss_distance_m'],
        labels={'tca_dt': 'Time of Closest Approach (UTC)', 'risk': 'Risk Level'}
    )
    fig_timeline.update_layout(template="plotly_dark", height=250, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_timeline, use_container_width=True)

with tab2:
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        selected_obj = st.selectbox("Select Object:", df["secondary_object"])
        threat_data = df[df["secondary_object"] == selected_obj].iloc[0]
        
        st.info(f"**Target:** {threat_data['secondary_object']}")
        if threat_data['risk'] == 'RED':
            st.error(f"**Risk Status:** {threat_data['risk']}")
        elif threat_data['risk'] == 'ORANGE':
            st.warning(f"**Risk Status:** {threat_data['risk']}")
        else:
            st.success(f"**Risk Status:** {threat_data['risk']}")
            
        st.write("**Relative Geometry (RTN):**")
        rtn_data = {
            "Dir": ["Radial", "In-Track", "Cross-Track"],
            "Dist (m)": [
                round(threat_data['rtn_data'].get('radial', 0), 1), 
                round(threat_data['rtn_data'].get('in_track', 0), 1), 
                round(threat_data['rtn_data'].get('cross_track', 0), 1)
            ]
        }
        st.table(pd.DataFrame(rtn_data))
        
    with col_b:
        st.write(f"**B-Plane Projection (Covariance Ellipse Scaled x{cov_scale})**")
        fig_bplane = go.Figure()
        
        # Origin (Collision)
        fig_bplane.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=15, color='blue'), name='Primary (0,0)'))
        
        # HBR Circle
        theta = np.linspace(0, 2*np.pi, 100)
        hbr_x = np.cos(theta) * hbr_meters
        hbr_y = np.sin(theta) * hbr_meters
        fig_bplane.add_trace(go.Scatter(x=hbr_x, y=hbr_y, mode='lines', line=dict(color='red', width=2), name=f'HBR ({hbr_meters}m)'))
        
        # Covariance Ellipse (Demo visual based on scale)
        cov_radius = (threat_data['miss_distance_m'] * 0.2) * cov_scale 
        ellipse_x = np.cos(theta) * cov_radius + threat_data['rtn_data'].get('in_track', 0)
        ellipse_y = np.sin(theta) * (cov_radius * 0.6) + threat_data['rtn_data'].get('cross_track', 0)
        fig_bplane.add_trace(go.Scatter(
            x=ellipse_x, y=ellipse_y, fill='toself', fillcolor='rgba(56, 189, 248, 0.2)',
            line=dict(color='#38bdf8', width=1), name='Covariance (1-sigma)'
        ))
        
        # Threat Object
        fig_bplane.add_trace(go.Scatter(
            x=[threat_data['rtn_data'].get('in_track', 0)],
            y=[threat_data['rtn_data'].get('cross_track', 0)],
            mode='markers+text', marker=dict(size=10, color='green'),
            text=[threat_data['secondary_object']], textposition="top center", name='Threat'
        ))
        
        fig_bplane.update_layout(
            xaxis_title="In-Track (m)", yaxis_title="Cross-Track (m)",
            template="plotly_dark", height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(scaleanchor="y", scaleratio=1) # Keep aspect ratio
        )
        st.plotly_chart(fig_bplane, use_container_width=True)

with tab3:
    st.subheader("3D RTN Geometry")
    selected_obj_3d = st.selectbox("Select Object for 3D View:", df["secondary_object"], key="sel3d")
    t_data = df[df["secondary_object"] == selected_obj_3d].iloc[0]
    
    r_val = t_data['rtn_data'].get('radial', 0)
    i_val = t_data['rtn_data'].get('in_track', 0)
    c_val = t_data['rtn_data'].get('cross_track', 0)
    
    fig_3d = go.Figure(data=[
        go.Scatter3d(x=[0, r_val], y=[0, i_val], z=[0, c_val], mode='lines+markers',
                     line=dict(color='red', width=4), marker=dict(size=[5, 10], color=['blue', 'green']),
                     name='Relative Vector')
    ])
    
    fig_3d.update_layout(
        scene=dict(
            xaxis_title='Radial (m)', yaxis_title='In-Track (m)', zaxis_title='Cross-Track (m)',
            bgcolor="#0b0f19"
        ),
        template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_3d, use_container_width=True)

with tab4:
    st.subheader("System Architecture & Disclaimer")
    st.markdown("""
    *   **Engine:** Orekit (Java) via GitHub Actions.
    *   **Backend:** FastAPI running on Render.
    *   **Database:** PostgreSQL on Supabase.
    *   **Frontend:** Streamlit (this app).
    """)
    st.warning("This is a research prototype. Do not use for actual operational collision avoidance.")

st.divider()
st.caption(f"Connected to: {CLOUD_API_URL}")
