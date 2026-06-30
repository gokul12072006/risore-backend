import re
import os
import requests
import concurrent.futures
import wikipedia
from src.news_fetcher import get_trending_news


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
    except Exception:
        pass
    return ""


def fetch_wikipedia_api(query: str) -> str:
    """Uses Groq 8B model to extract the main subject and fetch from Wikipedia."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_free_groq_api_key_here":
        return ""
        
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        prompt = f"Extract the main subject or entity from this question to search on Wikipedia. Output ONLY the subject name, nothing else. If it's a conversational greeting, output NONE. Query: '{query}'"
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=15
        )
        subject = completion.choices[0].message.content.strip()
        
        if subject.upper() != "NONE" and subject != "":
            def _wiki_search():
                try:
                    summary = wikipedia.summary(subject, sentences=4, auto_suggest=True)
                    return f"[SYSTEM ALERT - WIKIPEDIA FACT EXTRACTED for '{subject}':\n{summary}\n]"
                except wikipedia.exceptions.DisambiguationError as e:
                    return f"[SYSTEM ALERT - WIKIPEDIA: Multiple meanings found for '{subject}'. It could refer to {e.options[:3]}]"
                except wikipedia.exceptions.PageError:
                    return ""
                except Exception:
                    return ""
                    
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_wiki_search)
                try:
                    result = future.result(timeout=4)
                    if result:
                        return result
                except concurrent.futures.TimeoutError:
                    return ""
    except Exception:
        pass
    return ""


def fetch_jina_search(query: str) -> str:
    """Uses Jina Search AI as the ultimate autonomous web fallback."""
    def _search():
        try:
            jina_url = f"https://s.jina.ai/{query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/plain" # Ask Jina for markdown
            }
            response = requests.get(jina_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Return the first 6000 chars to avoid overwhelming context window
                return f"[SYSTEM ALERT - AUTONOMOUS WEB SCRAPE RESULTS:\n{response.text[:6000]}\n]"
        except Exception:
            pass
        return ""
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_search)
        try:
            # Strict 4-second timeout to prevent lag
            result = future.result(timeout=4) 
            if result:
                return result
        except concurrent.futures.TimeoutError:
            return ""
    return ""


def get_realtime_context(query: str) -> str:
    """Fetches real-time information from dedicated APIs (Weather, News, Wikipedia)."""
    context_chunks = []

    # 1. URLs
    urls = extract_urls(query)
    if urls:
        for url in urls:
            url_text = fetch_url_content(url)
            context_chunks.append(f"[Webpage Content from {url}:\n{url_text}\n]")
        return "\n\n" + "\n\n".join(context_chunks) + "\n"

    # 2. DEDICATED API ROUTER (Weather)
    if "weather" in query.lower() or "temperature" in query.lower():
        weather_context = fetch_weather_api(query)
        if weather_context:
            context_chunks.append(weather_context)
            return "\n\n" + "\n\n".join(context_chunks) + "\n"

    # 3. DEDICATED API ROUTER (News)
    if "news" in query.lower() or "latest update" in query.lower() or "trending" in query.lower():
        news_items = get_trending_news(5)
        if news_items:
            news_str = "\n".join([f"- {item['title']}" for item in news_items])
            context_chunks.append(f"[SYSTEM ALERT - LIVE BREAKING NEWS HEADLINES:\n{news_str}\n]")
            return "\n\n" + "\n\n".join(context_chunks) + "\n"
            
    # 4. FALLBACK TO WIKIPEDIA (For General Knowledge)
    keywords = ["who", "what", "where", "when", "why", "how", "history", "biography", "wiki", "explain", "details", "president", "country", "capital"]
    if any(word in query.lower() for word in keywords) and len(query.split()) >= 2:
        wiki_ctx = fetch_wikipedia_api(query)
        if wiki_ctx:
            context_chunks.append(wiki_ctx)

    # 5. ULTIMATE AUTONOMOUS FALLBACK (Jina Search)
    # If we still have no context, and the query is asking about something current or commercial:
    if not context_chunks:
        search_keywords = ["today", "now", "current", "latest", "time", "date", "event", "update", "upcoming", "price", "stock", "sale", "steam", "review", "release", "buy", "vs", "compare"]
        if any(word in query.lower() for word in search_keywords) and len(query.split()) >= 2:
            jina_ctx = fetch_jina_search(query)
            if jina_ctx:
                context_chunks.append(jina_ctx)

    if context_chunks:
        return "\n\n" + "\n\n".join(context_chunks) + "\n"
    return ""
