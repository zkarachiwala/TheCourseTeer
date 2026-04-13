# The Courseteer - A university course aggregator and search engine

All project documentation is in the `planning` directory.

The key document is PLAN.md included in full here:

@planning/PLAN.md

---

## Development Process

All feature work must follow the `/feature-dev:feature-dev` 7-phase workflow. Do not write implementation code before Phase 4 approval.

---

## Agent Routing

Tasks must be routed to the appropriate AI tool based on the strategy in `planning/BUILD_PLAN.md`. Apply this routing for every task:

### Use Claude Code (handle directly) when:
- Making architecture or design decisions
- Debugging across multiple files where full repo context is needed
- Reviewing critical code paths: schema migrations, data integrity, security
- Any task that requires reasoning about how parts of the codebase fit together

### Delegate to Gemini CLI when:
The task is well-specified and mechanical — it does not require understanding the broader codebase. Invoke via Bash:

```bash
gemini -m gemini-2.0-flash -p "<task prompt>"
```

Delegate to Gemini for:
- Generating boilerplate: Next.js pages, API routes, Tailwind components
- Writing scraper extraction logic for a single university (given the HTML structure)
- Writing unit tests for a specified function or module
- Generating SQL migration files from a schema description
- Drafting config files: `.env.example`, `docker-compose.yml`, CI yaml, `pyproject.toml`

If the output needs review or integration into the codebase, do that in Claude after Gemini returns.

### Delegate to OpenCode + Ollama when:
The task relates to local scraper development, HTML field extraction, or offline work where API quota should be preserved. Invoke via Bash:

```bash
opencode run "<task prompt>"
```

Delegate to OpenCode for:
- Prompt engineering for scraper HTML extraction patterns
- Iterating on AI re-mapping logic for the scraper
- Any task where Gemini is rate-limited and Claude context should be preserved

### Routing decision checklist
Before starting any task, ask:
1. Does this require understanding how multiple files relate? → Claude
2. Is the task fully specified with clear inputs and outputs? → Gemini CLI
3. Is this scraper/extraction work that should stay local? → OpenCode
4. Is Gemini rate-limited today? → OpenCode as fallback
