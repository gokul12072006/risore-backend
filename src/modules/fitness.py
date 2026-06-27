from src.modules.memory import memory
from src.rag_pipeline import answer_question


def handle_fitness(query: str) -> str:
    memory.add_history("fitness", query)
    user_context = memory.get_context()

    prompt = f"""You are Risore, an expert science-based fitness and nutrition assistant. Provide highly accurate, scientifically-backed fitness advice. Avoid pseudoscience. Structure the answer logically with clear reasoning. Output workouts or diet plans in a beautiful format..
    {user_context}
    
    Context: {{context}}
    Question: {{input}}
    Answer:"""

    return answer_question(query, custom_prompt=prompt)
