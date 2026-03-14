# Codebase Structure

**Analysis Date:** 2026-03-14

## Directory Layout

```
D:/0正事/学习资料/testforcc/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings (pydantic)
│   │   ├── database.py          # SQLAlchemy async setup
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── bots.py
│   │   │   ├── chat.py
│   │   │   ├── group_chat.py
│   │   │   ├── documents.py
│   │   │   ├── users.py
│   │   │   └── groups.py
│   │   └── services/            # Business logic
│   │       ├── llm_service.py
│   │       ├── rag_service.py
│   │       └── group_chat_service.py
│   └── chatbot.db               # SQLite database
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # React entry point
│   │   ├── App.tsx              # Main component
│   │   ├── index.css            # Global styles
│   │   ├── components/          # React components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── GroupChatPanel.tsx
│   │   │   ├── BotModal.tsx
│   │   │   ├── GroupModal.tsx
│   │   │   └── SettingsPanel.tsx
│   │   ├── api/                 # API clients
│   │   │   ├── index.ts         # All API functions
│   │   │   └── config.ts        # API configuration
│   │   └── types/               # TypeScript interfaces
│   │       └── index.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── .venv/                       # Python virtual environment
└── .planning/codebase/          # This documentation
```

## Directory Purposes

**backend/app/routers:**
- Purpose: API route handlers
- Contains: HTTP endpoint definitions
- Key files: `bots.py`, `chat.py`, `group_chat.py`

**backend/app/services:**
- Purpose: Business logic layer
- Contains: LLM integration, RAG, group chat logic
- Key files: `llm_service.py`, `rag_service.py`, `group_chat_service.py`

**frontend/src/components:**
- Purpose: React UI components
- Contains: Sidebar, Chat panels, Modals
- Key files: `ChatPanel.tsx`, `GroupChatPanel.tsx`, `Sidebar.tsx`

**frontend/src/api:**
- Purpose: Backend API client
- Contains: Fetch wrappers for all endpoints
- Key files: `index.ts`

**frontend/src/types:**
- Purpose: TypeScript type definitions
- Contains: Interface definitions matching backend models

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI application startup
- `frontend/src/main.tsx`: React application bootstrap

**Configuration:**
- `backend/app/config.py`: Settings class with environment variables
- `backend/app/database.py`: Database connection setup

**Core Logic:**
- `backend/app/services/llm_service.py`: LLM API integration (MiniMax)
- `backend/app/services/group_chat_service.py`: Multi-bot chat orchestration

**Testing:**
- Not detected - no test directory found

## Naming Conventions

**Python Backend:**
- Files: `snake_case.py` (e.g., `llm_service.py`)
- Classes: `PascalCase` (e.g., `LLMService`)
- Functions: `snake_case` (e.g., `chat_stream`)
- Variables: `snake_case` (e.g., `bot_ids`)

**TypeScript Frontend:**
- Files: `PascalCase.tsx` for components (e.g., `ChatPanel.tsx`)
- Files: `camelCase.ts` for utilities (e.g., `config.ts`)
- Interfaces: `PascalCase` (e.g., `Bot`, `Conversation`)
- Variables: `camelCase` (e.g., `selectedBot`, `isLoading`)

**Database:**
- Tables: `snake_case` (e.g., `bots`, `group_conversations`)
- Columns: `snake_case` (e.g., `bot_id`, `created_at`)

## Where to Add New Code

**New Backend Feature:**
- API endpoint: `backend/app/routers/<feature>.py`
- Business logic: `backend/app/services/<feature>_service.py`
- Model extension: `backend/app/models.py`

**New Frontend Feature:**
- Component: `frontend/src/components/<Feature>.tsx`
- API call: `frontend/src/api/index.ts` (add to existing export)
- Type: `frontend/src/types/index.ts`

**New Service:**
- Implementation: `backend/app/services/<service_name>.service.py`
- Register in router: Import and use in `backend/app/routers/`

## Special Directories

**.venv:**
- Purpose: Python virtual environment dependencies
- Generated: Yes (by virtualenv/venv)
- Committed: No (in .gitignore)

**.planning/codebase:**
- Purpose: GSD codebase documentation
- Generated: Yes
- Committed: Yes (to .planning/codebase/)

---

*Structure analysis: 2026-03-14*
