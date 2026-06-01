---
name: kenwood-blog-20-ideate-post
description: Pipeline step 2/6. Transform a captured idea into a crafted blog post
  draft through a 5-phase conversational workshop. Produces a ContentPiece in draft
  status.
metadata:
  short-description: Pipeline step 2/6.
---

# Skill: Ideate Blog Post

Transform a raw idea into a crafted blog post draft through a 5-phase conversational process.  The idea body accumulates working notes (provenance); the ContentPiece receives only the finished draft (output).

**Trigger:** User says "ideate this as a blog post" or similar, with an idea selected/referenced.

---

## References

- **Voice:** `voice.md` (co-located) -- Sam's conversational writing voice
- **Formats:** `post-formats.md` (co-located) -- 5 blog post format templates with selection guide
- **Writing rules:** `.claude/rules/writing.md` -- Editorial rules, banned words, LLM pattern avoidance
- **MC surfacing:** `.claude/rules/mc-surfacing.md` -- when and how to surface entities in Mission Control

---

## Prerequisites

- An idea exists in Kenwood with status `idea` (not promoted or archived)
- The idea has a markdown file with at least some body content (raw notes, a link, a thought)

To read the idea:
```bash
cli-kenwood ideas body <id>
```

To get idea metadata:
```bash
cli-kenwood ideas get <id>
```

---

## Phase 1: Absorb

**Goal:** Understand the raw material.  Produce a concise summary.

1. Read the idea body using `cli-kenwood ideas body <id>`

**MC:** After reading the idea, surface it: `cli-kenwood mc focus --entity-type idea --entity-id <id> --navigate`
2. If the idea contains links, read the linked content to understand the source material
3. Produce a short, plain-language summary (2-4 sentences): what is the source material about, and what is the core idea?
4. Present the summary to Sam for confirmation
5. Write the summary to the idea body under `## Summary`

**Writing to the idea body:**

When writing to the idea body, preserve all existing content.  If the idea has body content that isn't already under a `## Source Material` heading, move that existing content under `## Source Material` first, then add the new section below.

Use the MC edit-body endpoint or the idea file directly:
```
POST /mc/idea/<id>/edit-body
  body=<updated markdown body>
```

**Section format:**
```markdown
## Source Material
[Original body content preserved here]

## Summary
[2-4 sentence plain-language summary of the source material and core idea]
```

---

## Phase 2: Find the angle

**Goal:** Identify what makes this worth writing about from Sam's perspective.

1. Review the summary from Phase 1
2. Ask Sam: "What's your personal connection to this?  Have you built something related, hit this problem, or seen this play out with a client?"
3. Based on Sam's response, produce a one-paragraph angle statement:
   - Who is this for?
   - What is the original thought Sam brings?
   - Why does it matter right now?
4. Present the angle to Sam for confirmation
5. Write the angle to the idea body under `## Angle`

**Section format:**
```markdown
## Angle
[One-paragraph angle statement: who it's for, what original thought Sam brings, why it matters now]
```

---

## Phase 3: Shape the outline

**Goal:** Recommend a format and propose a post structure.

1. Read `post-formats.md` (co-located)
2. Based on the raw material type and the angle, recommend a format from the format selection guide:
   - Metaphor illuminating a tech trend -> Deep take
   - Single interesting observation with data -> Short take
   - Something built or broken -> Builder's log
   - Disagreement with industry consensus -> Counterpoint
   - Chart or statistic being misread -> Data piece
