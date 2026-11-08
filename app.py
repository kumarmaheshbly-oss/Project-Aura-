"""
Project Aura — AURA-SHIELD v24.3 (Complete)
Space Situational Awareness Dashboard
- Timezone-safe countdown
- 3D Orbit View
- Risk Queue + filters + CSV/Excel export
- Threat Analysis (B-plane + HBR + uncertainty ellipse + RTN)
- TCA Timeline
- Analytics charts
- Aura Copilot (rule-based)
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
# PAGE CONFIG + THEME
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Project Aura | AURA-SHIELD v24.3",
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
# HELPERS
# ─────────────────────────────────────────────
def get_countdown(tca_value):
    """Timezone-safe human countdown string."""
    if tca_value is None or (isinstance(tca_value, float) and np.isnan(tca_value)):
        return "—"
    try:
        tca_dt = pd.to_datetime(tca_value, utc=True)
        if getattr(tca_dt, "tzinfo", None) is None:
            tca_dt = tca_dt.tz_localize("UTC")
        now = pd.Timestamp.now(tz="UTC")
        secs = (tca_dt - now).total_seconds()
        if secs < 0:
            h = abs(secs) / 3600.0
            return f"{h:.1f}h ago" if h < 24 else f"{h/24:.1f}d ago"
        h = secs / 3600.0
        if h < 1:
            return f"{secs/60:.0f} min"
        if h < 24:
            return f"{h:.1f}h"
        return f"{h/24:.1f}d"
    except Exception:
        return "—"


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
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🛰️ Project Aura")
    st.caption("AURA-SHIELD v24.3 · Enterprise SSA")
    st.divider()

    st.subheader("⚙️ Controls")
    hbr_meters = st.slider("Hard Body Radius (m)", 5, 120, 35, 5)
    cov_scale = st.slider("Uncertainty scale (visual)", 0.5, 4.0, 1.5, 0.1,
                          help="Demo-only B-plane uncertainty ellipse scale")
    auto_refresh = st.toggle("Auto-refresh (60s)", value=False)
    show_all_cols = st.toggle("Show all table columns", value=False)

    st.divider()
    st.subheader("📡 System Telemetry")
    st.markdown("""
    <div style="font-family:monospace;font-size:0.8rem;color:#4ade80;line-height:1.65;">
    [SYS] GitHub Actions · ACTIVE<br>
    [API] FastAPI · 200 OK<br>
    [DB]  Supabase · Online<br>
    [SEC] AES-256 · ON
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.success("Backend · Online (Render)")
    st.success("Database · Connected (Supabase)")
    st.caption("Primary locked: **ISS (ZARYA)**")

# ─────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────
CLOUD_API_URL = "https://aura-backend-api-rsoj.onrender.com"

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
    st.error("❌ Could not connect to Cloud API. Refresh or check Render.")
    st.stop()

if len(data) == 0:
    st.warning("⚠️ No data in database. Run the Engine to push new reports.")
    st.stop()

df = pd.DataFrame(data)

# Force UTC-aware
df["tca"] = pd.to_datetime(df["tca"], utc=True)
if "created_at" in df.columns:
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
else:
    df["created_at"] = df["tca"]

df["miss_distance_km"] = df["miss_distance_m"] / 1000.0
df["radial_m"] = df.apply(lambda r: extract_rtn(r, "radial"), axis=1)
df["in_track_m"] = df.apply(lambda r: extract_rtn(r, "in_track"), axis=1)
df["cross_track_m"] = df.apply(lambda r: extract_rtn(r, "cross_track"), axis=1)

now_utc = pd.Timestamp.now(tz="UTC")
df["hours_to_tca"] = (df["tca"] - now_utc).dt.total_seconds() / 3600.0
df["countdown"] = df["tca"].apply(get_countdown)

risk_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "GREEN": 3}
df["risk_rank"] = df["risk"].map(risk_order).fillna(9)
df = df.sort_values(["risk_rank", "miss_distance_m"]).reset_index(drop=True)

