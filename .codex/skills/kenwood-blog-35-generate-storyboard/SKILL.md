---
name: kenwood-blog-35-generate-storyboard
description: Pipeline step 3.5/6. Operator-driven. Create and generate a visual storyboard
  for an approved content piece. Author markdown, validate, generate images, review.
  Runs between approval (step 30) and export (step 40).
license: MIT
metadata:
  author: otagelabs
  version: '1.0'
  short-description: Pipeline step 3.
---

Create a visual storyboard for a content piece.  This skill covers the full lifecycle: create the storyboard record, author the markdown file, validate, generate images, and review results.

Storyboards are optional.  Not every content piece needs one.  The operator decides.  When a storyboard exists, the export skill (step 40) automatically picks up the images and wires them into the blog post frontmatter.

**Trigger:** User says "create a storyboard for content piece #N", "generate storyboard images", "this post needs visuals", "storyboard for #N", or references creating visual assets for a content piece.

---

## References

- **Storyboard help:** `docs/help/content/storyboards.md` -- full format spec, CLI reference, gotchas
- **Storyboard template:** `content/storyboards/template.md` -- skeleton with authoring guidance
- **CLI help:** Read `docs/help/cli-reference/cli-kenwood.md` for exact flags
- **MC surfacing:** `.claude/rules/mc-surfacing.md` -- when and how to surface entities

---

## Input

A content piece ID (integer).

**Resolution order:**
1. If the user provides an ID explicitly, use it
2. If the user provides a title or partial reference, search via `cli-kenwood content list --search <query>` and match on title or slug.  Ask for disambiguation if multiple matches
3. If the conversation has been working on a specific content piece, use it
4. If the ID cannot be determined, ask: "Which content piece needs a storyboard?  Give me the ID, or I can list approved pieces."
5. If the user asks to see options, run `cli-kenwood content list --status approved --limit 10`

**Do not guess.**

---

## Phase 1: Check preconditions

Run in parallel:

```bash
cli-kenwood content get <ID>
cli-kenwood storyboards list --content-id <ID>
```

**Content piece check:**

| Status | Action |
|---|---|
| `approved` or later (`exported`, `scheduled`, `published`) | Proceed |
| `draft` | "Content piece #{id} is still in draft.  Approve it first (`/kenwood-blog-30-approve-content`) before creating a storyboard."  Stop. |

**Storyboard check:**

| Result | Action |
|---|---|
| No storyboard exists | Proceed to Phase 2 |
| Storyboard exists, status `drafting` | Skip to Phase 3 (author/edit the markdown) |
| Storyboard exists, status `complete` or `partial` | Tell the user: "Content piece #{id} already has a storyboard (status: {status}).  Want to regenerate specific frames, or start fresh?"  Wait for direction. |

**MC:** Surface the content piece: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID> --navigate`

---

## Phase 2: Create the storyboard record

```bash
cli-kenwood storyboards create --content-id <ID> --title "<content piece title>"
```

Note the storyboard ID from the output.  You need it for generation later.

**MC:** Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID>`

---

## Phase 3: Author the storyboard markdown

The markdown file is the single source of truth for all frame prompts.  It lives at:
```
content/storyboards/{content-piece-slug}.md
```

Get the slug from the `cli-kenwood content get` output.

### If the file does not exist

Copy the template and adapt it:

```bash
cp content/storyboards/template.md content/storyboards/{slug}.md
```

Then edit the file with these sections:

1. **Title (h1):** The content piece title
2. **Settings (h2):** `aspect_ratio: 16:9` and `model: google/gemini-2.5-flash-image` (defaults; adjust if the operator specifies)
3. **Style guide (h2):** Global art direction that applies to every frame.  Describe the visual style, colour palette, character designs, environment.  Be specific and visual.
4. **Frames (h2 each):** `## Frame NN - Title` with a scene description under each.  Zero-pad frame numbers (`01`, `02`, etc.).  Use a standard hyphen between number and title, not an em dash.
5. **Production notes (h2):** Sequencing and consistency guidance for the generator.

**Narrative structure:** Apply the four-beat arc (introduction, incident, climax, resolution).  See the "Structuring the narrative" section in `docs/help/content/storyboards.md`.

**Frame count:** Read the content piece body to determine the narrative beats.  Typical range is 8-20 frames.  Each frame should represent a distinct visual moment.

### If the file already exists

Read it, understand what's there, and edit as needed.  The operator may want to add frames, revise prompts, or adjust the style guide.

### Present to the operator

After authoring, show the operator:
- Total frame count
- The four-beat arc mapping (which frames cover introduction/incident/climax/resolution)
- Any style guide decisions that need confirmation

Wait for the operator to approve the markdown before generating.

---

## Phase 4: Validate

Run validation before committing to image generation:

```bash
cli-kenwood storyboards generate <ID> --validate
```

This parses the markdown and checks for:
- Required sections (style guide, production notes, at least one frame)
- Non-standard dashes in frame headings
- Resolved settings (model, aspect ratio)

If validation reports errors, fix the markdown and re-validate.  Warnings are informational; report them to the operator but don't block.

---

## Phase 5: Generate images

```bash
cli-kenwood storyboards generate <ID> --wait
```

This runs sequentially, generating one frame at a time via the OpenRouter API.  Frame 1 generates from text alone; subsequent frames receive the previous frame as a visual reference for consistency.

Generation takes time.  After kicking it off, report:

```
Storyboard generation started for content piece #{id}.
{N} frames queued.  Images will appear in content/storyboards/{slug}/ as they complete.
```

### Check progress

```bash
cli-kenwood storyboards status <ID>
```

Reports: total, complete, failed, pending, generating.

### Handle failures

If frames fail:
- Check `cli-kenwood storyboards status <ID>` for which frames failed
- Regenerate only the failed frames: `cli-kenwood storyboards generate <ID> --frames NN,NN`
- If failures persist, report to the operator with the error details

---

## Phase 6: Review

After generation completes, the MC gallery updates automatically (filesystem-driven, no sync needed).

**MC:** Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <ID>`

Report to the operator:

```
Storyboard complete for content piece #{id}.

  Frames:     {complete}/{total} generated
  Images:     content/storyboards/{slug}/
  Gallery:    visible in MC content detail view

Review the frames in the gallery.  If any frames need rework, tell me which ones and what to change.
```

If the operator wants to regenerate specific frames:
```bash
cli-kenwood storyboards generate <ID> --frames NN,NN
```

---

## Sync (edge case)

If images exist on disk but aren't reflected in the database (e.g., generated outside the CLI):

```bash
cli-kenwood storyboards sync <ID>
```

This is rarely needed.  The MC gallery reads from the filesystem directly.  Sync is for aligning the database records with what's on disk.

---

## DO NOT

- Generate images without the operator approving the markdown first
- Skip validation before generation
- Modify the content piece body -- this skill creates visual assets, not written content
- Assume every content piece needs a storyboard -- the operator decides
- Block the export pipeline -- storyboards are optional; export works with or without them
