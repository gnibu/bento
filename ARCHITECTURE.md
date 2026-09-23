# bento — architecture

bento is a **shared agent operating framework**: the reusable "way of working" a project
adopts as its baseline, with the project's own specifics layered on top. It started as a
personal kit; the decision is to make it the shared floor for Rose (and any other repo).

```
L0  Claude Code + Anthropic skills        (given)
L1  bento  → shared way of working         (a pinned dependency each repo installs)
L2  project layer → how THIS repo works    (the repo's own skills + CLAUDE.md, on top)
```

Precedence: **L2 > L1.** bento is the floor; the repo overrides it where they overlap.

## Four pillars

```
bento
  principles/    always-on stances       autonomy, prove-on-artifact, subtract-before-add
  conventions/   how to author L2        instruction-file pricing + pointer form,
                                          skill/procedure-routing (incl. "no match → design one"),
                                          what belongs in an AGENTS.md vs a doc vs a comment
  playbooks/     triggered task skills    eval-blind, hillclimb, … (bento-core plugin)
  forge/         generate + improve       bootstrap a fresh L2; evolve an existing one
```

- **Principles** are always-on → delivered via a committed `CLAUDE.md` `@import` (a plugin
  can't ship always-on text). See `install.sh` / `install/user-claude-md.md`.
- **Conventions** are the meta-layer: rules about *how the instruction layer itself is
  written*. This is where the instruction-pricing model and skill-routing discipline live.
- **Playbooks** are triggered skills, shipped by the `bento-core` plugin.
- **Forge** is the `bento-forge` plugin: `bento-init` (generate) + `bento-improve` (evolve).

`bento-init` inspects code, docs, and merged PR reviews, then pauses for approval
of the evidence, file design, and generated diff. Its `l2-state.py` helper refuses
existing instruction layers and records generated text in the consuming repo's
`.bento-state/baseline.json`. Both improvement paths use that baseline for
three-way merges, preserving non-conflicting hand edits and leaving files unchanged
on conflict. The baseline travels with the L2 in Git; it is not part of vendored
L1 or private hook state. See [generation and update mechanics](plugins/bento-forge/references/bento-init.md).

## The improve engine (do not rebuild)

`bento-forge improve` **is** Rose's `rose-session-learn` generalized: its Reflect → Route →
Propose loop and its instruction-file pricing model, run manually or from `ship` at PR time — with
the Route table's sinks widened from Rose-only (`AGENTS.md`/docs/skills) to **L1 (bento) vs
L2 (the repo)**. It is the mechanism that keeps factoring generic practices up into bento
over time, instead of a one-time manual port.

## Factoring Rose → bento (the decision)

Test for each practice: *would this help an agent in a repo that isn't Rose?*

**Generic → factor into bento:**
- Autonomy contract (Rose keeps only its concrete instances)
- Prove-on-artifact / before-after evidence discipline
- Instruction-file pricing + pointer form (from `rose-session-learn` Space budget)
- Skill/procedure-routing discipline, incl. "no match → design one" (`claude-md-improver`)
- The improve engine (`rose-session-learn`) → `bento-forge improve`
- Skill-authoring conventions (`create-skill`)
- eval-blind, hillclimb

**Rose-specific → stays in Rose (L2):**
- Production-data / Supabase boundaries, tenant isolation
- Concrete repo map, domain skills (RAG, config, client onboarding)
- Linear / branch / PR-org conventions (org-specific)

## How a project adopts bento

**Playbooks + forge (the plugins) — canonical marketplace install, not a submodule.**
Claude Code manages the clone and updates. Commit the marketplace + enablement to the
repo's `.claude/settings.json` to declare the team defaults. Each machine still needs
a registered marketplace and installed plugins; verify with the CLI:

```
claude plugin marketplace add gnibu/bento     # resolves from the repo's DEFAULT branch
claude plugin install bento-core@bento
claude plugin install bento-forge@bento
```

These commands default to user scope. Team declarations belong in project settings, while
registration and installed-plugin records live in the machine's Claude config directory.
Upgrade by rerunning `bash .bento/install.sh` (it runs `claude plugin marketplace update bento`
and `claude plugin update` for each plugin). Plugins are versioned by commit SHA (no
`version` field), so every merged commit is an update. The marketplace resolves
from the repo's **default branch**, so `marketplace.json` must live there — not just on a
feature branch.

**Principles (always-on) — the one gap the plugin system doesn't cover.** A plugin ships
only *triggered* surfaces, so the always-on principles still need a `CLAUDE.md` `@import`,
and a committed team import needs a stable in-repo path (the plugin cache under `~/.claude`
is per-machine, not committable). Options, cheapest first:
- Each dev imports them at user scope (`install.sh`) — personal, not enforced in CI.
- Inline the (short) principle text into the repo's own root instructions — committed and
  enforced, but it becomes the repo's copy, not the shared source.
- Vendor just `principles/PRINCIPLES.md` at a known path for a committed `@import`.

Keep bento **thin** so it doesn't duplicate what a mature repo already does better (Rose
has `investigate`, `ship`, …). bento carries the cross-cutting layer; the repo keeps its
domain skills.

## Cross-agent (Claude Code + Codex)

Both Claude and current Codex support native, triggered skills. Bento maintains one source
with two discovery adapters: a Claude marketplace/cache and relative Codex skill links.
The cross-agent install vendors Bento as a pinned submodule:

```
<repo>/
  .bento/                      # shared source, pinned git submodule
  .claude/settings.json        # Claude declarations + project hooks shared by worktrees
  .codex/skills/<skill>        # relative links into .bento/plugins/*/skills/<skill>
  .codex/config.toml          # committed hooks only when team scope is selected
  AGENTS.md                   # always-on principles + legacy fallback pointers
~/.codex/hooks.json           # personal Codex hooks (default scope)
```

