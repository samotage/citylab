---
name: morning-briefing
description: Run a strategic morning briefing that scans the web for AI, RAG, Claude, Rails, energy, MCP ecosystem, Anthropic platform changes, open-source agent frameworks, local/edge models, AI regulation (ANZ), AI agency landscape, inference economics, vertical AI plays, competitor intelligence, SMB AI services market, agentic marketing, sellable service opportunities, and critical Linux/infrastructure CVEs and security advisories. Produces a structured, actionable report.
argument-hint: "[--days N] [--format json] [--deep] [--section claude|rag|rails|energy|models|tools|regulation|services|marketing|failures|security]"
allowed-tools: WebSearch, WebFetch, Read, Write, Bash(date *), Bash(mkdir -p *)
---

# Morning Briefing — Strategic Intelligence Report

You are producing a morning briefing for the founder of an agentic-first startup building RAGlue — a citation-first RAG platform targeting technical-adjacent professionals (trades, field service, energy). The founder also runs ICU Solarcam (solar/camera IoT) and OtageLabs — an AI services consultancy targeting SMBs who need real agentic automation (not ChatGPT wrappers). OtageLabs' technical edge: Claude Code, MCP, orchestration pipelines, human-in-the-loop agent systems. The stack is Rails 8 + Postgres + Claude API.

The briefing serves TWO purposes: (1) technical intelligence for product development, and (2) commercial intelligence for selling OtageLabs services to SMBs — particularly those burned by low-quality AI service providers.

This briefing is the first thing read each day. Every item must earn its place. Five high-relevance items beat fifty mediocre ones. If a section has nothing worth reporting, say so in one line and move on.

---

## Deduplication Protocol (CRITICAL — No Groundhog Day)

**Before writing any output**, scan the archive directory `docs/morning-briefings/` for previous briefings. Read at least the last 3 briefing files (or all if fewer than 3 exist). Extract every topic, article, product, repo, event, and action item already covered.

**Rules:**
- **Do NOT re-report anything already covered in a previous briefing** unless there is a genuinely new development (e.g., a version bump on a previously covered tool, a follow-up to a story).
- **If a story has been developing** across multiple days, only report the NEW information. Don't re-explain the background.
- **Old statistics and studies** (e.g., "95% of AI pilots fail" from MIT 2025) should NEVER be re-reported. They're known context, not news. Reference them only if a new article builds meaningfully on them.
- **Trending GitHub repos** already featured in previous briefings should only reappear if they've had a significant change (major release, viral growth spike, new feature).
- **Regulatory items** (EU AI Act dates, Australia AI policy) are known calendar items. Only re-report if there's a concrete new development (new legislation tabled, new deadline announced), not just another article restating the same timeline.
- **CVEs** already covered in a previous briefing should only reappear if there is a material new development: a patch becomes available, exploit confirmed in the wild, affected systems list changes, or CISA adds it to the KEV catalog after initial coverage.
- When in doubt, leave it out. The user has explicitly said: "We don't need to be here on Groundhog Day."

---

## Research Protocol

Execute the following searches. **Run as many WebSearch and WebFetch calls in parallel as possible** to complete within 60 seconds. Do not run searches sequentially when they have no dependencies.

### Phase 1 — Parallel Intelligence Sweep

Run ALL of these simultaneously:

**Core Intelligence (always run):**

1. `WebFetch` https://www.anthropic.com/news — extract all articles from the last $DAYS days. Note titles, dates, and URLs.
2. `WebFetch` https://news.ycombinator.com/front — capture front page stories. For EVERY flagged story, capture TWO separate URLs: (a) the actual article URL (the destination link, e.g. `amplifying.ai/what-claude-code-chooses`), and (b) the HN discussion URL (e.g. `news.ycombinator.com/item?id=12345`). Flag anything touching: AI agents, RAG, Claude, citation, Ruby/Rails, agentic coding, developer tools.
3. `WebFetch` https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — extract the most recent changelog entries.
4. `WebFetch` https://github.com/trending/ruby?since=daily — capture trending Ruby repos. For each repo, capture the full GitHub URL (e.g. `github.com/owner/repo`).
5. `WebSearch` "Claude API" OR "Claude Code" OR "Anthropic" updates OR changes OR release — last $DAYS days
6. `WebSearch` RAG framework OR "retrieval augmented generation" OR citation AI — new OR launch OR release OR update — last $DAYS days
7. `WebSearch` "citation" OR "attribution" OR "source fidelity" RAG AI — startup OR product OR competitor — last $DAYS days

