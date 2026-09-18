# Wiring the bento-improve hooks

The subsystem uses **two** hooks that split the loop by what each can do:

| Hook | Script | Job |
|---|---|---|
| **Stop** | `session-stop.sh` | Reflect + bank the finished session to a local ledger. Silent, always-on, no env gate. Never opens a PR by itself. |
| **SessionStart** | `session-start.sh` | Offer to review ripened learnings and, at most every 30 days, instruct the agent to check for a newer Bento version before offering an update. Otherwise silent. |

Hook scripts ship with `bento-forge`; setup activates them in the selected scope. Claude
uses committed project settings by default, shared by all worktrees and teammates. A
personal scope can cover the same project's worktrees without changing team settings.

> Renamed: the Stop entry used to be `stop-nudge.sh`. It is now `session-stop.sh`
> (its job is bank, not nudge). Update any hook still pointing at the old name.

## The model: bank always, surface at start, PR on your yes

- **Stop → bank.** Every substantive session is reflected on and its candidates
  banked. This is env-independent and cross-agent (Claude + Codex): no
  `BENTO_IMPROVE_AUTORUN` to remember. A trivial session (no transcript, or
  fewer than 2 user turns and no tool use) is skipped so it costs nothing.
- **SessionStart → surface.** Next time you start a session, if learnings have
  ripened you get a prompt to review them. Say yes and the agent opens the PR via
  the `bento-improve` / session-learn skill. That interactive yes is the approval
  gate.
- **Check first, update manually.** On first use and every 30 days thereafter, SessionStart
  instructs the agent to check upstream automatically using read-only operations. The agent
  asks about updating only after confirming a newer version and reports the installed and
  available revisions/versions. Current, offline, and inconclusive checks stay silent.
  The hook itself makes no network request and installs nothing. A local
  timestamp in `~/.bento/update-reminder` prevents repeated checks across agents and
  workspaces. Set `BENTO_UPDATE_REMINDER_DAYS=0` to disable, or another positive number
  for the interval; `BENTO_UPDATE_REMINDER_STATE` overrides the timestamp path. Missing
  Python 3 or unavailable state silently skips this reminder, preserving learning prompts.
  The worker exports `BENTO_UPDATE_REMINDER_DAYS=0` for all its unattended children, so
  their hooks leave the reminder timestamp untouched. Other unattended callers should
  set the same override; see `autorun.md` → Tunables.
- **Fully hands-off?** Set `BENTO_IMPROVE_AUTO_PR=1` on the Stop command and the
  worker opens the PR itself once a learning ripens — no prompt needed. See
  `autorun.md`.

### Why two hooks — the model-visibility difference

A `Stop` hook **cannot** surface model-visible context. Its
`hookSpecificOutput.additionalContext` is *not* read by the model or user on
either Claude or Codex; the only field a Stop hook surfaces is `systemMessage`
(a UI warning, invisible in headless `codex exec`). So the Stop hook does the
silent work (bank) and says nothing.

A `SessionStart` hook's `additionalContext` **is** injected into the model's
context on both Claude and Codex. So surfacing the ripened learnings happens
there, where the agent can actually act on it. That is the whole reason the loop
is split across two hooks rather than crammed into one.

## Path to the scripts

The scripts live under the plugin at `scripts/`. Point each hook at wherever
bento is installed. With bento **vendored** in the repo (the `<repo>/.bento`
model), that is:

```
"$CLAUDE_PROJECT_DIR"/.bento/plugins/bento-forge/scripts/session-stop.sh
"$CLAUDE_PROJECT_DIR"/.bento/plugins/bento-forge/scripts/session-start.sh
```

Adjust the prefix if you install bento elsewhere (a plugin cache path or an
absolute checkout). Scripts call their siblings via `$(dirname "$0")`, so the
bundle is relocatable — only these two entry paths need to be correct.

## Add it (Claude)

For a vendored consumer, run once from the project root:

```bash
bash .bento/install.sh --claude-hooks                  # committed .claude/settings.json
# Or personal activation for this repo and every one of its worktrees:
bash .bento/install.sh --claude-hooks --scope personal  # user settings.json, guarded by repo
```

