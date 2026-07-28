import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_query import rag_chain
from domain_terms import expand_query

app = FastAPI(title="India Policy RAG API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"service": "India Policy RAG API", "endpoints": ["/ask (POST)"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask_question(request: QueryRequest):
    expanded = expand_query(request.question)
    result = rag_chain.invoke(expanded)

    sources = list(set(doc.metadata['source_file'] for doc in result['context']))

    response = {
        "question": request.question,
        "answer": result['answer'],
        "sources": sources
    }

    if expanded != request.question:
        response["expanded_query"] = expanded

    return response
