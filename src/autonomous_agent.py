import threading
import time
from langchain_core.documents import Document # type: ignore
from langchain_core.messages import HumanMessage # type: ignore

from src.database import SessionLocal, ProactiveSuggestion
from src.news_fetcher import get_trending_news
from src.deep_research import fetch_deep_context
from src.vector_store import create_or_update_chroma
from src.llm import get_llm

def autonomous_data_gathering_cycle():
    """
    The core loop for the Autonomous Agent.
    1. Fetches trends
    2. Deep researches them
    3. Embeds knowledge into ChromaDB
    4. Generates a proactive insight
    """
    print("\n[Autonomous Agent] Waking up to gather data...")
    try:
        trends = get_trending_news(2)
        if not trends:
            print("[Autonomous Agent] No trends found. Going back to sleep.")
            return

        combined_context = ""
        docs_to_embed = []
        
        for trend in trends:
            query = trend.get("title", "")
            if not query: continue
            
            print(f"[Autonomous Agent] Deep researching: {query}")
            context_string = fetch_deep_context(query)
            
            if context_string:
                combined_context += f"\n--- Trend: {query} ---\n{context_string}"
                # Create smaller chunks manually or just embed the whole context string (split by newlines for simplicity)
                chunks = context_string.split("\n\n")
                for chunk in chunks:
                    if len(chunk.strip()) > 50:
                        docs_to_embed.append(Document(page_content=chunk.strip(), metadata={"source": "autonomous_agent", "topic": query}))
        
        # Save to knowledge base
        if docs_to_embed:
            print(f"[Autonomous Agent] Memorizing {len(docs_to_embed)} new knowledge chunks into ChromaDB...")
            create_or_update_chroma(docs_to_embed)
        
        # Self-Reflection & Insight Generation
        if combined_context:
            print("[Autonomous Agent] Deeply reasoning over new data to generate insights...")
            llm = get_llm()
            
            prompt = f"""
            You are Risore 1.0, an elite, autonomous AI. 
            You just learned the following new information during your background research cycle:
            {combined_context[:10000]}
            
            Synthesize this information and write a highly engaging, proactive insight or greeting to the user.
            Imagine you are greeting them when they open the app. Tell them what you just learned and why it matters.
            Keep it under 3-4 sentences. Use emojis. DO NOT use XML/HTML tags. DO NOT apologize or mention you are an AI.
            """
            
            response = llm.invoke([HumanMessage(content=prompt)])
            insight = response.content if hasattr(response, "content") else str(response)
            
            # Clean out any <think> tags if they bleed into the final string
            import re
            insight = re.sub(r"<think>.*?</think>", "", insight, flags=re.DOTALL).strip()
            
            if insight:
                db = SessionLocal()
                try:
                    new_insight = ProactiveSuggestion(content=insight, is_read=False)
                    db.add(new_insight)
                    db.commit()
                    print("[Autonomous Agent] Insight saved successfully.")
                finally:
                    db.close()
                    
    except Exception as e:
        print(f"[Autonomous Agent] Error during autonomous cycle: {e}")

def autonomous_daemon(interval_minutes=60):
    """Background daemon to run the autonomous cycle periodically."""
    # Wait a few minutes on boot before starting heavy tasks
    time.sleep(30)
    
    while True:
        autonomous_data_gathering_cycle()
        time.sleep(interval_minutes * 60)
