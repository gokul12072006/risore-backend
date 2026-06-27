import time
import urllib.request
import xml.etree.ElementTree as ET

_cached_news = []
_last_fetch_time = 0
CACHE_DURATION = 3600  # Cache news for 1 hour to avoid spamming the API


def get_trending_news(limit=3):
    global _cached_news, _last_fetch_time

    current_time = time.time()
    # Return cached news if within cache duration
    if _cached_news and (current_time - _last_fetch_time < CACHE_DURATION):
        return _cached_news[:limit]

    url = "https://news.google.com/rss"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        news_list = []
        for item in items[:limit]:
            title_elem = item.find("title")
            title = title_elem.text if title_elem is not None and title_elem.text else ""
            # Remove the source suffix (e.g. " - CNN") for a cleaner title
            clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title

            news_list.append(
                {
                    "title": clean_title,
                    "description": "Trending global event today",
                    "prompt": f"Tell me about the recent news: {clean_title}",
                }
            )

        if news_list:
            _cached_news = news_list
            _last_fetch_time = current_time

        return news_list
    except Exception as e:
        print(f"Failed to fetch news: {e}")
        # Fallback suggestions if offline or error
        return [
            {
                "title": "Smart Budget",
                "description": "A budget that fits your lifestyle",
                "prompt": "Create a smart budget plan",
            },
            {
                "title": "Analytics",
                "description": "Empowers smarter decisions",
                "prompt": "Provide analytics insights",
            },
            {
                "title": "Spending",
                "description": "Optimize financial resources",
                "prompt": "Analyze my spending",
            },
        ][:limit]
