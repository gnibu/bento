# Codex (and any AGENTS.md-based agent) — adapter block

Codex has no plugin/skill loader; its only surface is `AGENTS.md`. Add the block below to
the consuming repo's root `AGENTS.md` (or a nested one) so Codex reaches the same bento
files Claude loads as plugins. Single source of truth stays in `.bento/`; this is only
pointers, so no content is duplicated.

```markdown
## bento (shared agent operating layer)

- **Principles (always-on):** read `.bento/principles/PRINCIPLES.md` at the start of a task.
- **Authoring instruction files / capturing learnings:** follow
  `.bento/conventions/instruction-layer.md`.
- **Playbooks — read the file when its task starts:**
  - Comparing models/prompts, "which variant is better?" →
    `.bento/plugins/bento-core/skills/eval-blind/SKILL.md`
  - Tuning a metric, stuck score, retrieval/latency work →
    `.bento/plugins/bento-core/skills/hillclimb/SKILL.md`
```

Claude Code reads this too (via the `CLAUDE.md` symlink) but doesn't need it — it gets the
principles by `@import` and the playbooks as auto-triggering skills. The block is what makes
Codex reach the identical files. Keep it terse: `AGENTS.md` is the highest-cost sink and both
agents pay for every line.
