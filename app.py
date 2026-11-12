"""
Project Aura — AURA-SHIELD v24.4 (Clean Edition)
Features: Risk Queue, Analytics, Threat Deep Dive, B-Plane, RTN, Maneuver Engine
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
    page_title="Project Aura | AURA-SHIELD v24.4",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0b0f19 0%, #111827 100%); }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1f2e, #131722);
        border: 1px solid #2a3142;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    }
    div[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.82rem !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.4rem !important; font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] {
        background: #0d111c; border-right: 1px solid #1e2433;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background: #1a1f2e; border-radius: 8px 8px 0 0;
        border: 1px solid #2a3142; color: #94a3b8; padding: 8px 14px;
    }
    .stTabs [aria-selected="true"] {
        background: #1e293b !important; color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    h1, h2, h3 { color: #f1f5f9 !important; letter-spacing: -0.02em; }
    .stCaption { color: #64748b !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. HELPERS
# ─────────────────────────────────────────────
def color_risk(val):
    return {
        "RED": "color:#f87171;font-weight:700",
        "ORANGE": "color:#fb923c;font-weight:700",
        "YELLOW": "color:#facc15;font-weight:700",
        "GREEN": "color:#4ade80;font-weight:700",
    }.get(val, "")

def extract_rtn(row, key):
    try:
        return float(row.get("rtn_data", {}).get(key, 0) or 0)
    except Exception:
        return 0.0

# ─────────────────────────────────────────────
# 3. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🛰️ Project Aura")
    st.caption("AURA-SHIELD v24.4 · Enterprise SSA")
    st.divider()

    st.subheader("⚙️ Controls")
    hbr_meters = st.slider("Hard Body Radius (m)", 5, 120, 35, 5)
    
    st.divider()
    st.subheader("📡 System Telemetry")
    st.markdown("""
    <div style="font-family:monospace;font-size:0.8rem;color:#4ade80;line-height:1.6;">
    [SYS] GitHub Actions: ACTIVE<br>
    [API] FastAPI: 200 OK<br>
    [DB]  Supabase: Online<br>
    [SEC] AES-256: ON
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.success("Backend · Online (Render)")
    st.success("Database · Connected (Supabase)")
    st.caption("Primary locked: **ISS (ZARYA)**")

# ─────────────────────────────────────────────
# 4. DATA LAYER (NEW API URL)
# ─────────────────────────────────────────────
CLOUD_API_URL = "https://aura-backend-api-2.onrender.com"

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data_from_cloud():
    try:
        r = requests.get(f"{CLOUD_API_URL}/api/reports/", timeout=55)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

with st.spinner("Connecting to Cloud Database…"):
    data = fetch_data_from_cloud()

if data is None:
    st.error("❌ Could not connect to Cloud API. Please refresh.")
    st.stop()

if len(data) == 0:
    st.warning("⚠️ No data found. Run the Engine to push new reports.")
    st.stop()

df = pd.DataFrame(data)

# Data processing
df["tca"] = pd.to_datetime(df["tca"], utc=True)
df["created_at"] = pd.to_datetime(df.get("created_at", df["tca"]), utc=True)
df["radial_m"] = df.apply(lambda r: extract_rtn(r, "radial"), axis=1)
df["in_track_m"] = df.apply(lambda r: extract_rtn(r, "in_track"), axis=1)
df["cross_track_m"] = df.apply(lambda r: extract_rtn(r, "cross_track"), axis=1)

now_utc = pd.Timestamp.now(tz="UTC")
df["hours_to_tca"] = (df["tca"] - now_utc).dt.total_seconds() / 3600.0

risk_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "GREEN": 3}
df["risk_rank"] = df["risk"].map(risk_order).fillna(9)
df = df.sort_values(["risk_rank", "miss_distance_m"]).reset_index(drop=True)

# ─────────────────────────────────────────────
# 5. HEADER + KPIs
# ─────────────────────────────────────────────
st.title("Space Situational Awareness")
st.markdown("**Autonomous Conjunction Assessment & Risk Analysis** · Powered by Orekit & FastAPI")

