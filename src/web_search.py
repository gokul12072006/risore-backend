from ddgs import DDGS

def needs_realtime(query: str) -> bool:
    """Check if the query likely needs real-time information."""
    keywords = ['weather', 'today', 'now', 'current', 'news', 'latest', 'time', 'date']
    query_lower = query.lower()
    return any(word in query_lower for word in keywords)

def get_realtime_context(query: str) -> str:
    """Fetches real-time information from the web."""
    if not needs_realtime(query):
        return ""
        
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            context_str = " ".join([r.get('body', '') for r in results])
            return f"\n\n[Real-Time Web Search Context: {context_str}]\n"
        return ""
    except Exception as e:
        return f"\n\n[Web Search Failed: {str(e)}]\n"
