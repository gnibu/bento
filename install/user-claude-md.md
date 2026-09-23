# Installing bento

## Principles (always-on) — via user CLAUDE.md import

A plugin ships only *triggered* skills, so the always-on principles ride your user
`CLAUDE.md`. Don't hand-edit — run the installer, which appends the import idempotently
(safe to re-run, honours `$CLAUDE_CONFIG_DIR`):

```
./install.sh
```

It adds `@<bento>/principles/PRINCIPLES.md` as a block at the end of `~/.claude/CLAUDE.md`.
Versioned + synced with the rest of bento; update by pulling the repo.

## Playbooks (triggered) — via the plugin

Dev-load while iterating (no install needed):

```
claude --plugin-dir /absolute/path/to/bento/plugins/bento
```

SKILL.md text hot-reloads; `/reload-plugins` for the rest.

Once extracted to its own GitHub repo (a marketplace), install for real at user scope so
it follows you into every project.

## Scope rule

bento is **personal**. Never commit it into a team repo (e.g. Rose). Keep the install
user-scope, or project-local and gitignored. The `/bento:init` and `/bento:learn` commands
*produce* committed team files (L2) — but bento itself stays yours.
