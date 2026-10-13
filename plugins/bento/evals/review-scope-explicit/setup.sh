#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
git rev-parse HEAD > "$(git rev-parse --git-path adversarial-review.head)"
