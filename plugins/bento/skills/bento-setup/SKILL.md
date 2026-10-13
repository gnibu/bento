---
name: bento-setup
description: Wire bento's always-on principles into Claude Code (CLAUDE.md import) and Codex (AGENTS.md block), and migrate an old submodule/plugin install. Idempotent; run after `npx skills add gnibu/bento` and after each update. Args — none = interactive; `--yes` = defaults; `--purge` = unwire.
---

# bento setup

`npx skills` installs the playbooks. This skill wires the one thing a skill can't carry:
the always-on principles in `PRINCIPLES.md` (next to this file). Every step is idempotent.
Report failures instead of claiming setup completed.

**Repo layer first.** Read the repo's `AGENTS.md`/`CLAUDE.md` and, if it exists, the
overlay `.agents/bento/bento-setup.md` at the repo root; follow it under the
[overlay rules](../bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).

`<skill>` is this skill's directory. Run from the consumer repo root.

## Scope

Match where bento's skills are installed:

- **project** — `.agents/skills/bento-setup/` or `.claude/skills/bento-setup/` exists in the
  repo (committed with `skills-lock.json`, so the repo pins its bento version).
- **global** — `~/.agents/skills/bento-setup/` or `<claude-dir>/skills/bento-setup/`.

`<claude-dir>` is `$CLAUDE_CONFIG_DIR` if set, else `~/.claude`, resolved to an absolute
path (npx skills uses the same rule; `CLAUDE.md` imports don't expand variables).

Both present → ask (`--yes`: project). Neither → stop and tell the user to run
`npx skills add gnibu/bento --skill '*'` (add `-g` for global).

To update, tell the user to rerun that same command, not `npx skills update`: update refreshes
only installed skills, so a skill added to bento since (one an updated playbook calls) never
lands.

## Apply

1. **Migrate** if any legacy install is detected (next section). Do it first.
2. **Claude principles.** Ensure the target `CLAUDE.md` contains the import line, appended as
   its own block at the end (imports mid-file are disallowed):

   ```
   # bento (always-on principles)
   @<import>
   ```

   - project: `./CLAUDE.md`, import `.claude/skills/bento-setup/PRINCIPLES.md`
   - global: `<claude-dir>/CLAUDE.md`, import `<claude-dir>/skills/bento-setup/PRINCIPLES.md`

   Skip if the line is present. Check the import target exists; if it doesn't, Claude
   wasn't an install target (`npx skills add ... -a claude-code`).
3. **Codex principles.** `python3 "<skill>/scripts/agents_block.py" <AGENTS.md>` with
   `./AGENTS.md` (project) or `${CODEX_HOME:-~/.codex}/AGENTS.md` (global). The block is
   marker-bounded and distilled, so rerun it after each bento update. Edit the `AGENTS.md`
   source, never a `CLAUDE.md` symlink.
4. **Verify.** Show the diff of each file touched. Start a fresh Claude/Codex session and
   confirm the `bento-*` skills are listed (Claude: `/bento-`; Codex: `$bento-`). Don't claim
   a running session reloaded anything.

Project-scope changes (`CLAUDE.md`, `AGENTS.md`, `.agents/`, `.claude/skills/`,
`skills-lock.json`) are for the user to review and commit. Setup, migrate and purge never
create or delete the repo's overlays in `.agents/bento/`.

## Migrate from the submodule/plugin install

Detect each legacy piece; remove only what is present. Report each removal.

1. **Submodule** (`.bento` in `.gitmodules`):
   `git submodule deinit -f .bento && git rm -f .bento`, then
   `rm -rf "$(git rev-parse --git-dir)/modules/.bento"`. Use `--git-dir`, never
   `--git-common-dir`: from a linked worktree the latter is the main checkout's submodule
   repository, still used by its checkout. Remove
   `git submodule update --init .bento` from any setup script (e.g. Conductor's).
2. **Claude plugin and marketplace** (`claude plugin list` shows `bento@bento`,
   `bento-core@bento` or `bento-forge@bento`): `claude plugin uninstall <id>` for each, then
   `claude plugin marketplace remove bento`. This is machine-wide: confirm first, since other
   repos on this machine lose the plugin too (install bento globally, or migrate them).
   Remove `bento` from committed `extraKnownMarketplaces` / `enabledPlugins` in `.claude/settings.json`.
3. **Old hooks.** Delete `SessionStart`/`Stop` handlers whose command mentions
   `.bento/plugins/` from `.claude/settings.json`, `.claude/settings.local.json`,
   `<claude-dir>/settings.json` and `${CODEX_HOME:-~/.codex}/hooks.json`, and the
   `# bento:hooks:start` … `# bento:hooks:end` block from `.codex/config.toml`. Keep unrelated
   handlers. Then `rm -f ~/.bento/update-reminder` and remove `~/.bento` if empty.
4. **Codex links.** Delete symlinks in `.codex/skills/` whose target contains `/.bento/`.
5. **Old principles import.** Remove the `# bento (personal agent kit — always-on principles)`
   heading and its `@…/principles/PRINCIPLES.md` line from `<claude-dir>/CLAUDE.md`.
   Apply step 2 writes the new one. The `AGENTS.md` block keeps its markers, so Apply step 3
   rewrites it in place.

## Purge (`--purge`)

1. Remove the `# bento (always-on principles)` block from the `CLAUDE.md` for the scope.
2. Remove the `<!-- bento:start -->` … `<!-- bento:end -->` block from the `AGENTS.md`,
   keeping unrelated instructions.
3. The skills themselves: `npx skills remove` each `bento-*` skill, same scope (`-g` for global).
