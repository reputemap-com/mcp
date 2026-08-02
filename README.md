# ReputeMap MCP Server

**Manage Google Business Profile reviews from Claude, Cursor, or any MCP client.**

ReputeMap is [Google review management for agencies & local businesses](https://reputemap.com). This hosted MCP server (Model Context Protocol) lets AI agents work with your review data directly — no scripts, no exports, no glue code:

> *"Show me every unanswered review under 3 stars from the last week, worst first."*
> *"How did the Downtown location's rating move this month vs last?"*
> *"Draft replies to the three newest negative reviews in a calm tone."*
> *"We just finished the Hendersons' job — send them a review request."*

- **Registry:** [`com.reputemap/reputemap`](https://registry.modelcontextprotocol.io/v0/servers?search=com.reputemap) (official MCP Registry)
- **Endpoint:** `https://api.reputemap.com/mcp` (Streamable HTTP, hosted — nothing to install)
- **Auth:** `Authorization: Bearer rmk_…` — [create an API key](https://app.reputemap.com/settings/api-keys) (any paid plan; the 14-day free trial counts)
- **Docs:** https://reputemap.com/docs/mcp

## Tools

| Tool | What it does | Credits |
|---|---|---|
| `list_locations` | Every location the org manages, with ids | 1 |
| `list_reviews` | Reviews, filterable (location, rating range, unanswered, last N days) — includes published reply text | 1 |
| `get_review_stats` | Per-location + totals: counts, average rating, 1–5 breakdown, unanswered, trailing-window activity | 1 |
| `send_review_request` | Sends a **real** review-request email through the campaign engine (respects opt-outs; idempotent) | 1 |
| `get_usage` | Current month's credit usage | free |

Tool calls share the plan's **1,000 credits/month** with the [REST API](https://reputemap.com/docs/api).

## Quick start

### npx (any stdio MCP client, incl. Claude Desktop)

```bash
REPUTEMAP_API_KEY="rmk_YOUR_KEY" npx reputemap-mcp
```

Zero dependencies — a [116-line stdio bridge](bin/cli.mjs) that forwards JSON-RPC to the hosted endpoint. npm: [`reputemap-mcp`](https://www.npmjs.com/package/reputemap-mcp)

### Claude Code

```bash
claude mcp add --transport http reputemap https://api.reputemap.com/mcp \
  --header "Authorization: Bearer rmk_YOUR_KEY"
```

### Claude Desktop

Merge [`configs/claude_desktop_config.json`](configs/claude_desktop_config.json) into **Settings → Developer → Edit Config** (Node.js ≥ 18), replace `rmk_YOUR_KEY`, restart the app.

### Cursor

Copy [`configs/cursor-mcp.json`](configs/cursor-mcp.json) to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project) and replace `rmk_YOUR_KEY`.

More recipes (cron digests, CRM sync, CI): [reputemap/examples](https://github.com/reputemap/examples)

## Safety model

The key only reaches data your org already owns. The single write action — `send_review_request` — goes through the same suppression/opt-out engine as in-app campaigns, so an over-eager agent can't spam your customers. Tools carry MCP annotations (`readOnlyHint`/`destructiveHint`), and discovery (`initialize`, `tools/list`) works without a key, so clients can render the catalog before you authenticate. Revoke the key at any time and access dies instantly.

## Links

- 🌐 [reputemap.com](https://reputemap.com) — the product
- 📚 [API docs](https://reputemap.com/docs/api) · [MCP docs](https://reputemap.com/docs/mcp)
- 💼 [LinkedIn](https://www.linkedin.com/company/reputemap)
- ✉️ yaro@reputemap.com
