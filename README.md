# bento

A shared agent operating framework — a reusable "way of working" a project adopts as its
baseline, with the project's own specifics layered on top. Works across agents (Claude Code,
Codex, and anything else [`npx skills`](https://github.com/vercel-labs/skills) supports). Layered:

```
L0  Claude Code + Anthropic skills        (given)
L1  bento  → shared way of working         (installed with npx skills, per project or per machine)
L2  project layer → how THIS repo works    (the repo's own skills + instructions, on top)
```

Precedence: **L2 > L1.** The project's own rules win; bento fills the gaps. See
`ARCHITECTURE.md` for the full design.

## What's in it

Everything ships as `bento-*` skills under `plugins/bento/skills/`, each self-contained:

- **Principles** — always-on standing rules (autonomy, prove-on-artifact, subtract-before-add),
  in `bento-setup/PRINCIPLES.md`. `bento-setup` wires them into `CLAUDE.md` / `AGENTS.md`.
- **Conventions** — how to author a repo's L2 (instruction-file pricing, pointer form, where
  each fact goes), in `bento-learn/references/instruction-layer.md`.
- **Playbooks** — triggered skills, each a pasteable checklist that proves its work on a real
  artifact:
  - `bento-eval-blind` — compare models/prompts without bias leaking into the verdict.
  - `bento-hillclimb` — tune a metric one variable at a time, keep-or-revert, logged.
  - `bento-figure-it-out` — fallback for a task no playbook covers; frame it, then maybe capture it.
  - `bento-authoring-a-playbook` — how to write a new bento playbook (gate, checklist, prove, eval).
  - `bento-investigate` — evidence-first root-cause debugging; fix at the shared source.
  - `bento-checkpoint` — capture in-progress state so work survives a reset or handoff.
  - `bento-refactor` — change structure while holding behavior; pin first, prove equivalence.
  - `bento-prototype` — throwaway spike to make a design decision cheaply; decide by observation.
  - `bento-multi-phase-plan` — plan a large change as verifiable units before implementing.
  - `bento-ship` — the whole PR flow: commit, sync on the current base, QA, verify, pre-PR
    review, one stop for decisions, push/PR, ticket update. Reads the base branch, forge and
    tracker from the repo's AGENTS.md, so a repo needs no PR skill of its own.
  - `bento-adversarial-review` — the other model family (Codex under Claude, Claude under
    Codex) reviews the diff; every finding is triaged against the code before any fix.
    Reviews only the commits since its last recorded review.
  - `bento-qa` — exercise a change on its real surface (browser/CLI/API), pin each changed
    behavior with a test, and bootstrap a test system when the repo has none. `bento-ship` runs it.
  - `bento-spec` — turn vague intent into a precise, executable spec before building.
  - `bento-cso` — security audit against common vuln classes; evidenced, confidence-calibrated.
  - `bento-docs` — write/update docs to match current code; release notes.
- **Forge** — the learning engine and generator:
  - `bento-learn` — Reflect → Route → Propose: route each session's learnings to their
    cheapest correct home (L1 bento / L2 repo), with an eval-gated keep-or-revert. Run it
    manually, or let `bento-ship` call it before final checks.
  - `bento-init` — bootstrap a fresh repo's L2 from code, docs, and merged PR reviews, with
    human checkpoints and a generated baseline for later three-way merges. See
    [the workflow and file contract](plugins/bento/skills/bento-init/references/init.md).
- **`bento-setup`** — wire the principles; migrate an old install; `--purge` to unwire.

Quality is built in: an **eval harness** (`claude plugin eval` with with/without ablation +
a `tool_used` firing indicator) proves whether a skill actually changes behavior — see
`plugins/bento/evals/`.

## Repo overlays

A repo adds rules to a bento skill without copying it: `.agents/bento/<skill-name>.md` at the
repo root (e.g. `.agents/bento/bento-ship.md`), read by that skill after `AGENTS.md`. An
overlay adds steps and may replace steps marked *(default)*; it never relaxes a guardrail.
`bento-learn` routes repo-specific learnings about a bento skill there. See
[the overlay rules](plugins/bento/skills/bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).

## Install

