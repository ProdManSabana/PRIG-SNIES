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

HEADER_ROW_HINTS = (
    "codigo",
    "institucion",
    "ies",
    "departamento",
    "municipio",
    "programa",
    "sector",
    "caracter",
    "ano",
    "semestre",
    "matriculados",
    "graduados",
    "inscritos",
    "admitidos",
    "docentes",
)

SKIP_SHEET_NAMES = {
    "indice",
    "index",
}

FILTER_DIMENSION_NAMES = {
    "institution_name",
    "sector",
    "academic_character",
    "department",
    "municipality",
    "domicile_department",
    "domicile_municipality",
    "program_department",
    "program_municipality",
    "programa_academico",
    "nivel_academico",
    "nivel_de_formacion",
    "modalidad",
    "sexo",
    "area_de_conocimiento",
    "nucleo_basico_del_conocimiento_nbc",
    "desc_cine_campo_amplio",
    "desc_cine_campo_especifico",
    "desc_cine_campo_detallado",
    "semester",
    "type_ies",
    "is_accredited",
    "institution_state",
}

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
    "codigo_de_la_institucion",
    "cod_ies",
    "ies",
)

IES_NAME_CANDIDATES = (
    "nombre_ies",
    "institucion",
    "institucion_de_educacion_superior_ies",
    "institucion_de_educacion_superior",
    "institucion_educacion_superior",
    "nombre_institucion",
)

DEPARTMENT_CANDIDATES = (
    "departamento",
    "departamento_domicilio",
    "departamento_de_domicilio_de_la_ies",
    "departamento_de_oferta_del_programa",
    "depto",
)

DEPARTMENT_CODE_CANDIDATES = (
    "codigo_del_departamento_ies",
    "codigo_del_departamento_programa",
    "codigo_departamento",
    "cod_departamento",
)

MUNICIPALITY_CANDIDATES = (
    "municipio",
    "municipio_domicilio",
    "municipio_de_domicilio_de_la_ies",
    "municipio_de_oferta_del_programa",
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


def dedupe_columns(columns: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    deduped: list[str] = []
    for index, column in enumerate(columns):
        base = column or f"unnamed_{index}"
        occurrence = counts.get(base, 0)
        deduped.append(base if occurrence == 0 else f"{base}_{occurrence}")
        counts[base] = occurrence + 1
    return deduped


def detect_header_row(frame: pd.DataFrame, max_scan_rows: int = 15) -> int:
    best_index = 0
    best_score = -1
    limit = min(len(frame.index), max_scan_rows)
    for row_index in range(limit):
        row = frame.iloc[row_index].tolist()
        values = [to_snake_case(value) for value in row if normalize_dimension_value(value)]
        if not values:
            continue
        hint_matches = sum(1 for value in values if any(hint in value for hint in HEADER_ROW_HINTS))
        score = (hint_matches * 10) + len(values)
        if score > best_score:
            best_score = score
            best_index = row_index
    return best_index


def promote_header_row(frame: pd.DataFrame) -> pd.DataFrame:
    header_row = detect_header_row(frame)
    header_values = []
    for index, value in enumerate(frame.iloc[header_row].tolist()):
        normalized = to_snake_case(value) if normalize_dimension_value(value) else f"unnamed_{index}"
        header_values.append(normalized)
    promoted = frame.iloc[header_row + 1 :].copy()
    promoted.columns = dedupe_columns(header_values)
    return clean_dataframe(promoted)


def detect_measure_column(frame: pd.DataFrame) -> str | None:
    candidate_columns = [
        column
        for column in frame.columns
        if not any(token in column for token in ("codigo", "cod_", "ano", "year", "vigencia"))
    ]
    hinted_columns = [column for column in candidate_columns if any(hint in column for hint in COUNT_COLUMN_HINTS)]
    for column in hinted_columns:
        if pd.to_numeric(frame[column], errors="coerce").notna().any():
            return column

    numeric_columns = [
        column
        for column in candidate_columns
        if pd.to_numeric(frame[column], errors="coerce").notna().any()
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

    workbook = pd.read_excel(path, sheet_name=None, header=None)
    return [(sheet_name, promote_header_row(frame)) for sheet_name, frame in workbook.items()]


def should_skip_sheet(sheet_name: str, frame: pd.DataFrame) -> bool:
    normalized_name = normalize_label(sheet_name)
    if normalized_name in SKIP_SHEET_NAMES:
        return True
    if frame.empty:
        return True
    if len(frame.columns) < 3:
        return True
    return False


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


def normalize_code(value: object) -> str | None:
    normalized = normalize_dimension_value(value)
    if normalized is None:
        return None

    text = normalized.strip()
    if not text:
        return None

    try:
        numeric = float(text)
    except ValueError:
        digits = re.sub(r"[^0-9]", "", text)
        return digits or None

    if pd.isna(numeric):
        return None

    if numeric.is_integer():
        return str(int(numeric))

    digits = re.sub(r"[^0-9]", "", text)
    return digits or None


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


def select_filter_dimensions(dimensions: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in dimensions.items() if key in FILTER_DIMENSION_NAMES}