**Ecosystem Intelligence (always run):**

8. `WebSearch` AI model release OR pricing OR "open source model" — OpenAI OR Google OR Meta OR Mistral OR Anthropic — last $DAYS days
9. `WebSearch` agentic coding OR "AI IDE" OR "Cursor" OR "Windsurf" OR "Cline" OR "Claude Code" — update OR release OR workflow — last $DAYS days
10. `WebSearch` "Rails 8" OR Hotwire OR Turbo OR Kamal OR "Ruby 3" — update OR release — last $DAYS days
11. `WebSearch` pgvector OR "vector search" PostgreSQL — update OR release OR benchmark — last $DAYS days
12. `WebSearch` AI regulation OR "AI policy" Australia OR "EU AI Act" — last $DAYS days
13. `WebSearch` "MCP" OR "model context protocol" OR "multi-agent" OR "agent orchestration" — framework OR pattern OR update — last $DAYS days

**Business & Services Intelligence (always run):**

14. `WebSearch` AI automation agency OR "AI services" small business OR SMB — pricing OR package OR new OR launch — last $DAYS days
15. `WebSearch` agentic marketing OR "AI marketing automation" OR "AI lead generation" OR "AI sales automation" — small business OR SMB OR agency — last $DAYS days
16. `WebSearch` AI implementation failure OR "AI chatbot" failed OR disappointed OR wasted OR "bad experience" — small business OR SMB — last $DAYS days
17. `WebSearch` AI agent UI OR "agent interface" OR "human in the loop" OR "AI dashboard" — design OR UX OR pattern — last $DAYS days
18. `WebSearch` "Claude Code" OR "MCP server" OR "agentic workflow" — consulting OR services OR agency OR freelance — last $DAYS days
19. `WebSearch` AI services professional services OR trades OR healthcare OR "real estate" OR "home services" — automation OR agent — last $DAYS days

**Platform & Infrastructure Intelligence (always run):**

20. `WebSearch` "MCP server" OR "model context protocol" — new OR release OR ecosystem OR registry OR community — last $DAYS days
21. `WebSearch` Anthropic API pricing OR "Claude pricing" OR "rate limit" OR "beta" OR "new feature" — last $DAYS days
22. `WebSearch` "open source agent framework" OR LangGraph OR CrewAI OR AutoGen OR "agent SDK" — release OR update OR comparison — last $DAYS days
23. `WebSearch` Ollama OR "llama.cpp" OR "local model" OR "edge AI" OR "small language model" — release OR benchmark OR deployment — last $DAYS days

**Market & Regulatory Intelligence (always run):**

24. `WebSearch` "AI regulation" OR "AI policy" OR "AI governance" Australia OR "New Zealand" OR ANZ — legislation OR compliance OR framework — last $DAYS days
25. `WebSearch` AI services OR "AI consulting" OR "AI agency" — legal OR trades OR healthcare OR "real estate" OR "property" — vertical OR specialisation — last $DAYS days
26. `WebSearch` "AI agency" OR "AI consultancy" — launched OR closed OR pivot OR funding OR pricing — last $DAYS days
27. `WebSearch` "GPU" OR "inference cost" OR "inference pricing" OR "API pricing war" — AI OR LLM — trend OR drop OR comparison — last $DAYS days

**Secondary Scans (always run, but only report if genuinely significant):**

28. `WebSearch` AEMO OR "Australian energy market" OR "solar" OR IoT — significant news — last $DAYS days
29. `WebSearch` "Product Hunt" AI agent OR RAG OR developer tool — launched this week
30. `WebFetch` https://github.com/trending/python?since=daily — capture trending Python repos. For each repo, capture the full GitHub URL (e.g. `github.com/owner/repo`). Flag anything RAG/AI/agent related.
31. `WebSearch` site:reddit.com (r/LocalLLaMA OR r/MachineLearning OR r/rails OR r/smallbusiness OR r/entrepreneur) — top posts this week
32. `WebSearch` "Hacker News" OR site:news.ycombinator.com — "AI agent" OR "developer tools" OR "AI startup" — trending OR top — last $DAYS days

