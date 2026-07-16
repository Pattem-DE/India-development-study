# India Development Study

An end-to-end data lakehouse pipeline studying India's development 
story from 2000 to 2024.

## Data Sources
- World Bank India Indicators (GDP, poverty, internet access)
- NPCI UPI Transaction Data (2016-2024)
- TRAI Telecom Subscriber Data (by state)
- Climate TRACE Emissions Data (India)

## Stack
- Python 3.11 — ingestion scripts
- DuckDB — local lakehouse storage
- dbt — data transformation and modeling
- Apache Airflow — orchestration
- Metabase — dashboarding

## Architecture
Raw Sources → Python Ingestion → DuckDB (raw) → dbt (staging → intermediate → marts) → Dashboard

## Project Structure
- ingestion/ — Python scripts to fetch data from APIs
- dbt_project/ — dbt models, tests, documentation
- airflow/dags/ — Airflow DAGs for orchestration
- data/ — local raw and processed data (gitignored)
- notebooks/ — exploratory analysis
- docs/ — architecture diagrams and notes
