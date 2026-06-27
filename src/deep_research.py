import re
import requests
from ddgs import DDGS
from src.llm import get_llm
from langchain_core.messages import HumanMessage  # type: ignore


def generate_subqueries(query: str) -> list:
    """Uses LLM to generate 3 distinct sub-queries for deep research."""
    try:
        llm = get_llm()
        prompt = (
            f"You are a research expert. The user wants to research: '{query}'.\n"
            "Generate 3 distinct, highly targeted search queries to gather comprehensive information from the web.\n"
            "Return ONLY the queries, separated by newlines, with no numbering, bullet points, or extra text."
        )
        response = llm.invoke([HumanMessage(content=prompt)])

        # Depending on LLM wrapper, it might return a string or an AIMessage
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)

        queries = [q.strip() for q in response_text.split("\n") if q.strip()]

        clean_queries = []
        for q in queries:
            # Remove leading numbers, bullets
            q = re.sub(r"^[\d\.\-\*\s]+", "", q)
            # Remove quotes
            q = q.replace('"', "").replace("'", "")
            if q:
                clean_queries.append(q)

        return clean_queries[:3] if clean_queries else [query]
    except Exception as e:
        print(f"Subquery generation error: {e}")
        return [query]


def fetch_deep_context(query: str) -> str:
    """Performs deep research by searching sub-queries and scraping URLs."""
    subqueries = generate_subqueries(query)

    # ensure original query is also included
    if query not in subqueries:
        subqueries.insert(0, query)

    unique_urls = set()
    ddgs = DDGS()

    for sq in subqueries[:4]:
        try:
            results = ddgs.text(sq, max_results=3)
            if results:
                for r in results:
                    url = r.get("href")
                    if url and not url.endswith((".pdf", ".jpg", ".png", ".webp")):
                        unique_urls.add(url)
        except Exception as e:
            print(f"DDGS error for '{sq}': {e}")
            continue

    target_urls = list(unique_urls)[:5]

    context_chunks = []

    for url in target_urls:
        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            }
            response = requests.get(jina_url, headers=headers, timeout=20)
            if response.status_code == 200:
                text = response.text[:15000]  # Limit to ~3-4k tokens per source
                context_chunks.append(f"[Source: {url}]\n{text}\n")
        except Exception as e:
            print(f"Jina scrape error for {url}: {e}")

    if context_chunks:
        return (
            "\n\n=== DEEP RESEARCH CONTEXT ===\n"
            + "\n\n".join(context_chunks)
            + "\n===========================\n"
        )
    return ""
