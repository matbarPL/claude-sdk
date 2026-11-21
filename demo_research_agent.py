r"""
Demo: Claude Agent SDK sports-science research agent.

Run: .\.venv\Scripts\python.exe demo_research_agent.py
"""

import asyncio
import sys
from pathlib import Path

from stridecoach.research_agent import generate_runner_profile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUNNER_INTAKE = (
    "34-year-old runner targeting a 1:38 Half Marathon in 12 weeks, "
    "currently running 38 km/week, recent 10K PB 45:20, "
    "mild right Achilles tightness after tempo runs."
)


async def main() -> None:
    output_file = Path("athlete_profile.md")
    print("=== Running StrideCoach Research Agent ===")
    result = await generate_runner_profile(RUNNER_INTAKE, output_path=str(output_file))
    print("\n=== Summary ===")
    print(result)

    if output_file.exists():
        print(f"\n=== Generated {output_file} ===")
        print(output_file.read_text(encoding="utf-8"))
    else:
        print(f"\n[Warning] {output_file} was not created.")


if __name__ == "__main__":
    asyncio.run(main())