Commit project settings so new worktrees inherit both hooks; initialize `.bento` in each
checkout. Personal settings honor `$CLAUDE_CONFIG_DIR` and use the common Git directory to
recognize all of this repo's worktrees. Neither choice needs a new `settings.local.json`
for each worktree. The installer merges hooks and preserves unrelated permissions/handlers.
Append `--auto-pr` only to opt into hands-off PRs. Use one scope, and remove obsolete Bento
handlers from old local settings to avoid running duplicates.

For marketplace-only installs, locate forge's `installPath` with `claude plugin list --json`
and point command hooks at its `scripts/session-start.sh` and `scripts/session-stop.sh`.
Merge them under the corresponding `hooks.SessionStart` / `hooks.Stop` arrays, each in a
`{"hooks": [{"type": "command", "command": "bash <quoted-absolute-script-path>", "timeout": 5}]}`
group. Cache paths can change on update; rerun setup to reconcile them.

Banking is silent by design — the session ends normally and the retrospective runs behind
it. Watch `~/.claude/bento-improve/worker.log` to see it work.

## Add it (Codex)

Use the deterministic installer from the consumer repo (Python 3.11+):

```bash
bash .bento/install.sh --codex                 # personal ~/.codex/hooks.json
bash .bento/install.sh --codex --hooks team    # committed .codex/config.toml instead
```

Choose one scope; Codex combines hooks from all active sources. Personal hooks honor
`$CODEX_HOME`. Existing hand-written hooks are preserved, so review old user `config.toml`
entries when migrating to `hooks.json` to avoid duplicate execution. The installer merges
only Bento's handlers, preserves unrelated hooks, and uses these actual scripts:

```
.bento/plugins/bento-forge/scripts/session-start.sh
.bento/plugins/bento-forge/scripts/session-stop.sh
```

Commands resolve the session's Git root, work from nested directories, and no-op when the
scripts are absent. `--auto-pr` sets `BENTO_IMPROVE_AUTO_PR=1` for Stop only. Without it,
Stop banks learnings and SessionStart surfaces candidates for review.

**Start a fresh Codex session after setup.** If prompted, review/trust the definitions in
`/hooks`. An existing `features.hooks = false` is respected. Personal hooks belong in
`~/.codex/hooks.json`, while team hooks stay in `.codex/config.toml`; see
[Codex hook locations and schema](https://developers.openai.com/codex/hooks).

## Verify

Banking spawns a detached worker instead of printing, so `session-stop.sh` emits
nothing either way — check the log. Note that Stop fires at the end of every
turn, so banking is **debounced**: the worker runs once the session has been idle
for `BENTO_IMPROVE_QUIESCE_SECS` (default 300s), reflecting on the complete
transcript. Log entries therefore appear minutes after the last turn, not at each
stop. Lower the window to see it quickly:

```bash
dir=.bento/plugins/bento-forge/scripts
echo "{\"session_id\":\"test456\",\"transcript_path\":\"/nope.jsonl\",\"cwd\":\"$PWD\"}" \
  | "$dir"/session-stop.sh
# missing transcript -> nothing arms, nothing spawned, nothing logged.
rm -rf "${TMPDIR:-/tmp}/bento-improve-test456"
```

Surfacing prints JSON when something has ripened or an update reminder is due. Disable
the reminder to verify learning prompts independently:

```bash
BENTO_UPDATE_REMINDER_DAYS=0 "$dir"/session-start.sh </dev/null
BENTO_UPDATE_REMINDER_DAYS=0 BENTO_IMPROVE_THRESHOLD=1 "$dir"/session-start.sh </dev/null
```

## Remove it

For Claude, run `bash .bento/install.sh --claude-hooks --purge` (or add `--scope personal`
for the personal scope). Remove legacy local Bento handlers separately, preserving other
handlers in the same groups. For Codex:

```bash
bash .bento/install.sh --codex --purge --hooks personal
# Or --hooks team for the committed scope. Purge also removes Bento skill links.
```

Personal hook removal affects all repos for this operator. Start a fresh Codex session.
