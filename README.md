# India Development Study

An end-to-end data lakehouse pipeline studying India's development 
story from 2015 to 2025.

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
- Python 3.11 — ingestion scripts
- DuckDB — local lakehouse storage
- dbt — data transformation and modeling (6 models, 16 tests)
- Apache Airflow — orchestration (coming soon)
- Metabase — dashboarding (coming soon)

## Architecture
Raw Sources → Python Ingestion → DuckDB (raw) → dbt (staging → intermediate → marts) → Dashboard

## dbt Models
- staging: stg_world_bank, stg_upi_historical, stg_climate_trace
- intermediate: int_india_yearly
- marts: mart_india_development, mart_emissions_by_sector

## Key Findings So Far
- GDP grew from $2.1T to $3.7T between 2015-2024
- UPI volume grew 65,000x from 2016 to 2024
- Internet users grew from 15% to 65% of population
- Power sector is India's largest emitter at 33% of total CO2e

## Project Structure
- ingestion/ — Python scripts to fetch data from APIs and Kaggle
- dbt_project/ — dbt models, tests, documentation
- airflow/dags/ — Airflow DAGs (coming soon)
- data/ — local raw and processed data (gitignored)
- docs/ — architecture diagrams and notes

## Planned Improvements
- TRAI state-level telecom subscriber data
- Airflow DAG for end-to-end orchestration
- Metabase dashboard
- dbt documentation site

## Setup
```bash
# Clone the repo
git clone git@github.com:YOURUSERNAME/India-development-study.git
cd India-development-study

# Create venv and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run ingestion
python ingestion/world_bank.py
python ingestion/npci_upi_historical.py
python ingestion/npci.py
python ingestion/climate_trace.py

# Run dbt
cd dbt_project
dbt run
dbt test
```
