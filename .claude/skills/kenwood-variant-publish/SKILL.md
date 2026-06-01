---
name: kenwood-variant-publish
description: "Publish approved content variants to their platforms and verify every published URL is live with correct content and working links. Run after variant generation and review. The post-and-validate step of the variant pipeline."
---

# Skill: Publish Variants

Publish approved content variants to their configured platforms, verify each published URL is live with correct content and working links, and transition variant status to deployed.

This is the post-generation step.  Generation (the `kenwood-variant-generate` skill) produces `draft` variants.  The operator reviews and approves them.  This skill handles everything after approval: publish, verify, transition.

**Trigger:** Operator says "publish the variants", "post these variants", "deploy the variants", "send them live", or references publishing after variant review/approval.  Also: "publish variant <id>", "publish the LinkedIn variant".

---

## References

- **Shared structure:** `../kenwood-variant-generate/variant-skill-structure.md` -- blog_url rule, CLI commands
- **MC surfacing:** `.claude/rules/mc-surfacing.md`

---

## Phase 1: Pre-flight

**Goal:** Identify what to publish, check credentials, confirm with operator.

1. List variants for the content piece:
   ```bash
   cli-kenwood variants list --content-id <id>
   ```

2. Filter to publishable variants:
   - `approved` status: ready to publish
   - `draft` status: report to operator -- "These variants are still in draft.  Approve them first, or say 'publish anyway' to proceed."
   - `deployed` status: already published -- skip unless operator says to re-publish
   - `rejected` / `cancelled` / `failed`: skip

3. Read content piece metadata for blog_url:
   ```bash
   cli-kenwood content get <id>
   ```
   Extract `blog_url`.  This is the canonical URL for link verification.  **Never construct URLs from `slug`.**

4. Check platform credentials:
   ```bash
   flask publish platforms --format json
   ```
   Flag any platforms where credentials are missing, expired, or untested.

5. Present the publish plan to operator:
   - List each variant: platform, type, character count, status
   - Flag credential issues
   - Flag Instagram as manual publish
   - Wait for operator confirmation

**Gate:** Operator confirms the publish plan.  Do not auto-publish.

---

## Phase 2: Publish (sequential, per platform)

For each variant in the confirmed plan:

1. **Execute publish:**
   ```bash
   cli-kenwood publish <id> --platform-ids <platform_id>
   ```

2. **Check immediate result.**  If the publish command returns an error:
   - Report the error immediately: "FAIL: <platform> publish error: <message>"
   - Do NOT transition variant status
   - Continue to next platform

3. **Capture published URL:**
   ```bash
   flask publish status --content-id <id> --format json
   ```
   Extract the published URL for this platform.


4. **Instagram exception:**  Instagram has no API credentials.  Report: "Instagram is manual.  Copy the caption from the variant review UI and post via the Instagram app.  Set link-in-bio URL to: `<blog_url with UTM>`."  Skip to Phase 3 for blog link verification only.

**One platform at a time.**  Failures on one platform do not halt the others, but each failure is reported immediately so the operator can decide.

---

## Phase 3: Validate (per published variant)

For each successfully published variant:

### 3a. Published URL check

```bash
curl -sL -o /dev/null -w "%{http_code}" "<published_url>"
```

Must return `200`.  The `-L` flag follows redirects.

- `200`: pass -- proceed to link check
- `404`: **FAIL** -- report immediately, do NOT transition status
- `401`/`403`: platform may require auth to view -- note as "unverifiable, check manually" and proceed
- Other errors: report and do NOT transition status

### 3b. Blog link verification

Extract the blog URL from the variant body or `format_metadata.utm_params`.  Construct the full URL with UTM parameters using `blog_url` from Phase 1.

```bash
curl -sL -o /dev/null -w "%{http_code}" "<blog_url_with_utm>"
```

Must return `200`.  If `404`:
- **FAIL** -- report immediately: "Blog link in <platform> variant returns 404: <url>"
- Do NOT transition variant status
- This is the specific failure this skill exists to prevent

### 3c. WordPress content check

For WordPress variants only (accessible via public URL):

```bash
curl -sL "<published_url>" | head -100
```

Verify the title appears in the page content.  If the page is a 404 or the title is missing, report the failure.

### 3d. Transition status

**Only if both URL check AND blog link check passed:**

```bash
cli-kenwood variants transition <variant_id> --action deployed
```

If either check failed, the variant stays at its current status.  The operator must fix the issue and re-publish.

---

## Phase 4: Report

Present a summary table:

```
Published variants for "{title}":

| Platform   | Type       | Status    | Live URL           | Blog Link | Verified |
|------------|------------|-----------|--------------------|-----------|---------+|
| LinkedIn   | post       | deployed  | linkedin.com/...   | 200       | yes      |
| X          | thread     | failed    | (publish error)    | --        | no       |
| WordPress  | article    | deployed  | wordpress.com/...  | 200       | yes      |
| BlueSky    | post       | deployed  | bsky.app/...       | 200       | yes      |
| Instagram  | caption    | manual    | --                 | 200       | pending  |
```

Notify via MC:
```bash
cli-kenwood mc notify --message "Published {n}/{total} variants for '{title}'. {verified_count} verified live."
```

Surface:
```bash
cli-kenwood mc focus --entity-type content_piece --entity-id <id>
```

**If any variants failed:** Summarise failures and suggest next steps:
- Credential errors: "Refresh <platform> credentials with `flask publish test-credentials --platform-id <id>`"
- 404 errors: "Check the URL construction.  The blog_url from CLI is: <url>"
- Publish retry: "Retry with `flask publish retry --publication-id <id>`"

---

## Hard Constraints

1. **Never transition to deployed without verification.**  A published URL that returns 404 is not "deployed."  The status must reflect reality.
2. **Verify every blog link.**  Every URL in a published variant pointing to the otageLabs blog must return 200.  This is the specific failure this skill exists to prevent.
3. **Report failures immediately.**  Each failure is reported as it's discovered.  Don't batch failures into the summary.
4. **Use `blog_url` for all link verification.**  Never verify links constructed from `slug`.  See `variant-skill-structure.md` Blog URL Construction.
5. **Sequential publishing.**  One platform at a time.  Catch and report failures before moving to the next.
6. **Operator confirms before publishing.**  Present the plan, wait for confirmation.  No auto-publish.

---

## Error Handling

| Error | Action |
|-------|--------|
| No approved/publishable variants | Report and stop |
| Platform credentials missing/expired | Report which platforms; publish the rest |
| Publish command fails | Report error, skip platform, continue to next |
| Published URL returns 404 | Report immediately, do NOT transition status |
| Blog link returns 404 | Report immediately, do NOT transition status |
| Published but no URL in status | Report: "Published but no URL captured. Check <platform> manually." |
| Variant transition fails | Report error but note publish succeeded -- operator can transition manually |

---

## DO NOT

- Mark a variant as deployed without verifying the live URL returns 200
- Skip blog link verification
- Auto-publish without operator confirmation
- Retry failed publishes without operator instruction -- use `flask publish retry` only when asked
- Construct verification URLs from `slug` -- always use `blog_url` or the published URL from status
- Halt the full publish set because one platform failed -- report the failure and continue
- Conflate "written to Kenwood" with "published to platform" -- these are different actions
