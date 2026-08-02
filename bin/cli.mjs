#!/usr/bin/env node
/**
 * ReputeMap MCP stdio bridge (Node 18+, zero dependencies).
 *
 * Speaks the Model Context Protocol over stdio to a local client and forwards
 * every JSON-RPC message to the hosted ReputeMap server — Streamable HTTP
 * with Bearer auth. The API key never leaves this process except as an
 * Authorization header on TLS requests to the endpoint below.
 *
 * Usage:
 *   REPUTEMAP_API_KEY="rmk_..." npx -y @reputemap/mcp
 *
 * Claude Desktop (claude_desktop_config.json):
 *   { "mcpServers": { "reputemap": {
 *       "command": "npx", "args": ["-y", "@reputemap/mcp"],
 *       "env": { "REPUTEMAP_API_KEY": "rmk_..." } } } }
 */

import { createInterface } from "node:readline";

const ENDPOINT =
  process.env.REPUTEMAP_MCP_URL ?? "https://api.reputemap.com/mcp";
const API_KEY = process.env.REPUTEMAP_API_KEY ?? "";

let sessionId = null;

if (!API_KEY) {
  console.error(
    "reputemap-mcp: REPUTEMAP_API_KEY is not set — tool calls will fail " +
      "with 401 until you export it (create a key at app.reputemap.com → " +
      "Settings → API keys).",
  );
}

function rpcError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

async function forward(message) {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
  };
  if (API_KEY) headers.Authorization = `Bearer ${API_KEY}`;
  if (sessionId) headers["Mcp-Session-Id"] = sessionId;

  let resp;
  try {
    resp = await fetch(ENDPOINT, {
      method: "POST",
      headers,
      body: JSON.stringify(message),
      signal: AbortSignal.timeout(60_000),
    });
  } catch (err) {
    return rpcError(message.id ?? null, -32001, `Cannot reach ${ENDPOINT}: ${err}`);
  }

  const sid = resp.headers.get("mcp-session-id");
  if (sid) sessionId = sid;

  const body = await resp.text();
  const ctype = resp.headers.get("content-type") ?? "";

  const parse = (text) => {
    try {
      return JSON.parse(text);
    } catch {
      return null;
    }
  };

  let parsed = null;
  if (ctype.includes("text/event-stream")) {
    for (const line of body.split("\n")) {
      if (line.startsWith("data:")) {
        parsed = parse(line.slice(5).trim());
        if (parsed) break;
      }
    }
  } else if (body) {
    parsed = parse(body);
  }

  if (parsed && (parsed.error || parsed.result || parsed.jsonrpc)) return parsed;

  if (!resp.ok) {
    const hint =
      resp.status === 401 || resp.status === 403
        ? "Missing or invalid API key — set REPUTEMAP_API_KEY " +
          "(create one at app.reputemap.com → Settings → API keys)."
        : body.slice(0, 300);
    return rpcError(message.id ?? null, -32000, `Upstream HTTP ${resp.status}. ${hint}`);
  }
  return null;
}

const rl = createInterface({ input: process.stdin, terminal: false });

rl.on("line", async (raw) => {
  const line = raw.trim();
  if (!line) return;
  let message;
  try {
    message = JSON.parse(line);
  } catch {
    return;
  }
  const response = await forward(message);
  if (message.id === undefined || message.id === null) return; // notification
  process.stdout.write(
    JSON.stringify(
      response ?? rpcError(message.id, -32002, "Empty upstream response"),
    ) + "\n",
  );
});
