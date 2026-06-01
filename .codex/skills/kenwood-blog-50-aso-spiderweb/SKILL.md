---
name: kenwood-blog-50-aso-spiderweb
description: Pipeline step 5/6. Automatic — runs after export. Weave a newly exported
  post into the blog corpus with bidirectional cross-links and ASO checks. Non-destructive
  changes applied autonomously. Runs on the website, not Kenwood.
metadata:
  short-description: Pipeline step 5/6.
---

# Skill: ASO Spiderweb

Weave a newly exported blog post into the existing blog corpus.  Add bidirectional cross-links — inline contextual links in body text and `related_posts` entries in frontmatter — and run lightweight ASO checks before publish.

This is where the agent reads the full blog, understands topical relationships, and applies non-destructive link insertions and entity fixes autonomously.  Destructive changes (content removal, significant structural alterations) are flagged to the operator for approval.

**This skill runs automatically as part of the publishing pipeline after export.**  Non-destructive changes are applied without operator approval.  If invoked manually, it behaves identically.

**Trigger:** Automatic after export transition, or user says "spiderweb this post", "cross-link the new post", "run ASO", or references preparing an exported post for publish.

---

## Hard constraints

1. **Non-destructive changes are applied autonomously.  Destructive changes require operator approval.**  Cross-link insertions, entity consistency fixes, and `related_posts` entries are non-destructive — apply them without individual approval.  Content removal, significant structural alterations, or rewrites are destructive — flag them to the operator and pause the pipeline until resolved.
2. **Do not rewrite content.**  Propose link insertions that fit the existing prose.  Do not rephrase, restructure, or "improve" sentences to accommodate links.  If a link can't be inserted naturally, don't force it.
3. **Do not touch unpublished posts.**  Only scan and modify posts where `published: true` in frontmatter.
4. **Writing rules apply.**  All anchor text must follow `.claude/rules/writing.md` — no banned words, no LLM patterns, Sam's voice.
5. **Quality over quantity.**  Expect 2-5 outbound links from the new post and 1-3 backlinks into existing posts.  Forcing links where there's no genuine semantic relationship hurts more than it helps.

---

## Scaling note

This skill reads the full blog corpus on every run.  At 13 posts (~2026-03), this is fast and fits comfortably in context.  **At ~50 posts, the full-corpus scan may become unmanageable.**  When the corpus approaches that size, the scan step (Phase 2) will need optimisation — tag-based pre-filtering, embedding similarity, or similar.  That's a future problem.  The skill is designed so the corpus scan is isolated in one phase, making it replaceable without rewriting the rest.

---

## References

- **Writing rules:** `.claude/rules/writing.md` — editorial rules, banned words, voice
- **Website blog directory:** `/Users/samotage/dev/otagelabs/v0-otage-labs-website-design/content/blog/`
- **Link format:** `/blog/{slug}` (relative paths, no domain)
- **Entity names:** Kenwood, Claude Headspace, May Belle, RAGlue, otageLabs (capitalisation matters for consistency)
- **MC surfacing:** `.claude/rules/mc-surfacing.md` — when and how to surface entities in Mission Control

---

## Input

The slug of the newly exported blog post (e.g., `2026-03-14-robot-meetings-need-minutes-too`) and the corresponding Kenwood content piece ID.

**Resolution order:**
1. If the user provides a content piece ID explicitly (e.g., "content piece #42"), use it to look up the slug via `cli-kenwood content get <ID>` from the Kenwood project root
2. If the user provides a website file path (e.g., `content/blog/2026-03-14-my-post.md`), derive the slug from the filename and look up the content piece via `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content list --search <slug>`
3. If the user provides a title or partial reference, search via `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content list --search <query>` and match on title or slug.  Ask for disambiguation if multiple matches are found.
4. If the conversation has just run the export skill, the slug and ID are known from that context — use them
5. If ambiguous, ask: "Which post?  Give me the slug or content piece ID, or I can list recent exports."

**Both slug and ID are needed.**  The slug is used for all website operations.  The ID is needed for the Kenwood status transition in Phase 7.

---

## Phase 1: Read the new post

Read the newly exported post from the blog directory:

```
{blog_dir}/{slug}.md
```

Extract:
- **Frontmatter:** title, slug, date, tags, summary, meta_description, existing `related_posts` (if any)
- **Body:** full markdown content
- **Key topics:** the central themes, claims, entities, and product references in the post

---

## Phase 2: Scan the corpus

Read all other published posts in the blog directory.  Filter to `published: true` only.

For each post, extract:
- Frontmatter (title, slug, tags, summary)
- Body content
- Existing `related_posts` entries (to avoid duplicate suggestions)

**Skip:**
- The new post itself
- Posts with `published: false`

---

## Phase 3: Cross-link analysis

Find semantic connections between the new post and the existing corpus.  Look for:

