# ReputeMap MCP: Google review management for AI agents

The [Model Context Protocol](https://modelcontextprotocol.io) server of
[ReputeMap](https://reputemap.com). It gives Claude, Cursor, Cline, VS Code,
Codex, Gemini CLI and any other MCP client your Google Business Profile
reviews: a filterable review inbox with owner replies inlined, per-location
stats, AI reply drafts, publishing a reply you approved, and honest
review-request emails.

> *"Show me every unanswered review under 3 stars from the last week, worst first."*
> *"Draft replies to the three newest negative reviews in a calm tone."*
> *"Publish the second draft for the Riverside review, exactly as written."*
> *"We just finished the Hendersons' job. Send them a review request."*

**You probably don't need to run anything.** The server is hosted:

```
https://api.reputemap.com/mcp          Streamable HTTP · JSON-RPC 2.0
Authorization: Bearer rmk_YOUR_KEY     app.reputemap.com → Settings → API keys
```

Registry: [`com.reputemap/reputemap`](https://registry.modelcontextprotocol.io/v0/servers?search=com.reputemap)
· included in every paid plan, from Solo ($19/month), and in the 14-day trial.

## Tools

Seven tools: four read, three act.

| Tool | What it does | Type | Credits |
|---|---|---|---|
| `list_locations` | Every location the org manages, with the ids the other tools take | read-only | 1 |
| `list_reviews` | Google reviews, newest first, with the published owner reply inlined. Filter by location, star range, unanswered only, or the last N days; up to 50 per page with `offset` paging. Each review carries Google's moderation state of the reply (`reply_state`, `reply_policy_violation`) | read-only | 1 |
| `get_review_stats` | Per location and org-wide: review count, average rating, 1–5★ breakdown, unanswered count, and activity in a trailing window (default 30 days) | read-only | 1 |
| `draft_reply` | 2–3 reply drafts for one review from ReputeMap's own generator, in the business's saved voice and sign-off. Optional one-off `instructions` (e.g. "keep it under 40 words"). Saves the draft to the app's editor and **never publishes** | saves a draft | 1 |
| `publish_reply` | Publishes the exact reply text the user approved to the review on Google | posts to Google | 1 |
| `send_review_request` | Sends **one real** review-request email to a customer through ReputeMap's campaign engine | sends email | 1 |
| `get_usage` | This month's credit usage, limit and rate limit | read-only | free |

Tools carry MCP annotations: the four read tools have `readOnlyHint`; the
other three don't, and `publish_reply` is also marked `destructiveHint`. Those
are the signals that make a client ask you before it runs a tool.

## Safety: what an eager agent can and can't do

- **Your data only.** The key reaches exactly what your org owns: its
  locations, reviews and stats. Cross-origin browser calls are refused.
- **Drafting never publishes.** `draft_reply` stores drafts in ReputeMap. Nothing
  reaches Google until `publish_reply` is called or someone clicks Publish in the app.
- **Publishing needs your explicit yes.** `publish_reply` takes the exact text you
  approved and nothing else. It replaces any existing owner reply on that review,
  which is why it is flagged destructive, and every publish is audit-logged. If
  Google refuses the request, the text stays in ReputeMap with a manual fallback
  (`status: "manual_required"`), so your words are never lost.
- **Google moderates owner replies, and the tools tell you.** `publish_reply`
  answers with `google_state`: `pending` means Google is checking the reply before
  showing it. `status: "rejected_by_google"` means Google won't show it;
  `policy_violation` and `detail` say why, so write a different reply.
  `list_reviews` carries the same state on every review, and a rejected reply
  counts as no reply for `unanswered_only`.
- **Opt-outs still win.** `send_review_request` runs through the same opt-out and
  suppression checks as in-app campaigns. If this location already asked this
  address, you get `status: "already_requested"`: no second email goes out and the
  credit is given back. It is still a real email to a real person, so it is
  annotated non-idempotent and clients confirm first.
- **Revoke in one click.** Keys are stored only as hashes and shown once. Revoking
  one cuts access off immediately.

## Get an API key

1. Have a ReputeMap workspace on any paid plan, or on the 14-day trial (card
   required). [Start here](https://app.reputemap.com/register).
2. In the app: **Settings → API keys** (owners and admins). The key starts with
   `rmk_` and is shown once.

Then pick your client below. Each client has two ways in:

- **Remote** (recommended): the client talks to `https://api.reputemap.com/mcp`
  directly and sends the key as an `Authorization: Bearer` header.
- **Local stdio bridge**: for clients that can only start a local program. The
  client runs `npx -y @reputemap/mcp` (Node 18+) with `REPUTEMAP_API_KEY` set,
  and the bridge forwards everything to the hosted endpoint.

## Setup per client

### Claude Code

Remote, one command, no restart:

```bash
claude mcp add --transport http reputemap https://api.reputemap.com/mcp \
  --header "Authorization: Bearer rmk_YOUR_KEY"
```

Writing `.mcp.json` by hand? Include `"type": "http"` in the entry. Without
it, Claude Code reads the entry as a local program and fails.

Stdio bridge instead:

```bash
claude mcp add reputemap -e REPUTEMAP_API_KEY=rmk_YOUR_KEY -- npx -y @reputemap/mcp
```

### Claude Desktop

Use the stdio bridge in `claude_desktop_config.json` (Settings → Developer →
Edit Config), then fully quit and reopen the app. Needs Node.js 18+.

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

The generic [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) bridge works too:
`"args": ["-y", "mcp-remote", "https://api.reputemap.com/mcp", "--header", "Authorization: Bearer rmk_YOUR_KEY"]`.

### Cursor

Remote, in `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

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

Stdio bridge instead:

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

### Cline

Open Cline → **MCP Servers** → **Configure MCP Servers**, which opens
`cline_mcp_settings.json`, and add the server. Remote:

```json
{
  "mcpServers": {
    "reputemap": {
      "type": "streamableHttp",
      "url": "https://api.reputemap.com/mcp",
      "headers": { "Authorization": "Bearer rmk_YOUR_KEY" },
      "disabled": false
    }
  }
}
```

Stdio bridge instead:

```json
{
  "mcpServers": {
    "reputemap": {
      "command": "npx",
      "args": ["-y", "@reputemap/mcp"],
      "env": { "REPUTEMAP_API_KEY": "rmk_YOUR_KEY" },
      "disabled": false
    }
  }
}
```

### VS Code (Copilot agent mode)

`.vscode/mcp.json` in the workspace. The top-level key is `servers`, not
`mcpServers`. VS Code asks for the key once and stores it, so it stays out of the file:

```json
{
  "inputs": [
    { "type": "promptString", "id": "reputemap-key", "description": "ReputeMap API key (rmk_...)", "password": true }
  ],
  "servers": {
    "reputemap": {
      "type": "http",
      "url": "https://api.reputemap.com/mcp",
      "headers": { "Authorization": "Bearer ${input:reputemap-key}" }
    }
  }
}
```

Stdio bridge instead: replace the `reputemap` entry with
`{ "type": "stdio", "command": "npx", "args": ["-y", "@reputemap/mcp"], "env": { "REPUTEMAP_API_KEY": "${input:reputemap-key}" } }`.

### Windsurf

`~/.codeium/windsurf/mcp_config.json`. Note the field is `serverUrl`:

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

### Codex CLI

`~/.codex/config.toml`, then export `REPUTEMAP_API_KEY` in your shell:

```toml
[mcp_servers.reputemap]
url = "https://api.reputemap.com/mcp"
bearer_token_env_var = "REPUTEMAP_API_KEY"
```

### Gemini CLI

```bash
gemini mcp add --transport http reputemap https://api.reputemap.com/mcp \
  --header "Authorization: Bearer rmk_YOUR_KEY"
```

Or in `~/.gemini/settings.json`, where the field is `httpUrl`:

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

### Any other MCP client

```
URL:        https://api.reputemap.com/mcp
Transport:  Streamable HTTP (JSON-RPC 2.0 over POST)
Header:     Authorization: Bearer rmk_YOUR_KEY   (X-API-Key: rmk_YOUR_KEY also works)
```

ChatGPT isn't supported yet: its connectors accept only OAuth, and this server
uses an API key.

**Check the connection:** ask *"list my ReputeMap locations"*. If the ids come
back, you're connected.

## Credits and limits

- **1,000 credits a month per org**, the same on every plan and shared with the
  [REST API](https://reputemap.com/docs/api). Credits reset on the 1st.
- Every tool call costs 1 credit except `get_usage`, which is free. A call with
  malformed arguments is rejected before a credit is charged, and a
  `send_review_request` that comes back `already_requested` is refunded.
- **60 requests a minute** per org.
- When credits run out, tools answer with an error your agent can read
  ("Monthly API credit limit reached"). `get_usage` tells you where you stand.

| Symptom | Cause and fix |
|---|---|
| `401` invalid or missing API key | Typo, or the key was revoked. Create a new one in Settings → API keys |
| `403` … requires an active paid plan | The workspace has no subscription. [Pick a plan](https://reputemap.com/#pricing); the 14-day trial counts |
| "Monthly API credit limit reached" | Credits reset on the 1st; check `get_usage` |
| Claude Desktop shows no tools | `npx` needs Node.js 18+; fully quit and reopen the app after editing the config |

## What's in this repo

A **zero-dependency stdio bridge** for clients that speak MCP over stdio and
can't send HTTP headers, in two flavours: [`bin/cli.mjs`](bin/cli.mjs)
(Node 18+, published as
[`@reputemap/mcp`](https://www.npmjs.com/package/@reputemap/mcp)) and
[`server.py`](server.py) (Python 3.9+, standard library only). Both forward
every JSON-RPC message to the hosted endpoint over TLS and stream the
responses back. The bridge holds no tool list of its own, so new tools reach
you as soon as the hosted server ships them.

```bash
# Node: one-liner, no install
REPUTEMAP_API_KEY="rmk_..." npx -y @reputemap/mcp

# Python: no dependencies
REPUTEMAP_API_KEY="rmk_..." python3 server.py
```

[`server.json`](server.json) is the manifest published to the
[official MCP registry](https://registry.modelcontextprotocol.io) as
`com.reputemap/reputemap`. [`.plugin/plugin.json`](.plugin/plugin.json) and
[`.mcp.json`](.mcp.json) describe the same server for plugin-aware clients.

The bridge is about 120 readable lines, so it also documents what travels
over the wire: your API key goes only into the `Authorization` header of TLS
requests to `api.reputemap.com`.

## Protocol notes

- Methods: `initialize` → `notifications/initialized` → `tools/list` /
  `tools/call`, plus `ping`. Supported revisions: 2024-11-05, 2025-03-26,
  2025-06-18, 2025-11-25.
- Discovery (`initialize`, `ping`, `tools/list`) answers without a key, so
  clients and directories can show the tool catalogue before you authenticate.
  `tools/call` always needs the key.
- Protocol errors use standard JSON-RPC codes. Tool-level errors (bad id, out
  of credits) come back as tool results with `isError: true`, so your agent can
  read them and tell you.
- The server is stateless: POST only, no session and no server-initiated SSE
  stream (`GET` answers 405). The bridge still honours `Mcp-Session-Id` and
  accepts both JSON and SSE-framed responses.
- JSON-RPC batches are accepted only from clients that negotiated a revision
  older than 2025-06-18, which removed batching. Requests with a foreign
  `Origin` header are refused.

## Links

- [reputemap.com](https://reputemap.com): Google review management for local businesses and agencies
- [MCP server overview](https://reputemap.com/mcp) · [MCP setup reference](https://reputemap.com/docs/mcp) · [REST API docs](https://reputemap.com/docs/api)
- Recipes (cron digests, CRM sync): [reputemap-com/examples](https://github.com/reputemap-com/examples)
- Companion agent skills: [reputemap-com/review-skills](https://github.com/reputemap-com/review-skills) (`npx skills add reputemap-com/review-skills`)
- [LinkedIn](https://www.linkedin.com/company/reputemap) · yaro@reputemap.com

ReputeMap is an independent tool and is not affiliated with Google.

## License

MIT, see [LICENSE](LICENSE).
