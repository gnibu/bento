# bento

A shared agent operating framework — a reusable "way of working" a project adopts as its
baseline, with the project's own specifics layered on top. Works across agents (Claude Code
and Codex). Layered:

```
L0  Claude Code + Anthropic skills        (given)
L1  bento  → shared way of working         (a pinned dependency each repo installs)
L2  project layer → how THIS repo works    (the repo's own skills + instructions, on top)
```

Precedence: **L2 > L1.** The project's own rules win; bento fills the gaps. See
`ARCHITECTURE.md` for the full design.

## Four pillars

- **`principles/PRINCIPLES.md`** — always-on standing rules (autonomy, prove-on-artifact,
  subtract-before-add). Delivered via a `CLAUDE.md` `@import`.
- **`conventions/instruction-layer.md`** — how to author a repo's L2: instruction-file
  pricing, pointer form, where each fact goes, task-triggered links, "no match → design one".
- **`plugins/bento-core/`** — triggered playbooks (skills), each a pasteable checklist that
  proves its work on a real artifact:
  - `eval-blind` — compare models/prompts without bias leaking into the verdict.
  - `hillclimb` — tune a metric one variable at a time, keep-or-revert, logged.
  - `figure-it-out` — fallback for a task no playbook covers; frame it, then maybe capture it.
  - `authoring-a-playbook` — how to write a new bento playbook (gate, checklist, prove, eval).
  - `investigate` — evidence-first root-cause debugging; fix at the shared source.
  - `checkpoint` — capture in-progress state so work survives a reset or handoff.
  - `refactor` — change structure while holding behavior; pin first, prove equivalence.
  - `prototype` — throwaway spike to make a design decision cheaply; decide by observation.
  - `multi-phase-plan` — plan a large change as verifiable units before implementing.
  - `ship` — land a change: sync base, verify, review diff, commit/push/PR (defers to the
    repo's AGENTS.md for base branch, PR, and ticket policy).
  - `qa` — exercise a change on its real surface (browser/CLI/API); report evidenced defects.
  - `spec` — turn vague intent into a precise, executable spec before building.
  - `cso` — security audit against common vuln classes; evidenced, confidence-calibrated.
  - `docs` — write/update docs to match current code; release notes.
  - `bento-setup` — wire bento into the environment (vendored plugins, principles, Codex block, hooks).
- **`plugins/bento-forge/`** — the learning engine and generator:
  - `bento-improve` — Reflect → Route → Propose: route each session's learnings to their
    cheapest correct home (L1 bento / L2 repo), with an eval-gated keep-or-revert. Run it
    manually, or let `ship` call it before final checks. Repo-specific learnings can ride in
    the same PR; generic bento learnings are reported for a separate bento PR.
  - `bento-init` — bootstrap a fresh repo's L2 from code, docs, and merged PR reviews,
    with human checkpoints and a generated baseline for later three-way merges.
    See [the workflow and file contract](plugins/bento-forge/references/bento-init.md).

Quality is built in: an **eval harness** (`claude plugin eval` with with/without ablation +
a `tool_used` firing indicator) proves whether a skill actually changes behavior — see
`plugins/bento-core/evals/`.

## Install

**Claude-only (via marketplace):**

```bash
claude plugin marketplace add gnibu/bento
claude plugin install bento-core@bento
claude plugin install bento-forge@bento
/bento-setup                               # wire principles + update hook (interactive; --yes for defaults)
```

Marketplace install gives Claude the **playbooks**; `/bento-setup` wires what a plugin can't:
the always-on **principles** (`@import` into your user `CLAUDE.md`), **Codex native skills**
(in vendored repos), the **AGENTS.md principles/fallback block**, and the **update-check hook**
(SessionStart). It asks hook scope (project/personal); `--yes` takes defaults (Claude project
hook, Codex personal hook), and `--purge` unwires. Rerunning it removes the retired Bento
`Stop` learning hook from older installs.

**Cross-agent (Claude + Codex), vendored in a repo:** run from the consumer repo's root
(requires Git, Python 3.11+, and the Claude Code CLI):

```bash
git submodule add https://github.com/gnibu/bento.git .bento  # first adoption only
git submodule update --init .bento                        # also after cloning
bash .bento/install.sh                                    # Claude plugins + principles
bash .bento/install.sh --claude-hooks                      # project hooks, inherited by worktrees
bash .bento/install.sh --codex --hooks none                # Codex skill links
# Start fresh Claude/Codex sessions, then invoke bento-setup to finish wiring.
```

**Committed `extraKnownMarketplaces` / `enabledPlugins` settings are not proof of a local
install.** Before `/bento-setup` can load, `install.sh` registers the directory marketplace
and installs both `bento-core@bento` and `bento-forge@bento` at user scope. It skips installed,
enabled plugins, enables disabled ones, and honors `$CLAUDE_CONFIG_DIR`. It needs no prompt
or `--yes` flag; each CLI operation has a five-minute timeout and failures exit nonzero.

Directory registration persists an **absolute path**, not a per-session `./.bento` lookup.
From a worktree, the installer uses the main checkout's initialized `.bento` and principles
path; both submodules must be clean and at the same commit. Otherwise it stops with repair
instructions. Keep that main checkout on disk. Existing bento marketplace registrations
(including GitHub) are preserved and reported; missing directories or worktree registrations
must be repaired explicitly. A machine has one marketplace named `bento`, shared across repos.

Verify from the consumer repo:

```bash
claude plugin marketplace list  # bento must appear
claude plugin list              # both plugins must be installed and enabled
```

Restart Claude and confirm the 14 core playbooks plus `bento-setup` are available. The plugin cache is
separate from the submodule pin: rerunning setup does not refresh already-installed content.
See **Update** below, `ARCHITECTURE.md`, and `install/agents-md-snippet.md`.

### Claude hooks: configure once per project

```bash
bash .bento/install.sh --claude-hooks  # merge into .claude/settings.json
```

Commit the resulting `.claude/settings.json` so every new worktree inherits the `SessionStart`
hook. Existing worktrees need the commit too. No per-worktree
`.claude/settings.local.json` is required. Keep `.bento` initialized in each checkout;
the hook resolves its scripts from that checkout's Git root. This also activates hooks
for teammates who use the committed configuration.

For personal activation across the same project's worktrees, use
`bash .bento/install.sh --claude-hooks --scope personal` instead. It merges into user
`settings.json` (honors `$CLAUDE_CONFIG_DIR`) and guards the hook to the repository's shared
Git directory, so unrelated projects are skipped. Run once per repository on each machine.
Use one scope and remove obsolete Bento handlers from old local settings to avoid duplicates.
The installer preserves unrelated settings/hooks and supports `--purge`.

In Conductor, committed project settings travel with the branch. If new workspaces need
submodule initialization, add `git submodule update --init .bento` to the consumer repo's
existing setup script; no local-settings copying is needed. See
[Conductor setup scripts](https://conductor.build/docs/reference/scripts/setup).

### Codex native skills

Current Codex supports native skills. With `.bento` initialized, use the deterministic
installer (Python 3.11+; no Claude CLI needed):

```bash
bash .bento/install.sh --codex                  # relative skill links + personal hooks
python3 .bento/install/bento-agents.py AGENTS.md # always-on principles + legacy fallback
```

It links every directory under `.bento/plugins/bento-core/skills/` into
`.codex/skills/<skill>` and adds `bento-improve` from forge. Codex discovers the playbooks
as **`bento-core:<name>`**, plus `bento-core:bento-setup` and `bento-forge:bento-improve`.
The Claude commands and Codex entrypoints use the same shared setup/improve instructions.
`AGENTS.md` remains the always-on principles and legacy fallback layer.

The installer preserves unrelated skills and hooks, refuses file/directory/link collisions
before making changes, reports each change, and is safe to rerun. Links are relative to the
consumer checkout, so they follow its submodule pin and can be committed for the team.

- `--hooks personal` (default): merge hooks into `~/.codex/hooks.json` (honors `$CODEX_HOME`).
- `--hooks team`: merge a marked block into committed `.codex/config.toml`.
- `--hooks none`: install only skill links.
- `--purge`: remove only Bento-owned links and hooks in the selected scope. For example,
  `bash .bento/install.sh --codex --purge --hooks personal`; repeat with `--hooks team` to
  remove team hooks too. Personal hook removal applies to every repo for this operator.

Use one hook scope to avoid duplicate execution. Existing hand-written hook wiring is
preserved; inspect `/hooks` and remove obsolete Bento entries when migrating from user
`config.toml`. The generated hook uses `.bento/plugins/bento-forge/scripts/session-start.sh`,
with a guard for repos where that script is absent. Existing
`features.hooks = false` settings are respected; review/trust new hooks in `/hooks` if prompted.
See the [Codex hook documentation](https://developers.openai.com/codex/hooks).

**Start a fresh Codex session after setup or purge.** Verify discovery from the consumer repo:

```bash
codex debug prompt-input "List Bento skills"  # includes bento-core:<name>
```

The `.codex/skills` link and namespace behavior is tested with codex-cli 0.153.4.

Dev-load while iterating: `claude --plugin-dir plugins/bento-core`. See
`install/user-claude-md.md`.

## Update (manual)

Bento updates are manual: choose when to pull a newer version and reconcile the wiring.
With the forge hook enabled, the session-start hook asks the agent to check upstream
automatically, at most once every 30 days (including the first session). The agent prompts
you only after confirming a newer version is available, showing the installed and available
revisions/versions. It stays silent when current, offline, or unable to verify an update.
Installing the update remains your choice. The hook itself makes no network request; the
agent performs the read-only check. Its timestamp lives in `~/.bento/update-reminder`, shared
across agents and workspaces. Set `BENTO_UPDATE_REMINDER_DAYS=0` in the hook environment to disable it, or
set a different interval in days. `BENTO_UPDATE_REMINDER_STATE` overrides the timestamp path.

Same repo, two install modes:

- **Marketplace install (Claude-only):**
  ```bash
  claude plugin marketplace update bento
  claude plugin update bento-core@bento
  claude plugin update bento-forge@bento     # restart to apply
  ```
- **Vendored (`.bento` submodule, cross-agent):**
  ```bash
  git submodule update --remote .bento      # pull latest bento
  git add .bento && git commit -m "chore: bump .bento"
  # From the durable main checkout, refresh Claude's separate marketplace/cache:
  claude plugin marketplace update bento
  claude plugin update bento-core@bento
  claude plugin update bento-forge@bento     # restart to apply
  ```
  These CLI updates use the **registered marketplace source**. If it is GitHub, they
  fetch GitHub content, regardless of the submodule pin. Setup reports the source;
  switching it requires explicitly removing `bento` and rerunning `bash .bento/install.sh`.
- **After either, re-run `bento-setup`** — idempotent; reconciles plugins, skill links,
  principles, the `AGENTS.md` block, and hooks. In Codex, invoke `$bento-core:bento-setup`.
  Codex-only installs can rerun `bash .bento/install.sh --codex`; their linked files follow
  the submodule pin directly and do not require Claude cache updates. Start a fresh session.

Pin/roll back by checking the submodule out at a specific bento SHA (or a `plugin@version`).

**Content self-update:** bento also improves *itself* — `bento-improve` routes generic
learnings back into bento (L1) as PRs. That's the framework evolving from real use, not just
version bumps.

Use potion off-the-shelf when it meets your generation needs; use `bento-init` when
you need bento's reviewed generation and baseline-aware updates.

## Installer checks

```bash
python3 -m unittest discover -s install -p 'test_*.py'
BENTO_TEST_CODEX=1 python3 -m unittest discover -s install -p 'test_*.py'
```

The second command also runs `codex debug prompt-input` in an isolated consumer fixture,
checking discovery of all linked skills and their absence after purge. Neither command
changes your personal Claude/Codex configuration.

## Not built yet (deliberately)

- More playbooks — add only when a real recurring task needs one, never speculatively.
- Eval cases for the ported playbooks (ship/qa/spec/cso/docs) — the harness exists; cases for
  eval-blind and hillclimb are in place, the rest are follow-ups.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril). See
`CREDITS.md`.
