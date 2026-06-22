from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_recommendation(query: str) -> str:
    memory.add_history("recommendation", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert product analyst and recommendation system. Generate recommendations based on budget, value for money, and reliability. Output pros and cons, feature comparison tables, and the best choice explanation..
    {user_context}
    
    Context: {context}
    Question: {input}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
