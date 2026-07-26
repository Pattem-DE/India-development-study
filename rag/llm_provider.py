"""
Dual-mode LLM provider.

Local development: uses Ollama's llama3.2:3b (free, fully local, no API
key needed - the primary model this project was built and tested with).

Cloud/fallback: uses Groq's free hosted API (llama-3.1-8b-instant) - fast
inference, generous free tier, works from anywhere including Streamlit
Community Cloud where Ollama cannot run.
"""

import os

def get_llm(force_fallback=False):
    if not force_fallback:
        try:
            from langchain_ollama import OllamaLLM
            import requests
            requests.get("http://localhost:11434/api/tags", timeout=2)
            print("Using Ollama LLM (llama3.2:3b) - local mode")
            return OllamaLLM(model="llama3.2:3b", temperature=0)
        except Exception:
            print("Ollama not reachable - falling back to Groq")

    from langchain_groq import ChatGroq
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable not set. "
            "Get a free key at console.groq.com and set it before using cloud mode."
        )
    print("Using Groq LLM (llama-3.1-8b-instant) - cloud mode")
    return ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=api_key)
