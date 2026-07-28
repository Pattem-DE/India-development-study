"""
Dual-mode embeddings provider.

Local development (WSL2 host): uses Ollama's nomic-embed-text at
localhost:11434 (matches 'india_policy_docs' collection).

Inside Airflow containers: Ollama runs as its own containerized service
(rootless Docker isolates containers from arbitrary host services), so
OLLAMA_BASE_URL is set to http://ollama:11434 in docker-compose.yaml and
picked up here automatically.

Cloud/fallback: uses sentence-transformers (all-MiniLM-L6-v2) - matches
the separate 'india_policy_docs_fallback' collection.
"""

import os

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

def get_embeddings(force_fallback=False, return_mode=False):
    if not force_fallback:
        try:
            from langchain_ollama import OllamaEmbeddings
            import requests
            requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
            print(f"Using Ollama embeddings (nomic-embed-text) at {OLLAMA_BASE_URL} - local mode")
            emb = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
            return (emb, True) if return_mode else emb
        except Exception:
            print("Ollama not reachable - falling back to sentence-transformers")

    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("Using sentence-transformers embeddings (all-MiniLM-L6-v2) - cloud mode")
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return (emb, False) if return_mode else emb