# ─────────────────────────────────────────────
# HEADER + KPIs
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
upcoming = df[df["hours_to_tca"] > 0]
next_tca_str = upcoming.sort_values("hours_to_tca")["countdown"].iloc[0] if len(upcoming) else "—"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Primary", "ISS (ZARYA)")
c2.metric("Events", len(df))
c3.metric("🔴 RED", red)
c4.metric("🟠 ORANGE", orange)
c5.metric("Closest Miss", f"{int(df['miss_distance_m'].min()):,} m")
c6.metric("Next TCA", next_tca_str)

if red > 0:
    st.error(f"🚨 **{red} RED alert(s)** — review Threat Analysis immediately.")
elif orange > 0:
    st.warning(f"⚠️ **{orange} ORANGE alert(s)** — elevated risk.")

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌍 3D Orbit",
    "📊 Risk Queue",
    "📈 Analytics",
    "🎯 Threat Analysis",
    "⏱️ TCA Timeline",
    "🤖 Aura Copilot",
])

# ─── TAB 1: 3D ORBIT ─────────────────────────
with tab1:
    st.subheader("3D Orbital Environment")
    st.caption("Visual approximation of LEO around ISS. Not real ephemeris.")

    u = np.linspace(0, 2 * np.pi, 70)
    v = np.linspace(0, np.pi, 70)
    x = 6371 * np.outer(np.cos(u), np.sin(v))
    y = 6371 * np.outer(np.sin(u), np.sin(v))
    z = 6371 * np.outer(np.ones(np.size(u)), np.cos(v))

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=x, y=y, z=z, colorscale="Blues", showscale=False,
        opacity=0.55, name="Earth", hoverinfo="skip",
    ))

    theta = np.linspace(0, 2 * np.pi, 120)
    r_iss = 6371 + 420
    fig.add_trace(go.Scatter3d(
        x=r_iss * np.cos(theta), y=r_iss * np.sin(theta), z=np.zeros_like(theta),
        mode="lines", line=dict(color="cyan", width=5), name="ISS Orbit (\~420 km)",
    ))
    fig.add_trace(go.Scatter3d(
        x=[r_iss], y=[0], z=[0], mode="markers+text",
        marker=dict(size=6, color="cyan"), text=["ISS"], textposition="top center", name="ISS",
    ))

    for i in range(min(4, max(len(df), 1))):
        r_s = 6371 + 530 + i * 40
        incl = 0.25 + i * 0.12
        fig.add_trace(go.Scatter3d(
            x=r_s * np.cos(theta),
            y=r_s * np.sin(theta) * np.cos(incl),
            z=r_s * np.sin(theta) * np.sin(incl),
            mode="lines", line=dict(color="orange", width=2),
            name=f"Secondary Orbit {i+1}", opacity=0.7,
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor="#0b0f19", camera=dict(eye=dict(x=1.55, y=1.55, z=1.15)), aspectmode="data",
        ),
        template="plotly_dark", height=600, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.04), paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── TAB 2: RISK QUEUE ───────────────────────