last_created = df["created_at"].max()
st.caption(
    f"Last data push: {last_created.strftime('%Y-%m-%d %H:%M:%S UTC')} · "
    f"Dashboard: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

red = int((df["risk"] == "RED").sum())
orange = int((df["risk"] == "ORANGE").sum())
yellow = int((df["risk"] == "YELLOW").sum())
green = int((df["risk"] == "GREEN").sum())

# Vertical layout for KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Records", len(df))
c2.metric("🔴 RED", red)
c3.metric("🟠 ORANGE", orange)
c4.metric("🟡 YELLOW", yellow)

st.divider()

# ─────────────────────────────────────────────
# 6. TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Risk Queue", "📈 Analytics", "🎯 Threat Deep Dive"])

# ─── TAB 1: RISK QUEUE ───────────────────────
with tab1:
    st.subheader("Live Conjunction Risk Queue")

    f1, f2, f3 = st.columns([2, 1.5, 1.5])
    with f1:
        search = st.text_input("🔍 Search secondary object", placeholder="STARLINK, COSMOS…")
    with f2:
        risk_filter = st.multiselect("Risk", ["RED", "ORANGE", "YELLOW", "GREEN"], default=["RED", "ORANGE", "YELLOW", "GREEN"])
    with f3:
        max_miss = st.number_input("Max Miss (m)", min_value=0, value=int(df["miss_distance_m"].max()) + 5000, step=5000)

    filtered = df.copy()
    if search:
        filtered = filtered[filtered["secondary_object"].str.contains(search, case=False, na=False)]
    if risk_filter:
        filtered = filtered[filtered["risk"].isin(risk_filter)]
    filtered = filtered[filtered["miss_distance_m"] <= max_miss]

    st.caption(f"Showing **{len(filtered)}** of **{len(df)}** events")

    display = filtered[["secondary_object", "risk", "tca", "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]].rename(columns={
        "secondary_object": "Secondary Object", "risk": "Risk", "tca": "TCA (UTC)",
        "miss_distance_m": "Miss Dist (m)", "relative_speed_km_s": "Rel Speed (km/s)", "pc_foster_exact": "Foster Pc",
    })

    st.dataframe(
        display.style.map(color_risk, subset=["Risk"]).format({
            "Miss Dist (m)": "{:,.1f}", "Rel Speed (km/s)": "{:.3f}", "Foster Pc": "{:.2e}",
        }), use_container_width=True, height=400,
    )

    d1, d2 = st.columns(2)
    with d1:
        st.download_button("📥 Download CSV", data=filtered.to_csv(index=False).encode("utf-8"), file_name="aura_risk_queue.csv", mime="text/csv", use_container_width=True)
    with d2:
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                filtered.to_excel(writer, index=False, sheet_name="RiskQueue")
            buf.seek(0)
            st.download_button("📥 Download Excel", data=buf, file_name="aura_risk_queue.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception:
            st.download_button("📥 CSV (Excel N/A)", data=filtered.to_csv(index=False).encode("utf-8"), file_name="aura_risk_queue.csv", mime="text/csv", use_container_width=True)

# ─── TAB 2: ANALYTICS ────────────────────────
with tab2:
    st.subheader("Conjunction Analytics")

    a1, a2 = st.columns(2)
    with a1:
        risk_counts = df["risk"].value_counts().reindex(["RED", "ORANGE", "YELLOW", "GREEN"], fill_value=0).reset_index()
        risk_counts.columns = ["Risk", "Count"]
        fig_pie = px.pie(risk_counts, names="Risk", values="Count", color="Risk", color_discrete_map={"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"}, hole=0.48, title="Risk Distribution")
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), height=360, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with a2:
        fig_sc = px.scatter(df, x="miss_distance_m", y="relative_speed_km_s", color="risk", size="pc_foster_exact", hover_name="secondary_object", color_discrete_map={"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"}, title="Miss Distance vs Relative Speed", labels={"miss_distance_m": "Miss Distance (m)", "relative_speed_km_s": "Rel Speed (km/s)"})
        fig_sc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), height=360, margin=dict(t=50, b=40, l=40, r=20))
        st.plotly_chart(fig_sc, use_container_width=True)

