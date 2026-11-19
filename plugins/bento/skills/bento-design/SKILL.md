---
name: bento-design
description: |
  Design rules for UI work: screens, pages, components, dialogs, forms, empty states, menus,
  mockups and the words on them. Use whenever building or changing a user interface.
  Triggers: "design", "UI", "screen", "page", "component", "layout", "mockup", "empty state",
  "label", "button text", "copy".
---

# Design

**Repo layer first.** Read the repo's `AGENTS.md`/`CLAUDE.md` and, if it exists, the
overlay `.agents/bento/bento-design.md` at the repo root; follow it under the
[overlay rules](../bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).

## As little text as possible

Text pulls attention away from the interface. Too much text is like no text: nobody reads it,
and the UI is just as confusing. The UI should work without reading it.

## Steps (paste as todos)

1. **Think twice before adding text.** If the layout, an icon, a state or a default already says
   it, add none.
2. **Cut what is left to the shortest wording.** A word beats a phrase, a phrase beats a
   sentence. No paragraphs, no help text that repeats the label, no "Please" or "Click here".
3. **Prove it.** Screenshot the changed UI and list its visible strings; cut every one the UI
   works without.

## Guardrails

- Keep what users need to act: an error says what to do, a destructive action names what it
  destroys.
- Accessible names (`alt`, `aria-label`) are not clutter: keep them.
