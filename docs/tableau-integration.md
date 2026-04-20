# Connecting Tableau to the PRIG SNIES API

This guide explains how Tableau can consume PRIG SNIES through the FastAPI layer instead of opening the DuckDB file directly.

The shipped Tableau Web Data Connector (WDC) now lives in `backend/app/api/static/tableau_wdc.html` and is served by FastAPI at:

`http://localhost:8000/static/tableau_wdc.html`

If you need row-level facts, the current API is still too aggregated for full self-service analysis. In that case, see the production-readiness notes below or use direct DuckDB ODBC instead.

## 1. Options at a glance

| Option | What Tableau sees | Good for | Extra work |
|---|---|---|---|
| **A. Web Data Connector (WDC)** | A live REST/JSON endpoint wrapped as a connector | Pre-aggregated summaries, the same slices the dashboard shows, dimension-filtered pulls | Already shipped in this repo |
| **B. Scheduled Hyper extract** | A `.hyper` file republished to Tableau Server/Cloud | Large result sets, scheduled refresh, offline analysis | A Python job that pulls from the API and writes `.hyper` |
| **C. OData endpoint** (future) | A native OData v4 feed | Zero-code connection from Tableau / Power BI / Excel | Add an OData adapter to the FastAPI app |
| **D. Direct DuckDB ODBC** (bypass) | Tableau connects to the `.duckdb` file | Ad-hoc analysis with full fact-row detail | Not via the API; file access required |

## 2. API surface currently available

| Endpoint | Query params | Row shape |
|---|---|---|
| `GET /api/v1/sync-status` | none | singleton status record |
| `GET /api/v1/filters` | none | `{years: int[], profiles: string[], dimensions: {name: string[]}}` |
| `GET /api/v1/summary` | `years[]`, `profiles[]`, `dimension_filter[]` | `[{year, profile, total_value}]` |
| `GET /api/v1/trend` | `group_by`, `years[]`, `profiles[]`, `dimension_filter[]` | `[{year, profile, group_value, total_value}]` |

Example requests:

```text
GET /api/v1/summary?years=2024&profiles=docentes
GET /api/v1/trend?group_by=sector&years=2024
```

List-type query params are sent as repeated keys:

```text
?years=2022&years=2023&profiles=docentes
```

The `dimension_filter` format is:

```text
dimension_name::value
```

Example:

```text
?dimension_filter=nivel_academico::Pregrado&dimension_filter=sexo::Femenino
```

## 3. Option A - Web Data Connector (WDC)

### 3.1 What is shipped

The repo already includes a working connector page at:

- File: `backend/app/api/static/tableau_wdc.html`
- Served URL: `http://localhost:8000/static/tableau_wdc.html`

The FastAPI app mounts that directory in `backend/app/api/app.py`, so the connector is served from the same origin as the API.

### 3.2 What the connector exposes

The WDC creates two Tableau tables:

- `snies_summary` from `/api/v1/summary`
- `snies_trend` from `/api/v1/trend`

The connector UI lets the user provide:

- API base URL
- `group_by` for the trend table
- years
- profiles
- repeated `dimension_filter` values in `dimension_name::value` format

### 3.3 Using it from Tableau Desktop

1. Start the PRIG SNIES stack.
2. Open Tableau Desktop.
3. Go to `Connect > To a Server > Web Data Connector`.
4. Paste `http://localhost:8000/static/tableau_wdc.html`.
5. In the connector page, keep the default API base URL unless you are pointing Tableau at another deployment.
6. Optionally fill in years, profiles, trend grouping, and dimension filters.
7. Click `Get data`.
8. Tableau will expose `snies_summary` and `snies_trend` as tables.

### 3.4 How it is wired in FastAPI

This is the actual static mount used by the repo:

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

As a result, the connector and the API share the same host and port.

### 3.5 CORS behavior

In the shipped local setup, the WDC is served from the same FastAPI origin as the API, so there is no cross-origin hop by default.

If you later move the connector to a different host, the API must allow that origin through CORS. The current app already enables broad CORS, but a production setup should tighten that allow-list.

## 4. Option B - Scheduled Hyper extract

Use this when you want Tableau Server or Tableau Cloud to refresh on a schedule without keeping a live connection to the API, or when the dataset grows beyond what a WDC pull should return in one shot.

