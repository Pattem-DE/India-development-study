import json
import os
import time
from langchain_community.embeddings import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "..", "chunks.jsonl")
CONNECTION_STRING = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"
COLLECTION_NAME = "india_policy_docs"
BATCH_SIZE = 20

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

    print("Initializing Ollama embeddings (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    print("Creating empty collection first...")
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

    print(f"\nDone. {total} chunks embedded and stored in pgvector collection '{COLLECTION_NAME}'")
    print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    run()
