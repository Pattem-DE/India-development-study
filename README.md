# India Development Study
An end-to-end orchestrated data lakehouse pipeline studying India's
development story from 2015 to 2025.
## The Story
How did a country of 1.4 billion people nearly double its GDP,
grow internet penetration from 15% to 65%, and build the world's
largest real-time payments network — all in 10 years?
## Data Sources
| Source | Data | Rows | Status |
|--------|------|------|--------|
| World Bank API | GDP, poverty, internet, mobile 2000-2024 | 158 | ✅ Live |
| NPCI via Kaggle | UPI transactions April 2016 - Aug 2025 | 113 | ✅ Live |
| NPCI via Kaggle | 11 payment products 2024 | 132 | ✅ Live |
| Climate TRACE API | Emissions by sector 2015-2024 | 80 | ✅ Live |
| TRAI Telecom | State-level internet and mobile data | - | 📋 Planned |
## Stack
- **Python 3.11** — ingestion scripts
- **DuckDB** — local lakehouse storage
- **dbt** — data transformation and modeling (6 models, 16 tests)
- **Apache Airflow** — orchestration, running fully containerized via Docker Compose
- **Docker + Docker Compose** — reproducible environment
- **Metabase** — dashboarding (coming soon)
## Architecture
Raw Sources (API/Kaggle)
→ Python Ingestion Scripts
→ DuckDB (raw layer)
→ dbt staging (clean + standardize)
→ dbt intermediate (join across sources)
→ dbt marts (analytics-ready tables)
→ Airflow orchestrates the entire flow end-to-end

## Orchestration
The full pipeline runs as a single Airflow DAG (`india_development_pipeline`):
ingest_world_bank → ingest_upi → ingest_npci → ingest_climate → dbt_run → dbt_test

Ingestion tasks run **sequentially rather than in parallel** — a deliberate 
design choice after discovering DuckDB only allows one writer at a time. 
Running tasks in parallel caused lock conflicts; chaining them fixed it.

Airflow runs entirely inside Docker (official `docker-compose.yaml`), using:
- **LocalExecutor** (not Celery — avoided a known Celery worker bug in 2.9.1)
- **PostgreSQL** as the metadata database
- A custom Docker image (see `Dockerfile`) with dbt and ingestion dependencies baked in

## dbt Models
- **staging**: `stg_world_bank`, `stg_upi_historical`, `stg_climate_trace`
- **intermediate**: `int_india_yearly`
- **marts**: `mart_india_development`, `mart_emissions_by_sector`

16 dbt tests covering not-null, uniqueness, and accepted-value constraints.

## Key Findings So Far
- GDP grew from $2.1T to $3.7T between 2015-2024
- UPI volume grew 65,000x from 2016 to 2024
- Internet users grew from 15% to 65% of population
- Power sector is India's largest emitter at 33% of total CO2e
- 2020 (COVID) shows a clear dip: GDP -5.67%, emissions dropped, but UPI still grew

## Engineering Notes — Real Issues Hit and Fixed
This project went through some issue debugging as mentioned below:
- **Idempotency bug**: World Bank ingestion was using `INSERT` without 
  clearing old data first — every DAG re-run duplicated rows (158 → 632). 
  Fixed by switching to `DROP TABLE` + `CREATE TABLE` like the other scripts.
- **DuckDB concurrent-write lock**: Running 4 ingestion tasks in parallel 
  caused "Conflicting lock" errors since DuckDB only supports one writer. 
  Fixed by chaining tasks sequentially in the DAG.
- **Celery worker crash**: Airflow's default CeleryExecutor hit a known 
  `NoneType` bug in this version. Switched to LocalExecutor — simpler and 
  more reliable for a single-machine setup.
- **File permission conflicts**: The Airflow container runs as a different 
  user than the WSL2 host, causing write-permission errors on the DuckDB 
  file and dbt logs. Fixed with proper directory permissions.

## Project Structure
├── dags/                   # Airflow DAG definitions
├── dbt_project/            # dbt models, tests, docs
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
├── ingestion/               # Python ingestion scripts
├── data/raw/                 # Local DuckDB file (gitignored)
├── Dockerfile                # Custom Airflow image with dependencies
├── docker-compose.yaml        # Full Airflow + Postgres stack
└── requirements.txt

## Planned Improvements
- TRAI state-level telecom subscriber data
- Metabase dashboard connected to the marts
- dbt documentation site (`dbt docs generate`)

## Setup

```bash
# Clone the repo
git clone git@github.com:YOURUSERNAME/India-development-study.git
cd India-development-study

# Create venv for local dbt/ingestion work
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run ingestion locally (optional - Airflow does this automatically)
python ingestion/world_bank.py
python ingestion/npci_upi_historical.py
python ingestion/npci.py
python ingestion/climate_trace.py

# Run dbt locally
cd dbt_project
dbt run
dbt test

# OR run the full orchestrated pipeline via Airflow
cd ..
docker compose up airflow-init
docker compose up -d
# Visit http://localhost:8080 (login: airflow/airflow)
# Trigger the 'india_development_pipeline' DAG
```
