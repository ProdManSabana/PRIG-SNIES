# PRIG SNIES

Plataforma de datos containerizada para análisis de educación superior en Bogotá, D.C. integrada con las bases consolidadas del SNIES y el registro de IES del HECAA.

## Qué incluye

- una capa de ingesta resiliente para archivos anuales de estudiantes y docentes del SNIES y datos de instituciones del HECAA
- libros de metadatos anuales preservados para posterior etiquetado de esquemas y gobernanza de datos
- un pipeline de normalización que preserva dimensiones arbitrarias de las fuentes
- un almacén analítico DuckDB
- un servicio FastAPI para agregados filtrados
- un dashboard Streamlit para conteos y ratios de estudiantes-por-docente

## Estructura del proyecto

- `backend/`: ingesta, normalización, almacén, API
- `dashboard/`: dashboard Streamlit
- `data/`: capas persistidas de landing, raw, processed y warehouse
- `docs/architecture.md`: decisiones de arquitectura
- `docs/warehouse-er-model.md`: referencia del modelo de datos interno

## Inicio rápido

1. Revisa `.env` si deseas cambiar años, departamento, puertos o cadencia de sincronización.
2. Inicia la plataforma:

```bash
docker compose up --build
```

3. Abre el dashboard en el puerto `8501` y la API en el puerto `8000`.

## Notas

- El pipeline está configurado para `Bogotá, D.C.` y años objetivo `2022, 2023, 2024`.
- La normalización actual es intencionalmente tolerante a esquemas porque los diseños de archivos del SNIES pueden variar por perfil y año.
- Si los portales activos cambian su estructura HTML o mecánica de descarga, los adaptadores de fuentes en `backend/app/sources/` son el lugar para actualizar.

---

## 📋 Guía de Instalación y Ejecución (Español)

### Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

- **Docker** (v20.10 o superior)
- **Docker Compose** (v2.0 o superior)
- **Git** (v2.25 o superior)
- **Python 3.9+** (opcional, solo si ejecutas sin Docker)

#### Verificar Versiones Instaladas

```bash
docker --version
docker compose version
git --version
python --version
```

### Instalación en Windows

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/ProdManSabana/PRIG-SNIES.git
   cd PRIG-SNIES
   ```

2. **Configurar variables de entorno (opcional)**
   ```bash
   # El archivo .env ya está configurado por defecto
   # Edítalo solo si necesitas cambiar puertos, años o departamento
   notepad .env
   ```

   Variables disponibles:
   - `TARGET_YEARS`: Años a procesar (ej: 2022,2023,2024)
   - `TARGET_DEPARTMENT`: Departamento (Bogotá, D.C. por defecto)
   - `API_PORT`: Puerto de la API (8000 por defecto)
   - `STREAMLIT_PORT`: Puerto del dashboard (8501 por defecto)
   - `SYNC_INTERVAL_HOURS`: Intervalo de sincronización (24 horas por defecto)

3. **Iniciar la plataforma con Docker Compose**
   ```bash
   docker compose up --build
   ```

4. **Acceder a los servicios**
   - **Dashboard Streamlit**: http://localhost:8501
   - **API FastAPI**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

   ** _Nota importante de ejecución_ : Si la plataforma en el Dashboard (tablero de visualización) se queda patinando por largo tiempo en la primera ejecución "Running fetch_json(...)", detenerla con 'Stop' arriba a la derecha, limpiar el caché del navegador y reiniciar con **Ctrl+Shift+R** 

5. **Detener la plataforma**
   ```bash
   docker compose down
   ```

### Instalación en Linux

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/ProdManSabana/PRIG-SNIES.git
   cd PRIG-SNIES
   ```

2. **Configurar variables de entorno (opcional)**
   ```bash
   nano .env
   # o tu editor preferido (vim, gedit, etc.)
   ```

3. **Iniciar la plataforma**
   ```bash
   docker compose up --build
   ```

4. **En otra terminal, verificar servicios**
   ```bash
   docker compose ps
   ```

5. **Ver logs en tiempo real**
   ```bash
   docker compose logs -f
   ```

6. **Acceder a los servicios**
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

7. **Detener servicios**
   ```bash
   docker compose down
   ```

