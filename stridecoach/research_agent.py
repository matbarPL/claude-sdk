"""
StrideCoach — Sports-Science Research Agent (Claude Agent SDK).

Demonstrates an autonomous agent loop (`query`) vs. a fixed API workflow:
the agent decides which files in `research_papers/` to discover (`Glob`),
read (`Read`), and synthesize (`Write`) within strict turn and USD guardrails.
"""

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultError,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

# Load ANTHROPIC_API_KEY from .env before launching the Agent SDK subprocess.
load_dotenv(".env", override=True)

MODEL = "claude-haiku-4-5-20251001"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


async def generate_runner_profile(
    runner_intake: str,
    output_path: str = "athlete_profile.md",
    max_budget_usd: float = 0.10,
    max_turns: int = 6,
) -> dict[str, Any]:
    """Traverse `research_papers/` and synthesize a personalized runner profile."""
    options = ClaudeAgentOptions(
        model=MODEL,
        cwd=str(PROJECT_ROOT),
        allowed_tools=["Glob", "Grep", "Read", "Write"],
        permission_mode="acceptEdits",
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        system_prompt=(
            "You are a sports-science research agent. Discover and read relevant files "
            "inside research_papers/ first. Cite the exact filenames you read, calculate "
            "appropriate VDOT training paces and Achilles/ACWR safety rules, and write a "
            f"concise, personalized runner profile and training zone card (under 80 lines) to {output_path}."
        ),
    )

    prompt = (
        f"Traverse research_papers/ and write a personalized runner profile to "
        f"{output_path} for this athlete intake:\n{runner_intake}"
    )

    summary: dict[str, Any] = {"subtype": "unknown", "total_cost_usd": 0.0, "num_turns": 0}

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                if message.error:
                    print(f"[Agent Error] {message.error}")
                if not message.content:
                    continue
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"[Agent Tool] -> {block.name} ({list(block.input.keys())})")
                    elif isinstance(block, TextBlock) and block.text.strip():
                        print(f"[Agent Note] {block.text.strip()}")
            elif isinstance(message, ResultMessage):
                summary = {
                    "subtype": message.subtype,
                    "is_error": message.is_error,
                    "total_cost_usd": message.total_cost_usd or 0.0,
                    "num_turns": message.num_turns,
                    "stop_reason": message.stop_reason,
                    "errors": message.errors,
                }
                print(
                    f"[Result] subtype={message.subtype} turns={message.num_turns} "
                    f"cost=${summary['total_cost_usd']:.4f}"
                )
    except ResultError as err:
        print(f"[Guardrail Triggered] {err}")

    return summary