3. Explain why this format fits (one sentence)
4. Propose a post structure:
   - Working title
   - 3-5 sections with working headings and one-sentence descriptions
   - Energy sources (where Sam's voice/experience is strongest)
   - Estimated word count based on the format
   - Tone note (e.g., "dry humor in section 2, vulnerable in the closer")
5. Present the outline to Sam and wait for feedback
6. Write the outline to the idea body under `## Outline`

**Section format:**
```markdown
## Outline
**Format:** [format name]
**Working title:** [title]
**Estimated length:** [N] words

1. [Section heading] -- [one-sentence description] [energy source]
2. [Section heading] -- [one-sentence description] [energy source]
3. [Section heading] -- [one-sentence description] [energy source]
...

**Tone note:** [guidance for the draft]
```

---

## Phase 4: Iterate

**Goal:** Refine the outline based on Sam's feedback until he says "go."

1. Wait for Sam's feedback on the outline
2. Sam may: add sections, cut sections, redirect the angle, sharpen headings, change the format, adjust the tone
3. Rework the outline based on feedback
4. Update the `## Outline` section of the idea body with each iteration
5. Present the updated outline and wait for the next round of feedback
6. **Repeat until Sam gives an explicit instruction to write** ("go," "write it," "draft it," "let's go," or similar)

Do NOT proceed to Phase 5 until Sam explicitly says to write.  Approval of the outline ("looks good," "I like it") is not the same as an instruction to draft.  If unclear, ask: "Ready for me to write the draft?"

### Phase 4 exit — lock the outline

Once Sam gives the explicit instruction to write, post a single-line transition announcement before anything else:

> Outline locked.  Entering Phase 5 — drafting now.  Format: `{format}`.  Target: `{N}` words.  Opener strategy: `{one-phrase}`.

This is the handoff signal to Sam.  It marks the boundary between conversational iteration and silent generation.  No further outline changes after this line — if Sam wants a change, return to Phase 4 and re-lock with a new transition announcement.

After posting the transition, run the gate check below and move to Phase 5.  Do not narrate the draft as you write it; Phase 5 is silent work until the completion report.

---

## Gate check (before Phase 5)

Before proceeding to Phase 5, verify:

- [ ] `## Summary` section is present and non-empty
- [ ] `## Angle` section is present and non-empty
- [ ] `## Outline` section is present and non-empty
- [ ] Sam has given an explicit instruction to write the draft

If any check fails, report which sections are missing or incomplete and return to the appropriate phase.

---

## Phase 5: Draft and promote

**Goal:** Generate the full draft and promote the idea to a ContentPiece.

### Step 1: Write the draft

Generate the full blog post draft following:
- The agreed outline from `## Outline`
- Sam's voice from `voice.md` (co-located)
- Writing rules from `.claude/rules/writing.md`
- The selected post format structure from `post-formats.md` (co-located)

**Before writing the opener,** check the last two published content pieces to avoid stacking the same opener pattern.  Use `cli-kenwood content list --status published --limit 2` to check.

### Step 2: Write draft to temporary file

Write the completed draft to a temporary file:
```bash
echo '<draft content>' > /tmp/kenwood-draft-<idea-id>.md
```

### Step 3: Promote with draft file

Promote the idea using the draft file as the ContentPiece body:
```bash
cli-kenwood ideas promote <id> --draft-file /tmp/kenwood-draft-<idea-id>.md
```

This creates a ContentPiece in `draft` status with:
- The draft content as the ContentPiece body (NOT the idea body)
- `source_idea_id` linking back to the originating idea
- The idea status set to `promoted`

The idea body retains all working notes (Source Material, Summary, Angle, Outline).

**MC surfacing is automatic.**  `cli-kenwood ideas promote` emits a workspace focus event targeting the new ContentPiece via the platform's `emit_mutation_event` path — MC will auto-navigate to it the moment the command returns.  Do NOT add a follow-up `cli-kenwood mc focus` call; it is redundant and pollutes the pipeline.  If the workspace does not surface the new piece, the failure is downstream of the skill (event bus, broadcaster, or MC client) — report it, do not paper over it with a manual focus call.

### Step 4: Clean up and report

1. Remove the temporary draft file
2. Post a single completion report to Sam:
   - ContentPiece ID and title
   - Word count
   - Format used
   - Confirmation that MC has surfaced the new piece
   - Reminder that the idea retains all ideation work

Do not narrate the draft body in chat — MC now shows it.  The completion report is the closing signal of Phase 5 and the skill.

---

## Idea body structure convention

The ideation process progressively builds these sections in the idea body:

```markdown
## Source Material
[Raw input -- links, quotes, observations, the original seed.  Pre-existing content stays here.]

## Summary
[Phase 1 output -- plain-language summary of source material and core idea]

## Angle
[Phase 2 output -- one-paragraph angle statement: who it's for, original thought, why it matters]

## Outline
[Phase 3/4 output -- post format, sections with headings and descriptions.  Updated through iterations.]

## Working Draft
[Optional -- Phase 4 scratch work, partial drafts, abandoned angles.  Not always present.]
```

These sections are a convention enforced by this skill, not by database schema.  Existing idea bodies (pre-ideation or manually written) are unaffected.  When the skill encounters an idea with existing body content, it preserves that content under `## Source Material` and adds new sections below.
