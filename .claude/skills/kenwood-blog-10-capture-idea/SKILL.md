---
name: kenwood-blog-10-capture-idea
description: "Pipeline step 1/6. Quick-capture a raw blog post idea into Kenwood. Pit stop, not a workshop — get the spark down and get out."
---

# Skill: Capture Idea

Quick-capture a raw idea into Kenwood so it's ready for later ideation.  This is a pit stop, not a workshop.  Get the spark down, seed the body with enough context to pick it up cold later, and get out of the way.

**Trigger:** User says "capture an idea", "new idea for the blog", "I had a thought about...", or begins describing a raw idea they want to save.

---

## Hard constraints

These are non-negotiable.  Violating any one means the skill has failed.

1. **Capture is lossy on purpose.**  Save the spark, not the bonfire.  The seed section is 1-3 sentences of the core thought.  If you are about to paste more than a short paragraph into the seed, STOP -- you are drafting, not capturing.
2. **Never create content.**  Do not write outlines, sections, hooks, kickers, talking points, or structured content of any kind.  That is the ideation skill's job.
3. **4 tool calls maximum.**  If you have burned 4 tool calls and haven't finished, something has gone wrong.  Stop, report what you have, and let the user decide next steps.
4. **Do not search for files.**  The CLI returns the file path.  Parse it from the JSON response.  Never glob, grep, or guess file locations.

---

## Scope gate (check BEFORE doing anything else)

Read the trigger message and assess the input:

| Input type | What it looks like | What to do |
|---|---|---|
| **Raw idea** | A sentence or two.  An observation, question, or claim.  No structure. | Proceed with capture. |
| **Developed idea** | Has sections, an outline, talking points, tone notes, a hook, or multiple structured paragraphs. | This exceeds capture scope.  See below. |

**When input is over-developed:**

1. Extract the core thought only -- one or two sentences that capture the central observation or claim
2. Tell the user: "That's more than a raw idea -- looks like you've already done ideation-level work.  I'll capture the core thought.  When you're ready to develop it, run `/kenwood-blog-20-ideate-post` and the outline you've already got can feed into the workshop."
3. Capture the core thought as the seed (not the full outline)
4. Do NOT paste structured content into the seed section

---

## References

- **Ideation skill:** `.claude/skills/kenwood-blog-20-ideate-post/SKILL.md` -- the downstream skill that turns a captured idea into a blog post draft
- **Writing rules:** `.claude/rules/writing.md` -- editorial rules (relevant when drafting the working title)
- **Ideas directory:** `ideas/` (configured in `config.yaml` under `ideas.directory`)
- **CLI help:** Read `docs/help/cli-reference/cli-kenwood.md` if you need to verify option syntax
- **MC surfacing:** `.claude/rules/mc-surfacing.md` — when and how to surface entities in Mission Control

---

## Phase 1: Receive and infer

**Goal:** Extract as much as possible from the trigger message before asking anything.

Parse the trigger message for:

| Signal | What to extract |
|--------|----------------|
| **Context** | Venture and project slugs.  "idea for my otageLabs blog" = venture `otagelabs`, project `otage-labs-blog`.  "idea for Kenwood" = venture `otagelabs`, project `kenwood`. |
| **Core thought** | What the idea is about.  The central observation, claim, or question. |
| **Why / why now** | Why it matters or why it's timely.  May not be present -- that's fine. |
| **Source material** | A link, article title, conversation reference, or nothing. |

**Source type inference -- never ask, always infer:**

| On-ramp | Source type |
|---------|------------|
| User is in conversation, describing a thought | `human_ideation` |
| Agent is processing trends and generating ideas | `trend_driven` |
| Agent is self-initiating from reflection or analysis | `agent_capture` |

---

## Phase 2: Enrich (conditional)

**Goal:** Ask only what's missing.  Skip what's already known from the trigger.

**Questions to ask (only if the answer isn't already in the trigger):**

1. **Core thought** (if missing): "What's the idea?"
2. **Why / why now** (if missing): "Why does this matter, or why now?"
3. **Source material** (if missing): "Any link or source that sparked this, or just a thought?"
   - "Just a thought" is a valid answer.  Accept it and move on.

**Context resolution (if venture/project can't be inferred):**
- Ask once: "Which venture and project is this for?"
- Do not ask separately for venture and project -- one question.

**Best case:** 0 questions (everything was in the trigger).
**Worst case:** 3 questions + context.

---

## Phase 3: Capture

**Goal:** Create the idea in Kenwood and seed the body.

### Step 1: Draft a working title

From the inputs, draft a short working title.  This is a label for scanning a list, not a headline.  Keep it plain and descriptive.

### Step 2: Create the idea with body

Build the body content first, then pass it inline via `--body`:

```bash
cli-kenwood ideas capture --title "<working title>" --venture <slug> \
  --project <slug> --source <source_type> \
  --body "## Source Material

<Link URL, article title, or 'Direct observation -- no external source.'>

## Seed

<Core thought in 1-3 sentences.  Preserve the user's phrasing.  Do not polish, expand, or rewrite.>"
```

Parse the JSON response.  It returns `idea.id`, `idea.slug`, and `idea.file_path`.  Use these directly -- do not search for the file.

**MC:** After creating the idea, surface it: `cli-kenwood mc focus --entity-type idea --entity-id <id> --navigate`

**If the CLI returns an error** (e.g., project not found), run `flask project list --venture <slug> --json` to find the correct project slug, then retry.

---

## Phase 4: Confirm

**Goal:** Present what was created.  Offer a title tweak.  Get out of the way.

Report:

```
Idea captured.

  ID:       #{id}
  Title:    {working title}
  Venture:  {venture} / {project}
  File:     {file_path from JSON response}

Title good, or want to change it?
```

- If the user wants to change the title, update it via `flask idea sync` after editing the frontmatter, or use the MC edit endpoint.
- If no change requested, done.

---

## Exit condition

The idea exists in Kenwood with:
- Status: `idea`
- Body seeded with `## Source Material` and `## Seed` (seed is 1-3 sentences max)
- Working title (user-reviewed)
- Ready for `/kenwood-blog-20-ideate-post` whenever the time comes

---

## DO NOT

- Write outlines, section plans, hooks, kickers, or structured content
- Expand the user's idea into something more developed than what they said
- Search for files -- the CLI response has the path
- Guess project slugs -- verify via CLI if unsure
- Exceed 4 tool calls for the entire capture
- Skip the scope gate -- always check input complexity first