**Security Intelligence (always run — this is infrastructure-critical):**

33. `WebFetch` https://www.cisa.gov/known-exploited-vulnerabilities-catalog — extract all CVEs added in the last 7 days. For each: CVE ID, vendor/product, vulnerability name, date added. The CISA KEV catalog is the authoritative list of vulnerabilities being actively exploited in the wild — anything here requires immediate attention regardless of $DAYS.
34. `WebSearch` Linux kernel CVE OR vulnerability CRITICAL OR HIGH — disclosed OR patched — last $DAYS days
35. `WebSearch` Ubuntu "security notice" OR "Red Hat security advisory" OR "AWS security bulletin" — CRITICAL OR HIGH — last $DAYS days

### Phase 2 — Deep Dives & URL Resolution

After Phase 1 results arrive, **date-filter first**: discard any result older than 30 days before ranking.  Then identify the **top 3-5 most significant findings** and use `WebFetch` on the **actual article URL** (NOT the aggregator page) to pull the full source for deeper analysis.  When you fetch the article, confirm its publication date from the page content — if it turns out to be older than 30 days, drop it and move to the next candidate.

**URL resolution rules:**
- If a finding came from Hacker News, WebFetch the **article's own URL** (the external link), not the HN discussion page.
- If a finding came from WebSearch, WebFetch the **actual source page** returned in the search results, not the search engine.
- If a finding came from GitHub trending, WebFetch the **repo's GitHub page** directly.
- If a finding came from Reddit via WebSearch, WebFetch the **linked article** if one exists, or note it as "Reddit discussion" with the subreddit and post title.
- For Anthropic blog items, WebFetch the **full article URL** (e.g. `https://anthropic.com/news/article-slug`), not the `/news` index page.

**Never cite a URL you haven't verified.** If you cannot confirm the actual destination URL for an article, say "URL unconfirmed" rather than guessing.

Prioritise:
- **ANY CVE on the CISA KEV catalog** — these are being actively exploited. Always deep-dive.
- Anything that directly impacts RAGlue's competitive position
- Claude/Anthropic changes that affect the tech stack
- Emerging competitors in citation-first RAG
- Rails/Postgres changes that affect infrastructure decisions
- SMB AI service market shifts — new agencies, pricing changes, vertical plays
- AI implementation failures that validate OtageLabs' positioning
- New agentic marketing tools or techniques that could be packaged as services
- AI agent UI/UX patterns that differentiate real products from demo-ware

---

## Argument Handling

Parse `$ARGUMENTS` for these flags:

| Flag | Default | Effect |
|------|---------|--------|
| `--days N` | 1 | Look back N days |
| `--format json` | markdown | Output as JSON instead of markdown |
| `--deep` | off | Run additional WebFetch on all flagged items, not just top 3-5 |
| `--section X` | all | Only run searches for section X (claude, rag, rails, energy, models, tools, regulation, services, marketing, failures, mcp, platform, frameworks, local, agencies, inference, verticals, security) |

If no arguments are provided, use defaults. Set `$DAYS` to the `--days` value (default 1).

---

## Output Format

### Markdown (default)

