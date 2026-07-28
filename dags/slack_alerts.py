"""
Shared Slack alerting callback for all Airflow DAGs in this project.
Posts a message to Slack whenever a task fails, including the DAG name,
task name, and a link to the Airflow logs for that run.
"""

import os
import requests


def slack_failure_alert(context):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set - skipping Slack alert")
        return

    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    execution_date = context['execution_date']
    log_url = context['task_instance'].log_url

    message = {
        "text": (
            f"🔴 *Airflow Task Failed*\n"
            f"*DAG:* {dag_id}\n"
            f"*Task:* {task_id}\n"
            f"*Time:* {execution_date}\n"
            f"*Logs:* {log_url}"
        )
    }

    try:
        requests.post(webhook_url, json=message, timeout=10)
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")
