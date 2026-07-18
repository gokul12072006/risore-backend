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
    Hybrid LLM Router with Auto-Failover:
    If an API fails during generation (e.g., rate limit, credit issue),
    it silently falls back to the next available provider.
    
    1. OpenRouter (Access to DeepSeek, Llama, Qwen, etc. for free/low cost)
    2. Google Gemini (Generous free tier)
    3. DeepSeek Direct API
    4. Groq (Lightning-fast)
    5. Ollama (100% private, local-first)
    6. Free Cloud Cluster Fallback
    """
    from src.config import LLM_MODEL

    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    available_llms = []

    # 1. OpenRouter API
    if openrouter_api_key and openrouter_api_key != "your_openrouter_api_key_here":
        try:
            from langchain_openai import ChatOpenAI
            # Using a strictly free model on OpenRouter to permanently avoid credit errors
            available_llms.append(
                ChatOpenAI(
                    model="google/gemini-2.0-flash-exp:free",
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.6,
                    max_tokens=2048,
                )
            )
        except Exception as e:
            print(f"OpenRouter init failed: {e}")

    # 2. Google Gemini API
    if gemini_api_key and gemini_api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            available_llms.append(
                ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=gemini_api_key,
                    temperature=0.6,
                )
            )
        except Exception as e:
            print(f"Gemini init failed: {e}")

    # 3. DeepSeek API
    if deepseek_api_key and deepseek_api_key != "your_deepseek_api_key_here":
        try:
            from langchain_openai import ChatOpenAI
            available_llms.append(
                ChatOpenAI(
                    model="deepseek-chat",
                    api_key=deepseek_api_key,
                    base_url="https://api.deepseek.com",
                    temperature=0.6,
                )
            )
        except Exception as e:
            print(f"DeepSeek init failed: {e}")

    # 4. Cloud: Groq API
    if groq_api_key and groq_api_key != "your_free_groq_api_key_here":
        try:
            from langchain_groq import ChatGroq
            # Reverting to Llama 3.3 for stability since Groq decommissioned the R1 endpoint temporarily
            available_llms.append(
                ChatGroq(
                    model="llama-3.3-70b-versatile", temperature=0.6, api_key=groq_api_key
                )
            )
        except Exception:
            pass

    # 5. Local: Ollama (Qwen 3B)
    try:
        import requests
        from langchain_community.llms import Ollama
        # Quick check if Ollama is alive
        res = requests.get("http://localhost:11434/", timeout=1)
        if res.status_code == 200:
            available_llms.append(Ollama(model=LLM_MODEL))
    except Exception:
        pass

    # 6. Cloud Fallback: Free Cluster
    available_llms.append(UltimateFreeCloudLLM())

    # Build the fallback chain
    primary_llm = available_llms[0]
    if len(available_llms) > 1:
        # If the primary fails at runtime, silently try the fallbacks in order
        return primary_llm.with_fallbacks(available_llms[1:])
    
    return primary_llm
