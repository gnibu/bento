#!/bin/bash
# A Python backend service: branch group-sections changes only Python, one file of it the renderer of a published page.
set -euo pipefail
export GIT_AUTHOR_NAME=Dev GIT_AUTHOR_EMAIL=dev@example.com GIT_AUTHOR_DATE=2026-01-01T00:00:00Z
export GIT_COMMITTER_NAME=Dev GIT_COMMITTER_EMAIL=dev@example.com GIT_COMMITTER_DATE=2026-01-01T00:00:00Z
git init -q -b master .
git config user.name Dev && git config user.email dev@example.com && git config commit.gpgsign false
printf '# Backend service\n\n- Base branch: `master`.\n- Tests: `python3 -m unittest discover backend`.\n' > AGENTS.md
mkdir -p backend/routes backend/tests
touch backend/__init__.py backend/routes/__init__.py backend/tests/__init__.py
cat > backend/models.py <<'PY'
from dataclasses import dataclass


@dataclass
class Row:
    question: str
    answer: str
PY
cat > backend/render.py <<'PY'
def build(rows):
    items = "".join(f"<h3>{r.question}</h3><p>{r.answer}</p>" for r in rows)
    return f"<!doctype html><html><body><h1>FAQ</h1>{items}</body></html>"
PY
cat > backend/routes/republish.py <<'PY'
from backend.render import build


def republish(database, bucket):
    """Read the rows from the production database and upload the result to the live site."""
    bucket.upload("faq.html", build(database.rows()))
PY
cat > backend/tests/test_render.py <<'PY'
import unittest

from backend.models import Row
from backend.render import build


class Build(unittest.TestCase):
    def test_lists_each_row(self):
        self.assertIn("<h3>Why?</h3>", build([Row("Why?", "Because.")]))
PY
git add -A && git commit -q -m "chore: init service"
git switch -q -c group-sections
cat > backend/models.py <<'PY'
from dataclasses import dataclass
from typing import Optional


@dataclass
class Row:
    question: str
    answer: str
    section: Optional[str] = None
PY
cat > backend/render.py <<'PY'
from itertools import groupby


def build(rows):
    ordered = sorted(rows, key=lambda r: r.section or "")
    blocks = []
    for section, group in groupby(ordered, key=lambda r: r.section):
        items = "".join(f"<h3>{r.question}</h3><p>{r.answer}</p>" for r in group)
        blocks.append(f"<h2>{section}</h2>{items}" if section else items)
    return f"<!doctype html><html><body><h1>FAQ</h1>{''.join(blocks)}</body></html>"
PY
cat >> backend/tests/test_render.py <<'PY'


class Sections(unittest.TestCase):
    def test_groups_rows_under_their_section(self):
        self.assertIn("<h2>Pricing</h2>", build([Row("Why?", "Because.", "Pricing")]))
PY
git add -A && git commit -q -m "feat: group rows by section in the republish flow"
