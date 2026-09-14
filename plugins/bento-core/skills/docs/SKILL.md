---
name: docs
description: |
  Write or update documentation so it matches the current code, and produce release notes.
  Use after shipping, or when docs have drifted. Triggers: "update the docs", "document this",
  "write release notes", "changelog", "the docs are out of date".
---

# Docs

Documentation is only useful if it's true. Write to match what the code actually does now, and
prove it against the source — not against memory.

## Steps (paste as todos)

1. **Scope it.** What changed, and which docs cover it — README, guides, API reference,
   changelog. New capability, changed behavior, or drift?
2. **Read the current code first.** Ground every statement in the actual implementation
   (signatures, flags, defaults, endpoints). Docs assert facts; verify each against source.
3. **Write to the audience and purpose.** How-to for tasks, reference for lookup, explanation
   for concepts — one mode per section. Lead with what the reader does, not history.
4. **Update, don't duplicate.** Amend the existing doc in place; link shared procedures rather
   than copying them. Delete stale statements you're replacing.
5. **Release notes / changelog** — group user-facing changes by what the user gains, in the
   repo's changelog convention. Skip internal churn.
6. **Prove it.** Spot-check each claim against the code; if there are runnable examples, run
   them. A doc that says something the code doesn't do is a bug.

## Guardrails

- No aspirational docs — describe current behavior, not intended-someday.
- Match the repo's existing doc structure and style; don't fork a parallel doc set.
- Keep run-specific detail (dates, one-off results) out of durable docs.
