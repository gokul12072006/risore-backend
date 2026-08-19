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
    
    1. Google Gemini (Generous free tier)
    2. SambaNova Cloud (Llama 3.1 405B - Free)
    3. GitHub Models (GPT-4o, Claude 3.5 - Free for GitHub users)
    4. DeepSeek Direct API
    5. Groq (Lightning-fast)
    6. Free Cloud Cluster Fallback (g4f)
    """
    from src.config import LLM_MODEL

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    sambanova_api_key = os.getenv("SAMBANOVA_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    available_llms = []

    # 1. Google Gemini API
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

    # 2. SambaNova Cloud (Free Llama 3.1 405B)
    if sambanova_api_key:
        try:
            from langchain_openai import ChatOpenAI
            available_llms.append(
                ChatOpenAI(
                    model="Meta-Llama-3.1-405B-Instruct",
                    api_key=sambanova_api_key,
                    base_url="https://api.sambanova.ai/v1",
                    temperature=0.6,
                )
            )
        except Exception as e:
            print(f"SambaNova init failed: {e}")

    # 3. GitHub Models (Free GPT-4o / Llama 3 for GitHub users)
    if github_token:
        try:
            from langchain_openai import ChatOpenAI
            available_llms.append(
                ChatOpenAI(
                    model="gpt-4o",
                    api_key=github_token,
                    base_url="https://models.inference.ai.azure.com",
                    temperature=0.6,
                )
            )
        except Exception as e:
            print(f"GitHub Models init failed: {e}")

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
