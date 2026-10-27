#!/bin/bash
# A project install updated with npx skills update: every bento skill but wup is present.
source "$(dirname "$0")/../_fixtures/repo.sh"
for s in "$(dirname "$0")"/../../skills/bento-*; do
  name=$(basename "$s")
  mkdir -p ".agents/skills/$name"
  printf -- '---\nname: %s\ndescription: Installed marker.\n---\n' "$name" > ".agents/skills/$name/SKILL.md"
done
mkdir -p .claude && ln -s ../.agents/skills .claude/skills
git add -A
git commit -q -m "test: install bento"
