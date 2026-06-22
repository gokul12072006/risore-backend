from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_productivity(query: str) -> str:
    memory.add_history("productivity", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert productivity engine. Provide actionable advice on task planning, daily schedules, project management, and goal tracking. Be concise and goal-oriented..
    {user_context}
    
    Context: {context}
    Question: {input}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