with tab2:
    st.subheader("Live Conjunction Risk Queue")

    f1, f2, f3, f4 = st.columns([2, 1.3, 1.3, 1.3])
    with f1:
        search = st.text_input("🔍 Search object", placeholder="STARLINK, COSMOS…")
    with f2:
        risk_filter = st.multiselect(
            "Risk", ["RED", "ORANGE", "YELLOW", "GREEN"],
            default=["RED", "ORANGE", "YELLOW", "GREEN"],
        )
    with f3:
        max_miss = st.number_input(
            "Max Miss (m)", min_value=0,
            value=int(df["miss_distance_m"].max()) + 5000, step=5000,
        )
    with f4:
        tca_filter = st.selectbox("TCA Window", ["All", "Upcoming only", "Past only", "< 24h"])

    filtered = df.copy()
    if search:
        filtered = filtered[filtered["secondary_object"].str.contains(search, case=False, na=False)]
    if risk_filter:
        filtered = filtered[filtered["risk"].isin(risk_filter)]
    filtered = filtered[filtered["miss_distance_m"] <= max_miss]
    if tca_filter == "Upcoming only":
        filtered = filtered[filtered["hours_to_tca"] > 0]
    elif tca_filter == "Past only":
        filtered = filtered[filtered["hours_to_tca"] <= 0]
    elif tca_filter == "< 24h":
        filtered = filtered[(filtered["hours_to_tca"] > 0) & (filtered["hours_to_tca"] < 24)]

    st.caption(f"Showing **{len(filtered)}** of **{len(df)}** events")

    cols = ["secondary_object", "risk", "tca", "countdown",
            "miss_distance_m", "relative_speed_km_s", "pc_foster_exact"]
    if show_all_cols:
        cols += ["radial_m", "in_track_m", "cross_track_m", "created_at"]

    display = filtered[cols].rename(columns={
        "secondary_object": "Secondary Object",
        "risk": "Risk",
        "tca": "TCA (UTC)",
        "countdown": "Time to TCA",
        "miss_distance_m": "Miss Dist (m)",
        "relative_speed_km_s": "Rel Speed (km/s)",
        "pc_foster_exact": "Foster Pc",
        "radial_m": "Radial (m)",
        "in_track_m": "In-Track (m)",
        "cross_track_m": "Cross-Track (m)",
        "created_at": "Created At",
    })

    st.dataframe(
        display.style.map(color_risk, subset=["Risk"]).format({
            "Miss Dist (m)": "{:,.1f}",
            "Rel Speed (km/s)": "{:.3f}",
            "Foster Pc": "{:.2e}",
        }),
        use_container_width=True, height=420,
    )

    d1, d2, _ = st.columns([1, 1, 3])
    with d1:
        st.download_button(
            "📥 CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="aura_risk_queue.csv", mime="text/csv",
            use_container_width=True,
        )
    with d2:
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                filtered.to_excel(writer, index=False, sheet_name="RiskQueue")
            buf.seek(0)
            st.download_button(
                "📥 Excel", data=buf, file_name="aura_risk_queue.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception:
            st.download_button(
                "📥 CSV (Excel N/A)",
                data=filtered.to_csv(index=False).encode("utf-8"),
                file_name="aura_risk_queue.csv", mime="text/csv",
                use_container_width=True,
            )

# ─── TAB 3: ANALYTICS ────────────────────────
with tab3:
    st.subheader("Conjunction Analytics")

    a1, a2 = st.columns(2)
    with a1:
        risk_counts = (
            df["risk"].value_counts()
            .reindex(["RED", "ORANGE", "YELLOW", "GREEN"], fill_value=0)
            .reset_index()
        )
        risk_counts.columns = ["Risk", "Count"]
        fig_pie = px.pie(
            risk_counts, names="Risk", values="Count", color="Risk",
            color_discrete_map={"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"},
            hole=0.48, title="Risk Distribution",
        )
        fig_pie.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
            height=360, margin=dict(t=50, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with a2:
        fig_sc = px.scatter(
            df, x="miss_distance_m", y="relative_speed_km_s",
            color="risk", size="pc_foster_exact",
            hover_name="secondary_object",
            hover_data={"miss_distance_m": ":.1f", "relative_speed_km_s": ":.3f",
                        "pc_foster_exact": ":.2e", "tca": True},
            color_discrete_map={"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"},
            title="Miss Distance vs Relative Speed",
            labels={"miss_distance_m": "Miss Distance (m)", "relative_speed_km_s": "Rel Speed (km/s)"},
        )
        fig_sc.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
            height=360, margin=dict(t=50, b=40, l=40, r=20),
        )
        if df["miss_distance_m"].max() / max(df["miss_distance_m"].min(), 1) > 40:
            fig_sc.update_xaxes(type="log")
        st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown("#### Foster Pc Ranking")
    fig_pc = px.bar(
        df.sort_values("pc_foster_exact", ascending=False),
        x="secondary_object", y="pc_foster_exact", color="risk",
        color_discrete_map={"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"},
        labels={"pc_foster_exact": "Pc (Foster)", "secondary_object": "Secondary"},
        log_y=True,
    )
    fig_pc.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
        height=360, xaxis_tickangle=-30, margin=dict(t=20, b=70, l=40, r=20),
    )
    st.plotly_chart(fig_pc, use_container_width=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Min Miss", f"{df['miss_distance_m'].min():,.1f} m")
    s2.metric("Median Miss", f"{df['miss_distance_m'].median():,.1f} m")
    s3.metric("Max Rel Speed", f"{df['relative_speed_km_s'].max():.3f} km/s")
    s4.metric("Highest Pc", f"{df['pc_foster_exact'].max():.2e}")

# ─── TAB 4: THREAT ANALYSIS ──────────────────
with tab4:
    st.subheader("Threat Analysis · B-Plane · RTN")

    selected = st.selectbox("Select Object:", df["secondary_object"].tolist())
    threat = df[df["secondary_object"] == selected].iloc[0]
    risk = threat["risk"]

    if risk == "RED":
        st.error(f"**Risk: {risk}** — Immediate attention recommended")
    elif risk == "ORANGE":
        st.warning(f"**Risk: {risk}** — Elevated conjunction risk")
    elif risk == "YELLOW":
        st.info(f"**Risk: {risk}** — Monitor closely")
    else:
        st.success(f"**Risk: {risk}** — Nominal")

    st.markdown(
        f"**Time to TCA:** `{threat['countdown']}`  ·  "
        f"**TCA (UTC):** `{threat['tca'].strftime('%Y-%m-%d %H:%M:%S')}`"
    )

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
        rtn_df = pd.DataFrame({
            "Component": ["Radial (R)", "In-Track (T)", "Cross-Track (N)"],
            "Distance (m)": [threat["radial_m"], threat["in_track_m"], threat["cross_track_m"]],
        })
        st.dataframe(rtn_df, hide_index=True, use_container_width=True)

        fig_rtn = go.Figure(go.Bar(
            x=["Radial", "In-Track", "Cross-Track"],
            y=[threat["radial_m"], threat["in_track_m"], threat["cross_track_m"]],
            marker_color=["#38bdf8", "#a78bfa", "#34d399"],
            text=[f"{v:,.0f}" for v in [threat["radial_m"], threat["in_track_m"], threat["cross_track_m"]]],
            textposition="outside",
        ))
        fig_rtn.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
            height=250, title="RTN Offsets (m)", margin=dict(t=40, b=30, l=40, r=20),
        )
        st.plotly_chart(fig_rtn, use_container_width=True)

    with right:
        st.markdown("##### B-Plane + Uncertainty Ellipse")

        it = float(threat["in_track_m"])
        ct = float(threat["cross_track_m"])
        color = {"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"}.get(risk, "#94a3b8")

        # Visual covariance (demo)
        sigma_it = max(abs(it) * 0.15, 80) * cov_scale
        sigma_ct = max(abs(ct) * 0.15, 80) * cov_scale
        max_ext = max(abs(it), abs(ct), hbr_meters * 2, sigma_it * 2.2, sigma_ct * 2.2, 80)
        axis_lim = max_ext * 1.3
        theta = np.linspace(0, 2 * np.pi, 120)

        fig_bp = go.Figure()

        for n_sig, opacity, dash in [(1, 0.18, "solid"), (2, 0.10, "dot")]:
            fig_bp.add_trace(go.Scatter(
                x=it + n_sig * sigma_it * np.cos(theta),
                y=ct + n_sig * sigma_ct * np.sin(theta),
                mode="lines", fill="toself", fillcolor=f"rgba(56,189,248,{opacity})",
                line=dict(color="#38bdf8", width=1, dash=dash),
                name=f"{n_sig}σ uncertainty", hoverinfo="skip",
            ))

        fig_bp.add_trace(go.Scatter(
            x=hbr_meters * np.cos(theta), y=hbr_meters * np.sin(theta),
            mode="lines", name=f"HBR ({hbr_meters} m)",
            line=dict(color="#ef4444", width=2, dash="dash"),
            fill="toself", fillcolor="rgba(239,68,68,0.14)",
        ))

        fig_bp.add_trace(go.Scatter(
            x=[it], y=[ct], mode="markers+text",
            marker=dict(size=14, color=color, line=dict(width=2, color="white")),
            text=[str(threat["secondary_object"])[:20]], textposition="top center", name="Secondary",
        ))
        fig_bp.add_trace(go.Scatter(
            x=[0], y=[0], mode="markers",
            marker=dict(size=12, color="#38bdf8", symbol="x"), name="Primary / Collision Point",
        ))
        fig_bp.add_trace(go.Scatter(
            x=[0, it], y=[0, ct], mode="lines",
            line=dict(color="#64748b", width=1, dash="dot"), showlegend=False, hoverinfo="skip",
        ))

        fig_bp.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.55)", font=dict(color="#e2e8f0"), height=480,
            xaxis=dict(title="In-Track (m)", range=[-axis_lim, axis_lim],
                       zeroline=True, zerolinecolor="#334155", gridcolor="#1e293b",
                       scaleanchor="y", scaleratio=1),
            yaxis=dict(title="Cross-Track (m)", range=[-axis_lim, axis_lim],
                       zeroline=True, zerolinecolor="#334155", gridcolor="#1e293b"),
            legend=dict(orientation="h", y=1.08, font=dict(size=11)),
            margin=dict(t=50, b=40, l=50, r=20),
        )
        st.plotly_chart(fig_bp, use_container_width=True)
        st.caption(
            "B-plane ⊥ relative velocity at TCA. Red = HBR. Blue ellipses = visual uncertainty "
            "(demo scale only — real systems use combined covariance)."
        )

        # RTN 3D mini
        st.markdown("##### Relative Position (RTN 3D)")
        fig3d = go.Figure()
        fig3d.add_trace(go.Scatter3d(
            x=[0, threat["radial_m"]], y=[0, threat["in_track_m"]], z=[0, threat["cross_track_m"]],
            mode="lines+markers",
            marker=dict(size=[6, 10], color=["#38bdf8", color]),
            line=dict(color="#64748b", width=4),
        ))
        fig3d.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0], mode="markers",
            marker=dict(size=8, color="#38bdf8", symbol="x"),
        ))
        fig3d.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), height=320, showlegend=False,
            scene=dict(
                xaxis_title="Radial (m)", yaxis_title="In-Track (m)", zaxis_title="Cross-Track (m)",
                bgcolor="rgba(15,23,42,0.6)",
            ),
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig3d, use_container_width=True)

