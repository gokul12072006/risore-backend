import os

modules_dir = os.path.join("d:/project/Model Risore", "src", "modules")
os.makedirs(modules_dir, exist_ok=True)

# Memory module
memory_code = """import os
import json
from src.config import BASE_DIR

MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

class MemorySystem:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        if not os.path.exists(self.memory_file):
            self.save_memory({"user_profile": {}, "history": [], "preferences": {}})

    def load_memory(self):
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"user_profile": {}, "history": [], "preferences": {}}

    def save_memory(self, data):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def update_preference(self, key, value):
        data = self.load_memory()
        data["preferences"][key] = value
        self.save_memory(data)

    def add_history(self, domain, query):
        data = self.load_memory()
        data["history"].append({"domain": domain, "query": query})
        if len(data["history"]) > 100:  # Keep last 100
            data["history"].pop(0)
        self.save_memory(data)
        
    def get_context(self):
        data = self.load_memory()
        prefs = data.get("preferences", {})
        if not prefs:
            return ""
        context = "User Preferences:\\n"
        for k, v in prefs.items():
            context += f"- {k}: {v}\\n"
        return context

memory = MemorySystem()
"""
with open(os.path.join(modules_dir, "memory.py"), "w") as f: f.write(memory_code)


def gen_module(name, role_desc):
    return f'''from src.rag_pipeline import answer_question
from src.modules.memory import memory

def handle_{name}(query: str) -> str:
    memory.add_history("{name}", query)
    user_context = memory.get_context()
    
    prompt = f"""You are Risore, an expert {role_desc}.
    {{user_context}}
    
    Context: {{context}}
    Question: {{input}}
    Answer:"""
    
    return answer_question(query, custom_prompt=prompt)
'''

modules_info = {
    "fitness": "science-based fitness and nutrition assistant. Provide highly accurate, scientifically-backed fitness advice. Avoid pseudoscience. Structure the answer logically with clear reasoning. Output workouts or diet plans in a beautiful format.",
    "tech": "full-stack developer and AI software architect. Provide highly accurate, optimized, and modern technical advice. Write clean, robust code with clear explanations. Format your response beautifully using markdown code blocks.",
    "daily_life": "daily-life assistant. Help the user with daily planning, reminders, habit building, goal tracking, and decision assistance. Be highly empathetic and practical.",
    "productivity": "productivity engine. Provide actionable advice on task planning, daily schedules, project management, and goal tracking. Be concise and goal-oriented.",
    "recommendation": "product analyst and recommendation system. Generate recommendations based on budget, value for money, and reliability. Output pros and cons, feature comparison tables, and the best choice explanation.",
    "education": "advanced learning companion. Help with concept explanations, study plans, and learning roadmaps across academic subjects. Be patient, pedagogical, and encourage deep understanding.",
    "app_dev": "mobile and software development expert. Provide guidance on Flutter, React Native, UI/UX best practices, and backend development. Give structured, architectural advice.",
    "video": "video creation and content strategy assistant. Help with script writing, storyboarding, editing suggestions, and social media content strategies (YouTube, TikTok, etc.). Be creative and trend-aware."
}

for mod, role in modules_info.items():
    with open(os.path.join(modules_dir, f"{mod}.py"), "w") as f:
        f.write(gen_module(mod, role))

# __init__.py
with open(os.path.join(modules_dir, "__init__.py"), "w") as f:
    f.write("")
