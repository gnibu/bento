# Codex (and any AGENTS.md-based agent) — adapter block

Codex has no plugin/skill loader; its only surface is `AGENTS.md`. bento installs a small
marker-bounded pointer block into the consuming repo's `AGENTS.md` so Codex reaches the same
files Claude loads as plugins. Single source of truth stays in `.bento/`; the block is only
pointers.

**Install it (idempotent, re-runnable):**

```bash
python3 .bento/install/bento-agents.py            # default target: ./AGENTS.md
```

`/bento-setup` runs this for you. The block it manages (authoritative version lives in
`install/bento-agents.py`):

```markdown
<!-- bento:start -->
## bento (shared agent operating layer, vendored at `.bento/`)

Agents without a plugin loader (e.g. Codex): read the target file when its trigger fires.

- Comparing models/prompts, "which variant is better?" -> `.bento/plugins/bento-core/skills/eval-blind/SKILL.md`
- Tuning a metric, stuck score, retrieval/latency -> `.bento/plugins/bento-core/skills/hillclimb/SKILL.md`
- Principles & instruction-authoring rules -> `.bento/principles/PRINCIPLES.md`, `.bento/conventions/instruction-layer.md`
<!-- bento:end -->
```

Kept deliberately terse: `AGENTS.md` is the highest-cost sink and both agents pay for every
line. Claude reads this too (via the `CLAUDE.md` symlink) but doesn't need it — it gets the
principles by `@import` and the playbooks as auto-triggering skills; the block exists for
Codex. Edit the `AGENTS.md` source, never a `CLAUDE.md` symlink.
