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

**Playbooks + forge (the plugins) — canonical marketplace install, not a submodule.**
Claude Code manages the clone and updates. Commit the marketplace + enablement to the
repo's `.claude/settings.json` so the team and CI get it automatically:

```
claude plugin marketplace add gnibu/bento     # resolves from the repo's DEFAULT branch
claude plugin install bento-core@bento
claude plugin install bento-forge@bento
```

This persists the marketplace + `enabledPlugins` into settings; commit those. Upgrade with
`claude plugin update` (pin releases with `claude plugin tag`). The marketplace resolves
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

The plugin/marketplace system is **Claude-only** — Codex reads `AGENTS.md`, with no plugin
or triggered-skill loader. To serve both, keep one agent-neutral source and two thin
wrappers. This requires bento to be **vendored in the repo** (Codex can't fetch a Claude
marketplace, so the files must be on disk):

```
<repo>/
  .bento/                      # vendored bento (git submodule, pinned) — so Codex can read it
  .claude/settings.json        # Claude: local-path marketplace ./.bento → auto-triggering skills
  AGENTS.md                    # Codex: principles + playbook pointers into .bento/ (see install/agents-md-snippet.md)
```

| pillar | shared source | Claude Code | Codex |
|---|---|---|---|
| principles | `.bento/principles/PRINCIPLES.md` | `CLAUDE.md` `@import` | `AGENTS.md` pointer |
| conventions | `.bento/conventions/*` | referenced | `AGENTS.md` pointer |
| playbooks | `.bento/plugins/**/SKILL.md` | auto-triggering skill (local marketplace) | `AGENTS.md` task-trigger pointer |

Trade-off: Codex loses auto-triggering (it follows a pointer and the model chooses to read);
same content, less ergonomics. That's inherent to Codex having no skill system.

Note: with the vendored `.bento`, Claude uses a **local-path** marketplace
(`claude plugin marketplace add ./.bento`), so bento need **not** be merged to its default
branch for a consuming repo to use it — the files are already present.

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
