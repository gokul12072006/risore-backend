import base64
import json
import os
import re
import urllib.parse
import uuid
import threading
import time
import requests
from typing import List, Optional

import firebase_admin
import jwt
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from firebase_admin import auth, credentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config import BASE_DIR
from src.database import ChatMessage, ChatSession, Task, User, get_db
from src.news_fetcher import get_trending_news

app = FastAPI(
    title="Risore AI API", description="Secure Backend API for Risore AI", version="1.0"
)

# Initialize Firebase Admin
try:
    cred_path = os.path.join(BASE_DIR, "serviceAccountKey.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print(
            "Warning: serviceAccountKey.json not found. Firebase Auth will operate in mock/unverified mode unless added."
        )
except ValueError:
    pass


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        if os.path.exists(os.path.join(BASE_DIR, "serviceAccountKey.json")):
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        else:
            # Fallback for dev mode
            return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        print(f"Token verification failed: {e}")
    return None


# Setup CORS to allow your website or apps to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # In production, change to your specific domain (e.g., "https://risore.com")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODE_INSTRUCTIONS = {
    "Overview": "CRITICAL MODE INSTRUCTION: Provide a high-level overview. Use bullet points, summarize key concepts, and avoid overly deep technical jargon.",
    "Technical": "CRITICAL MODE INSTRUCTION: Provide a highly technical, low-level explanation. Include architecture details, code snippets, scientific analysis, and strict engineering mechanics.",
    "Prioritise": "CRITICAL MODE INSTRUCTION: Focus your answer purely on actionable steps. Rank them strictly by importance and urgency. Tell the user what to do first, second, and third.",
    "Optimise": "CRITICAL MODE INSTRUCTION: Focus your answer on efficiency. How can this be improved? Discuss cost reduction, code refactoring, performance maximization, and scaling.",
    "Case Study": "CRITICAL MODE INSTRUCTION: Format your response strictly as a professional business/technical Case Study. Use headers: Background, Challenge, Solution, and Outcome.",
    "Friendly": "CRITICAL MODE INSTRUCTION: You are now a highly friendly, fun, and energetic AI, similar to a Character.ai persona! Use enthusiastic language, lots of emojis, and be conversational like a best friend. Keep the tone light-hearted, empathetic, and highly engaging while answering the user's questions."
}


class ChatMsg(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMsg] = []
    language: Optional[str] = "English"
    is_private: Optional[bool] = False
    session_id: Optional[str] = None
    ai_mode: Optional[str] = "Default"
    is_deep_research: Optional[bool] = False


class FeedbackRequest(BaseModel):
    user_query: str
    ai_response: str
    rating: int  # 1 for positive, 0 for negative


