---
name: /available-magic
id: available-magic
category: Utility
description: Instantly display all available skills, commands, and plugins
---

# /available-magic Command

**Goal:** Instantly display the pre-generated inventory of skills and commands.

**Command name:** `/available-magic`

---

## Prompt

Read the file `.claude/AVAILABLE_MAGIC.md` and display its contents to the user.

**If the file exists:** Display the full contents as-is. That's it — no scanning, no processing.

**If the file does NOT exist:** Tell the user:

> No inventory found. Run `/generate-magic` first to scan and generate the list.

---

**/available-magic command complete.**
