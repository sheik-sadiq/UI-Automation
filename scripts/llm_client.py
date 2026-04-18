"""
llm_client.py
=============
Wraps local Ollama API for self-healing.

The HEAL_SYSTEM_PROMPT encodes the locator-fix rules from
.github/skills/auto-heal.md so Gemma knows exactly what to produce:
a valid unified diff targeting only pages/, using Playwright's preferred
locator hierarchy.

Returns a unified diff string ready to pipe into `patch -p1`, or an empty
string if the model signals it cannot fix the failure.
"""
import requests

# ── System instruction (distilled from .github/skills/auto-heal.md) ──────────
HEAL_SYSTEM_PROMPT = """
You are an expert Playwright Python test maintenance engineer.
Your ONLY job is to fix broken page-object locators.

Rules:
- Only modify files inside pages/
- Only change locator definitions — NEVER alter test logic or imports
- Use Playwright locator strategies in this exact priority order:
    1. get_by_role(role, name=...)
    2. get_by_text(...)
    3. get_by_label(...)
    4. locator(css_selector)  — only as last resort
- Output ONLY a valid unified diff (diff -u format), nothing else —
  no explanation, no code fences, no markdown
- The diff header lines must follow the exact format:
    --- a/pages/filename.py
    +++ b/pages/filename.py
- Add a heal comment directly above the fixed locator line:
    # Healed YYYY-MM-DD: <one-line reason>
- If you are not confident in the fix, respond with exactly: CANNOT_FIX
""".strip()


def ask_llm(
    test_name: str,
    traceback: str,
    page_source: str,
    dom_snapshot: str,
) -> str:
    """
    Call local Ollama (gemma3:4b) with test context and live DOM snapshot.

    Parameters
    ----------
    test_name   : Name of the pytest function that failed.
    traceback   : Full error traceback from pytest-json-report.
    page_source : Current source of the responsible pages/*.py file.
    dom_snapshot: Extracted JSON of interactive elements from page.evaluate().

    Returns
    -------
    A unified diff string suitable for ``patch -p1``, or empty string
    on failure / low confidence.
    """
    user_message = f"""## Failing Test
`{test_name}`

## Error Traceback
```
{traceback}
```

## Current Page Object Source
```python
{page_source}
```

## Live Page Elements (interactive links, buttons, headings — JSON)
```json
{dom_snapshot}
```

Produce a unified diff that fixes the broken locator.
Remember: output ONLY the raw diff, no markdown fences, no explanation.
"""

    payload = {
        "model": "gemma3:4b",
        "system": HEAL_SYSTEM_PROMPT,
        "prompt": user_message,
        "stream": False,
        "options": {
            "temperature": 0.1,  # low temp -> deterministic
            "num_predict": 1000,
        }
    }

    try:
        print(f"[LLM] Dispatching request to local Ollama (gemma3:4b) for {test_name}...")
        resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        content = resp.json().get("response", "").strip()
    except Exception as exc:
        print(f"[LLM] Local Ollama API error for {test_name}: {exc}")
        return ""

    # Safety checks: reject if model signals uncertainty or output is malformed
    if "CANNOT_FIX" in content:
        print(f"[LLM] Model signalled CANNOT_FIX for {test_name}")
        return ""
    if not content.startswith("---"):
        # Sometimes small models still add markdown fences despite instructions.
        # Fallback strip if it wrapped in ```diff ... ```
        if content.startswith("```diff\n") and content.endswith("```"):
            print(f"[LLM] Stripping markdown fences from diff for {test_name}")
            content = content[8:-3].strip()
        else:
            print(f"[LLM] Unexpected response format for {test_name}:\n{content[:300]}")
            return ""

    return content
