---
name: regenerate-x-variant
description: Regenerate X/Twitter variants (thread + standalone) for a published content
  piece.
metadata:
  short-description: Regenerate X/Twitter variants (thread + standalone) for a published
    content piece.
---

# Skill: Regenerate X Variant

Regenerate X/Twitter variants independently of the full orchestration flow.  X produces two variant types: a thread (3--5 posts) and a standalone (single tweet).  They must use deliberately different angles.

**Trigger:** Skill injection "Regenerate" button on rejected/failed/cancelled X variants, or operator says "regenerate X variant for content piece <id>."

## References

- **Thread constraints:** `../kenwood-variant-generate/constraints/twitter-thread.md`
- **Standalone constraints:** `../kenwood-variant-generate/constraints/twitter-standalone.md`
- **Shared structure:** `../kenwood-variant-generate/variant-skill-structure.md` — input/output contract, voice self-check gate
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` — Sam's conversational writing voice (mandatory read before generating)
- **Writing rules:** `.claude/rules/writing.md` — banned words, double spaces, voice rules
- **MC surfacing:** `.claude/rules/mc-surfacing.md`

---

## Phase 1: Read Source

1. Read content piece metadata: `cli-kenwood content get <id>`
2. Read full content body: `cli-kenwood content body <id>`
3. Read storyboard images: `cli-kenwood storyboards list --content-id <id>`.  Thread variants use `featured_image_ref` on post 1; standalone tweets are text-only (set `featured_image_ref: null`).  If no storyboard or no completed frames and generating a thread, report to Sam before proceeding.  See `variant-skill-structure.md` § Image Discovery and Resolution.
4. Read the voice reference: `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  This is non-negotiable editorial law.  Internalise Sam's voice markers before generating.
5. Check for existing X variants: `cli-kenwood variants list --content-id <id>`
6. Surface: `cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate`

**Gate:** Content piece must be in `published` status.  If not, report and stop.

If existing X variants exist, note their bodies, statuses, and variant types (thread/standalone).  Rejected/failed/cancelled variants inform angle differentiation in Phase 2.

**Selective regeneration (FR6):** If only one variant type was rejected (thread or standalone), regenerate only that type unless Sam requests both.  If both were rejected, regenerate both.

---

## Phase 2: Generate

1. Read both X constraint files: `../kenwood-variant-generate/constraints/twitter-thread.md` and `../kenwood-variant-generate/constraints/twitter-standalone.md`
2. If regenerating after rejection: read the rejected variant(s) to understand previous angles.  Deliberately choose different approaches.
3. Identify the thread angle (structured argument that unpacks the insight across 3--5 posts).
4. Identify the standalone angle (compressed provocation from a different facet -- not a summary of the thread, not the hook post extracted).
5. Present both angles to Sam for confirmation.  Wait for approval.
6. Generate the thread variant following thread constraints.  Count each post — every post must be at or under 280 characters including the numbering prefix.
6b. **Mechanical character scan (mandatory before voice gate, applies to BOTH the thread AND the standalone).**  Scan each variant body for `—` (em dash), `–` (en dash), ` -- ` (double-hyphen), smart quotes (`"` `"` `'` `'`), and `…` (ellipsis char).  Any single hit is an automatic rewrite — these are LLM authorship tells.  Use straight ASCII substitutes (commas/semicolons/sentence breaks for dashes; `"` and `'` for quotes; `...` for ellipsis).  Re-scan after rewriting.  Do NOT proceed to the voice gate until clean.  Full pattern table in `../kenwood-variant-generate/variant-skill-structure.md`.

7. **Voice self-check (7-point gate)** on the thread variant.  All must pass before writing:
   1. Preserves at least one named reference from the source?  2. Uses specific terms, not generic substitutes?  3. Includes vulnerability or honest admission?  4. Closer passes punchline test?  5. Contains sentence-length variation?  6. Stays in scene rather than pivoting to advice or abstract principles?  Compress by finding a sharper story angle, not by abstracting.  7. Every sentence passes the coffee test — would Sam say it over a beer?  8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source?  Inflating or inverting facts is fabrication and an automatic fail.  Any failure means rewrite.
8. Construct thread `format_metadata` per the constraint file's output specification.
9. Write thread variant:
   ```bash
   cli-kenwood variants create --content-id <id> --platform twitter-x --variant-type thread --title "X thread" --body "<full thread text>" --format-metadata '<json>'
   ```
9. Surface thread and refresh content piece:
   ```bash
   cli-kenwood mc focus --entity-type content_variant --entity-id <thread_variant_id>
   cli-kenwood mc focus --entity-type content_piece --entity-id <id>
   ```
11. Generate the standalone variant following standalone constraints.  Must be at or under 280 characters.
12. **Voice self-check** on the standalone.  Checks 1, 2, 5, 6, and 7 must pass (vulnerability and closer checks are less applicable at 280 chars).  Any failure means rewrite.
13. Construct standalone `format_metadata` per the constraint file's output specification.
14. Write standalone variant:
    ```bash
    cli-kenwood variants create --content-id <id> --platform twitter-x --variant-type standalone --title "X standalone" --body "<tweet text>" --format-metadata '<json>'
    ```
13. Surface standalone and refresh content piece:
    ```bash
    cli-kenwood mc focus --entity-type content_variant --entity-id <standalone_variant_id>
    cli-kenwood mc focus --entity-type content_piece --entity-id <id>
    ```

---

## Phase 3: Report

1. Report both variants: thread (post count, hook preview) and standalone (full text preview)
2. Remind Sam to review in the variant review UI

---

## Hard Constraints

1. Per-post character count MUST be at or under 280.  The `1/` numbering prefix counts toward the limit.
2. Thread and standalone MUST use different angles.  If the standalone summarises the thread, the skill has failed.
3. Thread body field stores readable text (for review UI).  `format_metadata.posts` stores per-post structured data (for publisher).  Both must be generated.
4. **Voice is non-negotiable.**  Read `voice.md` before generating.  Apply voice self-check gate before writing each variant.  `.claude/rules/writing.md` banned words, double spaces, and LLM pattern avoidance enforced.
5. When regenerating after rejection, MUST use different angles from the rejected variant(s).
6. Selective regeneration: regenerate only the rejected variant type unless Sam requests both.
7. Do not duplicate constraint definitions -- reference the shared constraint files only.
