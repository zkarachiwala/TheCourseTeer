# The Courseteer - A university course aggregator and search engine

All project documentation is in the `planning` directory.

The key document is PLAN.md included in full here:

@planning/PLAN.md

---

## Development Process

All feature work must follow the `/feature-dev:feature-dev` 7-phase workflow. Do not write implementation code before Phase 4 approval.

### GitHub Project Integration

When a feature-dev request references an issue number (e.g. "feature-dev #4" or "work on issue 4"):

**Project:** `5` | Owner: `zkarachiwala` | Project ID: `PVT_kwHOAedlmM4BUdpc`
**Status field ID:** `PVTSSF_lAHOAedlmM4BUdpczhBlk6g`
**Status options:** Backlog `f75ad846` | Ready `61e4505c` | In progress `47fc9ee4` | In review `df73e18b` | Done `98236657`

**Step 1 — Before starting, move to "In Progress":**
```bash
ITEM_ID=$(gh project item-list 5 --owner zkarachiwala --format json | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; print(next(i['id'] for i in items if i.get('content',{}).get('number')==N))")
gh project item-edit --project-id PVT_kwHOAedlmM4BUdpc --id $ITEM_ID --field-id PVTSSF_lAHOAedlmM4BUdpczhBlk6g --single-select-option-id 47fc9ee4
```
Replace `N` with the issue number (integer, no quotes).

**Step 2 — Fetch issue context for the feature-dev workflow:**
```bash
gh issue view N --repo zkarachiwala/TheCourseTeer
```
Use the issue title and body as the feature description when running the 7-phase workflow.

**Step 3 — Before closing Phase 3, post a Decisions comment on the issue:**

Summarise all clarifying questions raised and answers given during Phase 3 as a GitHub issue comment:
```bash
gh issue comment N --repo zkarachiwala/TheCourseTeer --body "## Feature-dev decisions

<list questions and answers here>"
```
If any answer changes the broader architecture, also update `planning/PLAN_REVIEW.md` and `planning/PLAN.md`.

**Step 4 — When creating the PR, link it to the issue and add it to the project:**
```bash
# Create PR linked to the issue (replace N with issue number)
gh pr create --title "..." --body "Closes #N" ...

# Add the PR to the project board
PR_ID=$(gh pr view --json id -q '.id')
gh project item-add 5 --owner zkarachiwala --url $(gh pr view --json url -q '.url')
```

**Step 5 — After creating the PR, move the issue to "In Review":**
```bash
gh project item-edit --project-id PVT_kwHOAedlmM4BUdpc --id $ITEM_ID --field-id PVTSSF_lAHOAedlmM4BUdpczhBlk6g --single-select-option-id df73e18b
```

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
gemini -m gemini-2.5-flash -p "<task prompt>"
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

### Delegate to Claude Haiku when:
The task is mechanical and needs Claude tooling (e.g. file access, subagent tool use), or Gemini is rate-limited. Invoke via Agent tool with `model: "haiku"`:

- Generating boilerplate when Gemini is unavailable
- Writing unit tests for a specified function or module
- Scraper AI re-mapping fallback if Ollama is insufficient
- Any mechanical task that requires Claude tool access but not Sonnet reasoning

Model ID: `claude-haiku-4-5-20251001`

### Routing decision checklist
Before starting any task, ask:
1. Does this require understanding how multiple files relate? → Claude Sonnet (main session)
2. Is the task well-specified and mechanical? → Gemini CLI (`gemini-2.5-flash`)
3. Is this scraper/extraction work that should stay local? → OpenCode + Ollama
4. Is Gemini rate-limited and Claude tooling needed? → Claude Haiku (subagent)
5. Is Gemini rate-limited and no Claude tooling needed? → OpenCode as fallback
