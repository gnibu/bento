---
name: figure-it-out
description: |
  Fallback for a task no other playbook covers. Use when the request doesn't match an
  existing skill and you'd otherwise improvise. Triggers: an off-catalog task, "there's no
  skill for this", any multi-step work with no matching playbook.
---

# Figure it out

The catch-all so an unmatched task still gets a frame instead of being improvised. Sequence
it explicitly, do it, then decide whether it's worth capturing.

## Steps (paste as todos)

1. **State the goal and the done-condition** in one line. What does success look like, and
   how will you *prove* it (the artifact)?
2. **Map what it touches** before editing — the files, the real flow end to end. Don't
   start on the smallest diff until you understand the whole thing.
3. **Write the todolist.** Break the task into ordered, checkable steps. This list is the
   missing playbook.
4. **Do it**, one step at a time, acting on reversible work and pausing for irreversible
   writes (autonomy contract).
5. **Prove it on the real artifact**, not a self-report.
6. **Decide: capture or drop.** Did this task shape recur, or is it likely to? If yes and
   it has a nameable trigger → propose turning your todolist into a playbook
   (`authoring-a-playbook`). If it was a one-off → drop it, capture nothing.

## Guardrails

- Don't skip step 2 to reach a small diff faster — the smallest change in the wrong place
  is a second bug.
- One occurrence is not a pattern. Resist skilling a task you've done once.
