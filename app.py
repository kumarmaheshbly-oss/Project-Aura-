streamlit run app.py
"""
Project Aura — AURA-SHIELD v24.1
Space Situational Awareness Dashboard
Fixed timezone handling + full feature set
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
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Project Aura | AURA-SHIELD",
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
# HELPERS
# ─────────────────────────────────────────────
def get_countdown(tca_value):
    """Robust countdown. Always returns string. Never mixes naive/aware."""
    if tca_value is None:
        return "—"
    try:
        tca_dt = pd.to_datetime(tca_value, utc=True)
        if tca_dt.tzinfo is None:
            tca_dt = tca_dt.tz_localize("UTC")
        now = pd.Timestamp.now(tz="UTC")
        diff = tca_dt - now
        total_seconds = diff.total_seconds()

        if total_seconds < 0:
            hours_ago = abs(total_seconds) / 3600.0
            if hours_ago < 24:
                return f"{hours_ago:.1f}h ago"
            return f"{hours_ago / 24:.1f}d ago"

        hours = total_seconds / 3600.0
        if hours < 1:
            return f"{total_seconds / 60:.0f} min"
        if hours < 24:
            return f"{hours:.1f}h"
        return f"{hours / 24:.1f}d"
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
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/b/b4/International_Space_Station_after_undocking_of_STS-132.jpg",
        use_container_width=True,
    )
    st.title("Project Aura")
    st.caption("Open-Source SSA Pipeline")
    st.divider()

    st.subheader("📁 Data")
    uploaded_file = st.file_uploader("Upload Custom TLE / Report", type=["txt", "csv"])
    if uploaded_file is not None:
        st.info("Custom ingestion coming soon.")

    st.divider()
    st.subheader("⚙️ Controls")
    auto_refresh = st.toggle("Auto-refresh (60s)", value=False)
    show_all_cols = st.toggle("Show all table columns", value=False)
    hbr_meters = st.slider("Hard Body Radius (m)", 5, 120, 35, 5)
    cov_scale = st.slider(
        "Covariance scale (visual)", 0.5, 5.0, 1.5, 0.1,
        help="Visual uncertainty ellipse scale on B-plane (demo only)",
    )

    st.divider()
    st.subheader("🟢 System Status")
    st.success("Backend · Online (Render)")
    st.success("Database · Connected (Supabase)")
    st.success("Automation · Active (GitHub Actions)")
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


with st.spinner("Connecting to Cloud Database… (waking Render if asleep)"):
    data = fetch_data_from_cloud()

if data is None:
    st.error("❌ Could not connect to Cloud API. Refresh or check Render.")
    st.stop()

if len(data) == 0:
    st.warning("⚠️ No data in Cloud Database. Run the Engine to push new reports.")
    st.stop()

df = pd.DataFrame(data)

# Enrich — always force UTC
df["tca"] = pd.to_datetime(df["tca"], utc=True)
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["miss_distance_km"] = df["miss_distance_m"] / 1000.0
df["pc_log"] = np.log10(df["pc_foster_exact"].clip(lower=1e-30))

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
st.title("🛰️ Space Situational Awareness")
st.markdown("**AURA-SHIELD v24.1** · Conjunction Assessment & Risk Analysis · Powered by Orekit & FastAPI")

last_created = df["created_at"].max()
st.caption(
    f"Last data push: {last_created.strftime('%Y-%m-%d %H:%M:%S UTC')} · "
    f"Dashboard: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

total = len(df)
red = int((df["risk"] == "RED").sum())
orange = int((df["risk"] == "ORANGE").sum())
yellow = int((df["risk"] == "YELLOW").sum())
green = int((df["risk"] == "GREEN").sum())
min_miss = df["miss_distance_m"].min()

upcoming_mask = df["hours_to_tca"] > 0
next_tca_hours = df.loc[upcoming_mask, "hours_to_tca"].min() if upcoming_mask.any() else None

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.metric("Records", total)
c2.metric("🔴 RED", red)
c3.metric("🟠 ORANGE", orange)
c4.metric("🟡 YELLOW", yellow)
c5.metric("🟢 GREEN", green)
c6.metric("Closest Miss", f"{min_miss:,.0f} m")
c7.metric("Next TCA", f"{next_tca_hours:.1f} h" if next_tca_hours is not None else "—")

if red > 0:
    st.error(f"🚨 **{red} RED alert(s)** detected — review Threat Deep Dive immediately.")
elif orange > 0:
    st.warning(f"⚠️ **{orange} ORANGE alert(s)** — elevated conjunction risk.")

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Risk Queue",
    "📈 Analytics",
    "🎯 Threat Deep Dive",
    "⏱️ TCA Timeline",
    "📄 Architecture",
])

# ─── TAB 1: Risk Queue ───────────────────────
with tab1:
    st.subheader("Live Conjunction Risk Queue")

    f1, f2, f3, f4 = st.columns([2, 1.2, 1.2, 1.2])
    with f1:
        search = st.text_input("🔍 Search secondary object", placeholder="STARLINK, COSMOS…")
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

    display_cols = [
        "id", "secondary_object", "risk", "tca", "countdown",
        "miss_distance_m", "relative_speed_km_s", "pc_foster_exact",
    ]
    if show_all_cols:
        display_cols += ["radial_m", "in_track_m", "cross_track_m", "created_at"]

    df_disp = filtered[display_cols].copy()
    df_disp = df_disp.rename(columns={
        "id": "ID",
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
        df_disp.style.map(color_risk, subset=["Risk"]).format({
            "Miss Dist (m)": "{:,.1f}",
            "Rel Speed (km/s)": "{:.3f}",
            "Foster Pc": "{:.2e}",
        }),
        use_container_width=True,
        height=420,
    )

    col_dl1, col_dl2, _ = st.columns([1, 1, 3])
    with col_dl1:
        st.download_button(
            "📥 CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="aura_risk_queue.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_dl2:
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                filtered.to_excel(writer, index=False, sheet_name="RiskQueue")
            buf.seek(0)
            st.download_button(
                "📥 Excel",
                data=buf,
                file_name="aura_risk_queue.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception:
            st.download_button(
                "📥 CSV (Excel N/A)",
                data=filtered.to_csv(index=False).encode("utf-8"),
                file_name="aura_risk_queue.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ─── TAB 2: Analytics ────────────────────────
with tab2:
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
            color_discrete_map={
                "RED": "#f87171", "ORANGE": "#fb923c",
                "YELLOW": "#facc15", "GREEN": "#4ade80",
            },
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
            hover_data={
                "miss_distance_m": ":.1f",
                "relative_speed_km_s": ":.3f",
                "pc_foster_exact": ":.2e",
                "tca": True,
            },
            color_discrete_map={
                "RED": "#f87171", "ORANGE": "#fb923c",
                "YELLOW": "#facc15", "GREEN": "#4ade80",
            },
            title="Miss Distance vs Relative Speed",
            labels={
                "miss_distance_m": "Miss Distance (m)",
                "relative_speed_km_s": "Rel Speed (km/s)",
            },
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
        color_discrete_map={
            "RED": "#f87171", "ORANGE": "#fb923c",
            "YELLOW": "#facc15", "GREEN": "#4ade80",
        },
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

# ─── TAB 3: Threat Deep Dive ─────────────────
with tab3:
    st.subheader("Threat Analysis · B-Plane · RTN Geometry")

    selected = st.selectbox("Select Secondary Object", df["secondary_object"].tolist(), index=0)
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

    left, right = st.columns([1, 1.2])

    with left:
        st.markdown("##### Event Details")
        st.markdown(f"""
