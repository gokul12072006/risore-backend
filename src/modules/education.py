from src.modules.memory import memory
from src.rag_pipeline import answer_question


def handle_education(query: str) -> str:
    memory.add_history("education", query)
    user_context = memory.get_context()

    prompt = f"""You are Risore, an expert advanced learning companion. Help with concept explanations, study plans, and learning roadmaps across academic subjects. Be patient, pedagogical, and encourage deep understanding..
    {user_context}
    
    Context: {{context}}
    Question: {{input}}
    Answer:"""

    return answer_question(query, custom_prompt=prompt)
