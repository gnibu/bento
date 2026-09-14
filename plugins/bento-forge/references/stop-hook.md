# Wiring the bento-improve Stop hook

The nudge is **opt-in per operator**. The scripts ship with the `bento-forge`
plugin, but the activation lives in your **personal, gitignored**
`.claude/settings.local.json` so it never fires for coworkers who didn't opt in.

## Why personal scope

A `Stop` hook fires at the end of **every turn**. The script guards against
per-turn spam with a per-`session_id` sentinel, so it nudges at most once per
session. But whether you *want* that nudge at all is a personal preference — so
the trigger stays out of the committed `.claude/settings.json`.

## Two modes

| Mode | Behaviour |
|---|---|
| **nudge** (default) | Injects a reminder to capture the session's learnings. |
| **autorun** (`BENTO_IMPROVE_AUTORUN=1`) | Spawns a detached worker that reflects, banks candidates in a local ledger, and opens a PR once a learning recurs. See `autorun.md`. |

## Path to the script

The scripts live under the plugin at `scripts/stop-nudge.sh`. Point the hook at
wherever bento is installed. With bento **vendored** in the repo (the
`<repo>/.bento` model), that is:

```
"$CLAUDE_PROJECT_DIR"/.bento/plugins/bento-forge/scripts/stop-nudge.sh
```

Adjust the prefix if you install bento elsewhere (e.g. a plugin cache path or an
absolute checkout). Scripts call their siblings via `$(dirname "$0")`, so the
whole bundle is relocatable — only this one entry path needs to be correct.

## Add it

Use the `update-config` skill, or hand-edit `.claude/settings.local.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.bento/plugins/bento-forge/scripts/stop-nudge.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

If `settings.local.json` already has other keys (e.g. `permissions`), merge the
`hooks` block in rather than overwriting the file.

For **autorun**, prefix the command with the env var:

```json
"command": "BENTO_IMPROVE_AUTORUN=1 \"$CLAUDE_PROJECT_DIR\"/.bento/plugins/bento-forge/scripts/stop-nudge.sh"
```

Autorun is silent by design — the session ends normally and the retrospective
runs behind it. Watch `~/.claude/bento-improve/worker.log` to see it work.

## Verify

```bash
dir=.bento/plugins/bento-forge/scripts
echo '{"session_id":"test123"}' | "$dir"/stop-nudge.sh   # → emits additionalContext JSON
echo '{"session_id":"test123"}' | "$dir"/stop-nudge.sh   # → no output (sentinel hit)
rm -f "${TMPDIR:-/tmp}/bento-improve-test123.done"
```

Autorun spawns instead of printing, so it emits nothing either way — check the log:

```bash
echo "{\"session_id\":\"test456\",\"transcript_path\":\"/nope.jsonl\",\"cwd\":\"$PWD\"}" \
  | BENTO_IMPROVE_AUTORUN=1 "$dir"/stop-nudge.sh
sleep 1 && tail -1 ~/.claude/bento-improve/worker.log   # -> "test456 below gate" (or a repo-marker skip)
rm -f "${TMPDIR:-/tmp}/bento-improve-test456.done"
```

## Codex

Codex has the same hooks system (`[features].hooks`) with a `Stop` event; wire the same
script in `.codex/config.toml`:

```toml
[[hooks.Stop]]
[[hooks.Stop.hooks]]
type = "command"
command = 'bash "$(git rev-parse --show-toplevel)/.bento/plugins/bento-forge/scripts/stop-nudge.sh"'
```

Verified on codex-cli 0.153.4: the Stop hook fires and passes `session_id`,
`transcript_path`, and `cwd`, so **autorun works** (`BENTO_IMPROVE_AUTORUN=1`).

**The nudge must use `systemMessage`, not `additionalContext`.** For the `Stop` event,
`hookSpecificOutput.additionalContext` is *not* surfaced to the user or model on either
Claude or Codex — only `SessionStart`/`UserPromptSubmit` inject context. The field a Stop
hook surfaces is **`systemMessage`** ("shown as a warning in the UI"). `stop-nudge.sh`
emits `systemMessage` (with `additionalContext` kept as a harmless fallback), so the nudge
surfaces on both hosts. `systemMessage` is a UI warning, so it appears in an interactive
session — not in headless `codex exec` output (which is why exec can't verify it; test
interactively). To *continue* the turn instead of just warning, a Stop hook returns
`{"decision":"block","reason":"…"}` (the reason becomes the next prompt) — bento's nudge
deliberately only warns, it doesn't force continuation.

## Remove it

Delete the `Stop` block from `.claude/settings.local.json` (Claude) or `.codex/config.toml`
(Codex). Nothing else to undo.
