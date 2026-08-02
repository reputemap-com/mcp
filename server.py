#!/usr/bin/env python3
"""ReputeMap MCP stdio bridge.

Speaks the Model Context Protocol over stdio to a local client (Claude Desktop,
or any stdio-only agent) and forwards every JSON-RPC message to the hosted
ReputeMap MCP server — Streamable HTTP with Bearer auth. Zero dependencies:
Python 3.9+ standard library only.

Usage:
    export REPUTEMAP_API_KEY="rmk_..."   # app.reputemap.com → Settings → API keys
    python3 server.py

Claude Desktop config (claude_desktop_config.json):
    {
      "mcpServers": {
        "reputemap": {
          "command": "python3",
          "args": ["/absolute/path/to/server.py"],
          "env": { "REPUTEMAP_API_KEY": "rmk_..." }
        }
      }
    }

The key never leaves this process except as an Authorization header on TLS
requests to ENDPOINT below.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("REPUTEMAP_MCP_URL", "https://api.reputemap.com/mcp")
API_KEY = os.environ.get("REPUTEMAP_API_KEY", "")

_session_id: str | None = None


def _post(message: dict) -> tuple[dict | None, int]:
    """Forward one JSON-RPC message; return (parsed response | None, HTTP status)."""
    global _session_id
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    if _session_id:
        headers["Mcp-Session-Id"] = _session_id

    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(message).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                _session_id = sid
            body = resp.read().decode()
            ctype = resp.headers.get("Content-Type", "")
            if "text/event-stream" in ctype:
                # Streamable HTTP may answer as SSE: take the first data: payload.
                for line in body.splitlines():
                    if line.startswith("data:"):
                        return json.loads(line[5:].strip()), resp.status
                return None, resp.status
            if not body:
                return None, resp.status
            return json.loads(body), resp.status
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        try:
            parsed = json.loads(detail)
            if isinstance(parsed, dict) and ("error" in parsed or "result" in parsed):
                return parsed, exc.code
        except ValueError:
            pass
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32000,
                "message": f"Upstream HTTP {exc.code}. "
                + (
                    "Missing or invalid API key — set REPUTEMAP_API_KEY "
                    "(create one at app.reputemap.com → Settings → API keys)."
                    if exc.code in (401, 403)
                    else detail
                ),
            },
        }, exc.code
    except (urllib.error.URLError, TimeoutError) as exc:
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {"code": -32001, "message": f"Cannot reach {ENDPOINT}: {exc}"},
        }, 0


def main() -> None:
    if not API_KEY:
        print(
            "reputemap-mcp: REPUTEMAP_API_KEY is not set — tool calls will fail "
            "with 401 until you export it.",
            file=sys.stderr,
        )
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            message = json.loads(raw)
        except ValueError:
            continue
        response, _status = _post(message)
        # Notifications (no id) expect no response line.
        if message.get("id") is None:
            continue
        if response is None:
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32002, "message": "Empty upstream response"},
            }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