```
# Morning Briefing — [DATE]

## TL;DR
- [Most important item — one sentence, why it matters to YOU]
- [Second most important — one sentence]
- [Third — one sentence]
- [Fourth if warranted]
- [Fifth if warranted]

---

## Claude & Anthropic
[Items from searches 1, 2, 3, 5]

**[One-line summary of finding]**
Article: [actual article URL — the page you'd click through to read]
Discussion: [HN/Reddit discussion URL, if applicable — omit if none]
Relevance: `[action]` | `[watch]` | `[FYI]`
> [1-2 sentence context: what this means for your stack/business]

---

## RAG & Citation Intelligence
[Items from searches 6, 7]
[Same item format as above]
[ALWAYS flag any competitor entering citation-first RAG — this is top priority intelligence]

---

## AI Models & Industry
[Items from searches 8, 12, 13]
[Same item format]

---

## Agentic Development & Tooling
[Items from searches 9, 13]
[Same item format]

---

## Rails, Ruby & Postgres
[Items from searches 4, 10, 11]
[Same item format]

---

## Critical CVEs & Security Advisories
[Items from searches 33, 34, 35]
[This section runs EVERY briefing regardless of --section flag. Security is never optional.]
[FILTER: only report CVEs with CVSS >= 7.0 (HIGH or CRITICAL) OR any CVE on the CISA KEV catalog regardless of score]
[SCOPE: Linux kernel, Ubuntu, AWS infrastructure, Ruby/Rails dependencies, PostgreSQL, Nginx, and any component in the OtageLabs/ICU stack]
[If nothing meets the threshold: "No HIGH/CRITICAL CVEs in the last 7 days affecting the stack."]

**[CVE-XXXX-XXXXX — "Nickname" if it has one — CVSS N.N (SEVERITY)]**
Article: [NVD or vendor advisory URL]
CISA KEV: `[yes — actively exploited]` | `[no]`
Patch available: `[yes]` | `[no — workaround only]` | `[no mitigation yet]`
Relevance: `[action]` | `[watch]`
> [1-2 sentences: what the vulnerability does, what an attacker can do if they exploit it]
> [1 sentence: which parts of the ICU/OtageLabs stack are in the affected range, and whether they are protected]
> [If patch available: what the fix is and how urgent the reboot/update is]

---

## SMB AI Services Market
[Items from searches 14, 18, 19]
[Track: new AI agencies launching, pricing shifts, service package trends, vertical specialisation moves]
[ALWAYS flag agencies entering the agentic/Claude/MCP space — these are direct competitors]
[Note any pricing intelligence — what are agencies charging for what]

**[One-line summary of finding]**
Article: [actual article URL]
Relevance: `[action]` | `[watch]` | `[FYI]`
> [1-2 sentence context: what this means for OtageLabs' positioning/pricing]

---

## Agentic Marketing & Sales Intelligence
[Items from searches 15, 19]
[Track: AI-driven marketing tools, lead gen automation, content automation, outreach tools]
[Focus on tools/techniques OtageLabs could either USE for its own marketing or SELL as a packaged service]

---

## AI Implementation Failures & Trust Signals
[Items from searches 16]
[Track: SMB AI implementation horror stories, disappointed customers, wasted budgets, overpromised/underdelivered]
[This section validates OtageLabs' "we actually ship" positioning — every failure story is a potential sales angle]
[Note patterns: what went wrong, what the customer expected vs got, what vertical they're in]

---

## AI Agent UI & New Tools
[Items from searches 17, 21]
[Track: agent interface patterns, human-in-the-loop design, dashboard UX, new AI tools/platforms]
[Focus on what differentiates "actually usable" products from demo-ware]

---

## MCP Ecosystem & Tooling
[Items from searches 20, 13]
[Track: new MCP servers, protocol changes, community tools, registry updates, integration patterns]
[This directly affects what OtageLabs can build and sell — new MCP servers = new integration capabilities]

---

## Anthropic Platform & Pricing
[Items from searches 21, 5]
[Track: API pricing changes, new features, rate limit adjustments, beta programs, deprecations]
[Direct cost/capability impact on the stack — flag anything that changes unit economics]

---

## Open-Source Agent Frameworks
[Items from search 22]
[Track: LangGraph, CrewAI, AutoGen, and new entrants — releases, benchmarks, adoption signals]
[Know what the competition is building with, even if you don't use these frameworks]
[Flag any framework gaining serious traction — could indicate market direction]

---

## Local & Edge Models
[Items from search 23]
[Track: Ollama, llama.cpp, small models, edge deployment — releases, benchmarks, practical use cases]
[Relevant for privacy-sensitive SMB deployments where data can't leave the premises]
[Only report if genuinely useful for SMB deployment, not academic benchmarks]

---

## AI Regulation & Compliance (ANZ)
[Items from searches 24, 12]
[Track: Australian and NZ AI legislation, compliance frameworks, industry guidance]
[SMBs will need compliance guidance — this is a service opportunity for OtageLabs]
[Flag anything that creates urgency or deadlines for businesses]

---

## AI Agency & Consultancy Landscape
[Items from searches 26, 14]
[Track: who's launching, who's pivoting, who's failing, funding rounds, pricing signals]
[Pattern recognition for OtageLabs positioning — where are the gaps, what's oversaturated]

---

## Inference & Compute Economics
[Items from search 27]
[Track: GPU availability, inference pricing trends, API pricing wars, cost-per-token movements]
[Directly affects margin on any AI service OtageLabs delivers]
[Only report significant moves — not daily noise]

---

## Vertical AI Plays
[Items from search 25]
[Track: AI adoption in specific industries — legal, trades, healthcare, property, field service]
[Each vertical is a potential niche entry point for OtageLabs services]
[Flag any vertical showing rapid adoption or unmet demand]

---

## Energy & IoT
[Items from search 28 — only if there's something genuinely significant]
[If nothing: "No significant developments today."]

---

## Opportunities

### Service Packaging Ideas
- [New service ideas based on today's findings — what could OtageLabs sell?]
- [Vertical-specific opportunities spotted]
- [Pricing signals — what the market will bear]

### Content & Outreach Opportunities
- [LinkedIn post ideas based on today's findings — especially "burned by bad AI" angles]
- [Blog post angles that establish authority]
- [Case study opportunities — what would make a compelling before/after]

### Competitive Signals
- [Any moves by competitors or adjacent players]
- [Market openings spotted]
- [Agencies entering or exiting the space]

### Action Items
- [Things to DO today based on findings, not just FYI]
- [Sales/outreach actions — who to reach out to, what to post]

---

## Calendar & Upcoming
- [Upcoming deadlines, launches, events, or releases worth tracking]
- [Conference dates, beta deadlines, deprecation timelines]

---

*Sources consulted: [count] searches, [count] pages fetched*
*Generated: [timestamp]*
```

