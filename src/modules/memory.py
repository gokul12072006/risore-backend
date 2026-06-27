import json
import os

from src.config import BASE_DIR

MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")


class MemorySystem:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        if not os.path.exists(self.memory_file):
            self.save_memory({"user_profile": {}, "history": [], "preferences": {}})

    def load_memory(self):
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"user_profile": {}, "history": [], "preferences": {}}

    def save_memory(self, data):
        with open(self.memory_file, "w", encoding="utf-8") as f:
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
        context = "User Preferences:\n"
        for k, v in prefs.items():
            context += f"- {k}: {v}\n"
        return context


memory = MemorySystem()
