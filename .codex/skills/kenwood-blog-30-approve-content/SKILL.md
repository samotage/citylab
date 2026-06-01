---
name: kenwood-blog-30-approve-content
description: Pipeline step 3/6. Generate editorial metadata (summary, meta description,
  tags) for a content piece, then transition to approved. Last operator gate before
  the automatic publishing pipeline.
metadata:
  short-description: Pipeline step 3/6.
---

# Skill: Approve Content

Generate the editorial metadata for a content piece — summary, meta description, and tags — then transition it to `approved`.  This is where intelligence earns its keep: the agent reads the content, drafts metadata that's editorially sound, and presents it for the operator to review as a batch alongside the content.

After approval, the automatic publishing pipeline runs: export → SEO → deploy.  No further operator gates until the content is live.

**Trigger:** User says "approve this content piece", "get this ready for approval", "move to approved", or references approving a content piece by ID.

---

## Hard constraints

1. **The agent generates metadata autonomously.**  Draft summary, meta description, and tags based on the content body.  Present all three to the operator as a batch for review.  The operator reviews the content piece as a whole — body plus metadata — and approves or requests changes.  There are no separate approval gates for individual metadata fields.
2. **Writing rules apply.**  All drafted text must follow `.claude/rules/writing.md` — voice, banned words, specificity, double spacing after full stops.
3. **Do not touch the body.**  This skill edits metadata fields only (summary, meta_description, tags).  The content body is finished work from the ideation skill.  Leave it alone.

---

## References

- **Writing rules:** `.claude/rules/writing.md` — editorial rules, banned words, LLM pattern avoidance
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's writing voice (same voice applies to metadata)
- **Lifecycle definitions:** `src/kenwood/services/lifecycle_definitions.py` — preconditions for `draft → approved`
- **CLI help:** Read `docs/help/cli-reference/cli-kenwood.md`
- **MC surfacing:** `.claude/rules/mc-surfacing.md` — when and how to surface entities in Mission Control

---

## Input

A content piece ID (integer).

**Resolution order:**
1. If the user provides an ID explicitly, use it
2. If the user provides a website file path (e.g., `content/blog/my-post.md`), derive the slug from the filename and look up via `cli-kenwood content list --search <slug>`
3. If the user provides a title or partial reference, search via `cli-kenwood content list --search <query>` and match on title or slug.  Ask for disambiguation if multiple matches are found.
4. If the conversation has been working on a specific content piece and the ID is unambiguous, use it
5. If the ID cannot be determined, ask: "Which content piece?  Give me the ID, or I can list pieces in draft."
6. If the user asks to see options, run `cli-kenwood content list --status draft --limit 10` and present the results for selection

**Do not guess.**

---

## Phase 1: Read and assess

**Goal:** Understand the content and determine what metadata work is needed.

Run in parallel:

```bash
cli-kenwood content get <ID>
cli-kenwood content body <ID>
```

From the JSON response, extract: `id`, `title`, `status`, `summary`, `meta_description`, `tags`.

**Status check:**

| Current status | Action |
|---|---|
| `draft` | Proceed — will transition directly to `approved` after metadata generation |
| `approved` or later | Tell the user: "Content piece #{id} is already approved (status: {status}).  Nothing to do."  Stop. |

**MC:** After loading the content piece, surface it: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID> --navigate`

Read the content body.  Understand what the piece is about — you need this context to draft good metadata.

---

## Phase 2: Generate metadata

**Goal:** Draft summary, meta description, and tags as a batch, then present for review.

Read the content body (already loaded in Phase 1) and generate all three metadata fields.

### Summary

- 1-3 sentences.  This is a teaser, not an abstract.
- Capture the core claim or observation of the post.
- Use Sam's voice — direct, conversational, specific.
- Make a promise: tell the reader what they'll get if they click.
- No banned words.  No LLM patterns.  No corporate fluff.
- Double space after sentence-ending full stops.

### Meta description

- Maximum 160 characters (hard limit — the precondition gate enforces this).
- Distil the summary into a search-optimised snippet.
- Front-load the value proposition — search engines truncate from the right.
- Use Sam's voice — not generic SEO copy.
- No banned words.  No LLM patterns.

### Tags

- 3-6 tags.  Enough for discoverability, not so many they're meaningless.
- Use lowercase, hyphenated slugs (e.g., `ai-agents`, `cli-design`, `content-pipeline`).
- Mix of topic tags (what it's about) and category tags (what kind of post it is).
- Tags should be useful for filtering on a blog — think "what would a reader click to see more of?"

### Present to the operator

Present all three fields together:

```
Content piece #{id}: {title}

Draft metadata:

  Summary:
    "{summary text}"

  Meta description ({N} chars):
    "{meta description text}"

  Tags: {comma-separated tags}

Review the metadata alongside the content.  If everything looks good, I'll write the fields and move to approved.  The publishing pipeline (export → SEO → deploy) will run automatically after approval.

Any changes needed?
```

**If the operator requests changes:** Revise the specific fields they flag, present the updated batch, and ask again.

**If the operator approves** ("good", "fine", "yes", "ship it", "approve it"): Write all fields immediately:

```bash
cli-kenwood content update <ID> --summary "<summary>"
cli-kenwood content update <ID> --meta-description "<meta description>"
cli-kenwood content update <ID> --tags "<comma-separated tags>"
```

**MC:** After writing all metadata, surface it: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID>`

---

## Phase 3: Transition

**Goal:** Move the content piece directly from `draft` to `approved`.

### Step 1: Transition to `approved`

```bash
cli-kenwood content transition <ID> --action approve
```

**MC:** After the approval transition, surface it: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID>`

If the transition fails (precondition gate), parse the error.  Report which fields still fail and return to Phase 2 to fix them.  This should not happen if Phase 2 was completed correctly — but if it does, fix it rather than telling the user to fix it.

### Step 2: Confirm

```
Content piece #{id} approved.

  Title:            {title}
  Status:           approved
  Summary:          "{summary}"
  Meta description:  "{meta_description}" ({N} chars)
  Tags:             {tags}

Publishing pipeline will run automatically: export → SEO → deploy.

If this post needs visual storyboard images, now is the time:
  /kenwood-blog-35-generate-storyboard (optional — skipping goes straight to export)
```

---

## DO NOT

- Write or modify the content body — metadata fields only
- Fire the transition before the operator has reviewed the metadata batch
- Use generic SEO language — apply Sam's voice and the writing rules
- Skip presenting the metadata — even if fields were already populated, show them for review
- Prompt for per-field approval — present all metadata as a batch
- Reference manual invocation of steps 40, 50, or 60 — the pipeline runs automatically after approval
