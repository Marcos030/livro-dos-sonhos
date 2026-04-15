import os
from pathlib import Path

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from app.prompt import SYSTEM_PROMPT

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agents.db"


def create_agent(user_id: str, session_id: str | None = None) -> Agent:
    """Cria uma instância do agente Mestre dos Sonhos."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = SqliteDb(
        session_table="agent_sessions",
        db_file=str(DB_PATH),
    )

    agent = Agent(
        name="Mestre dos Sonhos",
        model=Claude(
            id="claude-sonnet-4-5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        db=db,
        # Memória: injeta histórico das últimas 10 interações no contexto
        add_history_to_context=True,
        num_history_runs=10,
        # Memória agentic: o agente decide o que memorizar sobre o usuário
        enable_agentic_memory=True,
        add_memories_to_context=True,
        # IDs
        user_id=user_id,
        session_id=session_id,
        # Prompt
        instructions=SYSTEM_PROMPT,
        markdown=True,
    )

    return agent
