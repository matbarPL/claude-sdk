# Lab 04: Prompt Caching Breakpoints, TTLs & Message Batches API

**Target Script:** `lab4_caching_batches.py`  
**Exam Domains:** Domain 5 (Model Selection & Optimization) & Domain 2 (Applications & Integration)  
**Model & Cost Guardrail:** `claude-haiku-4-5-20251001` (`max_tokens <= 64`, 2 batch requests max)

## 1. Learning Objectives
1. Structure requests in the fixed `tools -> system -> messages` prefix hierarchy and place `cache_control: {"type": "ephemeral"}` breakpoints on static content above the minimum cacheable token threshold.
2. Measure cache writes (`cache_creation_input_tokens`) vs. cache hits (`cache_read_input_tokens`) in `response.usage` and demonstrate how modifying an earlier prefix invalidates downstream cache blocks.
3. Submit an asynchronous batch job via `client.messages.batches.create()` with `custom_id` keys, poll its status, and inspect batch result types.

## 2. Implementation Requirements
Create `lab4_caching_batches.py`:
1. **Prompt Caching Prefix & Breakpoint Test**:
   - Create a static `REFERENCE_MANUAL` string of ~2,200 tokens (above the minimum cacheable threshold for Haiku 4.5).
   - Attach `cache_control={"type": "ephemeral"}` to the system block containing `REFERENCE_MANUAL`.
   - **Call 1 (Cache Write):** Ask question 1 about the manual; print `usage.input_tokens`, `usage.cache_creation_input_tokens`, and `usage.cache_read_input_tokens`.
   - **Call 2 (Cache Hit):** Immediately ask question 2 with the exact same `tools` and `system` prefix; confirm `cache_read_input_tokens > 0` and `cache_creation_input_tokens == 0`.
   - **Call 3 (Cache Invalidation Trap):** Inject a dynamic timestamp at the *beginning* of the `system` block and ask question 3; observe `cache_read_input_tokens` drop back to `0` because prefix matching broke at the first changed byte.
2. **Message Batches API Workflow (`client.messages.batches`)**:
   - Create a batch of 2 lightweight requests (`custom_id="req-001"`, `custom_id="req-002"`) using `client.messages.batches.create(requests=[...])`.
   - Poll `client.messages.batches.retrieve(batch.id)` every 5 seconds (up to 60s timeout) until `processing_status == "ended"`, or cancel cleanly via `client.messages.batches.cancel(batch.id)` if testing lifecycle states without waiting.
   - When `ended`, iterate over `client.messages.batches.results(batch.id)` and print each entry's `custom_id` and `result.type` (`succeeded`, `errored`, `canceled`, or `expired`).

## 3. Verification & Expected Output
Run:
```powershell
.\.venv\Scripts\python.exe lab4_caching_batches.py
```
Confirm:
- Call 1 shows `cache_creation_input_tokens > 0`; Call 2 shows `cache_read_input_tokens > 0`; Call 3 shows `cache_read_input_tokens == 0`.
- Batch creation returns a `msgbatch_...` ID with `processing_status == "in_progress"` and transitions to `"ended"` (or `"canceling"` if canceled).

## 4. CCDV-F Exam Checkpoints & Traps
- **Fixed Evaluation Order & Breakpoint Cap:** Anthropic evaluates cache prefixes strictly in `tools -> system -> messages` order and allows **up to 4** `cache_control` breakpoints per request. Always place dynamic variables (timestamps, user IDs) at the **end** of the prompt, never at the top.
- **TTL Pricing Trade-off:** Default ephemeral cache TTL is **5 minutes** (write = `1.25x` base input price, read = `0.1x` base input price). An optional **1-hour** TTL costs `2.0x` on write (still `0.1x` on read) and is useful when a human-in-the-loop pauses >5 minutes between turns.
- **Cache Isolation Scope:** On the direct Claude API, prompt caches are isolated **per workspace**; on Google Cloud Vertex AI, caches are isolated **per organization**.
- **Message Batches vs. Realtime:** Batches offer a **50% discount** on input and output tokens with a **24-hour** processing expiry (results retained 29 days; NOT eligible for Zero Data Retention). Batches reject `stream: true`, `speed`, and `max_tokens: 0`, return results out of order (always match by `custom_id`), and only bill `succeeded` items (`errored`, `canceled`, and `expired` cost nothing).
