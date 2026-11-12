"""
Project Aura — AURA-SHIELD v28.0 (Ultimate Maximum Edition)
The absolute farthest a pure Streamlit + Plotly SSA platform can go.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone, timedelta
import time
import io
import json

# Optional PDF support
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AURA-SHIELD v28 | Project Aura",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(ellipse at 50% -20%, #1e293b 0%, #0f172a 42%, #020617 100%);
        color: #e2e8f0;
    }
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.62);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 16px;
        padding: 15px 17px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        transition: all 0.28s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.55);
        box-shadow: 0 16px 48px rgba(56, 189, 248, 0.18);
    }
    div[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.8rem !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.65rem !important; font-weight: 800 !important; color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.98);
        border-right: 1px solid rgba(56, 189, 248, 0.15);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        border: 1px solid rgba(56, 189, 248, 0.12);
        color: #94a3b8;
        padding: 8px 14px;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.2) !important;
        color: #38bdf8 !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.3);
    }
    h1 { text-shadow: 0 0 28px rgba(56, 189, 248, 0.4); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PDF GENERATOR
# ─────────────────────────────────────────────
if PDF_AVAILABLE:
    class AuraPDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'PROJECT AURA - CONJUNCTION ASSESSMENT', 0, 1, 'C')
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, f'Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}', 0, 1, 'C')
            self.line(10, 25, 200, 25)
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()} | Research Prototype', 0, 0, 'C')

    def generate_pdf(threat, dv, fuel, target_sep):
        pdf = AuraPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "1. Event Telemetry", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(50, 8, "Primary Object:", border=0)
        pdf.cell(0, 8, str(threat.get('primary_object', 'ISS')), ln=True)
        pdf.cell(50, 8, "Secondary Object:", border=0)
        pdf.cell(0, 8, str(threat.get('secondary_object')), ln=True)
        pdf.cell(50, 8, "Risk Level:", border=0)
        pdf.cell(0, 8, str(threat.get('risk')), ln=True)
        pdf.cell(50, 8, "Miss Distance:", border=0)
        pdf.cell(0, 8, f"{threat.get('miss_distance_m', 0):,.2f} m", ln=True)
        pdf.cell(50, 8, "Foster Pc:", border=0)
        pdf.cell(0, 8, f"{threat.get('pc_foster_exact', 0):.2e}", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. RTN Geometry", ln=True)
        pdf.set_font("Arial", size=11)
        rtn = threat.get('rtn_data', {})
        pdf.cell(50, 8, "Radial (R):", border=0)
        pdf.cell(0, 8, f"{rtn.get('radial', 0):,.2f} m", ln=True)
        pdf.cell(50, 8, "In-Track (T):", border=0)
        pdf.cell(0, 8, f"{rtn.get('in_track', 0):,.2f} m", ln=True)
        pdf.cell(50, 8, "Cross-Track (N):", border=0)
        pdf.cell(0, 8, f"{rtn.get('cross_track', 0):,.2f} m", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Maneuver Assessment (CAM)", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(50, 8, "Target Separation:", border=0)
        pdf.cell(0, 8, f"{target_sep} m", ln=True)
        pdf.cell(50, 8, "Required Delta-V:", border=0)
        pdf.cell(0, 8, f"{dv:.3f} m/s", ln=True)
        pdf.cell(50, 8, "Estimated Fuel:", border=0)
        pdf.cell(0, 8, f"{fuel:.2f} kg", ln=True)

        return pdf.output(dest='S').encode('latin-1')

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🛰️ Project Aura")
    st.markdown("**AURA-SHIELD v28.0**")
    st.caption("Ultimate Maximum Edition")
    st.divider()

    st.subheader("⚙️ Mission Controls")
    primary_asset = st.selectbox("Primary Asset", ["ISS (ZARYA)", "Hubble", "CSS (Tianhe)", "Starlink-1007 (Mock)"])
    hbr = st.slider("Hard Body Radius (m)", 5, 250, 45, 5)
    auto_refresh = st.toggle("🔄 Auto-refresh (50s)", value=False)
    demo_mode = st.toggle("🚨 Critical RED Simulator", value=False)

    if demo_mode:
        st.error("CRITICAL DEMO ACTIVE")

    st.divider()
    if st.button("🔄 Force Refresh", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.subheader("📡 System Status")
    st.markdown("""
    <div style="font-family:monospace;font-size:0.74rem;line-height:1.65;color:#94a3b8;">
    [CORE] Engine: <span style="color:#4ade80">ONLINE</span><br>
    [API] Cloud: <span style="color:#38bdf8">FALLBACK</span><br>
    [CAM] Physics: <span style="color:#4ade80">ADVANCED</span><br>
    [3D] Geometry: <span style="color:#38bdf8">READY</span><br>
    [PDF] Report: <span style="color:#facc15">""" + ("AVAILABLE" if PDF_AVAILABLE else "Install fpdf2") + """</span><br>
    [ANIM] Relative: <span style="color:#4ade80">ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.caption(f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

# ─────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────
CLOUD_API = "https://aura-backend-api-2.onrender.com"

@st.cache_data(ttl=45, show_spinner=False)
def fetch_cloud():
    try:
        r = requests.get(f"{CLOUD_API}/api/reports/", timeout=9)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def generate_ultimate_fallback(primary="ISS (ZARYA)"):
    now = datetime.now(timezone.utc)
    base = [
        ("STARLINK-4821", 890, 11.2, 1.8e-5, "ORANGE", 210, -780, 290),
        ("COSMOS-1408 DEBRIS", 420, 13.7, 2.9e-4, "RED", 85, -310, 155),
        ("STARLINK-3012", 2450, 9.8, 4.1e-7, "YELLOW", -980, 2100, -620),
        ("FENGYUN-1C DEBRIS", 1780, 12.4, 8.6e-6, "ORANGE", 340, -1450, 480),
        ("STARLINK-2156", 6200, 14.9, 2.3e-9, "GREEN", 1800, -5100, 2200),
        ("IRIDIUM-33 DEBRIS", 980, 10.1, 3.4e-5, "ORANGE", -150, 820, -310),
        ("STARLINK-4478", 11200, 13.2, 7.1e-11, "GREEN", 3200, -8900, 4100),
        ("COSMOS-2251 DEBRIS", 3100, 8.9, 9.2e-7, "YELLOW", 1100, -2600, 900),
        ("STARLINK-1789", 540, 12.8, 1.1e-4, "RED", 120, -410, 210),
        ("ONEWEB-0124", 8700, 11.5, 4.8e-10, "GREEN", -2400, 7200, -1800),
        ("CZ-5B ROCKET BODY", 1350, 10.6, 1.5e-5, "ORANGE", 280, -1100, 390),
        ("STARLINK-5190", 7600, 13.8, 3.9e-10, "GREEN", 1900, -6400, 2800),
    ]
    data = []
    for i, (name, miss, speed, pc, risk, r, it, ct) in enumerate(base):
        hours = np.random.uniform(1.2, 40)
        data.append({
            "id": i + 1,
            "primary_object": primary,
            "secondary_object": name,
            "tca": (now + timedelta(hours=hours)).isoformat().replace("+00:00", "Z"),
            "miss_distance_m": float(miss) * np.random.uniform(0.85, 1.15),
            "relative_speed_km_s": float(speed) * np.random.uniform(0.92, 1.08),
            "pc_foster_exact": float(pc) * np.random.uniform(0.7, 1.4),
            "risk": risk,
            "rtn_data": {
                "radial": float(r) * np.random.uniform(0.9, 1.1),
                "in_track": float(it) * np.random.uniform(0.9, 1.1),
                "cross_track": float(ct) * np.random.uniform(0.9, 1.1)
            },
            "created_at": now.isoformat().replace("+00:00", "Z")
        })
    return data

with st.spinner("☁️ Establishing secure link..."):
    raw = fetch_cloud()

data_source = "Cloud API"
if raw is None or len(raw) < 3:
    raw = generate_ultimate_fallback(primary_asset)
    data_source = "Ultimate Fallback Dataset"

df = pd.DataFrame(raw)
df["primary_object"] = primary_asset   

if demo_mode:
    fake = {
        "id": 9999,
        "primary_object": primary_asset,
        "secondary_object": "COSMOS-1408 DEBRIS (CRITICAL DEMO)",
        "tca": (datetime.now(timezone.utc) + timedelta(hours=1.45)).isoformat().replace("+00:00", "Z"),
        "miss_distance_m": 241.8,
        "relative_speed_km_s": 14.6,
        "pc_foster_exact": 8.7e-4,
        "risk": "RED",
        "rtn_data": {"radial": 52.3, "in_track": -198.4, "cross_track": 97.1},
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    df = pd.concat([pd.DataFrame([fake]), df], ignore_index=True)

df["tca"] = pd.to_datetime(df["tca"], utc=True)
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["radial_m"] = df["rtn_data"].apply(lambda x: float(x.get("radial", 0)) if isinstance(x, dict) else 0.0)
df["in_track_m"] = df["rtn_data"].apply(lambda x: float(x.get("in_track", 0)) if isinstance(x, dict) else 0.0)
df["cross_track_m"] = df["rtn_data"].apply(lambda x: float(x.get("cross_track", 0)) if isinstance(x, dict) else 0.0)

now_utc = pd.Timestamp.now(tz="UTC")
df["hours_to_tca"] = (df["tca"] - now_utc).dt.total_seconds() / 3600.0

def compute_risk_score(row):
    pc = max(row["pc_foster_exact"], 1e-16)
    pc_score = min(42, -np.log10(pc) * 3.1)
    miss_score = max(0, 28 - (row["miss_distance_m"] / 160))
    time_score = max(0, 18 - row["hours_to_tca"] * 0.55)
    vel_score = min(12, row["relative_speed_km_s"] * 0.7)
    return round(pc_score + miss_score + time_score + vel_score, 1)

df["risk_score"] = df.apply(compute_risk_score, axis=1)
df["action_required"] = df["risk_score"] > 52

risk_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "GREEN": 3}
df["risk_rank"] = df["risk"].map(risk_order).fillna(9)
df = df.sort_values(["risk_rank", "risk_score"], ascending=[True, False]).reset_index(drop=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("Space Situational Awareness")
st.markdown(f"**Ultimate Autonomous Conjunction Assessment & CAM Platform** &nbsp;|&nbsp; Primary: `{primary_asset}` &nbsp;|&nbsp; Source: `{data_source}`")

red = int((df["risk"] == "RED").sum())
orange = int((df["risk"] == "ORANGE").sum())
yellow = int((df["risk"] == "YELLOW").sum())
green = int((df["risk"] == "GREEN").sum())
action = int(df["action_required"].sum())

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Events", len(df))
k2.metric("🔴 RED", red)
k3.metric("🟠 ORANGE", orange)
k4.metric("🟡 YELLOW", yellow)
k5.metric("🟢 GREEN", green)
k6.metric("⚡ Action Req.", action)

if red > 0:
    st.error("🚨 **CRITICAL RED ALERT ACTIVE** — Immediate CAM assessment required")

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Risk Queue",
    "📈 Intelligence",
    "🎯 Deep Dive + CAM",
    "🌌 3D Geometry",
    "📄 Mission Report"
])