| Field | Value |
|-------|-------|
| **Secondary** | `{threat['secondary_object']}` |
| **Miss Distance** | **{threat['miss_distance_m']:,.1f} m** ({threat['miss_distance_km']:.2f} km) |
| **Relative Speed** | {threat['relative_speed_km_s']:.4f} km/s |
| **Foster Pc** | `{threat['pc_foster_exact']:.3e}` |
| **Record ID** | {threat['id']} |
| **Created** | {threat['created_at'].strftime('%Y-%m-%d %H:%M UTC')} |
""")

        st.markdown("##### RTN Components")
        rtn_df = pd.DataFrame({
            "Component": ["Radial (R)", "In-Track (T)", "Cross-Track (N)"],
            "Distance (m)": [
                threat["radial_m"],
                threat["in_track_m"],
                threat["cross_track_m"],
            ],
        })
        st.dataframe(rtn_df, hide_index=True, use_container_width=True)

        abs_miss = abs(threat["miss_distance_m"])
        if abs_miss < 1000:
            interp = "Very close approach — operational teams would normally prepare avoidance options."
        elif abs_miss < 10000:
            interp = "Inside typical screening volume. Continue monitoring."
        else:
            interp = "Large miss distance. Risk low under nominal assumptions."
        st.caption(f"**Interpretation:** {interp}")

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
            height=260, title="RTN Offsets (m)", margin=dict(t=40, b=30, l=40, r=20),
            yaxis_title="meters",
        )
        st.plotly_chart(fig_rtn, use_container_width=True)

    with right:
        st.markdown("##### B-Plane (In-Track × Cross-Track) + Uncertainty Ellipse")

        it = float(threat["in_track_m"])
        ct = float(threat["cross_track_m"])
        color = {
            "RED": "#f87171", "ORANGE": "#fb923c",
            "YELLOW": "#facc15", "GREEN": "#4ade80",
        }.get(risk, "#94a3b8")

        # Visual covariance (demo only)
        sigma_it = max(abs(it) * 0.15, 80) * cov_scale
        sigma_ct = max(abs(ct) * 0.15, 80) * cov_scale

        max_extent = max(abs(it), abs(ct), hbr_meters * 2, sigma_it * 2.2, sigma_ct * 2.2, 80)
        axis_lim = max_extent * 1.3

        fig = go.Figure()
        theta = np.linspace(0, 2 * np.pi, 120)

        for n_sig, opacity, dash in [(1, 0.18, "solid"), (2, 0.10, "dot")]:
            ex = it + n_sig * sigma_it * np.cos(theta)
            ey = ct + n_sig * sigma_ct * np.sin(theta)
            fig.add_trace(go.Scatter(
                x=ex, y=ey, mode="lines",
                fill="toself", fillcolor=f"rgba(56,189,248,{opacity})",
                line=dict(color="#38bdf8", width=1, dash=dash),
                name=f"{n_sig}σ uncertainty",
                hoverinfo="skip",
            ))

        fig.add_trace(go.Scatter(
            x=hbr_meters * np.cos(theta),
            y=hbr_meters * np.sin(theta),
            mode="lines", name=f"HBR ({hbr_meters} m)",
            line=dict(color="#ef4444", width=2, dash="dash"),
            fill="toself", fillcolor="rgba(239,68,68,0.15)",
        ))

        fig.add_trace(go.Scatter(
            x=[it], y=[ct], mode="markers+text",
            marker=dict(size=15, color=color, line=dict(width=2, color="white")),
            text=[str(threat["secondary_object"])[:22]],
            textposition="top center", name="Secondary",
            hovertemplate=(
                f"<b>{threat['secondary_object']}</b><br>"
                f"In-Track: {it:,.1f} m<br>Cross-Track: {ct:,.1f} m<br>"
                f"Miss: {threat['miss_distance_m']:,.1f} m"
            ),
        ))

        fig.add_trace(go.Scatter(
            x=[0], y=[0], mode="markers",
            marker=dict(size=13, color="#38bdf8", symbol="x", line=dict(width=2)),
            name="Primary / Collision Point",
        ))

        fig.add_trace(go.Scatter(
            x=[0, it], y=[0, ct], mode="lines",
            line=dict(color="#64748b", width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))

       
