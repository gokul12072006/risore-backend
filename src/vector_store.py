import os
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from src.embedding import get_embedding_model
from src.config import CHROMA_DB_DIR, FAISS_DB_DIR

def create_or_update_chroma(chunks):
    """Stores document chunks into ChromaDB."""
    embeddings = get_embedding_model()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    return vectorstore

def get_chroma_retriever():
    """Retrieves context from ChromaDB."""
    embeddings = get_embedding_model()
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR, 
        embedding_function=embeddings
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})

def create_or_update_faiss(chunks):
    """Stores document chunks into FAISS."""
    embeddings = get_embedding_model()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_DB_DIR)
    return vectorstore

def get_faiss_retriever():
    """Retrieves context from FAISS database."""
    embeddings = get_embedding_model()
    index_path = os.path.join(FAISS_DB_DIR, "index.faiss")
    if os.path.exists(index_path):
        vectorstore = FAISS.load_local(
            FAISS_DB_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    return None
