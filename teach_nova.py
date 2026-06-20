import os
import sys

# Ensure src modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.document_processor import load_document, chunk_documents
from src.vector_store import create_or_update_chroma

KNOWLEDGE_DIR = "knowledge_base"

def ingest_knowledge():
    print(f"Starting to teach Nova from {KNOWLEDGE_DIR}...")
    
    if not os.path.exists(KNOWLEDGE_DIR):
        print("Knowledge base directory not found.")
        return
    
    all_chunks = []
    for filename in os.listdir(KNOWLEDGE_DIR):
        file_path = os.path.join(KNOWLEDGE_DIR, filename)
        if os.path.isfile(file_path):
            try:
                print(f"Reading and absorbing: {filename}...")
                docs = load_document(file_path)
                chunks = chunk_documents(docs)
                all_chunks.extend(chunks)
                print(f"  -> Extracted {len(chunks)} chunks of knowledge.")
            except Exception as e:
                print(f"  -> Failed to absorb {filename}: {e}")
                
    if all_chunks:
        print(f"Saving {len(all_chunks)} total knowledge chunks to Nova's brain (ChromaDB)...")
        create_or_update_chroma(all_chunks)
        print("Knowledge successfully integrated! Nova 1.0 is now smarter.")
    else:
        print("No new knowledge found to integrate.")

if __name__ == "__main__":
    ingest_knowledge()