| pillar | shared source | Claude Code | Codex |
|---|---|---|---|
| principles | `.bento/principles/PRINCIPLES.md` | `CLAUDE.md` `@import` | distilled into `AGENTS.md` |
| conventions | `.bento/conventions/*` | referenced | `AGENTS.md` pointer |
| playbooks | `.bento/plugins/**/SKILL.md` | native plugin skills | native skills via relative links |
| setup / improve | plugin `references/bento-setup.md` / `bento-improve.md` | command wrappers | `SKILL.md` wrappers |

`bash .bento/install.sh --codex` runs `install/bento-codex.py` without requiring Claude.
It discovers every core skill directory and the forge `bento-improve` entrypoint, preflights
collisions and hook configuration, then creates missing relative links and merges hooks.
Unrelated links, files, settings, and hook handlers are preserved. Reruns are idempotent;
purge removes only exact owned links (including dangling links) and owned hook entries.
Each mutation is reported. The links follow the current checkout's submodule pin.

Codex surfaces **`bento-core:<name>`**, including `bento-core:bento-setup`, and
`bento-forge:bento-improve` (verified with codex-cli 0.153.4's `debug prompt-input`). The
`AGENTS.md` block stays as an always-on principles and legacy fallback layer, not the primary
skill loader. **Start a fresh Codex session after setup.**

Personal hooks are merged into `${CODEX_HOME:-~/.codex}/hooks.json`; committed hooks stay in
`.codex/config.toml`. Choose one scope; hook sources are additive. Legacy hand-written
hooks are preserved, so remove obsolete Bento entries through review when migrating.
Generated hooks resolve the current Git root and use the real
`.bento/plugins/bento-forge/scripts/session-start.sh` path, silently
skipping repos without the script. Reruns remove the retired `session-stop.sh` learning
hook. Setup respects an explicit hooks disable and Codex's
hook review flow. See [Codex hooks](https://developers.openai.com/codex/hooks).

### Claude hooks across worktrees

`bash .bento/install.sh --claude-hooks` merges the SessionStart hook into committed project
`.claude/settings.json`, the default Claude scope in setup. Once committed, new worktrees
inherit the definitions. Hook commands resolve each session's Git root, so there is no
per-worktree absolute path or manual `settings.local.json` setup. Each checkout still needs
its `.bento` submodule initialized.

The personal alternative (`--scope personal`) merges into user Claude settings and guards
execution using the repository's common Git directory. All worktrees share that identity;
unrelated projects do not activate these hooks. This is one setup per repo per machine.
Both scopes preserve unrelated settings/handlers and support purge.
Choose one scope to avoid duplicate execution from additive hook sources.

### Vendored bootstrap and machine state

Run `git submodule update --init .bento` and `bash .bento/install.sh` in each consumer checkout
on each machine before invoking `/bento-setup`. The installer checks the real CLI state,
registers a directory marketplace when bento is absent, and installs/enables both plugins
at user scope. Committed `extraKnownMarketplaces.bento` and `enabledPlugins` declarations
alone do not establish that the directory marketplace or plugin cache exists on a machine.
`/bento-setup` prefers the consumer's submodule and repeats this check idempotently.

The CLI persists a local source as an **absolute path** in
`$CLAUDE_CONFIG_DIR/plugins/known_marketplaces.json` (default `~/.claude`), shared across
projects. A relative `./.bento` is not resolved afresh in each session. The installer resolves
worktrees to the main checkout's initialized `.bento`, requiring clean copies at the same
commit, and uses that durable path for the principles import too. Keep the main checkout;
worktree deletion is then safe. Missing or mismatched main-checkout copies stop setup with
repair instructions. Existing missing/worktree-based registrations also require repair.

Existing valid registrations, including GitHub, are preserved and reported. With a newly
registered **directory** marketplace, local content can be installed before bento merges to
its default branch. With an existing **GitHub** marketplace, Claude still installs from that
source. One machine cannot have multiple independent sources under the name `bento`.

Claude copies plugins into a separate versioned cache recorded in `installed_plugins.json`.
Changing the submodule pin changes Codex's files immediately, but does **not** update Claude's
installed skills. Refresh the registered marketplace, update both plugins, and restart
Claude (README **Update**). Setup installs missing plugins and updates installed ones from the
registered marketplace source, which is not necessarily the submodule pin. Verify marketplace/plugin lists, then confirm the 14 core playbooks plus setup
in a fresh session.

Updates are manual. On first use and at most every 30 days afterward, the shared
SessionStart hook instructs the agent to check upstream before prompting. The agent offers
an update only after confirming a newer version; current or inconclusive checks stay silent.
The hook itself makes no network request, and nothing installs automatically.
A local timestamp in `~/.bento/update-reminder` throttles checks across agents and
workspaces; `BENTO_UPDATE_REMINDER_DAYS=0` disables it. See README **Update** for options.

## Phased build

1. **Seed (done):** principles (autonomy, prove, subtract) + `eval-blind` + `hillclimb`,
   dev-loadable; `install.sh` wires principles into the user `CLAUDE.md`.
2. **Conventions:** extract the pricing/pointer/routing discipline from `rose-session-learn`
   + `claude-md-improver` into `conventions/`. Extraction, not authoring.
3. **Engine:** implement `bento-forge improve` = session-learn router with L1/L2 sinks.
4. **Adopt into Rose:** merge bento to its default branch; add the marketplace + enable the
   plugins in a committed `.claude/settings.json`, as a draft PR to `develop` for team
   review. Principles (the always-on `@import`) follow separately.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril).
