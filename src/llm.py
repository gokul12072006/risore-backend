import os
from typing import Any, List, Optional
import concurrent.futures

import g4f
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage
from pydantic import Field

# Load environment variables from .env file
load_dotenv()


class HybridRouter(SimpleChatModel):
    available_llms: List[Any] = Field(default_factory=list)

    def _call(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any
    ) -> str:
        last_error = ""
        for i, llm in enumerate(self.available_llms):
            try:
                response = llm.invoke(messages)
                if hasattr(response, 'content'):
                    return str(response.content)
                return str(response)
            except Exception as e:
                last_error = str(e)
                print(f"Fallback level {i} ({type(llm).__name__}) failed: {last_error}")
                continue
                
        return f"All AI providers are currently unavailable or rate-limited. Last error: {last_error}"

    @property
    def _llm_type(self) -> str:
        return "hybrid_router"


class UltimateFreeCloudLLM(SimpleChatModel):
    def _call(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any
    ) -> str:
        prompt = "\n".join([m.content for m in messages if hasattr(m, 'content') and isinstance(m.content, str)])
        def run_g4f():
            return g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=[{"role": "user", "content": prompt}],
                timeout=45,  # generous timeout for the cloud cluster to try all routes
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_g4f)
                response = future.result()
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
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    omniroute_base_url = os.getenv("OMNIROUTE_BASE_URL")
    omniroute_api_key = os.getenv("OMNIROUTE_API_KEY", "omniroute")

    available_llms = []

    # 0. OmniRoute API (290+ Providers, unified gateway)
    if omniroute_base_url:
        try:
            from langchain_openai import ChatOpenAI
            available_llms.append(
                ChatOpenAI(
                    model=os.getenv("OMNIROUTE_MODEL", "auto"),
                    api_key=omniroute_api_key,
                    base_url=omniroute_base_url,
                    temperature=0.6,
                )
            )
        except Exception as e:
            print(f"OmniRoute init failed: {e}")


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

    # 3.5 Nvidia NIM API (Free Tier for Llama 3 / Nemotron)
    if nvidia_api_key and nvidia_api_key != "your_nvidia_api_key_here":
        try:
            from langchain_openai import ChatOpenAI
            available_llms.append(
                ChatOpenAI(
                    model=os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct"),
                    api_key=nvidia_api_key,
                    base_url="https://integrate.api.nvidia.com/v1",
                    temperature=0.6,
                )
            )
        except Exception as e:
            print(f"Nvidia init failed: {e}")

    # 4. Cloud: Groq API
    if groq_api_key and groq_api_key != "your_free_groq_api_key_here":
        try:
            from langchain_groq import ChatGroq
            available_llms.append(
                ChatGroq(
                    model="qwen/qwen3.6-27b", temperature=0.6, api_key=groq_api_key
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

    # Build the bulletproof hybrid router
    return HybridRouter(available_llms=available_llms)
