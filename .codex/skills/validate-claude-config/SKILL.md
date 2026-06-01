---
name: validate-claude-config
description: Validate a project's .claude directory structure — symlinks, rules, shared
  resources, and custom rules alignment. Use this when checking if a project's .claude
  configuration follows the otageLabs convention, when setting up a new project, or
  when debugging agent tool/rule resolution issues.
allowed-tools: Read, Glob, Bash(ls *), Bash(readlink *), Bash(test *), Bash(file *)
metadata:
  short-description: Validate a project's.
---

# Validate .claude Configuration

You are validating the `.claude` directory structure for the current working directory. This project may or may not have custom rules. Your job is to inspect the filesystem, determine which configuration pattern is in use, run every check, and output a structured JSON result.

## Input

The prompt invoking this skill may include a `custom_rules_dir` parameter (e.g., `custom_rules_dir=headspace_rules`). This is the name of the project-specific rules directory at the project root.

- If `custom_rules_dir` is provided and non-empty: the project SHOULD be Config B (selective symlinks with a real rules directory).
- If `custom_rules_dir` is not provided or empty: the project may be Config A (full symlink) or Config C (self-contained). Detect which.

## Configuration Patterns

There are three valid patterns. Determine which one applies BEFORE running checks.

### Config A — Full Directory Symlink

The entire `.claude` directory is a symlink to `otl_support/python/.claude/`. No custom rules. Simplest configuration.

```
.claude -> ../../otl_support/python/.claude/     # (depth varies by project location)
```

**Detection:** `.claude` itself is a symlink. Run `test -L .claude`.

### Config B — Selective Symlinks (with or without Custom Rules)

`.claude` is a real directory. Individual items inside are symlinks to `otl_support/python/.claude/`. The `rules/` subdirectory is real (not a symlink) and contains a symlink to shared core rules, plus optionally a symlink to project-specific rules.

```
.claude/                          # real directory
  AVAILABLE_MAGIC.md  ->  otl_support/python/.claude/AVAILABLE_MAGIC.md
  commands            ->  otl_support/python/.claude/commands
  settings.json       ->  otl_support/python/.claude/settings.json
  skills              ->  otl_support/python/.claude/skills
  rules/                          # real directory
    core              ->  otl_support/python/.claude/rules/core
    {custom_rules_dir} -> {project_root}/{custom_rules_dir}/    # only if custom rules exist
```

**Detection:** `.claude` is a real directory AND at least one item inside (e.g., `settings.json`, `commands`, `skills`) is a symlink to a path containing `otl_support`. Run `readlink .claude/settings.json` — if it resolves to a path containing `otl_support`, this is Config B.

### Config C — Self-Contained

`.claude` is a real directory with no symlinks to `otl_support`. The project manages its own configuration independently. This is valid for projects outside the shared infrastructure.

**Detection:** `.claude` is a real directory AND no symlinks inside point to `otl_support`.

## Checks to Run

Run ALL applicable checks. Use `ls -la` to inspect symlink targets. Use `readlink` to resolve symlink destinations. Use `test -L` to check if a path is a symlink. Use `test -d` to check if a path is a directory. Use `test -f` to check if a path is a file.

### Universal Checks (all patterns)

1. **`.claude` exists** — `test -d .claude` (following symlinks) or `test -L .claude`
2. **`settings.json` accessible** — `test -f .claude/settings.json` (following symlinks)
3. **`rules/` accessible** — `test -d .claude/rules/` (following symlinks)
4. **`rules/core/` accessible** — `test -d .claude/rules/core/` (following symlinks)
5. **`rules/core/ai-guardrails.md` exists** — `test -f .claude/rules/core/ai-guardrails.md`
6. **`commands/` accessible** — `test -d .claude/commands/` (following symlinks)
7. **`skills/` accessible** — `test -d .claude/skills/` (following symlinks)

### Config A Checks (full symlink)

8. **`.claude` symlink resolves** — `readlink .claude` returns a path, and that path exists
9. **Symlink target is `otl_support/python/.claude/`** — the resolved path ends with `otl_support/python/.claude` or similar

### Config B Checks (selective symlinks)

10. **`.claude` is NOT a symlink** — `test -L .claude` should FAIL (it must be a real directory)
11. **`settings.json` is a symlink to otl_support** — `readlink .claude/settings.json` resolves to a path containing `otl_support/python/.claude/settings.json`
12. **`commands` is a symlink to otl_support** — `readlink .claude/commands` resolves to a path containing `otl_support/python/.claude/commands`
13. **`skills` is a symlink to otl_support** — `readlink .claude/skills` resolves to a path containing `otl_support/python/.claude/skills`
14. **`rules/` is NOT a symlink** — `test -L .claude/rules` should FAIL (must be a real directory)
15. **`rules/core` is a symlink to otl_support** — `readlink .claude/rules/core` resolves to a path containing `otl_support/python/.claude/rules/core`

### Config B Custom Rules Checks (only when `custom_rules_dir` is provided)

Skip checks 16-19 entirely if `custom_rules_dir` was not provided in the prompt. A Config B project without custom rules is valid.

16. **Custom rules symlink exists** — `test -L .claude/rules/{custom_rules_dir}` should succeed
17. **Custom rules symlink resolves** — `readlink .claude/rules/{custom_rules_dir}` returns a valid path that exists
18. **Custom rules directory at project root exists** — `test -d {custom_rules_dir}` in the project root
19. **Custom rules directory contains .md files** — `ls {custom_rules_dir}/*.md` returns at least one file

### Cross-Reference Checks

20. **Config mismatch: custom_rules_dir set but Config A** — if `custom_rules_dir` is provided but `.claude` is a full symlink, this is a misconfiguration. The project needs to be converted to Config B.
21. **Config mismatch: custom_rules_dir empty but Config B with custom rules symlink** — if no `custom_rules_dir` was provided but `.claude/rules/` contains a symlink to a `*_rules` directory, the project metadata is out of date.

## Execution

1. Read the `custom_rules_dir` value from the prompt (may be empty/absent).
2. Detect the configuration pattern (A, B, or C).
3. Run all universal checks.
4. Run pattern-specific checks.
5. Run cross-reference checks.
6. Compile results.

## Output

Your ENTIRE response must be a single JSON object. No text before it. No text after it. No markdown fencing. No explanation. The response will be parsed with `json.loads()` — anything other than valid JSON will break the parser.

Schema:

```
{
  "project_path": "/absolute/path/to/project",
  "custom_rules_dir": "headspace_rules" | null,
  "pattern": "full_symlink" | "selective_symlinks" | "self_contained",
  "passed": true | false,
  "checks": [
    {
      "id": 1,
      "name": ".claude exists",
      "passed": true | false,
      "detail": "optional detail string — only present when check fails or has useful context"
    }
  ],
  "summary": "7/7 checks passed." | "5/7 checks passed. 2 issues: broken symlink at rules/core, missing custom rules directory."
}
```

Rules for the output:
- `passed` is `true` only if ALL checks passed
- `checks` includes every check that was run (skip checks not applicable to the detected pattern)
- `detail` is present on failed checks (explaining what's wrong) and optionally on passed checks (showing resolved path)
- `summary` is a human-readable one-liner: count of passed/total, plus a brief list of issues if any failed
- Do NOT include checks that don't apply to the detected pattern (e.g., don't run Config B checks on a Config A project)