- **Shared tags** — posts covering the same topics
- **Shared entities** — references to the same products, tools, or concepts (Kenwood, Claude Headspace, etc.)
- **Shared themes** — complementary arguments, follow-on thoughts, contrasting positions
- **Direct references** — where one post's content directly relates to a specific passage in another

**Generate changes in both directions:**

### Outbound (new post → existing posts)

For each link:
- Identify the specific paragraph in the new post where the link fits
- Determine the anchor text and target slug
- Confirm the link fits naturally in the existing prose

### Inbound (existing posts → new post)

For each link:
- Identify the specific paragraph in the existing post where the link fits
- Determine anchor text that links to the new post's slug
- Confirm the link fits naturally in the existing prose

**Check for existing connections:**
- If the new post already links to a target post (inline link in body), don't add it again
- If an existing post already has the new post in its `related_posts` frontmatter, don't add it again

---

## Phase 4: ASO checks

Run these checks alongside the cross-link analysis.

### Answer-forward structure

Read the new post for paragraphs that meander without landing a concrete, citable statement.  AI systems extracting content for citations favour definitive claims with evidence.  Flag any section that:
- Poses a question but never answers it
- Describes a situation without drawing a conclusion
- Uses excessive hedging where a direct statement would be stronger

**These are flagged as destructive (structural) changes** — they require operator approval to address because fixing them means rewriting content.

### Entity consistency

Check that product and project names are referenced consistently across the new post and the existing corpus:
- **Kenwood** (not "kenwood" or "the Kenwood system")
- **Claude Headspace** (not "Headspace" alone or "Claude headspace")
- **May Belle** (not "Maybelle" or "may belle")
- **RAGlue** (not "Raglue" or "rag-lue")
- **otageLabs** (not "OtageLabs" or "Otage Labs")

**Entity consistency fixes in the new post are non-destructive** — apply them autonomously.

### Meta description validation

Check the new post's `meta_description`:
- Present and non-empty
- 160 characters or fewer
- Front-loads the value proposition (not a generic description)
- Matches the post's actual content

If issues found, flag them.  **Do not fix — the approve skill owns meta_description.**

---

## Phase 5: Apply non-destructive changes

Apply all non-destructive changes immediately without operator approval:

1. **Inline cross-links:** Edit the target file's body text — insert the markdown link at the determined location
2. **Frontmatter `related_posts`:** Add entries to the target file's frontmatter.  If `related_posts` doesn't exist yet, create it.
3. **Entity consistency fixes:** Apply corrections to the new post.

**Frontmatter format:**

```yaml
related_posts:
  - slug: target-post-slug
    context: "one-sentence description of why these posts are related"
```

Apply changes file by file.

---

## Phase 6: Report changes and flag destructive items

Present a summary of all changes applied and any destructive items flagged:

```
SEO optimisation complete.

  Non-destructive changes applied:
    Outbound links:   {N} added (to {list of target slugs})
    Inbound links:    {N} added (from {list of source slugs})
    Entity fixes:     {N} applied
    Files modified:   {list of filenames}

  {If destructive items found:}
  Destructive changes requiring approval:
    1. Answer-forward: {section heading} — {what's missing}
    ...

  {If no destructive items:}
  No destructive changes detected.

  Meta description: {ok / issues found}
```

**If destructive changes are flagged:** Present each one to the operator for approval.  The pipeline pauses until all flagged items are resolved (approved and applied, or rejected and skipped).

**If no destructive changes:** Proceed immediately to Phase 7.

---

## Phase 7: Status transition

**Goal:** Move the content piece to `aeo_optimised` in Kenwood.

Run from any directory — the `cd` handles the path:

```bash
cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content transition <ID> --action optimise
```

If the transition succeeds:

**MC:** Surface the updated entity:

```bash
cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc focus --entity-type content_piece --entity-id <ID>
```

**MC:** Notify the operator:

```bash
cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc notify --message "Content piece '{title}' SEO optimised — {N} cross-links added"
```

If the transition fails, **halt the pipeline**.  Notify the operator.

```
Pipeline halted: Status transition to 'aeo_optimised' failed: {error message}
The cross-link changes are applied, but the status could not be updated.
```

---

## Pipeline failure handling (FR8)

If any step in this skill fails:
- **Halt the pipeline immediately.**  Do not proceed to the next step.
- **Notify the operator** via flash banner: `cli-kenwood mc notify --message "SEO optimisation failed: {reason}.  Content piece remains at exported."`
- **Do not retry automatically.**  The operator decides whether to retry or investigate.

---

## DO NOT

- Rewrite post content to accommodate links — the link fits the prose, not the other way around
- Force links where there's no genuine semantic relationship
- Apply destructive changes (content removal, structural rewrites) without operator approval
- Touch unpublished posts
- Fix meta_description issues directly — route to the approve skill
- Modify site templates, components, or configuration
- Change tags, summary, or title — those are the approve skill's domain
- Suggest links to/from the same post (self-links)
- Wait for operator approval on non-destructive changes (cross-links, entity fixes)
- Reference manual invocation of subsequent pipeline skills — the pipeline continues automatically