@app.post("/api/chat")
async def chat_endpoint(
    req: ChatRequest,
    user_token: dict = Depends(get_current_user),
    x_device_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    try:
        user_context = ""
        if req.ai_mode and req.ai_mode in MODE_INSTRUCTIONS:
            user_context += f"{MODE_INSTRUCTIONS[req.ai_mode]}\n\n"

        if user_token:
            uid = user_token.get("user_id") or user_token.get("uid")
            user = db.query(User).filter(User.id == uid).first()
            if user and user.name:
                user_context += f"The user's name is {user.name}.\n"
            tasks = (
                db.query(Task)
                .filter(Task.user_id == uid, Task.completed == False)
                .all()
            )
            if tasks:
                task_list = "\n".join([f"- {t.task_content}" for t in tasks])
                user_context += f"The user's current pending tasks are:\n{task_list}\n"

        trends = get_trending_news(3)
        if trends:
            trend_list = "\n".join([f"- {t['title']}" for t in trends])
            user_context += f"System Update: Today's top global trending news events are:\n{trend_list}\n(Use this context if the user asks about current events.)\n"

        augmented_message = req.message
        if user_context:
            augmented_message = (
                f"[System Context: {user_context}]\nUser Message: {req.message}"
            )

        # DB Session Handling
        session_id = req.session_id
        if not req.is_private:
            uid = (
                user_token.get("user_id") or user_token.get("uid")
                if user_token
                else (x_device_id or "anonymous")
            )
            if not session_id:
                session_id = uuid.uuid4().hex
                new_session = ChatSession(
                    id=session_id, user_id=uid, title=req.message[:30].strip()
                )
                db.add(new_session)
                db.commit()

            user_msg = ChatMessage(
                session_id=session_id, role="user", content=req.message
            )
            db.add(user_msg)
            db.commit()

        # Format history
        history_str = ""
        for msg in req.history[-6:]:
            history_str += f"{msg.role.capitalize()}: {msg.content}\n"

        # Lazy load heavy AI modules to speed up boot time and save RAM
        from src.rag_pipeline import answer_question
        
        response = answer_question(
            augmented_message,
            language=req.language or "English",
            history=history_str,
            is_private=bool(req.is_private),
            is_deep_research=bool(req.is_deep_research),
        )

        # Parse for file generation tags
        # PDF
        pdf_match = re.search(
            r"<GENERATE_PDF>\s*<TITLE>(.*?)</TITLE>\s*<CONTENT>(.*?)</CONTENT>\s*</GENERATE_PDF>",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if pdf_match:
            title = pdf_match.group(1).strip()
            content = pdf_match.group(2).strip()
            filename = f"{uuid.uuid4().hex[:8]}.pdf"
            filepath = os.path.join("web", "downloads", filename)
            os.makedirs(os.path.join("web", "downloads"), exist_ok=True)

            from src.file_generator import generate_pdf
            if generate_pdf(title, content, filepath):
                download_link = (
                    f"\n\n**[📥 Download {title} (PDF)](/downloads/{filename})**"
                )
                response = response.replace(pdf_match.group(0), download_link)

        # Word
        word_match = re.search(
            r"<GENERATE_WORD>\s*<TITLE>(.*?)</TITLE>\s*<CONTENT>(.*?)</CONTENT>\s*</GENERATE_WORD>",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if word_match:
            title = word_match.group(1).strip()
            content = word_match.group(2).strip()
            filename = f"{uuid.uuid4().hex[:8]}.docx"
            filepath = os.path.join("web", "downloads", filename)
            os.makedirs(os.path.join("web", "downloads"), exist_ok=True)

            from src.file_generator import generate_word
            if generate_word(title, content, filepath):
                download_link = (
                    f"\n\n**[📥 Download {title} (Word)](/downloads/{filename})**"
                )
                response = response.replace(word_match.group(0), download_link)

        # Image
        image_match = re.search(
            r"\[GENERATE_IMAGE:\s*(.*?)\]",
            response,
            re.DOTALL,
        )
        if image_match:
            content = image_match.group(1).strip()
            parts = [p.strip() for p in content.split("|")]
            
            if len(parts) >= 3 and parts[-2].isdigit() and parts[-1].isdigit():
                prompt = " | ".join(parts[:-2]).strip()
                width = parts[-2]
                height = parts[-1]
            else:
                prompt = content
                width = "1024"
                height = "1024"

            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux-realism&nologo=true&enhance=true"
            image_md = (
                f"\n\n![Generated Image]({image_url})\n*Generated based on: {prompt}*"
            )
            response = response.replace(image_match.group(0), image_md)

        # Data Charts (QuickChart.io)
        chart_match = re.search(
            r"<GENERATE_CHART>\s*(.*?)\s*</GENERATE_CHART>",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if chart_match:
            chart_json_str = chart_match.group(1).strip()
            # Clean up potential markdown formatting around json
            chart_json_str = re.sub(r"^```(?:json)?\n?", "", chart_json_str)
            chart_json_str = re.sub(r"\n?```$", "", chart_json_str)
            
            import urllib.parse
            encoded_chart = urllib.parse.quote(chart_json_str)
            chart_url = f"https://quickchart.io/chart?c={encoded_chart}&bkg=white"
            chart_md = f"\n\n![AI Generated Chart]({chart_url})\n"
            response = response.replace(chart_match.group(0), chart_md)

        # Infographic
        info_match = re.search(
            r"<GENERATE_INFOGRAPHIC>\s*<TITLE>(.*?)</TITLE>\s*<CONTENT>(.*?)</CONTENT>\s*</GENERATE_INFOGRAPHIC>",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if info_match:
            title = info_match.group(1).strip()
            content = info_match.group(2).strip()
            
            lines = content.split('\n')
            formatted_lines = [f"> {line}" for line in lines]
            card_content = "\n".join(formatted_lines)
            
            formatted_infographic = f"\n\n> 📊 **{title.upper()}**\n> \n{card_content}\n\n"
            response = response.replace(info_match.group(0), formatted_infographic)

        # Format DeepSeek <think> tags gracefully
        think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL | re.IGNORECASE)
        if think_match:
            thought_process = think_match.group(1).strip()
            thought_md = f"> 🧠 **Risore's Internal Thought Process**\n> \n> {thought_process.replace(chr(10), chr(10) + '> ')}\n\n"
            response = response.replace(think_match.group(0), thought_md)

        if not req.is_private and session_id:
            ai_msg = ChatMessage(
                session_id=session_id, role="assistant", content=response
            )
            db.add(ai_msg)
            db.commit()

        return {"response": response, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback")
async def feedback_endpoint(req: FeedbackRequest):
    try:
        feedback_file = os.path.join(BASE_DIR, "feedback.json")
        feedback_data = []
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                try:
                    feedback_data = json.load(f)
                except Exception:
                    pass

        feedback_data.append(
            {"query": req.user_query, "response": req.ai_response, "rating": req.rating}
        )

        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, indent=4)

        return {"status": "success", "message": "Feedback recorded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat_with_file")
async def chat_with_file_endpoint(
    message: str = Form(...),
    language: str = Form("English"),
    is_private: bool = Form(False),
    is_deep_research: bool = Form(False),
    session_id: Optional[str] = Form(None),
    ai_mode: str = Form("Default"),
    files: List[UploadFile] = File(...),
    user_token: dict = Depends(get_current_user),
    x_device_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    try:
        user_context = ""
        if ai_mode and ai_mode in MODE_INSTRUCTIONS:
            user_context += f"{MODE_INSTRUCTIONS[ai_mode]}\n\n"

        if user_token:
            uid = user_token.get("user_id") or user_token.get("uid")
            user = db.query(User).filter(User.id == uid).first()
            if user and user.name:
                user_context += f"The user's name is {user.name}.\n"
            tasks = (
                db.query(Task)
                .filter(Task.user_id == uid, Task.completed == False)
                .all()
            )
            if tasks:
                task_list = "\n".join([f"- {t.task_content}" for t in tasks])
                user_context += f"The user's current pending tasks are:\n{task_list}\n"

        extracted_text = ""
        image_contents = []

        for file in files:
            file_ext = file.filename.split(".")[-1].lower()
            
            if file_ext == "pdf":
                import pdfplumber
                with pdfplumber.open(file.file) as pdf:
                    extracted_text += "\n" + "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                    
            elif file_ext in ["doc", "docx"]:
                from docx import Document
                doc = Document(file.file)
                extracted_text += "\n" + "\n".join([para.text for para in doc.paragraphs])
                
            elif file_ext == "txt":
                extracted_text += "\n" + (await file.read()).decode("utf-8")
                
            elif file_ext in ["jpg", "jpeg", "png", "webp"]:
                image_data = await file.read()
                base64_image = base64.b64encode(image_data).decode("utf-8")
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{file_ext};base64,{base64_image}"}
                })

        if image_contents:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key and api_key != "your_free_groq_api_key_here":
                from groq import Groq
                client = Groq(api_key=api_key)
                try:
                    user_prompt_lower = message.lower()
                    wants_generation = any(w in user_prompt_lower for w in ["make", "generate", "create", "turn", "convert", "change"]) and any(w in user_prompt_lower for w in ["image", "picture", "anime", "style", "look", "drawing"])
                    
                    if wants_generation:
                        system_prompt = "Describe exactly what is in these images in extreme detail (subjects, composition, lighting, poses, colors). If the images contain a cartoon, drawing, or video game character, describe them as if they were a real, living human being in a real photograph. DO NOT mention that it is a game, drawing, or 3D render. Just describe the visual contents as a real scene so it can be recreated perfectly."
                    else:
                        system_prompt = f"""You are an advanced, highly accurate Vision AI expert. Analyze the provided image(s) deeply.
- **Education/Math**: If the image contains a math problem, diagram, handwritten notes, or textbook excerpt, transcribe it perfectly and solve/explain it step-by-step as an expert tutor.
- **Fitness/Food**: If the image contains food, act as a nutritionist: identify the ingredients, estimate the portion sizes, and provide an estimated nutritional breakdown.
- **Text/OCR**: Extract any visible text perfectly without hallucinating.
- **General**: Identify all objects, context, and details accurately.

CRITICAL INSTRUCTION: DO NOT generate a preamble. NEVER mention what is NOT in the image (e.g., do NOT say "The image does not contain math problems or food"). Just answer the user's prompt directly based on what IS in the image.

User Message: {message}
Please answer in {language}."""

                    content = [{"type": "text", "text": system_prompt}] + image_contents

                    vision_response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[{"role": "user", "content": content}],
                    )

                    vision_text = vision_response.choices[0].message.content

                    if wants_generation:
                        width = 1024
                        height = 1024
                        msg_lower = message.lower()
                        if "4k" in msg_lower or "uhd" in msg_lower or "landscape" in msg_lower:
                            width, height = 3840, 2160
                        elif "1080p" in msg_lower or "16:9" in msg_lower:
                            width, height = 1920, 1080
                        elif "portrait" in msg_lower or "vertical" in msg_lower or "9:16" in msg_lower:
                            width, height = 2160, 3840

                        combined_prompt = f"{vision_text}. Applied style: {message}. Photorealistic, 8k resolution, cinematic lighting, shot on DSLR, highly detailed masterpiece."
                        combined_prompt = combined_prompt[:800]
                        encoded_prompt = urllib.parse.quote(combined_prompt)
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux-realism&width={width}&height={height}&nologo=true&enhance=true"
                        return {"response": f"I have transformed your image based on your request!\n\n![Generated Image]({image_url})\n*Style applied: {message}*"}
                    else:
                        extracted_text += f"\n[Vision AI Image Analysis: {vision_text}]\n"
                except Exception as ve:
                    extracted_text += f"\n[Vision AI Error: Could not analyze image. {str(ve)}]\n"
            else:
                extracted_text += "\n[Vision AI Error: No GROQ_API_KEY provided to analyze image.]\n"
        
        elif not extracted_text:
            return {"response": "I cannot read the provided files. Please upload a PDF, Word document, TXT, or Image."}

        # If it's a document (text extracted), pass it to the RAG pipeline
        if extracted_text:
            # DB Session Handling
            if not is_private:
                uid = (
                    user_token.get("user_id") or user_token.get("uid")
                    if user_token
                    else (x_device_id or "anonymous")
                )
                if not session_id:
                    session_id = uuid.uuid4().hex
                    new_session = ChatSession(
                        id=session_id, user_id=uid, title=message[:30]
                    )
                    db.add(new_session)
                    db.commit()

                user_msg = ChatMessage(
                    session_id=session_id,
                    role="user",
                    content=message + " [Attached File]",
                )
                db.add(user_msg)
                db.commit()

            augmented_message = ""
            if user_context:
                augmented_message += f"[System Context: {user_context}]\n"
            augmented_message += f"Document content: {extracted_text[:20000]}\n\nUser Question: {message}"
            # Lazy load heavy AI modules
            from src.rag_pipeline import answer_question
            
            response = answer_question(
                augmented_message,
                language=language,
                history="",
                is_private=is_private,
                is_deep_research=is_deep_research,
            )

            # Data Charts (QuickChart.io)
            chart_match = re.search(
                r"<GENERATE_CHART>\s*(.*?)\s*</GENERATE_CHART>",
                response,
                re.DOTALL | re.IGNORECASE,
            )
            if chart_match:
                chart_json_str = chart_match.group(1).strip()
                chart_json_str = re.sub(r"^```(?:json)?\n?", "", chart_json_str)
                chart_json_str = re.sub(r"\n?```$", "", chart_json_str)
                
                import urllib.parse
                encoded_chart = urllib.parse.quote(chart_json_str)
                chart_url = f"https://quickchart.io/chart?c={encoded_chart}&bkg=white"
                chart_md = f"\n\n![AI Generated Chart]({chart_url})\n"
                response = response.replace(chart_match.group(0), chart_md)

            # Parse Infographic for file chats as well
            info_match = re.search(
                r"<GENERATE_INFOGRAPHIC>\s*<TITLE>(.*?)</TITLE>\s*<CONTENT>(.*?)</CONTENT>\s*</GENERATE_INFOGRAPHIC>",
                response,
                re.DOTALL | re.IGNORECASE,
            )
            if info_match:
                title = info_match.group(1).strip()
                content = info_match.group(2).strip()
                lines = content.split('\n')
                formatted_lines = [f"> {line}" for line in lines]
                card_content = "\n".join(formatted_lines)
                formatted_infographic = f"\n\n> 📊 **{title.upper()}**\n> \n{card_content}\n\n"
                response = response.replace(info_match.group(0), formatted_infographic)

            if not is_private and session_id:
                ai_msg = ChatMessage(
                    session_id=session_id, role="assistant", content=response
                )
                db.add(ai_msg)
                db.commit()

            return {"response": response, "session_id": session_id}
        else:
            return {
                "response": "I couldn't extract any readable text from the uploaded file.",
                "session_id": session_id,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TaskCreate(BaseModel):
    task_content: str


@app.post("/api/sync_user")
async def sync_user(
    user_token: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = user_token.get("user_id") or user_token.get("uid")
    email = user_token.get("email")
    name = user_token.get("name")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, email=email, name=name)
        db.add(user)
    else:
        if name:
            user.name = name
        if email:
            user.email = email
    db.commit()
    return {"status": "synced"}


@app.get("/api/tasks")
async def get_tasks(
    user_token: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = user_token.get("user_id") or user_token.get("uid")
    tasks = db.query(Task).filter(Task.user_id == uid).all()
    return [
        {"id": t.id, "task_content": t.task_content, "completed": t.completed}
        for t in tasks
    ]


@app.post("/api/tasks")
async def create_task(
    task: TaskCreate,
    user_token: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = user_token.get("user_id") or user_token.get("uid")
    new_task = Task(user_id=uid, task_content=task.task_content)
    db.add(new_task)
    db.commit()
    return {"status": "created", "id": new_task.id}


@app.put("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    completed: bool,
    user_token: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = user_token.get("user_id") or user_token.get("uid")
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == uid).first()
    if task:
        task.completed = completed
        db.commit()
        return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: int,
    user_token: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = user_token.get("user_id") or user_token.get("uid")
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == uid).first()
    if task:
        db.delete(task)
        db.commit()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Task not found")


@app.get("/api/sessions")
async def get_sessions(
    user_token: dict = Depends(get_current_user),
    x_device_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    uid = (
        user_token.get("user_id") or user_token.get("uid")
        if user_token
        else (x_device_id or "anonymous")
    )
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == uid)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        {"id": s.id, "title": s.title, "created_at": s.created_at} for s in sessions
    ]


@app.get("/api/sessions/{session_id}")
async def get_session_messages(
    session_id: str,
    user_token: dict = Depends(get_current_user),
    x_device_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    uid = (
        user_token.get("user_id") or user_token.get("uid")
        if user_token
        else (x_device_id or "anonymous")
    )
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == uid)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in messages
    ]


@app.get("/api/trends")
async def get_trends_api():
    return get_trending_news(3)


@app.get("/api/ping")
async def ping():
    return {"status": "awake"}


@app.get("/api/proactive")
async def get_proactive_insights(
    db: Session = Depends(get_db)
):
    from src.database import ProactiveSuggestion
    
    # Fetch latest unread insight
    insight = db.query(ProactiveSuggestion).filter(ProactiveSuggestion.is_read == False).order_by(ProactiveSuggestion.created_at.desc()).first()
    
    if insight:
        insight.is_read = True
        db.commit()
        return {"has_insight": True, "insight": insight.content}
    return {"has_insight": False}


def keep_awake():
    """Background daemon to ping the server every 10 minutes to prevent Render from sleeping."""
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        return
        
    ping_url = f"{url}/api/ping"
    while True:
        try:
            time.sleep(600)  # 600 seconds = 10 minutes
            requests.get(ping_url, timeout=10)
            print(f"Keep-alive daemon pinged {ping_url} successfully.")
        except Exception as e:
            print(f"Keep-alive daemon failed to ping {ping_url}: {e}")


@app.on_event("startup")
async def startup_event():
    if os.environ.get("RENDER_EXTERNAL_URL"):
        print("Starting anti-sleep keep-alive daemon...")
        daemon_thread = threading.Thread(target=keep_awake, daemon=True)
        daemon_thread.start()

    print("Starting Autonomous Agent daemon...")
    from src.autonomous_agent import autonomous_daemon
    agent_thread = threading.Thread(target=autonomous_daemon, args=(60,), daemon=True)
    agent_thread.start()


# Mount the static web files so the website works exactly like ChatGPT on the root URL
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
