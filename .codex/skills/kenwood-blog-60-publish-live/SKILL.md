---
name: kenwood-blog-60-publish-live
description: Pipeline step 6/6. Automatic — runs after SEO. Commit blog changes, create
  and merge PR to main, verify Vercel production deployment. No operator gates. Runs
  on the website, not Kenwood.
metadata:
  short-description: Pipeline step 6/6.
---

# Skill: Publish Live

Commit the exported and cross-linked blog post to the otageLabs website, merge to main via PR, and verify the Vercel production deployment.

This is the final step in the publishing pipeline.  By this point the content has been written, approved, exported, and cross-linked.  This skill handles the git work and deployment verification autonomously.

**This skill runs automatically as part of the publishing pipeline after SEO optimisation.**  It does not wait for operator input at any step.  If invoked manually, it behaves identically.

**Trigger:** Automatic after SEO transition, or user says "publish this post", "send it live", "deploy the blog", or references publishing after a spiderweb run.

---

## Hard constraints

1. **Must be on `development` branch.**  If not, stop.
2. **Build must pass before committing.**  A failed `npm run build` means something is broken — do not commit broken code.
3. **Never force push.**  If push fails, stop and report.
4. **Never delete the `development` branch.**  It is a long-lived base branch.  Do not pass `--delete-branch` to any `gh` command.
5. **Merge conflicts stop the pipeline.**  Do not auto-resolve.  Report and stop.
6. **No variant generation after publish.**  After the content is live, the pipeline stops.  Do not prompt for variants.  Do not auto-start variants.  The operator initiates variant generation separately when ready.

---

## Paths

| Location | Path |
|----------|------|
| Website project root | `/Users/samotage/dev/otagelabs/v0-otage-labs-website-design` |
| Website blog content | `{website}/content/blog/` |
| Live blog URL pattern | `https://otagelabs.com/blog/{url_slug}` |
| Kenwood project root | `/Users/samotage/dev/otagelabs/automations/kenwood` |
| MC surfacing rules | `.claude/rules/mc-surfacing.md` |

---

## Input

No explicit input required for the git/deploy workflow.  The skill detects the blog post from uncommitted changes in the website repo.  However, the Kenwood content piece ID is needed for the status transition.

**Post detection:**
1. If the conversation has just run skill 50 (spiderweb), the post slug is known from context
2. Otherwise, detect from `git status` — look for new/modified files in `content/blog/`
3. If no blog changes exist, stop: "No blog changes found in the website repo.  Run the export and spiderweb skills first."

**Content piece ID resolution (for status transition):**
1. If the user provides a content piece ID explicitly, use it
2. If the blog post's frontmatter contains `kenwood_slug`, extract the ID from the slug (the trailing number after the last hyphen) and verify via `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content get <ID>`
3. If the user provides a title or partial reference, search via `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content list --search <query>` and match on title or slug.  Ask for disambiguation if multiple matches are found.
4. If the conversation has been working on a specific content piece and the ID is unambiguous, use it
5. If the ID cannot be determined, ask: "Which content piece ID should I mark as published?  I can look it up from the post slug if you give me the ID."

---

## Phase 1: Pre-flight

Run from the website project root.

1. **Check branch:** `git branch --show-current`
   - Must be `development`.  If not: halt pipeline.

2. **Fetch remote:** `git fetch origin main`

3. **Check for blog changes:** `git status --short`
   - Look for new or modified files in `content/blog/` or `public/blog/`
   - If no blog-related changes: halt pipeline.

4. **Identify the post:** Find the primary blog post file (new or modified `.md` in `content/blog/`).  Read its frontmatter to extract:
   - `title`
   - `slug` (this is the `url_slug` for the live URL)
   - `date`
   - `published` — if `false`, warn: "Post has `published: false` — it won't appear on the live site.  Continue anyway?"

5. **Flag non-blog changes:** If files outside `content/blog/` and `public/blog/` have been modified, note them.  They will be included in the commit.

---

## Phase 2: Build validation

```bash
cd {website} && npm run build
```

If the build fails:
- **Halt the pipeline.**
- Notify the operator: `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc notify --message "Deployment failed: build error.  Content piece remains at aeo_optimised."`
- Report the error output.

If the build succeeds, continue.

---

## Phase 3: Commit and push

```bash
cd {website}
git add -A
git commit -m "Publish: {title}

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin development
```

If push fails, halt pipeline and report.  Never force push.

---

## Phase 4: Create and merge PR

**Create the PR:**

