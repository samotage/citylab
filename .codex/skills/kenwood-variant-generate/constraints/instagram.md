# Instagram Caption Constraints

Platform: Instagram
Variant type: `caption`
Platform slug: `instagram`

---

## Character Limits and Format Rules

- **Character limit:** 2,200 characters (Instagram caption limit).
- **Format:** Plain text caption.  Instagram does not render markdown.  Line breaks and emoji are the formatting tools.
- **Publishing method:** Manual.  Sam copies the caption and posts via the Instagram app.  No API integration.

---

## Structural Requirements

1. **Hook line:** The first line must stop the scroll.  Instagram truncates captions after ~125 characters -- everything after is hidden behind "more."  The hook must create enough curiosity to earn the tap.
2. **Body:** 2--3 short paragraphs.  Each paragraph is a self-contained thought.  Instagram's feed favours scannable, visual text.
3. **CTA or question:** Encourages profile visit or comment.  Instagram does not make feed links clickable -- do not include a URL in the caption body as a CTA.  Use "link in bio" phrasing instead.
4. **Hashtags:** 3--5 relevant hashtags at the end, separated from the body by a line break.

---

## Voice: Sam Behind the Scenes

**Mandatory pre-read:** Before generating any Instagram variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.

**The source content is a voice reference, not just an argument to mine.**  The source piece captures Sam's experience.  The Instagram caption captures a specific moment from that experience; the feeling, the scene, the behind-the-scenes reality.

Instagram is Sam's most personal platform.  The caption captures a moment, not an argument.  Behind-the-scenes, not broadcast.

**Voice rules (non-negotiable):**
- Capture a specific moment from the source — the debugging session, the 3am realisation, the first time something worked.  The caption is a window into the experience, not a summary of the conclusions.
- Use at least one specific detail: a tool name, an agent name, a concrete number, a time.  "The retry counter said 847" grounds the caption in reality.
- Vulnerability is the dominant mode.  Instagram rewards the behind-the-scenes reality.  "This is what debugging an AI agent at 3am looks like" beats "AI agents require robust testing."
- Short sentences for small screens.  But vary the length — a longer sentence followed by a short fragment creates rhythm.
- **Linger in the moment.**  When the point is how something feels, expand into flowing description rather than compressing into a list.  Instagram's character budget has room for this.  Let the reader sit in the scene.
- **Concrete metaphors.**  Ground metaphors in physical, colloquial details.  "A hundred kilometers an hour" not "highway speed."
- Reference the image.  The caption should complement what the image shows, not exist independently of it.
- First person ("I"), contractions, casual phrasing.
- Follow `.claude/rules/writing.md` for banned words and voice rules.
- Double space after every sentence-ending full stop.

**Instagram anti-convergence (AI-average patterns to avoid):**
- Professional tone leaking from LinkedIn: "I'm pleased to share our latest insights"
- Abstract observations with no specific moment or detail
- Caption that works without the image — Instagram captions must reference the visual
- Generic motivational energy: "Keep building!" or "The journey continues"
- Uniform sentence length throughout
- Hashtags that are generic industry terms (#AI, #Tech) instead of specific (#AgentDebugging, #BuildInPublic)

---

## CTA Conventions

| CTA Type | When to Use | Example |
|----------|-------------|---------|
| Profile visit | Default | "Link in bio for the full breakdown." |
| Question | When engagement matters | "What's the weirdest bug you've found in production?" |

- **No clickable links in captions.**  Instagram feed posts do not make URLs in captions clickable.  Use "link in bio" phrasing.
- The `format_metadata.link_in_bio_url` stores the URL that should be set as the bio link when posting.

---

## Hashtag Rules

- **Count:** 3--5 hashtags.  Current Instagram best practice favours fewer, targeted hashtags over volume.
- **Relevance:** Each hashtag must relate directly to the post content.
- **Placement:** After the CTA, separated by a line break.
- **Format:** No spaces in multi-word tags (#AIEngineering, not #AI Engineering).
- **No banned or shadow-banned hashtags.**  Avoid overly generic tags like #AI or #tech that attract bots.

---

## Image Handling

- **Image selection is critical.**  Instagram is a visual platform.  The image is the primary content -- the caption supports it.
- Select the most appropriate storyboard image based on:
  1. **Visual impact** -- the image should stop a scroll
  2. **Relevance** -- the image should connect to the caption's angle
  3. **Authenticity** -- real screenshots and behind-the-scenes shots outperform stock or generic images
- Store the selected image in `format_metadata.selected_image` with `path` and `description`.
- Store visual direction notes in `format_metadata.visual_direction` explaining why this image was selected.
- If no storyboard exists, use the content piece's featured image.  If no featured image exists, the caption can be posted as text-only (though this is unusual for Instagram).

---

## UTM Parameter Requirements

The link-in-bio URL should include UTM parameters:
- `utm_source=instagram`
- `utm_medium=social`

Store in `format_metadata.utm_params` as `{"utm_source": "instagram", "utm_medium": "social"}`.
Store the full URL in `format_metadata.link_in_bio_url`.

**CRITICAL — URL construction:**  Build the link-in-bio URL from the `blog_url` field in `cli-kenwood content get <id>`, then append `?utm_source=instagram&utm_medium=social`.  **Do NOT use the Kenwood `slug` field** — it contains a date prefix and ID suffix (e.g. `2026-04-03-my-post-11`) that produce broken links.  The correct URL uses only the title slug (e.g. `https://otagelabs.com/blog/my-post`).

---

## Anti-Patterns

1. **Including clickable URLs in the caption.**  Instagram does not make feed links clickable.  Use "link in bio" phrasing.
2. **Writing a LinkedIn-length argument.**  Instagram captions support personal, behind-the-scenes moments, not 1,400-character professional arguments.
3. **Hashtag volume.**  10+ hashtags signals spam.  Keep to 3--5 targeted tags.
4. **Generic stock imagery.**  Instagram rewards authenticity.  Select real screenshots, debugging sessions, or behind-the-scenes moments from the storyboard.
5. **Copying the hook from another platform.**  Each platform gets its own hook.  Instagram hooks are more personal and visual than social media hooks.
6. **Corporate tone.**  Instagram is the most informal platform in this set.  Write like sharing a moment with friends, not presenting to colleagues.
7. **Ignoring the image.**  The caption should complement and extend the image, not exist independently of it.  Reference what the image shows.

---

## Example Output

Caption:

```
This is what debugging an AI agent at 3am looks like.

The error log tells you nothing useful.  The retry counter says 847.  The context window overflowed three hours ago and nobody noticed because the test suite only exercises the happy path.

Six months of production debugging and the pattern is always the same: it works in testing because testing is polite.  Production is not polite.

Link in bio for the full breakdown.

#AIEngineering #ProductionAI #BuildInPublic #AgentDebugging #DevLife
```

format_metadata:

```json
{
  "char_count": 487,
  "hashtags": ["#AIEngineering", "#ProductionAI", "#BuildInPublic", "#AgentDebugging", "#DevLife"],
  "selected_image": {
    "path": "/path/to/storyboard/agent-debugging-03.png",
    "description": "Terminal screenshot showing error log output with retry counter at 847"
  },
  "visual_direction": "This image works because it shows the raw reality of production debugging -- a terminal full of error output.  The retry counter number (847) is immediately attention-grabbing and creates curiosity about what went wrong.",
  "utm_params": {"utm_source": "instagram", "utm_medium": "social"},
  "link_in_bio_url": "https://otagelabs.com/blog/agent-debugging?utm_source=instagram&utm_medium=social"
}
```
