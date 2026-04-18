from pathlib import Path

import pandas as pd

from app.core.settings import get_settings
from app.db.warehouse import Warehouse
from app.services.http import HttpClient
from app.services.normalization import (
    DEPARTMENT_CANDIDATES,
    DIMENSION_COLUMN_EXCLUSIONS,
    IES_CODE_CANDIDATES,
    IES_NAME_CANDIDATES,
    MUNICIPALITY_CANDIDATES,
    append_json_dimensions,
    build_observation_id,
    detect_measure_column,
    dimensions_to_json,
    load_tabular_file,
    normalize_label,
    normalize_dimension_value,
    row_dimensions,
    select_first_existing,
    to_snake_case,
)
from app.sources.hecaa import HecaaSource
from app.sources.snies import SniesSource


def normalize_institutions(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    renamed = {column: to_snake_case(column) for column in frame.columns}
    frame = frame.rename(columns=renamed)
    mapping = {
        "codigo_ies": "institution_code",
        "nombre_ies": "institution_name",
        "ies_padre": "institution_parent_code",
        "sector": "sector",
        "caracter_academico": "academic_character",
        "departamento_municipio": "domicile_location",
        "estado_ies": "institution_state",
        "programas_vigentes": "programs_current",
        "programas_en_convenio": "programs_agreement",
        "acreditada": "is_accredited",
    }
    frame = frame.rename(columns={key: value for key, value in mapping.items() if key in frame.columns})
    if "domicile_location" in frame.columns:
        location_parts = frame["domicile_location"].astype(str).str.split("/", n=1, expand=True)
        frame["domicile_department"] = location_parts[0].str.strip()
        frame["domicile_municipality"] = location_parts[1].str.strip() if location_parts.shape[1] > 1 else None
    expected_columns = [
        "institution_code",
        "institution_name",
        "institution_parent_code",
        "sector",
        "academic_character",
        "domicile_department",
        "domicile_municipality",
        "institution_state",
        "programs_current",
        "programs_agreement",
        "is_accredited",
    ]
    for column in expected_columns:
        if column not in frame.columns:
            frame[column] = None
    frame["record_source"] = "hecaa"
    return frame[expected_columns + ["record_source"]].drop_duplicates()


def build_observation_frames(snies_assets, institution_dim: pd.DataFrame, target_department: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    observations: list[dict] = []
    dimensions: list[dict] = []

    institution_lookup = institution_dim.copy()
    if "institution_code" in institution_lookup.columns:
        institution_lookup["institution_code"] = institution_lookup["institution_code"].astype(str)

    for asset in snies_assets:
        if not asset.local_path or not asset.local_path.exists() or asset.profile == "metadatos":
            continue
        for sheet_name, frame in load_tabular_file(asset.local_path):
            if frame.empty:
                continue
            measure_column = detect_measure_column(frame)
            columns = list(frame.columns)
            institution_code_column = select_first_existing(columns, IES_CODE_CANDIDATES)
            institution_name_column = select_first_existing(columns, IES_NAME_CANDIDATES)
            department_column = select_first_existing(columns, DEPARTMENT_CANDIDATES)
            municipality_column = select_first_existing(columns, MUNICIPALITY_CANDIDATES)

            for row_index, row in frame.iterrows():
                source_key = asset.local_path.as_posix()
                observation_id = build_observation_id(source_key, sheet_name, int(row_index))
                row_dict = row.to_dict()
                institution_code = row_dict.get(institution_code_column) if institution_code_column else None
                institution_name = row_dict.get(institution_name_column) if institution_name_column else None
                department = row_dict.get(department_column) if department_column else None
                municipality = row_dict.get(municipality_column) if municipality_column else None

                measure_value = row_dict.get(measure_column) if measure_column else 1
                if pd.isna(measure_value):
                    measure_value = 1
                measure_value = pd.to_numeric(pd.Series([measure_value]), errors="coerce").fillna(1).iloc[0]

                excluded = set(DIMENSION_COLUMN_EXCLUSIONS)
                excluded.update(filter(None, [measure_column, institution_code_column, institution_name_column, department_column, municipality_column]))
                row_dims = row_dimensions(row_dict, excluded)

                institution_match = None
                if institution_code is not None and "institution_code" in institution_lookup.columns:
                    matches = institution_lookup[institution_lookup["institution_code"] == str(institution_code)]
                    if not matches.empty:
                        institution_match = matches.iloc[0].to_dict()

                canonical_dims = {
                    "institution_name": institution_name or (institution_match or {}).get("institution_name"),
                    "sector": (institution_match or {}).get("sector"),
                    "academic_character": (institution_match or {}).get("academic_character"),
                    "domicile_department": (institution_match or {}).get("domicile_department"),
                    "domicile_municipality": (institution_match or {}).get("domicile_municipality"),
                    "institution_state": (institution_match or {}).get("institution_state"),
                }
                combined_dims = append_json_dimensions(row_dims, canonical_dims)

                effective_department = str(
                    department
                    or combined_dims.get("departamento")
                    or combined_dims.get("domicile_department")
                    or ""
                ).strip()

                if effective_department and normalize_label(effective_department) != normalize_label(target_department):
                    continue

                observations.append(
                    {
                        "observation_id": observation_id,
                        "source": asset.source,
                        "year": asset.year,
                        "profile": asset.profile,
                        "source_file": str(asset.local_path),
                        "source_sheet": sheet_name,
                        "institution_code": str(institution_code) if institution_code is not None else None,
                        "institution_name": normalize_name(institution_name or canonical_dims.get("institution_name")),
                        "department": department or canonical_dims.get("domicile_department"),
                        "municipality": municipality or canonical_dims.get("domicile_municipality"),
                        "measure_value": float(measure_value),
                        "dimensions_json": dimensions_to_json(combined_dims),
                    }
                )

                for dimension_name, dimension_value in combined_dims.items():
                    dimensions.append(
                        {
                            "observation_id": observation_id,
                            "dimension_name": dimension_name,
                            "dimension_value": dimension_value,
                        }
                    )

    observation_frame = pd.DataFrame(observations)
    dimension_frame = pd.DataFrame(dimensions)
    return observation_frame, dimension_frame


def extract_field_metadata(snies_assets) -> pd.DataFrame:
    rows: list[dict] = []
    for asset in snies_assets:
        if asset.profile != "metadatos" or not asset.local_path or not asset.local_path.exists():
            continue
        for sheet_name, frame in load_tabular_file(asset.local_path):
            if frame.empty:
                continue
            for row_index, row in frame.iterrows():
                payload = {
                    key: value
                    for key, value in {
                        column: normalize_dimension_value(value)
                        for column, value in row.to_dict().items()
                    }.items()
                    if value is not None
                }
                rows.append(
                    {
                        "year": asset.year,
                        "source_file": str(asset.local_path),
                        "sheet_name": sheet_name,
                        "row_index": int(row_index),
                        "metadata_json": dimensions_to_json(payload),
                    }
                )
    return pd.DataFrame(rows)


def normalize_name(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def run_sync() -> None:
    settings = get_settings()
    warehouse = Warehouse(settings)
    warehouse.initialize()
    client = HttpClient()

    snies_source = SniesSource(settings, client)
    hecaa_source = HecaaSource(settings, client)

    discovered_assets = snies_source.discover_assets()
    downloaded_assets = snies_source.download_assets(discovered_assets)

    source_asset_rows = [
        {
            "source": asset.source,
            "year": asset.year,
            "profile": asset.profile,
            "title": asset.title,
            "url": asset.url,
            "local_path": str(asset.local_path) if asset.local_path else None,
            "status": "downloaded" if asset.local_path else "discovered",
        }
        for asset in downloaded_assets
    ]
    warehouse.replace_table("source_assets", pd.DataFrame(source_asset_rows))

    institutions_path = hecaa_source.fetch_institutions()
    institution_dim = normalize_institutions(institutions_path)
    warehouse.replace_table("institution_dim", institution_dim)

    observations, dimensions = build_observation_frames(downloaded_assets, institution_dim, settings.target_department)
    if observations.empty:
        observations = pd.DataFrame(
            columns=[
                "observation_id",
                "source",
                "year",
                "profile",
                "source_file",
                "source_sheet",
                "institution_code",
                "institution_name",
                "department",
                "municipality",
                "measure_value",
                "dimensions_json",
            ]
        )
    if dimensions.empty:
        dimensions = pd.DataFrame(columns=["observation_id", "dimension_name", "dimension_value"])

    warehouse.replace_table("fact_observations", observations)
    warehouse.replace_table("observation_dimensions", dimensions)
    field_metadata = extract_field_metadata(downloaded_assets)
    if field_metadata.empty:
        field_metadata = pd.DataFrame(columns=["year", "source_file", "sheet_name", "row_index", "metadata_json"])
    warehouse.replace_table("field_metadata", field_metadata)


if __name__ == "__main__":
    run_sync()
