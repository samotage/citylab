---
name: generate-variants
description: Generate platform-native content variants for a published content piece
  across all configured platforms in one session.
metadata:
  short-description: Generate platform-native content variants for a published content
    piece across all configured platforms in one session.
---

# Skill: Generate Variants

Generate platform-native content variants for a published content piece across all configured platforms in one session.  One read, one angle, all platforms.

**Trigger:** Skill injection registry button "Generate Variants" on published content pieces, or operator says "generate variants for content piece <id>."

---

## References

- **Shared structure:** `variant-skill-structure.md` (co-located) -- input/output contract, CLI commands, format_metadata schemas
- **Platform constraints:** `constraints/` (co-located) -- 7 platform-specific constraint files
- **Writing rules:** `.claude/rules/writing.md` -- editorial rules, banned words, LLM pattern avoidance, double spaces
- **MC surfacing:** `.claude/rules/mc-surfacing.md` -- when and how to surface entities in Mission Control
- **Voice:** `.claude/skills/kenwood-blog-20-ideate-post/voice.md` -- Sam's conversational writing voice

---

## Phase 1: Absorb

**Goal:** Read the source content and understand what we are working with.

1. Read content piece metadata:
   ```bash
   cli-kenwood content get <id>
   ```

2. Read the full content body:
   ```bash
   cli-kenwood content body <id>
   ```

3. Read storyboard images (if available):
   ```bash
   cli-kenwood storyboards list --content-id <id>
   ```
   If the command returns frames with `generation_status: complete`, use their `image_path` values for `featured_image_ref`.  If no storyboard or no completed frames, **report to Sam:** "No images found for content piece <id>.  Proceed as text-only?"  Wait for confirmation before continuing.  See `variant-skill-structure.md` § Image Discovery and Resolution for `featured_image_ref` semantics.

4. Check for existing variants:
   ```bash
   cli-kenwood variants list --content-id <id>
   ```

5. Surface the content piece in MC:
   ```bash
   cli-kenwood mc focus --entity-type content_piece --entity-id <id> --navigate
   ```

6. Read the voice reference:
   Read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  This is the voice benchmark — every variant must pass the voice tests in this document.  Internalise Sam's voice markers: named references, vulnerability over authority, observation over verdict, dry humor, sentence-rhythm variation, closer style.  This is non-negotiable editorial law, not optional context.

**Gate check:** Content piece must be in `published` status.  If not, report to Sam and stop.

### Existing Variants

If existing variants are found:
- Report which platforms already have variants and their statuses
- Ask Sam whether to skip those platforms or regenerate
- Default: skip platforms with existing `approved` or `deployed` variants; regenerate for platforms with `rejected`, `cancelled`, or `failed` variants

---

## Phase 2: Identify the Angle

**Goal:** Find the single sharpest insight that will carry across all platforms.

1. Analyse the source content for the sharpest angle -- the single insight, argument, or observation with the most cross-platform potential
2. Present the angle to Sam in 1--2 sentences
3. Wait for Sam's confirmation or redirection
4. If Sam redirects, adjust the angle and re-present

**Gate check:** Sam has confirmed the angle (explicit confirmation or "go" signal).  Do not proceed without confirmation.

### Voice Preservation

The source content has already been written in Sam's voice.  Your job is to compress and adapt the argument for each platform while preserving voice texture.  Specifically:

- **Named references** from the source (agent names, product names, project names) must survive into variants.  "Robbo, Mel, and Mark" becoming "three AI agents" is sanitisation — do not do this.
- **Vulnerability markers** (honest admissions, uncertainty, "I don't know" moments) must be preserved or adapted, not stripped.
- **Observation over verdict.**  If the source says "I watched three agents negotiate a schema," the variant does not become "Multi-agent collaboration is transforming software development."
- **Closer style.**  If the source ends with an open question, variants close with an open question or honest admission — not a thesis statement.

Do not sanitise the source into generic professional prose.  The source IS the voice benchmark for this variant set.

---

## Phase 3: Generate Variants

**Goal:** Generate platform-native variants in sequence, writing each to Kenwood before moving to the next.

### Determine Platforms

Read configured platforms.  For platforms with `supports_threads = true` (X, BlueSky), generate both thread and post/standalone variants.

### Generation Order

Generate in platform priority order:

1. LinkedIn (post)
2. X thread
3. X standalone
4. WordPress (article)
5. BlueSky post
6. BlueSky thread
7. Instagram (caption)

Skip platforms that are not configured or explicitly disabled.  Report skipped platforms with the reason.

### Per-Variant Process

For each variant:

1. **Read the constraint file** from `constraints/<platform>.md`
2. **Generate the variant** following all constraints.  Platform constraints are non-negotiable — character limits, format rules, structural requirements are law.
2b. **Mechanical character scan (mandatory before voice gate).**  Scan the variant body for `—` (em dash), `–` (en dash), ` -- ` (double-hyphen), smart quotes (`"` `"` `'` `'`), and `…` (ellipsis char).  Any single hit is an automatic rewrite — these are LLM authorship tells.  Use straight ASCII substitutes (commas/semicolons/sentence breaks for dashes; `"` and `'` for quotes; `...` for ellipsis).  Re-scan after rewriting.  Do NOT proceed to the voice gate until clean.  Full pattern table in `variant-skill-structure.md`.

