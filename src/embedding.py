import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from src.config import EMBEDDING_MODEL


def get_embedding_model():
    """Initializes the completely free Hugging Face API embedding model."""
    hf_token = os.environ.get("HUGGINGFACE_API_KEY")
    if not hf_token:
        print("WARNING: HUGGINGFACE_API_KEY is not set. Cloud embeddings will fail.")
        
    return HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=hf_token,
    )