### Instalación en macOS

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/ProdManSabana/PRIG-SNIES.git
   cd PRIG-SNIES
   ```

2. **Configurar variables de entorno (opcional)**
   ```bash
   nano .env
   ```

3. **Iniciar la plataforma**
   ```bash
   docker compose up --build
   ```

4. **Verificar que los servicios estén corriendo**
   ```bash
   docker compose ps
   ```

5. **Acceder a los servicios**
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Detener la plataforma**
   ```bash
   docker compose down
   ```

### Ejecución sin Docker (Desarrollo Local)

Si prefieres ejecutar la aplicación sin Docker:

#### Backend (API)

```bash
cd backend
pip install -r requirements.txt
python -m app.api
```

#### Dashboard

En otra terminal:

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

**Nota**: El backend debe estar ejecutándose primero.

### Comandos Útiles

| Comando | Descripción |
|---------|-------------|
| `docker compose up --build` | Inicia todos los servicios (reconstruye imágenes) |
| `docker compose up -d` | Inicia en background |
| `docker compose down` | Detiene todos los servicios |
| `docker compose logs -f api` | Ver logs de la API en tiempo real |
| `docker compose logs -f dashboard` | Ver logs del dashboard |
| `docker compose ps` | Listar servicios activos |
| `docker compose restart api` | Reiniciar servicio específico |

### Estructura de Datos

La aplicación crea automáticamente la siguiente estructura de directorios en `./data/`:

```
data/
├── landing/        # Datos descargados crudos del portal SNIES
├── raw/            # Datos después de extracción inicial
├── processed/      # Datos normalizados y transformados
└── warehouse/      # DuckDB warehouse (snies.duckdb)
```

### Solución de Problemas

**Error: "docker: command not found"**
- Instala Docker Desktop desde [docker.com](https://www.docker.com/products/docker-desktop)

**Error: "Cannot connect to Docker daemon"**
- Asegúrate de que Docker Desktop está ejecutándose
- En Linux: `sudo systemctl start docker`

**Error: "Port 8000 or 8501 already in use"**
- Cambia los puertos en `.env`:
  ```
  API_PORT=8001
  STREAMLIT_PORT=8502
  ```
- Luego reinicia: `docker compose up --build`

**Error: "No space left on device"**
- Limpia imágenes y contenedores: `docker system prune -a`

**Error: "Failed to download SNIES data"**
- Verifica tu conexión a internet
- Comprueba que `SNIES_BASE_URL` es accesible
- Revisa los logs: `docker compose logs scheduler`

### Notas de Configuración

- La plataforma está preconfigurada para **Bogotá, D.C.** (código 11)
- Los años por defecto son **2022, 2023, 2024**
- La sincronización automática ocurre cada **24 horas**
- El almacén de datos usa **DuckDB** para análisis eficiente

---

## 📖 Installation and Execution Guide (English)

### Prerequisites

Ensure you have the following installed on your system:

- **Docker** (v20.10 or higher)
- **Docker Compose** (v2.0 or higher)
- **Git** (v2.25 or higher)
- **Python 3.9+** (optional, only for local development without Docker)

#### Verify Installed Versions

```bash
docker --version
docker compose version
git --version
python --version
```

### Windows Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/PRIG-SNIES.git
   cd PRIG-SNIES
   ```

2. **Configure environment variables (optional)**
   ```bash
   # The .env file is pre-configured by default
   # Edit only if you need to change ports, years, or department
   notepad .env
   ```

   Available variables:
   - `TARGET_YEARS`: Years to process (e.g., 2022,2023,2024)
   - `TARGET_DEPARTMENT`: Department (Bogotá, D.C. by default)
   - `API_PORT`: API port (8000 by default)
   - `STREAMLIT_PORT`: Dashboard port (8501 by default)
   - `SYNC_INTERVAL_HOURS`: Sync interval (24 hours by default)

3. **Start the platform with Docker Compose**
   ```bash
   docker compose up --build
   ```

4. **Access the services**
   - **Streamlit Dashboard**: http://localhost:8501
   - **FastAPI**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

5. **Stop the platform**
   ```bash
   docker compose down
   ```

### Linux Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/PRIG-SNIES.git
   cd PRIG-SNIES
   ```

2. **Configure environment variables (optional)**
   ```bash
   nano .env
   # or your preferred editor (vim, gedit, etc.)
   ```

3. **Start the platform**
   ```bash
   docker compose up --build
   ```

4. **In another terminal, verify services**
   ```bash
   docker compose ps
   ```

5. **View real-time logs**
   ```bash
   docker compose logs -f
   ```

6. **Access the services**
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

7. **Stop services**
   ```bash
   docker compose down
   ```

### macOS Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/PRIG-SNIES.git
   cd PRIG-SNIES
   ```

2. **Configure environment variables (optional)**
   ```bash
   nano .env
   ```

3. **Start the platform**
   ```bash
   docker compose up --build
   ```

4. **Verify services are running**
   ```bash
   docker compose ps
   ```

5. **Access the services**
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Stop the platform**
   ```bash
   docker compose down
   ```

### Running Without Docker (Local Development)

If you prefer to run the application without Docker:

#### Backend (API)

```bash
cd backend
pip install -r requirements.txt
python -m app.api
```

#### Dashboard

In another terminal:

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

**Note**: The backend must be running first.

### Useful Commands

| Command | Description |
|---------|-------------|
| `docker compose up --build` | Start all services (rebuild images) |
| `docker compose up -d` | Start in background |
| `docker compose down` | Stop all services |
| `docker compose logs -f api` | View API logs in real-time |
| `docker compose logs -f dashboard` | View dashboard logs |
| `docker compose ps` | List active services |
| `docker compose restart api` | Restart specific service |