# ─── TAB 1 ───────────────────────────────────
with tab1:
    st.subheader("Live Priority Risk Queue")

    c1, c2, c3, c4 = st.columns([2.2, 1.1, 1.1, 1.1])
    with c1:
        search = st.text_input("🔍 Search Secondary Object", placeholder="e.g. COSMOS, STARLINK...")
    with c2:
        risk_f = st.multiselect("Risk Filter", ["RED", "ORANGE", "YELLOW", "GREEN"],
                                default=["RED", "ORANGE", "YELLOW", "GREEN"])
    with c3:
        max_miss = st.slider("Max Miss (m)", 100, 15000, 11000, 100)
    with c4:
        max_h = st.slider("Max Hours", 1, 48, 36)

    filtered = df[
        (df["risk"].isin(risk_f)) &
        (df["miss_distance_m"] <= max_miss) &
        (df["hours_to_tca"] <= max_h) &
        (df["hours_to_tca"] > -1.5)
    ].copy()

    if search.strip():
        filtered = filtered[filtered["secondary_object"].str.contains(search, case=False, na=False)]

    def style_risk(val):
        return {
            "RED": "background-color:rgba(248,113,113,0.25);color:#f87171;font-weight:700",
            "ORANGE": "background-color:rgba(251,146,60,0.22);color:#fb923c;font-weight:700",
            "YELLOW": "background-color:rgba(250,204,21,0.18);color:#facc15;font-weight:700",
            "GREEN": "background-color:rgba(74,222,128,0.12);color:#4ade80;font-weight:600",
        }.get(val, "")

    show = filtered[[
        "secondary_object", "risk", "risk_score", "hours_to_tca",
        "miss_distance_m", "pc_foster_exact", "relative_speed_km_s", "action_required"
    ]].copy()
    show.columns = ["Secondary", "Risk", "Score", "Hours", "Miss (m)", "Pc", "Speed", "Action"]

    st.dataframe(
        show.style.map(style_risk, subset=["Risk"]).format({
            "Score": "{:.1f}", "Hours": "{:.1f}", "Miss (m)": "{:,.0f}",
            "Pc": "{:.2e}", "Speed": "{:.2f}"
        }),
        use_container_width=True, height=430
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button("📥 CSV Export", filtered.to_csv(index=False).encode(),
                           "aura_v28_queue.csv", "text/csv")
    with col_b:
        st.download_button("📥 JSON Export", filtered.to_json(orient="records", indent=2).encode(),
                           "aura_v28_queue.json", "application/json")

# ─── TAB 2 ───────────────────────────────────
with tab2:
    st.subheader("Conjunction Intelligence")

    a1, a2 = st.columns(2)
    with a1:
        fig = px.pie(df, names="risk", hole=0.55, color="risk",
                     color_discrete_map={"RED":"#f87171","ORANGE":"#fb923c","YELLOW":"#facc15","GREEN":"#4ade80"},
                     title="Risk Distribution")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)

    with a2:
        fig = px.scatter(df, x="miss_distance_m", y="risk_score", color="risk",
                         size="pc_foster_exact", hover_name="secondary_object",
                         title="Miss Distance vs Risk Score",
                         color_discrete_map={"RED":"#f87171","ORANGE":"#fb923c","YELLOW":"#facc15","GREEN":"#4ade80"},
                         size_max=24)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Time-to-TCA Priority Map")
    fig = px.scatter(df.sort_values("hours_to_tca"), x="hours_to_tca", y="miss_distance_m",
                     color="risk", size="risk_score", hover_name="secondary_object",
                     color_discrete_map={"RED":"#f87171","ORANGE":"#fb923c","YELLOW":"#facc15","GREEN":"#4ade80"},
                     size_max=20)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis_title="Hours to TCA", yaxis_title="Miss Distance (m)")
    st.plotly_chart(fig, use_container_width=True)

