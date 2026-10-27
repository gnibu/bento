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

Everything ships as skills (`bento-*`, plus `wup`) under `plugins/bento/skills/`, each self-contained:

- **Principles** — always-on standing rules (autonomy, prove-on-artifact, subtract-before-add,
  report-what-matters, ship-through-bento-ship),
  in `bento-setup/PRINCIPLES.md`. `bento-setup` wires them into `CLAUDE.md` / `AGENTS.md`.
- **Conventions** — how to author a repo's L2 (instruction-file pricing, pointer form, where
  each fact goes), in `bento-learn/references/instruction-layer.md`.
- **Playbooks** — triggered skills, each a pasteable checklist that proves its work on a real
  artifact:
  - `bento-eval-blind` — compare models/prompts without bias leaking into the verdict.
  - `bento-hillclimb` — tune a metric one variable at a time, keep-or-revert, logged.
  - `bento-figure-it-out` — fallback for unmatched multi-step work; frame it, then maybe capture it.
  - `bento-authoring-a-playbook` — how to write a new bento playbook (gate, checklist, prove, eval).
  - `bento-investigate` — evidence-first root-cause debugging; fix at the shared source.
  - `bento-checkpoint` — capture in-progress state so work survives a reset or handoff.
  - `wup` — three-heading status on demand: what's done, what's next, what you must do.
  - `bento-refactor` — change structure while holding behavior; pin first, prove equivalence.
  - `bento-maintain` — one bounded maintenance change with proof: code improvement, instruction
    upkeep, documentation upkeep, dependency security, or a monitoring-driven fix. Reads repo
    overlays; factory mode returns edits and a report, leaving delivery to the caller.
  - `bento-hotspots` — rank Python/JS/TS refactoring targets by complexity x churn, with import
    cycles and fan-in/out; its diff mode flags what a branch made worse. `bento-ship` runs it.
  - `bento-prototype` — throwaway spike to make a design decision cheaply; decide by observation.
  - `bento-multi-phase-plan` — plan a large change as verifiable units before implementing.
    Plan-only requests stop at the plan; preparation inside a build request continues the work.
  - `bento-ship` — the whole PR flow: commit, sync on the current base, affected docs, QA,
    a conditional security audit, verify, pre-PR review, one stop for decisions, push/PR,
    ticket update. Reads the base branch, forge and
    tracker from the repo's AGENTS.md, so a repo needs no PR skill of its own.
  - `bento-adversarial-review` — the other model family (Codex under Claude, Claude under
    Codex) reviews the diff; every finding is triaged against the code before any fix.
    Reviews only the commits since its last recorded review.
  - `bento-qa` — exercise a change on its real surface (browser/CLI/API), pin each changed
    behavior with a test, and bootstrap a test system when the repo has none. `bento-ship` runs it.
  - `bento-spec` — turn vague intent into a precise, executable spec before building.
    Spec-only requests stop there; an implementation request resumes once the contract is settled.
  - `bento-cso` — security audit against common vuln classes; evidenced, confidence-calibrated.
    Ship calls it for changes to auth/permissions, trust boundaries, secrets, sensitive data
    exposure or untrusted input reaching queries, shells, file paths or templates.
  - `bento-docs` — write/update docs to match current code; release notes. Ship calls it before
    final checks when public behavior, CLI flags, API/config contracts or examples change.
- **Forge** — the learning engine and generator:
  - `bento-learn` — Reflect → Route → Propose: route each session's learnings to their
    cheapest correct home (L1 bento / L2 repo), with an eval-gated keep-or-revert. Run it
    manually, or let `bento-ship` call it before final checks. `--reviews` explicitly adds
    historical PR feedback; `--propose-only` returns proposals without applying them.
  - `bento-init` — bootstrap a fresh repo's L2 from code, docs, and merged PR reviews, with
    human checkpoints and a generated baseline for later three-way merges. See
    [the workflow and file contract](plugins/bento/skills/bento-init/references/init.md).
- **`bento-setup`** — wire the principles; install the pre-PR review gate (a Claude Code /
  Codex hook that reminds the agent, without blocking, to use `bento-ship` when it runs
  `git push` or `gh pr create` before a pre-PR review covers `HEAD`; other automation that
  pushes its own branches goes in `Pre-PR review gate: except …`); ask the repo's ship
  preferences once (missing ticket, QA, pre-PR review…;
  `--preferences` re-asks); migrate an old install; `--purge` to unwire. Discover the repository's actual maintenance tools and source-cited commands into
  the maintenance overlay, preserving manual rules and reporting missing integrations.

The **eval harness** (`claude plugin eval` with with/without ablation) has cases for all 20 skills.
Firing indicators check the intended skill, separately from behavior scores. Workflow cases
check captured edits, commands and artifacts, including spec/plan continuation, conditional
docs/security passes, and negative controls for routine test runs and tiny edits. See
`plugins/bento/evals/`. Coverage alone is not evidence of lift; compare the scored behavior.

