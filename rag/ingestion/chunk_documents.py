import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "policy_docs")
CHUNKS_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "chunks.jsonl")

def extract_pdf_text(filepath):
    reader = PdfReader(filepath)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def get_all_pdfs():
    pdfs = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith(".pdf"):
                category = os.path.basename(root)  # e.g. "budget_speeches" or "niti_aayog"
                pdfs.append({"path": os.path.join(root, f), "filename": f, "category": category})
    return pdfs

def chunk_all():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    pdfs = get_all_pdfs()
    print(f"Found {len(pdfs)} PDFs to process\n")

    all_chunks = []
    for pdf in pdfs:
        print(f"Processing: {pdf['filename']}...")
        text = extract_pdf_text(pdf["path"])
        chunks = splitter.split_text(text)
        print(f"  -> {len(chunks)} chunks")

        for i, chunk_text in enumerate(chunks):
            # Skip low-value chunks: cover pages, headers, very short fragments
            # that add noise without real content
            if len(chunk_text.strip()) < 150:
                continue
            all_chunks.append({
                "content": chunk_text,
                "source_file": pdf["filename"],
                "category": pdf["category"],
                "chunk_index": i
            })

    import json
    with open(CHUNKS_OUTPUT, "w") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")

    print(f"\nTotal chunks created: {len(all_chunks)}")
    print(f"Saved to: {CHUNKS_OUTPUT}")

if __name__ == "__main__":
    chunk_all()