# ─── TAB 3 ───────────────────────────────────
with tab3:
    st.subheader("Threat Deep Dive + Advanced CAM Engine")

    if "selected_threat" not in st.session_state:
        st.session_state.selected_threat = df["secondary_object"].iloc[0]

    selected = st.selectbox("Select Threat Object", df["secondary_object"].tolist(),
                            index=list(df["secondary_object"]).index(st.session_state.selected_threat)
                            if st.session_state.selected_threat in df["secondary_object"].values else 0)
    st.session_state.selected_threat = selected
    threat = df[df["secondary_object"] == selected].iloc[0]

    if threat["risk"] == "RED":
        st.error(f"🚨 CRITICAL — {selected} | Score: {threat['risk_score']}")
    elif threat["risk"] == "ORANGE":
        st.warning(f"⚠️ HIGH — {selected} | Score: {threat['risk_score']}")
    else:
        st.success(f"✅ Nominal — {selected} | Score: {threat['risk_score']}")

    left, right = st.columns([1, 1.15])

    with left:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.72);padding:18px;border-radius:14px;border:1px solid #334155;">
            <h3 style="margin:0 0 10px 0;color:#38bdf8;">Telemetry</h3>
            <p><b>Miss Distance</b><br><span style="font-size:1.35rem;color:#38bdf8;">{threat['miss_distance_m']:,.1f} m</span></p>
            <p><b>Relative Speed</b><br>{threat['relative_speed_km_s']:.2f} km/s</p>
            <p><b>Foster Pc</b><br><span style="color:{'#f87171' if threat['risk']=='RED' else '#4ade80'};font-weight:700;">{threat['pc_foster_exact']:.2e}</span></p>
            <p><b>Hours to TCA</b><br><span style="color:#facc15;">{threat['hours_to_tca']:.2f} h</span></p>
            <p><b>Risk Score</b><br><span style="font-size:1.25rem;">{threat['risk_score']}</span> / 100</p>
            <hr style="border-color:#334155;">
            <p style="margin-bottom:3px;"><b>RTN</b></p>
            <ul style="margin:0;padding-left:16px;font-size:0.92rem;">
                <li>Radial: {threat['radial_m']:,.1f} m</li>
                <li>In-Track: {threat['in_track_m']:,.1f} m</li>
                <li>Cross-Track: {threat['cross_track_m']:,.1f} m</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### Decision Support")
        if threat["risk_score"] > 70:
            st.error("**IMMEDIATE CAM recommended.** High Pc + short time-to-TCA.")
        elif threat["risk_score"] > 55:
            st.warning("**CAM strongly advised.** Monitor closely and prepare burn.")
        elif threat["risk_score"] > 40:
            st.info("Elevated risk. Continue monitoring. Prepare contingency.")
        else:
            st.success("Geometry currently acceptable. No urgent action.")

    with right:
        st.markdown("##### B-Plane + Covariance")
        it = threat["in_track_m"]
        ct = threat["cross_track_m"]
        theta = np.linspace(0, 2*np.pi, 90)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hbr*np.cos(theta), y=hbr*np.sin(theta), mode="lines",
                                 name="HBR", line=dict(color="#ef4444", width=2, dash="dash"),
                                 fill="toself", fillcolor="rgba(239,68,68,0.1)"))
        sig_it = max(abs(it)*0.2, 100)
        sig_ct = max(abs(ct)*0.2, 100)
        fig.add_trace(go.Scatter(x=it + sig_it*np.cos(theta), y=ct + sig_ct*np.sin(theta),
                                 mode="lines", name="≈1σ Cov", line=dict(color="#38bdf8", width=1.5, dash="dot"),
                                 fill="t
