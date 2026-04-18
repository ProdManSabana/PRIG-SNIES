import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


COUNT_COLUMN_HINTS = (
    "total",
    "cantidad",
    "conteo",
    "numero",
    "num_",
    "nro",
    "docentes",
    "estudiantes",
    "matriculados",
    "graduados",
    "inscritos",
    "admitidos",
)

DIMENSION_COLUMN_EXCLUSIONS = {
    "ano",
    "year",
    "vigencia",
    "perfil",
    "sheet_name",
    "source_file",
}

IES_CODE_CANDIDATES = (
    "codigo_ies",
    "codigo_institucion",
    "cod_ies",
    "ies",
)

IES_NAME_CANDIDATES = (
    "nombre_ies",
    "institucion",
    "institucion_educacion_superior",
    "nombre_institucion",
)

DEPARTMENT_CANDIDATES = (
    "departamento",
    "departamento_domicilio",
    "depto",
)

MUNICIPALITY_CANDIDATES = (
    "municipio",
    "municipio_domicilio",
)


def to_snake_case(value: str) -> str:
    normalized_text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", normalized_text.strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_")


def normalize_label(value: object) -> str:
    normalized_text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return normalized_text.strip().lower()


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned.columns = [to_snake_case(column) for column in cleaned.columns]
    cleaned = cleaned.dropna(axis=1, how="all").dropna(axis=0, how="all")
    return cleaned


def detect_measure_column(frame: pd.DataFrame) -> str | None:
    numeric_columns = list(frame.select_dtypes(include=["number"]).columns)
    numeric_columns = [
        column
        for column in numeric_columns
        if not any(token in column for token in ("codigo", "cod_", "ano", "year", "vigencia"))
    ]
    for column in numeric_columns:
        if any(hint in column for hint in COUNT_COLUMN_HINTS):
            return column
    return numeric_columns[-1] if numeric_columns else None


def select_first_existing(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def load_tabular_file(path: Path) -> list[tuple[str, pd.DataFrame]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path, sep=None, engine="python")
        return [("csv", clean_dataframe(frame))]

    workbook = pd.read_excel(path, sheet_name=None)
    return [(sheet_name, clean_dataframe(frame)) for sheet_name, frame in workbook.items()]


def build_observation_id(source_key: str, sheet_name: str, row_index: int) -> str:
    raw = f"{source_key}:{sheet_name}:{row_index}".encode("utf-8")
    return hashlib.md5(raw, usedforsecurity=False).hexdigest()


def normalize_dimension_value(value: object) -> str | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    text = str(value).strip()
    return text if text else None


def row_dimensions(row: dict, excluded_columns: set[str]) -> dict[str, str]:
    dimensions: dict[str, str] = {}
    for key, value in row.items():
        if key in excluded_columns:
            continue
        normalized = normalize_dimension_value(value)
        if normalized is None:
            continue
        dimensions[key] = normalized
    return dimensions


def append_json_dimensions(existing: dict[str, str], extra: dict[str, str | None]) -> dict[str, str]:
    merged = dict(existing)
    for key, value in extra.items():
        normalized = normalize_dimension_value(value)
        if normalized is not None:
            merged[key] = normalized
    return merged


def dimensions_to_json(dimensions: dict[str, str]) -> str:
    return json.dumps(dimensions, ensure_ascii=False, sort_keys=True)
