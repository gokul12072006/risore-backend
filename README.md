# Model Nova 1.0

An advanced, completely free, and open-source local AI assistant designed to be highly capable, lightning-fast, and secure.

## 🚀 Features
- **Hybrid Cloud Intelligence**: Uses the lightning-fast Groq API (Llama-3.3-70B) for near-instant responses. 
- **RAG Memory System**: Powered by `ChromaDB`. You can "teach" Nova by uploading documents (PDF, TXT, DOCX) to its permanent vector memory.
- **Bilingual Capability**: Fully capable of conversing, coding, and reasoning in both English and Tamil.
- **Zero-Cost Deployment**: Built exclusively with open-source and free tools. Absolutely no paid monthly subscriptions required.

## 🛠️ Installation & Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate the environment: `.\venv\Scripts\activate`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Add your free API key to the `.env` file: `GROQ_API_KEY=gsk_...`
5. Start the AI assistant: `python app.py`

## 🧠 Teaching Nova
To teach Nova new skills or provide it with private data:
1. Place your text, PDF, or markdown files into the `knowledge_base/` folder.
2. Run the training script: `python teach_nova.py`
3. The data is permanently embedded into the local `chroma_db` folder. Nova will automatically use this knowledge in future conversations.

---
*Safeguarded and Architected by Antigravity.*
