from typing import Annotated

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    snies_base_url: str = "https://snies.mineducacion.gov.co/portal/ESTADISTICAS/Bases-consolidadas/"
    hecaa_ies_url: str = "https://hecaa.mineducacion.gov.co/consultaspublicas/ies"
    target_department: str = "Bogotá, D.C."
    target_department_code: str = "11"
    target_years: Annotated[list[int], NoDecode] = Field(default_factory=lambda: [2022, 2023, 2024])
    sync_interval_hours: int = 24
    warehouse_path: Path = Path("/app/data/warehouse/snies.duckdb")
    landing_dir: Path = Path("/app/data/landing")
    raw_dir: Path = Path("/app/data/raw")
    processed_dir: Path = Path("/app/data/processed")
    api_port: int = 8000
    streamlit_port: int = 8501

    @field_validator("target_years", mode="before")
    @classmethod
    def parse_target_years(cls, value):
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for path in (settings.landing_dir, settings.raw_dir, settings.processed_dir, settings.warehouse_path.parent):
        path.mkdir(parents=True, exist_ok=True)
    return settings
