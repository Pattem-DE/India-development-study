"""
Dual-mode embeddings provider.

Local development: uses Ollama's nomic-embed-text (matches what was used
to build the original pgvector index, best quality for this project).

Cloud/fallback: uses sentence-transformers (all-MiniLM-L6-v2) - a small,
free, local Python model that runs without any external service or API
key, suitable for Streamlit Community Cloud's free tier.

Note: switching embedding models means previously-stored vectors won't be
directly comparable to new query vectors (different models produce
different vector spaces). For a true cloud deployment, the collection
would need to be re-embedded once with the fallback model. This module
just provides the loading logic; re-embedding is a separate step.
"""

import os

def get_embeddings(force_fallback=False):
    if not force_fallback:
        try:
            from langchain_ollama import OllamaEmbeddings
            import requests
            # Quick check that Ollama is actually reachable before committing to it
            requests.get("http://localhost:11434/api/tags", timeout=2)
            print("Using Ollama embeddings (nomic-embed-text) - local mode")
            return OllamaEmbeddings(model="nomic-embed-text")
        except Exception:
            print("Ollama not reachable - falling back to sentence-transformers")

    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("Using sentence-transformers embeddings (all-MiniLM-L6-v2) - cloud mode")
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
