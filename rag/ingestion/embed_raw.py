"""
Lightweight document embedding using raw psycopg2 + pgvector SQL,
deliberately avoiding langchain-postgres.

Why: langchain-postgres requires SQLAlchemy >=2.0 (uses RowMapping),
but Airflow 2.9.1 requires SQLAlchemy <2.0 - a genuine, unresolvable
version conflict when both need to coexist in the same Python
environment (the Airflow container). This script uses the same
database schema langchain-postgres creates, so it stays compatible
with rag_query.py's retrieval code, which continues to use
langchain-postgres in the separate WSL2 venv (no conflict there,
since it's not sharing an environment with Airflow's own core).
"""

import json
import os
import sys
import time
import uuid
import psycopg2
from psycopg2.extras import Json

CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "..", "chunks.jsonl")
BATCH_SIZE = 20

def load_chunks():
    chunks = []
    with open(CHUNKS_FILE) as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks

def get_or_create_collection(cur, conn, collection_name):
    """
    Atomic get-or-create using ON CONFLICT to avoid a race condition where
    two concurrent runs both see 'no existing collection' and each create
    a duplicate row with a different UUID - this happened when multiple
    Airflow DAG runs executed simultaneously, causing embedded chunks to
    scatter across multiple collection UUIDs under the same name.
    """
    new_uuid = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO langchain_pg_collection (uuid, name, cmetadata)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        """,
        (new_uuid, collection_name, Json({}))
    )
    conn.commit()

    # Whether we just inserted it or it already existed, fetch the
    # authoritative UUID for this name
    cur.execute(
        "SELECT uuid FROM langchain_pg_collection WHERE name = %s",
        (collection_name,)
    )
    return cur.fetchone()[0]

def embed_batch(texts, embedding_fn):
    """embedding_fn should return a list of vectors for a list of texts"""
    return embedding_fn(texts)

def run(collection_name, embedding_fn, connection_string):
    print(f"Embedding into collection: {collection_name}")
    chunks = load_chunks()
    total = len(chunks)
    print(f"Loaded {total} chunks")

    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    collection_id = get_or_create_collection(cur, conn, collection_name)

    # Clear existing embeddings for this collection - fresh start each run
    cur.execute(
        "DELETE FROM langchain_pg_embedding WHERE collection_id = %s",
        (collection_id,)
    )
    conn.commit()

    print(f"Collection ID: {collection_id}")
    print(f"Embedding in batches of {BATCH_SIZE}...\n")
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["content"] for c in batch]

        vectors = embed_batch(texts, embedding_fn)

        for chunk, vector in zip(batch, vectors):
            doc_id = str(uuid.uuid4())
            metadata = {
                "source_file": chunk["source_file"],
                "category": chunk["category"],
                "chunk_index": chunk["chunk_index"]
            }
            cur.execute(
                """
                INSERT INTO langchain_pg_embedding
                    (id, collection_id, embedding, document, cmetadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (doc_id, collection_id, vector, chunk["content"], Json(metadata))
            )
        conn.commit()

        done = min(i + BATCH_SIZE, total)
        pct = (done / total) * 100
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(f"  [{done}/{total}] {pct:.1f}% | ETA: {eta/60:.1f} min")

    cur.close()
    conn.close()
    print(f"\nDone. {total} chunks embedded in '{collection_name}'")
    print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")
