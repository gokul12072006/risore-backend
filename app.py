import gradio as gr
import os
import shutil
from src.config import DATA_DIR, LLM_MODEL, SUPPORTED_LANGUAGES
from src.document_processor import load_document, chunk_documents
from src.vector_store import create_or_update_chroma
from src.rag_pipeline import answer_question

def process_uploaded_file(file):
    if file is None:
        return "No file uploaded."
    
    try:
        # Save file to the integrated Storage directory (e.g., Google Drive if mapped)
        file_name = os.path.basename(file.name)
        file_path = os.path.join(DATA_DIR, file_name)
        shutil.copy(file.name, file_path)
        
        # Extract, chunk, and embed
        docs = load_document(file_path)
        chunks = chunk_documents(docs)
        create_or_update_chroma(chunks)
        
        return f"Successfully processed '{file_name}' and added it to Nova's knowledge base."
    except Exception as e:
        return f"Error processing file: {str(e)}"

def chat(message, history, language):
    """Chatbot function integrating user message and history."""
    response = answer_question(message, language)
    return response

# Custom CSS for a beautiful local UI
custom_css = """
#component-0 { font-family: 'Inter', sans-serif; }
.gradio-container { background-color: #0f172a; color: #f8fafc; }
.md h1, .md h2, .md h3 { color: #38bdf8; }
.feedback-box { padding: 10px; border-radius: 8px; background-color: #1e293b; border: 1px solid #334155; }
"""

with gr.Blocks(title="Nova 1.0 - Open Source AI") as app:
    gr.Markdown("# 🚀 Nova 1.0 - Open Source Local AI Assistant")
    gr.Markdown(f"**Current Model:** `{LLM_MODEL}` | **Storage Base:** `{DATA_DIR}` (Map this to Google Drive for Cloud Storage)")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🧠 Teach Nova (Knowledge Base)")
            gr.Markdown("Upload files to integrate them into Nova's memory. Supported: `.pdf`, `.docx`, `.txt`, `.md`.")
            
            file_input = gr.File(label="Upload Document")
            upload_btn = gr.Button("Teach AI", variant="primary")
            status_output = gr.Textbox(label="Status", interactive=False)
            
            upload_btn.click(process_uploaded_file, inputs=file_input, outputs=status_output)
            
            gr.Markdown("### ⚙️ Settings")
            lang_radio = gr.Radio(choices=SUPPORTED_LANGUAGES, value="English", label="Response Language")
            
        with gr.Column(scale=2):
            chatbot_interface = gr.ChatInterface(
                fn=chat,
                additional_inputs=[lang_radio],
                title="Chat with Nova 1.0",
                description="Ask questions about the uploaded documents."
            )

if __name__ == "__main__":
    print("Starting Nova 1.0 AI Assistant...")
    print("Make sure you have Ollama running locally with the selected model.")
    app.launch(server_name="0.0.0.0", server_port=7860, share=True)