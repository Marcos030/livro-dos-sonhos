import json
import logging
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import create_agent, DB_PATH

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

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
    logger.info(f"[/chat] user_id={request.user_id} session_id={session_id} msg={request.message[:50]!r}")

    try:
        agent = create_agent(user_id=request.user_id, session_id=session_id)
        response = agent.run(request.message)
        content = response.content if response and response.content else ""
        logger.info(f"[/chat] resposta gerada ({len(content)} chars)")
        return ChatResponse(response=content, session_id=session_id, user_id=request.user_id)
    except Exception as e:
        logger.error(f"[/chat] erro: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Envia um sonho e recebe a resposta em streaming via SSE com eventos de progresso."""
    from agno.run.agent import RunEvent

    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"[/chat/stream] RECEBIDO user_id={request.user_id} session_id={session_id} msg={request.message[:50]!r}")

    def event_generator():
        try:
            logger.info(f"[/chat/stream] iniciando gerador para user_id={request.user_id}")
            agent = create_agent(user_id=request.user_id, session_id=session_id)

            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

            content_chunks = 0
            for chunk in agent.run(request.message, stream=True, stream_events=True):
                ev = chunk.event

                if ev == RunEvent.run_started.value:
                    logger.info("[/chat/stream] evento: RunStarted")
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'Analisando seu sonho...'})}\n\n"

                elif ev == RunEvent.model_request_started.value:
                    logger.info("[/chat/stream] evento: ModelRequestStarted")
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'Consultando os palpites...'})}\n\n"

                elif ev == RunEvent.run_content.value:
                    if chunk.content is not None:
                        content_chunks += 1
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"

                elif ev == RunEvent.memory_update_started.value:
                    logger.info("[/chat/stream] evento: MemoryUpdateStarted")
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'Registrando na memória...'})}\n\n"

                elif ev == RunEvent.run_completed.value:
                    logger.info(f"[/chat/stream] RunCompleted — {content_chunks} chunks enviados")
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

                elif ev == RunEvent.run_error.value:
                    error_msg = chunk.content if chunk.content else "Erro desconhecido"
                    logger.error(f"[/chat/stream] RunError: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

        except Exception as e:
            logger.error(f"[/chat/stream] exceção no gerador: {e}", exc_info=True)
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


# Serve o frontend — tenta Path(__file__) e fallback para Path.cwd()
def _resolve_frontend() -> Path | None:
    candidates = [
        Path(__file__).resolve().parent.parent / "frontend",
        Path.cwd() / "frontend",
    ]
    for p in candidates:
        if (p / "index.html").exists():
            return p
    return None

_frontend_dir = _resolve_frontend()
if _frontend_dir:
    logger.info(f"Servindo frontend de: {_frontend_dir}")
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
else:
    logger.warning("Pasta frontend não encontrada — servindo apenas a API.")


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
