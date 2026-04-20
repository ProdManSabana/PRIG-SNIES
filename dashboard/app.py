import os

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
DEFAULT_GROUP_BY = "sector"
HIDDEN_DIMENSIONS = {
    "domicile_department",
    "domicile_municipality",
}


@st.cache_data(ttl=300)
def fetch_json(path: str, params: dict | None = None) -> dict:
    response = httpx.get(f"{API_BASE_URL}{path}", params=params, timeout=60)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="PRIG SNIES Dashboard", layout="wide")
st.title("PRIG SNIES | Bogota IES analytics")
st.caption("Student flows, docentes totals, and student-to-teacher ratios for Bogota, D.C. (2022-2024).")

sync_status = fetch_json("/api/v1/sync-status")
filter_payload = fetch_json("/api/v1/filters")
dimension_options = filter_payload.get("dimensions", {})
group_by = DEFAULT_GROUP_BY if DEFAULT_GROUP_BY in dimension_options else None

with st.sidebar:
    st.header("Filters")

    available_years = filter_payload.get("years", [])
    available_profiles = filter_payload.get("profiles", [])
    st.session_state.setdefault("years_filter", list(available_years))
    st.session_state.setdefault("profiles_filter", list(available_profiles))

    years = st.multiselect("Years", options=available_years, key="years_filter")
    profiles = st.multiselect("Profiles", options=available_profiles, key="profiles_filter")

    selected_dimension_filters: dict[str, list[str]] = {}
    for dimension_name in sorted(dimension_options.keys()):
        if dimension_name in HIDDEN_DIMENSIONS:
            continue
        selected_values = st.multiselect(
            dimension_name.replace("_", " ").title(),
            options=dimension_options[dimension_name],
            key=f"dim_{dimension_name}",
        )
        if selected_values:
            selected_dimension_filters[dimension_name] = selected_values

params = {
    "years": years,
    "profiles": profiles,
    "dimension_filter": [
        f"{dimension_name}::{value}"
        for dimension_name, values in selected_dimension_filters.items()
        for value in values
    ],
}

summary_df = pd.DataFrame(fetch_json("/api/v1/summary", params=params).get("rows", []))
trend_df = pd.DataFrame(
    fetch_json("/api/v1/trend", params={**params, "group_by": group_by}).get("rows", [])
) if group_by else pd.DataFrame()

if summary_df.empty:
    if sync_status.get("status") == "running":
        st.info(
            "Sync is currently running. "
            f"Downloaded assets: {sync_status.get('downloaded_assets', 0)} / {sync_status.get('source_assets', 0)}."
        )
    elif sync_status.get("status") == "failed":
        st.error(f"Last sync failed: {sync_status.get('message', 'Unknown error')}")
    else:
        st.warning("No data has been loaded yet.")
    st.json(sync_status)
    st.stop()

student_profiles = {
    "inscritos",
    "admitidos",
    "matriculados",
    "matriculados_primer_curso",
    "graduados",
}

total_students = summary_df.loc[summary_df["profile"].isin(student_profiles), "total_value"].sum()
total_teachers = summary_df.loc[summary_df["profile"] == "docentes", "total_value"].sum()
ratio = (total_students / total_teachers) if total_teachers else None

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Total students", f"{int(total_students):,}")
metric_2.metric("Total teachers", f"{int(total_teachers):,}")
metric_3.metric("Students / teachers", f"{ratio:,.2f}" if ratio is not None else "N/A")

summary_chart = px.bar(
    summary_df,
    x="year",
    y="total_value",
    color="profile",
    barmode="group",
    title="Counts by year and profile",
)
st.plotly_chart(summary_chart, use_container_width=True)

ratio_df = trend_df[trend_df["profile"] == "students_to_teachers_ratio"].copy()
if not ratio_df.empty:
    ratio_chart = px.line(
        ratio_df,
        x="year",
        y="total_value",
        markers=True,
        title="Students-to-teachers ratio",
    )
    st.plotly_chart(ratio_chart, use_container_width=True)

trend_chart_df = trend_df[trend_df["profile"] != "students_to_teachers_ratio"].copy()
if not trend_chart_df.empty:
    trend_chart = px.bar(
        trend_chart_df,
        x="year",
        y="total_value",
        color="group_value",
        facet_row="profile",
        title=f"Granular trend by {group_by}",
    )
    st.plotly_chart(trend_chart, use_container_width=True)

st.subheader("Aggregated rows")
st.dataframe(summary_df, use_container_width=True)
