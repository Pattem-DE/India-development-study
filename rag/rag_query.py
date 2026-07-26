from langchain_postgres import PGVector
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from domain_terms import expand_query
from embeddings_provider import get_embeddings
from llm_provider import get_llm

import os

# Local mode uses local Docker Postgres; cloud mode uses Supabase
# (Streamlit Community Cloud can't reach a local Docker container)
LOCAL_CONNECTION_STRING = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"
SUPABASE_CONNECTION_STRING = os.environ.get("SUPABASE_DB_URL", "").replace(
    "postgresql://", "postgresql+psycopg2://"
)

embeddings, using_ollama = get_embeddings(return_mode=True)
CONNECTION_STRING = LOCAL_CONNECTION_STRING if using_ollama else SUPABASE_CONNECTION_STRING

# Different embedding models produce incompatible vector spaces - each
# needs its own collection, embedded with that same model
COLLECTION_NAME = "india_policy_docs" if using_ollama else "india_policy_docs_fallback"

vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=CONNECTION_STRING,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

llm = get_llm()

prompt_template = """Use the following context from Indian government policy documents to answer the question.

Structure your answer in exactly this format:

**What the documents show:** State the specific facts, numbers, schemes, and
programs found in the context that relate to the question, citing which
document each comes from. Be direct and specific - use real numbers and names,
not vague summaries.

**Gap:** Only include this section if the documents don't fully answer the
question as asked. State plainly what specific information is missing, in
one or two sentences. Skip this section entirely if the documents fully
answer the question.

Never fabricate information that isn't in the context. Be careful with dates -
if a number is tied to a different year than the one asked about, say so
explicitly rather than implying it answers the question as asked.

Context:
{context}

Question: {question}

Answer:"""

prompt = PromptTemplate.from_template(prompt_template)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Modern LCEL RAG chain - retrieves docs, formats context, generates answer,
# while still returning the source documents for citation
rag_chain_from_docs = (
    {
        "context": lambda x: format_docs(x["context"]),
        "question": lambda x: x["question"],
    }
    | prompt
    | llm
    | StrOutputParser()
)

rag_chain = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer=rag_chain_from_docs)


def ask(question):
    expanded_question = expand_query(question)
    if expanded_question != question:
        print(f"[Query expanded to: {expanded_question}]")
    result = rag_chain.invoke(expanded_question)
    print(f"\nQ: {question}\n")
    print(f"A: {result['answer']}\n")
    sources = set(doc.metadata['source_file'] for doc in result['context'])
    print("Sources:", sources)
    print("=" * 80)

if __name__ == "__main__":
    ask("What specific milestones or targets has India outlined for zero-emission vehicles and charging infrastructure by 2030?")

    ask("How did central budget allocations for public health change in recent Union Budgets?")
