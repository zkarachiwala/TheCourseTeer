import httpx
from anthropic import AsyncAnthropic

_OLLAMA_URL = "http://localhost:11434/api/generate"
_OLLAMA_MODEL = "llama3"
_CLAUDE_MODEL = "claude-haiku-4-5-20251001"

_PROMPT_TEMPLATE = """\
You are a web scraping assistant. The CSS selector "{selector}" for field \
"{field_name}" has stopped working on this HTML:

{html_snippet}

Return ONLY a new CSS selector that extracts the same field. No explanation.\
"""


async def remap_selector(
    field_name: str,
    failing_selector: str,
    html_snippet: str,
) -> str:
    """
    Ask an LLM for a replacement CSS selector.

    Tries Ollama first (local, free). Falls back to Claude Haiku if Ollama
    is unavailable or returns an error.

    Returns the replacement selector string.
    """
    prompt = _PROMPT_TEMPLATE.format(
        selector=failing_selector,
        field_name=field_name,
        html_snippet=html_snippet[:4000],
    )
    try:
        return await _ask_ollama(prompt)
    except Exception:
        return await _ask_claude(prompt)


async def _ask_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _OLLAMA_URL,
            json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        text = response.json()["response"]
    return text.strip().splitlines()[0]


async def _ask_claude(prompt: str) -> str:
    client = AsyncAnthropic()
    message = await client.messages.create(
        model=_CLAUDE_MODEL,
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip().splitlines()[0]
