---
description: Wire bento into the current environment — principles (user CLAUDE.md), the Codex pointer block (AGENTS.md), and the learn hooks (Stop + SessionStart). Idempotent; run once after installing bento.
---

# bento setup

Marketplace install gives Claude the **playbooks**. This command wires the three things it
doesn't: the always-on **principles**, the **Codex pointer block**, and the **learn hooks**.
All steps are idempotent — safe to re-run.

Locate bento's root — the parent of the `plugins/` dir holding this plugin
(`${CLAUDE_PLUGIN_ROOT}/../..`), or `./.bento` if vendored as a submodule.

1. **Principles → user `CLAUDE.md`:** run `bash <bento>/install.sh`. It appends
   `@<bento>/principles/PRINCIPLES.md` to `~/.claude/CLAUDE.md` (honours `$CLAUDE_CONFIG_DIR`),
   only if absent. Principles load next session.

2. **Codex block → repo `AGENTS.md`** (only in a repo that has one): run
   `python3 <bento>/install/bento-agents.py ./AGENTS.md`. Marker-bounded, so re-running
   updates in place. Edit the `AGENTS.md` source, never a `CLAUDE.md` symlink. This is a
   **committed** change — review before landing in a team repo.

3. **Learn hooks (Stop + SessionStart)** — wire both, pointing at the vendored scripts
   (`<bento>/scripts/session-stop.sh` and `session-start.sh`; see
   `<bento>/plugins/bento-forge/references/stop-hook.md`). Wire them **personally** so they
   never fire for coworkers who didn't opt in:
   - **Claude → `.claude/settings.local.json`** (gitignored). Merge a `hooks` block adding
     `Stop → session-stop.sh` and `SessionStart → session-start.sh`; don't overwrite existing
     keys. Use the `${CLAUDE_PROJECT_DIR}` prefix.
   - **Codex → `.codex/config.toml`** with `[features].hooks = true`, adding `[[hooks.Stop]]`
     and `[[hooks.SessionStart]]` (command `bash "$(git rev-parse --show-toplevel)/.bento/…"`).
     Codex has no gitignored per-project config, so if this repo commits `.codex/config.toml`,
     tell the user it's a committed/team change and let them decide.
   - Skip any hook already wired (idempotent). Bank is silent + always-on; a PR only opens on
     the user's yes at SessionStart, or set `BENTO_IMPROVE_AUTO_PR=1` on the Stop command for
     hands-off.

Then confirm what was wired, flagging which steps touched **committed** files.
