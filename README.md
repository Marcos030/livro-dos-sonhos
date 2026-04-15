# Livro dos Sonhos 🔮

Agente de IA especialista em interpretação de sonhos para o Jogo do Bicho brasileiro.

Construído com [Agno](https://docs.agno.com), FastAPI e Claude (Anthropic).

## Como funciona

Você conta seu sonho e o **Mestre dos Sonhos** interpreta os símbolos, conectando-os à tradição popular do Jogo do Bicho. Ele retorna palpites com grupo, dezena, centena e milhar — tudo com explicação detalhada.

O agente mantém memória das suas conversas anteriores, identificando padrões recorrentes nos seus sonhos.

## Rodando localmente

### 1. Clone e instale

```bash
git clone https://github.com/seu-usuario/livro-dos-sonhos.git
cd livro-dos-sonhos
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure o .env

```bash
cp .env.example .env
# Edite o .env e adicione sua ANTHROPIC_API_KEY
```

### 3. Rode o servidor

```bash
python -m app.main
```

O servidor sobe em `http://localhost:8000`. Docs interativos em `http://localhost:8000/docs`.

## Endpoints da API

### `POST /chat`

Envia um sonho para análise.

```json
{
  "user_id": "marco",
  "message": "Sonhei que estava voando sobre o mar e vi uma cobra gigante",
  "session_id": null
}
```

Resposta:

```json
{
  "response": "### 🔮 Interpretação do Sonho\n...",
  "session_id": "uuid-gerado",
  "user_id": "marco"
}
```

### `GET /sessions/{user_id}?limit=10`

Retorna as últimas sessões do usuário.

### `GET /health`

Health check.

## Deploy no Render

1. Crie um repositório no GitHub com este código
2. Vá em [render.com](https://render.com) e conecte o repositório
3. O `render.yaml` já configura tudo — só adicione a `ANTHROPIC_API_KEY` nas variáveis de ambiente
4. Deploy automático a cada push

## Aviso Legal

Este projeto é apenas para fins de **entretenimento e educação**. O Jogo do Bicho é considerado contravenção penal no Brasil. Jogue com responsabilidade.
