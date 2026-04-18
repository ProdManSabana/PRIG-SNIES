from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class FilterOptions(BaseModel):
    years: list[int]
    profiles: list[str]
    dimensions: dict[str, list[str]]


class SummaryResponse(BaseModel):
    rows: list[dict]


class TrendResponse(BaseModel):
    rows: list[dict]

