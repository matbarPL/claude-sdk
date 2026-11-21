"""
StrideCoach Stage 1 demo: pre-flight count, truncation + stateless continuation,
live SSE coaching feedback, and a 3-workout season backfill batch payload.

Run: .\\.venv\\Scripts\\python.exe demo_stage1.py
"""

import json
import sys

from stridecoach.coach_api import StrideCoachAPI

# Windows consoles may default to a legacy code page that cannot print model output.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUN_NOTE = (
    "Post-run note, Tue 2026-11-17. Tempo run, 12.0 km in 52:40 (avg 4:23/km). "
    "Splits: 4:31, 4:27, 4:22, 4:19, 4:20, 4:18, 4:21, 4:24, 4:26, 4:23, 4:25, 4:21. "
    "Avg HR 161 bpm, max 174 bpm. Warm-up 2 km easy. Felt strong until km 9, then left calf tight. "
    "Right Achilles had a sharp twinge at km 11 that eased after a walk break. "
    "Sleep 6 h, RPE 7/10. Week-to-date volume 38 km; planned 45 km."
)

COACH_QUESTION = (
    "Give me coaching feedback on this run in 3 short bullet points, "
    "and tell me what to do about the Achilles twinge before my next session."
)


def main() -> None:
    api = StrideCoachAPI()
    messages = [{"role": "user", "content": f"{RUN_NOTE}\n\n{COACH_QUESTION}"}]

    # 1. Pre-flight token count (free endpoint, no generation)
    print("[1. Pre-flight Token Check]")
    tokens = api.count_workout_tokens(messages)
    print(f"  input_tokens = {tokens}\n")

    # 2. Truncation on turn 1, then stateless continuation on turn 2
    print("[2. Truncation & Stateless Continuation]")
    raw_turn1, turn1 = api.ask_coach(messages, max_tokens=18)
    print(f"  Turn 1 stop_reason={turn1.stop_reason} truncated={turn1.is_truncated} request_id={turn1.request_id}")
    print(f"  Turn 1 text: {turn1.text!r}")

    if turn1.is_truncated:
        # The API is stateless: resend the full history, including the assistant turn.
        messages.append({"role": "assistant", "content": raw_turn1.content})
        messages.append({"role": "user", "content": "Finish that thought concisely."})
        _, turn2 = api.ask_coach(messages, max_tokens=120)
        print(f"  Turn 2 stop_reason={turn2.stop_reason} truncated={turn2.is_truncated} request_id={turn2.request_id}")
        print(f"  Turn 2 text: {turn2.text!r}")
    else:
        print("  Turn 1 was not truncated; continuation skipped.")
    print()

    # 3. Live SSE streaming feedback on the run
    print("[3. Live SSE Coaching Feedback]")
    stream_messages = [{"role": "user", "content": f"{RUN_NOTE}\n\n{COACH_QUESTION}"}]
    print("  Stream: ", end="")
    streamed = api.stream_coach_feedback(stream_messages, max_tokens=200)
    print(f"  Final stop_reason={streamed.stop_reason} request_id={streamed.request_id} "
          f"usage={streamed.input_tokens} in / {streamed.output_tokens} out")
    print()

    # 4. Season backfill batch payload (built only, not submitted)
    print("[4. Season Backfill Batch Payload]")
    workouts = [
        {"workout_id": "run-2026-11-01", "note": "Easy 8 km, HR 138, legs fresh. Smooth pace throughout."},
        {"workout_id": "run-2026-11-08", "note": "Long run 18 km, last 4 km at marathon pace. Gel at 10 km."},
        {"workout_id": "run-2026-11-17", "note": RUN_NOTE},
    ]
    batch = api.build_season_backfill_batch(workouts, max_tokens=150)
    print(f"  {len(batch)} items, custom_ids = {[item['custom_id'] for item in batch]}")
    print("  First item:")
    print("  " + json.dumps(batch[0], indent=2).replace("\n", "\n  "))


if __name__ == "__main__":
    main()
