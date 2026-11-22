"""StrideCoach Stage 2B/2C: call cost accounting and conversation pruning."""

from typing import Any

# USD per million tokens for claude-haiku-4-5-20251001 (5-minute cache write).
PRICE_INPUT = 1.00
PRICE_CACHE_WRITE = 1.25
PRICE_CACHE_READ = 0.10
PRICE_OUTPUT = 5.00
MTOK = 1_000_000


def calculate_call_cost(usage: Any) -> dict[str, Any]:
    """Cost of one call from its usage object, compared with the same call without caching."""
    uncached_in = usage.input_tokens or 0
    cache_write = usage.cache_creation_input_tokens or 0
    cache_read = usage.cache_read_input_tokens or 0
    output = usage.output_tokens or 0

    total_in = uncached_in + cache_write + cache_read
    actual = (
        uncached_in * PRICE_INPUT
        + cache_write * PRICE_CACHE_WRITE
        + cache_read * PRICE_CACHE_READ
        + output * PRICE_OUTPUT
    ) / MTOK
    baseline = (total_in * PRICE_INPUT + output * PRICE_OUTPUT) / MTOK
    savings_pct = (baseline - actual) / baseline * 100 if baseline else 0.0

    return {
        "total_input_tokens": total_in,
        "cache_write_tokens": cache_write,
        "cache_read_tokens": cache_read,
        "output_tokens": output,
        "actual_usd": round(actual, 6),
        "uncached_baseline_usd": round(baseline, 6),
        "cache_savings_pct": round(savings_pct, 1),
    }


def _text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    return " ".join(b.text for b in content if getattr(b, "type", None) == "text")


def _digest(old: list[dict[str, Any]], max_chars: int = 120) -> str:
    """Deterministic, no-API digest: first max_chars of each old turn."""
    lines = []
    for m in old:
        text = " ".join(_text_of(m["content"]).split())
        suffix = "..." if len(text) > max_chars else ""
        lines.append(f"{m['role']}: {text[:max_chars]}{suffix}")
    return "\n".join(lines)


def prune_conversation_history(messages: list[dict[str, Any]], keep_last_n: int = 4) -> list[dict[str, Any]]:
    """
    Keep the last keep_last_n messages untouched and compact older turns into a
    <history_summary> user message. An assistant acknowledgment is added only when
    needed, so roles keep alternating.
    """
    if keep_last_n < 1:
        raise ValueError("keep_last_n must be at least 1")
    if len(messages) <= keep_last_n:
        return list(messages)

    old, recent = messages[:-keep_last_n], messages[-keep_last_n:]
    summary = [{"role": "user", "content": f"<history_summary>\n{_digest(old)}\n</history_summary>"}]
    if recent[0]["role"] == "user":
        summary.append({"role": "assistant", "content": "Noted. Continuing from that summary."})
    return summary + list(recent)
