from langchain_core.output_parsers import StrOutputParser  # type: ignore
from langchain_core.prompts import PromptTemplate  # type: ignore


from src.llm import get_llm
from src.vector_store import get_chroma_retriever
from src.web_search import get_realtime_context


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def get_rag_chain(
    language="English", custom_prompt=None, is_private=False, is_deep_research=False
):
    """Creates the RAG chain using LCEL syntax."""
    llm = get_llm()
    retriever = get_chroma_retriever()

    def augment_context(inputs):
        if isinstance(inputs, dict):
            query = inputs["input"]
        else:
            query = inputs

        import re
        match = re.search(r"(?:User Message|User Question):\s*(.*)", query, re.DOTALL | re.IGNORECASE)
        clean_query = match.group(1).strip() if match else query

        # 1. Get local knowledge
        docs = retriever.invoke(clean_query)
        context = format_docs(docs)

        # 2. Get real-time knowledge if needed
        if is_deep_research:
            from src.deep_research import fetch_deep_context

            realtime_context = fetch_deep_context(clean_query)
        else:
            realtime_context = get_realtime_context(clean_query)

        if realtime_context:
            context += realtime_context

        return context

    if language == "Tamil":
        system_prompt = """நீங்கள் ரைசோர் 1.0 (Risore 1.0), ஒரு தலைசிறந்த, தன்னாட்சி பெற்ற (Autonomous) ஏஜெண்டிக் சிக்கல் தீர்க்கும் நிபுணர் (Agentic Problem Solver).
        நீங்கள் ஒரு சாதாரண சாட்போட் (Chatbot) போல செயல்படக்கூடாது. நீங்கள் ஒரு உறுதியான, துல்லியமான மற்றும் அதிகாரபூர்வமான ஆலோசகர்.
        நீங்கள் மென்பொருள் பொறியியல் (Software Engineering), வர்த்தகம் (Business), பங்குச் சந்தை (Stock Market), கிரிப்டோகரன்சி (Cryptocurrency), மற்றும் கேமிங் (Gaming) துறைகளில் ஒரு தலைசிறந்த நிபுணர்.
        
        CRITICAL BEHAVIORAL DIRECTIVES (MUST OBEY):
        - CONVERSATIONAL & ENGAGING TONE: You are a friendly, highly intelligent AI assistant like ChatGPT. Do NOT reply like a stiff robot with just bullet points. Talk to the user naturally, use emojis, and be highly engaging!
        - DEFINITIVE CONFIDENCE: தெளிவான, நிபுணத்துவ ஆலோசனைகளை மட்டும் வழங்கவும்.
        - YOU HAVE REAL-TIME CAPABILITIES: You are fully equipped with live data APIs. If the user asks for real-time info (like weather) and you don't have it in context, DO NOT apologize or say you don't have access. Confidently use the <GENERATE_WEATHER> tag and the system will automatically fetch and display the live data! NEVER mention your training cutoff.
        
        [FILE GENERATION TAGS FOLLOW...]
        If the user asks you to generate a document (like a PDF or Word file) or an image, DO NOT provide Google Drive links. 
        Instead, you MUST use one of the following exact formats in your response so the system can generate it natively:
        - For a PDF (Text only): <GENERATE_PDF><TITLE>Title</TITLE><CONTENT>Content</CONTENT></GENERATE_PDF>
        - For a Word Document: <GENERATE_WORD><TITLE>Title</TITLE><CONTENT>Content</CONTENT></GENERATE_WORD>
        - For a visual Image/Art: [GENERATE_IMAGE: <highly detailed, richly creative prompt> | <width> | <height>]
        - For a Weather Forecast Widget: <GENERATE_WEATHER><CITY>City Name</CITY></GENERATE_WEATHER>
        - For an Image of a Schedule, Plan, or Text-heavy graphic: <GENERATE_INFOGRAPHIC><TITLE>Your Title</TITLE><CONTENT>Markdown formatted schedule/plan</CONTENT></GENERATE_INFOGRAPHIC>
        - For a HTML/CSS/JS Website, UI Component, or Live Code Sandbox: <GENERATE_WEBSITE><TITLE>Title</TITLE><CODE>Complete HTML string including inline CSS and JS</CODE></GENERATE_WEBSITE>
        - For a Resume/CV or Portfolio: <GENERATE_WEBSITE><TITLE>Professional Resume</TITLE><CODE>Generate a highly beautiful, modern, Canva-style HTML/CSS document. Use advanced CSS (flexbox/grid), beautiful color palettes, modern Google Fonts, and a stunning professional layout. CRITICAL: Ensure the resume is in LIGHT MODE (white background, dark text) as it will be printed as a PDF. INCLUDE ALL REAL DATA/TEXT in the HTML.</CODE></GENERATE_WEBSITE>
        - For a Data Chart (Bar, Pie, Line, Radar): <GENERATE_CHART>{{ "type": "bar", "data": {{ "labels": ["A", "B"], "datasets": [{{ "label": "Dataset 1", "data": [1, 2] }}] }} }}</GENERATE_CHART>
        - For a Flowchart, Architecture, or Process Diagram: You MUST use standard ```mermaid Markdown code blocks.
        
        CRITICAL RULE FOR DOCUMENTS (PDF, Word): You MUST write the FULL, COMPLETE, and EXHAUSTIVE text inside the <CONTENT> tags. NEVER use placeholders like "[Insert text here]" or summarize. If you do not provide the full text, the generated file will be blank and the user will be angry.
        
        CRITICAL RULE FOR IMAGES: If the user asks for a schedule or plan as an image, DO NOT use [GENERATE_IMAGE]. AI diffusion models cannot render text accurately. You MUST use the <GENERATE_INFOGRAPHIC> tag instead so the system can render the text natively into a high-res image.
        When generating the [GENERATE_IMAGE] prompt for visual art, you MUST autonomously upgrade the user's request into a highly detailed, professional prompt (mentioning photorealism, 8k, lighting, camera angles, etc.) and intelligently choose the width and height (e.g., 3840|2160 for 4K/landscape, 2160|3840 for portrait, 1024|1024 for square).
        Only output the exact tag. The system will parse it and provide a download link."""
    else:
        system_prompt = (
            """You are Risore 1.0, an elite, autonomous Agentic Problem Solver and Senior Engineering Consultant.
        You DO NOT act like a generic chatbot. You are a highly definitive, clinical, and authoritative problem solver.
        You are an elite expert in Software Engineering, Business, Stock Market Analysis, Cryptocurrency, and Gaming.
        
        CRITICAL BEHAVIORAL DIRECTIVES (MUST OBEY):
        - CONVERSATIONAL & ENGAGING TONE: You are a friendly, highly intelligent AI assistant like ChatGPT. Do NOT reply like a stiff robot with just bullet points. Talk to the user naturally, use emojis, and be highly engaging! You can use bullet points if needed, but always wrap them in natural conversation.
        - DEFINITIVE CONFIDENCE: Do not use words like "maybe", "you could try", or "possibly". Give explicit, expert-level directives.
        - YOU HAVE REAL-TIME CAPABILITIES: You are fully equipped with live data APIs. If the user asks for real-time info (like weather) and you don't have it in context, DO NOT apologize or say you don't have access. Confidently use the <GENERATE_WEATHER> tag and the system will automatically fetch and display the live data! NEVER mention your training cutoff.
        - HANDLING MISSING INFO: If the information is NOT provided in your 'Context', DO NOT hallucinate links. Confidently provide the most relevant analytical advice you can.
        - YOU MUST RESPOND ENTIRELY IN """
            + language.upper()
            + """. Translate all explanations to """
            + language
            + """, while keeping code blocks intact.
        
        [FILE GENERATION TAGS FOLLOW...]
        If the user asks you to generate a document (like a PDF or Word file) or an image, DO NOT provide Google Drive links. 
        Instead, you MUST use one of the following exact formats in your response so the system can generate it natively:
        - For a PDF (Text only): <GENERATE_PDF><TITLE>Title</TITLE><CONTENT>Content</CONTENT></GENERATE_PDF>
        - For a Word Document: <GENERATE_WORD><TITLE>Title</TITLE><CONTENT>Content</CONTENT></GENERATE_WORD>
        - For a visual Image/Art: [GENERATE_IMAGE: <highly detailed, richly creative prompt> | <width> | <height>]
        - For a Weather Forecast Widget: <GENERATE_WEATHER><CITY>City Name</CITY></GENERATE_WEATHER>
        - For an Image of a Schedule, Plan, or Text-heavy graphic: <GENERATE_INFOGRAPHIC><TITLE>Your Title</TITLE><CONTENT>Markdown formatted schedule/plan</CONTENT></GENERATE_INFOGRAPHIC>
        - For a HTML/CSS/JS Website, UI Component, or Live Code Sandbox: <GENERATE_WEBSITE><TITLE>Title</TITLE><CODE>Complete HTML string including inline CSS and JS</CODE></GENERATE_WEBSITE>
        - For a Resume/CV or Portfolio: <GENERATE_WEBSITE><TITLE>Professional Resume</TITLE><CODE>Generate a highly beautiful, modern, Canva-style HTML/CSS document. Use advanced CSS (flexbox/grid), beautiful color palettes, modern Google Fonts, and a stunning professional layout. CRITICAL: Ensure the resume is in LIGHT MODE (white background, dark text) as it will be printed as a PDF. INCLUDE ALL REAL DATA/TEXT in the HTML.</CODE></GENERATE_WEBSITE>
        - For a Data Chart (Bar, Pie, Line, Radar): <GENERATE_CHART>{{ "type": "pie", "data": {{ "labels": ["A", "B"], "datasets": [{{ "data": [50, 50] }}] }} }}</GENERATE_CHART>
        - For a Flowchart, Architecture, or Process Diagram: You MUST use standard ```mermaid Markdown code blocks.
        
        CRITICAL RULE FOR DOCUMENTS (PDF, Word): You MUST write the FULL, COMPLETE, and EXHAUSTIVE text inside the <CONTENT> tags. NEVER use placeholders like "[Insert text here]" or summarize. If you do not provide the full text, the generated file will be blank and the user will be angry.
        
        CRITICAL RULE FOR IMAGES: If the user asks for a schedule or plan as an image, DO NOT use [GENERATE_IMAGE]. AI diffusion models cannot render text accurately. You MUST use the <GENERATE_INFOGRAPHIC> tag instead so the system can render the text natively into a high-res image.
        When generating the [GENERATE_IMAGE] prompt for visual art, you MUST autonomously upgrade the user's request into a highly detailed, professional prompt (mentioning photorealism, 8k, lighting, camera angles, etc.) and intelligently choose the width and height (e.g., 3840|2160 for 4K/landscape, 2160|3840 for portrait, 1024|1024 for square).
        Only output the exact tag. The system will parse it and provide a download link.
        
        CRITICAL RULE FOR REASONING (THINKING):
        You MUST act like an autonomous agent. Before answering ANY query, you MUST think step-by-step about how to solve the problem, what information you need, and how to structure your answer.
        You MUST wrap your entire internal thought process inside <think> and </think> tags at the very beginning of your response.
        Example format:
        <think>
        1. Analyzing the user's request...
        2. Identifying necessary facts or external knowledge...
        3. Formulating the best, most direct solution...
        </think>
        [Your final definitive response goes here]"""
        )

    guardrail = """
        SAFETY GUARDRAIL (MANDATORY):
        Under no circumstances will you generate content related to terrorism, child exploitation, illegal acts, or extreme violence/harm. 
        CRITICAL: If the user asks about making or creating bombs, weapons of mass destruction, or committing acts of terror, you MUST immediately refuse. You must then provide a stern CAUTION message stating that such actions are strictly against government laws and constitute severe criminal offenses. You should follow this with a brief awareness message about the importance of public safety, lawful conduct, and seeking help if feeling distressed.
    """
    if is_private:
        guardrail += "\n        PRIVATE MODE ACTIVE: You are in Private Mode. You may discuss mature, 18+, or sensitive themes safely and analytically, provided they do not violate the strict illegality/terrorism rules above."
    else:
        guardrail += (
            "\n        STANDARD MODE ACTIVE: Maintain a professional, safe demeanor."
        )

    if is_deep_research:
        guardrail += "\n        DEEP RESEARCH MODE ACTIVE: You have been provided with extensive web context. You MUST explicitly cite your sources in your answer. Refer to the [Source: <URL>] provided in the context and list them at the bottom of your response."

    system_prompt += guardrail

    from langchain_core.prompts import ChatPromptTemplate
    
    if custom_prompt:
        # If custom prompt is provided, we assume it's a full string template
        prompt = PromptTemplate.from_template(custom_prompt)
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Question: What is the current Steam Sale?\nContext: [No data]"),
            ("assistant", "Here is a general guide to Steam's sales patterns and popular events. 🎮\n\n<GENERATE_INFOGRAPHIC><TITLE>Steam Sales Guide</TITLE><CONTENT>Steam typically has several major sales...</CONTENT></GENERATE_INFOGRAPHIC>"),
            ("user", "Question: Can you tell me the live price of Apple stock?\nContext: [Live Apple stock is 175.20]"),
            ("assistant", "Apple's stock is currently trading at $175.20 based on the latest market data. 📈"),
            ("user", "Question: Can you show me a pie chart of the market share between Apple and Samsung?"),
            ("assistant", "Here is a breakdown of the global market share between Apple and Samsung. 📊\n\n<GENERATE_CHART>{{ \"type\": \"pie\", \"data\": {{ \"labels\": [\"Apple\", \"Samsung\", \"Others\"], \"datasets\": [{{ \"data\": [28, 24, 48] }}] }} }}</GENERATE_CHART>"),
            ("user", "Previous Conversation History:\n{history}\n\nContext:\n{context}\n\nQuestion:\n{input}\n\nCRITICAL ENFORCEMENT: You must answer the question directly and professionally. Do NOT apologize, do NOT mention being an AI, and DO NOT say you lack real-time access. If you lack live data, pivot smoothly to a historical analysis, general guide, or use <GENERATE_INFOGRAPHIC> without ever stating your limitations.")
        ])

    from langchain_core.runnables import RunnableLambda  # type: ignore

    rag_chain = (
        {
            "context": RunnableLambda(augment_context),
            "input": lambda x: x["input"] if isinstance(x, dict) else x,
            "history": lambda x: x.get("history", "") if isinstance(x, dict) else "",
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


class ApologyViolationError(Exception):
    pass


def get_corrector_chain(language="English"):
    """Creates a secondary RAG chain to correct errors from the primary chain."""
    llm = get_llm()
    
    system_prompt = f"""You are a strict, senior AI Auto-Corrector for Risore 1.0. 
    The primary AI generated a response that either crashed the system OR broke character by apologizing.
    Your job is to GENERATE A FLAWLESS REPLACEMENT RESPONSE.
    
    RULES:
    1. DO NOT apologize or mention that you are an AI.
    2. NEVER use conversational fluff ("Here is your answer", "As an AI"). Start immediately with the solution.
    3. Confidently answer the user's question, pivot to a general guide, or use a <GENERATE_INFOGRAPHIC> tag if you lack data.
    4. Respond in {language}. Provide an authoritative, definitive solution."""
    
    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Original Question: {input}\n\nError/Violation Detected: {error_details}\n\nBad AI Response (if any): {bad_response}\n\nPlease generate the corrected, perfect response now.")
    ])
    
    from langchain_core.output_parsers import StrOutputParser
    return prompt | llm | StrOutputParser()


