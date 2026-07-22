from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'india_dev_study',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

PROJECT_DIR = '/opt/airflow/project'

with DAG(
    dag_id='india_development_pipeline',
    description='End-to-end India development data pipeline',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='0 6 1 * *',
    catchup=False,
    tags=['india', 'development', 'etl'],
) as dag:

    ingest_world_bank = BashOperator(
        task_id='ingest_world_bank',
        bash_command=f'cd {PROJECT_DIR} && python ingestion/world_bank.py',
    )

    ingest_upi = BashOperator(
        task_id='ingest_upi_historical',
        bash_command=f'cd {PROJECT_DIR} && python ingestion/npci_upi_historical.py',
    )

    ingest_npci = BashOperator(
        task_id='ingest_npci_products',
        bash_command=f'cd {PROJECT_DIR} && python ingestion/npci.py',
    )

    ingest_climate = BashOperator(
        task_id='ingest_climate_trace',
        bash_command=f'cd {PROJECT_DIR} && python ingestion/climate_trace.py',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f'cd {PROJECT_DIR}/dbt_project && dbt run --profiles-dir {PROJECT_DIR}/.dbt',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=f'cd {PROJECT_DIR}/dbt_project && dbt test --profiles-dir {PROJECT_DIR}/.dbt',
    )

    ingest_world_bank >> ingest_upi >> ingest_npci >> ingest_climate >> dbt_run >> dbt_test
