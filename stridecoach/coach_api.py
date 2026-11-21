"""
StrideCoach — Stage 1: Core Messages API & Streaming.

Wraps the Anthropic Messages API for post-run coaching feedback. Every response
is validated (stop_reason, empty content, block type) before any text is read.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import Message

# Load .env explicitly; the SDK does not read it on its own.
load_dotenv(".env", override=True)

logger = logging.getLogger(__name__)

# Pinned snapshot only. Never use floating -latest aliases.
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS_CAP = 300
DEFAULT_MAX_TOKENS = 150

# Message Batches API custom_id: 1-64 chars from [a-zA-Z0-9_-].
_CUSTOM_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

COACH_SYSTEM = (
    "You are StrideCoach, a concise running coach. Give practical, specific feedback "
    "on the workout described. Keep replies under 80 words in plain text with no markdown headings. "
    "Never invent splits, heart-rate values, or injury details that the athlete did not report. "
    "Flag pain or injury notes for professional review."
)


@dataclass
class CoachResponse:
    """Validated view of one Messages API response."""
    text: str
    stop_reason: str | None
    request_id: str | None
    input_tokens: int
    output_tokens: int
    is_truncated: bool
    is_refusal: bool


def _check_max_tokens(max_tokens: int) -> None:
    if not 1 <= max_tokens <= MAX_TOKENS_CAP:
        raise ValueError(f"max_tokens must be between 1 and {MAX_TOKENS_CAP}, got {max_tokens}")


class StrideCoachAPI:
    def __init__(self, client: Anthropic | None = None, model: str = MODEL, system_prompt: str = COACH_SYSTEM) -> None:
        self.client = client or Anthropic()
        self.model = model
        self.system_prompt = system_prompt

    # ------------------------------------------------------------------ validation
    @staticmethod
    def validate_response(response: Message) -> CoachResponse:
        """
        Inspect stop_reason and content before extracting any text.
        Order: refusal -> empty content -> text blocks (by type) -> max_tokens flag.
        """
        request_id = getattr(response, "_request_id", None)
        logger.info("stop_reason=%s request_id=%s", response.stop_reason, request_id)

        usage = response.usage
        input_tokens = usage.input_tokens if usage else 0
        output_tokens = usage.output_tokens if usage else 0

        def make(text: str, is_truncated: bool = False, is_refusal: bool = False) -> CoachResponse:
            return CoachResponse(
                text=text,
                stop_reason=response.stop_reason,
                request_id=request_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                is_truncated=is_truncated,
                is_refusal=is_refusal,
            )

        if response.stop_reason == "refusal":
            return make("[REFUSAL] Request declined by safety policy.", is_refusal=True)

        if not response.content:
            return make("[EMPTY] Response contained zero content blocks.")

        # Scan by type: thinking or tool_use blocks may precede the text.
        text_parts = [b.text for b in response.content if b.type == "text"]
        if not text_parts:
            block_types = [b.type for b in response.content]
            return make(f"[NO TEXT BLOCKS: {block_types}]")

        text = "\n".join(text_parts)
        return make(text, is_truncated=(response.stop_reason == "max_tokens"))

    # ------------------------------------------------------------------ pre-flight
    def count_workout_tokens(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> int:
        """Exact input-token count via the free count_tokens endpoint (no max_tokens parameter)."""
        kwargs: dict[str, Any] = {"model": self.model, "system": self.system_prompt, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        return self.client.messages.count_tokens(**kwargs).input_tokens

    # ------------------------------------------------------------------ realtime
    def ask_coach(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> tuple[Message, CoachResponse]:
        """
        Non-streaming call. Returns the raw Message (needed to continue a conversation)
        alongside the validated view.
        """
        _check_max_tokens(max_tokens)
        raw = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            max_tokens=max_tokens,
            messages=messages,
        )
        return raw, self.validate_response(raw)

    def stream_coach_feedback(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> CoachResponse:
        """SSE streaming: print text deltas live, then validate the assembled final Message."""
        _check_max_tokens(max_tokens)
        with self.client.messages.stream(
            model=self.model,
            system=self.system_prompt,
            max_tokens=max_tokens,
            messages=messages,
        ) as stream:
            for chunk in stream.text_stream:
                print(chunk, end="", flush=True)
            print()
            final = stream.get_final_message()
        return self.validate_response(final)

    # ------------------------------------------------------------------ batch
    def build_season_backfill_batch(
        self,
        workouts: list[dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> list[dict[str, Any]]:
        """
        Build Message Batches API request items (POST /v1/messages/batches).
        Each workout dict needs 'workout_id' (used as custom_id) and 'note'.
        Batches are for non-blocking backfills only, never for live coaching.
        """
        _check_max_tokens(max_tokens)
        seen: set[str] = set()
        requests: list[dict[str, Any]] = []
        for workout in workouts:
            custom_id = workout["workout_id"]
            if not _CUSTOM_ID_RE.match(custom_id):
                raise ValueError(f"Invalid custom_id {custom_id!r}: use 1-64 chars [a-zA-Z0-9_-]")
            if custom_id in seen:
                raise ValueError(f"Duplicate custom_id {custom_id!r} in batch")
            seen.add(custom_id)
            requests.append(
                {
                    "custom_id": custom_id,
                    "params": {
                        "model": self.model,
                        "system": self.system_prompt,
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": workout["note"]}],
                    },
                }
            )
        return requests
