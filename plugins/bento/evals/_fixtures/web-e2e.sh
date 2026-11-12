#!/bin/bash
# Shared eval fixture: a web app with unit tests and a Playwright suite of one spec per page.
# Branch settings-timezone changes only the settings page. With E2E_RUNNER=1 the repo also has
# its own selective runner (`npm run e2e`, mapping in e2e/affected.js, `-- --dry` prints it).
set -euo pipefail
export GIT_AUTHOR_NAME=Dev GIT_AUTHOR_EMAIL=dev@example.com GIT_AUTHOR_DATE=2026-01-01T00:00:00Z
export GIT_COMMITTER_NAME=Dev GIT_COMMITTER_EMAIL=dev@example.com GIT_COMMITTER_DATE=2026-01-01T00:00:00Z
git init -q -b master .
git config user.name Dev && git config user.email dev@example.com && git config commit.gpgsign false
mkdir -p src/pages src/shared e2e test
if [ "${E2E_RUNNER:-0}" = 1 ]; then
  run_line='- End-to-end: `make test-e2e` (whole Playwright suite, ~150 tests, 20 min); `npm run e2e` runs only the specs the branch affects (`npm run e2e -- --dry` prints the choice).'
  scripts='"test": "node --test test/", "e2e": "node e2e/affected.js"'
  cat > e2e/affected.js <<'JS'
// Maps changed files (git diff origin/master...) to the specs that cover them, then runs them.
const { execSync } = require("child_process");
const map = { "src/pages/login.js": ["e2e/login.spec.js"], "src/pages/settings.js": ["e2e/settings.spec.js"],
  "src/pages/billing.js": ["e2e/billing.spec.js"], "src/pages/dashboard.js": ["e2e/dashboard.spec.js"] };
const changed = execSync("git diff --name-only origin/master...", { encoding: "utf8" }).split("\n").filter(Boolean);
const all = changed.some((f) => f.startsWith("src/shared/") || f.startsWith("e2e/"));
const specs = all ? [] : [...new Set(changed.flatMap((f) => map[f] || []))];
console.log(all ? "all specs (shared code changed)" : specs.join(" ") || "no spec affected");
if (!process.argv.includes("--dry") && (all || specs.length)) execSync(`npx playwright test ${specs.join(" ")}`, { stdio: "inherit" });
JS
else
  run_line='- End-to-end: `make test-e2e` (whole Playwright suite, ~150 tests, 20 min).'
  scripts='"test": "node --test test/"'
fi
cat > AGENTS.md <<MD
# Agents

- Base branch: \`master\`. Forge: GitHub.
- Unit tests: \`npm test\`.
$run_line
MD
cat > package.json <<JSON
{ "name": "app", "private": true, "scripts": { $scripts }, "devDependencies": { "@playwright/test": "^1.48.0" } }
JSON
printf 'test-e2e:\n\tnpx playwright test\n' > Makefile
printf 'module.exports = { testDir: "e2e", webServer: { command: "npx serve src", port: 3000 } };\n' > playwright.config.js
printf 'export function layout(body) { return `<nav>App</nav><main>${body}</main>`; }\n' > src/shared/layout.js
for p in login settings billing dashboard; do
  printf 'import { layout } from "../shared/layout.js";\nexport function render() { return layout("<h1>%s</h1>"); }\n' "$p" > "src/pages/$p.js"
  cat > "e2e/$p.spec.js" <<JS
const { test, expect } = require("@playwright/test");
test("$p page loads", async ({ page }) => { await page.goto("/$p"); await expect(page.locator("h1")).toHaveText("$p"); });
test("$p page has no console errors", async ({ page }) => { const errors = []; page.on("pageerror", (e) => errors.push(e)); await page.goto("/$p"); expect(errors).toEqual([]); });
JS
done
cat > test/format.test.js <<'JS'
const test = require("node:test");
const assert = require("node:assert");
test("placeholder", () => assert.ok(true));
JS
git add -A && git commit -q -m "chore: init app"
git init -q --bare .origin.git && echo .origin.git >> .git/info/exclude
git remote add origin ./.origin.git && git push -q origin master
git switch -q -c settings-timezone
cat > src/pages/settings.js <<'JS'
import { layout } from "../shared/layout.js";
export function render(user = {}) {
  const tz = user.timezone || "UTC";
  return layout(`<h1>settings</h1><label>Timezone <select id="tz"><option selected>${tz}</option><option>Europe/Paris</option></select></label>`);
}
JS
git add -A && git commit -q -m "feat(settings): let users pick their timezone"
