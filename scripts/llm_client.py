"""
llm_client.py
=============
Wraps the Google Gemini API (google-generativeai SDK).

The HEAL_SYSTEM_PROMPT encodes the locator-fix rules from
.github/skills/auto-heal.md so Gemini understands exactly what to produce:
a valid unified diff targeting only pages/, using Playwright's preferred
locator hierarchy.

Returns a unified diff string ready to pipe into `patch -p1`, or an empty
string if Gemini signals it cannot fix the failure.
"""
import json
import os

import google.generativeai as genai

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
- Add a heal comment directly above the fixed locator line:
    # Healed YYYY-MM-DD: <one-line reason>
- If you are not confident in the fix, respond with exactly: CANNOT_FIX
""".strip()


def ask_llm(
    test_name: str,
    traceback: str,
    page_source: str,
    dom_snapshot: dict,
) -> str:
    """
    Call Gemini with the test failure context and a live DOM snapshot.

    Parameters
    ----------
    test_name   : Name of the pytest function that failed.
    traceback   : Full error traceback from pytest-json-report.
    page_source : Current source of the responsible pages/*.py file.
    dom_snapshot: ARIA accessibility tree captured from the live page.

    Returns
    -------
    A unified diff string suitable for ``patch -p1``, or empty string
    on failure / low confidence.
    """
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=HEAL_SYSTEM_PROMPT,
    )

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

## Live DOM Snapshot (ARIA accessibility tree)
```json
{json.dumps(dom_snapshot, indent=2)}
```

Produce a unified diff that fixes the broken locator.
Remember: output ONLY the diff, no markdown fences, no explanation.
"""

    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0.1,        # low temp → deterministic output
            max_output_tokens=1000,
        ),
    )

    content = response.text.strip()

    # Safety checks: reject if model signals uncertainty or output is malformed
    if "CANNOT_FIX" in content:
        print(f"[LLM] Gemini signalled CANNOT_FIX for {test_name}")
        return ""
    if not content.startswith("---"):
        print(f"[LLM] Unexpected response format for {test_name}:\n{content[:200]}")
        return ""

    return content
