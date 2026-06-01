# BlueSky Post Constraints

Platform: BlueSky
Variant type: `post`
Platform slug: `bluesky`

---

## Character Limits and Format Rules

- **Character limit:** 300 characters.  Hard ceiling enforced by the AT Protocol.
- **Format:** Single post.  No threading, no numbering.
- **Links:** Rendered as AT Protocol facets (clickable in the BlueSky app).  The publisher generates facets automatically from URLs in the text.

---

## Structural Requirements

A single sharp take with a conversational tone.  BlueSky rewards community engagement over broadcast.

1. **The take:** A conversational, community-oriented observation from a different angle than the BlueSky thread.  Not a compressed version of anything -- a standalone thought that invites response.
2. **The link:** Blog URL with UTM parameters.  Rendered as a clickable facet by the publisher.

The post must work as a standalone piece of content.  A reader who never sees the thread should find this post interesting and complete.

---

## Voice: Sam at the Meetup

**Mandatory pre-read:** Before generating any BlueSky post variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.

**The source content is a voice reference, not just an argument to mine.**  At 300 characters, compress the argument but preserve Sam's observational stance and at least one specific detail from the source.

BlueSky is Sam talking to peers; warmer than X, less polished than LinkedIn, more vulnerable than both.

**Voice rules (non-negotiable):**
- Thinking-out-loud energy means vulnerability, not vagueness.  "I keep running into this" is Sam.  "Many developers experience this" is a content mill.
- Use at least one specific detail from the source — a named tool, a concrete number, a named agent.  Specificity grounds the post in Sam's experience, not generic observation.
- Dry humor and honest observations.  BlueSky rewards the observations that happen to be funny because they're true.
- "I'm figuring this out too" energy outperforms authority positioning.  Share the insight directly, without the credential preamble.
- **Concrete metaphors.**  Ground metaphors in physical, tangible details — "a hundred kilometers an hour" not "highway speed."  Colloquial phrases ("smell the roses") do real work at 300 characters.
- First person ("I"), contractions, sentence fragments are all fine.
- **Observation over verdict.**  "I keep running into this" is an observation.  "The industry needs to solve this" is a verdict.  Sam observes; he doesn't pronounce.
- Vary sentence length.  A short fragment after a longer observation creates Sam's natural rhythm.
- Follow `.claude/rules/writing.md` for banned words and voice rules.
- Double space after every sentence-ending full stop.

**BlueSky anti-convergence (AI-average patterns to avoid):**
- Broadcast tone: "I'm pleased to announce" — BlueSky culture punishes this
- Authority positioning: "As someone who has been doing X for years" — credential preambles signal broadcast culture
- Generic observations that could come from anyone: no specific names, tools, or experiences
- Vague vulnerability: "This stuff is hard" without saying what specifically is hard
- Cross-posted feel: a post that reads like it was written for X and pasted into BlueSky

---

## CTA Conventions

- The link is the CTA.  No explicit "click here" or "read more" needed.
- If space allows, frame the link naturally: "Wrote about this:" or "More context:"
- Questions that invite community response work well as implicit CTAs.

---

## Hashtag Rules

- BlueSky does not use hashtags in the traditional sense.  The AT Protocol supports them as facets, but the culture does not favour hashtag-heavy posts.
- Zero hashtags is the default.  If a hashtag is genuinely part of an ongoing community conversation, one hashtag maximum.

---

## Image Handling

- No image on standalone posts.  This differentiates it from the thread variant (which has an image on post 1).
- The text stands on its own.

---

## UTM Parameter Requirements

The blog link must include UTM parameters:
- `utm_source=bluesky`
- `utm_medium=social`

Store in `format_metadata.utm_params` as `{"utm_source": "bluesky", "utm_medium": "social"}`.

**CRITICAL — URL construction:**  Build the blog link from the `blog_url` field in `cli-kenwood content get <id>`, then append `?utm_source=bluesky&utm_medium=social`.  **Do NOT use the Kenwood `slug` field** — it contains a date prefix and ID suffix (e.g. `2026-04-03-my-post-11`) that produce broken links.  The correct URL uses only the title slug (e.g. `https://otagelabs.com/blog/my-post`).

---

## Anti-Patterns

1. **Cross-posting from X.**  BlueSky's community is different from X's.  A post that works on X may fall flat on BlueSky.  Write for this platform specifically.
2. **Broadcast tone.**  "I'm pleased to announce" is anti-BlueSky.  "I keep running into this and it's driving me nuts" is pro-BlueSky.
3. **Exceeding 300 characters.**  The AT Protocol enforces this strictly.  Budget carefully.
4. **Hashtag stuffing.**  BlueSky culture does not favour hashtags.  Zero is the default.
5. **Copying the thread hook.**  The post takes a different angle from the thread.  It is a complementary perspective, not an excerpt.
6. **Authority positioning.**  "As an expert in X" signals broadcast culture.  Share the insight without the credential preamble.

---

## Example Output

```
I've been debugging production AI agents for six months.  The pattern is always the same: it works in testing because testing only exercises the happy path.  Production means empty strings at 3am.

https://otagelabs.com/blog/agent-debugging?utm_source=bluesky&utm_medium=social
```

Character count: ~267 (within 300 limit).

---

## format_metadata Output Specification

The `format_metadata` JSON object for a BlueSky post variant:

```json
{
  "char_count": <int, max 300>,
  "utm_params": {"utm_source": "bluesky", "utm_medium": "social"}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `char_count` | int | Character count of the post text.  Must be at or under 300. |
| `utm_params` | object | UTM tracking parameters for the blog link. |
