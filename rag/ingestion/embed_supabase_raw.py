"""
Embeds chunks using sentence-transformers into Supabase's
'india_policy_docs_fallback' collection - raw psycopg2 version for use
inside the Airflow container.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from embed_raw import run

CONNECTION_STRING = os.environ["SUPABASE_DB_URL"]

def get_st_embed_fn():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed_batch(texts):
        return model.encode(texts).tolist()

    return embed_batch

if __name__ == "__main__":
    embed_fn = get_st_embed_fn()
    run("india_policy_docs_fallback", embed_fn, CONNECTION_STRING)
