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

## The improve engine (do not rebuild)

`bento-forge improve` **is** Rose's `rose-session-learn` generalized: its Reflect → Route →
Propose loop, its instruction-file pricing model, and its recurrence-gated autorun — with
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

Pin bento as a git submodule so team + CI get one reproducible, versioned source for both
delivery channels:

```
<repo>/
  .bento/                         # submodule → github.com/<you>/bento @ pinned SHA
  .claude/
    settings.json  (committed)    # marketplace: "./.bento"; enabledPlugins: bento-core, bento-forge
    CLAUDE.md      (committed)    # @.bento/principles/PRINCIPLES.md   (+ conventions import)
```

Upgrade = bump the submodule SHA via a normal PR. bento evolves in its own repo, reviewed
independently of the consuming project.

Adopting into a mature repo (Rose) means: keep bento **thin** so it doesn't duplicate what
the repo already does better (Rose already has `investigate`, `ship`, …). bento carries the
cross-cutting layer; the repo keeps its domain skills.

## Phased build

1. **Seed (done):** principles (autonomy, prove, subtract) + `eval-blind` + `hillclimb`,
   dev-loadable; `install.sh` wires principles into the user `CLAUDE.md`.
2. **Conventions:** extract the pricing/pointer/routing discipline from `rose-session-learn`
   + `claude-md-improver` into `conventions/`. Extraction, not authoring.
3. **Engine:** implement `bento-forge improve` = session-learn router with L1/L2 sinks.
4. **Adopt into Rose:** push bento to GitHub; add as `.bento` submodule + committed
   `.claude/settings.json` + `CLAUDE.md` import, as a draft PR to `develop` for team review.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril).
