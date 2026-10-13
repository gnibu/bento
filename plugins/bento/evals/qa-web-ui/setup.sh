#!/bin/bash
# A static web app with no tests: master has a counter, branch ui-reset adds a Reset button.
set -euo pipefail
export GIT_AUTHOR_NAME=Dev GIT_AUTHOR_EMAIL=dev@example.com GIT_AUTHOR_DATE=2026-01-01T00:00:00Z
export GIT_COMMITTER_NAME=Dev GIT_COMMITTER_EMAIL=dev@example.com GIT_COMMITTER_DATE=2026-01-01T00:00:00Z
git init -q -b master .
git config user.name Dev && git config user.email dev@example.com && git config commit.gpgsign false
printf '# Agents\n\n- Base branch: `master`.\n- Run: `npx serve .` then open http://localhost:3000.\n' > AGENTS.md
printf '{ "name": "counter", "private": true, "scripts": { "start": "npx serve ." } }\n' > package.json
cat > index.html <<'HTML'
<!doctype html>
<html><body>
<p>Count: <span id="count">0</span></p>
<button id="inc">+1</button>
<script src="app.js"></script>
</body></html>
HTML
cat > app.js <<'JS'
let n = 0;
const out = document.getElementById("count");
document.getElementById("inc").onclick = () => { out.textContent = ++n; };
JS
git add -A && git commit -q -m "chore: init counter"
git switch -q -c ui-reset
sed -i.bak 's#<button id="inc">+1</button>#<button id="inc">+1</button>\n<button id="reset">Reset</button>#' index.html && rm index.html.bak
printf 'document.getElementById("reset").onclick = () => { n = 0; out.textContent = n; };\n' >> app.js
git add -A && git commit -q -m "feat: add a reset button"
