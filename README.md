# PRIG SNIES

Dockerized data platform for Bogotá, D.C. higher-education analytics across SNIES consolidated bases and the HECAA IES registry.

## What is included

- a resilient ingestion layer for SNIES yearly student/teacher files and HECAA institution data
- preserved yearly metadata workbooks for later schema labeling and governance
- a normalization pipeline that preserves arbitrary source dimensions
- a DuckDB analytical warehouse
- a FastAPI service for filtered aggregates
- a Streamlit dashboard for counts and students-to-teachers ratios

## Project layout

- `backend/`: ingestion, normalization, warehouse, API
- `dashboard/`: Streamlit dashboard
- `data/`: persisted landing, raw, processed, and warehouse layers
- `docs/architecture.md`: architecture decisions

## Quick start

1. Review `.env` if you want to change years, department, ports, or sync cadence.
2. Start the platform:

```bash
docker compose up --build
```

3. Open the dashboard on port `8501` and the API on port `8000`.

## Notes

- The pipeline is configured for `Bogotá, D.C.` and target years `2022, 2023, 2024`.
- The current normalization is intentionally schema-tolerant because SNIES file layouts can differ by profile and year.
- If the live portals change their HTML structure or download mechanics, the source adapters in `backend/app/sources/` are the place to update.