### Project Architecture

#### Services Overview

- **api**: FastAPI service providing filtered aggregates and analytics endpoints
  - Port: `8000` (configurable via `API_PORT`)
  - Endpoints: `/api/v1/summary`, `/api/v1/trend`, `/api/v1/filters`, `/api/v1/sync-status`

- **scheduler**: Background job for automated data ingestion and normalization
  - Runs every `SYNC_INTERVAL_HOURS` (24 hours by default)
  - Ingests SNIES and HECAA data from official portals

- **dashboard**: Streamlit analytics dashboard
  - Port: `8501` (configurable via `STREAMLIT_PORT`)
  - Displays student counts, teacher totals, and student-to-teacher ratios

#### Data Pipeline

```
SNIES Portal & HECAA Registry
         ↓
    Landing Layer (raw downloads)
         ↓
    Raw Layer (extracted data)
         ↓
    Processed Layer (normalized data)
         ↓
    DuckDB Warehouse (analytical)
         ↓
    FastAPI Service
         ↓
    Streamlit Dashboard
```

#### Data Structure

The application automatically creates the following directory structure in `./data/`:

```
data/
├── landing/        # Raw downloads from SNIES portal
├── raw/            # Extracted data from landing files
├── processed/      # Normalized and transformed data
└── warehouse/      # DuckDB warehouse (snies.duckdb)
```

### Dependencies

#### Backend (`backend/requirements.txt`)
- **APScheduler**: Job scheduling for automated ingestion
- **FastAPI**: Modern web API framework
- **DuckDB**: Analytical data warehouse
- **Pandas**: Data manipulation and analysis
- **BeautifulSoup4 & lxml**: Web scraping for portal data
- **OpenPyXL & xlrd**: Excel file handling
- **Pydantic Settings**: Configuration management
- **Uvicorn**: ASGI server

#### Dashboard (`dashboard/requirements.txt`)
- **Streamlit**: Web app framework for analytics dashboards
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation
- **httpx**: Async HTTP client for API communication

### Environment Variables Reference

| Variable                 | Default                                                     | Description |
|--------------------------|-------------------------------------------------------------|-------------|
| `SNIES_BASE_URL`         | https://snies.mineducacion.gov.co/portal/ESTADISTICAS/Bases-consolidadas/ | SNIES data portal URL |
| `HECAA_IES_URL`          | https://hecaa.mineducacion.gov.co/consultaspublicas/ies                   | HECAA IES registry URL |
| `TARGET_DEPARTMENT`      | Bogotá, D.C.                                                              | Department to analyze |
| `TARGET_DEPARTMENT_CODE` | 11                                                                        | Department code (DANE standard) |
| `TARGET_YEARS`           | 2022,2023,2024                                                            | Comma-separated years to process |
| `SYNC_INTERVAL_HOURS`    | 24                                                                        | Hours between automatic syncs |
| `API_PORT`               | 8000                                                                      | API service port |
| `STREAMLIT_PORT`         | 8501                                                                      | Dashboard service port |
| `WAREHOUSE_PATH`         | /app/data/warehouse/snies.duckdb                                          | DuckDB warehouse location |

### Troubleshooting for Maintainers

**Issue: "Cannot connect to SNIES portal"**
- Check if portal URL is still accessible
- Review `backend/app/sources/` adapters if HTML structure changed
- Check logs: `docker compose logs scheduler`

**Issue: "DuckDB file locked"**
- Ensure only one process accesses the warehouse
- Rebuild: `docker compose down && docker compose up --build`

**Issue: "Out of memory during processing"**
- Reduce `TARGET_YEARS` in `.env` to process fewer years at once
- Or increase Docker memory allocation in Docker Desktop settings

**Issue: "API not responding to dashboard requests"**
- Verify `api` service is running: `docker compose ps`
- Check API health: `curl http://localhost:8000/docs`
- Review API logs: `docker compose logs api`

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes to `backend/` or `dashboard/`
3. Test locally: `docker compose up --build`
4. Verify API endpoints work: `curl http://localhost:8000/docs`
5. Check dashboard loads: `http://localhost:8501`
6. Commit and push: `git push origin feature/your-feature`

### Notes

- The normalization pipeline is intentionally schema-tolerant because SNIES file layouts differ by profile and year
- If portal HTML structures change, update adapters in `backend/app/sources/`
- Data is persisted across container restarts (stored in `./data/` volume)
- All timestamps are in UTC

---

*Last updated: April 19, 2026*

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
- `docs/warehouse-er-model.md`: actual DuckDB schema (6 tables, 383,191 facts, 8.2M dimension rows, 390 institutions, 23 distinct dimension names) cross-referenced with the code that writes it. 

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
