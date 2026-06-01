# X Standalone Constraints

Platform: X (Twitter)
Variant type: `standalone`
Platform slug: `twitter-x`

---

## Character Limits and Format Rules

- **Character limit:** 280 characters.  Hard ceiling.  The API rejects anything over.
- **Format:** Single tweet.  No threading, no numbering.
- **Links count toward the character limit** but Twitter shortens URLs to 23 characters (t.co wrapping).  Budget 23 characters for any link.

---

## Structural Requirements

One sharp take plus a link.  That is the entire structure.

1. **The take:** A provocative, specific observation from a different angle than the thread.  Not a summary of the thread -- a complementary perspective.
2. **The link:** Blog URL with UTM parameters.

The standalone must be self-contained.  A reader who never sees the thread should find this tweet complete and interesting on its own.

---

## Voice: Sam at Maximum Compression

**Mandatory pre-read:** Before generating any X standalone variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.

**The source content is a voice reference, not just an argument to mine.**  At 280 characters you can't preserve everything, but you can preserve specificity and Sam's observational stance.

280 characters of Sam, not 280 characters of generic tech commentary.  Compression removes words, not personality.

**Voice rules (non-negotiable):**
- Use at least one specific term from the source — a named tool, a named agent, a concrete detail.  "Claude Code does this in three seconds" beats "AI tools can do this quickly."  Specificity is what makes Sam's compression feel like Sam and not a fortune cookie.
- The take must be falsifiable.  If a reader can't disagree, it's too generic.  "Your AI agent works in demo because you tested the happy path" is falsifiable.  "AI agents need better testing" is not.
- No hedging, no qualifiers.  "This breaks" not "This might break."
- Sentence fragments are fine.  Punchy rhythm works.  But vary the length — two fragments followed by a longer observation creates Sam's rhythm.
- **Concrete over abstract.**  Ground any metaphor in physical details — "a hundred kilometers an hour" not "highway speed."  At 280 characters every word carries weight; make them tangible.
- Contractions always.
- Follow `.claude/rules/writing.md` for banned words and voice rules.
- Double space after every sentence-ending full stop.

**X standalone anti-convergence (AI-average patterns to avoid):**
- Thought-leader announcements: "Excited to share..." or "Here's what I learned..."
- Generic observations that could apply to any AI company
- Soft openings: "Thinking about how..." — start with the observation itself
- Missing specificity: no named tools, no concrete numbers, no falsifiable claims
- Uniform cadence: every word carrying equal weight, no rhythm variation

---

## CTA Conventions

The link is the CTA.  No explicit call to action needed -- the take creates the curiosity, the link satisfies it.

---

## Hashtag Rules

- No hashtags on standalone tweets.  They waste characters and signal noise.

---

## Image Handling

- No image on standalone tweets.  The tweet is text-only.
- This differentiates it visually from the thread (which has an image on post 1/).

---

## UTM Parameter Requirements

The blog link must include UTM parameters:
- `utm_source=twitter`
- `utm_medium=social`

Store in `format_metadata.utm_params` as `{"utm_source": "twitter", "utm_medium": "social"}`.

**CRITICAL — URL construction:**  Build the blog link from the `blog_url` field in `cli-kenwood content get <id>`, then append `?utm_source=twitter&utm_medium=social`.  **Do NOT use the Kenwood `slug` field** — it contains a date prefix and ID suffix (e.g. `2026-04-03-my-post-11`) that produce broken links.  The correct URL uses only the title slug (e.g. `https://otagelabs.com/blog/my-post`).

---

## Anti-Patterns

1. **Restating the thread hook.**  The standalone must take a different angle from the thread.  If both variants say the same thing, the standalone adds no value.
2. **Summary tweets.**  "I wrote about X" is not a standalone.  "X breaks because Y" is a standalone.
3. **Thread teasers.**  "Thread below on AI agents" is not a standalone.  It is a thread promotion tweet, and the standalone variant is not that.
4. **Exceeding 280 characters.**  Count carefully.  URLs are shortened to 23 characters by Twitter.
5. **Hashtag stuffing.**  No hashtags.  Zero.
6. **Soft openings.**  "Thinking about how..." is scroll-past material.  Start with the observation.

---

## format_metadata Output Specification

Each X standalone variant must include a `format_metadata` JSON object with these fields:

```json
{
  "thread_count": 1,
  "is_thread": false,
  "char_count": "<int, max 280>",
  "per_post_char_counts": ["<int>"],
  "utm_params": {"utm_source": "twitter", "utm_medium": "social"}
}
```

---

## Example Output

```
Your AI agent works in demo because you tested the happy path.  Production means 3am, empty strings, and retry loops that never stop.

https://otagelabs.com/blog/agent-debugging?utm_source=twitter&utm_medium=social
```

Character count: ~198 (within 280 limit, accounting for t.co URL shortening).
