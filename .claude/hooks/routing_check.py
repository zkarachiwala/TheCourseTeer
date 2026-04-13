"""
Hook: UserPromptSubmit routing check.

Fires when the user submits a prompt. Injects an additionalContext
reminder when the prompt looks like a delegation-worthy task per
the agent routing rules in CLAUDE.md.
"""
import sys
import json

GEMINI_TASKS = [
    "component", "boilerplate", "template", "scaffold",
    "api route", "api endpoint", "page", "layout",
    "unit test", "write test", "generate test", "add test",
    "migration", "sql migration", "schema migration",
    "dockerfile", "docker compose", "docker-compose",
    "ci yaml", "github action", ".env", "env example",
    "pyproject", "requirements.txt", "package.json",
    "tailwind", "css class",
]

OPENCODE_TASKS = [
    "scraper", "extraction", "selector", "playwright",
    "html field", "re-mapping", "remap", "re-map",
    "robots.txt", "crawl", "parse html",
]

ROUTING_REMINDER = (
    "ROUTING CHECK (from CLAUDE.md): This prompt may be suitable for delegation.\n"
    "- Gemini CLI (boilerplate/tests/config/SQL): "
    "gemini -m gemini-2.0-flash -p \"<task>\"\n"
    "- OpenCode + Ollama (scraper/extraction/offline): "
    "opencode run \"<task>\"\n"
    "Apply the routing decision checklist in CLAUDE.md before proceeding."
)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    prompt = data.get("user_prompt", "").lower()

    matched_gemini = any(k in prompt for k in GEMINI_TASKS)
    matched_opencode = any(k in prompt for k in OPENCODE_TASKS)

    if matched_gemini or matched_opencode:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ROUTING_REMINDER,
            }
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
