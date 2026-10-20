# Changelog

## Unreleased

- **Shipping checks affected docs and sensitive changes.** `bento-ship` calls `bento-docs`
  before final checks for public behavior, CLI/API/config contracts or example changes, and
  `bento-cso` for auth, trust-boundary, secret or sensitive-data exposure changes. Security
  decisions use the existing decision stop; docs/security outcomes appear in the PR and report.
  Repo overlays can customize tooling while retaining the specialist triggers and security triage.
- **Spec and planning preserve the requested scope.** Spec-only and plan-only requests stop
  at their artifact. When used as preparation for an implementation request, they continue
  the authorized work once the contract is settled, without another permission round.
- **More precise skill routing and evals.** Debugging, tuning, comparisons and large-change
  planning have clearer boundaries. All 19 skills now have behavioral cases; new workflow
  cases cover secondary duties, continuation and trivial-task exclusions, and firing checks
  identify the intended skill rather than any skill call. Playbook authoring checks for an
  existing owner before adding a competing skill.
- **Shorter handoff and fallback checklists.** `bento-checkpoint` and `bento-figure-it-out`
  retain their evidence and scope rules with fewer steps and less repeated guidance.
- **New `bento-hotspots`: measure code quality in Python, JavaScript and TypeScript.**
  `hotspots.py` (lizard, via `uv run`) ranks functions by cognitive complexity x churn and
  files by size x churn, and lists import cycles and fan-in/fan-out. The agent reads each top
  entry and marks it refactor, leave or exclude before handing targets to `bento-refactor`.
  Its diff mode (`--base`) reports only what the branch made worse: a function past a limit
  (length, cyclomatic or cognitive complexity, nesting, parameters), a file past 500 lines, or
  an import cycle a new import closed. `bento-ship` runs it while reviewing its own diff, and
  `bento-refactor` uses the scan when no target is named.
- **Scheduled refactor:** `Run /bento-hotspots in unattended mode` on a schedule opens at most one
  draft PR per run, refactoring the top function behind a test. It skips functions with a
  `hotspots` PR (closed means rejected) and the overlay's `## Leave` list. The README shows
  how to schedule it.
- **`bento-ship` puts Web UI screenshots on the ticket, not the PR.** The ticket comment
  attaches them; the PR's test plan says what each shows and points to the ticket. With no
  ticket update, they go in the PR as before.
- **`bento-learn` keeps procedures out of `AGENTS.md`.** A procedure with no doc to go in
  gets one in `docs/procedures/`, named by its task (`run-tests.md`, `release.md`), with When,
  steps and Check. The root `AGENTS.md` lists every doc in a `## Docs` menu, trigger first. A
  code-scoped gotcha with no nearby `AGENTS.md` gets a new one in that directory, with a
  `CLAUDE.md` importing it. `check_entries.py` checks every proposed `AGENTS.md`/`CLAUDE.md`: it
  rejects an entry over a line without a pointer, or over two lines, and a menu missing a doc.
- **`bento-ship` creates the missing ticket.** When the repo has a tracker and the work has
  no ticket, ship creates one titled for the whole diff and links it to the PR, instead of
  reporting "no ticket". A repo can set it to `ask` or `never`.
- **Ship preferences per repo.** `bento-setup` asks once, and records in the
  `.agents/bento/bento-ship.md` overlay: missing ticket, ticket update, tracker details (read
  from `AGENTS.md` first), QA, pre-PR review, learnings and PR reviewers. Reruns ask only new
  questions; `--yes` writes the defaults; `/bento-setup --preferences` re-asks them all.
  `bento-ship` follows them, and its report names each one that applied.
- **`bento-qa` checks the server it tests is its own.** After starting a background server,
  it confirms the process listening on the port is the one it started, so a stale server or
  another workspace's never stands in for the change.
- **Agents run `bento-setup` on their own.** The skill and the `AGENTS.md` block say it is
  idempotent, local and reviewable, so an agent runs it after `npx skills add` or `update`
  instead of asking.
- **One `.claude/skills` link.** `bento-setup` replaces per-skill links with
  `.claude/skills -> ../.agents/skills` (asking first if it holds real folders), so a skill
  added later is never invisible to Claude. `bento-init` writes repo skills to
  `.agents/skills/` and accepts that link as greenfield.
- **`CLAUDE.md -> AGENTS.md` repos** skip the principles import, which would load them twice.
- **`agents_block.py` reports `unchanged`** and skips the write when the block is identical.
- **Verify is concrete:** headless `claude -p` and `codex exec` list the `bento-*` skills,
  compared against `.agents/skills/`.

## 0.3.0 — 2026-10-13

- **`bento-qa` leaves tests behind.** After exercising a change on its real surface, it pins
  each changed behavior with an automated test it has seen fail, and bootstraps the smallest
  stack-native test runner when the repo has none (a command that runs zero tests counts as
  none). Code too hard to test gets a seam or an `untestable` finding. A ship mode scopes it to
  the branch and returns a fixed QA report.
- **Web UI QA is end to end in a real browser.** `bento-qa` clicks through every critical
  journey in a browser (the Claude in Chrome MCP under Claude when connected, else
  `agent-browser` or Playwright), screenshots each key state and checks the console. Each
  journey also gets one end-to-end browser test that reruns, and `bento-ship` puts the
  screenshots in the PR's test plan.
- **`bento-ship` runs QA** before its checks, so the checks and the pre-PR review cover the new
  tests. A zero-test suite no longer passes as green, and the PR's test plan comes from the QA
  report.
- **Tests are planned up front.** `bento-spec` criteria and `bento-multi-phase-plan` PRs name
  their tests, and `bento-init` flags a repo with no test command as a gap.

## 0.2.0 — 2026-10-13

First versioned release since 0.1.1. It also carries the npx-skills install and `bento-*`
names (#26) and `bento-adversarial-review` (#28).

- **Repo overlays.** Every bento skill reads `AGENTS.md`/`CLAUDE.md`, then its overlay
  `.agents/bento/<skill-name>.md` if the repo has one. Overlays add rules and may replace steps
  marked *(default)*; they never relax a guardrail. `bento-learn` routes repo-specific
  learnings about a bento skill there; `bento-setup` never creates or deletes them.
- **`bento-adversarial-review` picks its own scope.** It skips a branch already reviewed at
  `HEAD`, reviews only the commits since the last review when history allows, and returns the
  reviewed sha in ship mode. An explicit scope still wins.
- **`bento-ship` holds the whole PR flow**, so a repo needs no PR skill of its own: commit
  first, one PR per ticket, stale-base detection, a single `ACTION REQUIRED` stop for
  learnings and decisions, push recovery, PR title and body rules, ticket comment and status
  with a re-check, and a report naming the pre-PR review (local) and the PR's reviewers.
