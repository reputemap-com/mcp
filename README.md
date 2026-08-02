# ReputeMap MCP — Google review management for AI agents

The [Model Context Protocol](https://modelcontextprotocol.io) surface of
[ReputeMap](https://reputemap.com): Google Business Profile reviews — a
filterable review inbox, per-location stats, and honest review-request
campaigns — for Claude, Cursor, Codex, Gemini CLI and any other MCP-capable
agent.

> *"Show me every unanswered review under 3 stars from the last week, worst first."*
> *"Draft replies to the three newest negative reviews in a calm tone."*
> *"We just finished the Hendersons' job — send them a review request."*

**You probably don't need to run anything.** The server is hosted:

```
https://api.reputemap.com/mcp          Streamable HTTP · JSON-RPC 2.0
Authorization: Bearer rmk_YOUR_KEY     app.reputemap.com → Settings → API keys
```

Registry: [`com.reputemap/reputemap`](https://registry.modelcontextprotocol.io/v0/servers?search=com.reputemap) · any paid plan (the 14-day free trial counts).

## Setup per client

**Claude Code** — one command, no restart:

```bash
claude mcp add --transport http reputemap https://api.reputemap.com/mcp \
  --header "Authorization: Bearer rmk_YOUR_KEY"
```

**Cursor** — `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "reputemap": {
      "url": "https://api.reputemap.com/mcp",
      "headers": { "Authorization": "Bearer rmk_YOUR_KEY" }
    }
  }
}
```

**Claude Desktop** — `claude_desktop_config.json`, then restart the app fully:

```json
{
  "mcpServers": {
    "reputemap": {
      "command": "npx",
      "args": ["-y", "@reputemap/mcp"],
      "env": { "REPUTEMAP_API_KEY": "rmk_YOUR_KEY" }
    }
  }
}
```

**VS Code (Copilot agent mode)** — `.vscode/mcp.json`:

```json
{
  "servers": {
    "reputemap": {
      "type": "http",
      "url": "https://api.reputemap.com/mcp",
      "headers": { "Authorization": "Bearer rmk_YOUR_KEY" }
    }
  }
}
```

**Windsurf** — `~/.codeium/windsurf/mcp_config.json` (the field is `serverUrl`):

```json
{
  "mcpServers": {
    "reputemap": {
      "serverUrl": "https://api.reputemap.com/mcp",
      "headers": { "Authorization": "Bearer rmk_YOUR_KEY" }
    }
  }
}
```

**Codex CLI** — `~/.codex/config.toml`, then export `REPUTEMAP_API_KEY`:

```toml
[mcp_servers.reputemap]
url = "https://api.reputemap.com/mcp"
bearer_token_env_var = "REPUTEMAP_API_KEY"
```

**Gemini CLI** — `~/.gemini/settings.json` (the field is `httpUrl`):

```json
{
  "mcpServers": {
    "reputemap": {
      "httpUrl": "https://api.reputemap.com/mcp",
      "headers": { "Authorization": "Bearer rmk_YOUR_KEY" }
    }
  }
}
```

**ChatGPT** — Settings → Connectors → create a custom connector (Developer
mode), point it at `https://api.reputemap.com/mcp` and pick **API key**
authentication, then paste your key.

Full walkthroughs with screenshots: [reputemap.com/docs/mcp](https://reputemap.com/docs/mcp).
More recipes (cron digests, CRM sync): [reputemap/examples](https://github.com/reputemap/examples).

## What's in this repo

A **zero-dependency stdio bridge** for clients that speak MCP over stdio and
can't send HTTP headers — in two flavours: [`bin/cli.mjs`](bin/cli.mjs)
(Node 18+, published as
[`@reputemap/mcp`](https://www.npmjs.com/package/@reputemap/mcp)) and
[`server.py`](server.py) (Python 3.9+, stdlib only). Both forward every
JSON-RPC message to the hosted endpoint over TLS and stream responses back.

```bash
# Node — one-liner, no install
REPUTEMAP_API_KEY="rmk_..." npx -y @reputemap/mcp

# Python — no dependencies
REPUTEMAP_API_KEY="rmk_..." python3 server.py
```

[`server.json`](server.json) is the manifest published to the
[official MCP registry](https://registry.modelcontextprotocol.io) as
`com.reputemap/reputemap`.

Being ~120 readable lines, the bridge doubles as a **reference for what
travels over the wire**: your API key goes only into the `Authorization`
header of TLS requests to `api.reputemap.com` — nothing else, nowhere else.

## Tools

| Tool | What it does | Credits |
|---|---|---|
| `list_locations` | Every location the org manages, with ids | 1 |
| `list_reviews` | Reviews, filterable (location, rating range, unanswered, last N days) — includes published reply text | 1 |
| `get_review_stats` | Per-location + totals: counts, average rating, 1–5 breakdown, unanswered, trailing-window activity | 1 |
| `send_review_request` | Sends a **real** review-request email through the campaign engine (respects opt-outs; idempotent) | 1 |
| `get_usage` | Current month's credit usage | free |

Credits ship with every ReputeMap plan (**1,000/month**, shared with the
[REST API](https://reputemap.com/docs/api)); `get_usage` is free and tells you
where you stand. Rate limit: **60 requests/minute** per org.

The one write action — `send_review_request` — goes through the same
suppression/opt-out engine as in-app campaigns, so an over-eager agent can't
spam your customers. Tools carry MCP annotations
(`readOnlyHint`/`destructiveHint`), and discovery (`initialize`, `tools/list`)
works without a key, so clients can render the catalog before you authenticate.
Revoke the key at any time and access dies instantly.

## Protocol notes

- Methods: `initialize` → `notifications/initialized` → `tools/list` /
  `tools/call`. Protocol errors use standard JSON-RPC codes; tool-level errors
  (bad id, out of credits) come back as tool results your agent can read.
- The server is stateless — no session required; the bridge still honours
  `Mcp-Session-Id` and accepts both JSON and SSE-framed responses.
- Batch requests are rejected (removed in MCP 2025-11-25); foreign `Origin`
  headers are refused.

## Links

- 🌐 [reputemap.com](https://reputemap.com) — Google review management for agencies & local businesses
- 📚 [API docs](https://reputemap.com/docs/api) · [MCP docs](https://reputemap.com/docs/mcp)
- 💼 [LinkedIn](https://www.linkedin.com/company/reputemap)
- ✉️ yaro@reputemap.com

## License

MIT — see [LICENSE](LICENSE).
