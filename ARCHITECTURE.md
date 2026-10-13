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
bento (plugins/bento/skills/, every skill self-contained and prefixed bento-)
  principles     always-on stances       bento-setup/PRINCIPLES.md
  conventions    how to author L2        bento-learn/references/instruction-layer.md
  playbooks      triggered task skills    bento-eval-blind, bento-hillclimb, …
  forge          generate + improve       bento-init (generate), bento-learn (evolve)
```

- **Principles** are always-on → a skill can't ship always-on text, so `bento-setup` wires
  them: a `CLAUDE.md` `@import` of the installed `PRINCIPLES.md`, and a distilled,
  marker-bounded block in `AGENTS.md` for Codex.
- **Conventions** are the meta-layer: rules about *how the instruction layer itself is
  written*. This is where the instruction-pricing model and skill-routing discipline live.
- **Playbooks** are triggered skills.
- **Forge**: `bento-init` (generate) + `bento-learn` (evolve).

`bento-init` inspects code, docs, and merged PR reviews, then pauses for approval
of the evidence, file design, and generated diff. Its `l2-state.py` helper refuses
existing instruction layers (installed `bento-*` skills don't count) and records generated
text in the consuming repo's `.bento-state/baseline.json`. Both improvement paths use that
baseline for three-way merges, preserving non-conflicting hand edits and leaving files
unchanged on conflict. The baseline travels with the L2 in Git; it is not part of the
installed L1. See [generation and update mechanics](plugins/bento/skills/bento-init/references/init.md).

## The improve engine (do not rebuild)

`bento-learn` **is** Rose's `rose-session-learn` generalized: its Reflect → Route →
Propose loop and its instruction-file pricing model, run manually or from `bento-ship` at PR time — with
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
- The improve engine (`rose-session-learn`) → `bento-learn`
- Skill-authoring conventions (`create-skill`)
- eval-blind, hillclimb

**Rose-specific → stays in Rose (L2):**
- Production-data / Supabase boundaries, tenant isolation
- Concrete repo map, domain skills (RAG, config, client onboarding)
- Linear / branch / PR-org conventions (org-specific)

## How a project adopts bento

**One install path for every agent: [`npx skills`](https://github.com/vercel-labs/skills).**
It discovers each `SKILL.md` folder in this repo and copies it to the agent's skills directory.
That is why every skill is self-contained (its references and scripts live in its own folder;
`bento-learn` and `bento-init` reach each other as siblings, so install all skills together)
and why every name carries the `bento-` prefix: skills from different packs share one flat
directory, and `ship`, `qa` or `setup` would collide.

| scope | where skills land | pinning | principles wiring |
|---|---|---|---|
| project (default) | `.agents/skills/bento-*` (Codex), `.claude/skills/bento-*` (Claude, links) | committed files + `skills-lock.json` | repo `CLAUDE.md` import + `AGENTS.md` block |
| global (`-g`) | `~/.agents/skills/`, `~/.claude/skills/` | none — `npx skills update` | `~/.claude/CLAUDE.md` import + `~/.codex/AGENTS.md` block |

Project scope is the team path: the committed skills *are* the pin, and a committed
`@.claude/skills/bento-setup/PRINCIPLES.md` import finally gives principles a stable in-repo
path. Global scope is the personal path.

Updates: `npx skills update`, then rerun `bento-setup` to refresh the distilled `AGENTS.md`
block. No hook nags about updates; `npx skills update` updates every installed pack at once.

**Why not the old setup.** bento used to ship as a `.bento` submodule plus a Claude
marketplace plugin, Codex symlinks into the submodule, and SessionStart hooks. That needed an
absolute-path marketplace registration, a durable main checkout for worktrees, a separate
plugin cache that drifted from the submodule pin, and per-agent hook installers. `npx skills`
replaces all of it. `bento-setup` carries the migration steps. `plugins/bento/.claude-plugin/`
remains only so `claude plugin eval` and `claude --plugin-dir` work during development.

Keep bento **thin** so it doesn't duplicate what a mature repo already does better (Rose
has `investigate`, `ship`, …). bento carries the cross-cutting layer; the repo keeps its
domain skills.

## Phased build

1. **Seed (done):** principles (autonomy, prove, subtract) + `eval-blind` + `hillclimb`.
2. **Conventions (done):** extract the pricing/pointer/routing discipline from
   `rose-session-learn` + `claude-md-improver`. Extraction, not authoring.
3. **Engine (done):** `bento-learn` = session-learn router with L1/L2 sinks.
4. **Adopt into Rose:** `npx skills add gnibu/bento` at project scope + `bento-setup`, as a
   draft PR to `develop` for team review.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril).
