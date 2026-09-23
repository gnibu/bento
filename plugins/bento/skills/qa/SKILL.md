---
name: qa
description: |
  Exercise a change against its real surface and report defects (browser, CLI, or API). Use
  before shipping UI/flow changes or to find bugs. Triggers: "QA this", "test the site/app",
  "find bugs", "does this actually work", "smoke test the change".
---

# QA

Drive the real surface the way a user would and report what actually breaks — prove-on-artifact
for behavior. Default is find-and-report; fix only when asked (`--fix`).

## Steps (paste as todos)

1. **Pick the surface and driver.** Web UI → a browser CLI available in the environment
   (`agent-browser`, Playwright — use what's installed; don't assume a bespoke daemon). CLI/TUI
   → run the binary. API → curl/HTTP. Name the driver you're using.
2. **List the critical paths** the change touches — the few user journeys that must work, plus
   the obvious edge cases (empty, error, boundary, unauthorized).
3. **Exercise each path on the real surface.** Perform the actions; capture evidence —
   screenshot, console/network log, exit code, response body. Observation is the test.
4. **Record defects with evidence.** For each: the steps, expected vs actual, and the captured
   artifact. No repro/artifact → not a confirmed defect.
5. **Report, ranked by severity.** Lead with blockers. If run with `--fix`, fix the
   root cause (see `investigate`), then re-run the failing path to confirm.

## Guardrails

- A defect claim needs an artifact (screenshot/log/output). "Looks broken" without evidence
  isn't a finding.
- Test behavior, not implementation. Drive the surface; don't grade the code.
- Don't trigger destructive or irreversible actions (deletes, real payments, emails) while
  exploring — note them as untested rather than firing them.
