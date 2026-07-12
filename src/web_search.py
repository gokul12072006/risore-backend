import re
import os
import requests
import concurrent.futures
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
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


_search_cache = {}
CACHE_DURATION = 3600  # 1 hour

_crypto_cache = {}
CRYPTO_CACHE_DURATION = 60  # 60 seconds

def fetch_crypto_api(query: str) -> str:
    """Uses LLM to extract coin name and fetches price from CoinGecko."""
    global _crypto_cache
    
    current_time = time.time()
    query_lower = query.lower().strip()
    
    if query_lower in _crypto_cache:
        cached_time, cached_result = _crypto_cache[query_lower]
        if current_time - cached_time < CRYPTO_CACHE_DURATION:
            return cached_result

    try:
        from src.llm import get_llm
        from langchain_core.messages import HumanMessage
        
        llm = get_llm()
        prompt = f"Extract the cryptocurrency or stock name from this query. Output ONLY the coin name (e.g. bitcoin, ethereum, beldex), nothing else. If it's not about crypto/stocks, output NONE. Query: '{query}'"
        
        response = llm.invoke([HumanMessage(content=prompt)])
        coin = response.content.strip().lower() if hasattr(response, 'content') else str(response).strip().lower()
        
        if coin != "none" and coin != "":
            search_url = f"https://api.coingecko.com/api/v3/search?query={urllib.parse.quote(coin)}"
            search_res = requests.get(search_url, timeout=5)
            if search_res.status_code == 200:
                coins = search_res.json().get('coins', [])
                if coins:
                    coin_id = coins[0]['id']
                    coin_name = coins[0]['name']
                    price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,inr,eur,gbp"
                    price_res = requests.get(price_url, timeout=5)
                    if price_res.status_code == 200:
                        data = price_res.json()
                        if coin_id in data:
                            price_usd = data[coin_id].get('usd', 'Unknown')
                            price_inr = data[coin_id].get('inr', 'Unknown')
                            price_eur = data[coin_id].get('eur', 'Unknown')
                            price_gbp = data[coin_id].get('gbp', 'Unknown')
                            result = f"[SYSTEM ALERT - LIVE CRYPTO DATA: {coin_name} is currently priced at ${price_usd} USD / ₹{price_inr} INR / €{price_eur} EUR / £{price_gbp} GBP.]"
                            _crypto_cache[query_lower] = (current_time, result)
                            return result
    except Exception as e:
        print(f"Crypto API error: {e}")
    return ""


def fetch_universal_search(query: str) -> str:
    """Uses DuckDuckGo Search and Jina Reader to autonomously answer any query."""
    global _search_cache
    
    current_time = time.time()
    query_lower = query.lower().strip()
    
    if query_lower in _search_cache:
        cached_time, cached_result = _search_cache[query_lower]
        if current_time - cached_time < CACHE_DURATION:
            return cached_result
            
    def _search():
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            results = ddgs.text(query, max_results=2)
            
            if not results:
                return ""
                
            def _fetch_jina(url):
                if not url or url.endswith((".pdf", ".jpg")):
                    return ""
                jina_url = f"https://r.jina.ai/{url}"
                headers = {"User-Agent": "Mozilla/5.0"}
                try:
                    res = requests.get(jina_url, headers=headers, timeout=6)
                    if res.status_code == 200:
                        return f"--- Source: {url} ---\n{res.text[:3000]}\n\n"
                except Exception:
                    pass
                return ""

            context = ""
            urls_to_fetch = [r.get("href") for r in results if r.get("href")]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as jina_executor:
                fetched_results = jina_executor.map(_fetch_jina, urls_to_fetch)
                for res_text in fetched_results:
                    if res_text:
                        context += res_text
            
            if context:
                result = f"[SYSTEM ALERT - UNIVERSAL WEB SEARCH RESULTS:\n{context}]"
                _search_cache[query_lower] = (current_time, result)
                return result
        except Exception as e:
            print(f"Universal search error: {e}")
        return ""
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_search)
        try:
            result = future.result(timeout=15)
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

    # 3. DEDICATED API ROUTER (Crypto)
    if any(word in query.lower() for word in ["price", "crypto", "bitcoin", "beldex", "stock", "usd"]):
        crypto_context = fetch_crypto_api(query)
        if crypto_context:
            context_chunks.append(crypto_context)
            return "\n\n" + "\n\n".join(context_chunks) + "\n"

    # 4. DEDICATED API ROUTER (News)
    if "news" in query.lower() or "latest update" in query.lower() or "trending" in query.lower():
        news_items = get_trending_news(5)
        if news_items:
            news_str = "\n".join([f"- {item['title']}" for item in news_items])
            context_chunks.append(f"[SYSTEM ALERT - LIVE BREAKING NEWS HEADLINES:\n{news_str}\n]")
            return "\n\n" + "\n\n".join(context_chunks) + "\n"
            
    # 5. FALLBACK TO WIKIPEDIA (For General Knowledge)
    keywords = ["who", "what", "where", "when", "why", "how", "history", "biography", "wiki", "explain", "details", "president", "country", "capital"]
    if any(word in query.lower() for word in keywords) and len(query.split()) >= 2:
        wiki_ctx = fetch_wikipedia_api(query)
        if wiki_ctx:
            context_chunks.append(wiki_ctx)

    # 6. ULTIMATE AUTONOMOUS FALLBACK (Universal Web Search)
    # If we still have no context, and the query is asking about something current:
    if not context_chunks:
        search_keywords = ["today", "now", "current", "latest", "time", "date", "event", "update", "upcoming", "sale", "steam", "review", "release", "buy", "vs", "compare", "score", "game", "match", "movie"]
        if any(word in query.lower() for word in search_keywords) and len(query.split()) >= 2:
            search_ctx = fetch_universal_search(query)
            if search_ctx:
                context_chunks.append(search_ctx)

    if context_chunks:
        return "\n\n" + "\n\n".join(context_chunks) + "\n"
    return ""
