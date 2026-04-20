import os

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
DEFAULT_GROUP_BY = "sector"
HIDDEN_DIMENSIONS = {
    "domicile_department",
    "domicile_municipality",
}
MAX_PIE_COLUMNS = 3


def format_profile_label(profile_name: str) -> str:
    return profile_name.replace("_", " ").title()


@st.cache_data(ttl=300)
def build_pie_figure(
    labels: tuple[str, ...],
    values: tuple[float, ...],
    colors: tuple[str, ...],
    title: str,
    legend_title: str,
) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(labels),
                values=list(values),
                marker={"colors": list(colors)},
                sort=False,
                textinfo="percent+value",
                texttemplate="%{value:,}<br>(%{percent})",
                hovertemplate=(
                    f"{legend_title}: %{{label}}<br>"
                    "Value: %{value:,}<br>"
                    "Share: %{percent}<extra></extra>"
                ),
            )
        ]
    )
    fig.update_layout(
        title_text=title,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        legend_title_text=legend_title,
    )
    return fig


def render_yearly_pie_charts(
    chart_df: pd.DataFrame,
    title_dimension: str,
) -> None:
    st.subheader(f"Granular trend by {title_dimension}")

    profile_names = sorted(chart_df["profile"].unique())
    group_values = sorted(chart_df["group_value"].astype(str).unique())
    palette = px.colors.qualitative.Plotly
    color_map = {
        group_value: palette[index % len(palette)]
        for index, group_value in enumerate(group_values)
    }
    legend_title = title_dimension.replace("_", " ").title()

    def show_profile_charts(profile_df: pd.DataFrame, profile_key: str) -> None:
        years_for_profile = sorted(profile_df["year"].unique())
        for start in range(0, len(years_for_profile), MAX_PIE_COLUMNS):
            year_slice = years_for_profile[start : start + MAX_PIE_COLUMNS]
            columns = st.columns(len(year_slice))
            for column, year_value in zip(columns, year_slice):
                year_df = (
                    profile_df[profile_df["year"] == year_value]
                    .sort_values("total_value", ascending=False)
                    .copy()
                )
                if year_df.empty:
                    column.info(f"No data for {year_value}.")
                    continue

                labels = tuple(year_df["group_value"].astype(str))
                values = tuple(float(value) for value in year_df["total_value"])
                colors = tuple(color_map[label] for label in labels)
                pie_chart = build_pie_figure(
                    labels=labels,
                    values=values,
                    colors=colors,
                    title=str(year_value),
                    legend_title=legend_title,
                )
                column.plotly_chart(
                    pie_chart,
                    use_container_width=True,
                    key=f"pie_{profile_key}_{year_value}",
                )

    if len(profile_names) == 1:
        show_profile_charts(chart_df, profile_names[0])
        return

    if st.session_state.get("active_profile_tab") not in profile_names:
        st.session_state["active_profile_tab"] = profile_names[0]

    active_profile = st.radio(
        "Profile",
        options=profile_names,
        format_func=format_profile_label,
        horizontal=True,
        key="active_profile_tab",
    )
    show_profile_charts(
        chart_df[chart_df["profile"] == active_profile].copy(),
        active_profile,
    )


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
    render_yearly_pie_charts(trend_chart_df, group_by)

st.subheader("Aggregated rows")
st.dataframe(summary_df, use_container_width=True)
