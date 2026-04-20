import asyncio
import sys
import json
import httpx
from anthropic import AsyncAnthropic

_OLLAMA_URL = "http://localhost:11434/api/generate"
_OLLAMA_MODEL = "llama3"
_CLAUDE_MODEL = "claude-3-5-haiku-20241022"

_PARSE_PROMPT = """\
You are a data extraction assistant. Convert the following extracted text \
from a university website into the clean format required for the field "{field_name}".

TEXT:
"{text}"

RULES:
- For "duration_years", return ONLY a number (e.g. 3 or 3.5).
- For "atar_guaranteed" or "atar_lowest_selection_rank", return ONLY a number (e.g. 85.5).
- For "price_annual_csp_aud" or "price_annual_dfee_aud", return ONLY a number representing the total cost.
- For "csp_available", return ONLY "Yes" or "No".
- For "degree_type", return ONLY "UG" or "PG".
- For "prerequisites", return a JSON array of subject names.
- For all other fields, clean the text and return it.

Return ONLY the cleaned value. No explanation.\
"""

async def _ask_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            _OLLAMA_URL,
            json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"].strip()

async def _ask_claude(prompt: str) -> str:
    client = AsyncAnthropic()
    message = await client.messages.create(
        model=_CLAUDE_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()

async def parse_text(field_name, text):
    prompt = _PARSE_PROMPT.format(field_name=field_name, text=text)
    try:
        # Try Ollama first
        result = await _ask_ollama(prompt)
        return result
    except Exception:
        # Fallback to Claude
        try:
            return await _ask_claude(prompt)
        except Exception as e:
            return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ai_parse.py <field_name> <text>")
        sys.exit(1)
    
    field_name = sys.argv[1]
    text = sys.argv[2]
    print(asyncio.run(parse_text(field_name, text)))
