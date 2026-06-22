from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from src.llm import get_llm
from src.vector_store import get_chroma_retriever

from src.web_search import get_realtime_context

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain(language="English", custom_prompt=None):
    """Creates the RAG chain using LCEL syntax."""
    llm = get_llm()
    retriever = get_chroma_retriever()
    
    def augment_context(inputs):
        if isinstance(inputs, dict):
            query = inputs["input"]
        else:
            query = inputs
            
        # 1. Get local knowledge
        docs = retriever.invoke(query)
        context = format_docs(docs)
        
        # 2. Get real-time knowledge if needed
        realtime_context = get_realtime_context(query)
        if realtime_context:
            context += realtime_context
            
        return context

    if language == "Tamil":
        system_prompt = """நீங்கள் ரைசோர் 1.0 (Risore 1.0), ஒரு அதிநவீன, திறமையான செயற்கை நுண்ணறிவு உதவியாளர்.
        கீழே கொடுக்கப்பட்டுள்ள தகவல்களை (Context) பயன்படுத்தி பயனரின் கேள்விக்கு பதிலளிக்கவும்.
        பயனர் சாதாரணமாக பேசினால் (உதாரணமாக: 'ஹலோ', 'எப்படி இருக்கிறீர்கள்'), இயல்பாக பதிலளிக்கவும்.
        தகவல்களில் இல்லாத பொதுவான கேள்விகளுக்கு, உங்களின் அறிவாற்றலை பயன்படுத்தி தெளிவாக பதிலளிக்கவும்.
        மிகவும் நட்பாகவும், துல்லியமாகவும், மனிதரைப் போலவும் உரையாடவும். "தகவல் இல்லை" என்று இயந்திரத்தனமாக கூற வேண்டாம்.
        
        Previous Conversation History:
        {history}
        
        Context: {context}
        
        Question: {input}
        
        Answer:"""
    else:
        system_prompt = """You are Risore 1.0, an advanced, highly capable open-source AI assistant. 
        You have access to a local knowledge base (provided as Context). 
        If the user asks a question covered by the Context, prioritize using that information.
        If the user is simply chatting (e.g., saying hello, asking how you are, expressing frustration), respond conversationally, empathetically, and naturally.
        If the user asks a general knowledge question or requests a task (like writing code) not in the Context, use your inherent AI knowledge to help them perfectly.
        Be extremely friendly, confident, and act like a premium world-class AI. Never say "I don't have the information" for casual chats.
        
        Previous Conversation History:
        {history}
        
        Context: {context}
        
        Question: {input}
        
        Answer:"""
        
    if custom_prompt:
        system_prompt = custom_prompt

    prompt = PromptTemplate.from_template(system_prompt)
    
    from langchain_core.runnables import RunnableLambda
    
    rag_chain = (
        {
            "context": RunnableLambda(augment_context),
            "input": lambda x: x["input"] if isinstance(x, dict) else x,
            "history": lambda x: x.get("history", "") if isinstance(x, dict) else ""
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def answer_question(question, language="English", custom_prompt=None, history=""):
    """Generates an answer using the RAG pipeline."""
    try:
        chain = get_rag_chain(language, custom_prompt)
        return chain.invoke({"input": question, "history": history})
    except Exception as e:
        return f"Error: Ensure Ollama is running and documents are indexed. Details: {str(e)}"
