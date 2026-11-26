#!/bin/bash
# A consumer repo whose root AGENTS.md grew past the size budget: a section of e2e gotchas for
# web/e2e/ (which has no AGENTS.md), a line restating bento's Ship principle, a line naming a
# script that is gone, and two lines that say the same thing. bento-learn adds one learning
# to that file, so its prune pass must propose cutting it back too.
source "$(dirname "$0")/../_fixtures/repo.sh"
git switch -q master
mkdir -p web/e2e/fixtures web/src api/migrations
cat >> AGENTS.md <<'MD'
- Lint: `make lint` (ruff + eslint).
- Asked to commit or open a PR: run bento-ship.
- Format Python with `scripts/format.sh` before committing.
- Run `make test` before pushing.
- Tests: `make test` runs the unit tests; run it before every PR.
- Secrets live in 1Password, never in `.env` files committed to git.
- The API is Flask in `api/`; the web app is Vite + React in `web/`.
- Node 20 for `web/`; `nvm use` reads `web/.nvmrc`.
- Python 3.11 for `api/`.
- Releases are tagged `vX.Y.Z` on master; CI publishes them.
- Feature flags live in `api/flags.py`.
- Log with `structlog`, never `print`.
- Timestamps are UTC everywhere; convert only in the UI.
- Money is in cents (integers) end to end.
- New endpoints need an OpenAPI entry in `api/openapi.yaml`.

## API

- Migrations: `make migrate` applies `api/migrations/`; never edit one that has shipped.
- `api/db.py` opens one session per request; don't share it across threads.
- Background jobs run in `api/jobs/` with RQ; `make worker` starts one.
- Rate limits are in `api/limits.py`, per route.
- Auth is JWT, verified in `api/auth.py`.
- Admin routes live under `api/admin/` and need the `admin` scope.
- Webhooks are verified in `api/webhooks.py` before any write.
- Pagination: cursor-based, `?after=<id>`; never offset.
- Errors return `{"error": {"code", "message"}}`; see `api/errors.py`.
- Celery is gone: don't add new tasks there, use RQ in `api/jobs/`.
- `api/settings.py` reads env vars once at import; restart after changing `.env`.
- Search uses Postgres full-text in `api/search.py`, not Elasticsearch.
- `make api` starts the API on port 8000 with reload.
- Seed data: `make seed` loads `api/fixtures/`.
- The OpenAPI spec is served at `/docs` in dev only.
- S3 uploads go through `api/storage.py`; local dev uses MinIO on port 9000.

## Web e2e tests

- Run them with `npm run e2e` in `web/`; they need the API up (`make api`).
- Playwright browsers install with `npx playwright install chromium` in `web/`.
- `web/e2e/fixtures/` holds the seeded users; log in as `alice@example.com` / `alice`.
- A test that waits on network must use `page.waitForResponse`, never `waitForTimeout`.
- `web/e2e/global-setup.ts` seeds the DB; rerun it after `make migrate`.
- Screenshots of failures land in `web/e2e/test-results/`; it is gitignored.
- Flaky on CI only? CI runs `web/e2e/` with 2 workers; reproduce with `--workers 2`.
- The checkout flow tests need `STRIPE_KEY=sk_test_x` in `web/.env.e2e`.
- Selectors: use `getByRole` or `data-testid`, never CSS classes in `web/e2e/` specs.
- `web/e2e/helpers/login.ts` caches the auth state; delete `web/e2e/.auth/` after a schema change.
- Run one spec: `npx playwright test web/e2e/checkout.spec.ts`.
- Traces: `npx playwright show-trace web/e2e/test-results/<test>/trace.zip`.
- The e2e DB is `app_e2e` on port 5433, separate from dev.
- Mobile viewport tests are tagged `@mobile` in `web/e2e/`; run them with `--grep @mobile`.
- `web/e2e/` specs must clean up the orders they create; the seed doesn't reset them.
- Time-dependent tests freeze the clock with `page.clock.install()` in `web/e2e/`.
- The admin specs in `web/e2e/admin/` need `ADMIN=1`.
- Visual snapshots in `web/e2e/__snapshots__/` update with `--update-snapshots`, never by hand.
- A spec under `web/e2e/` that hits a third-party URL must route it to a fake.
- File uploads in `web/e2e/` use `web/e2e/fixtures/files/`.
- Debug a spec headed: `npx playwright test --headed --debug` in `web/`.
- Retries are off locally; on CI `web/e2e/` retries once.
- Accessibility checks run with `@axe-core/playwright` in `web/e2e/a11y/`.
- E-mail flows read from the fake inbox at `web/e2e/helpers/inbox.ts`.
- Never commit `.only` in `web/e2e/`; CI fails on it.
- Locale tests set `locale` in `web/e2e/playwright.config.ts` projects.
- Network mocks for the payments API are in `web/e2e/mocks/payments.ts`.
- Downloads land in `web/e2e/downloads/`; it is gitignored.
- Clipboard tests need `permissions: ['clipboard-read']` in `web/e2e/`.
MD
cat > Makefile <<'MK'
lint:
	ruff check . && cd web && npx eslint .
format:
	ruff format .
test:
	python3 -m unittest
MK
for f in api/flags.py api/db.py api/limits.py api/auth.py web/e2e/global-setup.ts \
         web/e2e/playwright.config.ts web/e2e/checkout.spec.ts web/.nvmrc; do printf 'x\n' > "$f"; done
python3 "$(dirname "$0")/../../skills/bento-setup/scripts/agents_block.py" --terse on AGENTS.md >/dev/null
ln -s AGENTS.md CLAUDE.md
git add -A && git commit -q -m "chore: repo layer"
git push -q origin master
git switch -q eng-42-greeting
git rebase -q master