### JSON (--format json)

Output the same structure as a JSON object with keys: `date`, `tldr` (array), `sections` (object of arrays), `opportunities` (object), `calendar` (array), `metadata` (object with source_count, generated_at).

---

## Quality Standards

### Relevance Tags
- `[action]` — You should DO something about this today. Change code, update a dependency, respond to a competitor, write content.
- `[watch]` — Not actionable today but developing. Check back in 1-2 weeks.
- `[FYI]` — Good to know, no action needed. Context for future decisions.

### Source Integrity (CRITICAL)
- **Every item MUST link to the actual article URL** — the page a human would click to read the full content. Never link to an aggregator index page (e.g. `news.ycombinator.com/front`) when the actual article lives elsewhere (e.g. `amplifying.ai/what-claude-code-chooses`).
- **Link text MUST be the full URL path, not a site name.** The reader needs to see where the link goes.
  - WRONG: `[TechCrunch](https://techcrunch.com)` — this is a homepage, not an article
  - WRONG: `[anthropic.com](https://anthropic.com)` — this is a homepage, not the specific page
  - WRONG: `[github.com/googleworkspace](https://github.com/googleworkspace)` — this is an org page, not the specific repo
  - RIGHT: `[techcrunch.com/2026/03/04/anthropic-ceo-dario-amodei-...](https://techcrunch.com/2026/03/04/anthropic-ceo-dario-amodei-calls-openais-messaging-around-military-deal-straight-up-lies-report-says/)`
  - RIGHT: `[anthropic.com/research/labor-market-impacts](https://www.anthropic.com/research/labor-market-impacts)`
  - RIGHT: `[github.com/googleworkspace/cli](https://github.com/googleworkspace/cli)`
- **Every URL must point to the SPECIFIC page** — the article, the repo, the announcement, the research paper. Never link to a homepage, an org page, or a section landing page when a specific URL exists. If WebSearch returned a specific URL, USE IT.
- **Aggregator pages and article pages are different things.** HN front page, GitHub trending, Anthropic /news index, Reddit subreddit pages — these are discovery surfaces. The articles they link to are the actual sources. Always cite the article, not the discovery surface.
- **If an item was found via HN or Reddit**, provide BOTH the article URL and the discussion URL as separate links. The reader may want either.
- **Never reuse a URL across multiple items.** Each item must have its own verified URL. If two items share a source, they should probably be merged into one item.
- **Never fabricate or guess URLs.** If you cannot confirm the exact URL from the search results or fetched page, write "URL unconfirmed — search for: [descriptive search terms]" instead.
- **WebSearch results contain URLs** — use them. When WebSearch returns a result, the URL in that result is the article URL. Capture it at search time, don't try to reconstruct it later. Do NOT discard the specific URL and substitute a homepage later.

