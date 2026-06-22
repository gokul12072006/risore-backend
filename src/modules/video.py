from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_video(query: str) -> str:
    memory.add_history("video", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert video creation and content strategy assistant. Help with script writing, storyboarding, editing suggestions, and social media content strategies (YouTube, TikTok, etc.). Be creative and trend-aware..
    {user_context}
    
    Context: {context}
    Question: {input}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
