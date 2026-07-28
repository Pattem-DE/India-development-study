from langchain_community.embeddings import OllamaEmbeddings
from langchain_postgres import PGVector

CONNECTION_STRING = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"
COLLECTION_NAME = "india_policy_docs"

embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=CONNECTION_STRING,
)

query = "What are India's targets for electric vehicle charging infrastructure?"
results = vectorstore.similarity_search(query, k=3)

print(f"Query: {query}\n")
for i, doc in enumerate(results):
    print(f"--- Result {i+1} (from {doc.metadata['source_file']}) ---")
    print(doc.page_content[:300])
    print()
