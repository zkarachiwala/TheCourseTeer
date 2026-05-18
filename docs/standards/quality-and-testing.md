# Quality & Testing Standards

## TDD Workflow

All implementation follows Red → Green → Refactor:

1. **Red** — Write failing tests that define the expected behaviour. Run them and confirm they fail before writing any implementation code.
2. **Green** — Write the minimum code to make the tests pass.
3. **Refactor** — Improve clarity and remove duplication with the safety of passing tests.

Target: **>80% code coverage** for all new code.

---

## Quality Gates

Before marking any task complete:

- [ ] All tests pass
- [ ] Code coverage ≥ 80%
- [ ] Code follows [`docs/standards/code-style.md`](code-style.md)
- [ ] All public functions/methods have docstrings or JSDoc
- [ ] Type safety enforced (type hints in Python, TypeScript types in web)
- [ ] No linting or static analysis errors
- [ ] No hardcoded secrets or credentials
- [ ] Input validation present at system boundaries
- [ ] Mobile layout verified (if UI change)
- [ ] Documentation updated if behaviour changed

---

## Testing by Layer

### Scraper (Python / pytest)
```bash
cd scraper
uv run pytest tests/ -v
```
- Unit tests mock HTTP — do not make live requests
- Gold-standard fixture tests use saved HTML snapshots from `tests/gold_standards/fixtures/`
- DB integration tests require `DATABASE_URL` and are excluded in CI on forks

### Web (TypeScript / Vitest)
```bash
cd web
npm run test
```
- Server Components tested via Vitest
- Mock Drizzle responses for unit tests; use a real DB for integration tests

---

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Types:**
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, whitespace
- `refactor` — no behaviour change
- `test` — adding or fixing tests
- `chore` — maintenance, dependencies, config

**Examples:**
```
feat(scraper): add Federation University extraction config
fix(web): correct ATAR display for multi-campus courses
test(scraper): add gold-standard fixture for La Trobe accounting
chore: update gitignore to exclude conductor/ directory
```
