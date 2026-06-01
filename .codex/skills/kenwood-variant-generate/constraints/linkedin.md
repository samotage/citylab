# LinkedIn Post Constraints

Platform: LinkedIn
Variant type: `post`
Platform slug: `linkedin`

**Canonical strategy reference:** `docs/content_strategy/linkedin/otagelabs-content-360brew-guidelines.md`

---

## Purpose: Drive the Click

The LinkedIn post is a teaser.  The blog is the full argument.  The post exists to create enough curiosity and FOMO that the reader clicks through to the website.

This means the post must be interesting on its own AND withhold enough that the full article is the only way to get the payoff.  Hook them with a personal experience, hint at what you found, but do not give away the conclusion, the framework, or the specific steps.  The reader finishes the post knowing there is something valuable they can only get by clicking.

**Test:** After reading the post, would someone think "I need to read the full thing"?  If the post gives away the answer, it has failed as a teaser.

---

## Character Limits and Format Rules

- **Total character count:** 600--1,000 characters.  The short end of LinkedIn's range.  Teasers are lean; the depth lives on the website.
- **Hook (pre-"see more"):** First 140 characters must work as a standalone scroll-stopper.  This is what LinkedIn shows before truncating.  It must create enough tension or curiosity to earn the expand.
- **Body format:** Plain text, no markdown rendering.  Flowing conversational paragraphs, not single-sentence staccato.
- **No external links in post body.**  Links in the body incur a ~60% reach penalty under 360Brew.  Blog link goes in the first comment only; store it in `format_metadata.blog_link_for_comment`.
- **No hashtags.**  360Brew (March 2026) uses semantic interest graphs, not hashtag signals.  Hashtags are dead weight.  Zero hashtags in the post.
- **Single spaces after full stops.**  LinkedIn strips double spaces.  Use single spaces on this platform.

---

## Structural Requirements

The post is a conversational teaser in 2--3 flowing paragraphs.  Not a listicle, not single-sentence-per-line staccato, not a structured argument.  It reads like Sam telling someone about something he wrote, not like a content piece engineered for engagement metrics.

1. **Paragraph 1: The scene** (the hook lives here).  Drop the reader into a specific personal experience.  A moment, a contrast, something that happened.  This is the scroll-stopper and the "see more" earner.  Concrete, conversational, in-scene.

2. **Paragraph 2: The pivot.**  What the experience revealed or pointed to.  The insight or tension that makes the story worth telling.  This paragraph earns the reader's interest, but does NOT deliver the full argument.  It pivots from "here's what happened" to "here's why it matters."

3. **Paragraph 3: The tease.**  Hint at what's in the full blog post without giving it away.  Reference the specific experiments, findings, or frameworks the reader will find, but describe them in terms that create curiosity rather than satisfy it.  "I wrote up what worked and what was a loan with bad terms" implies specific answers the reader wants.  "Here are the five things that worked" gives them away.  End with the tease, not a thesis statement.  The last line should trail off into the reader's need to click, not wrap up the argument.

After the post body, add: "Link is in the first comment." (or similar natural phrasing).

**Format within paragraphs:** Flowing prose.  Multiple sentences per paragraph.  Conversational rhythm, not performative structure.  Short sentences can sit inside a longer paragraph for rhythm.  But the paragraph is the unit, not the sentence.

---

## Pillar Alignment

Every post must touch at least one content pillar.  Ideally two.  Target distribution across the content calendar: ~40% Pillar 1, ~35% Pillar 2, ~25% Pillar 3.

| Pillar | Focus | Named References |
|--------|-------|-----------------|
| 1. AI-native development (foundation) | Building production systems with intelligence designed in | Claude Code, spec-driven process, production-first |
| 2. Agent orchestration (differentiator) | Multi-agent coordination, agent monitoring | Claude Headspace, development orchestration tooling |
| 3. Service automation (buyer hook) | Turning manual processes autonomous | RAGlue, multi-platform automation system |

Store pillar alignment in `format_metadata.pillar_tags[]`.

---

## Drive the Click, Not the Save

Saves are valuable under 360Brew, but the primary goal of the LinkedIn post is website traffic.  The post is a teaser, not a self-contained resource.

The post drives clicks by:
- Opening with a personal experience that earns attention through specificity
- Establishing tension or curiosity that the post does not resolve
- Hinting at specific, named content in the full article ("what worked, what was a loan with bad terms") without delivering it

**Test:** Would someone click through to read the full thing?  If the post is self-contained and bookmarkable on its own, it has given away too much.  The save should happen on the blog, not on the LinkedIn post.

---

## Voice: Sam on LinkedIn

**Mandatory pre-read:** Before generating any LinkedIn variant, read `.claude/skills/kenwood-blog-20-ideate-post/voice.md`.  That document is the voice benchmark.  These platform-specific rules build on it; they do not replace it.

**The source content is a voice reference, not just an argument to mine.**  The source piece has already been written in Sam's voice.  Your job is to tease the argument for LinkedIn while preserving the voice texture.  Do not sanitise the source into generic professional prose.

### Voice rules for LinkedIn

