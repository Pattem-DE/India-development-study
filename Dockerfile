FROM apache/airflow:2.9.1

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Airflow 2.9.1 requires SQLAlchemy 1.x - some RAG packages (langchain-postgres
# and its dependencies) pull in SQLAlchemy 2.x, which breaks Airflow's own ORM.
# Pin it back down, installed last so nothing can silently upgrade it again.
RUN pip install --no-cache-dir "sqlalchemy>=1.4.0,<2.0.0"
