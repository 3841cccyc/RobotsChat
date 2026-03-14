# Technology Stack

**Analysis Date:** 2026-03-14

## Languages

**Primary:**
- Python 3.x - Backend API, services, LLM integration
- TypeScript 5.9 - Frontend UI components
- JavaScript (ES2022) - Frontend runtime

**Secondary:**
- None detected

## Runtime

**Environment:**
- Python 3.x (venv in `.venv/`)
- Node.js 18+ (for frontend build)

**Package Manager:**
- Python: `pip` with `requirements.txt`
- Node.js: `npm` 10+ with `package-lock.json`

## Frameworks

**Core:**
- FastAPI 0.109.0 - Python web framework for REST API
- React 19.2.0 - Frontend UI framework
- Vite 8.0.0-beta.13 - Frontend build tool

**Testing:**
- Not detected in current configuration

**Build/Dev:**
- Uvicorn 0.27.0 - ASGI server for FastAPI
- TailwindCSS 3.4.17 - CSS utility framework
- ESLint 9.39.1 - JavaScript/TypeScript linting
- TypeScript 5.9 - Type checking

## Key Dependencies

**Backend Critical:**
- `anthropic` - MiniMax API SDK (compatible with Anthropic SDK)
- `langchain==0.1.4` - LLM application framework
- `langchain-openai==0.0.5` - OpenAI embeddings integration
- `langchain-community==0.0.16` - Community integrations
- `chromadb==0.4.22` - Vector database for RAG
- `pypdf==3.17.4` - PDF document loading
- `python-docx==1.1.0` - Word document loading

**Backend Infrastructure:**
- `sqlalchemy==2.0.25` - ORM
- `aiosqlite==0.19.0` - Async SQLite driver
- `pydantic==2.5.3` - Data validation
- `pydantic-settings==2.1.0` - Settings management

**Frontend Critical:**
- `react==19.2.0` - UI library
- `lucide-react==0.577.0` - Icon library
- `clsx==2.1.1` - Utility for class names
- `tailwind-merge==3.5.0` - Tailwind CSS utility

## Configuration

**Environment:**
- Configuration via `.env` files
- Backend: `backend/app/config.py` loads settings
- Key config: `backend/app/config.py` - Pydantic Settings class
- Default database: SQLite (`chatbot.db`)

**Build:**
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/tailwind.config.js` - Tailwind CSS configuration
- `frontend/eslint.config.js` - ESLint configuration

## Platform Requirements

**Development:**
- Python 3.x with venv
- Node.js 18+
- MiniMax API key (for LLM)
- OpenAI API key (optional, for embeddings)

**Production:**
- FastAPI with Uvicorn server
- SQLite database (or compatible)
- Frontend built with Vite (static files)

---

*Stack analysis: 2026-03-14*
