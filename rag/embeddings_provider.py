"""
Dual-mode embeddings provider.

Local development: uses Ollama's nomic-embed-text (matches what was used
to build the primary pgvector collection 'india_policy_docs').

Cloud/fallback: uses sentence-transformers (all-MiniLM-L6-v2) - matches
the separate 'india_policy_docs_fallback' collection, since different
embedding models produce incompatible vector spaces and each needs its
own matching collection.
"""

import os

def get_embeddings(force_fallback=False, return_mode=False):
    if not force_fallback:
        try:
            from langchain_ollama import OllamaEmbeddings
            import requests
            requests.get("http://localhost:11434/api/tags", timeout=2)
            print("Using Ollama embeddings (nomic-embed-text) - local mode")
            emb = OllamaEmbeddings(model="nomic-embed-text")
            return (emb, True) if return_mode else emb
        except Exception:
            print("Ollama not reachable - falling back to sentence-transformers")

    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("Using sentence-transformers embeddings (all-MiniLM-L6-v2) - cloud mode")
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return (emb, False) if return_mode else emb
