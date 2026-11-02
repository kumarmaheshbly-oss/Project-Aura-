import streamlit as st
import pandas as pd
import json
import plotly.express as px

# 1. Page Configuration
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

# 2. Sidebar - File Uploader (Enterprise Feature)
st.sidebar.header("📁 Data Management")
uploaded_file = st.sidebar.file_uploader("Upload AURA-SHIELD Report (JSON)", type=["json"])

report = None
if uploaded_file is not None:
    report = json.load(uploaded_file)
    st.sidebar.success("✅ Custom report loaded successfully!")
else:
    # Agar koi file upload nahi karta, toh default file dhundhega
    try:
        with open("AURA_SHIELD_v22_Report.json", "r") as f:
            report = json.load(f)
        st.sidebar.info("Showing default repository data.")
    except FileNotFoundError:
        st.error("No data found! Please upload a report JSON from the sidebar.")
        st.stop()
    except json.JSONDecodeError:
        st.error("The default JSON file is corrupted. Please upload a valid report.")
        st.stop()

# 3. Safely Extract Summary (Fixes KeyError)
# Agar JSON mein risk_summary nahi hai, toh hum results se khud count kar lenge
summary = report.get("risk_summary")
if not summary:
    summary = {"RED": 0, "ORANGE": 0, "YELLOW": 0, "GREEN": 0}
    for res in report.get("results", []):
        risk = res.get("risk", "GREEN")
        if risk in summary:
            summary[risk] += 1

results = report.get("results", [])
primary_obj = report.get("primary", "Unknown")
version = report.get("version", "Unknown")
gen_time = report.get("generated_at", "Unknown")

# 4. Top Metrics (KPI Cards)
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Primary Object", primary_obj)
col2.metric("Objects Screened", len(results))
col3.metric("🔴 RED Alerts", summary.get("RED", 0), delta_color="inverse")
col4.metric("🟠 ORANGE Alerts", summary.get("ORANGE", 0))
col5.metric("🟡 YELLOW Alerts", summary.get("YELLOW", 0))

st.divider()

# 5. Main Dashboard Layout
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("⚠️ Conjunction Risk Queue")
    
    if len(results) == 0:
        st.info("No objects screened in this run.")
    else:
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        
        # Ensure columns exist before displaying
        display_cols = ["secondary", "risk", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]
        available_cols = [c for c in display_cols if c in df.columns]
        df_display = df[available_cols].copy()
        
        # Rename columns for professional look
        rename_map = {
            "secondary": "Secondary Object",
            "risk": "Risk Level",
            "miss_distance_m": "Miss Distance (m)",
            "relative_speed_km_s": "Rel. Speed (km/s)",
            "pc_foster_exact": "Foster Exact Pc"
        }
        df_display.rename(columns=rename_map, inplace=True)
        
        # Color code the Risk column
        def color_risk(val):
            color = 'red' if val == 'RED' else 'orange' if val == 'ORANGE' else 'yellow' if val == 'YELLOW' else 'green'
            return f'color: {color}; font-weight: bold'
        
        if 'Risk Level' in df_display.columns:
            st.dataframe(df_display.style.map(color_risk, subset=['Risk Level']), use_container_width=True, height=500)
        else:
            st.dataframe(df_display, use_container_width=True, height=500)

with right_col:
    st.subheader("🎯 Top Threat Details")
    if len(results) > 0:
        # Sort results by Pc (highest first) to ensure top threat is at index 0
        sorted_results = sorted(results, key=lambda x: x.get("pc_foster_exact", 0), reverse=True)
        top_threat = sorted_results[0]
        
        st.info(f"**Object:** {top_threat.get('secondary', 'Unknown')}")
        
        risk_status = top_threat.get('risk', 'GREEN')
        if risk_status == 'RED':
            st.error(f"**Risk Status:** {risk_status}")
        elif risk_status == 'ORANGE':
            st.warning(f"**Risk Status:** {risk_status}")
        elif risk_status == 'YELLOW':
            st.warning(f"**Risk Status:** {risk_status}")
        else:
            st.success(f"**Risk Status:** {risk_status}")
            
        st.write("**RTN Relative Geometry (meters):**")
        rtn_m = top_threat.get('rtn_m', {})
        rtn_data = {
            "Direction": ["Radial", "In-Track", "Cross-Track"],
            "Distance (m)": [
                rtn_m.get('radial', 0), 
                rtn_m.get('in_track', 0), 
                rtn_m.get('cross_track', 0)
            ]
        }
        st.table(pd.DataFrame(rtn_data))
        
        st.caption("Note: RTN values are calculated relative to the Primary's orbit (EME2000 frame).")

# 6. Methodology / Disclaimer Footer
st.divider()
st.caption(f"Data generated at: {gen_time} | Engine Version: {version}")
st.caption("Disclaimer: This is a research prototype. Do not use for actual operational collision avoidance.")
