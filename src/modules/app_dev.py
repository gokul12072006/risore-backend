from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_app_dev(query: str) -> str:
    memory.add_history("app_dev", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert mobile and software development expert. Provide guidance on Flutter, React Native, UI/UX best practices, and backend development. Give structured, architectural advice..
    {user_context}
    
    Context: {context}
    Question: {input}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
