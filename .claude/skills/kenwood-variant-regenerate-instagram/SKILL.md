---
name: regenerate-instagram-variant
description: "Regenerate an Instagram caption variant with storyboard image selection."
---

# Skill: Regenerate Instagram Variant

Regenerate an Instagram caption variant independently of the full orchestration flow.  Instagram is image-first: the skill selects a storyboard image, writes visual direction notes explaining the selection, and generates a caption with hook, short paragraphs, engagement CTA, and 3--5 hashtags.  Publishing is manual -- Sam copies the caption and posts via the Instagram app.

**Trigger:** Skill injection "Regenerate" button on rejected/failed/cancelled Instagram variants, or operator says "regenerate Instagram variant for content piece <id>."

## References

- **Platform constraints:** `../kenwood-variant-generate/constraints/instagram.md` — all Instagram rules, image selection criteria, CTA conventions, and format_metadata schema
- **Shared structure:** `../kenwood-variant-generate/variant-skill-structure.md` — input/output contract, voice self-check gate
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's conversational writing voice (mandatory read before generating)
- **Writing rules:** `.claude/rules/writing.md` — banned words, double spaces, voice rules
- **MC surfacing:** `.claude/rules/mc-surfacing.md` — when and how to surface entities

---

## Phase 1: Read Source

1. Read content piece metadata: `cli-kenwood content get <id>`
2. Read full content body: `cli-kenwood content body <id>`
3. Read the voice reference: `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  This is non-negotiable editorial law.  Internalise Sam's voice markers before generating.
4. Read storyboard images: `cli-kenwood storyboards list --content-id <id>`
5. Check for existing Instagram variants: `cli-kenwood variants list --content-id <id>`
6. Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate`

**Gate:** Content piece must be in `published` status.  If not, report and stop.

If existing Instagram variants exist, note their bodies, format_metadata (especially selected_image), and statuses.  Rejected/failed/cancelled variants inform the image and angle differentiation in Phase 2.

**Storyboard fallback:** If no storyboard exists, use the content piece's featured image.  If no image is available at all, report the absence to Sam and generate the caption anyway.

---

## Phase 2: Generate

1. Read the Instagram constraint file from `../kenwood-variant-generate/constraints/instagram.md`
2. If regenerating after rejection: read the rejected variant's body and format_metadata to understand the previous image selection and caption angle.  Select a different storyboard image (if multiple are available) or a different caption angle.
3. Review storyboard images and select the most appropriate one per selection criteria: visual impact (stops a scroll), relevance (connects to the caption's angle), authenticity (real screenshots and behind-the-scenes outperform polished graphics).
4. Write 1--2 sentences of visual direction notes explaining why this image was chosen.
5. Identify an Instagram-specific caption angle.  Instagram captures a feeling, a moment, or a behind-the-scenes glimpse -- not an argument.  The angle should differ from social platforms.
6. Generate the caption: hook line, 2–3 short paragraphs, CTA (engagement question or profile visit), 3–5 hashtags after a line break.  Count characters — target 800–1,500, hard limit 2,200.
6b. **Mechanical character scan (mandatory before voice gate).**  Scan the variant body for `—` (em dash), `–` (en dash), ` -- ` (double-hyphen), smart quotes (`"` `"` `'` `'`), and `…` (ellipsis char).  Any single hit is an automatic rewrite — these are LLM authorship tells.  Use straight ASCII substitutes (commas/semicolons/sentence breaks for dashes; `"` and `'` for quotes; `...` for ellipsis).  Re-scan after rewriting.  Do NOT proceed to the voice gate until clean.  Full pattern table in `../kenwood-variant-generate/variant-skill-structure.md`.

7. **Voice self-check (7-point gate).**  All must pass before writing:
   1. Captures a specific moment from the source (not a summary of conclusions)?  2. Uses at least one specific detail (tool name, agent name, concrete number)?  3. Includes vulnerability or behind-the-scenes honesty?  4. Closer is natural, not thesis-statement?  5. Contains sentence-length variation?  6. Stays in scene — a moment, a feeling — rather than pivoting to advice or abstract principles?  Compress by capturing a sharper moment, not by abstracting.  7. Every sentence passes the coffee test — would Sam say it over a beer?  8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source?  Inflating or inverting facts is fabrication and an automatic fail.  Any failure means rewrite.
8. Present the caption and selected image to Sam for confirmation.  Wait for approval.
9. Construct `format_metadata` JSON per the constraint file's output specification (char_count, hashtags, selected_image, visual_direction, utm_params, link_in_bio_url).
10. Write the variant:
   ```bash
   cli-kenwood variants create --content-id <id> --platform instagram --variant-type caption --title "Instagram caption" --body "<caption>" --format-metadata '<json>'
   ```
10. Surface variant and refresh content piece:
    ```bash
    cli-kenwood mc focus --entity-type content_variant --entity-id <variant_id>
    cli-kenwood mc focus --entity-type content_piece --entity-id <id>
    ```

---

## Phase 3: Report

1. Report: variant created, character count, hashtag count, selected image path, visual direction notes
2. Remind Sam to review in the variant review UI, then copy caption and post manually to Instagram
3. Note the `link_in_bio_url` that Sam should set as his bio link before posting

---

## Hard Constraints

1. Character count MUST be under 2,200 (Instagram limit).  Target 800--1,500 for effectiveness.
2. Hashtag count MUST be 3--5.  Not more.
3. NO URLs in caption body text.  Links are not clickable in Instagram feed captions.
4. CTA MUST be engagement question or profile visit, never a link click.
5. An image MUST be selected (or absence reported).  Instagram is visual-first.
6. Visual direction notes MUST explain why the image was chosen (1--2 sentences).
7. **Voice is non-negotiable.**  Read `voice.md` before generating.  Apply the 8-point voice self-check gate before writing.  `.claude/rules/writing.md` banned words, double spaces, and LLM pattern avoidance enforced.
8. When regenerating after rejection, MUST select a different storyboard image or use a different caption angle.
9. Do not duplicate constraint definitions -- reference the shared constraint file only.
