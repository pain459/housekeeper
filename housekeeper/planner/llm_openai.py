from __future__ import annotations

import os
from typing import Any, Dict, List

from openai import OpenAI

from ..models import HousekeeperPlan


def _system_prompt() -> str:
    # Keep it short; schema enforcement does the heavy lifting.
    return (
        "You are a conservative Linux housekeeping planner for Pop!_OS.\n"
        "You will be given a JSON audit snapshot from the machine.\n"
        "Your job:\n"
        "1) Identify high-signal findings (updates, disk/log growth, failed services, security posture).\n"
        "2) Propose a minimal, safe-by-default plan.\n"
        "Rules:\n"
        "- Do NOT propose commands that delete user files.\n"
        "- Prefer simulation/dry-run before any disruptive step.\n"
        "- Never use shell pipelines; commands must be argv arrays.\n"
        "- Keep actions few and high value.\n"
        "- Commands may include sudo, but treat them as disruptive.\n"
    )


def build_messages(audit: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": (
                "Here is the audit JSON. Generate a HousekeeperPlan.\n\n"
                f"{audit}"
            ),
        },
    ]


def generate_plan_from_audit(audit: Dict[str, Any]) -> HousekeeperPlan:
    """
    Returns a Pydantic-validated HousekeeperPlan using OpenAI Structured Outputs.
    """
    client = OpenAI()

    model = os.getenv("HK_OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("HK_OPENAI_TEMPERATURE", "0"))

    # Structured Outputs via Responses API + Pydantic parsing
    # See: Structured Outputs guide. :contentReference[oaicite:2]{index=2}
    resp = client.responses.parse(
        model=model,
        input=build_messages(audit),
        text_format=HousekeeperPlan,
        temperature=temperature,
    )

    plan = resp.output_parsed
    if plan is None:
        raise RuntimeError("Model did not return a parsed plan (output_parsed is None).")

    return plan
