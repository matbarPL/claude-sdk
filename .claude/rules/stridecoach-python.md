---
paths: ["stridecoach/**/*.py"]
---

# StrideCoach Python Rules

These rules apply to every Python file in the `stridecoach/` package. They are CCDV-F exam patterns, so keep them even when a shortcut looks harmless.

## Stop reason and empty content
- Always inspect `response.stop_reason` before reading any content. Handle each value explicitly:
  - `end_turn`: normal completion.
  - `max_tokens`: output was truncated. Flag it to the caller.
  - `refusal`: the request was declined. Return a refusal result, not text.
  - `tool_use`: the response contains tool calls. Run them and continue the loop.
  - `pause_turn`: a server-side tool loop paused. Resend the conversation to resume.
- Guard against an empty `response.content` before extracting text. HTTP 200 does not mean usable output.

## Block scanning
- Find text with `[b.text for b in response.content if b.type == "text"]`.
- Never use `response.content[0].text`. Thinking, tool-use, and other blocks can come first.

## Observability
- Log the request ID with `getattr(response, "_request_id", None)`. Streamed final messages may not carry the attribute, so the `getattr` form is required.

## Limits
- `max_tokens` must be `<= 300`.
- Model must be `claude-haiku-4-5-20251001`. Never use a floating `-latest` alias.
- Do not pass `temperature` to `messages.create()` or `messages.stream()`. The installed SDK rejects it.
