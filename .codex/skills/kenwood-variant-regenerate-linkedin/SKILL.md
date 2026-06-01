---
name: regenerate-linkedin-variant
description: Regenerate a LinkedIn variant for a published content piece.  Standalone
  skill for single-platform regeneration.
metadata:
  short-description: Regenerate a LinkedIn variant for a published content piece.
---

# Skill: Regenerate LinkedIn Variant

Regenerate a single LinkedIn variant independently of the full orchestration flow.  For cases where a rejected variant needs a fresh angle, source content changed, or LinkedIn-only generation is needed.

**Trigger:** Skill injection "Regenerate" button on rejected/failed/cancelled LinkedIn variants, or operator says "regenerate LinkedIn variant for content piece <id>."

## References

- **Platform constraints:** `../kenwood-variant-generate/constraints/linkedin.md` — all LinkedIn rules and format_metadata schema
- **Shared structure:** `../kenwood-variant-generate/variant-skill-structure.md` — input/output contract, CLI commands, voice self-check gate
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's conversational writing voice (mandatory read before generating)
- **Writing rules:** `.claude/rules/writing.md` — banned words, double spaces, voice rules
- **MC surfacing:** `.claude/rules/mc-surfacing.md` — when and how to surface entities

---

## Phase 1: Read Source

1. Read content piece metadata: `cli-kenwood content get <id>`
2. Read full content body: `cli-kenwood content body <id>`
3. Read storyboard images: `cli-kenwood storyboards list --content-id <id>`.  If frames with `generation_status: complete` exist, their `image_path` values are available for `featured_image_ref`.  If no storyboard or no completed frames, report to Sam and wait for confirmation before proceeding as text-only.  See `variant-skill-structure.md` § Image Discovery and Resolution for `featured_image_ref` semantics.
4. Read the voice reference: `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  This is non-negotiable editorial law, not optional context.  Internalise Sam's voice markers before generating.
5. Check for existing LinkedIn variants: `cli-kenwood variants list --content-id <id>`
6. Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate`

**Gate:** Content piece must be in `published` status.  If not, report and stop.

If existing LinkedIn variants exist, note their bodies and statuses.  Rejected/failed/cancelled variants inform the angle differentiation in Phase 2.

---

## Phase 2: Generate

1. Read the LinkedIn constraint file from `../kenwood-variant-generate/constraints/linkedin.md`
2. If regenerating after rejection: read the rejected variant's body to understand the previous angle.  Deliberately choose a different approach -- different hook, different argument structure, different entry point into the same core insight.
3. Identify a LinkedIn-specific teaser angle from the source content: what scene hooks the reader, what insight pivots their attention, what payoff stays on the blog.  Present the angle to Sam in 1--2 sentences.  Wait for confirmation.
4. Generate the LinkedIn variant following all constraint rules.  Count characters before writing — must be 600--1,000.  The post is a teaser: 2--3 flowing conversational paragraphs that create FOMO and drive the click to the full blog post.
4b. **Mechanical character scan (mandatory before voice gate).**  Scan the variant body for `—` (em dash), `–` (en dash), ` -- ` (double-hyphen), smart quotes (`"` `"` `'` `'`), and `…` (ellipsis char).  Any single hit is an automatic rewrite — these are LLM authorship tells.  Use straight ASCII substitutes (commas/semicolons/sentence breaks for dashes; `"` and `'` for quotes; `...` for ellipsis).  Re-scan after rewriting.  Do NOT proceed to the voice gate until clean.  Full pattern table in `../kenwood-variant-generate/variant-skill-structure.md`.

5. **Voice self-check (7-point gate).**  All must pass before writing:
   1. Preserves at least one named reference from the source?  **Yes/No**
   2. Uses specific terms from the source, not generic substitutes?  **Yes/No**
   3. Includes at least one vulnerability or honest admission?  **Yes/No**
   4. Closer passes the tease test (creates FOMO -- open question, honest admission, or hint at what's in the full post -- not thesis statement)?  **Yes/No**
   5. Contains at least two different sentence lengths in sequence?  **Yes/No**
   6. Stays in scene (characters acting, things happening) rather than pivoting to advice or abstract principles?  Scene over instruction on social, even when the source uses instruction.  Compress by finding a sharper story angle, not by abstracting.  **Yes/No**
   7. Every sentence passes the coffee test — would Sam say it over a beer?  Performed-sounding sentences get rewritten.  **Yes/No**
   8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source content piece?  Inflating, rounding, or inverting facts for hook impact is fabrication and an automatic fail.  **Yes/No**
   Any failure means rewrite, not ship.
6. Construct `format_metadata` JSON per the constraint file's output specification.
7. Write the variant:
   ```bash
   cli-kenwood variants create --content-id <id> --platform linkedin --variant-type post --title "LinkedIn post" --body "<body>" --format-metadata '<json>'
   ```
7. Surface variant and refresh content piece:
   ```bash
   cli-kenwood mc focus --entity-type content_variant --entity-id <variant_id>
   cli-kenwood mc focus --entity-type content_piece --entity-id <id>
   ```

---

## Phase 3: Report

1. Report to Sam: variant created, character count, hook preview (first ~50 chars), closer type
2. Remind Sam to review in the variant review UI

---

## Hard Constraints

1. **All format rules come from the constraint file.**  Read `../kenwood-variant-generate/constraints/linkedin.md` and follow it exactly.  Do not hardcode format values here.
2. Hook text MUST be extractable from the first 140 characters.
3. Body MUST be 2--3 flowing conversational paragraphs.  Not single-sentence staccato, not listicle format.
4. The post is a TEASER.  It must withhold the full argument/conclusion.  The blog link in the first comment is the resolution.
5. **Voice is non-negotiable.**  Read `voice.md` before generating.  Apply the 8-point voice self-check gate before writing.  `.claude/rules/writing.md` banned words and LLM pattern avoidance are enforced.
6. When regenerating after rejection, MUST use a different angle from the rejected variant.
7. Do not duplicate constraint definitions -- reference the shared constraint file only.
