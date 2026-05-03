# Testing Patterns

**Analysis Date:** 2026-05-04

## Test Framework

**Runner:**
- **Python:** `pytest` (version not specified in manifests, but used in `scraper/tests/`)
- **TypeScript:** `vitest` ^4.1.4 (configured in `web/vitest.config.ts`)

**Assertion Library:**
- **Python:** Built-in `assert` statement (standard for pytest)
- **TypeScript:** `expect` from `vitest`

**Run Commands:**
```bash
# Python
cd scraper && pytest

# TypeScript/React
cd web && npm test
```

## Test File Organization

**Location:**
- **Python:** Separate directory at `scraper/tests/`.
- **TypeScript:** Mixed approach. Separate directory at `web/src/__tests__/` and co-located files like `web/src/app/admin/scraper-builder/page.test.tsx`.

**Naming:**
- **Python:** `test_*.py`
- **TypeScript:** `*.test.ts` or `*.test.tsx`

**Structure:**
```
scraper/tests/
├── conftest.py
└── test_*.py

web/src/
├── __tests__/
│   └── lib/
│       └── *.test.ts
└── app/
    └── [feature]/
        └── *.test.tsx
```

## Test Structure

**Suite Organization:**
```typescript
// TypeScript (Vitest)
import { describe, it, expect } from 'vitest'

describe('Component Name', () => {
  it('does something expected', () => {
    // ...
    expect(result).toBe(expected)
  })
})
```

```python
# Python (Pytest)
import pytest

@pytest.mark.asyncio
async def test_feature_name(fixture):
    # ...
    assert result == expected
```

**Patterns:**
- **Setup pattern:** Python uses `conftest.py` with `@pytest_asyncio.fixture` for database pools and clean-up.
- **Teardown pattern:** `yield` in Python fixtures handles teardown (e.g., `clean_queue` in `scraper/tests/conftest.py`).
- **Assertion pattern:** Use `expect(...).toBe(...)` for TS and `assert ... == ...` for Python.

## Mocking

**Framework:**
- **Python:** `unittest.mock` and `pytest-mock` (implied).
- **TypeScript:** `vitest` built-in mocking capabilities.

**Patterns:**
```typescript
// Vitest mocking example (typical pattern)
import { vi } from 'vitest'
vi.mock('@/lib/api')
```

**What to Mock:**
- External API calls (e.g., Supabase, university websites).
- Complex browser interactions (in `scraper/browser.py`).

**What NOT to Mock:**
- Pure utility functions (e.g., `web/src/lib/area-map.ts`).
- Database schema logic (integration tests use a real Supabase instance).

## Fixtures and Factories

**Test Data:**
```python
# scraper/tests/conftest.py
@pytest_asyncio.fixture(scope="session")
async def university_id(pool):
    # Fetches actual seeded ID from database
    ...
```

**Location:**
- Python fixtures in `scraper/tests/conftest.py`.
- TypeScript setup in `web/src/test/setup.ts`.

## Coverage

**Requirements:** Not explicitly enforced in manifests.

**View Coverage:**
```bash
# TypeScript
cd web && npm test -- --coverage
```

## Test Types

**Unit Tests:**
- Logic testing in `web/src/lib/` and `scraper/universal_engine.py`.

**Integration Tests:**
- Scraper tests in `scraper/tests/` interact with the Supabase database.
- Component tests in `web/src/` use `@testing-library/react` to test UI behavior.

**E2E Tests:**
- Not explicitly detected, though some scraper tests simulate full extraction flows.

## Common Patterns

**Async Testing:**
- Python: `@pytest.mark.asyncio`.
- TypeScript: `async/await` within `it()` or `test()` blocks.

**Error Testing:**
```python
with pytest.raises(ValueError, match="..."):
    await function_that_raises()
```

---

*Testing analysis: 2026-05-04*
