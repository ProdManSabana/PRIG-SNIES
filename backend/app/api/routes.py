from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.settings import Settings, get_settings
from app.db.warehouse import Warehouse
from app.models.domain import STUDENT_PROFILES
from app.models.schemas import FilterOptions, HealthResponse, SummaryResponse, TrendResponse


router = APIRouter()


def get_warehouse(settings: Annotated[Settings, Depends(get_settings)]) -> Warehouse:
    warehouse = Warehouse(settings)
    warehouse.initialize()
    return warehouse


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/api/v1/filters", response_model=FilterOptions)
def filters(warehouse: Annotated[Warehouse, Depends(get_warehouse)]) -> FilterOptions:
    years = warehouse.query_df("select distinct year from fact_observations order by year").iloc[:, 0].dropna().astype(int).tolist()
    profiles = warehouse.query_df("select distinct profile from fact_observations order by profile").iloc[:, 0].dropna().astype(str).tolist()
    dims = warehouse.query_df(
        """
        select dimension_name, dimension_value
        from observation_dimensions
        where dimension_value is not null
        order by dimension_name, dimension_value
        """
    )
    dimension_options: dict[str, list[str]] = {}
    for dimension_name, group in dims.groupby("dimension_name"):
        dimension_options[str(dimension_name)] = group["dimension_value"].dropna().astype(str).unique().tolist()
    return FilterOptions(years=years, profiles=profiles, dimensions=dimension_options)


def build_filter_clause(years: list[int], profiles: list[str], dimension_filters: dict[str, list[str]]) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []

    if years:
        placeholders = ", ".join(["?"] * len(years))
        clauses.append(f"f.year in ({placeholders})")
        params.extend(years)

    if profiles:
        placeholders = ", ".join(["?"] * len(profiles))
        clauses.append(f"f.profile in ({placeholders})")
        params.extend(profiles)

    for dimension_name, values in dimension_filters.items():
        if not values:
            continue
        placeholders = ", ".join(["?"] * len(values))
        clauses.append(
            f"""
            exists (
                select 1
                from observation_dimensions d
                where d.observation_id = f.observation_id
                  and d.dimension_name = ?
                  and d.dimension_value in ({placeholders})
            )
            """
        )
        params.append(dimension_name)
        params.extend(values)

    if not clauses:
        return "1 = 1", params
    return " and ".join(clauses), params


def parse_dimension_filters(dimension_filter: list[str] | None) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for item in dimension_filter or []:
        if "::" not in item:
            continue
        name, value = item.split("::", 1)
        name = name.strip()
        value = value.strip()
        if not name or not value:
            continue
        parsed.setdefault(name, []).append(value)
    return parsed


@router.get("/api/v1/summary", response_model=SummaryResponse)
def summary(
    years: Annotated[list[int] | None, Query()] = None,
    profiles: Annotated[list[str] | None, Query()] = None,
    dimension_filter: Annotated[list[str] | None, Query()] = None,
    warehouse: Warehouse = Depends(get_warehouse),
) -> SummaryResponse:
    dimension_filters = parse_dimension_filters(dimension_filter)
    where_clause, params = build_filter_clause(years or [], profiles or [], dimension_filters)
    frame = warehouse.query_df(
        f"""
        select
            f.year,
            f.profile,
            sum(f.measure_value) as total_value
        from fact_observations f
        where {where_clause}
        group by 1, 2
        order by 1, 2
        """,
        params,
    )
    return SummaryResponse(rows=frame.fillna("").to_dict(orient="records"))


@router.get("/api/v1/trend", response_model=TrendResponse)
def trend(
    group_by: str = "institution_name",
    years: Annotated[list[int] | None, Query()] = None,
    profiles: Annotated[list[str] | None, Query()] = None,
    dimension_filter: Annotated[list[str] | None, Query()] = None,
    warehouse: Warehouse = Depends(get_warehouse),
) -> TrendResponse:
    dimension_filters = parse_dimension_filters(dimension_filter)
    where_clause, params = build_filter_clause(years or [], profiles or [], dimension_filters)
    frame = warehouse.query_df(
        f"""
        select
            f.year,
            f.profile,
            gd.dimension_value as group_value,
            sum(f.measure_value) as total_value
        from fact_observations f
        left join observation_dimensions gd
          on gd.observation_id = f.observation_id
         and gd.dimension_name = ?
        where {where_clause}
        group by 1, 2, 3
        order by 1, 2, 3
        """,
        [group_by, *params],
    )

    student_frame = warehouse.query_df(
        f"""
        select
            f.year,
            sum(case when f.profile in ({", ".join(["?"] * len(STUDENT_PROFILES))}) then f.measure_value else 0 end) as students,
            sum(case when f.profile = 'docentes' then f.measure_value else 0 end) as teachers
        from fact_observations f
        where {where_clause}
        group by 1
        order by 1
        """,
        [*sorted(profile.value for profile in STUDENT_PROFILES), *params],
    )

    ratio_rows = []
    for record in student_frame.to_dict(orient="records"):
        teachers = float(record["teachers"] or 0)
        students = float(record["students"] or 0)
        ratio_rows.append(
            {
                "year": int(record["year"]),
                "profile": "students_to_teachers_ratio",
                "group_value": "Bogotá, D.C.",
                "total_value": (students / teachers) if teachers else None,
            }
        )

    merged = frame.fillna("").to_dict(orient="records") + ratio_rows
    return TrendResponse(rows=merged)
