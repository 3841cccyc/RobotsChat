# Coding Conventions

**Analysis Date:** 2026-03-14

## Language Conventions

### Python (Backend)

**Files:**
- snake_case for filenames: `llm_service.py`, `group_chat.py`
- Single-purpose modules

**Functions:**
- snake_case: `async def chat()`, `def _deduplicate_text()`

**Variables:**
- snake_case: `api_key`, `conversation_id`, `system_prompt`

**Types/Classes:**
- PascalCase: `LLMService`, `Bot`, `Conversation`

**Constants:**
- UPPER_SNAKE_CASE: `MAX_ITERATIONS = 15`

**Type Annotations:**
- Used for function parameters and return types
- Example: `async def chat(messages: List[Dict[str, str]], system_prompt: str = "") -> str:`

### TypeScript/React (Frontend)

**Files:**
- PascalCase for components: `ChatPanel.tsx`, `BotModal.tsx`
- camelCase for utilities: `config.ts`, `api.ts`

**Functions:**
- camelCase: `handleSendMessage()`, `loadBots()`

**Variables:**
- camelCase: `selectedBot`, `currentConversationId`

**Interfaces/Types:**
- PascalCase: `Bot`, `ChatRequest`, `ViewMode`

**Constants:**
- PascalCase for enums/types: `'chat' | 'group-chat' | 'settings'`

## Code Style

### Backend (Python)

**Formatting:**
- No explicit formatter configured (PEP 8 implied)
- 4-space indentation
- Maximum line length not enforced

**Linting:**
- Not configured (no pylint or ruff)

**Imports:**
- Standard library first, then third-party, then local
- Example:
```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Bot
```

**Docstrings:**
- Chinese comments used throughout
- Function docstrings in Chinese: `"""发送消息并获取回复"""`
- Class docstrings: `"""LLM 服务封装 - 使用 Anthropic SDK (MiniMax)"""`

### Frontend (TypeScript/React)

**Formatting:**
- ESLint with TypeScript support
- `eslint.config.js` uses:
  - `@eslint/js`
  - `typescript-eslint`
  - `eslint-plugin-react-hooks`
  - `eslint-plugin-react-refresh`

**Linting Rules:**
- React hooks rules enforced
- React refresh allowed for HMR-compatible updates

**Imports:**
- React hooks first: `import { useState, useEffect, useCallback } from 'react';`
- Type imports: `import type { Bot, Conversation } from './types';`
- Named imports: `import { Sidebar, ChatPanel } from './components';`
- Relative imports with `./` or `../`

**Path Aliases:**
- None configured (relative paths only)

## Error Handling

### Backend

**API Errors:**
- Uses FastAPI's `HTTPException`
- Example: `raise HTTPException(status_code=404, detail="机器人不存在")`

**Service Errors:**
- Try-catch blocks for external calls
- Generic error messages returned to client
- Detailed errors logged via print()

```python
try:
    response = await llm_service.chat(...)
except Exception as e:
    print(f"[ERROR] LLM 调用失败: {str(e)}")
    raise HTTPException(status_code=500, detail=f"AI 调用失败: {str(e)}")
```

### Frontend

**API Errors:**
- Error caught in try-catch
- Error displayed via `alert()` or `console.error()`
- Type assertion for error details: `error: any`

```typescript
try {
  const response = await chatApi.send({...});
} catch (error: any) {
  console.error('发送消息失败:', error);
  const errorMsg = error?.message || error?.detail || JSON.stringify(error);
  alert('发送消息失败: ' + errorMsg);
}
```

## Logging

### Backend

**Framework:** Python `print()` statements

**Patterns:**
- Debug prints with `[DEBUG]` prefix
- Error prints with `[ERROR]` prefix
- Step tracking: `[STEP 1]`, `[STEP 2]`, etc.

```python
print(f"[DEBUG] 收到聊天请求: bot_id={request.bot_id}")
print(f"[ERROR] LLM 调用失败: {str(e)}")
print(f"\n========== AI 原始输出 ==========\n{original_response}\n")
```

### Frontend

**Framework:** Browser `console`

**Patterns:**
- `console.error()` for errors
- `console.log()` for debug output

```typescript
console.error('加载机器人失败:', error);
console.log("[DEBUG] 发送消息, apiConfig:", apiConfig);
```

## Comments

### Backend

- Chinese comments throughout codebase
- Purpose comments above functions
- Inline comments for complex logic
- Example: `# 强力去重：去除文本中的重复内容（多轮迭代）`

### Frontend

- Chinese comments for complex logic
- Section comments: `// 状态管理`, `// 加载机器人列表`
- Helper function comments: `// 辅助函数：检查文本是否重复`

## Function Design

### Backend

**Size:** Functions can be long (100+ lines in some cases)

**Parameters:**
- Type-annotated
- Optional parameters with defaults
- Example: `async def chat(messages: List[Dict[str, str]], system_prompt: str = "", ...)`

**Return Values:**
- Type-annotated return types
- Early returns for error cases

### Frontend

**Size:** Moderate, with hooks for reusable logic

**Parameters:**
- TypeScript typed
- Event handlers use arrow functions

**Return Values:**
- `useState` returns tuple: `[state, setState]`
- `useCallback` for memoized functions

## Module Design

### Backend

**Exports:**
- Single instance pattern: `llm_service = LLMService()`
- Router pattern: `router = APIRouter(prefix="/chat", tags=["chat"])`

**Module Organization:**
- `app/routers/` - API endpoints
- `app/services/` - Business logic
- `app/models.py` - Database models
- `app/schemas.py` - Pydantic schemas

### Frontend

**Exports:**
- Named exports for components: `export const Sidebar`
- Default exports for pages: `export default App`

**Barrel Files:**
- `src/types/index.ts` - All type exports
- `src/api/index.ts` - All API exports

---

*Convention analysis: 2026-03-14*
