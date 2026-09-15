from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config import STATIC_DIR
from src.rag import get_rag_service
from src.memory import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-load RAG service, embeddings, and FAISS vector store into memory
    print("[*] Starting up FastAPI server...")
    print("[*] Pre-warming RAG service and vector store into memory...")
    try:
        get_rag_service()
        print("[+] RAG service pre-loaded successfully. Server is ready!")
    except Exception as e:
        print(f"[!] Warning: RAG service could not be pre-loaded: {e}")
    yield
    print("[*] Shutting down FastAPI server...")


app = FastAPI(
    title="DocAnalyzer API",
    description="Enterprise Document & Company Policy RAG API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for external website integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or prompt")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversational memory")


class SourceItem(BaseModel):
    source: str
    page: Any
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    session_id: str


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DocAnalyzer RAG API",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        session_id = session_manager.get_or_create_session(request.session_id)
        chat_history = session_manager.format_history_for_prompt(session_id)

        rag = get_rag_service()
        result = rag.query(request.message, chat_history=chat_history)

        session_manager.add_turn(session_id, request.message, result["answer"])

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/{session_id}")
async def clear_session(session_id: str):
    session_manager.clear(session_id)
    return {"message": f"Session {session_id} reset successfully."}


# Serve full-page chat UI at root
@app.get("/")
async def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "DocAnalyzer API is running. UI not found in static folder."}


# Mount static directory for widget, css, and demo files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
