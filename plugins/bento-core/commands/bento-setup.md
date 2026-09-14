---
description: Wire bento's always-on principles into your user CLAUDE.md (run once after installing bento). Idempotent.
---

# bento setup

Marketplace install gives you the **playbooks** (triggered skills), but the **always-on
principles** aren't a plugin surface — they need an `@import` in your user `CLAUDE.md`. This
command adds it, once.

Do this:

1. Find bento's `install.sh`. It sits at the bento root — the parent of the `plugins/`
   directory that contains this plugin. From this plugin's root (`${CLAUDE_PLUGIN_ROOT}`),
   that's typically `${CLAUDE_PLUGIN_ROOT}/../../install.sh`. If bento is vendored in the
   repo instead (submodule), it's `./.bento/install.sh`.
2. Run it: `bash <path>/install.sh`. It idempotently appends
   `@<bento>/principles/PRINCIPLES.md` as a block at the end of `~/.claude/CLAUDE.md`
   (honours `$CLAUDE_CONFIG_DIR`), and is safe to re-run.
3. Confirm the import line is present in the user `CLAUDE.md`, then tell the user the
   principles load next session.

If `install.sh` can't be located, fall back to appending the import manually: resolve the
absolute path to bento's `principles/PRINCIPLES.md` and, only if that exact `@import` line
is not already in `~/.claude/CLAUDE.md`, append a new block:

```
# bento (shared agent operating layer — always-on principles)
@<abs>/principles/PRINCIPLES.md
```