### 4.1 Python job

```python
# tools/publish_hyper.py
from pathlib import Path
import httpx
from tableauhyperapi import (
    HyperProcess, Connection, CreateMode, Telemetry,
    TableDefinition, SqlType, Inserter, TableName, NOT_NULLABLE, NULLABLE,
)

API_BASE = "http://localhost:8000"
OUT = Path("data/exports/prig_snies.hyper")
OUT.parent.mkdir(parents=True, exist_ok=True)

def pull(path, params=None):
    response = httpx.get(API_BASE + path, params=params, timeout=60)
    response.raise_for_status()
    return response.json()["rows"]

summary_rows = pull("/api/v1/summary")
trend_rows = pull("/api/v1/trend", params={"group_by": "sector"})

summary_def = TableDefinition(
    TableName("Extract", "Summary"),
    [
        TableDefinition.Column("year", SqlType.int(), NOT_NULLABLE),
        TableDefinition.Column("profile", SqlType.text(), NOT_NULLABLE),
        TableDefinition.Column("total_value", SqlType.double(), NULLABLE),
    ],
)

trend_def = TableDefinition(
    TableName("Extract", "Trend"),
    [
        TableDefinition.Column("year", SqlType.int(), NOT_NULLABLE),
        TableDefinition.Column("profile", SqlType.text(), NOT_NULLABLE),
        TableDefinition.Column("group_value", SqlType.text(), NULLABLE),
        TableDefinition.Column("total_value", SqlType.double(), NULLABLE),
    ],
)

with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
    with Connection(
        endpoint=hyper.endpoint,
        database=OUT,
        create_mode=CreateMode.CREATE_AND_REPLACE,
    ) as conn:
        conn.catalog.create_schema("Extract")
        conn.catalog.create_table(summary_def)
        conn.catalog.create_table(trend_def)
        with Inserter(conn, summary_def) as inserter:
            inserter.add_rows([[r["year"], r["profile"], r["total_value"]] for r in summary_rows])
            inserter.execute()
        with Inserter(conn, trend_def) as inserter:
            inserter.add_rows(
                [[r["year"], r["profile"], r["group_value"], r["total_value"]] for r in trend_rows]
            )
            inserter.execute()
```

Install with:

```text
pip install tableauhyperapi httpx
```

### 4.2 Publishing

Publish the resulting `.hyper` file to Tableau Server or Tableau Cloud with `tabcmd` or the Tableau Server Client library.

## 5. Bypass: direct DuckDB ODBC

If your use case is ad-hoc analysis and Tableau has file access to `data/warehouse/snies.duckdb`, the fastest path is to bypass the API and connect Tableau directly to DuckDB.

1. Install the DuckDB ODBC driver.
2. Create a DSN pointing at the `.duckdb` file.
3. In Tableau, go to `Connect > To a Server > Other Databases (ODBC)`.
4. Drag `fact_observations`, `institution_dim`, and `observation_dimensions` into the model.

Trade-offs versus the API path:

- Row-level facts are available immediately.
- Query execution is usually faster.
- Tableau needs file-system access to the database file.
- You bypass API-level filtering and guardrails.
- Long reads can still contend with warehouse writes during sync.

## 6. Production-readiness checklist

Before using Tableau against the API in production, consider adding:

1. Authentication for the WDC or extract jobs.
2. A row-level `GET /api/v1/facts` endpoint with pagination.
3. A stable `GET /api/v1/schema` endpoint for column metadata.
4. Response limits or server-side caps for large requests.
5. Compression for bigger payloads.
6. A tighter CORS allow-list than `*`.

## 7. Option C - native OData endpoint (future)

Tableau has first-class OData connectors. Adding an OData layer would allow a more native drag-and-drop connection experience without a custom WDC page.

Minimum useful surface:

- `GET /odata/$metadata`
- `GET /odata/Summary`
- support for `$filter`, `$top`, `$skip`, and `$orderby`

## 8. Quick reference

| Want | Do |
|---|---|
| Live Tableau dashboards refreshed on demand | Use the shipped WDC at `http://localhost:8000/static/tableau_wdc.html` |
| Scheduled Tableau Server extracts | Build and publish a Hyper extract |
| Ad-hoc row-level analysis on the same host | Use DuckDB ODBC |
| A native connector story without custom HTML | Add OData to the API |