3. **Voice self-check (7-point gate).**  Before proceeding, verify all seven checks pass.  Any failure means rewrite, not ship:
   1. Does the variant preserve at least one named reference from the source (agent names, product names, project names)?  **Yes/No**
   2. Does the variant use specific terms from the source rather than generic substitutes?  **Yes/No**
   3. Does the variant include at least one vulnerability or honest admission from the source (where the platform's format allows)?  **Yes/No**
   4. Does the closer pass the punchline test — open question or honest admission, not thesis statement?  **Yes/No**
   5. Does the variant contain at least two different sentence lengths in sequence?  **Yes/No**
   6. Does the variant stay in scene — characters acting, things happening — rather than pivoting to advice, prescriptions, or abstract principles?  On social platforms, default to scene over instruction even when the source does.  When compressing, find a sharper angle from the story; don't summarise into a principle.  **Yes/No**
   6b. Does the variant linger in description where the point is how something feels, rather than compressing into tight parallel lists?  Are metaphors grounded in concrete, physical details rather than left as abstractions?  **Yes/No**
   7. Read every sentence aloud.  Would Sam say it over a beer?  Any sentence that sounds performed gets rewritten in plain language.  **Yes/No**
   8. Does every specific claim — numbers, outcomes, what happened, who did what — match the source content piece?  Cross-check: if the source says "twelve decisions, two lost," the variant cannot say "ten decisions, all lost."  Inflating, rounding, or inverting facts for hook impact is fabrication and an automatic fail regardless of how well the rest of the variant reads.  **Yes/No**
4. **Construct `format_metadata`** per the companion software PRD schema (referenced in `variant-skill-structure.md`)
5. **Write the variant:**
   ```bash
   cli-kenwood variants create \
     --content-id <id> \
     --platform <slug> \
     --variant-type <type> \
     --title "<title>" \
     --body "<body>" \
     --format-metadata '<json>'
   ```
6. **Surface in MC:**
   ```bash
   cli-kenwood mc focus --entity-type content_variant --entity-id <variant_id>
   cli-kenwood mc focus --entity-type content_piece --entity-id <id>
   ```
7. **Report to Sam:** Platform, type, character count, hook preview (first ~50 characters)

### Cross-Platform Awareness

Make deliberate cross-platform choices.  Each variant must be genuinely platform-native -- not the same text adapted to different character limits.

- X thread may tease the LinkedIn deep-dive
- BlueSky post takes a different conversational angle that complements WordPress
- Instagram caption captures a different facet than social platforms
- X standalone and BlueSky post find angles that complement their platform's thread
- Each platform's hook must be native to that platform's conventions -- no shared hooks

**Gate check:** All configured platform variants have been created.  No CLI errors.

---

## Phase 4: Summary

**Goal:** Report the complete picture and hand off to review.

1. Report the variant set:
   - Total variant count
   - Per-platform breakdown: platform, variant type, character count
   - The shared angle (from Phase 2)
   - Any platforms skipped and why

2. Remind Sam to review variants in the variant review UI.  Publishing to platforms is a separate action -- use the `kenwood-variant-publish` skill after review and approval.

3. Notify via MC:
   ```bash
   cli-kenwood mc notify --message "Generated {count} variants for '{title}' across {platform_count} platforms"
   ```

---

## Hard Constraints

These are non-negotiable.  Violating any of these is a skill failure.

1. **One read, one angle, all platforms.**  Source content is read once in Phase 1.  Angle is identified once in Phase 2.  All variants share that angle with platform-native execution.

2. **Write before moving on.**  Each variant is written to Kenwood via CLI immediately after generation.  No batching at the end.

3. **Platform constraints are law.**  Character limits, format rules, and structural requirements from the constraint files are non-negotiable.

4. **Cross-platform awareness, not duplication.**  Each platform variant must be genuinely platform-native.  Adapting the same text to different character limits is not variant generation.

5. **Surface as you go.**  Each variant is surfaced in MC via `cli-kenwood mc focus` immediately after creation.

6. **Voice is non-negotiable.**  Read `voice.md` before generating.  Apply the 8-point voice self-check gate before writing each variant.  `.claude/rules/writing.md` banned words and LLM pattern avoidance are enforced on all content.  A variant that passes platform mechanics but fails voice is not ready to ship.

---

## Anti-Patterns

Do not:

1. **Generate all variants in memory then write at the end.**  Write each one immediately.
2. **Ask Sam to approve each variant individually during generation.**  Generation produces drafts.  Review happens in the variant review UI after generation completes.
3. **Treat variant generation as summarisation.**  A LinkedIn post is not a summary of the blog post.  It is a platform-native piece of content that makes the same argument in the way LinkedIn's audience consumes it.
4. **Skip platforms without reporting.**  If a platform is skipped, say why.
5. **Generate thread posts that exceed character limits.**  Each thread post must independently fit within the per-post character limit.
6. **Use the same opening/hook across platforms.**  Each platform's hook is native to that platform's conventions.
