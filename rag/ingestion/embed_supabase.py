"""
Embeds document chunks into Supabase's cloud-hosted pgvector, using
sentence-transformers (matches the embedding model the deployed Streamlit
app will use in cloud/fallback mode). This is the actual data source for
the live deployed dashboard's RAG tab.
"""

import json
import os
import time
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "..", "chunks.jsonl")
CONNECTION_STRING = os.environ["SUPABASE_DB_URL"]
COLLECTION_NAME = "india_policy_docs_fallback"
BATCH_SIZE = 50

def load_chunks():
    docs = []
    with open(CHUNKS_FILE) as f:
        for line in f:
            item = json.loads(line)
            docs.append(Document(
                page_content=item["content"],
                metadata={
                    "source_file": item["source_file"],
                    "category": item["category"],
                    "chunk_index": item["chunk_index"]
                }
            ))
    return docs

def run():
    print("Loading chunks...")
    docs = load_chunks()
    total = len(docs)
    print(f"Loaded {total} chunks")

    print("Initializing sentence-transformers embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("Creating collection on Supabase...")
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )
    vectorstore.delete_collection()
    vectorstore.create_collection()

    print(f"\nEmbedding in batches of {BATCH_SIZE}...\n")
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        batch_start = time.time()
        vectorstore.add_documents(batch)
        elapsed_batch = time.time() - batch_start
        elapsed_total = time.time() - start_time
        done = min(i + BATCH_SIZE, total)
        pct = (done / total) * 100
        rate = done / elapsed_total if elapsed_total > 0 else 0
        eta_seconds = (total - done) / rate if rate > 0 else 0
        print(f"  [{done}/{total}] {pct:.1f}% | batch took {elapsed_batch:.1f}s | ETA: {eta_seconds/60:.1f} min")

    print(f"\nDone. {total} chunks embedded on Supabase collection '{COLLECTION_NAME}'")
    print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    run()
