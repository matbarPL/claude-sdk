"""
StrideCoach Stage 2 demo: cache threshold check, cached parsing (write, then read),
and conversation pruning.

Run: .\\.venv\\Scripts\\python.exe demo_stage2.py
"""

import sys

from stridecoach.cost import prune_conversation_history
from stridecoach.parser import MODEL, client, load_cached_handbook, parse_run_note_with_cache

# Windows consoles may default to a legacy code page that cannot print model output.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOTES = [
    "Tempo 10 km, 47:10, avg 4:43/km, HR 168, felt 7/10. Right Achilles tight after, walked it off.",
    "Intervals: 6x800m at 3:55/km with 2 min jog. HR peaked 181. Legs heavy, RPE 8. No pain.",
]


def main() -> None:
    print("[1. Cache threshold check]")
    handbook = load_cached_handbook()
    count = client.messages.count_tokens(
        model=MODEL,
        system=[{"type": "text", "text": handbook}],
        messages=[{"role": "user", "content": "ping"}],
    ).input_tokens
    verdict = "above" if count >= 4096 else "BELOW"
    print(f"  handbook ~ {count} tokens ({verdict} the 4,096-token minimum for Haiku 4.5)\n")

    print("[2. Cached parsing: write, then read]")
    for i, note in enumerate(NOTES, 1):
        workout, cost = parse_run_note_with_cache(note)
        print(f"  Call #{i}: {workout.workout_type}, {workout.distance_km} km, injury_flags={workout.injury_flags}")
        print(f"    cache_write={cost['cache_write_tokens']} cache_read={cost['cache_read_tokens']} "
              f"actual=${cost['actual_usd']} baseline=${cost['uncached_baseline_usd']} "
              f"savings={cost['cache_savings_pct']}%")
    print()

    print("[3. Conversation pruning]")
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Turn {i + 1}: " + "run detail " * 20}
        for i in range(8)
    ]
    pruned = prune_conversation_history(history, keep_last_n=4)
    print(f"  before: {len(history)} messages, after: {len(pruned)} messages")
    print(f"  roles after: {[m['role'] for m in pruned]}")


if __name__ == "__main__":
    main()
