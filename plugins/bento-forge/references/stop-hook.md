# Wiring the bento-improve hooks

The subsystem uses **two** hooks that split the loop by what each can do:

| Hook | Script | Job |
|---|---|---|
| **Stop** | `session-stop.sh` | Reflect + bank the finished session to a local ledger. Silent, always-on, no env gate. Never opens a PR by itself. |
| **SessionStart** | `session-start.sh` | If any learning has ripened (recurred across enough sessions), inject a model-visible prompt offering to review them and open a PR. Otherwise silent. |

Wiring is **opt-in per operator**: the scripts ship with the `bento-forge` plugin,
but the activation lives in your **personal, gitignored** `.claude/settings.local.json`
so it never fires for coworkers who didn't opt in.

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

Use the `update-config` skill, or hand-edit `.claude/settings.local.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.bento/plugins/bento-forge/scripts/session-stop.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.bento/plugins/bento-forge/scripts/session-start.sh",
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

For **fully hands-off PRs**, prefix the Stop command with the env var:

```json
"command": "BENTO_IMPROVE_AUTO_PR=1 \"$CLAUDE_PROJECT_DIR\"/.bento/plugins/bento-forge/scripts/session-stop.sh"
```

Banking is silent by design — the session ends normally and the retrospective
runs behind it. Watch `~/.claude/bento-improve/worker.log` to see it work.

## Add it (Codex)

Codex has the same hooks system (`[features].hooks`) with `Stop` and
`SessionStart` events; wire the same scripts in `.codex/config.toml`:

```toml
[[hooks.Stop]]
[[hooks.Stop.hooks]]
type = "command"
command = 'bash "$(git rev-parse --show-toplevel)/.bento/plugins/bento-forge/scripts/session-stop.sh"'

[[hooks.SessionStart]]
[[hooks.SessionStart.hooks]]
type = "command"
command = 'bash "$(git rev-parse --show-toplevel)/.bento/plugins/bento-forge/scripts/session-start.sh"'
```

Verified on codex-cli 0.153.4: the Stop hook fires and passes `session_id`,
`transcript_path`, and `cwd`, so banking works. `SessionStart` `additionalContext`
is injected into the model on Codex just as on Claude.

## Verify

Banking spawns a detached worker instead of printing, so `session-stop.sh` emits
nothing either way — check the log:

```bash
dir=.bento/plugins/bento-forge/scripts
echo "{\"session_id\":\"test456\",\"transcript_path\":\"/nope.jsonl\",\"cwd\":\"$PWD\"}" \
  | "$dir"/session-stop.sh
# missing transcript -> trivial skip, nothing spawned, nothing logged.
rm -f "${TMPDIR:-/tmp}/bento-improve-test456.done"
```

Surfacing prints JSON only when something has ripened:

```bash
"$dir"/session-start.sh </dev/null        # -> nothing, unless the ledger has ripe keys
BENTO_IMPROVE_THRESHOLD=1 "$dir"/session-start.sh </dev/null   # -> SessionStart JSON if any candidate is banked
```

## Remove it

Delete the `Stop` and `SessionStart` blocks from `.claude/settings.local.json`
(Claude) or `.codex/config.toml` (Codex). Nothing else to undo.
