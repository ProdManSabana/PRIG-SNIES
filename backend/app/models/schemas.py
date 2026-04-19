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


class SyncStatusResponse(BaseModel):
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    message: str | None = None
    source_assets: int = 0
    downloaded_assets: int = 0
    institution_rows: int = 0
    observation_rows: int = 0
    dimension_rows: int = 0
    metadata_rows: int = 0