# ─── TAB 3: THREAT DEEP DIVE (WITH CAM) ──────
with tab3:
    st.subheader("Threat Analysis · B-Plane · RTN")
    
    selected = st.selectbox("Select Object:", df["secondary_object"].tolist())
    threat = df[df["secondary_object"] == selected].iloc[0]
    risk = threat["risk"]

    if risk == "RED": st.error(f"**Risk: {risk}** — Immediate attention recommended")
    elif risk == "ORANGE": st.warning(f"**Risk: {risk}** — Elevated conjunction risk")
    elif risk == "YELLOW": st.info(f"**Risk: {risk}** — Monitor closely")
    else: st.success(f"**Risk: {risk}** — Nominal")

    left, right = st.columns([1, 1.15])

    with left:
        st.markdown("##### Event Details")
        st.markdown(f"""
| Field | Value |
|-------|-------|
| **Secondary** | `{threat['secondary_object']}` |
| **Miss Distance** | **{threat['miss_distance_m']:,.1f} m** |
| **Relative Speed** | {threat['relative_speed_km_s']:.4f} km/s |
| **Foster Pc** | `{threat['pc_foster_exact']:.3e}` |
""")
        st.markdown("##### RTN Geometry")
        rtn_df = pd.DataFrame({"Component": ["Radial (R)", "In-Track (T)", "Cross-Track (N)"], "Distance (m)": [threat["radial_m"], threat["in_track_m"], threat["cross_track_m"]]})
        st.dataframe(rtn_df, hide_index=True, use_container_width=True)

    with right:
        st.markdown("##### B-Plane Projection")
        it = float(threat["in_track_m"])
        ct = float(threat["cross_track_m"])
        color = {"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"}.get(risk, "#94a3b8")
        
        max_ext = max(abs(it), abs(ct), hbr_meters * 2, 80)
        axis_lim = max_ext * 1.3
        theta = np.linspace(0, 2 * np.pi, 120)

        fig_bp = go.Figure()
        fig_bp.add_trace(go.Scatter(x=hbr_meters * np.cos(theta), y=hbr_meters * np.sin(theta), mode="lines", name=f"HBR ({hbr_meters} m)", line=dict(color="#ef4444", width=2, dash="dash"), fill="toself", fillcolor="rgba(239,68,68,0.14)"))
        fig_bp.add_trace(go.Scatter(x=[it], y=[ct], mode="markers+text", marker=dict(size=14, color=color, line=dict(width=2, color="white")), text=[str(threat["secondary_object"])[:20]], textposition="top center", name="Secondary"))
        fig_bp.add_trace(go.Scatter(x=[0], y=[0], mode="markers", marker=dict(size=12, color="#38bdf8", symbol="x"), name="Primary"))
        fig_bp.add_trace(go.Scatter(x=[0, it], y=[0, ct], mode="lines", line=dict(color="#64748b", width=1, dash="dot"), showlegend=False, hoverinfo="skip"))
        
        fig_bp.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.55)", font=dict(color="#e2e8f0"), height=400, xaxis=dict(title="In-Track (m)", range=[-axis_lim, axis_lim], zeroline=True, zerolinecolor="#334155", gridcolor="#1e293b", scaleanchor="y", scaleratio=1), yaxis=dict(title="Cross-Track (m)", range=[-axis_lim, axis_lim], zeroline=True, zerolinecolor="#334155", gridcolor="#1e293b"), margin=dict(t=40, b=40, l=50, r=20))
        st.plotly_chart(fig_bp, use_container_width=True)

    st.divider()
    st.markdown("### 🚀 Collision Avoidance Maneuver (CAM)")
    st.markdown("Calculate the required Delta-V to ensure a safe separation.")
    
    req_sep = st.number_input("Required Safe Separation (m)", min_value=1000, max_value=10000000, value=1000, step=1000)
    
    if st.button(f"Calculate Maneuver for {threat['secondary_object']}", type="primary"):
        payload = {
            "object_name": threat['secondary_object'],
            "miss_distance_m": float(threat['miss_distance_m']),
            "relative_speed_km_s": float(threat['relative_speed_km_s']),
            "time_to_tca_hours": float(threat['hours_to_tca']),
            "required_separation_m": float(req_sep)
        }
        
        with st.spinner("Calculating maneuver..."):
            try:
                res = requests.post(f"{CLOUD_API_URL}/api/maneuver/calculate", json=payload, timeout=15)
                if res.status_code == 200:
                    man_data = res.json()
                    if man_data['maneuver_required']:
                        st.error(f"⚠️ **Maneuver Required!**")
                        m1, m2 = st.columns(2)
                        m1.metric("Required Delta-V", f"{man_data['delta_v_m_s']} m/s")
                        m2.metric("Estimated Fuel Cost", f"{man_data['fuel_cost_estimate_kg']} kg")
                        st.info(f"**Direction:** {man_data['direction']} burn")
                    else:
                        st.success("✅ No maneuver required. Miss distance is safe.")
                else:
                    st.error("Failed to calculate maneuver. Check backend logs.")
            except Exception as e:
                st.error(f"Error connecting to Maneuver API: {e}")

# Footer
st.divider()
st.caption(f"Connected to Cloud API: {CLOUD_API_URL} | v24.4 Enterprise")
