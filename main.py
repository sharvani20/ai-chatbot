from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from database import init_db, log_message, get_history
from datetime import datetime
import uuid
import os

app = FastAPI(title="AI Chatbot API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Groq setup ────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set!")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are a helpful, friendly, and intelligent customer support assistant. "
    "Answer clearly and concisely. If you don't know something, say so honestly."
)

# ── In-memory session store (session_id → list of messages) ──────────────────
sessions: dict = {}

# ── Initialize DB ─────────────────────────────────────────────────────────────
init_db()
print("Chatbot API ready with Groq (Llama 3) ✅")


# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    timestamp: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "AI Chatbot API (Groq) is running 🚀", "docs": "/docs"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())

    # Initialize session history
    if session_id not in sessions:
        sessions[session_id] = []

    # Add user message
    sessions[session_id].append({"role": "user", "content": req.message})

    # Keep last 20 messages to stay within token limits
    history = sessions[session_id][-20:]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=512,
            temperature=0.7,
        )
        reply = response.choices[0].message.content

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    # Save assistant reply to session
    sessions[session_id].append({"role": "assistant", "content": reply})

    timestamp = datetime.utcnow().isoformat()
    log_message(session_id, req.message, reply, timestamp)

    return ChatResponse(reply=reply, session_id=session_id, timestamp=timestamp)


@app.get("/history/{session_id}")
def history(session_id: str):
    rows = get_history(session_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, "messages": rows}


@app.delete("/history/{session_id}")
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"message": f"Session {session_id} context cleared."}