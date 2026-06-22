from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_daily_life(query: str) -> str:
    memory.add_history("daily_life", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert daily-life assistant. Help the user with daily planning, reminders, habit building, goal tracking, and decision assistance. Be highly empathetic and practical..
    {user_context}
    
    Context: {context}
    Question: {input}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
