# Codebase Concerns

**Analysis Date:** 2026-03-14

## Tech Debt

**CORS Open to All Origins:**
- Issue: CORS allows all origins (`allow_origins=["*"]`) in `backend/app/main.py`
- Files: `backend/app/main.py` (lines 29-35)
- Impact: Any website can make API requests to the backend
- Fix approach: Restrict to specific frontend origin in production

**Hardcoded Dummy API Key for Embeddings:**
- Issue: RAG service uses "dummy-key-for-initialization" when no API key is provided
- Files: `backend/app/services/rag_service.py` (line 30)
- Impact: Embeddings may fail silently or use incorrect endpoint
- Fix approach: Require valid API key or use a mock implementation for development

**Duplicate Deduplication Logic:**
- Issue: Text deduplication is implemented in both backend (`llm_service.py`) and frontend (`App.tsx`)
- Files: `backend/app/services/llm_service.py` (lines 24-110), `frontend/src/App.tsx` (lines 12-46)
- Impact: Maintenance burden, inconsistent deduplication behavior
- Fix approach: Consolidate deduplication in backend only

**In-Memory Concurrency Control:**
- Issue: GroupChatService uses in-memory `_active_loops` dict for concurrency control
- Files: `backend/app/services/group_chat_service.py` (line 17)
- Impact: Does not work with multiple server instances (no horizontal scaling)
- Fix approach: Use Redis or database-based locking

**StaticPool for SQLite:**
- Issue: Database uses StaticPool (single connection) in `backend/app/database.py`
- Files: `backend/app/database.py` (line 10)
- Impact: Poor performance under concurrent load
- Fix approach: Use NullPool or proper connection pooling, migrate to PostgreSQL for production

**Debug Print Statements:**
- Issue: Extensive debug print statements throughout codebase
- Files: Multiple files including `llm_service.py`, `group_chat_service.py`, `chat.py`, `group_chat.py`
- Impact: Logs sensitive information, degrades performance
- Fix approach: Use proper logging module (logging.INFO, logging.DEBUG)

---

## Known Bugs

**Incorrect Assignment in chat.py:**
- Issue: `conversation.updated_at = Message.created_at` assigns column object, not value
- Files: `backend/app/routers/chat.py` (line 112)
- Trigger: Any chat message sent
- Workaround: Should be `conversation.updated_at = datetime.utcnow()`

**Inconsistent Token Estimation:**
- Issue: Token estimation uses rough formula (chars/2) which is inaccurate
- Files: `backend/app/services/group_chat_service.py` (lines 279-298)
- Impact: May truncate or keep too many messages

---

## Security Considerations

**No Authentication:**
- Risk: All API endpoints are publicly accessible without authentication
- Files: All routers in `backend/app/routers/`
- Current mitigation: None
- Recommendations: Add JWT or session-based authentication

**No Input Validation:**
- Risk: No sanitization of user inputs (messages, bot names, prompts)
- Files: Routers accept user input without validation
- Recommendations: Add Pydantic validation and input sanitization

**API Keys in Environment:**
- Risk: API keys may be logged in debug output
- Files: `backend/app/config.py`, `backend/app/services/llm_service.py`
- Current mitigation: Keys come from environment
- Recommendations: Ensure debug logging excludes sensitive data

---

## Performance Bottlenecks

**Synchronous Regex Deduplication:**
- Problem: Complex deduplication runs synchronously, blocking the event loop
- Files: `backend/app/services/llm_service.py` (lines 24-110)
- Cause: 15+ iterations with multiple regex operations on potentially large text
- Improvement path: Move to thread pool or optimize algorithm

**Multiple Database Commits in Loops:**
- Problem: Each bot response commits to database individually
- Files: `backend/app/routers/group_chat.py`, `backend/app/services/group_chat_service.py`
- Impact: Slow response times for multi-bot conversations
- Improvement path: Batch commits or use transactions

**No Response Caching:**
- Problem: Identical queries re-call LLM every time
- Files: All chat endpoints
- Improvement path: Add caching layer (Redis) for repeated queries

---

## Fragile Areas

**RAG Service Embeddings Initialization:**
- Files: `backend/app/services/rag_service.py` (lines 24-37)
- Why fragile: Embeddings created with dummy key may fail silently, causing RAG to not work
- Safe modification: Add validation that embeddings are working before use

**GroupChatService Locking:**
- Files: `backend/app/services/group_chat_service.py` (lines 17-33)
- Why fragile: In-memory dictionary resets on server restart, no persistence
- Safe modification: Use database or Redis for lock state

**Complex Deduplication Regex:**
- Files: `backend/app/services/llm_service.py` (lines 24-110)
- Why fragile: 15 iterations with multiple regex patterns - hard to understand and maintain
- Safe modification: Simplify or document heavily

---

## Scaling Limits

**SQLite Database:**
- Current capacity: Single user, small dataset
- Limit: No concurrent writes, file-based
- Scaling path: Migrate to PostgreSQL

**In-Memory State:**
- Current capacity: Single server instance
- Limit: No horizontal scaling with multiple instances
- Scaling path: Use Redis for session/state management

**Embedding API:**
- Current capacity: Depends on API rate limits
- Limit: OpenAI/MiniMax rate limits
- Scaling path: Add request queuing and rate limiting

---

## Dependencies at Risk

**LangChain Community:**
- Risk: Version compatibility issues between langchain packages
- Impact: RAG functionality may break on dependency updates
- Migration plan: Pin specific versions, consider migrating to langchain-core

**Anthropic SDK:**
- Risk: API changes may break existing code
- Impact: Chat functionality depends on SDK stability
- Migration plan: Use httpx directly for more control

---

## Missing Critical Features

**Error Recovery:**
- Problem: No retry logic for failed API calls or database operations
- Blocks: Reliable production deployment

**Rate Limiting:**
- Problem: No protection against abuse
- Blocks: Public deployment

**Health Checks:**
- Problem: Basic health check only returns "healthy" without verifying dependencies
- Blocks: Proper container orchestration

---

## Test Coverage Gaps

**No Backend Tests:**
- What's not tested: All backend logic (routers, services)
- Files: `backend/app/routers/`, `backend/app/services/`
- Risk: Bugs may not be caught until production
- Priority: High

**No Frontend Tests:**
- What's not tested: React components and state management
- Files: `frontend/src/`
- Risk: UI bugs and regressions
- Priority: Medium

---

*Concerns audit: 2026-03-14*
