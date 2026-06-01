# Vault Conventions

The portfolio knowledge vault is an Obsidian graph at `~/Documents/Obsidian/Sam/`. It holds cross-project knowledge — people, companies, decisions, concepts, projects. It is NOT a code reference, task tracker, or project-local notepad. `.claude` memory handles project-specific context; the vault handles portfolio-wide context.

## Query Triggers — When to Search the Vault

Before acting, ask: **"Am I about to..."**

1. **Resolve an unknown entity?** — A person, company, or entity name with no local context → `kg_search` or `kg_node`
2. **Make a cross-project recommendation?** — A decision affecting multiple projects → `kg_search` with tag filter for prior decisions
3. **Trace relationships?** — Need to understand how entities connect → `kg_subgraph` (N-hop traversal)
4. **Respond to an operator vault reference?** — Sam says "check the vault", names a vault note, or asks about knowledge not available locally → `kg_search` or `kg_node`

If yes to any → query the vault before proceeding.

### Anti-Triggers — When NOT to Query

- Question answerable from the current repo, git history, or `.claude` memory — local context is cheaper
- Routine code tasks (tests, bug fixes, commands) — vault adds latency without value
- Already queried this entity in the current session — don't re-query

## Memory Graduation — When to Write to Vault

Write to the vault when ALL four criteria are met:

1. **Cross-project relevant** — useful beyond the current project/session
2. **Entity-level** — about a person, company, decision, or concept — not a task detail or code pattern
3. **Durable** — expected to be true in 30 days
4. **Not already in the vault** — check via `kg_search` before writing

Stay in `.claude` memory when ANY of: project-specific operational detail, session-specific context, code patterns, ephemeral state.

**Dual-write:** If information meets graduation AND is needed for the current project, write to both `.claude` memory and vault.

## MCP Server Routing

All vault tools are on the `knowledge-graph` MCP server. Check your intent before every call:

| Intent | Tools |
|---|---|
| Search / read | `kg_search`, `kg_node`, `kg_subgraph`, `kg_paths`, `kg_bridges`, `kg_common` |
| Create note | `kg_create_node` |
| Append to note | `kg_annotate_node` |
| Add wikilink | `kg_add_link` |

**Rule:** Am I reading or writing? Read → search/traversal tools. Write → create/annotate/link tools. Never use a write tool to search or a read tool to write.

## Vault File References in Output

When you mention a vault file in conversation output (chat, channel, or voice), always use the full absolute path: `/Users/samotage/Documents/Obsidian/Sam/<path>`.

Never use:
- Relative paths (`meetings/foo.md`, `people/bar.md`)
- Tilde paths (`~/Documents/Obsidian/Sam/foo.md`)
- Bare wikilinks (`[[foo]]`)

Why: Headspace file preview detection requires paths starting with `/` to generate clickable preview chips. Relative and tilde paths are invisible to the detector.

## Frontmatter Contract

All vault notes use YAML frontmatter with required fields: `type`, `created`, `tags`. See S2 frontmatter contract for the full field list per entity type. When writing notes, always include the required frontmatter.

## Vault Index

The vault index at `data/vault_index.md` lists entity types, high-centrality nodes, recent additions, and tags. Read it at session start to know what's queryable without loading the full graph. The index is regenerated periodically — do not edit it manually.
