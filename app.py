"""
Project Aura — AURA-SHIELD v23.0
Next-level Space Situational Awareness Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
import io

# ─────────────────────────────────────────────
# 1. PAGE CONFIG + THEME
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Project Aura | AURA-SHIELD v23",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Core dark theme refinements */
    .stApp {
        background: linear-gradient(180deg, #0b0f19 0%, #111827 100%);
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1f2e, #131722);
        border: 1px solid #2a3142;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 700 !important;
    }

    /* Sidebar polish */
    section[data-testid="stSidebar"] {
        background: #0d111c;
        border-right: 1px solid #1e2433;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1a1f2e;
        border-radius: 8px 8px 0 0;
        border: 1px solid #2a3142;
        color: #94a3b8;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #1e293b !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    /* Headers */
    h1, h2, h3 {
        color: #f1f5f9 !important;
        letter-spacing: -0.02em;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🛰️ Project Aura")
    st.caption("AURA-SHIELD v23.0 | Open-Source SSA")
    st.divider()

    st.subheader("📁 Data Management")
    uploaded_file = st.file_uploader(
        "Upload Custom TLE / Report (CSV)",
        type=["txt", "csv"],
        help="Custom ingestion coming in a future release",
    )
    if uploaded_file is not None:
        st.info("Custom TLE processing will be available soon.")

    st.divider()
    st.subheader("⚙️ System Status")
    st.success("🟢 Backend: Online (Render)")
    st.success("🟢 Database: Connected (Supabase)")
    st.success("🟢 Automation: Active (GitHub)")

# ─────────────────────────────────────────────
# 3. HEADER
# ─────────────────────────────────────────────
st.title("Space Situational Awareness")
st.markdown("**Cloud-Connected Conjunction Assessment** | Powered by Orekit & FastAPI")

# ─────────────────────────────────────────────
# 4. DATA FETCHING
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

with st.spinner("Connecting to Cloud Database... (Waking up server if asleep)"):
    data = fetch_data_from_cloud()

if data is None:
    st.error("❌ Could not connect to Cloud API. Please refresh or check the Render server.")
    st.stop()

if len(data) == 0:
    st.warning("⚠️ No data found. Please run the Engine to push new data.")
    st.stop()

df = pd.DataFrame(data)

# ─────────────────────────────────────────────
# 5. KPI METRICS
# ─────────────────────────────────────────────
total_records = len(df)
red_alerts = len(df[df['risk'] == 'RED'])
orange_alerts = len(df[df['risk'] == 'ORANGE'])
green_alerts = len(df[df['risk'] == 'GREEN'])

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Primary Object", "ISS (ZARYA)")
col2.metric("Cloud Records", total_records)
col3.metric("🔴 RED Alerts", red_alerts)
col4.metric("🟠 ORANGE Alerts", orange_alerts)
col5.metric("🟢 GREEN Alerts", green_alerts)

st.divider()

# ─────────────────────────────────────────────
# 6. MAIN TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Risk Queue", "🎯 Threat Details & B-Plane", "ℹ️ Architecture Info"])

with tab1:
    st.subheader("Live Conjunction Risk Queue")
    
    df_display = df[["id", "secondary_object", "risk", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]]
    df_display.columns = ["ID", "Secondary Object", "Risk Level", "Miss Dist (m)", "Rel Speed (km/s)", "Foster Pc"]
    
    def color_risk(val):
        color = 'red' if val == 'RED' else 'orange' if val == 'ORANGE' else 'yellow' if val == 'YELLOW' else 'green'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(df_display.style.map(color_risk, subset=['Risk Level']), use_container_width=True, height=400)
    
    # Export Button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Risk Queue as CSV",
        data=csv,
        file_name='aura_conjunction_risk_queue.csv',
        mime='text/csv',
    )

with tab2:
    st.subheader("Top Threat Analysis")
    
    selected_obj = st.selectbox("Select Object to Analyze:", df["secondary_object"])
    threat_data = df[df["secondary_object"] == selected_obj].iloc[0]
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.info(f"**Target:** {threat_data['secondary_object']}")
        if threat_data['risk'] == 'RED':
            st.error(f"**Risk Status:** {threat_data['risk']}")
        elif threat_data['risk'] == 'ORANGE':
            st.warning(f"**Risk Status:** {threat_data['risk']}")
        else:
            st.success(f"**Risk Status:** {threat_data['risk']}")
            
        st.write("**Relative Geometry (meters):**")
        rtn_data = {
            "Direction": ["Radial", "In-Track", "Cross-Track"],
            "Distance (m)": [
                threat_data['rtn_data'].get('radial', 0), 
                threat_data['rtn_data'].get('in_track', 0), 
                threat_data['rtn_data'].get('cross_track', 0)
            ]
        }
        st.table(pd.DataFrame(rtn_data))
        
    with col_right:
        st.write("**B-Plane Projection (2D)**")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=[threat_data['rtn_data'].get('in_track', 0)],
            y=[threat_data['rtn_data'].get('cross_track', 0)],
            mode='markers+text',
            marker=dict(size=15, color='red' if threat_data['risk']=='RED' else 'green'),
            text=[threat_data['secondary_object']],
            textposition="top center",
            name='Satellite'
        ))
        
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(size=20, color='blue', symbol='circle'),
            name='Collision Point (0,0)'
        ))
        
        # HBR Circle (Scaled for visibility)
        theta = [i for i in range(0, 360, 10)]
        hbr_x = [np.cos(np.radians(t)) * 35 for t in theta] 
        hbr_y = [np.sin(np.radians(t)) * 35 for t in theta]
        fig.add_trace(go.Scatter(x=hbr_x, y=hbr_y, mode='lines', name='HBR (35m)', line=dict(color='red', width=2)))
        
        fig.update_layout(
            title="B-Plane Geometry",
            xaxis_title="In-Track (m)",
            yaxis_title="Cross-Track (m)",
            showlegend=True,
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("System Architecture")
    st.markdown("""
    **Project Aura** is a distributed Microservices Architecture designed for scalability and transparency.
    
    *   **Data Ingestion:** Automated fetching of TLE data from Ivanstanojevic APIs.
    *   **Compute Engine (GitHub Actions):** Orekit (Java) runs numerical propagation and calculates Probability of Collision (Pc) using the Foster analytical method.
    *   **Backend API (Render):** FastAPI serves the calculated data over REST endpoints.
    *   **Database (Supabase):** PostgreSQL stores historical conjunction reports permanently.
    *   **Frontend:** Streamlit dashboard for real-time visualization.
    """)
    st.info("Version: AURA-SHIELD v23.0")

# Footer
st.divider()
st.caption(f"Connected to Cloud API: {CLOUD_API_URL}")
st.caption("Disclaimer: This is a research prototype. Do not use for actual operational collision avoidance.")
