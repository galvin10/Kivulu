import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ── PAGE CONFIG ───────────────────────────────────────
st.set_page_config(
    page_title="Kivulu Dashboard",
    layout="wide",
    page_icon="📊"
)

# ── LOAD DATA ─────────────────────────────────────────
DEFAULT_FILE = r"./kivulu_GIS Ready.xlsx"

if not os.path.exists(DEFAULT_FILE):
    st.error(f"❌ File not found: {DEFAULT_FILE}")
    st.stop()

df = pd.read_excel(DEFAULT_FILE)

# Clean columns
df.columns = df.columns.str.strip().str.lower()
df = df.fillna("unknown")

# Convert numeric safely
df["respondent_age"] = pd.to_numeric(df.get("respondent_age"), errors="coerce")
df["hh_size"] = pd.to_numeric(df.get("hh_size"), errors="coerce")
df["illness_episodes_3m"] = pd.to_numeric(df.get("illness_episodes_3m"), errors="coerce")

# ── DERIVED COLUMNS ───────────────────────────────────
df["vulnerability"] = df.get("medical_cost_burden", "").map({
    "very_difficult": "High",
    "difficult": "Medium",
    "manageable": "Low"
})

df["access_level"] = df.get("travel_time", "").apply(
    lambda x: "High Access" if str(x) == "lt15" else "Low Access"
)

df["ins_priority"] = df.get("join_low_cost", "").map({
    "yes": "High",
    "not_sure": "Medium",
    "no": "Low"
})

# ── HELPER FUNCTION (fixes ALL value_counts bugs) ─────
def make_counts(df, col):
    if col not in df.columns:
        return pd.DataFrame({col: [], "count": []})
    d = df[col].value_counts().reset_index()
    d.columns = [col, "count"]
    return d

# ── HEADER ────────────────────────────────────────────
st.title("🏥 Kivulu Health & Vulnerability Dashboard")
st.caption("Interactive GIS Household Survey")

# ── KPI CARDS ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric("Households", len(df))

col2.metric(
    "High Vulnerability",
    f"{(df['vulnerability'] == 'High').mean() * 100:.1f}%"
)

col3.metric(
    "Low Access",
    f"{(df['access_level'] == 'Low Access').mean() * 100:.1f}%"
)

col4.metric(
    "Insurance Demand",
    f"{(df['ins_priority'] == 'High').mean() * 100:.1f}%"
)

st.markdown("---")

# ── FILTERS ───────────────────────────────────────────
f1, f2 = st.columns(2)

illness_options = ["All"] + sorted(df["main_illness"].dropna().unique().tolist()) if "main_illness" in df else ["All"]
income_options = ["All"] + sorted(df["income_stability"].dropna().unique().tolist()) if "income_stability" in df else ["All"]

selected_illness = f1.selectbox("Filter by Illness", illness_options)
selected_income = f2.selectbox("Filter by Income Stability", income_options)

filtered_df = df.copy()

if selected_illness != "All":
    filtered_df = filtered_df[filtered_df["main_illness"] == selected_illness]

if selected_income != "All":
    filtered_df = filtered_df[filtered_df["income_stability"] == selected_income]

# ── ROW 1: PIE CHARTS ─────────────────────────────────
c1, c2, c3 = st.columns(3)

fig1 = px.pie(filtered_df, names="vulnerability", title="Vulnerability")
c1.plotly_chart(fig1, use_container_width=True)

fig2 = px.pie(filtered_df, names="access_level", title="Health Access")
c2.plotly_chart(fig2, use_container_width=True)

fig3 = px.pie(filtered_df, names="ins_priority", title="Insurance Priority")
c3.plotly_chart(fig3, use_container_width=True)

# ── ROW 2: BAR CHARTS ─────────────────────────────────
c4, c5 = st.columns(2)

illness_counts = make_counts(filtered_df, "main_illness")

fig4 = px.bar(
    illness_counts,
    x="main_illness",
    y="count",
    title="Main Illness",
    color="main_illness"
)
c4.plotly_chart(fig4, use_container_width=True)

income_counts = make_counts(filtered_df, "income_stability")

fig5 = px.bar(
    income_counts,
    x="income_stability",
    y="count",
    title="Income Stability",
    color="income_stability"
)
c5.plotly_chart(fig5, use_container_width=True)

# ── ROW 3: HISTOGRAMS ─────────────────────────────────
c6, c7 = st.columns(2)

fig6 = px.histogram(
    filtered_df,
    x="respondent_age",
    nbins=10,
    title="Age Distribution"
)
c6.plotly_chart(fig6, use_container_width=True)

fig7 = px.histogram(
    filtered_df,
    x="hh_size",
    nbins=10,
    title="Household Size"
)
c7.plotly_chart(fig7, use_container_width=True)

# ── ROW 4: MORE INSIGHTS ──────────────────────────────
c8, c9 = st.columns(2)

transport_counts = make_counts(filtered_df, "transport_mode")

fig8 = px.bar(
    transport_counts,
    x="transport_mode",
    y="count",
    title="Transport to Facility",
    color="transport_mode"
)
c8.plotly_chart(fig8, use_container_width=True)

chronic_counts = make_counts(filtered_df, "chronic_illness")

fig9 = px.pie(
    chronic_counts,
    names="chronic_illness",
    values="count",
    title="Chronic Illness"
)
c9.plotly_chart(fig9, use_container_width=True)

# ── DATA TABLE ────────────────────────────────────────
st.markdown("### 📋 Filtered Data")
st.dataframe(filtered_df, use_container_width=True)
