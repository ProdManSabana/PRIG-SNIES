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
   - **Tableau WDC**: http://localhost:8000/static/tableau_wdc.html

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
   - Tableau WDC: http://localhost:8000/static/tableau_wdc.html

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
   - Tableau WDC: http://localhost:8000/static/tableau_wdc.html

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
   - **Tableau WDC**: http://localhost:8000/static/tableau_wdc.html

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
   - Tableau WDC: http://localhost:8000/static/tableau_wdc.html

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
   - Tableau WDC: http://localhost:8000/static/tableau_wdc.html

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
  - Static WDC: `/static/tableau_wdc.html`

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

# Used tool: mcp__gitkraken__git_log_or_diff

Searched for files matching `backend/**/*.py`

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES)



Ran terminal command: cd c:/Users/ae.wills22/source/repos/PRIG-SNIES && git log --oneline -30

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/README.md)

Ran terminal command: cd c:/Users/ae.wills22/source/repos/PRIG-SNIES ; git log --oneline -30

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/docs/architecture.md)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/main.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/pipeline/sync.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/db/warehouse.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/api/app.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/core/settings.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/api/routes.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/backend/app/sources/snies.py)

Read [](file:///c%3A/Users/ae.wills22/source/repos/PRIG-SNIES/docker-compose.yaml)

Aquí te presento un análisis comprensivo de las decisiones técnicas y arquitectónicas del proyecto PRIG SNIES basado en el historial de commits y la estructura del código:

---

# ANÁLISIS DE DECISIONES TÉCNICAS Y ARQUITECTÓNICAS - PRIG SNIES

## 1. RESUMEN EJECUTIVO

PRIG SNIES es una plataforma de datos containerizada construida con principios de **arquitectura modular y resiliente**. Las decisiones técnicas responden a la necesidad de integrar múltiples fuentes de datos con esquemas inconsistentes (SNIES, HECAA) manteniendo flexibilidad, durabilidad y facilidad de mantenimiento a largo plazo.

---

## 2. ARQUITECTURA GENERAL

### Modelo de Capas Separadas

El proyecto implementa un **patrón de capas de datos** bien definido:

```
SNIES/HECAA (Portales Públicos)
         ↓
    Landing Layer (Descarga cruda)
         ↓
    Raw Layer (Extracción inicial)
         ↓
    Processed Layer (Normalización)
         ↓
    DuckDB Warehouse (Analytical)
         ↓
    FastAPI Service (Agregados filtrados)
         ↓
    Streamlit Dashboard (Visualización)
```

**Justificación**: Esta separación permite que cada capa sea independiente, versionable y auditable. Los datos se preservan en cada etapa, facilitando la gobernanza de datos y permitiendo reproducibilidad de análisis históricos.

### Orquestación con Docker Compose

**Decisión**: Tres servicios containerizados (`api`, `scheduler`, `dashboard`) con volumen compartido.

**Beneficios**:
- **Reproducibilidad**: Mismo ambiente en desarrollo, testing y producción
- **Aislamiento**: Cada servicio está aislado pero coordinado
- **Escalabilidad horizontal**: Fácil replicar servicios sin cambiar código
- **Facilidad de deploy**: Un único comando (`docker compose up --build`)

---

## 3. DECISIONES TÉCNICAS CLAVE

### 3.1 Modelo de Datos: Observación-Dimensión (Schema-Agnostic)

**Decisión**: En lugar de fijar un esquema wide (muchas columnas), se usa:
- `fact_observations`: Una fila = una medida
- `observation_dimensions`: Tabla tall para dimensiones descubiertas dinámicamente
- `field_metadata`: Preserva metadatos originales

**Justificación**:
```python
# En sync.py:115-257
# Normalización tolerante a esquemas heterogéneos
for asset in snies_assets:
    for sheet_name, frame in load_tabular_file(asset.local_path):
        # Detecta automáticamente columnas de medida
        measure_column = detect_measure_column(frame)
        # Extrae dimensiones de forma flexible
        row_dims = row_dimensions(row_dict, excluded)
```

**Ventajas**:
- ✅ **Robustez**: Tolera cambios en estructura de archivos SNIES entre años/perfiles
- ✅ **Sostenibilidad**: Años 2022, 2023, 2024 con layouts diferentes conviven sin recodificación
- ✅ **Escalabilidad**: Agregar nuevos años con estructuras variantes es transparente

### 3.2 DuckDB como Almacén Analítico

**Decisión**: Usar DuckDB en lugar de PostgreSQL, MySQL o data warehouse en la nube.

**Justificación técnica**:
- **Embebido**: Se ejecuta como archivo en disco (simplifica despliegue)
- **OLAP nativo**: Optimizado para agregaciones y análisis (no OLTP)
- **Sin servidor**: No requiere servicio separado
- **Compresión nativa**: Reduce overhead de storage

**Impacto en atributos de calidad**:

| Atributo | Beneficio |
|----------|-----------|
| **Robustez** | Archivo único simplifica backups y recuperación |
| **Mantenibilidad** | Cero configuración de servidor externo |
| **Escalabilidad** | Soporta cientos de millones de filas eficientemente |
| **Accesibilidad** | API estándar SQL, bajo conocimiento requerido |

### 3.3 Reintentos y Manejo de Locks

**Decisión**: Implementar reintentos exponenciales para locks de DuckDB.

```python
# warehouse.py:14-35
DUCKDB_LOCK_RETRY_ATTEMPTS = 10
DUCKDB_LOCK_RETRY_DELAY_SECONDS = 1

def should_retry_duckdb_lock(exc: duckdb.IOException) -> bool:
    message = str(exc)
    return "Could not set lock on file" in message and "Conflicting lock is held" in message
```

**Beneficios**:
- ✅ **Robustez**: Tolera condiciones transitorias (scheduler y API accediendo simultáneamente)
- ✅ **Resilencia**: Evita fallos falsos por contención normal

### 3.4 Configuración Centralizada con Pydantic Settings

**Decisión**: Settings singleton con validación automática.

```python
# core/settings.py
class Settings(BaseSettings):
    snies_base_url: str = "https://snies.mineducacion.gov.co/..."
    target_department: str = "Bogotá, D.C."
    target_years: list[int] = [2022, 2023, 2024]
    warehouse_path: Path = Path("/app/data/warehouse/snies.duckdb")
```

**Ventajas**:
- ✅ **Mantenibilidad**: Un único punto de verdad para configuración
- ✅ **Escalabilidad**: Permite parametrizar comportamiento sin recodificar
- ✅ **Sostenibilidad**: Cambios en URLs de portal requieren solo actualizar `.env`

### 3.5 Normalization Service: Funciones Puras

El módulo `services/normalization.py` contiene funciones sin estado:

```python
def normalize_code(value: str) -> str:
    """Normaliza códigos DANE sin efectos laterales"""
    
def normalize_label(value: str) -> str:
    """Normaliza labels para comparación case-insensitive"""
    
def select_first_existing(columns: list, candidates: list) -> str | None:
    """Detecta columnas por patrones de nombres"""
```

**Beneficios**:
- ✅ **Testabilidad**: Funciones puras son triviales de testear
- ✅ **Reutilización**: Mismo código en sync y API
- ✅ **Mantenibilidad**: Lógica de normalización centralizada

### 3.6 FastAPI con Dependency Injection

```python
# api/routes.py
def get_warehouse(settings: Annotated[Settings, Depends(get_settings)]) -> Warehouse:
    return Warehouse(settings)

@router.get("/api/v1/filters", response_model=FilterOptions)
def filters(warehouse: Annotated[Warehouse, Depends(get_warehouse)]) -> FilterOptions:
    # Warehouse inyectado automáticamente
```

**Ventajas**:
- ✅ **Testabilidad**: Mock fácil de Warehouse para tests
- ✅ **Escalabilidad**: Soporte para cambiar implementación sin afectar endpoints
- ✅ **Mantenibilidad**: Separación clara de concerns (HTTP vs lógica de datos)

### 3.7 CORS Abierto para Accesibilidad

```python
# api/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Justificación**:
- ✅ **Accesibilidad**: Dashboard y herramientas externas (Tableau WDC) pueden conectar sin barreras
- ⚠️ **Trade-off**: Seguridad reducida en producción (debería restringirse a origen conocido)

---

## 4. CÓMO LAS DECISIONES SOPORTAN LOS ATRIBUTOS DE CALIDAD

### 4.1 ROBUSTEZ

| Decisión | Mecanismo | Ejemplo |
|----------|-----------|---------|
| Schema-agnostic | Tolera varianza estructural | SNIES 2022 vs 2024 layouts diferentes |
| Reintentos de locks | Maneja contención transitoria | API y scheduler simultáneos sin fallos |
| Validación con Pydantic | Rechaza configuración inválida en startup | Tipos de dato validados automáticamente |
| Preservation de metadatos | Auditoria de transformaciones | `field_metadata` table conserva originales |

**Commit evidencia**: `68b1e8c` - *"Enhance warehouse connection handling with retry logic"*

### 4.2 ESCALABILIDAD

| Decisión | Mecanismo | Límite actual |
|----------|-----------|---------------|
| DuckDB OLAP | Agregaciones eficientes en millones de filas | 383,191 facts, 8.2M dimension rows |
| Capas separadas | Landing/Raw/Processed pueden procesarse independientemente | Agregar años sin reprocess histórico |
| Scheduler asincrónico | Ingesta no bloquea API | Sync cada 24h no afecta queries |
| Docker compose scale | Replicar servicios horizontalmente | `docker-compose up --scale api=3` |

**Commit evidencia**: `de60adb` - *"Optimizations and refactorings... implementing caching mechanisms"*

### 4.3 SOSTENIBILIDAD

| Decisión | Mecanismo | Implicación |
|----------|-----------|-------------|
| Settings en `.env` | Cambios de URLs/años sin tocar código | Portal SNIES cambia → solo editar `.env` |
| Patrón adapter para fuentes | `SniesSource`, `HecaaSource` centralizados | Nuevo portal requiere solo nuevo adapter |
| Normalización tolerante | Cambios futuros en SNIES no rompen pipeline | Resiliencia a evolución de data sources |
| Metadatos preservados | Etiquetas futuras sin redownload | Gobernanza de datos escalable |

**Commit evidencia**: `61f571b` - *"Rebuilt the filtering: added a HIDDEN_DIMENSIONS set"* - Prueba de evolución del sistema

### 4.4 MANTENIBILIDAD

| Decisión | Beneficio | Ejemplo |
|----------|----------|---------|
| Modularidad (packages) | `app.pipeline`, `app.sources`, `app.db` aislados | Cambio en warehouse no afecta sources |
| Tipos explícitos (Pydantic) | IDE autocompletion, errores detectados temprano | `class SourceAsset(dataclass)` bien tipado |
| Funciones puras | Sin estado global, determinísticas | `normalize_code()` siempre igual output |
| Documentación inline | Decisiones explicadas en docstrings/commits | README en español e inglés |

**Commit evidencia**: `50c4720` - *"Expanded the README.md file with more detailed information"*

### 4.5 ACCESIBILIDAD

| Decisión | Mecanismo | Acceso |
|----------|-----------|--------|
| FastAPI auto-docs | Swagger UI en `/docs` | Descubrimiento de API sin leer código |
| CORS abierto | Integración desde navegador | Tableau WDC, herramientas externas |
| Interfaz SQL estándar | DuckDB soporta SQL puro | Herramientas BI genéricas (DBeaver, etc.) |
| Streamlit dashboard | UI visual sin codificar | Análisis exploratorio sin SQL |
| Docker Compose | Setup en 1 comando | `docker compose up --build` |

**Commit evidencia**: `d1c3677` - *"Add Tableau Web Data Connector and update API documentation"* - Explícito en accesibilidad

---

## 5. ANÁLISIS DEL HISTORIAL DE COMMITS

### Evolución de la Arquitectura

| Período | Commit | Foco | Implicación |
|---------|--------|------|-------------|
| **Inicial** | `310180f` - Initial commit | Estructura base | Planificación previa |
| **Core** | `de60adb` - Optimizations | Caching, query optimization | Escalabilidad temprana |
| **Estabilización** | `c28f2b0` - Fix scheduler dependencies | Confiabilidad | Lecciones aprendidas |
| **Integraciones** | `d1c3677` - Tableau WDC | Ecosistema | Accesibilidad extendida |

**Patrón**: Arquitectura estable → Optimizaciones → Expansión de integraciones

---

## 6. TRADE-OFFS Y DECISIONES CONSCIENTES

### 6.1 DuckDB vs Postgres

| Aspecto | DuckDB | Postgres |
|--------|--------|----------|
| **Complejidad** | Cero (embebido) | Alta (servidor) |
| **Escalabilidad horizontal** | Limitada | Excelente |
| **Costo** | Ninguno | Infraestructura |
| **Para PRIG** | ✅ Elegido | ✗ Overkill |

**Decisión consciente**: Se prioriza operacionalidad simple sobre escala masiva.

### 6.2 CORS Abierto

```python
allow_origins=["*"],  # ⚠️ Seguridad reducida
```

**Impacto**: Accesibilidad vs. Seguridad. Apropiado para datos públicos (educación superior), pero en producción debería restringirse:

```python
allow_origins=["https://dashboard.domain.com", "https://tableau.domain.com"]
```

### 6.3 Normalización Tolerante vs. Validación Estricta

**Decisión**: Aceptar data sucia, normalizar en pipeline, no rechazar.

```python
# Acepta variaciones en nombres de columnas
institution_code_column = select_first_existing(columns, IES_CODE_CANDIDATES)
```

**Trade-off**:
- ✅ **Robustez**: Pipeline no falla por formato ligero distinto
- ⚠️ **Calidad**: Posibles datos malformados pasan desapercibidos

**Mitigación**: `field_metadata` table preserva originales para auditoria.

---

## 7. RECOMENDACIONES PARA EVOLUCIÓN

### Corto Plazo (Mantenibilidad Inmediata)
1. **Restringir CORS** en producción: `allow_origins=["domain.com"]`
2. **Agregar logging** en warehouse connections para monitoreo
3. **Tests de integración** para sync pipeline (actualmente implícitos)

### Mediano Plazo (Escalabilidad)
1. **Migración a DuckDB con replicación** si datos crecen >10GB
2. **Cache layer** (Redis) para queries frecuentes
3. **Metrics** de rendimiento (tiempo de sync, latencia de queries)

### Largo Plazo (Sostenibilidad)
1. **CI/CD** automatizado con validación de schema
2. **Data contracts** formales con fuentes SNIES/HECAA
3. **Versionado de warehouse** para rollback de transformaciones

---

## 8. CONCLUSIÓN

PRIG SNIES implementa una **arquitectura pragmática y bien pensada** que prioriza:

1. **Flexibilidad sobre rigidez**: Schema-agnostic tolera evolución de fuentes
2. **Operacionalidad sobre complejidad**: DuckDB embebido vs. infraestructura compleja
3. **Preservación sobre descarte**: Metadatos conservados para gobernanza futura
4. **Accesibilidad sobre exclusividad**: CORS, Swagger, Tableau WDC abiertos

Las decisiones técnicas son **inversamente proporcionales al acoplamiento**, permitiendo que el sistema evolucione sin recodificación masiva. La separación de capas, uso de funciones puras, y configuración externalizada hacen del sistema **altamente mantenible** para equipos de pequeño y mediano tamaño.

El historial de commits muestra una **maduración gradual** desde MVP a plataforma estable, con énfasis creciente en integraciones y accesibilidad—indicador de salud arquitectónica.