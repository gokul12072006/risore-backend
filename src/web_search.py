import re

import requests

from ddgs import DDGS


def extract_urls(query: str) -> list:
    """Finds all URLs in the given text query."""
    # A standard regex for extracting URLs
    url_pattern = re.compile(r"(https?://[^\s]+)")
    return url_pattern.findall(query)


def fetch_url_content(url: str) -> str:
    """Fetches and extracts readable text from a URL using Jina Reader API."""
    try:
        # Route through Jina's LLM-friendly reader API to bypass anti-bot protections
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(jina_url, headers=headers, timeout=15)
        response.raise_for_status()

        # Jina returns clean Markdown text
        text = response.text
        # Limit extracted text to prevent overloading the LLM
        return text[:15000]
    except Exception as e:
        return f"[Failed to fetch content from {url}: {str(e)}]"


def needs_realtime(query: str) -> bool:
    """Use the AI's own brain (LLM) to autonomously decide if it needs to search the web."""
    try:
        from src.llm import get_llm
        llm = get_llm()
        prompt = (
            f"Analyze the following user query: '{query}'\n"
            "Does this query require searching the live internet for current events, real-time data, specific facts, Wikipedia knowledge, or recent updates? "
            "Think carefully. If it's a casual greeting or a general logic question, say NO. If it asks for information about the world, products, news, or facts, say YES. "
            "Reply ONLY with the exact word 'YES' or 'NO'."
        )
        response = llm.invoke(prompt).strip().upper()
        if "YES" in response:
            return True
        elif "NO" in response:
            return False
    except Exception:
        pass
    
    # Fallback to expanded keyword heuristic if LLM fails
    keywords = ["weather", "today", "now", "current", "news", "latest", "time", "date", "event", "update", "upcoming", "who", "what", "where", "when", "how", "price", "stock", "wiki"]
    query_lower = query.lower()
    return any(word in query_lower for word in keywords)


def get_realtime_context(query: str) -> str:
    """Fetches real-time information from the web and/or provided URLs."""
    context_chunks = []

    # 1. First, check for explicit URLs in the user's prompt
    urls = extract_urls(query)
    if urls:
        for url in urls:
            url_text = fetch_url_content(url)
            context_chunks.append(f"[Webpage Content from {url}:\n{url_text}\n]")

    # 2. Check if a general web search is needed
    if needs_realtime(query) and not urls:
        try:
            results = DDGS().text(query, max_results=3)
            if results:
                search_str = " ".join([r.get("body", "") for r in results])
                context_chunks.append(
                    f"[Real-Time Web Search Results:\n{search_str}\n]"
                )
        except Exception as e:
            context_chunks.append(f"[Web Search Failed: {str(e)}]")

    if context_chunks:
        return "\n\n" + "\n\n".join(context_chunks) + "\n"
    return ""
