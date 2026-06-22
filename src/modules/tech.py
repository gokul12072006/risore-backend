from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_tech(query: str) -> str:
    memory.add_history("tech", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert full-stack developer and AI software architect. Provide highly accurate, optimized, and modern technical advice. Write clean, robust code with clear explanations. Format your response beautifully using markdown code blocks..
    {user_context}
    
    Context: {context}
    Question: {input}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