- **First person for otageLabs as an entity.**  "I," not "we" -- solo practice.  But "we" drawing readers into shared experience is conversational, not corporate ("just like we've always done").
- **Preserve named references from the source.**  If the source names people (Robbo, Mel, Mark), projects (Kenwood), or tools (Claude Code, RAGlue), the variant keeps at least one.  "Three AI agents" is a summary.  "Robbo as the architect, Mel on the BA side" is Sam.
- **Observation over verdict.**  "I keep watching teams build demos that die" is an observation.  "The PoC has become a comfort blanket" is a verdict.  Convert verdicts to observations.
- **Vulnerability survives compression.**  If the source has a moment of honest admission, surprise, or discomfort, the LinkedIn variant must preserve at least one.  Vulnerability is a strength on LinkedIn, not a weakness.
- **Ground every claim in something built, observed, or measured.**  No ungrounded authority.  LinkedIn's audience expects substance from practitioner experience, not thought leadership positioning.
- **Close with a tease, not a thesis.**  The final line should leave the reader wanting more.  An open question works.  An honest admission works.  A hint at specific findings works ("I wrote up what worked").  A neat summary does not.
- **Vary sentence length.**  Short sentences after long ones.  Sentence fragments are fine.  Monotonous cadence is the loudest AI tell on LinkedIn.
- **Flowing paragraphs, not staccato.**  The post should read like Sam talking, not like a listicle.  Multiple sentences per paragraph.  Conversational rhythm.
- **Concrete metaphors.**  Ground metaphors in physical, tangible details.  "A hundred kilometers an hour" not "highway speed."  Colloquial phrases ("smell the roses") do real work.
- **Contractions.**  "I'll," "won't," "can't," "it's."  Formal phrasing is death on any platform.
- **Directness.**  No "I think" or "I believe."  State it.
- **Dry humor where it fits.**  Observations that happen to be funny because they're true.  Not jokes.
- Follow `.claude/rules/writing.md` for banned words and LLM pattern avoidance.

### Anti-convergence: what AI-average LinkedIn content looks like

These are the tells.  If your variant matches any of these patterns, rewrite before proceeding.

- **Single-sentence-per-paragraph staccato.**  Every line a standalone sentence with a blank line after it.  This is the default AI LinkedIn format.  It reads like a content template, not a person talking.  Sam writes in flowing paragraphs.
- **Generic authority opener.**  "In today's rapidly evolving AI landscape..." or "As someone who works with AI agents daily..."  Sam never opens this way.
- **Sanitised specifics.**  Named agents become "AI agents."  Named projects become "a software project."  Named tools become "AI tools."  Every proper noun replaced with a category noun is a step toward content mill territory.
- **Vulnerability stripped.**  The honest admissions and moments of surprise are gone, replaced with confident professional narration.  If the variant reads like a case study instead of a person reflecting, it's been sanitised.
- **Uniform sentence length.**  Every sentence 15-20 words.  No fragments, no variation.  Reads like a press release.
- **Thesis-statement closer.**  Ends with a neat, quotable summary instead of a tease or an admission.  If the last line could go on a conference slide, cut it.
- **"I'm excited to share" energy.**  Any whiff of announcement framing instead of reflection.
- **Self-contained argument.**  The post delivers the full insight, the full framework, the full conclusion.  Nothing left to click through for.  This is the anti-teaser pattern.

---

## Image and UTM Rules

- Featured image from the source content piece's storyboard (if available).  Store path in `format_metadata.featured_image_ref`.  No storyboard image means text-only post.
- Blog link for first comment: use the `blog_url` field from `cli-kenwood content get <id>` and append `?utm_source=linkedin&utm_medium=social`.  Store in `format_metadata.blog_link_for_comment`.  This link goes in the first comment after posting, never in the post body.  **Do NOT construct the URL from the Kenwood `slug` field** -- it contains a date prefix and ID suffix that produce broken links.

---

## Anti-Patterns

- Do not give away the full argument.  Tease the blog post; withhold the payoff.
- Do not start with "I" -- vary the opener (scene, observation, moment).
- Do not open with "I'm excited to share" or "Just published."  Start with the scene.
- Do not write single-sentence paragraphs.  Write flowing conversational paragraphs.
- Do not include hashtags.  Zero hashtags anywhere in the post.
- Do not put external links in the post body.  Blog link goes in first comment only.
- Do not use em dashes -- use semicolons, commas, or sentence breaks.
- Do not end with a CTA like "DM me," "follow for more," or "like and share."  End with a tease.
- Do not write listicles ("5 ways AI will...").
- Do not write about AI abstractly.  Ground in something built, broken, or learned.
- Do not deliver the conclusion.  The conclusion lives in the blog post.

---

## format_metadata Output Specification

Each LinkedIn variant must include a `format_metadata` JSON object with these fields:

```json
{
  "char_count": "<int, 600-1000>",
  "hook_text": "<string, first 140 chars of body>",
  "pillar_tags": ["<string>", "...1-3 entries from: ai-native-dev, agent-orchestration, service-automation"],
  "closer_type": "<tease|open_question|honest_admission>",
  "blog_link_for_comment": "<string, {blog_url}?utm_source=linkedin&utm_medium=social -- use blog_url from cli-kenwood content get, or null if no source blog post>",
  "utm_params": {"utm_source": "linkedin", "utm_medium": "social"},
  "featured_image_ref": "<string, storyboard image path or null>"
}
```
