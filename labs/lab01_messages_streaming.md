# Lab 01: Messages API, Token Counting, Stop Reasons & SSE Streaming

**Target Script:** `lab1_messages.py`  
**Exam Domains:** Domain 2 (Applications & Integration) & Domain 5 (Model Selection & Optimization)  
**Model & Cost Guardrail:** `claude-haiku-4-5-20251001` (`max_tokens <= 120`, <$0.001 per run)

## 1. Learning Objectives
1. Count exact input tokens pre-flight using `client.messages.count_tokens()` and explain why counts are tied to the target model's tokenizer.
2. Manage stateless multi-turn conversation history in application state by appending both assistant responses and user follow-ups.
3. Inspect `stop_reason` (`end_turn`, `max_tokens`, `tool_use`, `pause_turn`, `refusal`) and `_request_id` on every response, including empty-content guards.
4. Stream responses over Server-Sent Events (SSE) using `client.messages.stream()` and extract the assembled `Message` via `stream.get_final_message()`.

## 2. Implementation Requirements
Build or extend `lab1_messages.py` with the following functions:
1. **`preflight_token_check(client, model, system, messages)`**:
   - Call `client.messages.count_tokens(model=model, system=system, messages=messages)`.
   - Print `input_tokens` before making a billable generation call.
2. **`test_truncation_and_continuation(client, model, system)`**:
   - Send a prompt with `max_tokens=12` so Claude truncates mid-sentence (`stop_reason == "max_tokens"`).
   - Log `response._request_id` (maps to the `request-id` HTTP response header).
   - Append `{"role": "assistant", "content": response.content}` and a new `{"role": "user", "content": "Finish that sentence concisely."}` message, then re-send the full array to verify `stop_reason == "end_turn"`.
3. **`stream_with_validation(client, model, system, messages)`**:
   - Use `with client.messages.stream(...) as stream:` to print `stream.text_stream` chunks in real time.
   - Call `final_msg = stream.get_final_message()`.
   - Implement a response validator helper `validate_message(msg)` that checks `msg.stop_reason` first (handling `refusal`, `max_tokens`, and `end_turn`) and guards against empty `msg.content` blocks before reading `.text`.
4. **`compare_sampling_determinism(client, model)`**:
   - Run the same short prompt twice at `temperature=0.0` vs. `temperature=1.0` (`max_tokens=24`) to observe sampling variance.

## 3. Verification & Expected Output
Run:
```powershell
.\.venv\Scripts\python.exe lab1_messages.py
```
Confirm:
- Pre-flight token count prints an integer > 0.
- Truncated call outputs `stop_reason: max_tokens` and a `req_...` request ID.
- Continuation call outputs `stop_reason: end_turn` without losing context from turn 1.
- Streamed text prints incrementally, followed by final `usage` token counts.

## 4. CCDV-F Exam Checkpoints & Traps
- **Stateless API:** `POST /v1/messages` never stores conversation history server-side; omitting earlier turns drops all prior context.
- **Transport of Streaming:** SSE streaming runs over the single HTTP response connection—not a separate WebSocket or bidirectional socket. Event sequence: `message_start` -> (`content_block_start` -> `content_block_delta`+ -> `content_block_stop`)+ -> `message_delta` -> `message_stop` (with optional `ping` events anywhere).
- **Silent HTTP 200 Failures:** An HTTP `200 OK` response can still represent a truncated (`max_tokens`), refused (`refusal`), or empty `end_turn` output, and mid-stream `overloaded_error` events can arrive after an initial `200 OK`. Always inspect `stop_reason` and `content` before downstream parsing.
- **Cloud Provider Differences:** On direct API (`Anthropic()`), `model` is in the JSON body and `anthropic-version` is an HTTP header. On Google Cloud Vertex AI (`AnthropicVertex`), `model` is in the endpoint URL and `anthropic_version: "vertex-2023-10-16"` moves into the JSON body.
