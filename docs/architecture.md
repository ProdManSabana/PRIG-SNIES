# PRIG SNIES Architecture

## Goal

Build a reproducible end-to-end platform that:

- discovers annual SNIES student and teacher consolidated files
- enriches those datasets with the HECAA IES registry
- filters the analytical layer to Bogotá, D.C. and years 2022-2024
- exposes a dashboard-ready API for student counts, teacher counts, and students-to-teachers ratios

## Data flow

1. `scheduler` runs the sync job on a fixed interval.
2. `SniesSource` discovers yearly assets directly from the SNIES catalog page by matching the official link titles.
3. `HecaaSource` captures the IES registry into the raw layer.
4. The pipeline stores downloaded assets in `data/landing/`.
5. Files are normalized into a schema-agnostic observation model:
   - `fact_observations`: one measure per row
   - `observation_dimensions`: flexible key/value dimensions discovered from the source columns
   - `field_metadata`: preserved workbook metadata rows for future label governance and schema mapping
6. The API queries DuckDB and exposes filtered aggregates to the dashboard.

## Why this model

SNIES schemas can vary between years, profiles, and workbook sheets. Instead of hardcoding a single wide schema, the platform converts each row into:

- one numeric measure (`measure_value`)
- canonical IES fields where they can be identified
- a flexible set of discovered dimensions for all remaining categorical fields

That keeps the system resilient when 2022, 2023, and 2024 files are not identical.

## Core tables

### `source_assets`

Catalog of discovered/downloaded files.

### `institution_dim`

IES master dimension sourced from HECAA and used to classify observations by sector, academic character, and domicile.

### `fact_observations`

Canonical fact table with year, profile, institution references, and numeric value.

### `observation_dimensions`

Tall dimension table used to drive arbitrary filtering in the dashboard.

### `field_metadata`

Raw metadata workbook content preserved in JSON form so future versions can translate technical column names into official business labels without re-downloading the source files.

## Services

### `api`

FastAPI service over DuckDB.

### `scheduler`

Background sync loop for recurring refreshes.

### `dashboard`

Streamlit analytics UI for filters, annual totals, granular grouping, and ratio monitoring.

## Deployment shape

`docker-compose.yaml` coordinates all services and mounts a shared `./data` volume so raw files and the warehouse survive restarts.
