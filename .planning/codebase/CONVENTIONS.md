# Coding Conventions

**Analysis Date:** 2026-05-04

## Naming Patterns

**Files:**
- **Python:** `snake_case.py` (e.g., `scraper/universal_engine.py`)
- **TypeScript/React:** `kebab-case.ts` or `kebab-case.tsx` (e.g., `web/src/components/course-card.tsx`)
- **Tests:** `test_*.py` for Python, `*.test.ts` or `*.test.tsx` for TypeScript.

**Functions:**
- **Python:** `snake_case()` (e.g., `def extract_data()`)
- **TypeScript:** `lowerCamelCase()` (e.g., `function getArea()`)

**Variables:**
- **Python:** `snake_case`
- **TypeScript:** `lowerCamelCase`

**Types:**
- **TypeScript:** `UpperCamelCase` for interfaces and types (e.g., `interface CourseCardProps`).

## Code Style

**Formatting:**
- **Python:** Follows Google Python Style Guide. Indentation: 4 spaces. Line length: 80 characters.
- **TypeScript:** Follows Google TypeScript Style Guide. Indentation: 2 spaces. Single quotes for strings. Explicit semicolons.

**Linting:**
- **Python:** `pylint` is recommended in the style guide.
- **TypeScript:** Google TypeScript Style Guide (enforced by `gts` conceptually, though config files were not found, the code adheres to it).

## Import Organization

**Order:**
1. Standard Library
2. Third-party packages
3. Local application imports

**Path Aliases:**
- **TypeScript:** `@/` points to `web/src/` (configured in `web/tsconfig.json`).

## Error Handling

**Patterns:**
- **Python:** Use built-in exception classes. Avoid bare `except:` clauses.
- **TypeScript:** Prefer explicit error checking. Use `zod` for schema validation and parsing (e.g., `web/package.json`).

## Logging

**Framework:** `print` or `logging` in Python; `console` in TypeScript.

**Patterns:**
- Log significant events in scrapers (e.g., `scraper/run.py`).

## Comments

**When to Comment:**
- Use JSDoc for TypeScript public APIs.
- Use triple double quotes `"""Docstrings"""` for all Python modules, classes, and functions.

**JSDoc/TSDoc:**
- Used for documentation in TypeScript files.

## Function Design

**Size:** Keep functions small and focused on a single responsibility.

**Parameters:** Prefer descriptive parameter names. Python uses type annotations for public APIs.

**Return Values:** Explicit return types are encouraged.

## Module Design

**Exports:**
- **TypeScript:** Use **named exports**. **Do not use default exports** (Google TS Style Guide rule).

**Barrel Files:**
- Limited usage observed; components are usually imported directly from their files.

---

*Convention analysis: 2026-05-04*
