---
name: file-search
description: Search the local filesystem for documents and files by topic, keyword, or name. Use when the user asks you to find, locate, or search for a file or document — especially when the search is by topic or content rather than an exact filename. Handles both text-searchable formats (markdown, txt, csv, code) and binary formats (docx, xlsx, pptx, pdf) that cannot be content-searched. Produces ranked results with match-type indicators.
allowed-tools: Glob, Grep, Read, Bash(ls *), Bash(find *), Bash(file *)
---

# File Search — Multi-Pass Document Finder

You are searching the local filesystem to find files matching a user's query. The query is typically a topic or description ("find the document about process monitoring"), not an exact filename.

Your job is to cast a wide net, then rank and present results. Never rely on a single search strategy — binary formats are invisible to content search, and filenames don't always describe content.

---

## Step 1: Understand the Query

Extract from the user's request:
- **Key terms** — the core topic words (e.g., "process monitoring overview")
- **Search root** — where to look. If the user says "in my documents," start at `~/Documents`. If they name a client or project folder, start there. If unspecified, ask.
- **Format hints** — did they say "spreadsheet," "Word doc," "PDF," "markdown"? Use these to prioritise but don't limit the search to just that format.

---

## Step 2: Filename Expansion (ALL formats — this is your primary net)

Binary formats (.docx, .xlsx, .pptx, .pdf) cannot be content-searched. For these files, the filename is the ONLY signal. But even for text-searchable formats, filename matching is fast and catches files where the content match might be buried.

**Generate 5-10 filename glob variations from the key terms:**

For a query like "process monitoring overview":
- Phrase combinations: `*process*monitor*`, `*monitor*process*`
- Individual keywords: `*process*`, `*monitor*`, `*overview*`
- Synonyms: `*surveillance*`, `*observ*`, `*tracking*`
- Naming conventions: the same stems with hyphens, underscores, spaces, camelCase
- Abbreviations: `*proc*mon*`, `*pm_*`

Run each glob pattern across the search root using the Glob tool. Collect the union of all results.

**Important:** Glob is case-sensitive on many systems. For each stem, consider both lowercase and capitalised forms, or use Bash `find -iname` for case-insensitive matching when the Glob tool doesn't cover it:
```
find /path -iname "*process*monitor*" -type f
```

---

## Step 3: Directory Listing (bounded search spaces)

When the search root is a bounded space (a client folder, a project directory, a specific subdirectory), list the entire directory contents:

```
ls -laR /path/to/directory
```

Scan the listing manually. Humans name files in ways that keyword searches miss — acronyms, project codes, dates, version numbers. A 50-file directory listing takes seconds and catches what glob patterns miss.

Skip this step only when the search root is very broad (e.g., all of `~/Documents` with thousands of files).

---

## Step 4: Content Search (text-searchable formats only)

Use Grep to search inside files that support text-based content search.

**Text-searchable formats:** `.md`, `.txt`, `.html`, `.csv`, `.json`, `.yaml`, `.yml`, `.xml`, `.py`, `.rb`, `.js`, `.ts`, `.sh`, `.sql`, `.log`, `.rst`, `.tex`, `.cfg`, `.ini`, `.toml`

**NOT text-searchable (binary):** `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.doc`, `.xls`, `.ppt`, `.numbers`, `.pages`, `.keynote`, `.odt`, `.ods`, `.odp`

Search for key terms in text-searchable files:
```
Grep pattern="process monitoring" path=/search/root glob="*.md"
Grep pattern="process monitoring" path=/search/root glob="*.txt"
```

Run searches for multiple key terms and text formats in parallel.

### Markdown Section Context

For matches in `.md` files, extract the nearest heading above the match to provide section context. This turns "found in `workshop-agenda.md`" into "found in `workshop-agenda.md` > Strategic Opportunities" — much more useful for triage.

To get section context: after finding a match, read a window of lines above it and identify the nearest `#` heading. Include this in your results.

---

## Step 5: Score and Rank

Merge all results from Steps 2-4. Score each file:

| Signal | Weight |
|--------|--------|
| Content match (key terms found inside file) | High |
| Filename matches multiple key terms | High |
| Filename matches single key term | Medium |
| Found in directory listing, name looks relevant | Low |
| Binary format (content not verified) | Flag it |

Deduplicate — a file found by both filename and content search should appear once with both signals noted.

---

## Step 6: Present Results

Present results in descending relevance order. For each result:

1. **File path** (full absolute path)
2. **Match type** — `content match`, `filename match`, or `directory listing`
3. **Format note** — for binary formats, add: `(binary — matched by filename only, content not searchable)`
4. **Section context** — for markdown content matches, include the heading context
5. **Brief relevance note** — why this file matched (which terms, which section)

### Example Output

```
1. /Users/sam/Documents/Clients/ICU/Process Monitoring Subsystem Overview.docx
   📄 Filename match (3/3 terms: process, monitoring, overview)
   ⚠️ Binary format — content not searchable, matched by filename only

2. /Users/sam/Documents/Clients/ICU/workshop-26.4.10/ICU-Workshop-Agenda-2026-04-8.md
   📝 Content match > "Strategic Opportunities" section
   Mentions "process monitoring as a product play using cameras as sensors"

3. /Users/sam/Documents/Clients/ICU/Process_monitoring_estimate_v0.1.xlsx
   📄 Filename match (2/3 terms: process, monitoring)
   ⚠️ Binary format — content not searchable, matched by filename only
```

---

## When There Are No Results

If all passes return nothing:
1. Confirm the search root is correct — ask the user if you're looking in the right place
2. Suggest broadening the search to a parent directory
3. List the directory contents so the user can scan visually

Never report "not found" without having run all three passes (filename, directory, content).

---

## Constraints

- **Never claim content match on a binary file.** If you can't read inside it, say so.
- **Never skip the filename expansion pass.** It's the only strategy that works across all formats.
- **Run independent searches in parallel** — don't run filename globs one at a time.
- **Respect the search root.** Don't search the entire filesystem unless the user asks you to.
- **If a binary text extractor tool becomes available** (MCP or CLI), use it for Tier 1.5 content extraction on binary formats before falling back to filename-only matching.
