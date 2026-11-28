#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
cat > auth.py <<'PY'
def can_delete(user, doc):
    return user.is_admin or doc.owner_id == user.id or doc.shared
PY
git add auth.py && git commit -q -m "feat: shared docs can be deleted by anyone they are shared with"