Install all skills together (`bento-learn` uses `bento-init`'s helper and vice versa).

**Per project** (team repos — the version is pinned by what you commit):

```bash
npx skills add gnibu/bento --skill '*' -a claude-code codex -y
```

This writes `.agents/skills/bento-*` (read by Codex), `.claude/skills/bento-*` (per-skill links
for Claude) and `skills-lock.json`. `bento-setup` then replaces the per-skill links with one
`.claude/skills -> ../.agents/skills` link, which `npx skills` keeps on later installs and
updates, so no skill is left without a link. Commit them.

**Per machine** (personal, every repo): add `-g`. Skills land in `~/.agents/skills/` and
`~/.claude/skills/` (`$CLAUDE_CONFIG_DIR/skills/` when set).

Then start a fresh session and run **`/bento-setup`** (Claude) or **`$bento-setup`** (Codex). It
adds the principles import to `CLAUDE.md` and the principles block to `AGENTS.md` (project
files, or the user `CLAUDE.md` / `AGENTS.md` under `$CLAUDE_CONFIG_DIR` / `$CODEX_HOME`,
defaulting to `~/.claude` / `~/.codex`, for a global install).

## Update

```bash
npx skills add gnibu/bento --skill '*' -a claude-code codex -y   # add -g for global
```

Re-add rather than `npx skills update`: update re-adds only skills whose hash changed, skips
skills installed before skill-path tracking (it prints their `add` command instead), and never
installs a skill bento added since, so a playbook that starts calling one would find it
missing. Then run `bento-setup`; agents do this on their own after either command. It refreshes
the distilled `AGENTS.md` block and the `.claude/skills` link (the `CLAUDE.md` import follows
the installed file automatically). For a project install, commit the updated skills
and `skills-lock.json`; that commit is the version bump. Roll back with git.

**Content self-update:** `bento-learn` routes generic learnings back into bento (L1) as PRs —
the framework evolving from real use, not just version bumps.

## Migrate from the submodule / plugin install

Older bento shipped as a `.bento` git submodule plus a Claude marketplace plugin
(`/bento:<name>`), Codex symlinks, and a SessionStart update hook. To move a repo over:

```bash
npx skills add gnibu/bento --skill '*' -a claude-code codex -y   # add -g for global
```

Then start a fresh session and run `/bento-setup` (or `$bento-setup`). It detects and removes
the legacy pieces, asking before machine-wide changes:

1. the `.bento` submodule (`git submodule deinit -f .bento && git rm -f .bento`);
2. the `bento@bento` plugin and `bento` marketplace (machine-wide: migrate or globally install
   bento for other repos first), plus committed `extraKnownMarketplaces`/`enabledPlugins` entries;
3. SessionStart/Stop hooks pointing into `.bento/plugins/` (Claude settings, `~/.codex/hooks.json`,
   the marked block in `.codex/config.toml`) and `~/.bento/update-reminder`;
4. `.codex/skills/` symlinks (Codex reads `.agents/skills/` directly);
5. the old `@…/principles/PRINCIPLES.md` import in your user `CLAUDE.md`.

It then writes the new principles wiring. Also drop `git submodule update --init .bento` from
any workspace setup script (e.g. Conductor's). Skill names changed from `/bento:ship` to
`/bento-ship` (and `$bento:ship` to `$bento-ship`).

## Develop

```bash
claude --plugin-dir plugins/bento            # dev-load the skills
npx skills add . --list                      # what npx skills will install
python3 -m unittest discover -s plugins/bento/skills/bento-init/scripts -p 'test_*.py'
python3 -m unittest discover -s plugins/bento/skills/bento-learn/scripts -p 'test_*.py'
python3 -m unittest discover -s plugins/bento/skills/bento-setup/scripts -p 'test_*.py'
claude plugin eval ./plugins/bento --runs 3 --ablation with-without --no-publish \
  --scaffold --allow-tools Bash               # scaffolded cases build a git repo per run
```

Use potion off-the-shelf when it meets your generation needs; use `bento-init` when
you need bento's reviewed generation and baseline-aware updates.

## Not built yet (deliberately)

- More playbooks — add only when a real recurring task needs one, never speculatively.
- Eval cases for spec/cso/docs — the harness exists; the rest have cases.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril). See
`CREDITS.md`.