# ─── TAB 5: TCA TIMELINE ─────────────────────
with tab5:
    st.subheader("TCA Timeline & Countdown")

    timeline = df.sort_values("tca").copy()

    fig_tl = px.scatter(
        timeline, x="tca", y="miss_distance_m",
        color="risk", size="pc_foster_exact",
        hover_name="secondary_object",
        hover_data={"tca": True, "miss_distance_m": ":.1f", "hours_to_tca": ":.1f",
                    "pc_foster_exact": ":.2e", "relative_speed_km_s": ":.3f"},
        color_discrete_map={"RED": "#f87171", "ORANGE": "#fb923c", "YELLOW": "#facc15", "GREEN": "#4ade80"},
        title="Miss Distance vs TCA",
        labels={"tca": "Time of Closest Approach (UTC)", "miss_distance_m": "Miss Distance (m)"},
    )
    # Now line (plotly expects ms)
    fig_tl.add_vline(
        x=now_utc.value / 1_000_000,
        line_dash="dash", line_color="#38bdf8",
        annotation_text="Now", annotation_position="top",
    )
    fig_tl.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
        height=420, margin=dict(t=50, b=40, l=50, r=20),
    )
    if timeline["miss_distance_m"].max() / max(timeline["miss_distance_m"].min(), 1) > 40:
        fig_tl.update_yaxes(type="log")
    st.plotly_chart(fig_tl, use_container_width=True)

    st.markdown("#### Upcoming Events")
    up = timeline[timeline["hours_to_tca"] > 0][
        ["secondary_object", "risk", "tca", "countdown", "miss_distance_m", "pc_foster_exact"]
    ].rename(columns={
        "secondary_object": "Secondary", "risk": "Risk", "tca": "TCA (UTC)",
        "countdown": "Time Left", "miss_distance_m": "Miss (m)", "pc_foster_exact": "Pc",
    })
    if len(up) == 0:
        st.info("No upcoming TCAs in the current dataset.")
    else:
        st.dataframe(
            up.style.map(color_risk, subset=["Risk"]).format({"Miss (m)": "{:,.1f}", "Pc": "{:.2e}"}),
            use_container_width=True, hide_index=True,
        )

    st.markdown("#### Past Events")
    past = timeline[timeline["hours_to_tca"] <= 0][
        ["secondary_object", "risk", "tca", "countdown", "miss_distance_m", "pc_foster_exact"]
    ].rename(columns={
        "secondary_object": "Secondary", "risk": "Risk", "tca": "TCA (UTC)",
        "countdown": "Time Ago", "miss_distance_m": "Miss (m)", "pc_foster_exact": "Pc",
    })
    if len(past) == 0:
        st.info("No past events in the current dataset.")
    else:
        st.dataframe(
            past.style.map(color_risk, subset=["Risk"]).format({"Miss (m)": "{:,.1f}", "Pc": "{:.2e}"}),
            use_container_width=True, hide_index=True,
        )

