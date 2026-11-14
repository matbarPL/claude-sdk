# Lab 06: Minimal MCP Server (Tools, Resources, Prompts & `stdio` Transport)

**Target Scripts:** `lab6_mcp_server.py` and `lab6_mcp_client.py`  
**Exam Domains:** Domain 8 (Tools & MCPs — 10.6%)  
**Model & Cost Guardrail:** Local `stdio` MCP test + optional single Haiku tool call (<$0.0005)

## 1. Learning Objectives
1. Explain the roles of MCP **Host** (e.g., Claude Code / IDE), **Client** (1:1 protocol session), and **Server** (capability provider).
2. Implement all three MCP server primitives using the official Python `mcp` SDK (`FastMCP`): **Tools** (model-controlled actions), **Resources** (application/user-controlled read-only data), and **Prompts** (user-invoked templates).
3. Enforce strict `stdio` transport hygiene: write JSON-RPC messages exclusively to `stdout` and send all diagnostic logs strictly to `stderr`.
4. Contrast local `stdio` transport with remote **Streamable HTTP** transport and configure MCP server registration across scopes (`local`, `project` `.mcp.json`, and `user`).

## 2. Implementation Requirements
1. **Create `lab6_mcp_server.py` using `mcp.server.fastmcp.FastMCP`**:
   - Configure Python's `logging` module to stream exclusively to `sys.stderr` (never `print()` to `stdout`).
   - **Tool (`@mcp.tool()`):** `lookup_exam_domain(domain_number: int) -> str` returning the domain title and exam weight for domains `1` through `8`.
   - **Resource (`@mcp.resource("config://sandbox-policy")`):** Read-only resource returning the project's cost and security guardrails (demonstrate path traversal validation if exposing `file://` URIs).
   - **Prompt (`@mcp.prompt()`):** `ccdvf_drill_prompt(topic: str) -> str` returning a structured exam-question generator template.
   - Run with `mcp.run(transport="stdio")`.
2. **Create `lab6_mcp_client.py` to Connect & Inspect Capabilities**:
   - Spawn `lab6_mcp_server.py` as a subprocess via `mcp.client.stdio.stdio_client` using `.\.venv\Scripts\python.exe`.
   - Initialize the `ClientSession`, call `session.list_tools()`, `session.list_resources()`, and `session.list_prompts()`, invoke `lookup_exam_domain(domain_number=2)`, and read `config://sandbox-policy`.

## 3. Verification & Expected Output
Run:
```powershell
.\.venv\Scripts\python.exe lab6_mcp_client.py
```
Confirm:
- Client handshake succeeds without JSON-RPC framing errors.
- `list_tools()`, `list_resources()`, and `list_prompts()` return the registered primitives, and `lookup_exam_domain(2)` returns Domain 2 details.

## 4. CCDV-F Exam Checkpoints & Traps
- **`stdout` Corruption Rule:** Over `stdio` transport, writing even a single `print("Server started")` line to `stdout` corrupts the JSON-RPC stream and crashes the MCP connection. Always log to `stderr`.
- **Three Primitives & Control Model:**
  - *Tools:* Model-controlled (Claude decides when to invoke via `tool_use`).
  - *Resources:* Application/client-controlled read-only context (must validate canonical paths against `../` traversal when serving `file://` resources).
  - *Prompts:* User-controlled reusable workflow templates (often surfaced as slash commands).
- **MCP Registration Scopes:** `project` scope stores server config in `.mcp.json` at the repo root (shared with teammates via git); `local` and `user` scopes are stored in `~/.claude.json`.
