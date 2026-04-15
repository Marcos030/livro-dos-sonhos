import json
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent import create_agent, DB_PATH

load_dotenv()

app = FastAPI(
    title="Livro dos Sonhos API",
    description="Agente de IA especialista em interpretação de sonhos para o Jogo do Bicho",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str


class SessionInfo(BaseModel):
    session_id: str
    created_at: str | None = None


# --- Routes ---

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "Mestre dos Sonhos"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Envia um sonho para o Mestre dos Sonhos analisar (resposta completa)."""
    session_id = request.session_id or str(uuid.uuid4())

    try:
        agent = create_agent(
            user_id=request.user_id,
            session_id=session_id,
        )
        response = agent.run(request.message)
        content = response.content if response and response.content else ""

        return ChatResponse(
            response=content,
            session_id=session_id,
            user_id=request.user_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Envia um sonho e recebe a resposta em streaming via SSE."""
    session_id = request.session_id or str(uuid.uuid4())

    def event_generator():
        try:
            agent = create_agent(
                user_id=request.user_id,
                session_id=session_id,
            )

            # Envia o session_id como primeiro evento
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

            # Stream da resposta do agente
            response_stream = agent.run(request.message, stream=True)
            for event in response_stream:
                if event.content is not None:
                    yield f"data: {json.dumps({'type': 'content', 'content': event.content})}\n\n"

            # Sinaliza fim do stream
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/sessions/{user_id}", response_model=list[SessionInfo])
async def get_sessions(user_id: str, limit: int = 10):
    """Retorna as últimas sessões de um usuário."""
    import sqlite3

    if not DB_PATH.exists():
        return []

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT session_id, created_at
            FROM agent_sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            SessionInfo(session_id=row[0], created_at=row[1])
            for row in rows
        ]
    except Exception:
        return []


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
