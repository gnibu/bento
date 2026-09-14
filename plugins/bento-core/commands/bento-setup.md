---
description: Wire bento into the current environment — always-on principles (user CLAUDE.md) and, in a repo, the Codex pointer block (AGENTS.md). Idempotent; run once after installing bento.
---

# bento setup

Marketplace install gives Claude the **playbooks**. This command wires the two things it
doesn't: the always-on **principles** (for Claude) and the **Codex pointer block** (for
AGENTS.md-based agents). Both steps are idempotent.

Locate bento's root — the parent of the `plugins/` dir holding this plugin
(`${CLAUDE_PLUGIN_ROOT}/../..`), or `./.bento` if vendored as a submodule.

1. **Principles → user `CLAUDE.md`:** run `bash <bento>/install.sh`. It appends
   `@<bento>/principles/PRINCIPLES.md` to `~/.claude/CLAUDE.md` (honours `$CLAUDE_CONFIG_DIR`),
   only if absent. Principles load next session.

2. **Codex block → repo `AGENTS.md`** (only when working in a repo that has one): run
   `python3 <bento>/install/bento-agents.py ./AGENTS.md`. It adds or updates a
   marker-bounded pointer block so Codex reaches the same `.bento/` files. Edit the
   `AGENTS.md` source, never a `CLAUDE.md` symlink. Skip this step outside a repo.

Then confirm to the user what was wired, and that step 2 is a **committed** change (review
before landing in a team repo).