```bash
gh pr create --base main --head development \
  --title "Publish: {title}" \
  --body "$(cat <<'EOF'
## Summary

Publishes blog post: **{title}**

Blog URL: https://otagelabs.com/blog/{url_slug}

---
Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Capture the PR URL from the output.

**Merge the PR:**

```bash
gh pr merge {PR_URL} --merge
```

Do not pass `--delete-branch`.

If merge fails due to conflicts:
- **Halt the pipeline.**
- Notify the operator: `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc notify --message "Deployment failed: merge conflict.  Content piece remains at aeo_optimised."`
- Report the conflicting files.

---

## Phase 5: Vercel verification

Wait 60 seconds for Vercel to deploy from main.

Take a screenshot:

```bash
npx playwright screenshot --viewport-size "1280,800" \
  --wait-for-timeout 5000 \
  "https://otagelabs.com/blog/{url_slug}" /tmp/blog-published.png
```

Read the screenshot.  Check that:
- The page renders (not a 404 or error page)
- The post title is visible
- The content appears correctly

**If 404 or build-in-progress:** Wait another 60 seconds and retry once.

**If still not live after retry:**
- **Halt the pipeline.**
- Notify the operator: `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc notify --message "Deployment failed: page not live after retry.  Content piece remains at aeo_optimised.  Check https://otagelabs.com/blog/{url_slug} manually."`
- Do not run the status transition.  The content piece remains at `aeo_optimised`.

---

## Phase 5b: Status transition

**Goal:** Move the content piece to `published` in Kenwood.

**Only run this phase if Phase 5 verified the deployment successfully.**  If deployment could not be verified, skip this phase entirely — the content piece status should remain at `aeo_optimised` until the deployment is confirmed.

Run from any directory — the `cd` handles the path:

```bash
cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content transition <ID> --action publish
```

If the transition succeeds:

**MC:** Surface the updated entity:

```bash
cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc focus --entity-type content_piece --entity-id <ID>
```

If the transition fails, report the error but do not fail the publish.  The code is merged and the post is live.  The user can run the transition manually later.

```
Note: Status transition to 'published' failed: {error message}
The deployment itself succeeded — the post is live.
Run `cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood content transition <ID> --action publish` manually to update the status.
```

---

## Phase 6: Report

**MC:** Notify the operator (run from Kenwood project root):

```bash
cd /Users/samotage/dev/otagelabs/automations/kenwood && cli-kenwood mc notify --message "Content piece '{title}' published to otagelabs.com"
```

Print a summary:

```
Published.

  Post:           {title}
  Live URL:       https://otagelabs.com/blog/{url_slug}
  PR:             {PR URL}
  Commit:         {commit hash}
  Deployment:     {verified / unverified — check manually}

Publishing pipeline complete.  The content piece is live.
```

**STOP HERE.**  The publishing pipeline is finished.  Do not prompt for variant generation.  Do not suggest next steps related to variants.  The operator initiates variant generation separately when ready.

---

## Pipeline failure handling (FR8)

If any step in this skill fails:
- **Halt the pipeline immediately.**  Do not proceed to the next step.
- **Notify the operator** via flash banner with the failure reason and the content piece's current state.
- **Do not retry automatically.**  The operator decides whether to retry or investigate.

Specific failure banners:
- Build failure: "Deployment failed: build error.  Content piece remains at aeo_optimised."
- Push failure: "Deployment failed: push error.  Content piece remains at aeo_optimised."
- Merge conflict: "Deployment failed: merge conflict.  Content piece remains at aeo_optimised."
- Deployment not verified: "Deployment failed: page not live after retry.  Content piece remains at aeo_optimised."

---

## Error handling

| Error | Action |
|-------|--------|
| Not on `development` branch | Halt pipeline.  Notify operator. |
| No blog changes | Halt pipeline.  Notify operator. |
| Build fails | Halt pipeline.  Notify operator with error details. |
| Push fails | Halt pipeline.  Notify operator.  Never force push. |
| PR creation fails | Halt pipeline.  Notify operator. |
| Merge conflict | Halt pipeline.  Notify operator with conflicting files.  Do not auto-resolve. |
| Vercel not deployed after retry | Halt pipeline.  Notify operator.  Do not transition status. |

---

## DO NOT

- Force push to any branch
- Delete the `development` branch
- Auto-resolve merge conflicts
- Commit if the build fails
- Skip the build validation step
- Modify blog content — that is the domain of earlier pipeline skills
- Run the website dev server — this skill publishes to production, not preview
- Prompt for variant generation after publishing
- Suggest "now do the variants" or similar next steps
- Auto-start any variant workflow
- Retry failed steps automatically — the operator decides
