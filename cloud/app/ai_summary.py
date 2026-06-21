"""Farmer-facing AI summary via the Claude API (PRD section 9.3).

Pass aggregated period JSON (zone counts, score + factors, treatments needed),
not raw rows. Falls back to a deterministic template if no API key is set, so
the demo never hard-fails on a missing key.
"""
from __future__ import annotations

import os

MODEL = os.environ.get("ACRE_CLAUDE_MODEL", "claude-sonnet-4-6")

PROMPT_TEMPLATE = """You are writing a short status update for a farmer who has
60 seconds to read it. Here is this period's data from their field scans:

{period_data}

Write a 3-4 sentence plain-language summary covering: what needs attention
first, which zones, and what to do about it. No jargon. End with one concrete
next action."""


def generate_summary(period_data: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_summary(period_data)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": PROMPT_TEMPLATE.format(period_data=period_data),
            }],
        )
        return resp.content[0].text
    except Exception as exc:
        return _fallback_summary(period_data, error=str(exc))


def _fallback_summary(period_data: dict, error: str | None = None) -> str:
    score = period_data.get("farm_score", "n/a")
    worst = period_data.get("worst_zones", [])
    treatments = period_data.get("treatments_needed", [])
    parts = [f"Farm health score is {score}/100."]
    if worst:
        parts.append("Zones needing attention: " + ", ".join(worst) + ".")
    else:
        parts.append("No zones are currently flagged for treatment.")
    if treatments:
        parts.append("Recommended treatments: " + ", ".join(treatments) + ".")
    parts.append("Next action: re-scan the flagged zones after treating.")
    prefix = "[offline summary] " if error or True else ""
    return prefix + " ".join(parts)
