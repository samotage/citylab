---
description: "Gmail MCP tool routing rules — which server handles reads vs writes. Load before any Gmail tool call."
---

# Gmail Tool Routing

Two Gmail MCP servers are available.  They are NOT interchangeable.

## Routing table

| Operation | MCP server | Tool prefix | Example |
|-----------|-----------|-------------|---------|
| Search, read, list, get thread | Managed connector | `mcp__claude_ai_Gmail__` | `mcp__claude_ai_Gmail__search_threads` |
| Create draft | Managed connector | `mcp__claude_ai_Gmail__` | `mcp__claude_ai_Gmail__create_draft` |
| Send, forward, modify | klodr | `mcp__gmail__` | `mcp__gmail__send_email` |

## Why the split

The managed connector has Anthropic's classifier protection against prompt injection on the read path.  The klodr server handles writes (because the managed connector is draft-only for outbound).  Using klodr for reads bypasses classifier protection.

## Pre-call self-check

Before every Gmail tool call, verify the prefix:
- About to call a `mcp__gmail__` read tool (`search_emails`, `read_email`, `get_thread`)? → **STOP.  Wrong server.**  Use the `mcp__claude_ai_Gmail__` equivalent
- About to call a `mcp__gmail__` write tool (`send_email`, `forward_email`, `modify_email`)? → Correct server.  Proceed through the content approval gate

## Authorised klodr tools

Only these three klodr tools may be invoked:

| Tool | Authority |
|------|-----------|
| `modify_email` | **Mark-as-read only** — `removeLabelIds: ["UNREAD"]`.  No labels, no archive, no moves |
| `send_email` | After Layer 3 content approval gate (`/email:send-forward-gate`) |
| `forward_email` | After Layer 3 content approval gate — strongest gate (recipient named, full body shown) |

Any other klodr tool exposed by the MCP is **OFF-LIMITS** regardless of OAuth scope.

## Reference

Full security surface: `otl_support/claude_headspace/data/references/email-hardening.md`
