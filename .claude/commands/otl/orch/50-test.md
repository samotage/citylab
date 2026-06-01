---
name: '50: test'
description: 'Worker: run targeted tests, fix failures if needed'
---

# Hackathon Test Worker

Run tests against the code that was just built. Fix what you can. Report what you can't.

**You are a worker. Do NOT interact with the user. Return your result and exit.**

---

## Inputs (from lead context)

- `prd_path` — path to the PRD file
- `branch` — feature branch (you should already be on it)
- `attempt` — 1 or 2 (the lead manages retry logic)
- `build_notes` — notes from the build worker (may contain setup instructions)

---

## Steps

### 1. Discover the test setup

```bash
# Check what exists
ls pytest.ini pyproject.toml setup.cfg jest.config* vitest.config* Makefile 2>/dev/null
ls tests/ test/ __tests__/ 2>/dev/null | head -20
grep -r "test" package.json 2>/dev/null | head -5
```

If NO test infrastructure exists and this is attempt 1:
- Write basic tests for the core functionality (the "Done When" items from the PRD)
- Use whatever framework fits the project's stack
- Commit the test files

### 2. Run targeted tests

Check what was built:

```bash
git diff --name-only [base_branch]...HEAD
```

Run tests relevant to those files. Adapt to the stack:

```bash
pytest tests/ -x -v                    # Python
npm test                               # Node
go test ./...                          # Go
cargo test                             # Rust
```

### 3. Evaluate results

**All pass:** Return success.

**Failures on attempt 1:**
1. Read the failure output
2. Fix the code (not the tests — unless the test is wrong)
3. Commit the fix:
   ```bash
   git add -A
   git commit -m "[hack:test-fix] fix: [what you fixed]

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```
4. Return with `status: fixed`

**Failures on attempt 2:** Don't fix again. Log what's broken and return.

### 4. Return result

```yaml
test_result:
  status: [passed|fixed|failed]
  tests_run: [N]
  tests_passed: [N]
  tests_failed: [N]
  failures:
    - test: [test name]
      error: [short description]
  notes: [anything relevant]
```
