"""
Embeds chunks using Ollama (containerized, reached via OLLAMA_BASE_URL)
into the 'india_policy_docs' collection - raw psycopg2 version for use
inside the Airflow container (avoids langchain-postgres/SQLAlchemy conflict).
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(__file__))
from embed_raw import run

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
CONNECTION_STRING = "postgresql://airflow:airflow@postgres:5432/airflow"

def ollama_embed_batch(texts):
    vectors = []
    for text in texts:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=120
        )
        response.raise_for_status()
        vectors.append(response.json()["embedding"])
    return vectors

if __name__ == "__main__":
    run("india_policy_docs", ollama_embed_batch, CONNECTION_STRING)