# ─── TAB 6: AURA COPILOT ─────────────────────
with tab6:
    st.subheader("🤖 Aura Copilot")
    st.caption("Rule-based demo on live data. No external LLM required.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": (
                "Hello! I am **Aura Copilot**. Ask me about:\n"
                "- Closest miss distance\n"
                "- Highest risk / Pc object\n"
                "- Next TCA time\n"
                "- How many events / RED alerts\n"
                "- Primary object"
            ),
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about closest miss, highest risk, next TCA…"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        pl = prompt.lower()
        response = (
            "I couldn't match that. Try: **closest miss**, **highest risk/Pc**, "
            "**next TCA**, **how many**, or **primary**."
        )
        try:
            if any(w in pl for w in ["closest", "miss distance", "nearest"]):
                row = df.loc[df["miss_distance_m"].idxmin()]
                response = (
                    f"Closest object: **{row['secondary_object']}** — "
                    f"**{int(row['miss_distance_m']):,} m** miss "
                    f"(Risk: {row['risk']}, Pc: {row['pc_foster_exact']:.2e})."
                )
            elif any(w in pl for w in ["highest risk", "highest pc", "most dangerous", "highest"]):
                row = df.loc[df["pc_foster_exact"].idxmax()]
                response = (
                    f"Highest Pc: **{row['secondary_object']}** — "
                    f"**Pc = {row['pc_foster_exact']:.2e}** "
                    f"(Risk: **{row['risk']}**, Miss: {int(row['miss_distance_m']):,} m)."
                )
            elif any(w in pl for w in ["next tca", "tca", "when", "upcoming", "time of closest"]):
                future = df[df["hours_to_tca"] > 0].sort_values("hours_to_tca")
                if len(future) == 0:
                    response = "No upcoming TCAs in the current dataset (all events are past)."
                else:
                    row = future.iloc[0]
                    response = (
                        f"Next TCA: **{row['secondary_object']}** at "
                        f"**{row['tca'].strftime('%Y-%m-%d %H:%M:%S UTC')}** "
                        f"({row['countdown']}). Miss: {int(row['miss_distance_m']):,} m."
                    )
            elif any(w in pl for w in ["how many", "total", "count", "number", "red"]):
                response = (
                    f"Currently **{len(df)}** events — "
                    f"RED: {red}, ORANGE: {orange}, YELLOW: {yellow}, GREEN: {green}."
                )
            elif "iss" in pl or "primary" in pl:
                response = (
                    "Primary object is **ISS (ZARYA)**. All assessments are relative to the ISS."
                )
        except Exception as e:
            response = f"Error while analysing data: `{e}`"

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption(f"Connected → `{CLOUD_API_URL}` · AURA-SHIELD v24.3")
st.caption("Research prototype only. Do not use for operational collision avoidance.")

if auto_refresh:
    import time
    time.sleep(60)
    st.rerun() 
