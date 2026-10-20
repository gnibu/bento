#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
cat > reset.py <<'CODE'
def issue_reset(user_id, store):
    token = str(user_id)
    store[token] = user_id
    return token


def consume_reset(token, user_id, password, store, users):
    if token in store:
        users[user_id].password = password
        return True
    return False
CODE
