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
DEFAULT_FILE = "./kivulu_GIS Ready.xlsx"

if not os.path.exists(DEFAULT_FILE):
    st.error(f"❌ File not found: {DEFAULT_FILE}")
    st.stop()

try:
    df = pd.read_excel(DEFAULT_FILE, engine="openpyxl")
except Exception as e:
    st.error(f"❌ Failed to read Excel file: {e}")
    st.info("Make sure 'openpyxl' is included in requirements.txt.")
    st.stop()

# ── CLEAN DATA ────────────────────────────────────────
df.columns = df.columns.str.strip().str.lower()

for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].astype(str).str.strip().str.lower()

df = df.fillna("unknown")

expected_cols = [
    "respondent_age",
    "hh_size",
    "illness_episodes_3m",
    "medical_cost_burden",
    "travel_time",
    "join_low_cost",
    "main_illness",
    "income_stability",
    "transport_mode",
    "chronic_illness"
]

for col in expected_cols:
    if col not in df.columns:
        df[col] = "unknown"

# Convert numeric safely
df["respondent_age"] = pd.to_numeric(df["respondent_age"], errors="coerce")
df["hh_size"] = pd.to_numeric(df["hh_size"], errors="coerce")
df["illness_episodes_3m"] = pd.to_numeric(df["illness_episodes_3m"], errors="coerce")

# ── DERIVED COLUMNS ───────────────────────────────────
df["vulnerability"] = df["medical_cost_burden"].map({
    "very_difficult": "High",
    "difficult": "Medium",
    "manageable": "Low"
}).fillna("Unknown")

df["access_level"] = df["travel_time"].apply(
    lambda x: "High Access" if str(x) == "lt15" else "Low Access"
)

df["ins_priority"] = df["join_low_cost"].map({
    "yes": "High",
    "not_sure": "Medium",
    "no": "Low"
}).fillna("Unknown")

# ── HELPER FUNCTIONS ──────────────────────────────────
def make_counts(dataframe, col):
    if col not in dataframe.columns or dataframe.empty:
        return pd.DataFrame({col: [], "count": []})
    d = dataframe[col].fillna("unknown").value_counts().reset_index()
    d.columns = [col, "count"]
    return d

def safe_pie(dataframe, names_col, title):
    if names_col not in dataframe.columns or dataframe.empty:
        data = pd.DataFrame({names_col: ["No data"], "count": [1]})
        return px.pie(data, names=names_col, values="count", title=title)

    counts = make_counts(dataframe, names_col)
    if counts.empty:
        counts = pd.DataFrame({names_col: ["No data"], "count": [1]})

    return px.pie(counts, names=names_col, values="count", title=title)

def safe_bar(dataframe, x_col, title):
    counts = make_counts(dataframe, x_col)
    if counts.empty:
        counts = pd.DataFrame({x_col: ["No data"], "count": [0]})

    return px.bar(
        counts,
        x=x_col,
        y="count",
        title=title,
        color=x_col
    )

# ── HEADER ────────────────────────────────────────────
st.title("🏥 Kivulu Health & Vulnerability Dashboard")
st.caption("Interactive GIS Household Survey")

# ── KPI CARDS ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric("Households", len(df))
col2.metric("High Vulnerability", f"{(df['vulnerability'] == 'High').mean() * 100:.1f}%")
col3.metric("Low Access", f"{(df['access_level'] == 'Low Access').mean() * 100:.1f}%")
col4.metric("Insurance Demand", f"{(df['ins_priority'] == 'High').mean() * 100:.1f}%")

st.markdown("---")

# ── FILTERS ───────────────────────────────────────────
f1, f2 = st.columns(2)

illness_options = ["All"] + sorted(df["main_illness"].dropna().astype(str).unique().tolist())
income_options = ["All"] + sorted(df["income_stability"].dropna().astype(str).unique().tolist())

selected_illness = f1.selectbox("Filter by Illness", illness_options)
selected_income = f2.selectbox("Filter by Income Stability", income_options)

filtered_df = df.copy()

if selected_illness != "All":
    filtered_df = filtered_df[filtered_df["main_illness"] == selected_illness.lower()]

if selected_income != "All":
    filtered_df = filtered_df[filtered_df["income_stability"] == selected_income.lower()]

if filtered_df.empty:
    st.warning("No records match the selected filters.")

# ── ROW 1: PIE CHARTS ─────────────────────────────────
c1, c2, c3 = st.columns(3)

fig1 = safe_pie(filtered_df, "vulnerability", "Vulnerability")
c1.plotly_chart(fig1, use_container_width=True, theme=None)

fig2 = safe_pie(filtered_df, "access_level", "Health Access")
c2.plotly_chart(fig2, use_container_width=True, theme=None)

fig3 = safe_pie(filtered_df, "ins_priority", "Insurance Priority")
c3.plotly_chart(fig3, use_container_width=True, theme=None)

# ── ROW 2: BAR CHARTS ─────────────────────────────────
c4, c5 = st.columns(2)

fig4 = safe_bar(filtered_df, "main_illness", "Main Illness")
fig4.update_xaxes(tickangle=-30, nticks=6)
c4.plotly_chart(fig4, use_container_width=True, theme=None)

fig5 = safe_bar(filtered_df, "income_stability", "Income Stability")
fig5.update_xaxes(tickangle=-20, nticks=6)
c5.plotly_chart(fig5, use_container_width=True, theme=None)

# ── ROW 3: DIFFERENT NUMERIC CHARTS ───────────────────
c6, c7 = st.columns(2)

age_df = filtered_df.dropna(subset=["respondent_age"])
hh_df = filtered_df.dropna(subset=["hh_size"])

# Respondent Age → Box Plot
if age_df.empty:
    fig6 = px.box(
        pd.DataFrame({"respondent_age": []}),
        y="respondent_age",
        title="Respondent Age (No data)"
    )
else:
    fig6 = px.box(
        age_df,
        y="respondent_age",
        points="outliers",
        title="Respondent Age Distribution"
    )

fig6.update_yaxes(title_text="Respondent Age (years)", nticks=8)
fig6.update_xaxes(showticklabels=False)
c6.plotly_chart(fig6, use_container_width=True, theme=None)

# Household Size → Violin Plot
if hh_df.empty:
    fig7 = px.violin(
        pd.DataFrame({"hh_size": []}),
        y="hh_size",
        title="Household Size (No data)"
    )
else:
    fig7 = px.violin(
        hh_df,
        y="hh_size",
        box=True,
        points="all",
        title="Household Size Distribution"
    )

fig7.update_yaxes(title_text="Household Size", nticks=8)
fig7.update_xaxes(showticklabels=False)
c7.plotly_chart(fig7, use_container_width=True, theme=None)

# ── ROW 4: MORE INSIGHTS ──────────────────────────────
c8, c9 = st.columns(2)

fig8 = safe_bar(filtered_df, "transport_mode", "Transport to Facility")
fig8.update_xaxes(tickangle=-25, nticks=6)
c8.plotly_chart(fig8, use_container_width=True, theme=None)

chronic_counts = make_counts(filtered_df, "chronic_illness")
if chronic_counts.empty:
    chronic_counts = pd.DataFrame({"chronic_illness": ["No data"], "count": [1]})

fig9 = px.pie(
    chronic_counts,
    names="chronic_illness",
    values="count",
    title="Chronic Illness"
)
c9.plotly_chart(fig9, use_container_width=True, theme=None)

# ── DATA TABLE ────────────────────────────────────────
st.markdown("### 📋 Filtered Data")
st.dataframe(filtered_df, use_container_width=True)
