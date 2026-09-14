---
name: authoring-a-playbook
description: |
  How to write a new bento playbook (a bento-core skill). Use when adding or editing a
  playbook, or turning a repeated task into one. Triggers: "add a playbook", "new skill for
  bento", "capture this as a skill", "write a SKILL.md".
---

# Authoring a playbook

A bento playbook is a triggered skill that opens with a pasteable checklist and proves its
work on a real artifact. Keep them few and earned.

## Gate first — should it exist?

Add a playbook only when the same task shape has recurred (≥2–3 times) and you can name a
concrete trigger. One occurrence → do it inline via `figure-it-out`, don't skill it.
Speculative playbooks are cost paid by every future reader. Default to not adding.

## Steps (paste as todos)

1. **Name the trigger.** When does this fire? Write it as the `description` with concrete
   trigger phrases — that's what makes the skill auto-invoke.
2. **Write the checklist.** Numbered, ordered, checkable steps the agent pastes as todos.
   Lead with them; prose is secondary.
3. **Demand proof.** Include a step that verifies on a real artifact (transcript, test,
   file, before/after) — never a self-report.
4. **Add guardrails.** The 2–3 failure modes this playbook prevents.
5. **Keep it generic.** bento playbooks must help in any repo. Repo/org-specific detail
   belongs in that repo's L2, not here.
6. **Prove it lifts.** Add a `claude plugin eval` case (with/without arm) and run
   `claude plugin eval` — keep the playbook only if it changes behavior. No lift → don't ship.

## Guardrails

- Fix the principle, not the example. Minimal GOOD/BAD pairs; add a BAD example only when
  the instruction alone isn't enough.
- No verbatim production data, no dates/history in the body — state current scope only.
- Shorter is better: if the explanation is longer than the steps, cut the explanation.
