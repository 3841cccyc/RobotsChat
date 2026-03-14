# External Integrations

**Analysis Date:** 2026-03-14

## APIs & External Services

**LLM (Large Language Model):**
- MiniMax API (via Anthropic SDK) - Primary chat completion
  - SDK: `anthropic` Python package
  - API Key: `MINIMAX_API_KEY` or `minimax_api_key` in config
  - Base URL: `https://api.minimaxi.com/anthropic` (configurable)
  - Model: `MiniMax-M2.5` (configurable)
  - Implementation: `backend/app/services/llm_service.py`

**Embeddings:**
- OpenAI API (optional, for vector embeddings)
  - SDK: `langchain-openai` (OpenAIEmbeddings)
  - API Key: `OPENAI_API_KEY` or `openai_api_key` in config
  - Model: `text-embedding-3-small` (configurable)
  - Dimensions: 1536 (configurable)
  - Implementation: `backend/app/services/rag_service.py`

## Data Storage

**Databases:**
- SQLite
  - Connection: `sqlite+aiosqlite:///./chatbot.db` (configurable via `database_url`)
  - Client: SQLAlchemy 2.0.25 with async support
  - Implementation: `backend/app/database.py`
  - ORM Models: `backend/app/models.py`

**Vector Storage:**
- ChromaDB
  - Purpose: RAG (Retrieval-Augmented Generation) for document embeddings
  - Persisted at: `./vector_stores/` (configurable)
  - Implementation: `backend/app/services/rag_service.py`

**File Storage:**
- Local filesystem only
  - Documents stored in: `./uploads/` or application working directory
  - Supported formats: PDF, DOC/DOCX, TXT

**Caching:**
- None detected

## Authentication & Identity

**Auth Provider:**
- None (custom implementation)
  - Simple session/user management via database
  - No OAuth or external identity provider
  - Implementation: `backend/app/routers/users.py`, `backend/app/models.py`

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Python `print()` statements in services
- Uvicorn access logs (enabled via `access_log=True`)
- Implementation: Console output in `backend/app/main.py`

## CI/CD & Deployment

**Hosting:**
- Not configured (local development)

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- `MINIMAX_API_KEY` - MiniMax API key for LLM
- `OPENAI_API_KEY` - OpenAI API key for embeddings (optional)
- `database_url` - Database connection string (optional, has default)
- `minimax_base_url` - MiniMax API endpoint (optional, has default)
- `minimax_model` - LLM model name (optional, has default)
- `embedding_model` - Embedding model name (optional, has default)
- `host` - Server host (optional, default: 0.0.0.0)
- `port` - Server port (optional, default: 8000)

**Secrets location:**
- `backend/.env` file (gitignored, not committed)
- Template: `backend/.env.example`

## Webhooks & Callbacks

**Incoming:**
- None detected (REST API only)

**Outgoing:**
- None detected

---

*Integration audit: 2026-03-14*