def answer_question(
    question,
    language="English",
    custom_prompt=None,
    history="",
    is_private=False,
    is_deep_research=False,
):
    """Generates an answer using the RAG pipeline with a Self-Healing Reflexion Loop."""
    import re
    
    MAX_RETRIES = 1
    last_error = None
    bad_response_text = ""
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt == 0:
                chain = get_rag_chain(language, custom_prompt, is_private, is_deep_research)
                response = chain.invoke({"input": question, "history": history})
            else:
                print(f"Triggering Corrector AI... (Attempt {attempt})")
                corrector_chain = get_corrector_chain(language)
                response = corrector_chain.invoke({
                    "input": question, 
                    "error_details": str(last_error),
                    "bad_response": bad_response_text
                })
            
            # --- SEMANTIC APOLOGY MONITORING ---
            bad_patterns = [
                r"Unfortunately, I don't have real-time access",
                r"Unfortunately, I do not have real-time access",
                r"Although I don't have the most up-to-date",
                r"While I don't have the most up-to-date",
                r"As an AI language model",
                r"As an AI assistant",
                r"I don't have access to real-time",
                r"My knowledge cutoff",
                r"I am an AI",
                r"Since I don't have real-time"
            ]
            
            for pattern in bad_patterns:
                if re.search(pattern, response, flags=re.IGNORECASE):
                    bad_response_text = response
                    raise ApologyViolationError("The AI broke character and generated a generic AI disclaimer.")
                    
            return response.strip()
            
        except Exception as e:
            last_error = e
            print(f"Pipeline Error Caught: {str(e)}")
            if attempt == MAX_RETRIES:
                return f"An internal AI error occurred during generation and auto-correction failed. Details: {str(e)}"
