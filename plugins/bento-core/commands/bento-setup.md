---
description: Wire bento into the current environment — principles (user CLAUDE.md), the Codex pointer block (AGENTS.md), and the learn hooks (Stop + SessionStart). Idempotent; run once after installing bento. Args — none = interactive; `--yes` = batch defaults; `--purge` = unwire.
---

# bento setup

Marketplace install gives Claude the **playbooks**. This command wires the three things it
doesn't: the always-on **principles**, the **Codex pointer block**, and the **learn hooks**.
All steps are idempotent — safe to re-run.

## Modes

- **Interactive (default, no args):** ask the two choices below, then wire.
- **Batch (`--yes` / non-interactive / no TTY):** skip the questions, apply the **defaults**
  (hook scope = personal, auto-PR = off). For headless/CI.
- **Purge (`--purge`):** unwire everything this command adds and stop (see Purge).

## Ask first (interactive only)

Use the host's question prompt for these; in batch mode take the default:

1. **Hook scope** — where do the learn hooks live?
   - **Personal** *(default)* → gitignored `.claude/settings.local.json` (+ your `~/.codex/config.toml`). Only you get them.
   - **Committed / team** → committed `.claude/settings.json` + `.codex/config.toml`. Every teammate's session then banks (a background reflection each) — only choose this if the team agreed.
2. **Auto-PR** — when a learning ripens, open the PR automatically?
   - **Off** *(default)* → you're prompted at next SessionStart and approve. Recommended.
   - **On** → set `BENTO_IMPROVE_AUTO_PR=1` on the Stop command (fully hands-off).

Locate bento's root — the parent of the `plugins/` dir holding this plugin
(`${CLAUDE_PLUGIN_ROOT}/../..`), or `./.bento` if vendored as a submodule.

1. **Principles → user `CLAUDE.md`:** run `bash <bento>/install.sh`. It appends
   `@<bento>/principles/PRINCIPLES.md` to `~/.claude/CLAUDE.md` (honours `$CLAUDE_CONFIG_DIR`),
   only if absent. Principles load next session.

2. **Codex block → repo `AGENTS.md`** (only in a repo that has one): run
   `python3 <bento>/install/bento-agents.py ./AGENTS.md`. Marker-bounded, so re-running
   updates in place. Edit the `AGENTS.md` source, never a `CLAUDE.md` symlink. This is a
   **committed** change — review before landing in a team repo.

3. **Learn hooks (Stop + SessionStart)** — wire both at the vendored scripts
   (`<bento>/scripts/session-stop.sh`, `session-start.sh`; see
   `<bento>/plugins/bento-forge/references/stop-hook.md`), into the location the **scope**
   answer picked:
   - **Personal** → Claude: gitignored `.claude/settings.local.json` (merge a `hooks` block,
     `${CLAUDE_PROJECT_DIR}` prefix, don't overwrite existing keys). Codex: your
     `~/.codex/config.toml` (Codex has no gitignored per-project file), guarded so it no-ops
     where `.bento` is absent.
   - **Committed** → Claude: `.claude/settings.json`. Codex: `.codex/config.toml` with
     `[features].hooks = true`.
   - If **auto-PR = on**, prefix the Stop command with `BENTO_IMPROVE_AUTO_PR=1 `.
   - Skip any hook already wired (idempotent).

Then confirm what was wired, flagging which steps touched **committed** files.

## Purge (`--purge`)

Unwire everything this command adds, then stop — the inverse of setup, idempotent:

1. Remove the `@…/principles/PRINCIPLES.md` import block from `~/.claude/CLAUDE.md`.
2. Remove the `<!-- bento:start -->…<!-- bento:end -->` block from `./AGENTS.md`.
3. Remove the bento `Stop`/`SessionStart` hooks (the ones pointing at `.bento/…`) from
   `.claude/settings.json`, `.claude/settings.local.json`, `~/.codex/config.toml`, and
   `.codex/config.toml` — leaving any non-bento hooks untouched.

Purge does **not** remove the `.bento` files/submodule or uninstall the plugin — that's a
`git submodule deinit` / `claude plugin uninstall`, left to the user.
