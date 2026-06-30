import os
from typing import Any, List, Optional

import g4f
from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM

# Load environment variables from .env file
load_dotenv()


class UltimateFreeCloudLLM(LLM):
    def _call(
        self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any
    ) -> str:
        # Create a massive load-balanced cluster of free providers.
        # It automatically routes your prompt to the next available server if one is overloaded.
        provider_cluster = g4f.Provider.RetryProvider(
            [
                g4f.Provider.HuggingChat,
                g4f.Provider.HuggingSpace,
                g4f.Provider.BlackboxPro,
                g4f.Provider.DeepInfra,
                g4f.Provider.PollinationsAI,
            ]
        )

        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                provider=provider_cluster,
                messages=[{"role": "user", "content": prompt}],
                timeout=45,  # generous timeout for the cloud cluster to try all routes
            )
            if response:
                return response
        except Exception as e:
            return f"All Free Cloud nodes are temporarily overloaded. Error: {str(e)}"

        return "The Cloud AI cluster is heavily overloaded right now. Please wait 10 seconds and try again."

    @property
    def _llm_type(self) -> str:
        return "ultimate_free_cloud"


def get_llm():
    """
    Hybrid LLM Router:
    1. If a GROQ_API_KEY is found, it uses the lightning-fast Groq API.
    2. If Ollama is running locally, it uses Qwen 3B (100% private, local-first).
    3. If neither is available, it falls back to the keyless Free Cloud Cluster.
    """
    from src.config import LLM_MODEL

    api_key = os.getenv("GROQ_API_KEY")

    # 1. Cloud: Groq API
    if api_key and api_key != "your_free_groq_api_key_here":
        try:
            from langchain_groq import ChatGroq

            # We use DeepSeek R1 to enable native "overthinking" (metacognition)
            return ChatGroq(
                model="deepseek-r1-distill-llama-70b", temperature=0.6, api_key=api_key
            )
        except Exception:
            pass

    # 2. Local: Ollama (Qwen 3B)
    try:
        import requests
        from langchain_community.llms import Ollama

        # Quick check if Ollama is alive
        res = requests.get("http://localhost:11434/", timeout=1)
        if res.status_code == 200:
            return Ollama(model=LLM_MODEL)
    except Exception:
        pass

    # 3. Cloud Fallback: Free Cluster
    return UltimateFreeCloudLLM()
