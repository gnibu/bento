#!/bin/bash
# A repo whose root AGENTS.md already has a section about one subfolder, control-room/, and a
# branch that fixes a control-room bug. bento-learn must not grow the root file with a tip the
# fix makes moot, nor with a gotcha that only concerns control-room/.
source "$(dirname "$0")/../_fixtures/repo.sh"
mkdir -p control-room/src control-room/e2e/fakes control-room/test
cat >> AGENTS.md <<'MD'
- Style: `ruff format` before committing Python; Prettier for JS.
- Secrets live in 1Password, never in `.env` files committed to git.

## Control Room

- Control Room is the Electron app in `control-room/`; `npm start` there runs it.
- Its threads resume Claude conversations; see control-room/src/resume.js.
- e2e tests: `node control-room/e2e/drive.js`; the fakes are in `control-room/test/fakes/`.
- Never take the user's focus in an e2e run: pass `--background` to drive.js.
MD
cat > control-room/src/resume.js <<'JS'
// Resume a thread's Claude conversation.
function resumeArgs(thread) {
  return ["--resume", thread.sessionId];
}
module.exports = { resumeArgs };
JS
printf 'module.exports = { claude: () => ({ ok: true }) };\n' > control-room/e2e/fakes/claude.js
printf 'console.log("drive");\n' > control-room/e2e/drive.js
printf '{"name":"control-room","scripts":{"test":"node --test test/"}}\n' > control-room/package.json
printf '// writes threads under $CR_HOME, default ~/.nightshift/control-room\n' > control-room/test/threads.test.js
git add -A && git commit -q -m "chore: control room"
cat > control-room/src/resume.js <<'JS'
// Resume a thread's Claude conversation. A thread whose conversation was never saved has no
// session file: start a new conversation instead of failing every message.
const fs = require("fs");
function resumeArgs(thread) {
  return fs.existsSync(thread.sessionPath) ? ["--resume", thread.sessionId] : ["--session-id", thread.sessionId];
}
module.exports = { resumeArgs };
JS
printf 'test("missing session starts a new conversation", () => {});\n' > control-room/test/resume.test.js
git add -A && git commit -q -m 'fix(control-room): start a new conversation when the saved one is missing'