## Repo overlays

A repo adds rules to a bento skill without copying it: `.agents/bento/<skill-name>.md` at the
repo root (e.g. `.agents/bento/bento-ship.md`), read by that skill after `AGENTS.md`. An
overlay adds steps and may replace steps marked *(default)*; it never relaxes a guardrail.
`bento-learn` routes repo-specific learnings about a bento skill there. See
[the overlay rules](plugins/bento/skills/bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).

## Install

Install all skills together: maintenance reuses the refactor/docs/investigation playbooks
and QA's proof reference; Learn and Init share review collection and baseline helpers.

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
adds the principles block to `AGENTS.md` (and to a `CLAUDE.md` that doesn't already read it),
asks once whether you want terse reports, and adds the pre-PR
review gate to `.claude/settings.json` / `.codex/hooks.json` (project
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
the principles block (keeping your terse-reports answer) and the `.claude/skills` link. For a
project install, commit the updated skills and `skills-lock.json`; that commit is the version bump. Roll back with git.

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

## Scheduled refactor

`bento-hotspots` has an unattended mode: each run picks the worst refactorable function, refactors
it behind a test, and opens one draft PR labelled `hotspots`. Rejected PRs and the `## Leave`
list in `.agents/bento/bento-hotspots.md` keep it from proposing the same thing twice.
Schedule this prompt in the repo, with bento installed:

```text
Run /bento-hotspots in unattended mode.
```

- **Claude Code:** `/schedule` creates a cloud routine on a cron, e.g. daily at 2:00.
- **GitHub Actions:** an `on: schedule` workflow running `anthropics/claude-code-action` with
  that prompt.

Either needs network access, so `uv` can fetch lizard.

## Maintenance from a person or factory

Run `bento-maintain <task> [scope]` for `code-improvement`, `instructions-upkeep`,
`docs-upkeep`, `security-fix` or `error-fix`. Claude uses `/bento-maintain`; Codex uses
`$bento-maintain`. Required checks, protected paths, dependency pins and monitoring details
come from the repository's instructions and `.agents/bento/bento-maintain.md`.
After installation, `bento-setup` discovers the repository's actual tools and writes only
its source-cited mapping block in that overlay. Manual rules survive refreshes. A missing
monitoring/advisory integration is reported as unavailable; no provider is assumed.

A factory invokes, for example, `bento-maintain code-improvement backend --factory`, passing
the assignment's permissions. The worker returns report Markdown, an outcome
(`completed`, `no_op`, `failed`) and a summary. It never commits, pushes, opens PRs or creates
tickets; the local adapter owns delivery and tracker policy. No quota meter, hub issue or
profile file is needed. See [factory adoption and overlay examples](plugins/bento/skills/bento-maintain/references/factory-adoption.md).

Larger cleanups reuse `bento-multi-phase-plan` to inventory sites and define verifiable
batches; the factory tracks authorization and batch completion. Complexity jobs continue to
call `bento-hotspots`. To propose lessons from past PR feedback, explicitly request
`bento-learn --reviews --propose-only`; ordinary maintenance does not change standing rules
from review text. Evidence follows [the shared proof contract](plugins/bento/skills/bento-qa/references/proof.md).

## Develop

```bash
claude --plugin-dir plugins/bento            # dev-load the skills
npx skills add . --list                      # what npx skills will install
python3 -m unittest discover -s plugins/bento/skills/bento-init/scripts -p 'test_*.py'
python3 -m unittest discover -s plugins/bento/skills/bento-learn/scripts -p 'test_*.py'
python3 -m unittest discover -s plugins/bento/skills/bento-setup/scripts -p 'test_*.py'
python3 -m unittest discover -s plugins/bento/skills/bento-hotspots/scripts -p 'test_*.py'  # needs uv
claude plugin eval ./plugins/bento --runs 3 --ablation with-without --no-publish \
  --scaffold --allow-tools Bash Write Edit    # scaffolded cases build a git repo per run
# Parallel eval processes need their own --output-dir: runs started together share a results dir
```

Skill scripts must run on Python 3.9, the `python3` macOS ships with the Command Line Tools:
use `from __future__ import annotations` for `X | None` hints, and no `match` or other 3.10+
syntax. Run the tests under `/usr/bin/python3` too.

Use `--tag workflow` for the workflow and routing-boundary cases. Their graders inspect tool
traces or a named output file, rather than trusting the final summary; negative Skill checks
set `arm: both` so they remain scored under ablation.

Use potion off-the-shelf when it meets your generation needs; use `bento-init` when
you need bento's reviewed generation and baseline-aware updates.

## Not built yet (deliberately)

- More playbooks — add only when a real recurring task needs one, never speculatively.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril). See
`CREDITS.md`.
