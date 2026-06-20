import os

# Google Drive Integration / Storage Path
# For Google Colab: os.environ["NOVA_STORAGE_PATH"] = "/content/drive/MyDrive/Nova_DB"
BASE_DIR = os.getenv("NOVA_STORAGE_PATH", os.path.join(os.getcwd(), "nova_storage"))

DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
FAISS_DB_DIR = os.path.join(BASE_DIR, "faiss_db")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
os.makedirs(FAISS_DB_DIR, exist_ok=True)

# Recommended Lightweight Open-Source Models (Ollama)
# Options: qwen2.5:3b, gemma2:2b, llama3.2:3b
LLM_MODEL = os.getenv("NOVA_LLM_MODEL", "qwen2.5:3b")

# Embedding Model (Hugging Face - Fast & Free)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Supported Languages
SUPPORTED_LANGUAGES = ["English", "Tamil"]
