import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Project Aura | SSA Dashboard", page_icon="🛰️", layout="wide")

st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("🛰️ Project Aura: Space Situational Awareness")
st.markdown("**AURA-SHIELD v22.0** | Cloud-Connected Conjunction Assessment")

# 2. Cloud API Setup
CLOUD_API_URL = "https://aura-backend-api-7s3j.onrender.com"

@st.cache_data(ttl=60) # 60 seconds ka cache taaki baar baar API call na ho
def fetch_data_from_cloud():
    try:
        # Timeout is 60 seconds kyunki free Render server ko 'jagne' me time lagta hai
        response = requests.get(f"{CLOUD_API_URL}/api/reports/", timeout=60)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

with st.spinner("Connecting to Cloud Database... (If the server was asleep, this may take 30-50 seconds)"):
    data = fetch_data_from_cloud()

if data is None:
    st.error("❌ Could not connect to Cloud API. Please refresh or check the Render server.")
    st.stop()

# 3. Calculate Metrics
if len(data) == 0:
    st.warning("⚠️ No data found in the Cloud Database. Please run the Colab Engine to push new data.")
    st.stop()

df = pd.DataFrame(data)

# Summary metrics
total_records = len(df)
red_alerts = len(df[df['risk'] == 'RED'])
orange_alerts = len(df[df['risk'] == 'ORANGE'])
green_alerts = len(df[df['risk'] == 'GREEN'])

# 4. Top Metrics (KPI Cards)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Primary Object", "ISS (ZARYA)")
col2.metric("Cloud Records", total_records)
col3.metric("🔴 RED Alerts", red_alerts, delta_color="inverse")
col4.metric("🟠 ORANGE Alerts", orange_alerts)
col5.metric("🟢 GREEN Alerts", green_alerts)

st.divider()

# 5. Main Dashboard Layout
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("⚠️ Live Conjunction Risk Queue")
    
    df_display = df[["secondary_object", "risk", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]]
    df_display.columns = ["Secondary Object", "Risk Level", "Miss Distance (m)", "Rel. Speed (km/s)", "Foster Exact Pc"]
    
    def color_risk(val):
        color = 'red' if val == 'RED' else 'orange' if val == 'ORANGE' else 'yellow' if val == 'YELLOW' else 'green'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(df_display.style.map(color_risk, subset=['Risk Level']), use_container_width=True, height=400)

with right_col:
    st.subheader("🎯 Top Threat Details")
    
    top_threat = df.iloc[0]
    
    st.info(f"**Object:** {top_threat['secondary_object']}")
    
    if top_threat['risk'] == 'RED':
        st.error(f"**Risk Status:** {top_threat['risk']}")
    elif top_threat['risk'] == 'ORANGE':
        st.warning(f"**Risk Status:** {top_threat['risk']}")
    else:
        st.success(f"**Risk Status:** {top_threat['risk']}")
        
    st.write("**RTN Relative Geometry (meters):**")
    rtn_data = {
        "Direction": ["Radial", "In-Track", "Cross-Track"],
        "Distance (m)": [
            top_threat['rtn_data'].get('radial', 0), 
            top_threat['rtn_data'].get('in_track', 0), 
            top_threat['rtn_data'].get('cross_track', 0)
        ]
    }
    st.table(pd.DataFrame(rtn_data))

# 6. Footer
st.divider()
st.caption(f"Connected to Cloud API: {CLOUD_API_URL}")
st.caption("Disclaimer: This is a research prototype. Do not use for actual operational collision avoidance.")
