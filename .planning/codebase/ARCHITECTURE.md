# Architecture

**Analysis Date:** 2026-03-14

## Pattern Overview

**Overall:** Layered REST API with Service Repository Pattern

**Key Characteristics:**
- FastAPI-based backend with async SQLAlchemy ORM
- React + TypeScript frontend with Vite
- Completely separated dual chat systems (1-on-1 and Group chat)
- Streaming response support for real-time chat experience

## Layers

**API Layer (Routers):**
- Purpose: HTTP endpoint definitions
- Location: `backend/app/routers/`
- Contains: `bots.py`, `chat.py`, `group_chat.py`, `documents.py`, `users.py`, `groups.py`
- Depends on: Services, Models
- Used by: Frontend clients

**Service Layer:**
- Purpose: Business logic implementation
- Location: `backend/app/services/`
- Contains: `llm_service.py` (LLM integration), `rag_service.py` (document retrieval), `group_chat_service.py` (multi-bot chat)
- Depends on: Models, External APIs (MiniMax)
- Used by: Routers

**Data Access Layer (Models):**
- Purpose: Database schema and ORM models
- Location: `backend/app/models.py`
- Contains: `Bot`, `Conversation`, `Message`, `Document`, `User`, `Group`, `GroupConversation`, `GroupMessage`
- Depends on: SQLAlchemy
- Used by: Routers, Services

**Database Layer:**
- Purpose: Database connection management
- Location: `backend/app/database.py`
- Contains: Async engine, session factory, initialization
- Depends on: SQLite (aiosqlite)

**Frontend Layer:**
- Purpose: UI and API integration
- Location: `frontend/src/`
- Contains: Components, API clients, Types
- Depends on: React, TypeScript, Fetch API
- Uses: Backend REST APIs

## Data Flow

**1-on-1 Chat Flow:**
1. User sends message via `frontend/src/App.tsx` (ChatPanel component)
2. HTTP POST to `/chat/` endpoint (`backend/app/routers/chat.py`)
3. Router retrieves Bot and Conversation from database
4. Router calls `llm_service.chat()` with messages and context
5. LLM service calls MiniMax API via Anthropic SDK
6. Response saved to database as Message
7. Response returned to frontend for display

**Group Chat Flow:**
1. User selects multiple bots and starts group chat
2. HTTP POST to `/group-chat/start-stream` endpoint
3. Router calls `group_chat_service.start_group_chat_stream()`
4. Service iterates through bots, calls LLM for each
5. Stream responses back to frontend using Server-Sent Events
6. Frontend renders each bot's response in real-time

**Document RAG Flow:**
1. User uploads document via `ChatPanel`
2. HTTP POST to `/documents/{bot_id}/upload`
3. RAG service extracts text and stores in vector store
4. On chat with `use_docs=true`, RAG performs similarity search
5. Relevant context appended to LLM prompt

## Key Abstractions

**Bot Entity:**
- Represents an AI chatbot with personality
- Examples: `backend/app/models.py` - `Bot` class
- Pattern: SQLAlchemy ORM model with relationships

**Conversation Entity:**
- Represents a chat session
- Examples: `Conversation` (1-on-1), `GroupConversation` (group)
- Pattern: Separate models for isolation

**Group System:**
- Manages collections of bots for group chat
- Examples: `Group`, `GroupMember`, `GroupConversation`, `GroupMessage`
- Pattern: Independent system completely isolated from 1-on-1 chat

**LLM Service:**
- Abstracts LLM API calls
- Examples: `backend/app/services/llm_service.py`
- Pattern: Singleton service class

**RAG Service:**
- Handles document retrieval
- Examples: `backend/app/services/rag_service.py`
- Pattern: Vector store integration

## Entry Points

**Backend Entry:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` or `python -m app.main`
- Responsibilities: FastAPI app initialization, CORS setup, router registration, lifespan management

**Frontend Entry:**
- Location: `frontend/src/main.tsx`
- Triggers: Vite dev server loads index.html which loads main.tsx
- Responsibilities: React app bootstrap, StrictMode rendering

**Component Entry:**
- Location: `frontend/src/App.tsx`
- Responsibilities: Main state management, routing between views (chat/group-chat/settings)

## Error Handling

**Strategy:** HTTPException with status codes + error messages

**Patterns:**
- 404: Resource not found (e.g., "机器人不存在")
- 500: Server errors (e.g., "AI 调用失败")
- Frontend catches errors and displays alerts

## Cross-Cutting Concerns

**Logging:** Print statements with `[DEBUG]` and `[ERROR]` prefixes in backend services

**Validation:** Pydantic schemas in `backend/app/schemas.py`

**Authentication:** None (open API for demo purposes)

**CORS:** Configured to allow all origins in `backend/app/main.py`

---

*Architecture analysis: 2026-03-14*
