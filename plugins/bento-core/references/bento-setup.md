# bento setup

Set up Bento for the requested agents. Claude uses a marketplace and plugin cache; Codex
uses native skill links. Both use shared principles and the forge learning hooks.
All installer steps are idempotent. Report failures instead of claiming setup completed.

## Bootstrap before this entrypoint is available

From the consumer repo, run `git submodule update --init .bento`, then:

- Claude: `bash .bento/install.sh`, then start a fresh Claude session.
- Codex: `bash .bento/install.sh --codex`, then start a fresh Codex session and invoke
  `$bento-core:bento-setup`. No Claude CLI is needed for Codex-only setup.

Committed Claude marketplace/enablement settings alone do not prove plugins are installed.
The shell installer checks the actual machine-local CLI state before installing them.

## Modes and choices

- **Interactive:** establish which agents to configure and use the host's question prompt
  for scope and auto-PR choices that the user has not already specified.
- **Batch (`--yes` / non-interactive / no TTY):** use defaults: Claude hooks = project,
  Codex hooks = personal, auto-PR = off. Configure the current agent unless both are requested.
- **Purge (`--purge`):** go directly to Purge; do not run installation steps first.

Scope choices:

- **Claude project (default):** committed `.claude/settings.json`. Configure once, commit,
  and new worktrees inherit it, including teammates' checkouts. No per-worktree local file.
- **Claude personal:** user `settings.json` under `${CLAUDE_CONFIG_DIR:-~/.claude}`. Hooks are
  guarded to this repository's shared Git directory, so all its worktrees are covered while
  unrelated projects are skipped. This replaces repeated `.claude/settings.local.json` setup.
- **Codex personal (default):** `${CODEX_HOME:-~/.codex}/hooks.json`; guarded to no-op in repos
  without the vendored scripts. **Codex team:** committed `.codex/config.toml` instead.
- **Auto-PR:** off by default (bank now, offer ripe learnings next session). Enable only when
  requested, by passing `--auto-pr` to the hook installers.

Choose one hook scope per agent. Hooks from multiple locations are additive. Preserve
unrelated hooks; report obsolete hand-written Bento hooks for removal to avoid duplicates.

## Locate the source

Run from the consumer repo root. Prefer its initialized `.bento` submodule. For Claude
marketplace-only installs, use `claude plugin marketplace list --json` (`installLocation`)
to find the checkout containing `install.sh` and `principles/`. Do not assume
`${CLAUDE_PLUGIN_ROOT}/../..` is Bento: the versioned plugin cache lacks the root installer.
The steps below use `<bento>` for that source checkout.

## Apply

1. **Claude plugins + principles** (Claude only): run `bash <bento>/install.sh` (Python 3.9+).
   In vendored mode it checks marketplace/plugin lists, registers Bento if absent, and
   installs/enables both plugins at user scope. An existing principles import does not skip
   this check. Commands are non-interactive with a five-minute timeout each; allow enough
   tool time and stop/report errors.

   Directory registration persists an absolute path. From worktrees, the installer uses
   the main checkout's initialized `.bento` for marketplace and principles; both copies must
   be clean and at the same commit. Missing/mismatched copies stop with repair instructions.
   Existing valid marketplace sources (including GitHub) are preserved and reported. Stale
   or worktree-based registrations require explicit repair. Setup does not update existing
   caches to the submodule pin; see README **Update**.

2. **Codex native skills + hooks** (Codex, vendored mode, Python 3.11+): run
   `python3 <bento>/install/bento-codex.py --repo . --hooks personal`, or `--hooks team`.
   Append `--auto-pr` only when chosen. It links every core skill and forge `bento-improve`
   into `.codex/skills/`, preflights collisions, merges hooks, and reports each change.
   Skills appear as `bento-core:<name>` and `bento-forge:bento-improve`; links follow the
   current checkout's submodule pin. Do not hand-write the links or Codex hook configuration.

3. **Always-on principles and legacy fallback:** run
   `python3 <bento>/install/bento-agents.py ./AGENTS.md`. The marker-bounded block updates in
   place. Edit the `AGENTS.md` source, never a `CLAUDE.md` symlink. Review this committed change.

4. **Claude hooks** (Claude, vendored mode): run
   `python3 <bento>/install/bento-claude-hooks.py --repo . --scope project`, or `--scope personal`.
   Append `--auto-pr` only when chosen. The installer preserves unrelated settings and hook
   handlers. Commit project settings so future worktrees inherit the hooks. Do not create a
   new `.claude/settings.local.json` in each worktree.

Both hook installers use `.bento/plugins/bento-forge/scripts/session-start.sh` and
`session-stop.sh`, resolved from the session's Git root and guarded when scripts are absent.
Keep `.bento` initialized in each checkout (`git submodule update --init .bento`). For
marketplace-only Claude hook wiring, use the installed forge script paths described in
`<bento>/plugins/bento-forge/references/stop-hook.md`.

## Verify

Report what changed and which files are committed. For Claude, report the marketplace
source, verify `claude plugin marketplace list` and `claude plugin list`, then restart and
confirm the 14 core playbooks plus setup. For Codex, **start a fresh Codex session after
setup**, and verify the names with `codex debug prompt-input` from the consumer repo.
If Codex requests hook review, use `/hooks`. Respect `features.hooks = false`; do not override
it silently. Do not claim that a running session reloaded skills or that a configured Stop
hook has already executed.

## Purge

1. Remove the Bento principles import block from the user `CLAUDE.md` (honor
   `$CLAUDE_CONFIG_DIR`) and the `<!-- bento:start -->` … `<!-- bento:end -->` block from
   `AGENTS.md`, preserving unrelated instructions.
2. For Codex, run `python3 <bento>/install/bento-codex.py --repo . --purge --hooks personal`
   and/or `--hooks team` for the installed scopes. Only owned links and hooks are removed.
   Personal Codex hook removal affects every repo for this operator.
3. For Claude, run `python3 <bento>/install/bento-claude-hooks.py --repo . --purge --scope project`
   and/or `--scope personal`. Personal removal affects this repo's worktrees only. Preserve
   unrelated handlers when removing any legacy hand-written Bento local hooks.
4. Start fresh agent sessions.

Purge keeps the `.bento` submodule, machine-level marketplace, and installed Claude plugins.
Their removal is a separate `git submodule deinit` / `claude plugin uninstall` operation.
