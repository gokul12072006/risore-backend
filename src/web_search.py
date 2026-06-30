import re
import os
import requests
import concurrent.futures

from ddgs import DDGS


def extract_urls(query: str) -> list:
    """Finds all URLs in the given text query."""
    url_pattern = re.compile(r"(https?://[^\s]+)")
    return url_pattern.findall(query)


def fetch_url_content(url: str) -> str:
    """Fetches and extracts readable text from a URL using Jina Reader API."""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(jina_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text[:15000]
    except Exception as e:
        return f"[Failed to fetch content from {url}: {str(e)}]"


def needs_realtime(query: str) -> bool:
    """Use an ultra-fast keyword heuristic to decide if it needs to search the web."""
    keywords = ["weather", "today", "now", "current", "news", "latest", "time", "date", "event", "update", "upcoming", "who", "what", "where", "when", "how", "price", "stock", "wiki", "sale", "steam"]
    query_lower = query.lower()
    return any(word in query_lower for word in keywords)


def fetch_weather_api(query: str) -> str:
    """Uses Groq 8B model to extract city and fetch from wttr.in."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_free_groq_api_key_here":
        return ""
        
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        prompt = f"Extract the city name from this query. Output ONLY the city name, nothing else. If there is no city, output NONE. Query: '{query}'"
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        city = completion.choices[0].message.content.strip()
        
        if city.upper() != "NONE" and city != "":
            wttr_url = f"https://wttr.in/{city}?format=%l:+%C+%t+(Feels+like+%f)+Wind:+%w"
            res = requests.get(wttr_url, timeout=5)
            if res.status_code == 200:
                weather_str = res.text.strip()
                return f"[SYSTEM ALERT - LIVE WEATHER DATA PROVIDED: {weather_str}]"
    except Exception as e:
        pass
    return ""


def get_duckduckgo_search(query: str) -> str:
    """Runs a DDG search but forcibly aborts after 3 seconds to prevent 50-second delays."""
    def _search():
        try:
            results = DDGS().text(query, max_results=3)
            if results:
                return " ".join([r.get("body", "") for r in results])
        except Exception:
            pass
        return ""
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_search)
        try:
            # 3-second hard timeout fixes the 50-second delay bug!
            result = future.result(timeout=3)
            if result:
                return f"[Real-Time Web Search Results:\n{result}\n]"
        except concurrent.futures.TimeoutError:
            print("DuckDuckGo search timed out after 3 seconds. Skipping to prevent delay.")
        except Exception as e:
            pass
    return ""


def get_realtime_context(query: str) -> str:
    """Fetches real-time information from dedicated APIs or web fallback."""
    context_chunks = []

    # 1. URLs
    urls = extract_urls(query)
    if urls:
        for url in urls:
            url_text = fetch_url_content(url)
            context_chunks.append(f"[Webpage Content from {url}:\n{url_text}\n]")

    # 2. DEDICATED API ROUTER (Weather)
    if "weather" in query.lower() or "temperature" in query.lower():
        weather_context = fetch_weather_api(query)
        if weather_context:
            context_chunks.append(weather_context)
            # If weather is found, skip the slow DDG fallback to save time!
            return "\n\n" + "\n\n".join(context_chunks) + "\n"

    # 3. FALLBACK WEB SEARCH
    if needs_realtime(query) and not urls:
        search_ctx = get_duckduckgo_search(query)
        if search_ctx:
            context_chunks.append(search_ctx)

    if context_chunks:
        return "\n\n" + "\n\n".join(context_chunks) + "\n"
    return ""
