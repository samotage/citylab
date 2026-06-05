---
name: '60: ship'
description: 'Worker: commit remaining changes, push, create PR'
---

# Hackathon Ship Worker

Make sure everything is committed and pushed, then create a pull request. The lead handles the PR merge.

**You are a worker. Do NOT interact with the user. Return your result and exit.**

---

## Inputs (from lead context)

- `branch` — feature branch (you should already be on it)
- `prd_path` — path to the PRD
- `test_status` — pass/fail summary from test phase
- `smoke_status` — pass/fail summary from smoke phase

---

## Steps

### 1. Commit any uncommitted changes

```bash
git status --porcelain
```

If anything uncommitted:

```bash
git add -A
git commit -m "[hack:ship] final changes for [feature-name]

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 2. Update TASKS.md status

Add a status summary at the bottom of TASKS.md:

```markdown
## Ship Status

- Build: complete
- Tests: [passed / N failures]
- Smoke: [passed / N failures]

### Known Issues
[List any unresolved test or smoke failures, or "None"]
```

```bash
git add TASKS.md
git commit -m "[hack:ship] final status update

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 3. Move PRD to done

```bash
mkdir -p $(dirname [prd_path])/done
git mv [prd_path] $(dirname [prd_path])/done/$(basename [prd_path])
git commit -m "[hack:done] move [prd-name] to done

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4. Push

```bash
git push -u origin [branch]
```

### 5. Create PR

```bash
gh pr create --title "feat(hack-[feature-name]): implementation" --body "$(cat <<'EOF'
## Summary

Hackathon implementation for [feature-name].

## Testing

- Tests: [test_status]
- Smoke: [smoke_status]

## Known Issues

[List from TASKS.md Ship Status, or "None"]
EOF
)" --base master
```

Capture the PR URL and PR number from the output.

### 6. Return result

```yaml
ship_result:
  status: success
  branch: [branch]
  commit: [HEAD SHA]
  pr_url: [PR URL]
  pr_number: [PR number]
  known_issues: [count of unresolved failures]
```
