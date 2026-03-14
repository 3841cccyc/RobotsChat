# Testing Patterns

**Analysis Date:** 2026-03-14

## Test Framework

### Backend (Python)

**Status:** No test framework configured

**Not Found:**
- No `pytest`, `unittest`, or `nose` in requirements.txt
- No `tests/` directory
- No test configuration files

**Recommendation:** Add `pytest` and `pytest-asyncio` for async testing

### Frontend (TypeScript/React)

**Status:** No test framework configured

**Package.json shows:**
- No Jest, Vitest, or React Testing Library
- No test scripts in package.json

**Recommendation:** Add `vitest` with `@testing-library/react`

## Test File Organization

### Current State

**No test files found in codebase.**

All `*test*` files found are in `node_modules/` (library tests), not project tests.

### Recommended Structure (Not Yet Implemented)

```
backend/
├── tests/
│   ├── __init__.py
│   ├── routers/
│   │   ├── test_chat.py
│   │   └── test_bots.py
│   └── services/
│       └── test_llm_service.py

frontend/
├── src/
│   ├── __tests__/
│   │   ├── App.test.tsx
│   │   └── ChatPanel.test.tsx
│   └── components/
│       └── ChatPanel.test.tsx
```

## Test Patterns (Not Yet Established)

Since no tests exist, here are recommended patterns based on the codebase structure:

### Backend Recommended Patterns

```python
# tests/test_chat.py (recommended)
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_chat_endpoint(client):
    response = await client.post("/chat/", json={
        "bot_id": 1,
        "message": "Hello"
    })
    assert response.status_code == 200
```

### Frontend Recommended Patterns

```typescript
// src/__tests__/App.test.tsx (recommended)
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
  });

  it('handles message sending', async () => {
    render(<App />);
    // Test logic here
  });
});
```

## Mocking

### Current State

No mocking framework in use.

### Recommended Patterns

**Backend:**
- Use `pytest-mock` for mocking
- Mock external services (LLM API, database)

```python
@pytest.fixture
def mock_llm_service(mocker):
    return mocker.patch('app.services.llm_service.llm_service.chat', return_value="Mock response")
```

**Frontend:**
- Use Vitest's `vi.fn()` for mocking
- Mock fetch/API calls

```typescript
import { vi } from 'vitest';

global.fetch = vi.fn(() => Promise.resolve({
  json: () => Promise.resolve({ message: 'test' }),
  ok: true
}));
```

## Fixtures and Factories

### Current State

No test fixtures found.

### Recommended Patterns

**Backend:**
- Use `pytest.fixture` for database sessions
- Create test data factories

```python
@pytest.fixture
async def test_bot(db_session):
    bot = Bot(name="Test Bot", system_prompt="Test")
    db_session.add(bot)
    await db_session.commit()
    return bot
```

**Frontend:**
- Use testing-library's built-in fixtures
- Create test data helpers

```typescript
const mockBot = {
  id: 1,
  name: 'Test Bot',
  system_prompt: 'You are helpful.',
  // ... other fields
};
```

## Coverage

### Current State

- No coverage enforcement
- No coverage configuration
- No coverage reports generated

### Recommended Commands (Not Yet Configured)

```bash
# Backend
pytest --cov=app --cov-report=html

# Frontend
vitest --coverage
```

## Test Types

### Unit Tests

**Scope:** Not implemented
- Individual service functions (LLM service, RAG service)
- Utility functions
- Schema validation

### Integration Tests

**Scope:** Not implemented
- API endpoint testing
- Database operations
- Router behavior

### E2E Tests

**Status:** Not used
- No Cypress, Playwright, or Selenium configured

## Common Patterns to Establish

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

### Error Testing

```python
@pytest.mark.asyncio
async def test_handles_error():
    with pytest.raises(HTTPException) as exc_info:
        await failing_function()
    assert exc_info.value.status_code == 404
```

---

*Testing analysis: 2026-03-14*
