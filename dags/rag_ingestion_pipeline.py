from datetime import datetime, timedelta
from airflow import DAG
from slack_alerts import slack_failure_alert
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'india_dev_study',
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'email_on_failure': False,
    'on_failure_callback': slack_failure_alert,
}

PROJECT_DIR = '/opt/airflow/project'

# Weekly during February only - catches the Union Budget speech (published
# Feb 1st) whether it's released exactly on time or a few days late.
# Cron: "0 8 1-28/7 2 *" = 8am, every 7th day starting from the 1st, in
# February only (days 1, 8, 15, 22)
with DAG(
    dag_id='budget_speech_check',
    description='Weekly check for new Union Budget speech during February',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='0 8 1-28/7 2 *',
    catchup=False,
    tags=['rag', 'ingestion', 'budget'],
) as budget_dag:

    fetch_budget = BashOperator(
        task_id='fetch_budget_speeches',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/fetch_budget_speeches.py',
    )

    rechunk = BashOperator(
        task_id='rechunk_documents',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/chunk_documents.py',
    )

    reembed_local = BashOperator(
        task_id='reembed_local_ollama',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/embed_and_store_raw.py',
    )

    reembed_cloud = BashOperator(
        task_id='reembed_supabase_cloud',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/embed_supabase_raw.py',
    )

    fetch_budget >> rechunk >> [reembed_local, reembed_cloud]


# Quarterly check for new NITI Aayog policy papers - these are published
# irregularly, so a quarterly check is a reasonable balance between
# staying current and not re-running unnecessarily
with DAG(
    dag_id='niti_aayog_quarterly_check',
    description='Quarterly check for new NITI Aayog policy documents',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='0 8 1 1,4,7,10 *',  # 8am on the 1st of Jan/Apr/Jul/Oct
    catchup=False,
    tags=['rag', 'ingestion', 'niti_aayog'],
) as niti_dag:

    fetch_niti = BashOperator(
        task_id='fetch_niti_aayog_docs',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/fetch_niti_aayog.py',
    )

    rechunk_niti = BashOperator(
        task_id='rechunk_documents',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/chunk_documents.py',
    )

    reembed_local_niti = BashOperator(
        task_id='reembed_local_ollama',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/embed_and_store_raw.py',
    )

    reembed_cloud_niti = BashOperator(
        task_id='reembed_supabase_cloud',
        bash_command=f'cd {PROJECT_DIR} && python rag/ingestion/embed_supabase_raw.py',
    )

    fetch_niti >> rechunk_niti >> [reembed_local_niti, reembed_cloud_niti]
