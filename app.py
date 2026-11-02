import streamlit as st
import pandas as pd
import json
import plotly.express as px

# 1. Page Configuration (Enterprise Look)
st.set_page_config(page_title="Project Aura | SSA Dashboard", page_icon="🛰️", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("🛰️ Project Aura: Space Situational Awareness")
st.markdown("**AURA-SHIELD v22.0** | Real-time Conjunction Assessment via Foster Pc Engine")

# 2. Load Data
try:
    with open("AURA_SHIELD_v22_Report.json", "r") as f:
        report = json.load(f)
except FileNotFoundError:
    st.error("Report file not found! Please run the Colab script first to generate `AURA_SHIELD_v22_Report.json` and upload it to GitHub.")
    st.stop()

# 3. Top Metrics (KPI Cards)
summary = report["risk_summary"]
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Primary Object", report["primary"])
col2.metric("Objects Screened", report["total_objects_screened"])
col3.metric("🔴 RED Alerts", summary.get("RED", 0), delta_color="inverse")
col4.metric("🟠 ORANGE Alerts", summary.get("ORANGE", 0))
col5.metric("🟡 YELLOW Alerts", summary.get("YELLOW", 0))

st.divider()

# 4. Main Dashboard Layout
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("⚠️ Conjunction Risk Queue")
    
    if len(report["results"]) == 0:
        st.info("No objects screened in this run.")
    else:
        # Convert results to DataFrame
        df = pd.DataFrame(report["results"])
        
        # Format the dataframe for display
        df_display = df[["secondary", "risk", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]]
        df_display.columns = ["Secondary Object", "Risk Level", "Miss Distance (m)", "Rel. Speed (km/s)", "Foster Exact Pc"]
        
        # Color code the Risk column
        def color_risk(val):
            color = 'red' if val == 'RED' else 'orange' if val == 'ORANGE' else 'yellow' if val == 'YELLOW' else 'green'
            return f'color: {color}; font-weight: bold'
        
        st.dataframe(df_display.style.map(color_risk, subset=['Risk Level']), use_container_width=True, height=500)

with right_col:
    st.subheader("🎯 Top Threat Details")
    if len(report["results"]) > 0:
        top_threat = report["results"][0]
        
        st.info(f"**Object:** {top_threat['secondary']}")
        
        # Use st.warning for RED, st.success for GREEN
        if top_threat['risk'] == 'RED':
            st.error(f"**Risk Status:** {top_threat['risk']}")
        elif top_threat['risk'] == 'ORANGE':
            st.warning(f"**Risk Status:** {top_threat['risk']}")
        else:
            st.success(f"**Risk Status:** {top_threat['risk']}")
            
        st.write("**RTN Relative Geometry (meters):**")
        rtn_data = {
            "Direction": ["Radial", "In-Track", "Cross-Track"],
            "Distance (m)": [top_threat['rtn_m']['radial'], top_threat['rtn_m']['in_track'], top_threat['rtn_m']['cross_track']]
        }
        st.table(pd.DataFrame(rtn_data))
        
        st.caption("Note: RTN values are calculated relative to the Primary's orbit (EME2000 frame).")

# 5. Methodology / Disclaimer Footer
st.divider()
st.caption(f"Data generated at: {report['generated_at']} | Engine: {report['version']}")
st.caption("Disclaimer: This is a research prototype. Do not use for actual operational collision avoidance.")