### Signal Discipline
- **Do not pad sections.** If a search returned nothing relevant, say "No significant developments" and move on.
- **Do not echo search noise.** Listicles, AI-generated filler articles, and recycled content are not intelligence. Skip them.
- **Date-check everything — HARD CUTOFF.**  Every item must have a publication date.  Before including ANY item, verify its publication date from the article page, byline, or URL slug.  Rules:
  - **Hard cutoff: 30 days.**  Nothing older than 30 days from today's date, period.  No exceptions, no "foundational reference" escape clause.  If the article is older than 30 days, it is not news — drop it.
  - **Soft cutoff: 21 days.**  Items older than 21 days should only appear if they represent a genuinely new development (e.g., a product launched last week that you're seeing for the first time).
  - **If you cannot determine the publication date**, do not include the item.  Write "date unconfirmed — skipped" in your working notes and move on.
  - **WebSearch results often return old articles** ranked by relevance, not recency.  The "last N days" search qualifier is unreliable — search engines routinely return older results.  Always verify the actual publication date on the article itself.
- **Confidence signal.** If you only found one weak source for something, flag it: "Single source — verify independently."
- **Competitive findings always go to the top.** Anyone entering the citation-first RAG space or targeting technical-adjacent professionals is priority intelligence regardless of section.

### Source Hierarchy
1. Official announcements (Anthropic blog, GitHub releases, company blogs)
2. Practitioner experience (HN discussions, Reddit threads with real usage, r/smallbusiness, r/entrepreneur)
3. Aggregators with editorial quality (The Information, TechCrunch, ArsTechnica)
4. Industry reports (BCG, McKinsey, PwC, US Chamber of Commerce — for market sizing and trends)
5. Newsletters and curated digests (TLDR AI, Ruby Weekly)
6. Blog posts and tutorials (useful for ecosystem signals, low weight for news)
7. AI agency/consultancy websites (useful for competitive intelligence and pricing signals — treat claims skeptically)

### What NOT to include
- AI hype pieces with no substance
- "Top 10 AI tools" listicles
- Press releases that are just marketing
- Anything you've seen recycled across multiple low-quality sources
- Theoretical papers with no practical implications for the business

---

## Output Delivery

**Two-step output: SCREEN FIRST, then DISK.**

### Step 1 — Print to screen (MANDATORY)

After completing all research, **output the entire briefing as plain text in the chat**. The user reads the briefing on screen — in the chat window or via voice. Do NOT summarise, abbreviate, or show a "TL;DR only" version. Print the FULL briefing — every section, every link, every table, every item — directly to the conversation. This is the primary delivery method.

### Step 2 — Save to disk (after screen output)

After the full briefing has been printed to screen, save an identical copy to disk:

- **Directory:** `docs/morning-briefings/` **relative to your current working directory** (the project root you were launched in)
- **Filename format:** `YYYY-MM-DD-Day-HHMM-slug.md` where:
  - `YYYY-MM-DD` is the briefing date
  - `Day` is the day of the week (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
  - `HHMM` is the local time the briefing was generated (24hr format)
  - `slug` is a short kebab-case slug (2-5 words) of the most significant item in the briefing
  - Example: `2026-03-03-Mon-0610-webmcp-chrome-early-preview.md`
- **Create the directory** if it doesn't exist yet (use `Bash` to `mkdir -p docs/morning-briefings/`)
- **Write the full briefing** (the complete markdown output) to the file using the `Write` tool
- **Confirm the save** at the end of the output with the full filename

**Path rule:** Your working directory is the project you serve. All file output goes there. If your working directory is `/Users/samotage/0_robot`, write to `/Users/samotage/0_robot/docs/morning-briefings/`. Never write files to `otl_support`, `.claude`, or any directory outside the project root.

If `--format json` is used, use `.json` extension instead of `.md`.

If the file already exists (e.g. re-running the briefing the same day), overwrite it with the fresh results.

---

## Execution Notes

- **Speed matters.** Maximise parallel tool calls. Don't wait for one search to finish before starting the next.
- **Use WebFetch strategically.** WebSearch casts the net. WebFetch goes deep on the best catches. Don't WebFetch everything — it's slower.
- **Today's date context.** Always include the current date in the briefing header. Use it to assess recency of results.
- **Repeat findings.** If the same item appears across multiple searches, that's a signal of importance — mention it once, in the most relevant section, but note that it's generating cross-category buzz.
- **Be Ferret about it.** Hunt for signal. Get excited when you find something good. Be honest when there's nothing. Don't oversell weak findings.
